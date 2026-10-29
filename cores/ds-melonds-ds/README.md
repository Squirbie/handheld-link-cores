<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# melonDS DS — big ROMs, steady netplay, DraStic-style controls

> A patched melonDS DS libretro core for the Anbernic RG35XX Pro running KNULLI: 256–512 MB ROMs no longer crash for lack of memory, two-device netplay stops dropping, and the pop-up screen and controls work like DraStic's.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/ds-melonds-ds-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `melondsds_libretro.so` (linux aarch64, 5,546,496 bytes) |
| Version | upstream v1.4.0 plus six patches (we call this final build "v2") |
| md5 | `e0f45595139d4c81ce8b442498c4f6ad` (release copy; the device build is `5443e0001602467348f4df9ea42c5849` — they differ only in 8 embedded build-path strings, which the release copy has neutralized) |
| Upstream | [JesseTG/melonds-ds](https://github.com/JesseTG/melonds-ds) v1.4.0 (`f394adb`)<br>Engine, fetched by the upstream build and **not modified**: [JesseTG/melonDS](https://github.com/JesseTG/melonDS), branch `jtg/fix-uninitialized-opengl` (`16f127d`) |
| License | GPL-3.0 (same as upstream) |
| Tested on | Anbernic RG35XX Pro (H700, Cortex-A53, 1 GB RAM) · KNULLI |

## What it does

[melonDS DS](https://github.com/JesseTG/melonds-ds) is the libretro port of the melonDS Nintendo DS emulator. This build fixes the problems we ran into on the RG35XX Pro and adds the controls that DraStic users are used to.

- **Big ROMs no longer crash.** Pokémon Black, White, Black 2, White 2 and Dragon Quest IX (256–512 MB ROMs) used to be killed for running out of memory, because the ROM was copied three times (by RetroArch, by the core and by the emulator). The core now maps the ROM file straight into memory instead of copying it. Pokémon Black went from 775 MB to 557 MB of memory use, and Black 2 now starts (measured on the device, 2026-10-07).
- **Two-device play no longer drops.** When two slow handhelds linked up over Wi-Fi, the host gave up on the other side's reply too early and the game cut the connection. The wait is now timed on the wall clock at 150 ms, and a blank "not ready" reply counts as an answer and ends the wait (the same as in upstream melonDS). A two-device Mario Kart DS race ran with zero timeouts (about 22 fps in the race and 29 fps in the lobby, 2026-10-08).
- **L2 = pop-up screen.** In a layout that shows only one screen, holding L2 slides the other screen up from the bottom as a translucent window (75% size, rounded corners). Double-tap L2 within 350 ms and the window stays up (pinned) until the next L2 press. It is modeled on the pop-up screen in melonDS for Android.
- **DraStic controls.** R2 swaps which screen is big, R3 presses the pen (the right stick moves it), and SELECT + Left/Right cycles through the screen layouts. We turned off the doubled pen speed while L2 is held, and we turned off the L2 + Y shortcut that closed the DS lid and put the game to sleep (L2 is the pop-up key, so it was easy to hit by accident).
- **Small screen in the corner.** While one screen is big, the other stays visible in the top-left corner at 1/4 size with a green border, just like DraStic's default layout.
- **(v2) Pop-ups that follow the stick.** With the top screen big, pushing the right stick brings up the touch window (the bottom screen) by itself. With the bottom screen big, using the stick fades the L2 window so the pen underneath shows through. Tiny icons in the window's corner show what it is (finger = touch window, eye = view window, pin = pinned). A `pip=` option keeps text on the small screen from turning to mush.
- **Small fixes.** The pen no longer switches itself off after 3 seconds of holding the stick at the same force, and a few variables that were never initialized are now initialized.

On the H700 this core is slower than DraStic (25–60 fps depending on the game), so we run most DS games on DraStic or [DSperate](../ds-dsperate/) and pick this core per game.

## What we changed

Every patch touches only files under `src/libretro/` in the upstream repository; the melonDS engine that the upstream build downloads is unmodified. In the patches, names containing `hb_`, `hanbang` and similar (`hanbang.hpp`, `hb_popup.cfg`, the `[hanbang]` log prefix) are only our marker for "changed here". We left them as they are so that patches, binaries and scripts stay consistent.

1. **ROM file mapping** (`retro/info.{cpp,hpp}`, `info.cpp`, `core/core.cpp`, `config/console.cpp`). The NDS content info now asks for `need_fullpath=true` and `persistent_data=false` (GBA is unchanged). When the frontend hands over only a path, `GameInfo` maps the file read-only with `mmap`. For ROMs of 32 MiB or more it reserves a power-of-two-sized region with `posix_memalign` and maps the ROM file over it with `MAP_PRIVATE|MAP_FIXED`; that region serves as the cart buffer, which removes the two copies (`CopyToUnique` and `PadToPowerOf2`). If anything fails, it falls back to copying as before.
2. **Netplay timing** (`net/mp.{cpp,hpp}`, `libretro.cpp`, `core/core.hpp`). The wait for a client's reply was timed with `std::clock` (process CPU time) with a 25 ms budget. It now uses `steady_clock` with 150 ms (adjustable from 5 to 2000 ms with `MELONDSDS_MP_TIMEOUT_MS`) and yields while it waits. Each received packet is tagged with the sending client's number, and `MpState::ReplyAid()` ties a blank reply (AID 0) to that client, so `MP_RecvReplies` counts a blank reply as "answered" without copying any data from it.
3. **L2 pop-up** (`render/software.{cpp,hpp}`, `input/{input,joypad}.hpp`). In single-screen layouts (top only or bottom only), `DrawPopup()` draws the other screen while L2 is held: 75% size, about 85% opaque, rounded corners (radius 6), bilinear scaling, sliding up over 9 frames. In the top-only layout it also draws the touch cursor inside the window.
4. **Lid-close hotkey off** (`input/{joypad,input}.cpp`). L2 + Y (close lid) is always disabled, and the control label `Y / Close Lid` becomes `Y`.
5. **DraStic-style controls and small screen** (`input/{joypad,input}.{cpp,hpp}`, `screenlayout.{cpp,hpp}`, `render/software.{cpp,hpp}`, `core/tasks.cpp`). R2 = `SwapScreens` (layout index `^1`), R3 = touch. SELECT + Right/Left = next/previous layout, including switching the small screen on and off; Left/Right are not sent to the DS while SELECT is held. Two L2 presses within 350 ms pin the pop-up (`steady_clock`). `DrawPictureInPicture()` draws the other screen at 1/4 size with an opaque green border (`0xFF03CF03`) and the touch cursor. The on-screen layout notice is turned off, and `_layoutIndex` and `_layouts` are now initialized.
6. **UI v2** (the files above, plus the new `hanbang.hpp` and changes in `input/cursor.cpp`, `platform/mp.cpp`, `libretro.cpp`, `net/mp.cpp` and `core/core.cpp`). The draw order is tidied up (big screen, small screen, pen, window, corner icons, pen inside the window). Added: the automatic touch window (D), fading (C), corner icons (11×11 dots), area-average downscaling of the small screen (`pip=0/1/2`; mode 2 outputs 512×384, and during multiplayer the mode drops to 1 automatically), a horizontal sample table for the window, L2 pen acceleration off, a fix for the timer that hides the stick pen, reading `hb_popup.cfg`, and a multiplayer timing log.

More detail is in the comments inside the patches (a mix of Korean and English).

## Core options

### `nds.opt`

`/userdata/system/configs/retroarch/config/melonDS DS/nds.opt` — the options we changed or care about:

| Option | Value we use | Notes |
|---|---|---|
| `melonds_number_of_screen_layouts` | `"2"` | |
| `melonds_screen_layout1` | `"bottom"` | was `"top"` |
| `melonds_screen_layout2` | `"top"` | was `"bottom"` |
| `melonds_render_mode` | `"software"` | The pop-up and the small screen are drawn by the software renderer only |
| `melonds_jit_enable` | left on | |
| `melonds_threaded_renderer` | left on | |
| `melonds_mac_address_mode` | do not use | It rewrites `firmware.bin` when the game closes |

The default view is a big bottom screen with the top screen small in the top-left corner. SELECT + Right steps through `bottom + small screen → top + small screen → bottom only → top only`.

### Pop-up settings file (optional)

`/userdata/system/configs/advanced_drastic/hb_popup.cfg` is the same file the DraStic-side pop-up reads. The core reads it once when a game starts, and uses the defaults below if the file or a line is missing. Unknown lines are skipped. Set the environment variable `MELONDSDS_HB_POPUP_CFG=<path>` to read a file from another location.

| Key | Default | Meaning |
|---|---|---|
| `auto` | `1` | With the top screen big, pushing the right stick opens the touch window by itself (`0` = off) |
| `fade` | `40` | Opacity (%) of the L2 window while you use the stick with the bottom screen big |
| `alpha` | `85` | Window opacity (%) |
| `pip` | `1` | How the small screen is shrunk: `0` nearest pixel, `1` area average, `2` render at double size and average (sharpest, slightly heavier) |

### Controls (what changed in this core)

| Button | Action |
|---|---|
| Hold L2 | The other screen appears as a translucent window (in single-screen layouts) |
| Double-tap L2 (within 350 ms) | Pins the window; the next L2 press releases it |
| R2 | Swap the big screen (top/bottom) |
| Right stick · R3 | Move the pen · press the pen |
| SELECT + Right / Left | Next / previous screen layout (Left/Right are not sent to the game meanwhile) |
| L2 + Y | Nothing (lid closing is disabled) |

### Diagnostic switches

These take effect within 1–2 seconds, without quitting the game.

| Switch | Effect |
|---|---|
| `echo 2 > /tmp/melonds_pip` | Change the small-screen mode right away (0, 1 or 2). `rm /tmp/melonds_pip` goes back to the value from the settings file. The environment variable `MELONDSDS_PIP` works too. |
| `touch /tmp/melonds_mp_stats` | Writes one multiplayer statistics line per second to `/tmp/melonds_mp_stats.log`: frames, emulation time, time waiting for the link, packets sent and received, timeouts and more. `rm` the file to stop; it also stops by itself above 20 MB. While the file doesn't exist, the cost is two `stat` calls every 60 frames. The meaning of each field is written in the `#` lines at the top of the log. |
| `MELONDSDS_MP_TIMEOUT_MS=<5–2000>` | Multiplayer reply timeout in milliseconds (150 by default). |

## Install on KNULLI

This is how we install it. Download `ds-melonds-ds-linux-aarch64.zip` from [Releases](https://github.com/Squirbie/handheld-link-cores/releases) and unzip it.

1. **Put the file in place.** Copy `melondsds_libretro.so` to `/userdata/system/hanbang_cores/` (default path used by the prebuilt files), which is on the SD card. RetroArch looks for the core at `/usr/lib/libretro/melondsds_libretro.so`, so make that path a **symlink** to the copied file. KNULLI's system partition is read-only, so after creating the symlink, save it into the overlay with `knulli-save-overlay`. (The core lives on the SD card because the overlay is a RAM disk, and a big file there would eat memory. If you delete that folder, the core won't start.) Before the first swap, back up the original file as `melondsds_libretro.so.orig` (ours was the official v1.4.0 linux-arm64 build). The core name stays the same. For the record, we also set the version shown in the `.info` file to 1.4.0; that isn't required.
2. **Pick this core per game.** In EmulationStation, choose "melonDS DS" as that game's core, or add two lines to `knulli.conf`:
   ```
   nds["<ROM file name>.zip"].emulator=libretro
   nds["<ROM file name>.zip"].core=melondsds
   ```
3. **Set the core options** in `nds.opt` as described under [Core options](#core-options).
4. **Pop-up settings (optional).** Create `hb_popup.cfg` if you want values other than the defaults.
5. **Check it.** Compare the file's md5. When a game starts, the standard-error (stderr) log should contain one line like `[hanbang] popup cfg …: auto=… fade=… alpha=… pip=…`; that line means this build is running.
6. **Undo.** Put the backed-up `melondsds_libretro.so.orig` back. To turn off only the pop-up behavior, put `auto=0`, `fade=85` and `pip=0` in `hb_popup.cfg`.

### Companion scripts (optional)

Two-device play and save syncing use a few helper scripts from [`knulli-scripts/`](../../knulli-scripts/) in this repository. Copy them to `/userdata/system/claude/` (default path used by the prebuilt files); the EmulationStation hook goes to `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files). Keep only that one file in the `scripts` folder, because everything in it gets run.

- [`nds_save_sync.py`](../../knulli-scripts/nds_save_sync.py) and [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) — keep DraStic saves (`.dsv`) and this core's saves (`.srm`) in sync for the same game.
- [`hb_dsmac.py`](../../knulli-scripts/hb_dsmac.py) — gives each device its own DS wireless address.
- [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py) — writes in-game saves to the file right away during netplay.
- [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py) — when a room for the same game is open, shows a "join / play solo" window.
- [`hb_direct.py`](../../knulli-scripts/hb_direct.py) — links the devices directly during link play, without going through the router.
- The DraStic-side pop-up (`hb_dsosd`) reads the same `hb_popup.cfg`; it is not part of this repository.

### Other devices and operating systems

- **Build environment.** The file was built with GCC 12.2 on Debian 12 and needs glibc 2.34 or newer and libstdc++ 3.4.29 or newer. On older Linux, rebuild from the patches. It ran fine on KNULLI (glibc 2.40). Android, Windows and macOS can't use this file; apply the patches to the upstream source and build for that platform.
- **CPU.** It is built with `-mcpu=cortex-a53`. It will probably run on other ARMv8 CPUs too, but we only tested a Cortex-A53. It uses the ARM64 JIT, so on an OS that can't create executable memory (`PROT_EXEC`) you have to set `melonds_jit_enable = "disabled"`, which is much slower.
- **ROM mapping (patch 0001) assumes glibc.** It relies on `posix_memalign` handing out a big region that `free()` later unmaps as a whole. On musl, bionic (Android), Windows or macOS, fix or drop patch 0001. The frontend must pass the **file path** (`need_fullpath`); without a path, or if mapping fails (this includes ROMs under 32 MB), the core copies the ROM as before.
- **`hb_popup.cfg` and the `/userdata/...` paths are KNULLI's.** On another OS, point to the file with `MELONDSDS_HB_POPUP_CFG`.
- The pop-up and the small screen are drawn by the **software renderer** only (this build has OpenGL off).
- **Link play** runs through RetroArch netplay (netpacket) between two devices. Both must run the same patched core and be on the same network. Each device needs a **different DS wireless address (MAC)**; copying the firmware file wholesale makes them identical and causes a join error (`knulli-scripts/hb_dsmac.py` gives each device its own). Don't use the core option `melonds_mac_address_mode`, because it rewrites `firmware.bin` when the game closes. We only tested link play with the same patched core on both sides.
- **Speed.** On this device (H700) it is slower than DraStic, at 25–60 fps depending on the game.

## Build from source

We built it in a Debian 12 (aarch64, glibc 2.36) virtual machine with CMake and Ninja.

```sh
git clone https://github.com/JesseTG/melonds-ds.git
cd melonds-ds
git checkout v1.4.0            # f394adbacb5722ee97c1b37c8064da9a25818310
while read -r p; do git apply --check "/path/to/patches/$p" && git apply "/path/to/patches/$p" || break; done < /path/to/patches/series

# CMake downloads the engine itself. If the upstream branch has moved, pin it to 16f127db by adding
#   -DFETCHCONTENT_SOURCE_DIR_MELONDS=<melonDS checkout at 16f127dbb587a73371827ce79689c5d237c4b59b>
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS="-mcpu=cortex-a53" -DCMAKE_CXX_FLAGS="-mcpu=cortex-a53" \
  -DCMAKE_C_FLAGS_RELEASE="-O3 -DNDEBUG" -DCMAKE_CXX_FLAGS_RELEASE="-O3 -DNDEBUG" \
  -DCMAKE_SHARED_LINKER_FLAGS="-Wl,-z,nodelete" -DCMAKE_MODULE_LINKER_FLAGS="-Wl,-z,nodelete" \
  -DENABLE_JIT=ON -DENABLE_LTO_RELEASE=ON -DENABLE_NETWORKING=ON \
  -DENABLE_OPENGL=OFF -DENABLE_OGLRENDERER=OFF -DENABLE_THREADED_RENDERER=ON
cmake --build build --target melondsds_libretro
readelf -d build/src/libretro/melondsds_libretro.so | grep FLAGS_1     # NODELETE should show up
```

- The engine is the `jtg/fix-uninitialized-opengl` branch of [JesseTG/melonDS](https://github.com/JesseTG/melonDS), which `cmake/FetchDependencies.cmake` (line 44) points to in v1.4.0. At build time it was commit `16f127dbb587a73371827ce79689c5d237c4b59b` (parent `906e9ebb27da8c6a715cd7abab4abfe8a8d29427`), and the branch tip was still the same commit on 2026-10-29. A branch can move, so pin this commit when you rebuild.
- Compiler and flags: GCC 12.2 (Debian 12, aarch64), `-O3 -mcpu=cortex-a53`, JIT on, OpenGL off, `-Wl,-z,nodelete`.
- The `cmake` line above is our build folder's CMake settings (`CMakeCache.txt`), tidied up. The command line typed for the first configuration wasn't recorded.
- **Keep `-Wl,-z,nodelete`.** On the RG35XX Pro, a build without it (we tried one built with zig) made RetroArch exit with code -11 every time a game was closed, and the flag brought it back to 0. We kept it for the GCC build for the same reason. After building, check that `NODELETE` is there.
- On a machine or VM with only about 3 GB of RAM, the final LTO link (`-flto=auto` uses every CPU) can run out of memory. We compiled with `ninja -j2` and ran the link command by hand with `-flto=2` instead of `-flto=auto`.
- Even in the same environment, the md5 is not guaranteed to come out identical (LTO, build paths).

## Patches

Apply them in numeric order (the order is also listed in [`patches/series`](patches/series)). The file hashes that each patch expects at its start (the git blob hashes on its `index` lines) match the hashes recorded after the previous patch, with no gaps.

| Order | File | What it does |
|---|---|---|
| 1 | [`0001-rom-file-mapping.patch`](patches/0001-rom-file-mapping.patch) | Maps big ROM files into memory instead of copying them, so Pokémon Black/White (1 and 2) and similar ROMs no longer run out of RAM |
| 2 | [`0002-netplay-wallclock-timeout-and-blank-replies.patch`](patches/0002-netplay-wallclock-timeout-and-blank-replies.patch) | Netplay: reply timeout on the wall clock (150 ms), and blank replies count as answers |
| 3 | [`0003-l2-popup.patch`](patches/0003-l2-popup.patch) | Hold L2 for a translucent pop-up of the other screen; a double tap pins it |
| 4 | [`0004-lid-close-hotkey-off.patch`](patches/0004-lid-close-hotkey-off.patch) | Turns the L2 + Y lid-close hotkey off |
| 5 | [`0005-drastic-style-controls-and-pip.patch`](patches/0005-drastic-style-controls-and-pip.patch) | DraStic-style controls (R2 swap, R3 touch, SELECT + Left/Right layouts) and the small screen in the top-left corner |
| 6 | [`0006-ui-v2-auto-popup-badges-pip-quality-mp-stats.patch`](patches/0006-ui-v2-auto-popup-badges-pip-quality-mp-stats.patch) | UI v2: stick-driven pop-ups, corner icons, a sharper small screen, `hb_popup.cfg`, and the multiplayer timing log |

**Why these six are the final set**

- There is no single combined patch. The core was built by stacking patches. The final build (`5443e000`, "v2") differs from the previous build (`aa068ff8`, which had patches 0001–0005) by patch 0006, and 0006 starts from exactly the file hashes that 0001–0005 produce.
- 0006 is the diff of two commits (`1c90e0b`, `688ed5a`, on top of `88bf8ab`) on a branch in our build VM's private repository; `88bf8ab` is the previous build. Those commits aren't in any public repository, which is why the diff is kept here as a patch.
- The strings inside the core file match: `hanbang: mapped … ROM file` (0001), `MELONDSDS_MP_TIMEOUT_MS` (0002), `Pop-up Screen (hold, double-tap = pin)` and `Swap Screens` (0005, 0006), and `MELONDSDS_PIP`, `/tmp/melonds_mp_stats` and `[hanbang] popup cfg …` (0006) are present. The old `Y / Close Lid` (removed by 0004) and the layout notice `Layout {}/{}` (removed by 0005) are not. `readelf` shows `NODELETE` in `FLAGS_1` (checked on `5443e000`).
- This file was installed on the test device and tried on 2026-10-12.

**What we checked, and what we didn't**

- Checked: all 20 starting file hashes in the six patches equal the v1.4.0 tree's hashes for the same files (2026-10-29, compared from repository metadata only); the chain of hashes between patches has 0 breaks; the final core's strings match; `NODELETE` and the required libraries are present; and the patch format is intact (`git apply --numstat`).
- Not done: we did not download the upstream source for this release and run `git apply --check` (we only compared hashes), and we did not compare with the latest upstream `main`.

<details>
<summary>File hash chain (for verification)</summary>

The git blob hashes recorded on the patches' `index` lines: the file at `v1.4.0`, and after the last patch that touches it (paths relative to `src/libretro/`). Where several patches change a file, all their numbers are listed. The recorded values describe the files as built. A little comment text in the patches was edited for publication after the build, so a file you get by applying the patches can hash differently from the recorded final value.

| File | v1.4.0 | Recorded final | Patches |
|---|---|---|---|
| `config/console.cpp` | `73b7e24` | `722a08c` | 0001 |
| `core/core.cpp` | `df32f07` | `91de02b` | 0001, 0006 |
| `core/core.hpp` | `bb52319` | `7e382dc` | 0002 |
| `core/tasks.cpp` | `87bfa2a` | `d3d1dc9` | 0005 |
| `hanbang.hpp` | (new file) | `62a22da` | 0006 |
| `info.cpp` | `9ba200b` | `c5b1fca` | 0001 |
| `input/cursor.cpp` | `98b8766` | `d69063a` | 0006 |
| `input/input.cpp` | `0b0b101` | `a805d5c` | 0004, 0005, 0006 |
| `input/input.hpp` | `c37e7a6` | `2d6c188` | 0003, 0006 |
| `input/joypad.cpp` | `fabccaa` | `7d6b4a7` | 0004, 0005, 0006 |
| `input/joypad.hpp` | `6a571be` | `10bd6e9` | 0003, 0005, 0006 |
| `libretro.cpp` | `b56f23a` | `388d36d` | 0002, 0006 |
| `net/mp.cpp` | `caa185d` | `f714193` | 0002, 0006 |
| `net/mp.hpp` | `f6b5dfc` | `807b7b4` | 0002 |
| `platform/mp.cpp` | `30ee4c2` | `432d88b` | 0006 |
| `render/software.cpp` | `0884b70` | `91bb791` | 0003, 0005, 0006 |
| `render/software.hpp` | `c08c753` | `cd8c1d8` | 0003, 0005, 0006 |
| `retro/info.cpp` | `c55aa81` | `e885d9c` | 0001 |
| `retro/info.hpp` | `f5e8175` | `470a180` | 0001 |
| `screenlayout.cpp` | `fb727c9` | `6684326` | 0005 |
| `screenlayout.hpp` | `6edc64e` | `06f531d` | 0005 |

</details>

## Upstream status

One change is worth sending upstream: patch **0002** (netplay waits on the wall clock, blank replies count as answers). It fixes two clear bugs in the netpacket multiplayer path (57 lines added, 7 removed):

1. The wait for a reply was timed with `std::clock`, which is process CPU time summed over all threads, so the real wait often ended well before 25 ms. On two slow handhelds, the host gave up on the answer too early and the game dropped the link.
2. A blank "not ready" reply (AID 0) was not counted as an answer, so the host always waited out the full timeout. Upstream melonDS stops waiting once every client has answered, blank or not.

We confirmed it with two-device Mario Kart DS races (about 22 fps, 0 timeouts). Before sending it, someone needs to check whether the latest `main` already fixes this and retest: we only used the web to confirm the upstream address and commit, not to compare with `main`.

The rest — ROM file mapping (it assumes glibc), the L2 pop-up, the small screen, button remapping, lid-close off and the diagnostic log — is tuned to the RG35XX Pro, so we are not sending it. We also left out the member initialization (`ScreenLayoutData` / `JoypadState`), because we couldn't confirm it is a real problem. A draft title and text for 0002 are in [`UPSTREAM.md`](../../UPSTREAM.md) and in `upstream_pr_candidate` of [`cores/MANIFEST.ds.jsonl`](../MANIFEST.ds.jsonl).

## License

- melonDS DS is licensed under the **GNU GPL v3.0** (upstream `LICENSE`, kept in [`LICENSES/melonds-ds_LICENSE`](../../LICENSES/melonds-ds_LICENSE)). These patches are released under the same terms.
- The melonDS engine is GPL-3.0 as well.
