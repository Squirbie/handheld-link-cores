<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# DOSBox Pure IPX — IPX netplay without crashing RetroArch

> A DOSBox Pure 0.9.9 build that restarts DOS with IPX enabled when a RetroArch netplay session starts, which avoids the RetroArch crashes seen when opening IPX games such as Heretic and Hexen over netplay on a handheld.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/dos-dosbox-pure-ipx-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| **Core file** | `dosbox_pure_hb_ipx_libretro.so` — aarch64 Linux, 2,627,720 bytes, stripped (in the release zip, not stored in git) |
| **Version** | `0.9.9` (the changed spot writes a log line starting `[DOSBOX] hanbang: network requested`) |
| **md5** | `20380390bed1c8042b5264b259d16e85` |
| **Upstream** | [schelling/dosbox-pure](https://codeberg.org/schelling/dosbox-pure) on Codeberg @ [`6108e45`](https://codeberg.org/schelling/dosbox-pure/commit/6108e45e5f1c4ba7d66f32aa109027afa67d74a9) (tag `0.9.9`, "Set version to 0.9.9", 2023-12-23). KNULLI's stock core is also 0.9.9. The old address, `github.com/schellingb/dosbox-pure`, now only shows a "moved" notice. |
| **License** | GPL-2.0-or-later |
| **Tested on** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (the only environment checked) |

## What it does

On the handheld (RetroArch 1.22.2), opening or joining a netplay room to play Heretic or Hexen with two players could make **RetroArch crash with -11 (SIGSEGV)**:

- After IPXSETUP had failed once with "IPX not detected", opening or joining a room crashed it, even with no guest.
- Running IPXSETUP right after starting as host (within 1 second) crashed it. After 1 minute it was fine.

**The exact line behind the crash was not pinned down.** Stock 0.9.9 never crashed when the same steps were run in 3 Mac sessions and 31 VM sessions (aarch64, under gdb). It seems to need conditions that exist only on the handheld, such as KNULLI's RetroArch build, speed, Wi-Fi and sound. So instead of fixing one line, this build makes the two suspect code paths **unreachable**.

**What behaves differently:** when netplay starts while DOS is running, **DOS restarts for 1 or 2 seconds** (unsaved progress is lost). Stock did this only within 10 seconds of starting DOS. After that it spliced IPX in while the game kept running, but IPXSETUP did not run again, so cooperative play did not work (8 of 10 stock guest joins in the VM). Solo DOS games run exactly like stock.

## What we changed

One place in `dosbox_pure_libretro.cpp`: `DBP_EnableNetwork()` (14 lines added, 2 removed). In 0.9.9 the netplay-start callback does one of three things:

1. If DOS started less than 10 seconds ago, it calls `retro_reset()` **from inside** the callback, which restarts the whole core.
2. Otherwise it freezes the DOS thread in the middle of a frame and, from the main thread, deletes and re-creates the `ipx` and `serial` sections (IVT 0x7A/0x73, IRQ11, callback, timer, BIOS COM values).
3. If DOSBox is shut down (`control == NULL`), it reads NULL.

This patch removes the first two. A running DOS is only marked with `dbp_state = DBPSTATE_REBOOT`; at the top of the next `retro_run`, DOS is restarted through the same path that options use when they need a restart (`DBP_ForceReset`). `init_dosbox` turns IPX and the modem on **before** it starts the DOS thread. Only when you booted an OS image (`BOOT`) is the stock behavior kept as is. Case 3 only sets the flag and returns. One line is left in the device log so you can find it: `[DOSBOX] hanbang: network requested (state N, program X) - restarting DOS with IPX/modem`.

`hanbang` in that log line and in the code comments only marks the places we changed.

## Core options

This build adds no core options. It keeps the stock `dosbox_pure_*` options. KNULLI's configurator applies those (svga, 16 MB, sb16 and so on) only when the core is named `dosbox_pure`, which is why the core is installed under the stock name (see below).

## Install on KNULLI

**Replace the stock core under its stock name.** KNULLI's configurator only applies the `dosbox_pure_*` options when the core is named `dosbox_pure`, and the ES feature (gamepad to keyboard) is also tied to that core name, so a new name would lose both. Put the **same file** on both devices. Download `dos-dosbox-pure-ipx-linux-aarch64.zip` from the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest), unzip it, and install with no game running.

**Before you start**

- The prebuilt `.so` is for **aarch64 Linux** (glibc 2.34 or older). For another CPU or OS, rebuild it from the patch.
- Only **KNULLI + RetroArch 1.22.2** has been checked. If the crash comes from somewhere else, such as KNULLI's RetroArch, Wi-Fi or sound, this patch may not make it go away.
- **Starting netplay restarts every DOS game**, so unsaved progress is lost. Solo DOS games are not affected (without netplay there are 0 restarts).
- Only two players were tested (`-nodes 2`); three were not tried. When the guest leaves, the host's game stops (original Doom-engine behavior; quit with the hotkey).
- A KNULLI update overwrites the symlink, which puts the stock core back, and the crashes can return. Check the link after updating.
- Check the unzipped file: md5 as above, sha256 `ade7d774f0ac78c7b41f1818b958576b22322067dc38e6fff577ef2e67cfec86`.

**Steps.** Copy the file into `/userdata/system/hanbang_cores/` (default path used by the prebuilt files) and point the stock name at it:

```sh
HC=/userdata/system/hanbang_cores
LIB=/usr/lib/libretro/dosbox_pure_libretro.so
mkdir -p $HC
# 1) Check that the current core is stock 0.9.9. If it is not (for example, a KNULLI update brought a newer version), stop and rebuild on that version instead.
# 2) Keep a copy of the stock core, only the first time (and only when $LIB is not already a symlink)
[ -e $HC/dosbox_pure_libretro.so.stock_0.9.9 ] || [ -L $LIB ] || cp $LIB $HC/dosbox_pure_libretro.so.stock_0.9.9
# 3) Copy the patched file over, and check that its md5 is 20380390bed1c8042b5264b259d16e85 before continuing
cat > $HC/dosbox_pure_hb_ipx_libretro.so.new < dosbox_pure_hb_ipx_libretro.so
mv -f $HC/dosbox_pure_hb_ipx_libretro.so.new $HC/dosbox_pure_hb_ipx_libretro.so && sync
mount -o remount,rw /
ln -sfn $HC/dosbox_pure_hb_ipx_libretro.so $LIB
knulli-save-overlay
```

- **Undo:** `ln -sfn $HC/dosbox_pure_libretro.so.stock_0.9.9 $LIB && knulli-save-overlay`.
- **Auto-start is not part of this folder.** In our setup, the Heretic and Hexen save bundles chain `AUTOBOOT.DBP` → `HBNET.BAT`: with no IPX it starts a solo game; with IPX present (DOS has been restarted by netplay) it runs `IPXSETUP.EXE -nodes 2`, and pressing Esc there starts a solo game. A 17-byte machine-code program, `HBIPX.COM`, tells whether IPX is present by calling `INT 2F AX=7A00`. With only this core installed, you have to run `IPXSETUP` yourself inside DOS after netplay starts.

## Build from source

```sh
git clone https://codeberg.org/schelling/dosbox-pure
cd dosbox-pure
git checkout 6108e45e5f1c4ba7d66f32aa109027afa67d74a9        # tag 0.9.9
PATCHES=/path/to/handheld-link-cores/cores/dos-dosbox-pure-ipx/patches
git apply "$PATCHES"/0001-hanbang-restart-DOS-instead-of-live-IPX-modem-switch.patch     # or: patch -p1 < the same file
make -j2 BUILD=RELEASE MAKE_CPUFLAGS='-mcpu=cortex-a53'       # Debian 12 aarch64, gcc 12.2.0
# -> dosbox_pure_libretro.so   (on the device it is installed as dosbox_pure_hb_ipx_libretro.so)
```

- `-mcpu=cortex-a53` is tuned for the RG35XX line (H700). Change it for another CPU.
- Checked during development: `NEEDED` is `libstdc++`, `libm`, `libgcc_s` and `libc`; it needs glibc 2.34 or older and GLIBCXX 3.4.29 or older; the exported functions are 25 `retro_*` plus 44 C++ template weak symbols.

## Patches

| Order | File | What it does |
|---|---|---|
| 1 | `0001-hanbang-restart-DOS-instead-of-live-IPX-modem-switch.patch` | Restarts DOS when netplay starts, so IPX and the modem are turned on from the beginning (commit `308cfebd`). |

- **Checked on 2026-10-29 (on a Mac).** Applying the patch to upstream `6108e45` gives a source tree that is **identical** to our `hb_ipx` branch (commit `308cfebd`). The build made during development has md5 `20380390bed1c8042b5264b259d16e85` and its source is `hb_ipx 308cfebd`.
- **Test results (development notes).** With the patched core: 60 netplay sessions (54 in a VM plus 6 on a Mac) and 7 solo launches, with **0 crashes**. Of 22 two-instance sessions, 20 ended in cooperative play. With the exact file that goes on the devices (`20380390`): 12 VM sessions, 0 crashes, 6 cooperative. Heretic and Hexen two-player play was confirmed on two devices.
- **What good cooperative play looked like.** The guest joined and cooperative play began 3 seconds later; the map showed a green arrow and a yellow arrow in the same place; and in Hexen, when one player walked forward, that player moved away on the other's screen.

## Upstream status

Not planned. The crash was only seen on the handheld and its exact cause is unconfirmed (stock does not reproduce it in 34 Mac and VM sessions). The patch also changes behavior, because a running DOS is restarted when netplay starts, so it is closer to a workaround tuned to the RG35XX plus RetroArch 1.22.2 than to a fix. The NULL-read guard that was part of the original work (`control == NULL`) has already been added upstream (checked during development: 2026-02-05, `77061c2`). `upstream_pr_candidate` in [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) is marked as not worth sending.

A check made during development found that the latest upstream (Codeberg `main`, `468dad0`, 2026-10-19) still has both of the other paths (the reset inside the callback and the live splice). This time Codeberg's pages could not be read automatically, so that was not re-checked.

## License

- Upstream DOSBox Pure is **GPL-2.0-or-later**: its `LICENSE` is GPLv2, the file headers say "version 2 … or (at your option) any later version", and the core info says `GPLv2`. A copy of the license text is in [`LICENSES/dosbox-pure_LICENSE`](../../LICENSES/dosbox-pure_LICENSE). Changed places carry a "hanbang 2026-10-19" comment, and the original copyright headers are untouched.
- If you distribute binaries that contain this core, you must also publish the modified source — this patch.
