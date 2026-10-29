<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# Genesis Plus GX GG Dual — Gear-to-Gear cable play for two devices

> A libretro core that runs two Game Gear consoles joined by an emulated Gear-to-Gear cable inside one core, so link-cable games can be played on two handhelds over RetroArch netplay.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/gg-genesisplusgx-dual-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| **Core file** | `genesisplusgx_gg_dual_libretro.so` — aarch64 Linux, 11,984,232 bytes (in the release zip, not stored in git) |
| **Version** | `1.1-os4-302fe82` (inner core `v1.7.4-302fe82`) |
| **md5** | `2db4468dac16b8754d268e90348639a0` |
| **Upstream** | [libretro/Genesis-Plus-GX](https://github.com/libretro/Genesis-Plus-GX) @ [`302fe82`](https://github.com/libretro/Genesis-Plus-GX/commit/302fe82fccbe2e036c3e13891db6513982a497ac) ("[Core/MD] improved invalid SRAM header info detection", 2024-02-27). This is the commit KNULLI's genesisplusgx package points to (the stock core reports `v1.7.4-302fe82`). The same commit is also in the author's own repository, [ekeeke/Genesis-Plus-GX](https://github.com/ekeeke/Genesis-Plus-GX). |
| **License** | Genesis Plus GX License: **non-commercial, so it may not be sold**, and modified versions must ship complete source (see upstream `LICENSE.txt` and the License section below) |
| **Tested on** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (the only environment checked) |

## What it does

The stock Genesis Plus GX core only stores the values written to the Game Gear's extension port (0x01 to 0x06). It never passes them to a partner, and it has no NMI, so link-cable games could not be played together. This core puts **two Game Gears inside one core** and emulates the Gear-to-Gear cable between them (a cross-wired parallel port, a serial UART and the NMI), so two handhelds can play them over RetroArch netplay. The host's screen shows console 1P; the guest's screen shows console 2P.

- **Stays in sync.** The two consoles run in turns, one scanline at a time. If both press the same button in the same frame, console 2P is delayed by one frame, so rollback netplay doesn't drift.
- **Everyone keeps their own save.** Per-player save mode (kind 4) lets the guest play on their own save, for games like Last Bible Special where the link only opens when a save exists.
- **Checked on two devices:** Sonic Drift 2 VERSUS, with each player driving their own car. On a virtual-machine test bench, Super Columns, Pac-Attack, Super Monaco GP and the LINK GAME of Fatal Fury Special, among others, also reached the start of a link battle with independent control.

### Good to know

- Both devices need the same core file and the same ROM.
- With `gg_dual_link` set to `on`, console 2P runs even when you play alone. Games whose menu changes when a cable is present, such as Super Monaco GP, then offer a "1PLAYER / 2PLAYERS" choice. Playing solo ran at about 59 frames per second on the device, which is fine. Set the option to `off` for stock behavior.
- Known limits: the parallel-port handshake and the serial model follow documentation, and have not been compared against a real Game Gear. Games like Last Bible Special, where the link only opens when a save exists, need a save.

## What we changed

1. **The cable and line-stepped execution (0001).** The cable model `core/hb_gglink.h`; ports 0x01 to 0x05 in `io_ctrl.c`; a line-stepped `system_frame_sms` in `system.c`; `retro_run` split into pieces plus `hb_gg_*` functions in `libretro/libretro.c`; and the two-console front end in `dual/` (`libretro_dual.c`, `build_dual.sh`, `link_dual.T`). The front end merges the inner objects with `ld -r` and uses `objcopy --redefine-syms` to prefix every global name with `ggA_` or `ggB_`, making two copies. Only 25 `retro_*` functions are exported.
2. **Serial as a plain UART (0002).** A received byte overwrites the previous one, and the NMI fires only when "received and enabled" goes from 0 to 1. A same-frame button press delays console 2P by one frame. Also adds a line-step test path and statistics.
3. **Option text (0003).** `;` becomes `,` in an option description (one byte). RetroArch cut the value list at the first `; `, so the menu showed `restart); on`.
4. **Per-player saves (0004, version 1.1-os4).** `dual/hb_ownsave.h`, `hb_storage.h` and `hb_romfile.h` (the same modules as the Neo Geo Pocket and WonderSwan dual cores) plus changes in `libretro_dual.c`. When the host receives a request (HBQ3), it puts the guest's `.srm` into console 2P's save RAM and restarts console 2P. The guest (`--connect`) reports a `RETRO_MEMORY_SAVE_RAM` size of 0, so RetroArch neither reads nor writes the guest's 1P save; the core saves midway and exports at the end only once it is confirmed as player 2.

Names and comments containing `hb_` or `hanbang` only mark the places we changed; nothing was renamed.

## Core options

The first value is the default.

| Option | Values | What it does |
|---|---|---|
| `gg_dual_screen` | `1P` · `2P` | Whose picture and sound you get (host or solo = 1P, guest = 2P). |
| `gg_dual_link` | `on` · `off` | `off` gives the stock single-console behavior. Read only when a game starts. |

**Saves.** Console 1P uses `.srm`; console 2P uses `<ROM name>.p2.sav` on the host. The state is both consoles plus a ROM fingerprint (about 295 KB, fixed size).

## Install on KNULLI

Put the **same `.so`** on both devices. Download `gg-genesisplusgx-dual-linux-aarch64.zip` from the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest), unzip it, and install with no game running.

