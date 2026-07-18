#!/usr/bin/env python3
"""Tune the Android TV box to a channel number via ADB keyevents.

Usage: python tuner.py 101
Requires ADB network debugging enabled on the box (see docs/box-setup.md).
"""

import json
import pathlib
import subprocess
import sys
import time

CONFIG_PATH = pathlib.Path(__file__).parent / "bridge_config.json"

# Android keycodes: KEYCODE_0 is 7, KEYCODE_9 is 16
DIGIT_KEYCODE_BASE = 7
KEYCODE_DPAD_CENTER = 23
KEYCODE_WAKEUP = 224


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def adb(cfg, *args, check=True):
    cmd = [cfg["adb_path"], "-s", f'{cfg["box_ip"]}:5555', *args]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=20, check=check)


def connect(cfg):
    out = subprocess.run([cfg["adb_path"], "connect", f'{cfg["box_ip"]}:5555'],
                         capture_output=True, text=True, timeout=20)
    if "connected" not in out.stdout.lower():
        raise RuntimeError(f"adb connect failed: {out.stdout.strip()} {out.stderr.strip()}")


def tune(number):
    cfg = load_config()
    connect(cfg)
    adb(cfg, "shell", "input", "keyevent", str(KEYCODE_WAKEUP), check=False)
    # Bring the IPTV player to the foreground (no-op if already there).
    adb(cfg, "shell", "monkey", "-p", cfg["player_package"],
        "-c", "android.intent.category.LAUNCHER", "1", check=False)
    time.sleep(cfg["launch_wait_seconds"])
    for digit in str(number):
        adb(cfg, "shell", "input", "keyevent", str(DIGIT_KEYCODE_BASE + int(digit)))
        time.sleep(0.2)
    adb(cfg, "shell", "input", "keyevent", str(KEYCODE_DPAD_CENTER), check=False)
    print(f"tuned to {number}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print(__doc__)
        sys.exit(2)
    tune(sys.argv[1])
