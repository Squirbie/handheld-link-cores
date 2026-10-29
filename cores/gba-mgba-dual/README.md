<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# mGBA Dual — two GBAs and a link cable inside one core

> A libretro core that runs two Game Boy Advances joined by a virtual link cable, so two handhelds can play GBA link-cable games over plain RetroArch netplay.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/gba-mgba-dual-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `mgba_dual_libretro.so` (aarch64 Linux, 1,248,696 bytes, stripped) |
| Version | `1.6-os4 (mGBA 7a12d6d4)` (`os4` is a label meaning "own save, 4th revision") |
| md5 | `df34be2b181f863497fa749d04d5c1c0` |
| Upstream | [libretro/mgba](https://github.com/libretro/mgba) at commit `7a12d6d`, plus five commits from [tangobattle/mgba](https://github.com/tangobattle/mgba) |
| License | MPL-2.0 |
| Tested on | Anbernic RG35XX Pro · KNULLI |

This is the final build that is actually installed on the RG35XX Pro (KNULLI, aarch64 Linux).
The prebuilt `.so` is not stored in this folder. It comes in the release zip `gba-mgba-dual-linux-aarch64.zip` (see the Download button).
This folder holds the documentation and the patches only. No ROMs, BIOS files or saves are included.

## What it does

Plenty of GBA games have two-player modes that need a link cable (The Legend of Zelda: Four Swords, Yu-Gi-Oh!, Tekken Advance, Mega Man Battle Network / Rockman EXE, Bomberman, and more), but a handheld has only one GBA in it.
This core runs **two GBAs (1P and 2P) inside one core** and joins them with a virtual link cable.
When two devices swap controller input over RetroArch netplay, both run exactly the same calculation and produce exactly the same picture.
The host shows the 1P screen and sound, and the guest shows 2P's. Only what is displayed differs.

What this build can do:

- **Connect in any order.** It doesn't matter who opens the link menu first (Zelda: Four Swords, Yu-Gi-Oh!, ...). The cable connects either way (since 1.4).
- **Each player keeps their own save.** The guest's save is loaded into the 2P slot on the host's device for the session and goes back to the guest's own save afterward. The host's save is never mixed in.
- **Pair games.** Different editions of the same series can play each other, such as Rockman EXE 5 Team of Blues and Team of Colonel, or Bomberman Blue and Red (since 1.5).
- **Single-pak games.** For games where one cartridge serves several players (Bomberman Story, Magical Quest, Shantae), the guest's GBA boots with no cartridge from a real BIOS and receives the host's program over the cable (since 1.6).
- **Solo mode** (`mgba_dual_link=off`), and a small file that switches the 1P / 2P display even in the middle of a game.

Both devices must run the **same build** (1.6-os4). If the builds differ, the core refuses to load the other side's save state, so the two sides can't drift apart unnoticed. All you see is a "load failed / out of sync" notice.

## What we changed

1. **A new libretro frontend**, `src/platform/libretro/dual/libretro_dual.c` (patch 0006, CMake option `LIBRETRO_DUAL`).
   It holds two GBAs running the same ROM plus one `GBASIOLockstepCoordinator`. `retro_run` steps whichever cores are awake in turn on a single thread until 1P has finished a frame (the same approach as tangobattle/mgba-rollback).
   That makes the whole system a deterministic function of the two pads' input, so RetroArch netplay's input sync plus rollback is all it needs. Port 0 is 1P and port 1 is 2P.
   A save state holds both cores, both lockstep drivers, both saves, and the values that mGBA's own state drops (audio FIFO, DMA), in a fixed size of 1,058,208 bytes.
   The RTC runs on a fixed clock (2004-01-01 plus emulated time).
2. **Lockstep and state exactness taken from tangobattle/mgba** (0001–0005): cooperative single-thread driving, bit-exact state restore, no clock overflow after about 128 seconds, and exact restore of the audio state.
3. **Link-pin restore on state load** (0008): RCNT's low bits (the link pins) are restored exactly. Without this, after a netplay join or resync the CRC kept differing, and the state had to be re-sent at every check (every 30 frames; 490 times in five minutes, now 0).
4. **Link accuracy**: SIOCNT clock and baud bits and peers that aren't ready yet (0010); the VRAM contention mask and SIO event order on rewind (0011); and **link timing (0016)**.
   With link timing, the SD line reads 1 even while the partner GBA sits in a menu, and a parent that writes start bit 0 during a transfer stops it. That is why Zelda and Yu-Gi-Oh! connect regardless of who goes first.
5. **Saving**: the 2P save name and write (0007, 0009), and **a separate save for each player** (0014, 0015). The guest's save goes into the host's 2P slot and is written back at the end. The core checks that the guest really joined as 2P, writes through a temporary file plus fsync, and takes an intermediate save after the data has been stable for 5 seconds.
6. **Pair games** (0018): only the 2P GBA boots a different ROM (another edition of the same series). The state version field changes only for a pair. Without a pair, the output is byte-identical to 1.4.1.
7. **Single-pak** (0019): with the per-game option `mgba_dual_p2_nocart = "enabled"`, 2P boots from the BIOS with no ROM and waits for the host's multiboot signal (`0x6200`). If the BIOS can't be used, 2P boots from the pack and a log line is written. With the option off (the default), the output is byte-identical to 1.5.

Names starting with `hb_` or `HB_`, and the word `hanbang`, in the patched code are only our marker for "changed here". We left them as they are so that patches, binaries and scripts stay consistent.

### How it was checked

- **1.6 stage (single-pak):** harness 18/18 (Bomberman Story, Magical Quest, Shantae). Real RetroArch 1.22.2 netplay showed 0 desyncs, and 8,700 rewinds plus 2,700 real RetroArch states showed 0 mismatches. With the option off, the per-frame fingerprints match 1.5 (27,492 frames).
- **1.5 stage (pair games):** Bomberman Blue and Red, and Rockman EXE 5 Team of Blues and Team of Colonel, got as far as starting a battle and choosing chips. Without a pair, the output is byte-identical to 1.4.1 (22,899 frames).
- **1.4 stage (link timing, offset-timing harness):** Zelda: Four Swords 361/361, Yu-Gi-Oh! 2006 346/361, KOF EX2 161/161 (passed / total). Full-state rewind comparisons: 26,250 with 0 mismatches (GBA and WonderSwan combined).
- **Limits:** most testing used Mac and virtual-machine harnesses, plus real RetroArch inside a VM. Long runs over a device's Wi-Fi and the link menus of every game were not checked.

## Core options

Defined in `libretro_dual.c`.

| Option | Values | Meaning |
|---|---|---|
| `mgba_dual_link` | on / off | Cable link (read once, when the content is loaded). Off creates only one GBA and normally uses the regular `.srm` save. |
| `mgba_dual_screen` | 1P / 2P | Whose screen and sound to show (host or solo = 1P, guest = 2P). It does not affect the emulation state. |
| `mgba_dual_use_bios` | ON / OFF | Use a BIOS file if one is present (set it the same on both devices). |
| `mgba_dual_skip_bios` | OFF / ON | Skip the BIOS intro screen (set it the same on both devices). |
| `mgba_dual_p2_nocart` | disabled / enabled | Single-pak: boot 2P without a cartridge (set it the same on both devices). |

Runtime files (all in the RAM disk `/tmp`; ignored if missing): `/tmp/hb_dual_screen` (`1P` or `2P`, checked every 30 frames) · `/tmp/hb_dual_p2rom` (path of the 2P ROM for pair games) · `/tmp/hb_ownsave/*` (the own-save exchange).

## Install on KNULLI

This is how we set it up on the RG35XX Pro. Adjust paths and names if your setup differs.

1. **Core file.** Put `mgba_dual_libretro.so` in `/userdata/system/hanbang_cores/` (default path used by the prebuilt files) on the SD card.
   Then point the read-only root's `/usr/lib/libretro/mgba_dual_libretro.so` at that file: run `mount -o remount,rw /`, then `ln -sfn /userdata/system/hanbang_cores/mgba_dual_libretro.so /usr/lib/libretro/mgba_dual_libretro.so`, and save with `knulli-save-overlay`.
   The core has a new name, so the stock mGBA core is left untouched.
2. **Core info file.** `/usr/share/libretro/info/mgba_dual_libretro.info`: copy the stock `mgba_libretro.info`, set `display_name = "Nintendo - Game Boy Advance (mGBA Dual)"` and `corename = "mGBA Dual"`, and save with `knulli-save-overlay`.
   Without it, the emulator launcher refuses to start the core and reports a missing `.info` file.
3. **ES feature table.** In ES's `es_features_*.cfg`, add `<core name="mgba_dual" features="netplay" />` inside the libretro `<cores>` block so the core shows up as a netplay core.
4. **Per-game core line** in `/userdata/system/knulli.conf`: `gba["<ROM file name>.zip"].core=mgba_dual`. Add it only for GBA games that use the link cable. Everything else keeps its usual core.
5. **Per-game option file** `/userdata/system/configs/retroarch/config/mGBA Dual/<ROM name>.opt`, which the game-start hook rewrites on every launch:
   ```
   mgba_dual_screen = "1P"          # "2P" for the guest
   mgba_dual_use_bios = "ON"
   mgba_dual_skip_bios = "ON"
   mgba_dual_p2_nocart = "enabled"  # single-pak games only
   ```
6. **BIOS.** `/userdata/bios/gba_bios.bin`, the **same file on both devices**. Single-pak games need a real BIOS.
7. **Helper scripts** from this repository's [`knulli-scripts/`](../../knulli-scripts/) folder. Copy them to `/userdata/system/claude/` (default path used by the prebuilt files), except for the hook:
   - [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) is the ES game start / stop hook, and it goes to `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files). It writes the `.opt` file and launches the scripts below. That folder should hold only this one executable, because on exFAT every file counts as executable.
   - [`hb_direct.py`](../../knulli-scripts/hb_direct.py) looks at the host / guest roles and writes `1P` or `2P` to `/tmp/hb_dual_screen`.
   - [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py) is the guest's prompt ("a room for the same game is open"). For pair games it also handles the 2P ROM (`/tmp/hb_dual_p2rom`) and sends the guest's save.
   - [`hb_ownsave.py`](../../knulli-scripts/hb_ownsave.py) runs the own-save exchange (request, confirmation, write-back).
   - [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py) writes the host's save to the card during netplay.
8. **Update both devices together**, because a state from a different build is refused. While no game is running, upload the new file next to the old one, check its md5, then swap it in.

### Other devices and operating systems

- This `.so` is for **aarch64 Linux only** (it uses glibc symbol versions up to GLIBC_2.35). On anything else, rebuild from the patches. A macOS arm64 build was made for test tooling; Windows and Android have not been tried.
- The state format **differs from stock mGBA** (fixed size: two cores, drivers and saves). You can't exchange states with the stock mGBA core, and two builds of this core refuse each other's states when the version field differs (`0x100` link timing, `0x200` pair, `0x400` no cartridge).
- The default is **the same ROM on both devices**. For pair games (different editions), the helper scripts have to create `/tmp/hb_dual_p2rom` and the host-side request (`HBQ4`). Without the scripts, that feature can't be used.
- **Own save, pair games and the guest side of single-pak are built around the helper scripts (`hb_ownsave.py`, `hb_joinask.py`) and the KNULLI launcher (RetroArch's log pipe).**
  If there are no files in `/tmp/hb_ownsave`, the core behaves as a plain two-GBA core (set `mgba_dual_screen=2P` by hand on the guest). It contains Linux-only code (it reads `/proc/self/cmdline` and `/proc/net/tcp`), so it has not been tested on other operating systems.
- Single-pak needs a **real GBA BIOS** (the same file on both devices) and `mgba_dual_use_bios=ON`. Without them, 2P boots from the pack as before (the same as 1.5).
- Running two GBAs in one core is **heavier than a single-GBA core**. On the H700 it is estimated at about 3.5 times real time, which left headroom for rewinding. Check slower devices yourself.
- Three- and four-player link, Wireless Adapter (RFU) games, e-Reader and GameCube link are out of scope and untested. (Pokémon FireRed / LeafGreen wireless is handled by the [`gba-gpsp-rfu`](../gba-gpsp-rfu/) core.)
- If the device hook rewrites the per-game `.opt` file wholesale, the single-pak line can disappear. The hook (`nds_save_sync.sh`) is set up to carry that line over.
- When you play alone, some games see the invisible 2P as connected: the link menu looks as if a partner were there.

## Build from source

This is exactly how it was built. The build machine was Debian 12 (aarch64, gcc 12.2, cmake 3.25).
The resulting `.so` links only libc and libm, uses glibc symbol versions up to GLIBC_2.35, and exports just the 25 `retro_*` symbols.

```sh
# the patches (this repository)
git clone https://github.com/Squirbie/handheld-link-cores.git
CORE="$PWD/handheld-link-cores/cores/gba-mgba-dual"

# upstream at the base commit
git clone https://github.com/libretro/mgba.git
cd mgba
git checkout 7a12d6d4b9acb14c0ae62c9166b6a2f3d08007f6

# (a) apply the patches one by one, in order
for p in $(grep -v '^#' "$CORE/patches/series"); do git apply "$CORE/patches/$p"; done
# (b) or apply the single combined patch instead (never both)
# git apply "$CORE/patches/all-in-one/mgba-dual-1.6-os4-vs-libretro-mgba-7a12d6d4.patch"

cmake -S . -B build -DLIBMGBA_ONLY=ON -DBUILD_LIBRETRO=ON -DLIBRETRO_DUAL=ON -DM_CORE_GB=OFF \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS=-mcpu=cortex-a53
cmake --build build --target mgba_libretro -j2
strip --strip-unneeded build/mgba_dual_libretro.so
```

- `-mcpu=cortex-a53` is for the RG35XX Pro (H700). Drop it or change it on other CPUs.
- The patches also apply with `patch -p1`.
- A different compiler will not produce a byte-identical `.so`. Check the version string instead (`1.6-os4 (mGBA 7a12d6d4)`).

### Reproducibility

- The upstream tree hash `8ccf4fd1929aafd9211b19d6dec771a33f43299a` matches GitHub's. Apart from a few code comments that were reworded afterward, the patched sources match the recorded build sources: patches 0001–0009 give the same tree as the development branch used for the build, and the intermediate stages match by file fingerprint (`libretro_dual.c`, `sio.c` and `lockstep.h` at the 1.3-os4 stage; `libretro_dual.c` and `hb_ownsave.h` at the 1.5 and 1.6 stages).
- `git apply` in order, `git apply` with the combined patch, and `patch -p1` in order all produce the same tree.
- **Not done:** the core was not recompiled when this folder was put together, so a byte-identical `.so` has not been confirmed. What was checked instead are the per-stage source fingerprints and the version string inside the `.so` (`1.6-os4 (mGBA 7a12d6d4)`).
- No copy of the complete final source tree survives (it only existed inside the build VM during development), so the changed files were compared by fingerprint.
- Porting to the latest stock mGBA has not been done.

## Patches

Apply them in this order. `patches/series` lists the same order. To apply everything at once, use only `patches/all-in-one/mgba-dual-1.6-os4-vs-libretro-mgba-7a12d6d4.patch` (using it together with the individual patches would apply the changes twice).

Base: libretro/mgba commit `7a12d6d4b9acb14c0ae62c9166b6a2f3d08007f6` (2026-09-16, "Libretro: Disable debug logging noise"), tree hash `8ccf4fd1929aafd9211b19d6dec771a33f43299a`.

Patches 0001–0005 are five commits from tangobattle/mgba (MPL-2.0). The original authors are credited in that repository's history.

| Patch | tangobattle/mgba commit | Date | Title |
|---|---|---|---|
| 0001 | `2db16a6053f7da68fc485589a4426825b6341f50` | 2026-07-17 | GBA SIO: cooperative-lockstep + savestate-exactness fork delta |
| 0002 | `7dc7c64a176bfcf4abfefe9aefe5e413246da771` | 2026-07-18 | GBA SIO: shared clocks survive the int32 cycle wrap (lockstep.c part only) |
| 0003 | `7bd57294a4af5b7998b043faacf80b2bb777cfcf` | 2026-07-20 | GBA Audio: savestates roundtrip the mix exactly |
| 0004 | `69a8ab2ee138c63449f17df0967adbe18760b560` | 2026-07-20 | GBA Audio: re-land the full decoded-PSG savestate exactness patch |
| 0005 | `89e7fd7ff21e369f325fba9ef8b486510a1eebc9` | 2026-07-20 | GBA Audio: restore the master-enable field on load |

| Order | File | What it does | Build after this step |
|---|---|---|---|
| 1 | [`0001-gba-sio-cooperative-lockstep-savestate-exactness.patch`](patches/0001-gba-sio-cooperative-lockstep-savestate-exactness.patch) | Cooperative lockstep and state exactness (tangobattle) | |
| 2 | [`0002-gba-sio-lockstep-int32-cycle-wrap.patch`](patches/0002-gba-sio-lockstep-int32-cycle-wrap.patch) | Shared clocks survive the int32 cycle wrap (tangobattle) | |
| 3 | [`0003-gba-audio-savestate-mix-roundtrip.patch`](patches/0003-gba-audio-savestate-mix-roundtrip.patch) | The sound mix survives a state round trip (tangobattle) | |
| 4 | [`0004-gba-audio-decoded-psg-savestate.patch`](patches/0004-gba-audio-decoded-psg-savestate.patch) | Save every decoded PSG value (tangobattle) | |
| 5 | [`0005-gba-audio-restore-master-enable.patch`](patches/0005-gba-audio-restore-master-enable.patch) | Restore the sound master-enable value (tangobattle) | |
| 6 | [`0006-libretro-add-mgba-dual-core.patch`](patches/0006-libretro-add-mgba-dual-core.patch) | The new frontend, `mgba_dual_libretro` | 1.0 |
| 7 | [`0007-dual-p2-save-name-inside-archive.patch`](patches/0007-dual-p2-save-name-inside-archive.patch) | Name the 2P save after the ROM inside an archive | |
| 8 | [`0008-gba-io-restore-rcnt-link-pins-on-load.patch`](patches/0008-gba-io-restore-rcnt-link-pins-on-load.patch) | Restore the RCNT link-pin bits | |
| 9 | [`0009-dual-p2-save-without-atomic-rename.patch`](patches/0009-dual-p2-save-without-atomic-rename.patch) | 2P save on file systems where rename can't replace a file | |
| 10 | [`0010-gba-sio-clock-selection-and-unprepared-peers.patch`](patches/0010-gba-sio-clock-selection-and-unprepared-peers.patch) | Clock selection and peers that aren't ready | |
| 11 | [`0011-gba-rollback-vram-contention-and-sio-events.patch`](patches/0011-gba-rollback-vram-contention-and-sio-events.patch) | Rewind: VRAM contention and SIO event order | |
| 12 | [`0012-dual-link-off-single-gba.patch`](patches/0012-dual-link-off-single-gba.patch) | The `mgba_dual_link` option | 1.1-rbfix |
| 13 | [`0013-dual-screen-file-runtime-selection.patch`](patches/0013-dual-screen-file-runtime-selection.patch) | Pick the 1P / 2P display from a file | 1.1-rbfix-screenfile |
| 14 | [`0014-dual-guest-own-save.patch`](patches/0014-dual-guest-own-save.patch) | A separate save for each player | 1.2-ownsave |
| 15 | [`0015-dual-ownsave-harden.patch`](patches/0015-dual-ownsave-harden.patch) | Twelve fixes from reviewing own save | 1.3-os4, md5 `818fa42f` |
| 16 | [`0016-gba-sio-link-timing-sd-and-start-bit.patch`](patches/0016-gba-sio-link-timing-sd-and-start-bit.patch) | Link timing (SD line and start bit 0) | 1.4-os4, md5 `4d4ab1c7` |
| 17 | [`0017-dual-zero-current-samples-in-link-states.patch`](patches/0017-dual-zero-current-samples-in-link-states.patch) | Zero the output-only sound sample count | 1.4.1-os4, md5 `2af4a20c` |
| 18 | [`0018-dual-pair-game-different-rom-for-2p.patch`](patches/0018-dual-pair-game-different-rom-for-2p.patch) | Pair games | 1.5-os4, md5 `2119a22f` |
| 19 | [`0019-dual-singlepak-2p-without-cartridge.patch`](patches/0019-dual-singlepak-2p-without-cartridge.patch) | Single-pak | 1.6-os4, md5 `df34be2b` |

- Each patch header (Subject, Origin, a short summary, then the description) says what was changed and why.
- The md5 values are the first eight hex digits of the `.so` built at that step. Those for the builds before `1.6-os4` come from our development log, and only the final build matches the file described here.
- A patch from our development series that was never deployed (it copied the 1P save into the 2P slot when 2P had none) is left out. The numbers above follow the shipped series.

## Upstream status

- Not checked: how libretro/mgba `master` has moved since the base commit (`7a12d6d`).
- **Worth sending upstream? No.** It isn't a standalone bug fix. The core of it (0001–0005) is tangobattle/mgba's cooperative lockstep code, and the other fixes only make sense on top of that code and the new `mgba_dual` frontend.
  Own save, pair games and single-pak depend on the KNULLI helper scripts, and they use reserved fields of the state format (such as the VRAM contention mask), so the states are not compatible with stock mGBA.
- If anything, the link-timing fix (SD line and start bit 0; patches 0010 and 0016) could be offered to tangobattle/mgba.

## License

- **MPL-2.0**, the same as mGBA (license text: [`LICENSES/mgba_LICENSE`](../../LICENSES/mgba_LICENSE)). The new files (`src/platform/libretro/dual/*`) carry MPL-2.0 headers, and the parts taken from tangobattle/mgba are MPL-2.0 too. The patches follow the upstream license.
- Keep the copyright notices in the upstream file headers (for example, mGBA's copyright holder) as they are. If you distribute the core (`.so`), you must also provide the source of the modified files. The upstream commit plus these patches are that source.
