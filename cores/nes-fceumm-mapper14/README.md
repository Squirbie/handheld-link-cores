<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# FCEUmm mapper 14 — work RAM for SL1632 boards

> FCEUmm with 8 KB of work RAM added to NES mapper 14 (SL1632), so the 512 KB + 512 KB Korean translation of "Downtown Special - Kunio-kun no Jidaigeki Da yo Zenin Shuugou!" boots instead of stopping at a black screen.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/nes-fceumm-mapper14-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `fceumm_libretro.so` (linux aarch64, 4,261,840 bytes, not stripped) |
| Version | `(SVN)-63643ba-hb1` as reported by the core (core name `FCEUmm`) |
| md5 | `d944c5c6451efea1aaab950317886426` |
| sha256 | `0edc2c13f987394f5a7dbbd05c2ce49ec3fadd3f560452ebbfe59ee0c6584f90` |
| Upstream | [libretro/libretro-fceumm](https://github.com/libretro/libretro-fceumm) at `63643ba` ("Remove FCEUD_SoundToggle", 2024-01-25); the stock FCEUmm on the tested device is the same commit |
| License | GPL-2.0-or-later |
| Tested on | Anbernic RG35XX Pro · KNULLI |

## What it does

Work RAM is extra memory on the cartridge board that a game can use as scratch space (and, if the board has a battery, to keep save data). Stock FCEUmm gives NES mapper 14 (the SL1632 board) none, and that is why one ROM in particular never started.

- **What was wrong.** The Korean translation of "Downtown Special - Kunio-kun no Jidaigeki Da yo Zenin Shuugou!" (mapper 14, 512 KB program, 512 KB graphics) reads and writes the work-RAM area (`$6000`–`$7FFF`) 11,735 times. Stock FCEUmm's mapper 14 has **0 bytes** of work RAM, and on top of that it sends every write to `$4100`–`$FFFF` to the mapper registers, so writes to `$6000`–`$7FFF` vanished even if RAM had been attached. The game stopped at a black screen.
- **The fix.** The core attaches 8 KB of work RAM (it is saved too, if the ROM header has the battery flag) and splits the register writes into `$4100`–`$5FFF` and `$8000`–`$FFFF`, so `$6000`–`$7FFF` goes to the RAM.
- **The result.** The game runs at 60–61 fps from the Korean title screen through the game modes (1P vs COM, 1P vs 2P, co-op, versus) and into the fights.
- **One core for everything.** We used to launch this one ROM on the Mesen core. Mesen is heavy on this handheld (45–49 fps even in single player), and with the two devices on different cores, link play could not connect either. Now the ROM runs on FCEUmm like every other NES game.

## What we changed

The whole change is the patch [`patches/mapper14_wram.patch`](patches/mapper14_wram.patch), two places in `src/mappers/mapper014.c`. The comments we added start with `hanbang:`; that is only our marker for "changed here".

1. In `UNLSL1632_Init`, `GenMMC3_Init(info, 256, 512, 0, 0)` becomes `GenMMC3_Init(info, 512, 512, 8, info->battery)`: the program size goes from 256 to 512 KB, the work RAM from 0 to 8 KB, and the battery flag comes from the ROM header.
2. In `UNLSL1632Power`, the write handler `SetWriteHandler(0x4100, 0xFFFF, UNLSL1632CMDWrite)` is split in two, `0x4100`–`0x5FFF` and `0x8000`–`0xFFFF`, which leaves `$6000`–`$7FFF` to the work-RAM handlers that `GenMMC3Power` sets up.
3. This is the same behavior as Mesen's `MMC3_14`, which attaches MMC3's default RAM; that is why the ROM already ran on Mesen.

```diff
--- a/src/mappers/mapper014.c
+++ b/src/mappers/mapper014.c
@@ -98,11 +98,14 @@
 
 static void UNLSL1632Power(void) {
 	GenMMC3Power();
-	SetWriteHandler(0x4100, 0xFFFF, UNLSL1632CMDWrite);
+	/* hanbang: leave $6000-$7FFF to the work RAM handlers set by GenMMC3Power */
+	SetWriteHandler(0x4100, 0x5FFF, UNLSL1632CMDWrite);
+	SetWriteHandler(0x8000, 0xFFFF, UNLSL1632CMDWrite);
 }
 
 void UNLSL1632_Init(CartInfo *info) {
-	GenMMC3_Init(info, 256, 512, 0, 0);
+	/* hanbang: 8KB work RAM at $6000 (Downtown Special Korean 512K/512K hack uses it; Mesen gives it too) */
+	GenMMC3_Init(info, 512, 512, 8, info->battery);
 	cwrap = UNLSL1632CW;
 	info->Power = UNLSL1632Power;
 	GameStateRestore = StateRestore;
```

## Install on KNULLI

This is how we install it. Download `nes-fceumm-mapper14-linux-aarch64.zip` from [Releases](https://github.com/Squirbie/handheld-link-cores/releases) and unzip it.

**Replace the stock core under its stock name.** Then the `.info` file, the EmulationStation (ES) feature settings and `knulli.conf` stay untouched, and every NES/Famicom game uses this core. Keep the file in `/userdata/system/hanbang_cores/` (default path used by the prebuilt files) and point RetroArch's core path at it with a symlink. With no game running:

```sh
HB=/userdata/system/hanbang_cores/fceumm_libretro.so
mkdir -p /userdata/system/hanbang_cores
cat > $HB.new < fceumm_libretro.so       # check that its md5 is d944c5c6… first
chmod 755 $HB.new && mv -f $HB.new $HB && sync
mount -o remount,rw /
ln -sfn $HB /usr/lib/libretro/fceumm_libretro.so
knulli-save-overlay
```

- **Undo.** Remove the file on the overlay side, using the overlay path: `rm /overlay/overlay/usr/lib/libretro/fceumm_libretro.so && knulli-save-overlay`, then reboot. Be careful not to delete the visible path (`/usr/lib/libretro/…`) instead: the overlay then records a "whiteout" and the file disappears entirely. Keep a copy of the original core somewhere safe (the stock one on the tested device has md5 `4661bc574366aa7a1bd10f388f555544`).
- If `knulli.conf` has a line that launches this ROM with Mesen, delete it. This core is enough.
- Put the **same file** on both devices for link play. That is the safest: netplay also connects when the version strings differ, but the emulation state can drift apart.

### Other devices and operating systems

- The `.so` is for **aarch64 Linux** (symbols from glibc 2.33 or older; it needs `libm` and `libc`). Other CPUs and operating systems need a rebuild from the patch.
- **The patch does not apply to the latest upstream as it is.** Upstream later moved `src/mappers/` to `src/boards/` and rewrote mapper 14 on top of `asic_mmc3.h` (`src/boards/14.c`; seen at `ac0d00a` on 2026-10-11). We have not checked whether this ROM runs on the new implementation.
- Known limits (unrelated to this patch): the Korean translation of Megami Tensei II shows a broken title picture on all three cores we tried, because it expands the graphics RAM to 256 KB with an unusual patch. Its Korean text only displays correctly in FCEUmm, so we keep it on FCEUmm. Light-gun games such as Duck Hunt (Zapper) only accept a mouse, so they can't be used on this handheld.

## Build from source

```sh
git clone https://github.com/libretro/libretro-fceumm
cd libretro-fceumm
git checkout 63643ba02c8eaea15dbe167ef907f3da7a3e6fd7
patch -p1 < /path/to/patches/mapper14_wram.patch
make -f Makefile.libretro platform=unix GIT_VERSION="-63643ba-hb1"      # Debian 12 aarch64, gcc 12, -O2
# → fceumm_libretro.so
```

- The version text the core reports, `(SVN)-63643ba-hb1`, comes from `GIT_VERSION`. RetroArch netplay connects as long as the core **name** (`FCEUmm`) matches, and only warns when the version text differs (checked in RetroArch's source), so a device that still has the stock core can connect as well.
- During development we built in a VM (Debian 12, gcc 12.2.0, `-O2`) without any extra CPU flags. The command above was written down from upstream's `Makefile.libretro`, so it may differ a little from our VM script.

## Patches

| Order | File | What it does |
|---|---|---|
| 1 | [`mapper14_wram.patch`](patches/mapper14_wram.patch) | Gives mapper 14 8 KB of work RAM and splits the register write range so `$6000`–`$7FFF` reaches it (two places in `src/mappers/mapper014.c`); the build is called `hb1`, md5 `d944c5c6451efea1aaab950317886426` |

- **Checked** (on the web, 2026-10-29): upstream `63643ba`'s `src/mappers/mapper014.c` (110 lines) still contains the two lines the patch removes, `SetWriteHandler(0x4100, 0xFFFF, UNLSL1632CMDWrite);` and `GenMMC3_Init(info, 256, 512, 0, 0);`.
- **Not done:** applying the patch afresh for this release, because the source of that commit was not at hand. The build that produced `d944c5c6` was made in a VM during development from this source.
- **Did it break other games?** (during development) We took 44 games from the 234 NES titles on one test device: one ROM per mapper, the mapper 14 titles and the Disk System. Each ran for 600 frames on the stock core and on this one, and we compared the last screens. **43 were pixel-identical.** The one difference is this ROM (black screen on stock, title screen here, which is the fix). One of the 43, Megami Tensei II (Korean), differed at first only because it loaded a save file written by the earlier stock run; after deleting the save and running both again, they matched. CPU use in the same scene matched stock too (RetroArch main thread 44–47% vs 40–48%).

## Upstream status

Not sending it for now. In the old implementation at `63643ba` (`src/mappers/mapper014.c`) this was a clear defect: no work RAM, and the registers intercepting `$6000`–`$7FFF` writes. But upstream has since moved the file to `src/boards/14.c` and rewritten mapper 14 on top of `asic_mmc3.h` (seen at `ac0d00a`, 2026-10-11), so this patch no longer applies. If the same Korean ROM still shows a black screen with the new implementation, send a small PR or issue then, written against the new code. The details are in `upstream_pr_candidate` of [`cores/MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl).

## License

Upstream FCEUmm is licensed under the **GPL-2.0-or-later** (`Copying` is GPLv2, kept in [`LICENSES/libretro-fceumm_Copying`](../../LICENSES/libretro-fceumm_Copying); the file headers say "version 2 … or (at your option) any later version"). This patch is under the same terms, and when we distribute the core binary, we publish the modified source (this patch) with it.
