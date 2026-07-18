# TV box setup

Goal: the TV turns on → the channel lane is already there → Grandma picks a
channel by number or with up/down. No app-hopping.

The box was identified as **IP Set Top Box ACT4K2020** (ACT Stream TV 4K,
Android TV) with Google Play Store access — so everything runs on the
existing box.

## Step 1 — Install a player: Televizo (from Play Store)

> **Why not OTT Navigator?** It was removed from the Play Store. A listing
> named "OTT Navigator IPTV" that still appears there is a **clone by a
> different developer — do not install it**. The real one can be sideloaded
> (see the end of this doc), but Televizo installs cleanly from the Play
> Store and supports everything our playlist uses.

1. Play Store → search **Televizo** (`com.ottplay.ottplay`) → Install.
2. Open it → **Playlists → Add playlist → URL** and paste the raw GitHub URL
   of `playlist.m3u`, e.g.
   `https://raw.githubusercontent.com/<your-username>/<repo>/main/playlist.m3u`
3. EPG loads automatically from the `url-tvg` header inside the playlist. If
   the guide stays empty: **Settings → EPG → Add EPG source** and paste
   `https://epgshare01.online/epgshare01/epg_ripper_IN1.xml.gz`.
4. Recommended settings for the Grandma experience:
   - Playlist **update interval: 6 hours** (or "on app start").
   - **Use channel numbers from playlist** (our fixed `tvg-chno` values) — in
     playlist or appearance settings.
   - **Open last channel on startup**: on.
   - Hide unwanted groups so only Serials / Movies / News / Bhakti /
     Lifestyle lanes remain.
5. Test: with the channel list open, up/down zaps channels; OK opens the
   numbered list; if a paired input device has digit keys, typing `101`
   should jump to Star Plus. **If digit tuning does not work in Televizo,
   switch to the real OTT Navigator (below), which supports it.**

## Step 2 — Daily use

- **Up/Down** on the remote zaps to the previous/next channel.
- **OK** opens the numbered channel list; scroll and pick.
- The Alexa bridge (or any remote/keyboard with digits) tunes by number.

## Step 3 — One-time prep for the Alexa bridge

1. **Settings → Device Preferences → About** → click **Build** 7 times to
   unlock Developer options.
2. **Developer options → Network debugging (ADB over network): on**.
3. In the ACT router admin page, give the box a **fixed IP** (DHCP
   reservation) so the bridge always finds it.
4. If you end up using OTT Navigator instead of Televizo, change
   `player_package` in `alexa-bridge/bridge_config.json` to
   `studio.scillarium.ottnavigator`.

## Alternative — sideload the real OTT Navigator

1. Play Store → install **Downloader** (by AFTVnews).
2. Settings → Apps → Security & restrictions → allow **Unknown sources** for
   Downloader.
3. Open Downloader → enter code **982469** (official ottnavigator.com APK) →
   install.
4. Configure the same playlist URL; enable **Settings → Start → Launch on
   system boot** and **On start open: Last channel**; sort channels by number.
