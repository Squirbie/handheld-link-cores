<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# blueMSX — saves that stick, disk swaps that work, netplay that stays in sync

> Three fixes for the libretro blueMSX core: in-game saves are written to disk, the next/previous-disk hotkey works under RetroArch 1.22, and save states are complete and byte-stable, so two devices stay in sync over netplay.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/msx-bluemsx-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| **Core file** | `bluemsx_libretro.so` — aarch64 Linux, 1,685,216 bytes (in the release zip, not stored in git) |
| **Version** | `git 572c918-hbnp1` |
| **md5** | `83032767d18ac489157269e56e770cd1` |
| **Upstream** | [libretro/blueMSX-libretro](https://github.com/libretro/blueMSX-libretro) @ [`572c918`](https://github.com/libretro/blueMSX-libretro/commit/572c91856a5288b7433c619af651e31f00f3ce7e) ("Merge pull request #182 from jfroco/master", 2024-12-04). This is the same commit as the stock core KNULLI ships, which reports `git-572c918`. |
| **License** | Per file: BSD-style for blueMSX's own files, plus some GPL, ZLIB and freeware files (see upstream `license.txt` and the License section below) |
| **Tested on** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (the only environment checked) |

## What it does

The libretro port of blueMSX (MSX and MSX2) had three problems on a handheld. This build fixes all three.

1. **In-game saves are kept.** When you quit, the cartridge's battery SRAM and flash were never written to a file, so saves inside Koei titles and similar games were gone after a restart.
2. **The disk-swap hotkey works.** In multi-disk games, RetroArch 1.22's "next/previous disk" did nothing.
3. **Two devices stay in step during netplay.** Saving and loading states mishandled timers, the board, the floppy head and sound-chip state, so the scenes on the two devices drifted apart.

### Good to know

- Both devices need the **same core, BIOS, ROM database and settings**. For example, if a 60 Hz setting exists on only one device, the other runs at 50 Hz.
- Remaining risks:
  - On MSX2, the first 1 or 2 video frames after a load look different (cosmetic only).
  - The *contents* of flash and disk saves are not part of the state.
  - CMOS is taken from the host, so the guest's `MSX2.cmos` is also written with the host's values.
  - Keyboard input from key files (`.keys`) may not reach the core during netplay (judged from the source; unconfirmed).
  - A few rare sound states are still not fixed: VLM5030, Majutsushi, turboR PCM and the printer DAC.
- The netplay host uses about 217 MB of memory, the same as before.

## What we changed

1. **Write SRAM and flash on unload, and fix the disk tray (patch 01, `libretro.c`).**
   - `retro_unload_game` never tore the board down, so the mappers' `destroy` callbacks (which call `sramSave()`) never ran. It now calls `boardInfo.destroy()`, so battery SRAM and flash (Koei titles, ASCII8/16 SRAM, MegaFlashROM and others) are written to the save folder. Upstream's latest master has no such call either (checked 2026-10-29).
   - `get_eject_state()` always reports "open". RetroArch 1.22 doesn't change the disk index while the tray is closed, so a single press of the hotkey did nothing. This is a workaround for the handheld setup.
2. **Load saved flash (patch 02, `AmdFlash.c` and `MegaromCartridge.c`).**
   - At startup the saved `.sram` is now read *after* the ROM is copied. That code had been disabled with `#if 0`, so the flash saved last time was overwritten by the empty area inside the ROM.
   - `MegaFlashRomSccPlus` allocates 2 MB of flash when the ROM is larger than 1 MB (for Korean-converted games on Yamanooto-style flash cartridges).
3. **hbnp1: state fixes for netplay and rewind (patch 03).** It touches 158 files, with about 750 lines added and 180 removed. Of those, 153 spots are `malloc` changed to `calloc` (uninitialized memory used to end up in the state); the rest add state items, clean up timers and so on.
   - Game progress drifted apart because:
     1. `retro_unserialize` loaded the device state but did not clear the timers, so timers from the pre-load timeline fired at the wrong time. (blueMSX's own rewind calls `boardTimerCleanup` first.)
     2. The board's pending-interrupt slot and its 64-bit time were not restored.
     3. Timers whose time had passed but had not fired yet were dropped on load. (The sound mixer's timer could stop forever.)
     4. The floppy controller WD2793 saved `diskTracks[0]` but read `diskTracks0`, so the head position always came back as 0. This is why the RAM of M.U.L.E. drifted. **It is still in upstream's latest master (checked 2026-10-29).**
     5. The RTC mode and CMOS contents were missing from the state.
   - State bytes and sound were not stable because:
     6. Garbage got into the state: file-name fields, 4-byte alignment padding, the machine name, uninitialized memory (about 150 `malloc` spots and the C++ sound-chip objects), and a "saved at" timestamp stored in every state (it differed per device and per second). For the C++ objects, a **new file, `Src/Libretro/HbZeroNew.cpp`** (included in the patch), makes the global `operator new` return zero-filled memory. This is a blunt workaround that only works inside this core; for upstream, clearing the members in the constructors is the right fix.
     7. Sound-side fields were missing from the state: the mixer (time, pending samples, timer), DAC and key click, SCC, the MSX-AUDIO resampling position, the OPL noise generator (rand), the floppy sound motor, and the MSX-MUSIC feedback and output filter.
   - Safety:
     8. The 2 MB state buffer size was not checked when saving (an MSX2 state is 1.76 MB, so there is little headroom).
     9. The in-memory zip file-count limit was 64; beyond that, device state was silently dropped.
   - States made with the previous core still load in the new core.

**RetroArch 1.22.2's state check (verified from its source).** The host sends a CRC of the whole state buffer (2 MB). If the guest's first comparison fails, the guest turns the check off for the rest of the session; if the CRC arrives late, the guest asks for the whole state every time it mismatches. With the old core the state bytes always differed, so drift either could not be corrected or was re-synced over and over.

Names and comments containing `hb_` or `hanbang` only mark the places we changed; nothing was renamed.

### Test results (development test bench)

A harness ran the core directly, without RetroArch, and recorded screen, sound, RAM and state fingerprints on every frame. It ran 8 games (Champion Pro Wrestling, Butamaru Pants, Rise Out, Brother Adventure, Arkanoid 2, Hole in One Special, M.U.L.E. (a disk game) and Rune Master 3) for 3,600 frames each. The runs included late joins (the guest receives the host's state), rewinds (guest-style and host-style), save then load, and a one-hour difference between the devices' clocks.

- **Before the fix:** the state bytes of the same scene differed, sound differed after joins and rewinds, and M.U.L.E.'s RAM kept drifting from frame 1,724 on.
- **After the fix:** the four MSX1 games match in screen, RAM, sound and state bytes. The four MSX2 games match in RAM and sound, and only the **first 1 or 2 video frames after a load** differ (putting the video buffer in the state would push it past 2 MB, so it is left out). The RTC time is taken from the host at join.
- **On two devices:** in one Champion Pro Wrestling netplay session the title and match screens matched, and there was no drift for 12 seconds, even past the state-check interval (600 frames). Other games were not tested on the devices one by one; only a representative session was checked.

## Core options

This build adds no core options; the settings are the stock blueMSX options.

## Install on KNULLI

**Replace the stock core under its stock name.** Then every MSX game starts with this core, and you don't have to touch `.info` files, ES features or `knulli.conf`. Put the **same file** on both devices (if the versions differ, netplay drifts apart). Download `msx-bluemsx-linux-aarch64.zip` from the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest), unzip it, and install with no game running.

**Before you start**

- The prebuilt `.so` is for **aarch64 Linux**: it only uses glibc 2.33 or older symbols and needs `libstdc++`, `libm` and `libc`. For another CPU or OS, rebuild it from the patches.
- Only **KNULLI + RetroArch 1.22.2** has been checked.
- Before installing, compare the cores, RetroArch, BIOS, ROM database and `blueMSX.cfg` of the two devices, read-only. We compared 108 items and found 2 differences (a ROM missing on one device, and the CMOS file), then went ahead.
- Check the unzipped file: md5 as above, sha256 `9186b7b9d2ca7149bf42cef2134e12fdef7f03ab98813096356ce669ebd37228`.

**Steps.** Copy the file into `/userdata/system/hanbang_cores/` (default path used by the prebuilt files) and point the stock name at it:

```sh
HB=/userdata/system/hanbang_cores/bluemsx_libretro.so
LINK=/usr/lib/libretro/bluemsx_libretro.so
mkdir -p /userdata/system/hanbang_cores
cat > $HB.hbnew < bluemsx_libretro.so          # check the md5 of the copied file before running the next line
chmod 755 $HB.hbnew
[ -L $LINK ] || cp -p $LINK $HB.old            # if it is a real file inside the overlay, keep the old core on the SD card
mv -f $HB.hbnew $HB
mount -o remount,rw /
ln -sfn $HB $LINK
knulli-save-overlay                             # keeps the symlink after a reboot
```

- **Undo:** put the old core you kept back in the same place and re-point the link (`ln -sfn …`).
- In-game saves end up as `<ROM name>.sram` in `/userdata/saves/msx1` and `/userdata/saves/msx2`.

## Build from source

```sh
git clone https://github.com/libretro/blueMSX-libretro
cd blueMSX-libretro
git checkout 572c91856a5288b7433c619af651e31f00f3ce7e
PATCHES=/path/to/handheld-link-cores/cores/msx-bluemsx/patches
for p in "$PATCHES"/*.patch; do patch -p1 < "$p" || break; done
make -f Makefile.libretro platform=unix GIT_VERSION=" 572c918-hbnp1" -j2     # Debian 12 aarch64, gcc 12.2.0
# -> bluemsx_libretro.so
```

- `GIT_VERSION` becomes the version text the core reports (`git` plus this text). It must be the same on both devices.
- During development the same source was built in a VM (Debian 12 aarch64, gcc 12.2.0). Upstream's `Makefile.libretro` sets `CFLAGS` and `CXXFLAGS` with `:=` (`-std=gnu89`, `-std=gnu++98` and so on), so environment variables can't override them; if you need CPU flags, add them in that file. The VM build script is not in this repository, so the command above was put together from upstream's Makefile and may differ slightly from what was run.

## Patches

Apply the files in `patches/` **in number order**, one at a time, from the top of the source tree with `patch -p1`.

| Order | File | What it does |
|---|---|---|
| 1 | `01-sramflush-disk.patch` | Writes SRAM and flash when the content is unloaded; the disk tray always reports "open". |
| 2 | `02-flashsave.patch` | Loads saved flash after the ROM copy; 2 MB flash for large `MegaFlashRomSccPlus` ROMs. |
| 3 | `03-hbnp1-netplay-sync.patch` | Netplay and rewind state fixes (hbnp1). |

- Patch 03 goes **on top of** 01 and 02. According to the development notes, applying 01, 02 and 03 to a clean `572c918` and building again gives the same `83032767` core.
- An earlier core was built from 01 and 02 with zig/clang; the same source built with gcc matched it in screen and RAM fingerprints over 8 games × 3,600 frames (only one frame of MSX2 first-frame sound differed). That is how the two builds were confirmed to be the same version.
- The three `#` lines at the top of `02-flashsave.patch` are a description header that `patch` ignores.
- **Not verified:** the patches could not be re-applied from scratch when this folder was prepared, because no upstream source tree was at hand. Instead, upstream's file contents were checked on the web (`retro_unload_game` in `libretro.c` and the `diskTracks` tags in `WD2793.c`; both upstream `572c918` and master are as described above). Run `git apply --check` or `patch --dry-run -p1` first.

## Upstream status

Worth sending, but not as one piece: patch 03 touches 158 files, which is hard to accept in one go, so it should go upstream in three parts.

- **A. Write battery-backed SRAM and flash when the content is unloaded** (patch 01). Neither upstream `572c918` nor master calls `boardInfo.destroy()` (checked 2026-10-29).
- **B. WD2793 saves `diskTracks[0]` but reads `diskTracks0`** (patch 03). Both versions are the same here (checked).
- **C. Make save states complete and byte-stable** (patch 03): timer, board and sound-chip state is missing or polluted, which breaks netplay and rewind.

Two things must change before sending: the "tray always open" change in patch 01 is a RetroArch 1.22 workaround and should be dropped, and `HbZeroNew.cpp` in patch 03 (a zero-filling global `operator new`) is our own workaround and should become clearing the members in the constructors. Draft title: "Save battery-backed SRAM/flash on unload, fix the WD2793 state tag typo, and make savestates complete and byte-stable". The English draft text is in [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) under `upstream_pr_candidate`.

## License

- The upstream blueMSX source tree has **different licenses per file** (upstream `license.txt`; a copy is in [`LICENSES/blueMSX-libretro_license.txt`](../../LICENSES/blueMSX-libretro_license.txt)): files by the blueMSX team carry BSD-style terms, `Fmopl`, `Ymdeltat` and the `OpenMsx*` / `R800Dasm` files that came from openMSX are GPL, `TinyXML` and `Unzip` are ZLIB, `V9938` is freeware, and the `Scale2x` family is BSD.
- The patches follow the **original terms of each file they change**. The combined binary contains GPL files, so it is treated as subject to the GPL's source-disclosure terms, and these patches plus the base-commit information are published as the source.
