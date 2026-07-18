# Alexa bridge

Lets the Echo Dot tune the TV: **"Alexa, turn on Star Plus"** → this bridge
sends the channel number to the IPTV player on the box over ADB.

How it works: [fauxmo](https://github.com/n8henrie/fauxmo) emulates WeMo smart
plugs on the LAN — one per channel marked `voice: true` in `channels.yaml`.
When Alexa "switches on" a channel-device, fauxmo calls the local tuner server,
which sends digit keypresses to the box via ADB.

## One-time setup

1. On the TV box: enable **Network debugging (ADB)** and give the box a fixed
   IP — see `docs/box-setup.md`, Step 3.
2. Edit `bridge_config.json` → set `box_ip` to the box's IP.
3. Install tools on this PC:
   ```
   pip install fauxmo pyyaml
   winget install Google.PlatformTools     # provides adb
   ```
   (If `adb` is not on PATH afterwards, put the full path to `adb.exe` in
   `bridge_config.json` → `adb_path`.)
4. Test ADB + tuning directly (TV on, the IPTV player from
   `bridge_config.json` → `player_package` installed):
   ```
   python tuner.py 101
   ```
   The TV should switch to channel 101. Accept the "Allow USB debugging?"
   prompt on the TV the first time.
5. Generate the device list and start the bridge:
   ```
   python make_fauxmo_config.py
   start.bat
   ```
6. Say **"Alexa, discover devices"** (or Alexa app → Devices → +). The channel
   names should appear as devices. Then: "Alexa, turn on Zee TV".
7. To make it permanent: Task Scheduler → Create Task → run `start.bat` at
   logon.

Nicer phrases: in the Alexa app create a **Routine** per channel, e.g. phrase
"Star Plus chalao" → action Smart Home → Star Plus → On. Routines also let you
use Hindi phrases Grandma prefers.

## Known limitations

- Works only while this PC is on and on the same network. (The bridge can
  later move to a Raspberry Pi or an old Android phone running Termux.)
- Echo firmware occasionally breaks local WeMo emulation. If discovery finds
  nothing after a couple of tries, the fallback is Home Assistant with its
  Alexa integration — or a ₹400–600 wireless numpad remote, which the
  numbered playlist already supports.
- Voice tuning takes ~5 seconds end to end (ADB connect + keypresses).
