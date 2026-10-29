<p align="center"><a href="README.md"><img src="../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# KNULLI scripts — the glue around the cores

> The cores work on their own with RetroArch's netplay menu. These scripts make it a one-button experience on KNULLI: the **Join / Solo** prompt, sending the guest's save home, a direct Wi-Fi link for DS, a PSP ad-hoc relay and a few quality-of-life services.

[![Download](https://img.shields.io/badge/download-knulli--scripts.zip-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/knulli-scripts.zip) &nbsp; [← All cores](../README.md)

<p align="center">
  <img src="../docs/images/join-window-en.png" width="420" alt="Join / Solo prompt">
</p>

## What's here

| File | What it does |
|---|---|
| `nds_save_sync.sh` | EmulationStation game-start / game-end hook — the entry point that calls the helpers below. It must be the **only** file in `/userdata/system/scripts/` (KNULLI runs every file there). |
| `hb_joinask.py` | The **Join / Solo** prompt. When a game starts, it asks the local network whether a netplay room for the same game is open and, if so, offers to join it (solo after 10 s). Handles DSperate rooms and paired versions too. Shows Korean when `system.language` starts with `ko`, English otherwise (override with `HB_LANG`). |
| `launcher/emulatorlauncher.patch` | Small patch for KNULLI's `configgen/emulatorlauncher.py`: starts the guest after the prompt picked Join, and keeps the per-game core for guests joining from the ES netplay lobby. |
| `hb_ownsave.py` | Per-player saves for the dual-console cores (GBA, WonderSwan, Neo Geo Pocket, Game Gear): the guest's own save plays in the host's P2 slot and goes back to the guest afterwards. Also holds the table of paired versions. |
| `netplay_sram_flush.py` | Writes in-game saves to disk right away during netplay, with an optional CPU boost while a session runs. |
| `nds_save_sync.py` | Keeps DS saves in step between DraStic, melonDS DS and DSperate. |
| `hb_direct.py` | DS link play: connects the two devices directly over Wi-Fi (no router hop) for lower latency. |
| `hb_dsmac.py` | Gives every device its own DS firmware MAC after an SD card was cloned. |
| `hb_pspadhoc.py` | PSP ad-hoc multiplayer: a local relay server plus automatic host selection. |
| `hb_dskeys.py` · `hb_dshold.py` · `hb_ds_remember.py` | DraStic helpers: button helper, swap the screens while L2 is held, remember the large-screen layout per game. |
| `hb_idlesave.py` | Saves a state and sleeps after a long idle time in game; saves and powers off just before the battery runs out. |
| `hb_wifimem.py` | Remembers several Wi-Fi networks and reconnects on its own, like a phone. |
| `services/` | KNULLI service wrappers for `hb_idlesave`, `hb_wifimem`, `hb_dsmac` and `hb_pspadhoc`. |

## Install

On the device over SSH, from the unpacked `knulli-scripts` folder:

```sh
# 1) scripts (default folder: DSperate's prebuilt binary calls hb_direct.py and hb_joinask.py from here)
mkdir -p /userdata/system/claude
cp *.py /userdata/system/claude/
cp -r fonts /userdata/system/claude/            # Galmuri pixel fonts for the prompt (OFL-1.1); optional

# 2) the ES hook — keep it the only file in this folder
mkdir -p /userdata/system/scripts
cp nds_save_sync.sh /userdata/system/scripts/
chmod +x /userdata/system/scripts/nds_save_sync.sh

# 3) the launcher patch, so "Join" really starts the guest
mount -o remount,rw /
patch -p1 -d / < launcher/emulatorlauncher.patch
knulli-save-overlay

# 4) optional services: copy, then add their names to system.services in knulli.conf
mkdir -p /userdata/system/services
cp services/* /userdata/system/services/
```

- Turn the prompt off: `global.hb_joinask=0` in `/userdata/system/knulli.conf`, or create `/userdata/system/claude/hb_joinask.off`.
- Undo the launcher patch: `patch -R -p1 -d / < launcher/emulatorlauncher.patch && knulli-save-overlay`.
- Logs go to `/tmp` (RAM), for example `/tmp/hb_joinask.log`.

## Before you use them

- They were written for **KNULLI on the RG35XX Pro** and its paths. On other systems, adjust the paths and the hook first.
- The game tables inside (paired versions in `hb_ownsave.py`, link families and Single-Pak games in `hb_joinask.py`, DS groups in `../cores/ds-dsperate/glue/groups.txt`) match file names in our test library. Edit them to match your file names.
- Each file starts with a short English summary; the detailed notes below it are the original Korean design log.

## License

GPL-3.0-or-later (see [`LICENSE`](../LICENSE)). The Galmuri fonts in the release zip are under the SIL Open Font License 1.1 (`fonts/Galmuri-OFL.txt`).
