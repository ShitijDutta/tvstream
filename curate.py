#!/usr/bin/env python3
"""Build a curated IPTV playlist from public source playlists.

Reads channels.yaml, fetches the source playlists, matches each configured
channel against source entries by tvg-id, health-checks every candidate
stream, and writes:

  playlist.m3u  - the curated lineup with fixed channel numbers (tvg-chno)
  status.md     - per-channel health report

A channel is never silently dropped: if no candidate passes the health
check, the best-ranked candidate is still emitted and flagged in status.md.
This matters because the health check may run outside India (GitHub
Actions), where geo-blocked streams return 403 yet play fine at home.
"""

import argparse
import concurrent.futures
import datetime
import fnmatch
import re
import sys
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
import yaml

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')

# Health-check verdicts, best to worst. Anything before DEAD gets emitted.
ALIVE, GEO_BLOCKED, DEAD, UNCHECKED = "OK", "GEO?", "DEAD", "UNCHECKED"


@dataclass
class SourceEntry:
    tvg_id: str
    name: str
    url: str
    attrs: dict
    extra_lines: list = field(default_factory=list)  # #EXTVLCOPT / #EXTHTTP etc.
    source_name: str = ""


@dataclass
class Pick:
    entry: SourceEntry
    verdict: str
    detail: str = ""
    ratio: float = None  # download speed / realtime bitrate, if measured


def parse_m3u(text, source_name):
    entries = []
    attrs, name, extra = {}, "", []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#EXTINF"):
            attrs = dict(ATTR_RE.findall(line))
            # Display name follows the last attribute quote + comma; entries
            # without attributes just have "#EXTINF:-1,Name".
            if '",' in line:
                name = line.rsplit('",', 1)[1].strip()
            else:
                name = line.split(",", 1)[1].strip() if "," in line else ""
            extra = []
        elif line.startswith("#EXTVLCOPT") or line.startswith("#EXTHTTP") or line.startswith("#KODIPROP"):
            extra.append(line)
        elif line.startswith("#"):
            continue
        else:  # stream URL terminates the record
            if attrs or name:
                entries.append(SourceEntry(
                    tvg_id=attrs.get("tvg-id", ""), name=name, url=line,
                    attrs=attrs, extra_lines=extra, source_name=source_name,
                ))
            attrs, name, extra = {}, "", []
    return entries


def fetch_sources(cfg):
    entries = []
    for src in cfg["sources"]:
        try:
            resp = requests.get(src["url"], timeout=30, headers={
                "User-Agent": cfg["settings"]["user_agent"]})
            resp.raise_for_status()
            got = parse_m3u(resp.text, src["name"])
            print(f"fetched {src['name']}: {len(got)} entries")
            entries.extend(got)
        except Exception as exc:
            print(f"WARNING: could not fetch {src['name']}: {exc}", file=sys.stderr)
    return entries


def candidates_for(channel, entries):
    """All source entries matching the channel, in preference order."""
    seen, result = set(), []
    for pattern in channel["match"]:
        for entry in entries:
            if entry.url not in seen and fnmatch.fnmatch(entry.tvg_id, pattern):
                seen.add(entry.url)
                result.append(entry)
    return result


def stream_headers(entry, default_ua):
    headers = {"User-Agent": entry.attrs.get("http-user-agent", default_ua)}
    if "http-referrer" in entry.attrs:
        headers["Referer"] = entry.attrs["http-referrer"]
    for line in entry.extra_lines:
        if line.startswith("#EXTVLCOPT:http-user-agent="):
            headers["User-Agent"] = line.split("=", 1)[1]
        elif line.startswith("#EXTVLCOPT:http-referrer="):
            headers["Referer"] = line.split("=", 1)[1]
    return headers


