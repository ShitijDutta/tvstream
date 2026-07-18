#!/usr/bin/env python3
"""Generate fauxmo's config.json from ../channels.yaml.

Every channel marked `voice: true` becomes a virtual smart-home device the
Echo Dot can discover ("Alexa, discover devices"), so "Alexa, turn on
Star Plus" tunes the TV. Re-run after changing channels.yaml, then restart
fauxmo and re-discover.
"""

import json
import pathlib

import yaml

HERE = pathlib.Path(__file__).parent
FIRST_DEVICE_PORT = 12340


def main():
    channels = yaml.safe_load((HERE.parent / "channels.yaml").read_text(encoding="utf-8"))["channels"]
    bridge = json.loads((HERE / "bridge_config.json").read_text(encoding="utf-8"))
    base = f'http://127.0.0.1:{bridge["tuner_port"]}'

    devices = []
    for i, ch in enumerate(c for c in channels if c.get("voice")):
        devices.append({
            "name": ch["name"],
            "port": FIRST_DEVICE_PORT + i,
            "on_cmd": f'{base}/tune/{ch["number"]}',
            "off_cmd": f"{base}/noop",
            "method": "GET",
            "state_cmd": f"{base}/noop",
        })

    config = {
        "FAUXMO": {"ip_address": "auto"},
        "PLUGINS": {"SimpleHTTPPlugin": {"DEVICES": devices}},
    }
    out = HERE / "config.json"
    out.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} with {len(devices)} voice devices:")
    for d in devices:
        print(f'  "Alexa, turn on {d["name"]}"')


if __name__ == "__main__":
    main()
