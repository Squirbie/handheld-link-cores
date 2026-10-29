<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# MAME 2003-Plus — save states that keep netplay in sync

> A patched MAME 2003-Plus libretro core whose save states are complete enough for two-handheld netplay, rewind and run-ahead.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/arcade-mame2003-plus-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `mame2003_plus_libretro.so`, 42,816,416 bytes, aarch64 Linux (in the release zip `arcade-mame2003-plus-linux-aarch64.zip`) |
| Version | Version label `61305d6-blankfix1-bf9`. The first patch's name stayed in the label, ten more patches are included, and the last one adds `-bf9`. Internal build name: "bf9" |
| md5 | `5dbeaf459d9c05a5eb175a286c7ed4a7`<br>sha256 `c5750587ae054213bffce5462f97647a5e691312609cdf7203fbd35acba08be4` |
| Upstream | [libretro/mame2003-plus-libretro](https://github.com/libretro/mame2003-plus-libretro) at commit `61305d6` ("4 entries added (#1915)", 2025-01-10); full hash `61305d60329d6a9abf7ddad1c3657b3253c5e64d` |
| License | MAME non-commercial license (MAME 0.78). Free to use, but you may not sell it. See [License](#license) |
| Tested on | Anbernic RG35XX Pro (H700, aarch64, 1 GB RAM) · KNULLI · RetroArch 1.22 |

> **Unofficial modified build.** Please do not ask the MAME 2003-Plus developers about problems with this build. No ROMs, BIOS files or saves are included in this repository; use only ROMs you own.

## What it does

MAME 2003-Plus is the libretro core that runs a huge catalog of classic arcade boards. RetroArch netplay works by having the host send its *current state* to the guest, who then carries on from there. That only works if a save state really contains everything the game needs, and on the stock core it often did not. This build fixes four problems:

- **The guest's screen was blank, or different from the very first frame.** The state left out values that each board needs: values held inside the CPU, timers, the interrupt queue, the video chip's private video memory, and more.
- **Some games could not start netplay at all** (and had no usable save states or rewind), because the core wrongly decided they cannot be saved.
- **A few boards had huge states** (20~53 MB) because big ROM banks that never change were saved again and again. Netplay keeps dozens of states for rewinding, which ran a 1 GB handheld out of memory.
- **Music went wrong after a load, and netplay hitched now and then.** Two fixes taken from upstream: after loading a state, the YM2151 sound chip rebuilt every channel with the wrong algorithm, and the input values a board had latched were not in the state, so the first frame after a rollback ran with the wrong buttons.

The goal is netplay and save states that work, not more accurate emulation. Parts of some sound chips are still missing from the state, so the sound can be off for a moment right after a guest joins (see [Known limits](#known-limits)).

## What we changed

Eleven patches, applied in order on top of upstream commit `61305d6`. 0009 and 0010 are upstream fixes, taken as they are. Code comments and log lines that contain `hanbang` just mark places we changed; we did not rename them.

1. **Complete the save state** (patches 0001, 0003 and 0005 to 0008). Many boards kept values outside the registered state, or derived data that was never rebuilt after a load. We register the missing values and rebuild derived data right after loading.
   - 0001 is the broad one (39 files, +835 / -81): the CPU scheduler (frame, vblank, CPU halts, local clocks, 64-bit cycle counts), persistent timers (phase and order), the IRQ event queue, the missing T-11, M6809 and Z80 registers, YM2151 timers, and each board's private video RAM, registers and latches. Derived caches are rebuilt after loading, and pointers are saved as offsets instead of addresses. It also appends `-blankfix1` to the core's version string. Boards covered: Nintendo Vs., Bally Sente, Taito SJ, Atari System 2, MegaSys1, Sega System 1, Taito L, Leland / Ataxx, DECO Cassette, HD63484, Namco ND-1 (YGV608), Paradise, Toaplan 1, Williams and Super Qix.
   - 0003, 0005, 0007 and 0008 then add one board family each (see the [Patches](#patches) table): the HuC6280 CPU and HuC6270 video chip, the Atari GT board, Atari System 1 / Gauntlet, and the Vs. System MMC3 mapper with its protection counters.
   - 0005 also fixes a bug in `atarigen.c`: it registered five `UINT8` variables as `INT32`, so saving and loading overwrote the neighboring memory.
   - 0006 narrows 0005: its persistent timers changed the host's picture on other Atari boards, so only `atarigt` uses them and the other boards go back to the original `timer_set`.
2. **Stop wrongly refusing to serialize** (0002). `GAME_DOESNT_SERIALIZE` was defined as `0x0420`, which is exactly `GAME_IMPERFECT_SOUND` (`0x0400`) plus `GAME_WRONG_COLORS` (`0x0020`). Every game marked "imperfect sound" or "wrong colors" therefore counted as unserializable, reported a state size of 0, and netplay could not even start. The clash had been in the source since 2018 (about 323 games by upstream's count, and 13 of the 215 two-or-more-player MAME 2003-Plus games on our game list). The fix is one line: the flag gets its own bit, `0x0800`.
3. **Keep large ROM banks out of the state** (0004). Banks that never change (several MB, up to 48 MB) were saved with every state, so a state was 20~53 MB, and netplay holds dozens of rewind states. `register_banks()` now skips every bank of 1 MB or more that never appears in a write map (that is, ROM) and logs one `hanbang: read-only bank` line for each bank it skips.
4. **Take two fixes from upstream** (0009, 0010). They were merged upstream in October 2026, after our base commit, and they apply as they are on top of our patches.
   - 0009 (upstream `b52156ee`, PR #2041): after a load, `ym2151_postload_refresh()` passed the channel and the algorithm to `set_connect()` the wrong way round, so every FM channel was rebuilt with the wrong algorithm until the game wrote that register again. One line. The state layout does not change, so older states still load.
   - 0010 (upstream `32775973`, PR #2053, plus the `hd6309.c` part of `6266128c`, PR #2176): the input values each board latched at the last VBLANK are saved in the state, so the first frame after a load or a rollback reads the same buttons as the original run. The HD6309 CPU also saves its D and W accumulators and the cycles of an interrupt taken outside the execute loop. This changes the state layout, so states from bf8 and earlier no longer load.
5. **Version label** (0011): `-blankfix1` becomes `-blankfix1-bf9`, so the core info tells this build apart from the previous one.

### How it was tested

Every test used the same method. The host (A) runs 20 s or 60 s and saves a state. A guest (B) in a **fresh process** starts the same ROM, runs 2 frames, then loads that state. With no input, 300 frames are run, and a hash of each raw frame is compared with the host's (`300/300` means not one frame differs). We also compared the host's own video with the core before the fix, to check that the emulation itself was not changed. These tests ran on a Mac and in a virtual machine; real-device tests were done separately.

| Patch | Result |
|---|---|
| 0001 | 26 sets tested (the 23 sets reported with a blank guest screen, plus 3 of the 4 control sets; the fourth cannot save states at all). On the stock core, 22 sets showed a diverging guest screen. After the fix, all 26 sets × (20 s, 60 s) = 52 conditions gave 300/300. With the guest run for 120 frames first: 52/52. Loading the same state three more times: 156/156. Host video, stock core versus fixed core: identical in 52/52. Loading after a reset and scenes after cassette loading were identical too. |
| 0002 | One-line fix. 13 of the 215 two-or-more-player MAME 2003-Plus games on our game list failed netplay setup because of the flag clash. After the fix, 11 of them connect and run; the other two have very large states and run on FBNeo instead. |
| 0003 | Two sets that use the HuC6280 CPU (state taken at 20 s). `battlera`: guest screen 0/300 to 300/300, state 23,656 to 156,010 bytes. `actfancr`: 92/300 to 300/300, state 56,672 to 56,735 bytes. A control set that does not use the HuC6280 has a byte-identical state. |
| 0004 | State size drops from the 20~53 MB range to 1.6~3.2 MB (CAGE sound-board family from about 20 MB to 1.6 MB, ST-V family to 3.2 MB). Three tested sets without big read-only banks keep the same state size. |
| 0005 | One CAGE-family set (`primrage`): states taken at 20, 60, 120 and 180 s all go from 0~16/300 to 300/300. Rewinding inside one process is identical too; before the fix, the first rewind killed the process with `Unimplemented op` from the sound DSP. State size 1,589,080 to 2,273,679 bytes. |
| 0006 | 15 Atari sets plus 4 sets from other boards: the host's screen matches the 0004 build in 19 of 19 (300/300). With 0005 alone, one Atari game matched in only 2/300 and another in 195/300. |
| 0007 | `gauntlet`: 0 to 300. Two System 1 boards: `marble` 299 to 300, `roadblst` 294 to 300. The host's screen in 19 regression sets is identical to the 0006 build. State size grows by 5 bytes (`gauntlet`) and 170 bytes (System 1). |
| 0008 | 24 Vs. System sets: 22 already matched, and the 2 sets that use protection counters go from 0 to 300 (also from a 60 s state). The host's screen is identical to the 0007 build for these 24 sets and 4 more. |
| 0009 | `imgfight`, state taken at 20 s, guest audio compared with the host's (best match within ±25 ms): 0.5 s after the load the waveform is the same with this build (correlation 1.000) and not before (0.192). Later in the run both builds differ by the same amount, because other sound state (the mixer's pending samples, sample chips) is still missing. In `gaunt2` and `rodland` both builds were already above 0.99, since those games rewrite the register at almost every note. |
| 0010 | Coin held from 3 frames before the save to 3 frames after it (the guest presses it only after loading): `rodland` guest screen 1/600 → 600/600; `gaunt2` and `imgfight` were already 600/600. HD6309 boards with no input: `mx5000` from a 60 s state 0/600 → 600/600 (from 20 s: 600 in both builds), `ghostb` 600 in both. The host alone gives exactly the same video and audio as bf8 in all 14 runs (7 sets). State size grows by 120 bytes, or 128 on HD6309 boards. These runs used 600 frames instead of 300. |
| Real devices | Each time the core changed, representative games were connected on two real handhelds and the host and guest screens were compared by photo. Across several passes, all 215 two-or-more-player MAME 2003-Plus games on our game list were connected at least once (recorded 2026-10-21). bf9 (2026-10-29): installed on both devices with `install.sh --from` (the previous file went to `hanbang_cores/backup/`); `rodland` over netplay connected, and of two pairs of simultaneous screenshots the second was identical (the first differed only by moving sprites, the shots being a fraction of a second apart). A mahjong game through [`arcade-mahjong-pad`](../arcade-mahjong-pad/) starts on bf9. |

### Known limits

- Apart from the coin test for 0010, the tests are input-free. Two-player input, latency, rewind and audio sync were only checked on representative games on the devices.
- `rockrage`: the guest's sprite flicker can run one frame out of step with the host's, in bf8 and bf9 alike.
- Some sound state (PC Engine C6280, MSM5205, TMS5220, POKEY, the mixer's pending samples) is not in the state yet, so the sound can be briefly off right after a guest joins.
- Some boards have bigger states now (CAGE family: 1.59 MB to 2.27 MB). Rewind keeps several states, so memory use rises accordingly.
- A correct state does not help if the device is too slow. The ST-V family runs at only 30~40 fps even when playing alone, and the CAGE sound-board family at about 46 fps (77% of full speed), so we do not offer those for netplay.
- Drivers we could not run for lack of ROMs: `tmek` and Midway V-Unit (same DSP core). For some Atari drivers without ROMs, only the host-screen regression test was done.

## Core options

None added or changed. The only visible difference in the core info is the version label, which ends in `-blankfix1-bf9`.

## Install on KNULLI

Download `arcade-mame2003-plus-linux-aarch64.zip` from the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest) and unzip it. This is how we installed it:

1. **Where the file goes:** `/userdata/system/hanbang_cores/mame2003_plus_libretro.so` (default path used by the prebuilt files), on the SD card. The file RetroArch looks for, `/usr/lib/libretro/mame2003_plus_libretro.so`, is a **symlink** to it. The core lives on the SD card because KNULLI's overlay is a RAM disk, so a big file there eats memory. If you delete that folder, some arcade games will not start.
2. **Swapping the file:** only while no game is running (EmulationStation's local web API reports `runningGame` as "NO GAME"). Copy the new file over as `mame2003_plus_libretro.so.hbnew`, check the md5, run `chmod 755`, replace the old file with `mv -f`, then `sync`. Before replacing, keep the previous file in the same folder under an old name (we used a suffix such as `.bf8`). RetroArch loads the core when a game starts, so no restart is needed.
3. **Both devices must run the same file.** Mixed builds produce different state sizes and the guest cannot join. Check the md5 on both.
4. **Per game:** if this core is not the default for the system, add one line to `knulli.conf`: `arcade["<ROM name>.zip"].core=mame2003_plus`.
5. **Check:** the md5, and the version in the core info reads `61305d6-blankfix1-bf9`. With RetroArch logging on, games that have large banks print a `hanbang: read-only bank` line.
6. **Rolling back:** put the saved file back. Save states made with another build will not load in this one, and the other way around (before installing, we confirmed there were 0 arcade save-state files on both devices).

### Other devices and systems

- **The file is for aarch64 Linux only.** On 32-bit ARM, x86, Android, Windows or macOS, apply the patches to the upstream source and build for that platform.
- **glibc 2.33 or newer** (libm 2.29 or newer) is required, because it was built with GCC 12.2 on Debian 12. On older Linux, rebuild it there. It worked without problems on KNULLI.
- **Netplay was only tested with the same file on both sides.** Mixing it with the stock core or another build leaves the guest unable to join, or diverging.
- **Save states are not compatible.** This build puts different items into the state than upstream or any earlier build, so states and autosaves from those cannot be loaded, and the other way around.
- **Memory:** depending on the board, the state grows (0005) or shrinks (0004). It was tested on a device with 1 GB of RAM.
- It was tested only on the RG35XX Pro (H700) with KNULLI and RetroArch 1.22. Other front ends' netplay implementations were not checked.

### Companion scripts

Two scripts in [`knulli-scripts/`](../../knulli-scripts/) work together with this core (see [`knulli-scripts/README.md`](../../knulli-scripts/README.md) for where they go):

- [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py) asks "join or play solo?" when a room for the same game is already open.
- [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py) writes in-game saves to a file right away during netplay.

Arcade mahjong games that read their keys from a keyboard need a separate wrapper core: see [`arcade-mahjong-pad`](../arcade-mahjong-pad/).

## Build from source

We built it on Debian 12 (aarch64) with GCC 12.2.0, running plain `make` in the upstream source folder (with `-j1`, because memory ran short). The result needs glibc 2.33 or newer.

```sh
git clone https://github.com/libretro/mame2003-plus-libretro.git
cd mame2003-plus-libretro
git checkout 61305d60329d6a9abf7ddad1c3657b3253c5e64d
for p in /path/to/patches/00*.patch; do git apply --check "$p" && git apply "$p" || break; done
make              # add -jN if you have the RAM; platform=unix is picked automatically on aarch64 Linux
# result: mame2003_plus_libretro.so
```

- The md5 may differ from ours even in the same environment (compiler version, build paths). The exact command line and options of our build were not recorded.
- To check only that the source compiles on a Mac (the result is a `dylib`):
  ```sh
  make -j6 platform=osx ARCH=arm64 'CC=clang -std=gnu89 -fcommon -Dfdopen=fdopen -Wno-error=incompatible-function-pointer-types'
  ```
- If the patches are applied inside a `git` checkout, the version label in the core info becomes `<short hash>-blankfix1-bf9`.

## Patches

Apply them in the order of [`patches/series`](patches/series). Later patches continue in files fixed by earlier ones (`atarigen.c`: 0005, then 0006, then 0007).

| Order | File | What it does |
|---|---|---|
| 1 | `0001-state-completeness-blankfix1.patch` | Saves the CPU scheduler, persistent timers, IRQ event queue, the missing T-11 / M6809 / Z80 registers, YM2151 timers and each board's private video RAM, registers and latches; rebuilds derived caches after loading; appends `-blankfix1` to the version string (39 files, +835 / -81). |
| 2 | `0002-driver-h-game-doesnt-serialize-own-bit.patch` | Changes `GAME_DOESNT_SERIALIZE` in `src/driver.h` from `0x0420` to `0x0800`, so it no longer overlaps `GAME_IMPERFECT_SOUND` (`0x0400`) plus `GAME_WRONG_COLORS` (`0x0020`); also fixes a typo in the comment. |
| 3 | `0003-h6280-huc6270-battlera-state.patch` | Registers the HuC6280 CPU (PC, registers, eight MMR registers, timer, IRQ), the HuC6270 video chip (128 KB VRAM, registers, palette) and the driver values of the `battlera` board; rebuilds the tile, sprite and color caches after loading (3 files, +77 / -6). |
| 4 | `0004-register-banks-skip-readonly-large-banks.patch` | `register_banks()` in `mame-memory.c` leaves out banks of 1 MB or more that never appear in a write map (ROM), and logs one `hanbang: read-only bank` line per skipped bank (+12). |
| 5 | `0005-tms32031-cage-atarirle-atarigt-state.patch` | Registers the TMS32031 DSP, the CAGE sound board (latches, DMA, timers, sound buffer), the four sprite (RLE) screen buffers and the tile, color, scroll and protection state of the Atari GT board; corrects the five `UINT8` variables that `atarigen.c` registered as `INT32`; turns the VBLANK / scanline callbacks into saved persistent timers (6 files, +117 / -9). |
| 6 | `0006-atarigen-persistent-timers-atarigt-only.patch` | Uses 0005's persistent timers only on `atarigt`; every other Atari board goes back to the original `timer_set`, because the persistent timers had changed those boards' host picture (+52 / -15). |
| 7 | `0007-atari-system1-gauntlet-slapstic-atarimo-state.patch` | After loading, rebuilds the slapstic (protection chip) bank's ROM copy, the sprite display-list cache and the playfield scroll / tile bank; registers Atari System 1's priority pens, three line-interrupt timers and joystick / 6522 values. Emulation itself is unchanged, only registration and post-load handling (6 files, +85 / -1). |
| 8 | `0008-vsnes-mmc3-and-protection-state.patch` | Registers the Vs. System (NES-based) MMC3 mapper values, the hidden `last_bank` and the mirroring setting; after loading, re-applies the PRG / CHR banks and mirroring and re-installs the IRQ callback; registers the protection counters (`prot_index`, `security_counter`, `VSindex`) (`vsnes_machine.c`, +45 / -7). |
| 9 | `0009-ym2151-postload-connect-args-upstream-b52156ee.patch` | Upstream `b52156ee` (PR #2041): `ym2151_postload_refresh()` calls `set_connect(op, channel, algorithm)` in the right order (`ym2151.c`, 1 line). |
| 10 | `0010-input-port-latch-hd6309-state-upstream-32775973-6266128c.patch` | Upstream `32775973` (PR #2053): registers the latched input port values and VBLANK values (`inptport.c`, +6). From upstream `6266128c` (PR #2176), only the `hd6309.c` part: registers the D and W accumulators and `extra_cycles` (+3). |
| 11 | `0011-version-label-bf9.patch` | Changes the version suffix from `-blankfix1` to `-blankfix1-bf9` (`mame2003.c`, 1 line). |

**Build chain** (first 8 hex digits of each md5): the stock core on the device, `9566440f` (full md5 `9566440fcc8d1825831e18f1aa3e147e`, built from the same commit, version label `61305d60`), then 0001 `9971dced`, 0002 `cd9cc09f`, 0003 `4852947b`, 0004 `427e1497`, 0005 `f6c2666f`, 0006 `48670ebc`, 0007 `f10ff081`, 0008 `30e1ebc1`, and finally 0009 to 0011 together **`5dbeaf45`**, the shipped file. We called these builds bf1 to bf9. The 0004 and 0005 builds were intermediate steps that were never installed on the devices, but their patches are in every later build.

**md5 of the patch files in this folder** (first 8 hex digits): 0001 `833927e3`, 0002 `1a35f0df`, 0003 `d247010c`, 0004 `646ca82d`, 0005 `dd3a13f1`, 0006 `0b6f686e`, 0007 `4d8a3c0a`, 0008 `41781480`, 0009 `0632bcfc`, 0010 `76c08faf`, 0011 `a9aa80d5`.

**Notes on the patch files**

- 0002 and 0004: only the header lines were normalized; the changes themselves are as they were.
- 0006 started out as a Python script. The patch was made by running the script on a source tree with 0001 to 0005 applied and saving the difference; the content is the same as the script's.
- 0008: the header was normalized and the context was cut from 3 lines to 1, so that a credit comment with a contributor's e-mail address in the original source is not copied into the patch. Applying it gives exactly the same file as the original patch.
- 0009 and 0010: copied from the upstream commits without changes. Upstream `6266128c` also covers several sound chips; only its `hd6309.c` part is in 0010.

### What is verified, and what is not

- **Verified:** all eleven patches apply in order, in one go, to a clean checkout of `61305d6`, and the result is exactly the source tree the shipped file was built from (the two `git diff` outputs are identical). The "before" file fingerprint (the `index` line) of 0001 matches that commit's file (2026-10-29).
- **Verified:** strings in the shipped `.so` match the patches: `hanbang: read-only bank` (0004); `VSindex`, `security_counter`, `prot_index`, `mirror_reg` (0008); `HuC6270_vram`, `adpcm_toggle` (0003); `expanded_mram`, `protmode` (0005); `next_timer_scanline`, `playfield_yscroll_applied`, `trakball_cur` (0007); `cpu_scheduler` (0001); `port values` and `extra_cycles` (0010). Its version label reads `61305d6-blankfix1-bf9`.
- **Verified:** the patched source compiles and links on a Mac (Apple clang 21, arm64) without errors (2026-10-29, warnings off). The shipped file was built separately with GCC on aarch64 Linux, so it is a different file from that Mac `dylib`.
- **0008 detail:** the finished diff was used, not the original script version. The script alone would miss two lines (`#include "state.h"` and the `VSindex` registration) that the diff contains, which matches `VSindex` being in the shipped core.
- **Not verified:** the 0002 build (`cd9cc09f`) no longer exists as a file, so it is known from records only. The exact command line and options of the bf8 build were not recorded, and rebuilding bf8 in the same virtual machine gave a different md5 (same code size). bf9 was built with plain `make -j2` in that tree, and building it a second time gave the same md5 `5dbeaf45`. Of the 29 board files that 0001 touches, a few (the `decocass`, `leland`, `taitosj` and `williams` machine files, among others) could not be compared with upstream history because the lookup hit an API rate limit.

## Upstream status

Checked against upstream `master` on 2026-10-29. Nothing has been sent yet; English PR drafts are in [`../MANIFEST.arcade.jsonl`](../MANIFEST.arcade.jsonl) (`upstream_pr_candidate` and `more_pr_candidates`) and are summarized in [`UPSTREAM.md`](../../UPSTREAM.md).

- **0009 and 0010 come from upstream**, so there is nothing to send for them.
- **0002 is already upstream, so there is nothing to send.** We fixed the `GAME_DOESNT_SERIALIZE` overlap on 2026-10-21. Upstream made the same fix on 2026-10-24, with the same value `0x0800`: commit `ea58c97b5743c1e488dc6ba9556199bd19cf4efe`, [PR #2131](https://github.com/libretro/mame2003-plus-libretro/pull/2131) ("GAME_DOESNT_SERIALIZE: own flag bit, it was IMPERFECT_SOUND | WRONG_COLORS", related to issue #212).
- **The rest has to be re-cut first.** On the same day, upstream also merged its own timer and CPU-scheduling save-state work (PR #2133, `c47cda1f`). Our other patches were written against `61305d6` on top of our own timer work, so they must be rebased onto current upstream and retested before they can be sent.
- **0001 is not planned as one PR.** It is 39 files, and in October 2026 upstream landed overlapping work with a different approach: timers and CPU scheduling (#2133), the interrupt event queue (#2048), YM2151 timers (#2042), Z80 extra cycles (#2133), sound (#2043, #2049) and random numbers (#2132). What upstream still lacks (the M6809 and T-11 registers, the soft-reset address refresh in `state.c`, board-private video RAM and latches) would have to be rewritten and split per board.
- **Still missing upstream, and worth sending after a rebase:** 0003 (H6280 / HuC6270 state, small and self-contained, the same approach as `m6809_init`), 0004 (12 lines; caveat: a driver that changes ROM-bank bytes without going through a write map would lose them from the state, we saw none, but a maintainer should judge), 0005 and 0006 (Atari GT state and the `UINT8`-registered-as-`INT32` bug, which could go first on its own), and 0007 and 0008 (registration and post-load handling only, low risk). In the files they touch, upstream has no relevant commits after our base commit; `atarirle_vidhrdw.c` only has random-number and blood-color commits. They must be adapted to upstream's new timer-state approach, so they may not apply as they are.

## License

MAME 2003-Plus is under the classic **MAME non-commercial license** (the MAME 0.78 Usage and Distribution License). The text is in the upstream `LICENSE.md`, and this repository keeps a copy at [`LICENSES/mame2003-plus-libretro_LICENSE.md`](../../LICENSES/mame2003-plus-libretro_LICENSE.md). The patches and the modified core follow the same terms. In short:

- MAME is a non-profit project. **You may not sell the source or the binary.** Selling a device or memory card with this core on it is not allowed either.
- If you distribute a compiled binary, you must also distribute the source or tell people where to get it. The patches in this folder plus the upstream commit named above serve that purpose.
- Derivative works are allowed only if their source is freely available. They must not be called "MAME" and must make clear they are not an official distribution, which is why we call this an unofficial modified build.
- ROM images are copyrighted material. Do not distribute the emulator on the same medium as illegal ROM copies. There are no ROMs in this repository.