def check_stream(entry, settings):
    timeout = (settings["connect_timeout"], settings["read_timeout"])
    try:
        resp = requests.get(entry.url, headers=stream_headers(entry, settings["user_agent"]),
                            timeout=timeout, stream=True, allow_redirects=True)
        status = resp.status_code
        if status in (401, 403, 451):
            return GEO_BLOCKED, f"HTTP {status}"
        if status >= 400:
            return DEAD, f"HTTP {status}"
        chunk = b""
        for part in resp.iter_content(chunk_size=1024):
            chunk = part
            break
        resp.close()
        if not chunk:
            return DEAD, "empty response"
        if entry.url.split("?")[0].endswith((".m3u8", ".m3u")) and b"#EXTM3U" not in chunk:
            return DEAD, "not an HLS manifest"
        return ALIVE, f"HTTP {status}"
    except requests.RequestException as exc:
        return DEAD, type(exc).__name__


def resolve_media_playlist(url, headers, timeout, depth=0):
    """Follow an HLS master playlist to its first media playlist."""
    text = requests.get(url, headers=headers, timeout=timeout).text
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if depth < 2 and any(l.startswith("#EXT-X-STREAM-INF") for l in lines):
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF") and i + 1 < len(lines):
                return resolve_media_playlist(
                    urljoin(url, lines[i + 1]), headers, timeout, depth + 1)
    return url, lines


def measure_speed(entry, settings):
    """Download (part of) the newest segment; return (dl_mbps, need_mbps) or None."""
    if not entry.url.split("?")[0].endswith((".m3u8", ".m3u")):
        return None
    headers = stream_headers(entry, settings["user_agent"])
    timeout = (settings["connect_timeout"], settings["read_timeout"])
    try:
        media_url, lines = resolve_media_playlist(entry.url, headers, timeout)
        seg_url = seg_dur = None
        for i, line in enumerate(lines):
            if line.startswith("#EXTINF"):
                m = re.match(r"#EXTINF:([\d.]+)", line)
                for nxt in lines[i + 1:]:
                    if not nxt.startswith("#"):
                        seg_url, seg_dur = urljoin(media_url, nxt), float(m.group(1)) if m else None
                        break
        if not seg_url or not seg_dur:
            return None
        start = time.monotonic()
        resp = requests.get(seg_url, headers=headers, timeout=timeout, stream=True)
        total = int(resp.headers.get("Content-Length") or 0)
        got = 0
        for part in resp.iter_content(chunk_size=65536):
            got += len(part)
            if got >= settings["speed_max_bytes"] or time.monotonic() - start > settings["read_timeout"]:
                break
        resp.close()
        elapsed = time.monotonic() - start
        if not got or elapsed <= 0:
            return None
        dl_mbps = got * 8 / elapsed / 1e6
        need_mbps = (total or got) * 8 / seg_dur / 1e6
        return dl_mbps, need_mbps
    except requests.RequestException:
        return None


def speed_detail(speed):
    if not speed or not speed[1]:
        return "speed n/a"
    return f"{speed[0]:.1f} Mbps, {speed[0] / speed[1]:.1f}x realtime"


def pick_fastest(alive, settings):
    """Prefer the first candidate with enough headroom; else the fastest measured."""
    scored = []
    for cand in alive[:3]:  # cap measurement cost per channel
        speed = measure_speed(cand, settings)
        ratio = (speed[0] / speed[1]) if speed and speed[1] else None
        scored.append((cand, speed, ratio))
        if ratio is not None and ratio >= settings["min_speed_ratio"]:
            break  # preference order already ranks quality; good enough wins
    measured = [s for s in scored if s[2] is not None]
    cand, speed, ratio = max(measured, key=lambda s: s[2]) if measured else scored[0]
    return Pick(cand, ALIVE, speed_detail(speed), ratio=ratio)


def pick_stream(channel, entries, settings, executor):
    cands = candidates_for(channel, entries)
    if not cands:
        return None
    futures = {executor.submit(check_stream, c, settings): c for c in cands}
    verdicts = {}
    for fut, cand in futures.items():
        try:
            verdicts[cand.url] = fut.result()
        except Exception as exc:  # never let one stream kill the run
            verdicts[cand.url] = (DEAD, type(exc).__name__)
    alive = [c for c in cands if verdicts[c.url][0] == ALIVE]  # preference order
    if alive:
        if settings.get("speed_test"):
            return pick_fastest(alive, settings)
        return Pick(alive[0], ALIVE, verdicts[alive[0].url][1])
    for cand in cands:
        verdict, detail = verdicts[cand.url]
        if verdict == GEO_BLOCKED:
            return Pick(cand, GEO_BLOCKED, detail)
    verdict, detail = verdicts[cands[0].url]
    return Pick(cands[0], DEAD, detail)


