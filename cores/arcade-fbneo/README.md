<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# FBNeo — leaner netplay states and a fixed input table

> A byte-patched FBNeo libretro core: smaller, steadier Taito F3 netplay states, and a corrected player-2 input table for one arcade game.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/arcade-fbneo-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `fbneo_libretro.so`, 77,036,704 bytes, aarch64 Linux (in the release zip `arcade-fbneo-linux-aarch64.zip`) |
| Version | Version string `v1.0.0.03 74a979724`, unchanged from the stock core (only 9 bytes differ). The stock core `fa5feb62b5d8c4f9a71786bc649409cd` was patched in two steps, via `9e31af9441611566af6d61cee10a1e7b`, into this file (internal build name: "FBNeo c942499f") |
| md5 | `c942499fc72a61400d4e6a486841fb37`<br>sha256 `49dba24f3742618a8849deffd1ced19f6f4706154dc7df3fce837b54eb1f4d0b` |
| Upstream | [libretro/FBNeo](https://github.com/libretro/FBNeo) at commit `74a9797` ("(libretro) update files", 2025-03-01); the same commit also exists in [finalburnneo/FBNeo](https://github.com/finalburnneo/FBNeo), where the drivers live. Full hash: `74a979724da9a3c4c8986076123c3293861614c5` |
| License | FBNeo non-commercial license. Free to use, but you may not sell it. See [License](#license) |
| Tested on | Anbernic RG35XX Pro (H700, aarch64, 1 GB RAM) · KNULLI · RetroArch 1.22 |

> **Unofficial modified build.** Please do not ask the FBNeo developers about problems with this build. No ROMs, BIOS files or saves are included in this repository; use only ROMs you own.

## What it does

FBNeo is the all-in-one arcade core in RetroArch. We did not rebuild it: we changed 9 bytes in the stock binary that came with the device, to fix two problems.

- **Taito F3 netplay drifted apart, and it was heavy.** In netplay the host sends its state to the guest. The small save chip that holds a game's settings and high scores (the EEPROM) was not part of that state, so the two sides disagreed and the picture and progress soon diverged. The state itself was also needlessly big (4.8 MB, because it included 4 MB of DSP delay memory that FBNeo's F3 emulation never uses), and since rewind copies a state every frame, the host needed about 710 MB of RAM (measured in a virtual machine), which is a lot for a handheld with 1 GB. On top of that, a coin could vanish or shift after a rewind, or when a guest loaded the host's state.
- **Player 2's up and down did nothing in one arcade game** (`grainbow`). Up (jump) and down (crouch) for player 2 never worked, because the game's input table pointed other buttons at the same bits.

The changes are so small that the "patches" are two Python scripts instead of source patches.

## What we changed

The stock core came with the device image: md5 `fa5feb62b5d8c4f9a71786bc649409cd`, version string `v1.0.0.03 74a979724`, built with GCC `Ubuntu/Linaro 7.5.0`. We did not build it, and we could not find out which build server or command produced it. **So the byte patches fit only this exact file.**

The order is: stock core `fa5feb62` → step 1, `patch_fbneo.py` → `9e31af94` → step 2, `patch_grainbow.py` → **`c942499f`**. File offsets below are counted from 0.

1. **`eeprom`: the EEPROM travels with the netplay state** (`patch_fbneo.py`; one instruction at file offset `0x158ce60`, and the byte that actually changes is `0x158ce62`). `EEPROMScan` added `eeprom_data` (the 1,024 bytes of EEPROM) to the state only in the run-ahead context (`ACB_RUNAHEAD`, bit 7). The patch changes `tbnz w24,#7` to `tbnz w24,#9`, which moves it to the netplay-state context (`ACB_NET_OPT`, bit 9). On a device that does not use run-ahead, the regular state layout stays the same. **This affects every FBNeo game that uses an EEPROM**, not only F3.
2. **`dram`: leave out 4 MB nobody uses** (`patch_fbneo.py`; file offset `0x2743940`, 2 bytes). The Taito F3 `DrvScan` saved "All Ram" from the start up to `TaitoRamEnd`, which includes the 4 MB `TaitoES5510DRAM` delay memory. FBNeo's ES5510 does not run the DSP, so that memory is never used. `ldr x6,[x4,#2632]` becomes `ldr x6,[x4,#4560]`, so the length now ends where `TaitoES5510DRAM` starts. The state shrinks from 4,825,160 to 631,880 bytes. **This also changes the layout of regular F3 save states**: old F3 states cannot be loaded.
3. **`coin`: level instead of edge** (`patch_fbneo.py`; file offset `0x2742f0c`, 4 bytes). F3 `DrvFrame` counts a coin only if it was not pressed in the previous frame, using `previous_coin`, a static variable that is not part of the state. After a rewind, or when a guest loaded the host's state, coins could vanish or shift. `ldrb w17,[x9,#48]` becomes `mov w17,#0`, so the previous value always reads 0 and the signal stays on as long as the button is held, the way MAME's F3 driver works.
4. **`grainbow`: the input table** (`patch_grainbow.py`; file offsets `0x29c768` and `0x29c9a8`, 1 byte each). In `GrainbowInputList` (`d_legionna.cpp`), `P3 Start` and `P4 Start` pointed at the same bits as `P2 Up` and `P2 Down` (`DrvJoy1+8` and `DrvJoy1+9`). The table's two relocation addends change from `DrvJoy1+8` and `DrvJoy1+9` to `DrvJoy3+8` and `DrvJoy3+9` (`f8` to `d8`, `f9` to `d9`). Those are the real START3 and START4 bits: `0x0100` and `0x0200` of the system port at `0x10074c`, which are `DrvJoy3` bits 8 and 9.

Both scripts have safety checks. `patch_fbneo.py` writes only if the input file's md5 is `fa5feb62b5d8c4f9a71786bc649409cd` and each spot to change holds the expected old value. `patch_grainbow.py` writes only if it finds the input table and it resolves to exactly one match. Otherwise nothing is written.

### Results

| What | Result |
|---|---|
| Running the scripts in order | The stock core `fa5feb62` becomes `9e31af9441611566af6d61cee10a1e7b` and then **`c942499fc72a61400d4e6a486841fb37`**, exactly, and that is byte-for-byte the file installed on the devices (rechecked 2026-10-29). |
| F3 netplay (two RetroArch 1.22.2 instances connected in a virtual machine, comparing the state CRC every frame) | Stock core: the EEPROM is not in the state, so the guest diverges. `eeprom` alone: diverges because of the coins. **All three fixes: no game-state divergence over 3,500+ frames** (only the sound chip differed). State 4,825,160 to 631,880 bytes, host memory about 710 MB to about 200 MB, one state save 1.08 ms to 0.13 ms (in the virtual machine). |
| Settings used with it | Per-game `netplay_input_latency_frames_min=2` and `netplay_input_latency_frames_range=2` (input latency 2 / 2); the number of rewinds dropped by 44~61%. |
| A Taito game that is not F3 | The game state did not diverge on the stock core either (only values inside the sound chip differed), so it is outside the scope of these patches. |
| Two real devices | One representative F3 game: coins and screens matched, 54 fps (the same as playing alone), host RAM about 330 MB (2026-10-25). The build with the input-table fix was installed on both devices and checked on one of them (2026-10-26). |
| Input-table fix | In the service-menu input test screen, the stock core lit the `P-2 UP` cell for P3 START and the `P-2 DOWN` cell for P4 START; the fixed core lights the ST3 and ST4 cells. In a 40-frame input test, the screen-change score for player 2 up / down went from 0 (stock core) to 1221 / 1671 (fixed core). Nine other games showed identical screen and state hashes. |

### Known limits

- The `eeprom` fix **overwrites the guest's EEPROM (settings and high scores) with the host's.** When the game ends, the host's values can get saved on the guest's device. We used a hook that restores the guest's `.nv` and `.fs` save files after play (see [Companion scripts](#companion-scripts)).
- The `coin` fix changes how the coin signal works. We confirmed that the credit count matches on both devices, but there is no record of checking that one press gives exactly one credit.
- After the `dram` fix, **old F3 state files cannot be loaded** (before installing, we confirmed there were 0 F3 save-state files on both devices).
- The input-table fix does not make that game a three-player game. The original is a two-player game, and P3 and P4 START only show up in the service-menu input test.
- This is a prebuilt file that was patched, not a source rebuild. The source-level changes under [Build from source](#build-from-source) mean the same thing, but they have not been compiled or tested.

## Core options

None added or changed. The per-game RetroArch settings we used with it are in step 4 of the install notes below.

## Install on KNULLI

Download `arcade-fbneo-linux-aarch64.zip` from the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest) and unzip it. This is how we installed it:

1. **Where the file goes:** `/userdata/system/hanbang_cores/fbneo_libretro.so` (default path used by the prebuilt files), on the SD card. The file RetroArch looks for, `/usr/lib/libretro/fbneo_libretro.so`, is a **symlink** to it. The reasons the core lives on the SD card, and why that folder must not be deleted, are the same as in the [MAME folder](../arcade-mame2003-plus/README.md#install-on-knulli).
2. **Swapping the file:** only while no game is running (EmulationStation's local web API reports `runningGame` as "NO GAME"). Copy the new file over as `fbneo_libretro.so.hbnew`, check the md5, then `chmod 755`, `mv -f` and `sync`. We kept the stock file on the device as `fbneo_libretro.so.old_<first 8 digits of its md5>`.
3. **Both devices must run the same file.** The F3 state size changes, so if only one side is patched, the guest cannot join or drifts.
4. **Per-game settings** (`knulli.conf`): for the three Taito games we tested (two F3 games and one 8-bit board) we added two lines: `arcade["<ROM name>.zip"].retroarch.netplay_input_latency_frames_min=2` and `arcade["<ROM name>.zip"].retroarch.netplay_input_latency_frames_range=2`.
5. **Protect the guest's saves:** because of the `eeprom` fix, the guest's EEPROM and NVRAM get the host's values, so install the hook script as well (see [Companion scripts](#companion-scripts)).
6. **Check:** the md5. To roll back, put the saved file back.

### Other devices and systems

- **`patch_fbneo.py` fits only the stock core `fa5feb62b5d8c4f9a71786bc649409cd`.** Other FBNeo builds (a different version, compiler or RetroArch build server) have different offsets and the script stops. Please do not force the values. `patch_grainbow.py` finds the input table by itself, so it may work on other aarch64 FBNeo builds with the same structure, but we only confirmed it on this build.
- The file is for aarch64 Linux only (glibc 2.17 or newer is enough). For other CPUs or operating systems, build the source for that device.
- We only tested with the same file on both devices. Because of `dram`, the F3 state layout differs from upstream's.
- Because of `eeprom`, **the guest's save files get overwritten with the host's values.** If every player has to keep their own saves on their own handheld, you need the hook (or something that does the same job).
- `eeprom` affects every FBNeo game that uses an EEPROM (1 KB more goes into the state), while `dram` and `coin` only affect Taito F3. Neo Geo does not call `EEPROMScan` and is not F3, so by our analysis the changed code does not run for it (we did not test Neo Geo games separately).
- The devices also carry a separate, newer official FBNeo core (`fbneo2026`); we did not patch that one.

### Companion scripts

Both are in [`knulli-scripts/`](../../knulli-scripts/).

- [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) is the game start / stop hook. Its section 23 (protecting the `.nv` and `.fs` files of an FBNeo netplay guest) is the partner of the `eeprom` fix. Install the hook as `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files) and the other scripts in `/userdata/system/claude/` (default path used by the prebuilt files).
- [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py) writes in-game saves to a file right away during netplay (the hook passes the guest marker on to this file).

## Build from source

There is nothing to compile. The shipped file is the stock binary with 9 bytes changed, so the "patches" are two Python scripts. You only need Python 3 (run with `python3 -I`).

```sh
python3 -I patches/patch_fbneo.py    <stock fbneo_libretro.so, md5 fa5feb62b5d8c4f9a71786bc649409cd>  step1.so            # md5 9e31af9441611566af6d61cee10a1e7b
python3 -I patches/patch_grainbow.py step1.so                                                          fbneo_libretro.so   # md5 c942499fc72a61400d4e6a486841fb37
```

- `patch_fbneo.py` installs all three fixes (`eeprom`, `dram`, `coin`) at once. A third argument, a comma-separated choice from `eeprom,dram,coin`, installs only some of them.
- Both scripts write a new file; the input file is left untouched.
- The stock core `fa5feb62` is the prebuilt file from the device image. We do not know which build server or command produced it, which is why the byte patches fit only this exact file.

### Source-level equivalents (for reference)

If a byte patch is not possible for your build, these source changes mean the same thing. The paths were checked against upstream `master` on 2026-10-29; they have not been compiled or tested.

- `src/burn/drv/pst90s/d_legionna.cpp`: in `GrainbowInputList`, point `P3 Start` and `P4 Start` at `DrvJoy3 + 8` and `DrvJoy3 + 9`.
- `src/burn/devices/eeprom.cpp`: in `EEPROMScan`, scan `eeprom_data` not only for `ACB_RUNAHEAD` but also for `ACB_NET_OPT` (our binary patch swaps the first for the second).
- `src/burn/drv/taito/d_taitof3.cpp`: in `DrvScan`, leave the `TaitoES5510DRAM` block out of the "All Ram" length, and either put `previous_coin` into the state (`SCAN_VAR`) or stop using it, as we did.

## Patches

Run them in the order of [`patches/series`](patches/series). The header comments inside the scripts are in Korean.

| Order | File | What it does |
|---|---|---|
| 1 | `patches/patch_fbneo.py` | Byte-patches three spots in the stock core (`eeprom`, `dram`, `coin`; 7 bytes). Refuses to write unless the input file's md5 is `fa5feb62b5d8c4f9a71786bc649409cd` and every spot holds the expected old value. Result md5: `9e31af9441611566af6d61cee10a1e7b`. |
| 2 | `patches/patch_grainbow.py` | Finds the `GrainbowInputList` table by itself and changes two relocation addends (`DrvJoy1+8` and `DrvJoy1+9` to `DrvJoy3+8` and `DrvJoy3+9`; 2 bytes). Refuses to write unless exactly one table is found. Result md5: `c942499fc72a61400d4e6a486841fb37`. |

### What is verified, and what is not

- **Verified:** running the two scripts in order on the stock core gives a file that is byte-identical to the one on the devices. All four issues are still present on upstream `master`. The commit hash is the same in both repositories, libretro/FBNeo and finalburnneo/FBNeo (checked through their APIs on 2026-10-29). The evidence for the input-table fix is the service-menu test screen and the 40-frame input test.
- **Not verified:** where the stock core came from (build server, command line); rebuilding the fixes from source and testing them; whether one press of the `coin` fix gives exactly one credit; and F3 netplay with only `dram` or only `coin` installed (we did try `eeprom` alone, `eeprom` plus `dram`, and all three).

## Upstream status

Checked against upstream `master` (finalburnneo/FBNeo) on 2026-10-29: **all four issues are still there.** Nothing has been sent yet. English PR drafts and the reasoning are in [`../MANIFEST.arcade.jsonl`](../MANIFEST.arcade.jsonl) (`upstream_pr_candidate` and `more_pr_candidates`) and are summarized in [`UPSTREAM.md`](../../UPSTREAM.md).

| Fix | On upstream |
|---|---|
| Input table (`grainbow`) | `GrainbowInputList` in `d_legionna.cpp` still has `P3 Start = DrvJoy1 + 8` and `P4 Start = DrvJoy1 + 9`, overlapping `P2 Up` and `P2 Down`. That file was last changed on 2026-10-02. |
| `eeprom` | `EEPROMScan` still scans `eeprom_data` only under `ACB_RUNAHEAD` (the recording flag `ACB_EEPROM` is separate). The `ACB_NET_OPT` flag exists but is not used there. |
| `dram` | The "All Ram" range in F3 `DrvScan` still runs from `TaitoRamStart` to `TaitoRamEnd`, ES5510 DRAM included. |
| `coin` | `previous_coin` is still a `static UINT8` outside the state and is not saved with `SCAN_VAR`. |

- **The input-table fix is the one clear bug fix and worth sending.** It is two lines and still present upstream. The evidence: the service-menu input test screen, the 40-frame input test, MAME's system port `0x10074c` (START3 and START4 are `0x0100` and `0x0200`, which are `DrvJoy3` bits 8 and 9), and the check on nine other games. One caution: we verified it by changing 2 bytes in a prebuilt core, so it needs a source-build check before we send it. The place to send it is finalburnneo/FBNeo, where the drivers live.
- **The three F3 netplay fixes should not go in as a PR yet.** We tested them only as byte patches on a prebuilt file, in a virtual machine and on two devices, and `coin` changes the meaning of the coin signal (level instead of edge). Rebuild them from source and test first, then open an issue that describes what we saw (state size, divergence, EEPROM) and ask the maintainers for their opinion.

## License

FBNeo is under the **FBNeo non-commercial license** (upstream `src/license.txt`; this repository keeps a copy at [`LICENSES/FBNeo_src_license.txt`](../../LICENSES/FBNeo_src_license.txt)). The scripts and the patched core follow the same terms. In short:

- You may not sell, lease or rent it, or use it to make money, in source or binary form. **Selling a device or memory card with this core on it is not allowed either.**
- Changes to the source must be made public. The scripts here and the description above are our changes.
- When you distribute it, you must include the full license text verbatim. This repository keeps a copy in `LICENSES/`, so ship that along with any binary you pass on.
- You may not distribute it with ROM images unless you have the right to distribute them. You may not ask for donations to support work on a project that uses the FBNeo source.
- The original Final Burn terms (non-commercial, keep the copyright notices, publish the source or link to it) and MAME's license (for the parts that use MAME code) apply as well.
- The scripts in this folder contain no FBNeo source, but the patched binary is a derivative of FBNeo and follows the terms above.