**Before you start**

- The prebuilt `.so` is for **aarch64 Linux**: it only uses glibc 2.34 or older symbols and needs `libm` and `libc`. For another CPU or OS, rebuild it from the patches. The build relies on GNU binutils (`ld -r` and `objcopy`), so it has only been checked on Linux.
- Only **KNULLI + RetroArch 1.22.2** has been checked.
- Per-player saves switch on only when the KNULLI hook writes files into `/tmp/hb_ownsave/`. Without them the core runs the plain way: the host's 1P `.srm` plus `.p2.sav`.
- Check the unzipped file: md5 as above, sha256 `5232650917d039247e0f67e2dea0bd0c579287a3ec56b0b39fa6a5151c5ef595`.

**Steps**

1. Copy the core to SD storage, into `/userdata/system/hanbang_cores/` (default path used by the prebuilt files), and put a symlink in `/usr/lib/libretro/`. The new file name leaves the stock `genesisplusgx_libretro.so` untouched.
   ```sh
   mkdir -p /userdata/system/hanbang_cores
   cp genesisplusgx_gg_dual_libretro.so /userdata/system/hanbang_cores/ && chmod 755 /userdata/system/hanbang_cores/genesisplusgx_gg_dual_libretro.so
   mount -o remount,rw /
   ln -sfn /userdata/system/hanbang_cores/genesisplusgx_gg_dual_libretro.so /usr/lib/libretro/genesisplusgx_gg_dual_libretro.so
   ```