def emit_playlist(picks, cfg, path):
    lines = [f'#EXTM3U url-tvg="{cfg["settings"]["epg_url"]}"']
    for channel, pick in picks:
        if pick is None:
            continue
        e = pick.entry
        attrs = [
            f'tvg-id="{e.tvg_id}"',
            f'tvg-chno="{channel["number"]}"',
            f'tvg-name="{channel["name"]}"',
        ]
        if e.attrs.get("tvg-logo"):
            attrs.append(f'tvg-logo="{e.attrs["tvg-logo"]}"')
        if e.attrs.get("http-user-agent"):
            attrs.append(f'http-user-agent="{e.attrs["http-user-agent"]}"')
        if e.attrs.get("http-referrer"):
            attrs.append(f'http-referrer="{e.attrs["http-referrer"]}"')
        attrs.append(f'group-title="{channel["group"]}"')
        # Mark channels whose best-known stream failed the last check, so the
        # on-TV channel list itself shows what is likely down right now.
        display = channel["name"] if pick.verdict != DEAD else f'{channel["name"]} •down'
        lines.append(f'#EXTINF:-1 {" ".join(attrs)},{display}')
        lines.extend(e.extra_lines)
        lines.append(e.url)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def emit_status(picks, path):
    now = datetime.datetime.now(datetime.timezone.utc)
    ist = now + datetime.timedelta(hours=5, minutes=30)
    lines = [
        "# Channel status",
        "",
        f"Generated {now:%Y-%m-%d %H:%M} UTC ({ist:%Y-%m-%d %H:%M} IST).",
        "",
        "`GEO?` means the checker (which may run outside India) was blocked;",
        "the stream is still included and usually plays fine from home.",
        "`DEAD` channels are still included with their best-known URL, but need attention.",
        "",
        "| # | Channel | Status | Detail | Matched entry | Source |",
        "|---|---------|--------|--------|---------------|--------|",
    ]
    problems = 0
    for channel, pick in picks:
        if pick is None:
            lines.append(f'| {channel["number"]} | {channel["name"]} | NO MATCH | '
                         "no source entry matched | - | - |")
            problems += 1
            continue
        if pick.verdict == DEAD:
            problems += 1
        lines.append(f'| {channel["number"]} | {channel["name"]} | {pick.verdict} | '
                     f'{pick.detail} | {pick.entry.name} | {pick.entry.source_name} |')
    lines += ["", f"Channels needing attention: **{problems}**", ""]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="channels.yaml")
    ap.add_argument("--out", default="playlist.m3u")
    ap.add_argument("--status", default="status.md")
    ap.add_argument("--no-check", action="store_true",
                    help="skip health checks (emit first match per channel)")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    settings = cfg["settings"]

    entries = fetch_sources(cfg)
    if not entries:
        print("ERROR: no source playlist could be fetched", file=sys.stderr)
        return 1

    picks = []
    if args.no_check:
        for channel in cfg["channels"]:
            cands = candidates_for(channel, entries)
            picks.append((channel, Pick(cands[0], UNCHECKED) if cands else None))
    else:
        with concurrent.futures.ThreadPoolExecutor(settings["max_workers"]) as executor:
            for channel in cfg["channels"]:
                pick = pick_stream(channel, entries, settings, executor)
                picks.append((channel, pick))
                label = f"{pick.verdict} ({pick.detail})" if pick else "NO MATCH"
                print(f'  {channel["number"]:>4} {channel["name"]:<22} {label}')

    emit_playlist(picks, cfg, args.out)
    problems = emit_status(picks, args.status)
    matched = sum(1 for _, p in picks if p is not None)
    print(f"wrote {args.out}: {matched}/{len(picks)} channels matched, "
          f"{problems} flagged in {args.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
