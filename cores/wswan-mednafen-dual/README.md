<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# Beetle WonderSwan Dual — the WonderSwan link cable for two devices

> A libretro core that runs two WonderSwan consoles joined by the serial link cable inside one core, so link-cable games can be played on two handhelds over RetroArch netplay.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/wswan-mednafen-dual-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| **Core file** | `mednafen_wswan_dual_libretro.so` — aarch64 Linux, 2,312,664 bytes (in the release zip, not stored in git) |
| **Version** | `1.9-os4 f01a6988+ownsave+rot+pr` (core name `Beetle WonderSwan Dual`, inner core `v0.9.35.1`) |
| **md5** | `53e2b57da54e3af050614309872d7a4e` |
| **Upstream** | [libretro/beetle-wswan-libretro](https://github.com/libretro/beetle-wswan-libretro) @ [`4b01295`](https://github.com/libretro/beetle-wswan-libretro/commit/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd) ("minor wording nitpick (#104)", 2026-07-31) |
| **License** | GPL-2.0-or-later |
| **Tested on** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (the only environment checked) |

## What it does

The stock Beetle WonderSwan core emulates a single console, so games that use the link cable for two players could not be played together: One Piece Grand Battle Swan Colosseum, Puyo Puyo Tsuu, Kurupara!, Shanghai Pocket, Detective Conan, and others. This core puts **two WonderSwans inside one core**, wires their serial ports together, and lets two handhelds play them over RetroArch netplay. The host's screen shows console 1P; the guest's screen shows console 2P.

- **Stays in sync.** Savestates are made byte-for-byte stable, so RetroArch netplay (rollback included) keeps both devices in step.
- **Everyone keeps their own save.** The guest plays on their own save and gets it back when the session ends.
- **Portrait games stand upright**, and games that are picky about link timing get per-game timing.
- **Pair games.** A few link games came as two different cartridges that talk to each other. The core can put a different ROM into console 2P (Detective Conan 08 ↔ 06).
- **Checked on two devices:** One Piece Grand Battle link play with the real save intact, the start of a Shanghai Pocket match, and the Conan 08 ↔ 06 screen for sending data from the earlier game.

### Good to know

- Both devices need the same core file and the same ROM. Pair games only work with their defined partner ROM.
- With `wswan_dual_link` set to `on`, console 2P runs even when you play alone, which costs CPU. Measured on the RG35XX Pro with Golden Axe: 81% CPU at 1220 MHz, against 71% at 785 MHz on the stock core. Set the option to `off` for stock speed when you play solo.
- Known limits: in Sennou Millennium, if both players press START on the title screen in the same frame, the game reports a communication error (not a core problem); it starts normally as soon as the presses are even one frame apart. Only identical ROMs can link, so a Korean-translated ROM cannot link with the Japanese original. Portrait orientation is decided when the game loads; SELECT cannot rotate it.

## What we changed

1. **A new front end, `dual/libretro_dual.c`.** It builds the inner Beetle WonderSwan core twice, with about 300 external names prefixed `wsA_` and `wsB_` (`dual/build_dual.sh`), and links both copies into one `.so`. The two consoles take turns running one scanline (256 cycles) at a time, and after each line the serial byte that just finished is handed to the other console's receiver. Pad port 0 drives console 1P (host), pad port 1 drives console 2P (guest). Only 25 `retro_*` functions are exported.
2. **The serial port (`comm.c`) rewritten to behave like the hardware (patch 0001).** Status register 0xB3 always shows the receive-ready and overrun bits. A byte takes 10 bit times (3,200 cycles at 9,600 bps, 800 cycles at 38,400 bps). The transmit IRQ is level-triggered, like receive, and the byte in flight is saved in the savestate.
3. **A line-stepped execution API, `hb_ws_*` (0002).** `retro_run` is split into smaller functions. Used as a single console, the core runs exactly like stock.
4. **Stable savestates (0003).** The unused tail of the 60 Hz audio cache (`LRAV`) is zeroed, so the same scene always serializes to the same bytes. Before, every save differed, and netplay CRC checks mismatched.
5. **State layout.** A 64-byte header followed by the state of both consoles (a fixed size for each game). Flag bits in the header's version field mark portrait (0x100), half-frame timing (0x200) and pair game (0x400), so states made with different settings refuse each other.
6. **Screen file (0006).** `/tmp/hb_dual_screen` selects the 1P or 2P picture and sound while the game is running.
7. **Per-player saves (0007, 0009).** The guest plays on their own save and gets it back after the session. 0009 hardens this with atomic writes, a transaction folder and a thread that confirms the guest really is console 2P. 0008 adds a build-time check that the netplay version string fits in 32 bytes including the terminator.
8. **Portrait games (0010).** Vertical games are stood upright and the buttons are remapped to match.
9. **Link timing (0013).** The `wswan_dual_link_phase` option (version 1.5), plus a fix that matches console 2P's 60 Hz count to console 1P's when a guest save is received (1.6).
10. **Serial overwrite and a CPU guard (0014, version 1.7).** When the receive buffer is full and a new byte arrives, the new byte overwrites the old one (Kurupara! needs this). If instructions that never reduce the cycle count keep coming, each is charged one cycle, which stops an endless loop.
11. **Shanghai Pocket mode (0015, 1.8).** Only when the ROM header identifies Shanghai Pocket and two consoles are running: serial bytes are delivered at the exact cycle (800 or 3,200) and interrupt priority and a few other details are matched. For every other game the state is identical to 1.7.
12. **Pair games (0016, 1.9).** Console 2P can run a different ROM (request type HBQ4, path in `/tmp/hb_dual_p2rom`). For games that aren't pairs, the state is identical to 1.8 down to the byte.

Names and comments containing `hb_` or `hanbang` only mark the places we changed; nothing was renamed.

## Core options

The first value is the default.

| Option | Values | What it does |
|---|---|---|
| `wswan_dual_screen` | `1P` · `2P` | Whose picture and sound you get (host or solo = 1P, guest = 2P). |
| `wswan_dual_link` | `on` · `off` | `off` doesn't run console 2P, so the speed matches a single-console core. Read only when a game starts. |
| `wswan_dual_link_phase` | `same` · `half` | Whether console 2P runs half a frame later. Only Puyo Puyo Tsuu and Fire Pro Wrestling use `half`. Both devices must use the same value. |
| `wswan_rotate_display` | `manual` · `landscape` · `portrait` | Stands portrait games upright (same key as the original core). SELECT never rotates. |
| `wswan_dual_pair_hold` | `off` · `1P` · `2P` | Pair games only: holds all buttons on that console for 2 seconds at power-on (Detective Conan 06's send screen). |

**Files in `/tmp`** (the core runs normally when they don't exist):

- `/tmp/hb_dual_screen` — `1P` or `2P`; takes precedence over the option.
- `/tmp/hb_ownsave/` — the transaction folder for per-player saves.
- `/tmp/hb_dual_p2rom` — one line: the path of console 2P's ROM for a pair game.

**Saves.** Console 1P normally uses `.srm`; console 2P uses `<ROM name>.p2.sav` on the host. The guest's device neither reads nor writes the 1P and 2P saves (per-player save mode), and it receives its console-2P progress back as its own save when the session ends.

## Install on KNULLI

Put the **same `.so`** on both devices (if the version strings differ, RetroArch warns and the session can drift out of sync). Download `wswan-mednafen-dual-linux-aarch64.zip` from the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest), unzip it, and install with no game running.

**Before you start**

- The prebuilt `.so` is for **aarch64 Linux**: it only uses glibc 2.34 or older symbols and needs just `libc.so.6`. For another CPU or OS, rebuild it from the patches. `dual/build_dual.sh` has a Mac mode, and a Mac arm64 test build worked (for testing only; it was not installed on a device).
- Only **KNULLI + RetroArch 1.22.2** has been checked.
- Per-player saves, pair games and the screen file switch on only when the KNULLI hook writes files into `/tmp`. Without those files the core runs the plain way: the host's 1P `.srm` plus `.p2.sav`. Guest detection reads `--connect` from the launch command and the RetroArch log line that reports joining as player 2, so it relies on the shape of KNULLI's launcher.
- Check the unzipped file: md5 as above, sha256 `8d0af05a909dc722e5920255c76d96bab62dd1e05f68f4ebf34c794346cc07ca`.

**Steps**

1. Copy the core to SD storage, into `/userdata/system/hanbang_cores/` (default path used by the prebuilt files), and put a symlink where RetroArch looks. KNULLI's `/usr` is an overlay, so save it with `knulli-save-overlay`, or the link is gone after a reboot. The new file name leaves the stock `mednafen_wswan_libretro.so` untouched.
   ```sh
   mkdir -p /userdata/system/hanbang_cores
   cp mednafen_wswan_dual_libretro.so /userdata/system/hanbang_cores/ && chmod 755 /userdata/system/hanbang_cores/mednafen_wswan_dual_libretro.so
   mount -o remount,rw /
   ln -sfn /userdata/system/hanbang_cores/mednafen_wswan_dual_libretro.so /usr/lib/libretro/mednafen_wswan_dual_libretro.so
   knulli-save-overlay
   ```
2. **Core info file.** Without it the launcher refuses to run the core. Copy the stock info file and change the names:
   ```sh
   I=/usr/share/libretro/info
   sed -e 's/^display_name = .*/display_name = "Bandai - WonderSwan\/Color (Beetle WonderSwan Dual)"/' \
       -e 's/^corename = .*/corename = "Beetle WonderSwan Dual"/' $I/mednafen_wswan_libretro.info > $I/mednafen_wswan_dual_libretro.info
   knulli-save-overlay
   ```
3. **Pick the core per game** in `/userdata/system/knulli.conf` (`wswanc` for color games, `wswan` for monochrome): `wswanc["<ROM file name>.zip"].core=mednafen_wswan_dual`
4. **Show "start netplay game" in ES.** Add one line to the ES feature table (`es_features_*.cfg`): `<core name="mednafen_wswan_dual" features="netplay" />`
5. **Game-start hook.** Each time a game starts, the hook writes that game's core option file, `/userdata/system/configs/retroarch/config/Beetle WonderSwan Dual/<ROM name>.opt`: host or solo gets `1P`, guest gets `2P`, and link is `on`. The hook is block 19 of [`knulli-scripts/nds_save_sync.sh`](../../knulli-scripts/).
   - Install it as `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files), and keep that folder to this one file, because KNULLI runs every file in it.
   - The helper scripts in the same folder go to `/userdata/system/claude/` (default path used by the prebuilt files): `hb_ownsave.py` (per-player saves) and `hb_joinask.py` (the join-or-play-solo prompt).
6. **Screen settings.** To keep the shaders and screen position you use with the stock core, copy that core's RetroArch config files (for example `wswanc.cfg` and `wswan.cfg` in `config/<core name>/`) into `config/Beetle WonderSwan Dual/`. RetroArch can't read them under a different core name.
7. **Undo.** Run `rm /usr/lib/libretro/mednafen_wswan_dual_libretro.so && knulli-save-overlay` and remove the `core=mednafen_wswan_dual` line from `knulli.conf`. The stock core doesn't read the 2P save `.p2.sav`, so just leave it.

## Build from source

```sh
git clone https://github.com/libretro/beetle-wswan-libretro
cd beetle-wswan-libretro
git checkout 4b01295838ea89e3f1355bbe4cb5cf98aa6108cd
PATCHES=/path/to/handheld-link-cores/cores/wswan-mednafen-dual/patches
for p in "$PATCHES"/*.patch; do patch -p1 < "$p" || break; done
```

The build below is the one used for the prebuilt file (Debian 12, aarch64, gcc 12.2.0). Compile the inner core once the normal way to get its **symbol list**, then use that list to compile two prefixed copies (`wsA_` and `wsB_`) and link them together.

```sh
B=$PWD/b; mkdir -p $B
# The version text the core reports. It must be the same on both devices and, together with "1.9-os4", at most 31 characters (checked at build time)
printf '#define GIT_VERSION " f01a6988+ownsave+rot+pr"\n' > $B/ver.h
cat > $B/flags <<EOF
-O2 -DNDEBUG -fPIC -mcpu=cortex-a53 -I. -Imednafen -Imednafen/include -Ilibretro-common/include -DSIZEOF_DOUBLE=8
-DMEDNAFEN_VERSION_NUMERIC=931 -DMPC_FIXED_POINT -DSTDC_HEADERS -D__STDC_LIMIT_MACROS -D__LIBRETRO__ -D_LOW_ACCURACY_
-DINLINE=inline -DWANT_16BPP -DWANT_STEREO_SOUND -DFRONTEND_SUPPORTS_RGB565 -include $B/ver.h -w
EOF
SRCS="mednafen/wswan/sound.c mednafen/wswan/interrupt.c mednafen/wswan/comm.c mednafen/wswan/rtc.c mednafen/wswan/tcache.c
mednafen/wswan/gfx.c mednafen/wswan/wswan-memory.c mednafen/wswan/v30mz.c mednafen/wswan/eeprom.c mednafen/sound/Blip_Buffer.c
mednafen/mempatcher.c mednafen/state.c mednafen/settings.c libretro.c libretro-common/compat/compat_strl.c libretro-common/compat/compat_snprintf.c"
for s in $SRCS; do gcc @$B/flags -c -o $B/inner_$(echo $s | tr / _).o $s; done   # 1) for the symbol list
CC=gcc NM=nm bash dual/build_dual.sh linux $B "$SRCS"                              # 2) two copies, linked together
strip --strip-unneeded $B/mednafen_wswan_dual_libretro.so
```

- `-mcpu=cortex-a53` is tuned for the RG35XX line (H700). Change it for another CPU.
- Rebuilding with the same tools (Debian 12 aarch64, gcc 12.2.0-14+deb12u1) gave byte-identical cores for the 1.7 and 1.8 sources during development. With different tools the md5 will differ, but the behavior is the same.
- The Mac arm64 test build uses `dual/build_dual.sh mac …` (for testing only).

## Patches

Apply the files in `patches/` **in file-name order**, one at a time.

| Order | File | What it does |
|---|---|---|
| 1 | `0001-WonderSwan-UART-accurate-status-timing-and-level-IRQ.patch` | Rewrites the serial port (`comm.c`) to behave like the hardware and adds a link port for a front end. |
| 2 | `0002-Libretro-run-a-frame-line-by-line-hb_ws_-API-for-a-t.patch` | Splits `retro_run` into a line-by-line API (`hb_ws_*`) for a two-console front end. |
| 3 | `0003-Libretro-zero-the-unused-tail-of-the-60Hz-audio-cach.patch` | Zeroes the unused tail of the 60 Hz audio cache in savestates, so identical scenes save identical bytes. |
| 4 | `0004-Libretro-add-Beetle-WonderSwan-Dual-two-WonderSwans-.patch` | Adds the two-console front end, `dual/libretro_dual.c` (version 1.0). |
| 5 | `0005-Libretro-dual-trace-heartbeat-every-60-shown-frames-.patch` | Test-only trace heartbeat every 60 shown frames (active only with `WSWAN_DUAL_TRACE`). |
| 6 | `0006-screen-file-runtime-selection.patch` | `/tmp/hb_dual_screen` selects the 1P or 2P picture and sound while the game runs. |
| 7 | `0007-guest-own-save.patch` | Per-player saves: the guest plays on their own save (version 1.1-ownsave). |
| 8 | `0008-netplay-version-length.patch` | The netplay version string is 32 bytes including the terminator; the length is now checked at build time. |
| 9 | `0009-ownsave-harden.patch` | Finishes the save protection: atomic writes, a transaction folder, and a thread that confirms the guest is console 2P. |
| 10 | `0010-rotate-portrait.patch` | Stands portrait games upright and remaps the buttons (version 1.3-os4). |
| 11 | `0013-ws16-from-0010.patch` | Adds the link timing option (1.5) and, when a guest save arrives, matches console 2P's 60 Hz count to console 1P's (1.6-os4). |
| 12 | `0014-ws17-serial-overwrite-cpu-guard.patch` | Serial overwrite and a guard against endless CPU loops, for Kurupara! (1.7-os4). |
| 13 | `0015-ws18-shanghai-mode.patch` | Shanghai Pocket mode (1.8-os4). |
| 14 | `0016-ws19-pair-game.patch` | Pair games, Detective Conan 08 ↔ 06 (1.9-os4). |

- **Why 0011 and 0012 are missing.** 0011 was version 1.4 (end of frame for console 2P moved to line 64); it broke One Piece and was reverted. 0012 was a standalone 1.5 whose content is already in `0013-ws16-from-0010.patch`, a cumulative patch that goes directly on top of 0010. Neither is part of the final version, so neither is included.
- `0001` to `0005` are in `git format-patch` format and also apply with `git am`. `0015` and `0016` are `diff -ruN` output (`-p1`).
- Some comments inside the patches are in Korean; they were left as written.
- **Checked on 2026-10-29 (on a Mac).** The 14 patches apply in order to upstream `4b01295` with no fuzz, and the resulting source reports `DUAL_VERSION` `1.9-os4`. For 0001 to 0005, the git blob hashes of the 14 files they touch matched our commit. Development test-bench records: for games that aren't pairs, 1.9 is byte-identical in state to 1.8 (3 games × 4 settings × 2 seeds = 24 combinations), and a pair-game rewind of 600 frames had 0 mismatches.
- Whenever the core changed, one round of One Piece link play was repeated on the devices (receive the guest save, then Grand Battle 1P vs. 2P) to make sure nothing had regressed.

## Upstream status

Worth sending: two small, independent fixes that also affect the stock single-console core.

1. **Savestates that are not reproducible** (patch 0003). The unused tail of the 60 Hz audio cache (`LRAV`) is never cleared, so the same scene can serialize to different bytes, which shows up as netplay CRC mismatches. Upstream master has no `memset` there (checked 2026-10-29).
2. **An endless V30MZ loop** (the `v30mz.c` part of patch 0014). The loop can fail to end on an instruction that consumes no cycles. Upstream master has no such guard either (checked).

Both are a few lines each and can go upstream as separate pull requests. Draft title: "Fix non-deterministic savestates (unused LRAV tail) and guard the V30MZ loop against zero-cycle instructions". The English draft text is in [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) under `upstream_pr_candidate`.

The two-console front end, the serial link and the per-player saves are specific to this setup, so they will not be sent.

## License

- Upstream Beetle WonderSwan (Mednafen) is **GPL-2.0-or-later**: its `COPYING` is GPLv2 and the file headers say "version 2 … or (at your option) any later version". A copy of the license text is in [`LICENSES/beetle-wswan-libretro_COPYING`](../../LICENSES/beetle-wswan-libretro_COPYING). The patches in this folder follow those terms, and the newly written `dual/libretro_dual.c` carries the same GPL header.
- `dual/hb_ownsave.h`, `hb_storage.h` and `hb_romfile.h` have no separate header. They are combined into the same core, so they are released under the same terms as the core (written for this project).
- If you distribute binaries that contain this core, you must also publish the modified source — these patches.