2. **Core info file.** Without it the launcher refuses to run the core. Copy the stock Genesis Plus GX info file to `/usr/share/libretro/info/genesisplusgx_gg_dual_libretro.info`, change its `display_name` to `"Sega - Game Gear (Genesis Plus GX GG Dual)"`, and run `knulli-save-overlay` (KNULLI's `/usr` is an overlay, so the symlink from step 1 also needs this to survive a reboot).
3. **Pick the core per game** in `/userdata/system/knulli.conf`: `gamegear["<ROM file name>.zip"].core=genesisplusgx_gg_dual`
4. **Show "start netplay game" in ES.** Add one line to the ES feature table (`es_features_*.cfg`): `<core name="genesisplusgx_gg_dual" features="netplay" />`
5. **Game-start hook.** Each time a game starts, the hook writes `config/Genesis Plus GX GG Dual/<ROM name>.opt` with the host or solo player on `1P`, the guest on `2P`, and `gg_dual_link = "on"`. The hook is block 22 of [`knulli-scripts/nds_save_sync.sh`](../../knulli-scripts/).
   - Install it as `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files), and keep that folder to this one file, because KNULLI runs every file in it.
   - The helper scripts in the same folder go to `/userdata/system/claude/` (default path used by the prebuilt files): `hb_ownsave.py` (per-player saves) and `hb_joinask.py` (the join-or-play-solo prompt).
6. **Screen settings.** Copy the stock core's screen settings (`gamegear.cfg` and the `.glslp` file) into `config/Genesis Plus GX GG Dual/` and your shaders and screen position carry over.
7. **Undo.** Delete the symlink and the info file, run `knulli-save-overlay`, and remove the `knulli.conf` line. The stock core is untouched.

## Build from source

```sh
git clone https://github.com/libretro/Genesis-Plus-GX
cd Genesis-Plus-GX
git checkout 302fe82fccbe2e036c3e13891db6513982a497ac
PATCHES=/path/to/handheld-link-cores/cores/gg-genesisplusgx-dual/patches
for p in "$PATCHES"/*.patch; do patch -p1 < "$p" || break; done
nice bash dual/build_dual.sh "-302fe82"     # Debian 12 aarch64, gcc 12
# -> build_dual/genesisplusgx_gg_dual_libretro.so   (a single-console test build, genesis_plus_gx_hb_libretro.so, appears next to it)
```

- The script (1) builds the inner objects with the original `Makefile.libretro` (`platform=unix`, `-mcpu=cortex-a53`, `-j1`), (2) renames the symbols into two copies, and (3) links them with the wrapper. The `ARCH_FLAGS` environment variable changes the CPU flags.
- The per-player save module uses a thread. On systems older than glibc 2.34, add `-lpthread` to the wrapper's link line in `dual/build_dual.sh` (the prebuilt file was linked with `-lm -lpthread`).
- Rebuilding the same source gave identical output except for the 20-byte build-id (development notes), so the md5 of a file you build yourself may differ from the table.

## Patches

Apply the files in `patches/` **in file-name order**, one at a time.

| Order | File | What it does |
|---|---|---|
| 1 | `0001-GG-Dual-Gear-to-Gear-link-hooks-line-stepped-SMS-GG-.patch` | The cable model, line-stepped execution and the two-console front end. |
| 2 | `0002-GG-Dual-plain-UART-serial-NMI-on-RX-ready-enable-edg.patch` | Serial as a plain UART, plus a one-frame delay for same-frame presses. |
| 3 | `0003-GG-Dual-option-description-uses-comma-instead-of-semicolon.patch` | `;` becomes `,` in an option description. |
| 4 | `0004-GG-Dual-1.1-os4-guest-own-save.patch` | Per-player saves (kind 4), the final version (1.1-os4). |

- **`0003` is a reconstructed patch.** This one-byte fix was made directly in the source folder on 2026-10-22 and built into the core, but it was never committed (the same text change was also applied once as a byte-level edit of the binary). On 2026-10-29 the `git diff` of that folder (against commit `3ef1895`) was turned into patch format. `0004` was made on top of the source that already contained the fix.
- `0004` was originally named `0003-GG-Dual-1.1-os4-guest-own-save.patch`; its number moved when 0003 was slotted in above it. The content is the same.
- Source provenance: `302fe82` plus two commits on the `hb_gg_dual` branch is patches 0001 and 0002.
- Some comments inside the patches are in Korean; they were left as written.
- **Checked on 2026-10-29 (on a Mac).** The 4 patches apply in order to upstream `302fe82` with no fuzz, and the resulting source is identical to the development source folder (0001 + 0002 + the option fix + 0004). The version text is `DUAL_VERSION "1.1-os4"` plus `GIT_VERSION`. During development, 0001 and 0002 built twice gave identical results, and the 0004 version was built twice by re-linking only the wrapper, also with identical results (the inner objects come from the same source as the build whose md5 starts `303ef6a0`).

## Upstream status

Not planned. This is a setup-specific feature, with two core copies (`ggA_` and `ggB_`) and a cable model inside one device, rather than a standalone bug fix for the upstream single-console emulator. Extension-port communication is only usable with a front end that connects two instances, so upstream is unlikely to accept it. The option-text fix (`;` becomes `,`, patch 0003) applies only to our own option names. (`upstream_pr_candidate` in [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) is marked as not worth sending.)

## License

- Upstream Genesis Plus GX uses its own license (`LICENSE.txt`; a copy is in [`LICENSES/Genesis-Plus-GX_LICENSE.txt`](../../LICENSES/Genesis-Plus-GX_LICENSE.txt)). In short, it is **non-commercial**: you may redistribute it, but you may **not sell it or use it in a commercial product or activity**. That includes selling a device or an image that ships this core for money. Modified versions must be distributed with the **complete modified source (including the source of the components used)**, and the copyright notices and disclaimers must stay intact. For the exact terms, follow the upstream `LICENSE.txt`.
- The patches in this folder (and the newly written `dual/` and `core/hb_gglink.h`) are published under the same terms. Components merged inside, such as zlib and FLAC, follow their own terms.
- `dual/hb_ownsave.h`, `hb_storage.h` and `hb_romfile.h` have no separate header; they are released under the same terms as this core (written for this project).
