# TV box setup (OTT Navigator)

Goal: the TV turns on → the channel lane is already there → Grandma picks a
channel by number or with up/down. No app-hopping.

## Step 0 — Identify the box

1. Check the sticker under the ACT set-top box for the model name.
2. On the TV: **Settings → Device Preferences / System → About** shows the model
   and Android TV version.
3. Decisive test: is **Google Play Store** in the apps list?
   - **Yes** → continue below on this box.
   - **No (locked/proprietary box)** → use a Google TV stick or a Fire TV Stick
     plugged into the TV instead. On Fire TV, install OTT Navigator by
     sideloading with the **Downloader** app (code method), since it is not in
     the Amazon Appstore. A Fire TV Stick also pairs natively with the Echo Dot.

## Step 1 — Install and configure OTT Navigator

1. Play Store → search **OTT Navigator IPTV** (`studio.scillarium.ottnavigator`) → Install.
2. Open it → **Settings → Playlists → Add playlist → URL** and paste the raw
   GitHub URL of `playlist.m3u`, e.g.
   `https://raw.githubusercontent.com/<your-username>/<repo>/main/playlist.m3u`
3. EPG usually loads automatically from the `url-tvg` header inside the
   playlist. If the guide stays empty: **Settings → EPG → Add source** and paste
   `https://epgshare01.online/epgshare01/epg_ripper_IN1.xml.gz`, then match
   channels by name.
4. Recommended settings for the Grandma experience:
   - **Settings → Playlists → (your playlist) → Update interval: 6 hours**
   - **Settings → Start → Launch on system boot: on**
   - **Settings → Start → On start open: Last channel**
   - **Settings → Channels → Sort: by number** (uses our fixed `tvg-chno`)
   - Long-press unwanted groups → hide, so only Serials / Movies / News /
     Bhakti / Lifestyle lanes remain.

## Step 2 — Daily use

- **Up/Down** on the remote zaps to the previous/next channel.
- **OK** opens the numbered channel list; scroll and pick.
- With any remote or keyboard that has digits (or the Alexa bridge), typing
  `101` tunes straight to Star Plus.

## Step 3 — One-time prep for the Alexa bridge (Phase 2)

1. **Settings → Device Preferences → About** → click **Build** 7 times to
   unlock Developer options.
2. **Developer options → Network debugging (ADB over network): on**.
3. In the ACT router admin page, give the box a **fixed IP** (DHCP reservation)
   so the bridge always finds it.
