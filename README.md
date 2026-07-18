# TVStream

A self-maintained live-TV "channel lane" for the family TV, replacing the
Airtel IPTV box: fixed channel numbers, a program guide, and optional Alexa
voice tuning — running on the ACT connection with any Android TV / Google TV
device as the player.

```
GitHub Actions (every 6h)
  └─ curate.py: fetch public playlists → keep our channels → health-check
     → playlist.m3u (stable raw URL) + status.md (health report)

TV box: Televizo (or OTT Navigator) subscribes to the playlist URL + EPG
Echo Dot (optional): "Alexa, Star Plus chalao" → alexa-bridge → ADB → tunes channel
```

## Repo layout

| Path | Purpose |
|------|---------|
| `channels.yaml` | The lineup: channel numbers, names, match patterns, groups |
| `curate.py` | Builds `playlist.m3u` + `status.md` from public sources |
| `.github/workflows/refresh.yml` | Re-runs the curator every 6 hours |
| `docs/box-setup.md` | Player app (Televizo) setup on the TV box |
| `alexa-bridge/` | Echo Dot voice control (runs on a PC on the same network) |

## Setup

1. Create a **public** GitHub repository (the raw playlist URL must be
   fetchable by the TV box without authentication) and push this project.
2. In the repo: **Actions** tab → enable workflows → run **Refresh playlist**
   once manually (`workflow_dispatch`).
3. Follow `docs/box-setup.md` on the TV box, using
   `https://raw.githubusercontent.com/<user>/<repo>/main/playlist.m3u`.
4. Optional voice control: see `alexa-bridge/README.md`.

To change the lineup, edit `channels.yaml` and re-run
`python curate.py` (or wait for the next scheduled run). `status.md` always
shows which channels are healthy.

## Reality check on sources

Streams come from the public [iptv-org](https://github.com/iptv-org/iptv)
playlists. The Doordarshan / news / devotional entries are official free
streams. The pay GEC entries (Star Plus, Colors, Zee TV, Sony…) are
**unofficial restreams**: they disappear and reappear, which is exactly why
the curator health-checks and substitutes streams automatically — but there is
no guarantee, and their legality is grey. Stable, legal alternatives to keep
in mind if a must-have channel keeps dying:

- **JioHotstar** (~₹299/3 months) — Star Plus and Colors serials on demand.
- **ZEE5** — Zee TV serials; **SonyLIV** — Sony serials.
- **DD Free Dish** (~₹1,500 one-time, ₹0/month) — satellite dish carrying the
  free rerun GECs (Star Utsav, Sony Pal, Colors Rishtey, Dangal…), fully
  independent of the internet connection.
- **Waves** (Prasar Bharati) — free official OTT app with DD channels.

## Cutover checklist (before cancelling Airtel)

1. All Serials-group channels play smoothly at evening peak time for a full week.
2. Grandma has used only the new setup for that week without help.
3. `status.md` shows no persistent `DEAD` on her must-have channels.
