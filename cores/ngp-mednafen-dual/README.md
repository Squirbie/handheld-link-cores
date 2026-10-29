<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# Beetle NeoPop Dual — the Neo Geo Pocket link cable for two devices

> A libretro core that runs two Neo Geo Pocket (Color) consoles joined by an emulated link cable inside one core, so link-cable battles can be played on two handhelds over RetroArch netplay.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/ngp-mednafen-dual-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| **Core file** | `mednafen_ngp_dual_libretro.so` — aarch64 Linux, 831,096 bytes (in the release zip, not stored in git) |
| **Version** | `1.2-os5 os5rtc` (core name `Beetle NeoPop Dual`, inner core `v1.29.0.0 os5rtc`) |
| **md5** | `91b8d251fbd72d776d1b2616b2a2b111` |
| **Upstream** | [libretro/beetle-ngp-libretro](https://github.com/libretro/beetle-ngp-libretro) @ [`139fe34`](https://github.com/libretro/beetle-ngp-libretro/commit/139fe34c8dfc5585d6ee1793a7902bca79d544de) ("tvos: properly set min supported version (#114)", 2024-10-21). This is the same commit as the stock core KNULLI ships, which reports `Beetle NeoPop v1.29.0.0-139fe34`. |
| **License** | GPL-2.0-or-later |
| **Tested on** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (the only environment checked) |

## What it does

The stock Beetle NeoPop core doesn't emulate the link cable, so link games such as The King of Fighters R-1 and R-2, SNK vs. Capcom: The Match of the Millennium and Card Fighters' Clash could not be played together. This core puts **two Neo Geo Pocket (Color) consoles inside one core** and wires them together by emulating serial channel 0 and the BIOS communication calls, so two handhelds can play them over RetroArch netplay. The host's screen shows console 1P; the guest's screen shows console 2P.

- **Stays in sync.** The clock (RTC), the flash (save) and the Z80 state are made deterministic for rollback netplay. Two of these fixes, the Z80 IRQ line and the merging of flash blocks, repair bugs that the stock single-console core has too.
- **Everyone keeps their own save.** The guest plays on their own save. **Pair games** put a different ROM into console 2P: Card Fighters' Clash (SNK edition ↔ Capcom edition) and Dive Alert (Becky edition ↔ Matt edition).
- **Tweaks for picky games:** Delta Warp (time packet), Card Fighters' Clash (starting VS mode) and Unitron (first-move draw).
- **Checked on two devices:** a versus match in SNK vs. Capcom: The Match of the Millennium, and the Tsunagete Pon battle mode. Delta Warp, Card Fighters' Clash and Unitron were checked on a virtual-machine test bench, and the core is installed on both devices.

### Good to know

- Both devices need the same core file and the same ROM. Pair games only work with their defined partner edition.
- With `ngp_dual_link` set to `on`, console 2P runs even when you play alone, and in games that switch on a link slot, such as KOF R-2, the screen looks a little different from stock (the game notices the partner console). With `off` the core behaves like stock NeoPop.
- Known limits: only games whose ROM communicates through the BIOS communication calls are emulated. Koi Koi Mahjong works with one player picking 1P and the other picking 2P. Some Korean-patched ROMs overflow the on-screen link messages (the Korean Card Fighters' Clash 2 needed a one-byte ROM fix; that is not a core problem).

## What we changed

1. **`mednafen/ngp/hb_link.c`, the link cable.** When the link is on, it emulates serial channel 0 (SC0BUF, SC0CR, SC0MOD and BR0CR; RTS at 0xB2; the CTS handshake; INTRX0 at `0x6FE4` and INTTX0 at `0x6FE8`) and implements the BIOS communication calls (COM*) on ring buffers in the BIOS work RAM (`0x6C80`, `0x6CC0` and `0x6D00` to `0x6D06`). The RTC reads "base time + emulated cycles" (saved in the state) instead of the host clock. With the link off, the core behaves like stock NeoPop.
2. **The `dual/` front end.** The inner objects are merged with `ld -r`, and `objcopy --redefine-syms` prefixes every global name with `ngpA_` or `ngpB_` to make two copies (`dual/Makefile.dual`). The consoles run in turns, line by line, with a fixed-size state and a 1P/2P screen option. Only 25 `retro_*` functions are exported.
3. **Deterministic states.** The Z80 IRQ line (`iline`) is saved in the state (0001). The `FIXME std::max` in `flash_optimise_blocks`, which shrank an erased 32 KB sector to a few hundred bytes, is fixed; loading a state without flash data restores the ROM and the block list; and a pending flash command is saved (0003). The state header carries a ROM fingerprint, so states made with another ROM or another 2P edition are refused (0004).
4. **Option text (0005).** `;` becomes `,` in the option descriptions. RetroArch cuts a description from its value list at the first `;`, and it was cutting in the wrong place.
5. **BIOS default serial handlers (0006).** `COMINIT` installs HLE handlers at the user vectors `0x6FE4` and `0x6FE8` and sets `INTES0=0x66`. Games that call only `COMINIT` (Pocket Tennis, Tsunagete Pon, Magical Drop, Samurai Shodown 2 and others) used to stall after the first byte; this fixes that.
6. **Per-player saves and pair games (0007, version 1.1-os4).** The guest plays on their own save, and a pair game can run a different ROM in console 2P.
7. **os5 (0008 to 0010).** INTTX0 is raised when the transmit buffer empties (Delta Warp's time packet). `COMRECIVESTART` also asserts RTS (Card Fighters' Clash, "press A on either side"). When the 64-byte send ring is full, `COMCREATEDATA` returns `RA3=0xFF` (starting VS mode in Card Fighters' Clash).
8. **os5rtc (0011).** Console 2P's clock runs 3 seconds behind console 1P's (`HB_P2_RTC_SKEW`). A game that seeds its random numbers from the RTC (Unitron) used to draw identical numbers on both consoles and tie the first-move draw forever.

Names and comments containing `hb_` or `hanbang` only mark the places we changed; nothing was renamed.

## Core options

The first value is the default.

| Option | Values | What it does |
|---|---|---|
| `ngp_dual_screen` | `1P` · `2P` | Whose picture and sound you get (host or solo = 1P, guest = 2P). |
| `ngp_dual_link` | `on` · `off` | Runs console 2P on the link cable. `off` = solo, one console. Takes effect after a restart. |
| `ngp_dual_language` | `english` · `japanese` | Language of both consoles. Takes effect after a restart. |
| `ngp_dual_p2_rom` | `same` · `partner` | Console 2P's cartridge. `partner` = the other edition of a pair game, taken from `/tmp/hb_ngp_dual_p2.ngc`. Takes effect after a restart. |

**Files in `/tmp`** (the core runs normally when they don't exist): `/tmp/hb_ownsave/` (the transaction folder for per-player saves), `/tmp/hb_dual_p2rom` (the pair game's console-2P ROM) and `/tmp/hb_dual_screen` (picture and sound selection). The core reads ROMs as plain files, so the hook unpacks ZIPs into `/tmp`.

**Saves.** Console 1P uses the same `.flash` file as the stock core; console 2P uses `<ROM name>.p2.flash` on the host. The guest's device doesn't write a save when it finishes: its own save goes into the host's console-2P slot in per-player save mode (kind 3) and comes back afterwards.

## Install on KNULLI

Put the **same `.so`** on both devices. Download `ngp-mednafen-dual-linux-aarch64.zip` from the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest), unzip it, and install with no game running.

**Before you start**

- The prebuilt `.so` is for **aarch64 Linux**: it only uses glibc 2.34 or older symbols and needs `libstdc++`, `libgcc_s` and `libc`. For another CPU or OS, rebuild it from the patches.
- Only **KNULLI + RetroArch 1.22.2** has been checked.
- Per-player saves, pair games and the screen file switch on only when the KNULLI hook writes files into `/tmp`. Without those files the core runs the plain way: the host's 1P `.flash` plus `.p2.flash`.
- Check the unzipped file: md5 as above, sha256 `3eb30e50c31cbd6d8c92794969736507454ff905d54e42096ea42aa65c54d5a3`.

**Steps**

1. Copy the core to SD storage, into `/userdata/system/hanbang_cores/` (default path used by the prebuilt files), and put a symlink in `/usr/lib/libretro/`. The new file name leaves the stock `mednafen_ngp_libretro.so` untouched.
   ```sh
   mkdir -p /userdata/system/hanbang_cores
   cp mednafen_ngp_dual_libretro.so /userdata/system/hanbang_cores/ && chmod 755 /userdata/system/hanbang_cores/mednafen_ngp_dual_libretro.so
   mount -o remount,rw /
   ln -sfn /userdata/system/hanbang_cores/mednafen_ngp_dual_libretro.so /usr/lib/libretro/mednafen_ngp_dual_libretro.so
   ```
2. **Core info file.** Without it the launcher refuses to run the core. Copy the stock info file, change the names, and save the overlay (KNULLI's `/usr` is an overlay, so the symlink from step 1 also needs this to survive a reboot):
   ```sh
   I=/usr/share/libretro/info
   sed -e 's/^display_name = .*/display_name = "SNK - Neo Geo Pocket \/ Color (Beetle NeoPop Dual)"/' \
       -e 's/^corename = .*/corename = "Beetle NeoPop Dual"/' $I/mednafen_ngp_libretro.info > $I/mednafen_ngp_dual_libretro.info
   knulli-save-overlay
   ```
3. **Pick the core per game** in `/userdata/system/knulli.conf`: `ngpc["<ROM file name>.zip"].core=mednafen_ngp_dual` (use `ngp[...]` for monochrome games).
4. **Show "start netplay game" in ES.** Add one line to the ES feature table (`es_features_*.cfg`): `<core name="mednafen_ngp_dual" features="netplay" />`. The "start netplay game" entry (hold A on a game) then shows up.
5. **Game-start hook.** Each time a game starts, the hook writes `config/Beetle NeoPop Dual/<ROM name>.opt` with the host or solo player on `1P`, the guest on `2P`, `ngp_dual_link = "on"` and `ngp_dual_p2_rom = "same"`. For a pair game, the guest's join prompt sends its own edition's save and the partner ROM, and the host's core swaps console 2P's ROM at that moment. The hook is block 21 of [`knulli-scripts/nds_save_sync.sh`](../../knulli-scripts/).
   - Install it as `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files), and keep that folder to this one file, because KNULLI runs every file in it.
   - The helper scripts in the same folder go to `/userdata/system/claude/` (default path used by the prebuilt files): `hb_ownsave.py` (per-player saves) and `hb_joinask.py` (the join-or-play-solo prompt).
6. **Screen settings.** Copy the stock core's screen settings (`Beetle NeoPop.cfg` and the `.glslp` file) to names starting with `Beetle NeoPop Dual.` and your shaders and screen position carry over.
7. **Undo.** Delete the symlink, run `knulli-save-overlay`, and remove the `knulli.conf` line. The stock core is untouched.

## Build from source

```sh
git clone https://github.com/libretro/beetle-ngp-libretro
cd beetle-ngp-libretro
git checkout 139fe34c8dfc5585d6ee1793a7902bca79d544de
PATCHES=/path/to/handheld-link-cores/cores/ngp-mednafen-dual/patches
for p in "$PATCHES"/*.patch; do patch -p1 < "$p" || break; done
nice make -j1 -f dual/Makefile.dual GIT_VERSION=os5rtc      # Debian 12 aarch64, gcc 12
# -> build_dual/mednafen_ngp_dual_libretro.so   (a single-console test build, mednafen_ngp_hb_libretro.so, appears next to it)
```

- `ARCH_FLAGS` defaults to `-mcpu=cortex-a53` (tuned for the RG35XX line, H700). Set `ARCH_FLAGS=` to change it for another CPU.
- The `GIT_VERSION` text becomes part of the version the core reports, `1.2-os5 <text>`. It must be the same on both devices, and together with `1.2-os5` it can be at most 32 bytes including the terminator (checked at compile time).
- The Makefile relies on GNU binutils (`ld -r` and `objcopy`), so it has only been checked on Linux.

## Patches

Apply the files in `patches/` **in file-name order**, one at a time.

| Order | File | What it does |
|---|---|---|
| 1 | `0001-NGP-save-the-Z80-IRQ-line-in-savestates.patch` | Saves the Z80 IRQ line in savestates. |
| 2 | `0002-NGP-Dual-link-cable-for-two-consoles-in-one-core.patch` | Serial channel 0, the BIOS communication calls, a deterministic clock, a line-stepped API and the two-console front end. |
| 3 | `0003-NGP-deterministic-flash-state-rollback-netplay.patch` | Makes the flash state deterministic for rollback netplay. |
| 4 | `0004-NGP-Dual-refuse-states-made-with-other-ROMs.patch` | Puts a ROM fingerprint in the state header; states made with other ROMs are refused. |
| 5 | `0005-NGP-Dual-option-descriptions-use-instead-of.patch` | `;` becomes `,` in option descriptions, so RetroArch no longer cuts the value list in the wrong place. |
| 6 | `0006-NGP-Dual-BIOS-default-serial-handlers-at-COMINIT.patch` | `COMINIT` installs the BIOS default serial handlers. |
| 7 | `0007-NGP-Dual-1.1-os4-guest-own-save-kind-3-and-NGP-partner-pairs.patch` | Per-player saves (kind 3) and pair games (1.1-os4). |
| 8 | `0008-NGP-Dual-1.2-os5-INTTX0-when-the-transmit-buffer-emp.patch` | INTTX0 is raised when the transmit buffer empties (1.2-os5). |
| 9 | `0009-NGP-Dual-1.2-os5-COMRECIVESTART-asserts-RTS.patch` | `COMRECIVESTART` also asserts RTS. |
| 10 | `0010-NGP-Dual-1.2-os5-COMCREATEDATA-returns-FF-when-the-s.patch` | `COMCREATEDATA` returns `0xFF` when the send ring is full. |
| 11 | `0011-os5rtc-p2-rtc-skew.patch` | Console 2P's clock runs 3 seconds behind console 1P's (`os5rtc`, the final version). |

- `0011` was originally named `os5_p2_rtc_skew.patch`. It was renamed so it applies in order; the content is the same.
- Source provenance: `139fe34` plus patches 0001 to 0010 is the `hb_dual` branch at `7b5d908`, and the final core is that source plus 0011.
- Some comments inside the patches are in Korean; they were left as written.
- **Checked on 2026-10-29 (on a Mac).** Reverse-applying the 10 patches gave 12 original files whose git blob hashes all matched the `index` lines in the patches, and applying them forward again matched all 37 files. `0011` applies with no fuzz, and the result's hash equals the patch's `516a654`. During development, two builds with `GIT_VERSION=7b5d908` came out identical (md5 starting `3c1499b5`), and os5rtc, rebuilt with the same tools, came out as `91b8d251`.

## Upstream status

Worth sending: savestate bugs that also exist in the stock single-console core. They show up as desyncs in rewind, run-ahead and netplay.

1. **The Z80 IRQ line is missing from the savestate** (patch 0001). Upstream master is unchanged here (checked 2026-10-29).
2. **`flash_optimise_blocks` shrinks erased 32 KB blocks** because of its `FIXME std::max` (patch 0003). Upstream master is unchanged here too (checked 2026-10-29).
3. **Loading a state that has no flash data** does not restore the ROM and the block list (patch 0003; not checked against master).

Patch 0003 mixes in our `hb_link.c` part, so only the `flash.c`, `system.c` and `rom.c` changes should be extracted and sent. Draft title: "Savestate fixes for rollback/run-ahead: save the Z80 IRQ line, fix flash block merging, restore ROM/flash on load". The English draft text is in [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) under `upstream_pr_candidate`.

The two-console front end, the link and the per-player saves are specific to this setup, so they will not be sent.

## License

- Upstream Beetle NeoPop (Mednafen NeoPop) is **GPL-2.0-or-later**: its `COPYING` is GPLv2 and the file headers say "version 2 … or (at your option) any later version". A copy of the license text is in [`LICENSES/beetle-ngp-libretro_COPYING`](../../LICENSES/beetle-ngp-libretro_COPYING). The patches follow those terms, and the newly written `hb_link.c`, `hb_link.h` and `dual/libretro_dual.c` carry the same GPL header.
- `dual/hb_ownsave.h`, `hb_storage.h` and `hb_romfile.h` have no separate header. They are combined into the same core, so they are released under the same terms as the core (written for this project).
- If you distribute binaries that contain this core, you must also publish the modified source — these patches.
