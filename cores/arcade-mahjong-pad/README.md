<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# Mahjong Pad — keyboard-only mahjong arcade games on a gamepad

> Two thin libretro wrapper cores that let arcade mahjong games on FBNeo and MAME 2003-Plus be played with a handheld's gamepad instead of a keyboard.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/arcade-mahjong-pad-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `fbneo_mj_libretro.so` and `mame2003_plus_mj_libretro.so`, 72,584 bytes each, aarch64 Linux (both in the release zip `arcade-mahjong-pad-linux-aarch64.zip`) |
| Version | One source file, [`patches/hb_mjpad.c`](patches/hb_mjpad.c) (md5 `7c721fac65a15a9649bd27464777bb3a`), compiled twice with different options. It wraps the real cores `fbneo_libretro.so` ([arcade-fbneo](../arcade-fbneo/), md5 `c942499fc72a61400d4e6a486841fb37`) and `mame2003_plus_libretro.so` ([arcade-mame2003-plus](../arcade-mame2003-plus/), md5 `30e1ebc1ea097bd2cddd4e8e85b31f7e`) |
| md5 | `fbneo_mj_libretro.so`: `92e23de148cb45fb645cc270cba95bfd`<br>`mame2003_plus_mj_libretro.so`: `fb23fd640ae81b3cbdde89ad3d43f4e5`<br>sha256 of `fbneo_mj_libretro.so`: `543cc430544efda049cae8257d2a2fc185b667567eb878f235abfeb5a5be72e6`<br>sha256 of `mame2003_plus_mj_libretro.so`: `294b11405fe9059a7c8936f577ac26fbec9bbe9384350180f5c71848dca47974` |
| Upstream | None. This is original code: it contains no FBNeo or MAME source and loads the real core with `dlopen` at run time |
| License | The same terms as the core it wraps: the FinalBurn Neo license for `fbneo_mj`, the MAME license for `mame2003_plus_mj`. Both are non-commercial, so you may not sell them. See [License](#license) |
| Tested on | Anbernic RG35XX Pro (H700, aarch64) · KNULLI · RetroArch 1.22 |

> No ROMs, BIOS files or saves are included in this repository; use only ROMs you own.

## What it does

Arcade mahjong games read their keys (A to N for the tiles, plus kan, pon, chi, riichi and ron) from a **keyboard only**. A handheld has no keyboard, so you could insert a coin and press start, but you could not discard a tile. These wrapper cores sit in front of the real core (FBNeo or MAME 2003-Plus). When the real core asks for the keyboard, the wrapper **answers with player 1's gamepad buttons** and draws a row of A to N cells at the bottom of the screen.

- Press left or right on the D-pad to pick a cell (A to N), then press A to discard that tile.
- The row at the bottom has 14 cells. The selected cell is gold and the others are drawn dark and translucent, so the tile graphics in the game are not hidden.
- Ron, riichi, pon, chi and kan each have their own button. Coin (SELECT) and start (START) are handled by the real core as before.
- We use it for 27 arcade games that read mahjong keys from the keyboard (20 on FBNeo, 7 on MAME 2003-Plus).

### Controls

| Button | Action |
|---|---|
| Left / Right | Move the selection one cell (hold to repeat: it starts after 18 frames, then repeats every 6 frames) |
| Down / Up | Jump to the leftmost cell (A) / the rightmost cell (N, the tile you just drew) |
| A | Press the key of the selected cell (discard a tile, choose a menu item). The cell you started pressing stays held until you release |
| R2 | Press N (the tile you just drew) right away |
| B | Ron (`Z`) |
| X | Riichi (`Left Shift`) |
| Y | Pon (`Left Alt`) |
| L | Chi (`Space`) |
| R | Kan (`Left Ctrl`) |
| L2 | Show or hide the row at the bottom of the screen |
| SELECT / START | Coin / start, handled by the real core as before |

## What we changed

This is not a modification of the cores. It is a thin wrapper core placed in front of them, written as a single source file.

1. **Structure.** Both `.so` files export the `retro_*` functions of a libretro core. On first use they `dlopen` the real core and pass every call straight through to the functions found with `dlsym` (serialization, memory and cheats included). Only three things are intercepted: `retro_set_environment` (to peek at the pixel format, `SET_PIXEL_FORMAT`), `retro_set_video_refresh` (to draw the row at the bottom) and `retro_set_input_poll` / `retro_set_input_state` (to turn the pad into mahjong keys).
2. **Input.** Keyboard queries (`RETRO_DEVICE_KEYBOARD`) from the real core are answered from player 1's pad (port 0). `A` to `N` come from the selected cell (or from R2 for N); `Z`, `LSHIFT`, `LALT`, `SPACE` and `LCTRL` come from B, X, Y, L and R. Any other query (a joystick, for example) is passed to the front end unchanged. **While the wrapper is active, a real keyboard is not forwarded to the core** (gamepad only).
3. **Video.** Software-rendered frames (`XRGB8888`, `RGB565`, `0RGB1555`) are copied, and the 14 cells are drawn into the bottom 7 rows (a 3×5 dot font; the selected cell has a `0xFEB713` gold background). Nothing is drawn if the frame is narrower than 70 or shorter than 40 pixels, or if the core uses a hardware framebuffer.
4. **When it switches on (the only difference between the two builds).**
   - **FBNeo build:** it switches on when the real core **first asks for the keyboard**. FBNeo asks only in games that have mahjong keys. The controller info (`SET_CONTROLLER_INFO`) could not be used to decide, because FBNeo removes the keyboard entry itself.
   - **MAME 2003-Plus build** (`-DHB_MJ_ALWAYS`): it is on from the start. MAME 2003-Plus asks for the keyboard whenever its input interface is `simultaneous` (the default `retropad` does not read the keyboard), and this core is only used for mahjong games.
5. **Where the real core lives.** The path is set at compile time with `HB_MJ_REAL` (a string). At run time, the environment variable `HB_MJ_REAL`, if set, overrides it (meant for testing). The defaults are `/userdata/system/hanbang_cores/fbneo_libretro.so` (default path used by the prebuilt files) for the FBNeo build and `/userdata/system/hanbang_cores/mame2003_plus_libretro.so` for the MAME build. The `hb_` and `HB_` prefixes in file and symbol names just mark code we wrote; we did not rename them.
6. **What upstream does** (checked on 2026-10-29 in `libretro/FBNeo`, `src/burner/libretro/retro_input.cpp`). FBNeo binds the inputs named `mah a` to `mah n` to `RETROK_a` to `RETROK_n`, and `kan` = `LCTRL`, `pon` = `LALT`, `chi` = `SPACE`, `reach` = `LSHIFT`, `ron` = `z`. This is the same mapping the wrapper uses. The code was meant to give every player their own keyboard (port `nMaxPlayers` plus the player number), but it contains `if (nPlayer > 0) return 0;`, so **only player 1** gets keys. The comment right above points to https://github.com/finalburnneo/FBNeo/issues/2117. That is why two-player mahjong does not work on this setup (we list these games as 1 player). The wrapper answers keyboard queries from player 1's pad no matter which port they come in on.

### Tested, and not tested

- **Tested:** in a virtual-machine test bench that presses keys, 32 mahjong-key games (the list at that time) started and showed the mahjong table.
- **Tested:** on a device, one FBNeo mahjong game from inserting a coin and choosing 1 player, through to a game in progress and discarding tiles (including R2, left / right and L2); and two MAME mahjong games from credit, through the deal, into a game in progress.
- **Tested:** the source compiles without warnings in both configurations on a Mac (`-Wall -Wextra`, 2026-10-29). The key mapping in upstream FBNeo is the same as the wrapper's.
- **Not tested:** two-player mahjong, netplay, FBNeo's other mahjong keys (such as `ff`), a speed comparison with and without the wrapper, and the exact compile options we used (they were not recorded).

### Known limits

- **There is no two-player mahjong.** FBNeo does not read player 2's mahjong keys at all.
- The other mahjong keys that FBNeo reads (`ff`, `lc`, `bet`, `score`, `big`, `small`, `wup`) are not answered by the wrapper. Games that really need those keys cannot be played.
- Mahjong games played with a joystick (they do not use the keyboard) and some board mahjong games that have a joystick mode are better off on **plain FBNeo, without the wrapper**; we switched them back. KNULLI's config generator writes a `fbneo-dipswitch-<rom>-Controls=Joystick` line for each FBNeo game, and that line is not written when the game is launched with the wrapper core.
- Netplay was not tested (we list these games as 1 player because two-player mahjong does not work).

## Core options

| Where | Name | Value | What it does |
|---|---|---|---|
| RetroArch core option, set per game for the MAME build | `mame2003-plus_input_interface` | `simultaneous` | MAME 2003-Plus reads mahjong keys from the keyboard only in this input mode. The default, `retropad`, does not read the keyboard. |
| Environment variable, at run time | `HB_MJ_REAL` | The path of the real core's `.so` file | Overrides the compiled-in path (meant for testing). |
| Compile-time define | `HB_MJ_REAL` | A string path, for example `"/userdata/system/hanbang_cores/fbneo_libretro.so"` | Sets the default path of the real core. |
| Compile-time define | `HB_MJ_ALWAYS` | Defined or not | The wrapper is on from the start. It is used for the MAME build. |

## Install on KNULLI

Download `arcade-mahjong-pad-linux-aarch64.zip` from the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest) and unzip it; it holds both `fbneo_mj_libretro.so` and `mame2003_plus_mj_libretro.so`. The wrapper needs the real cores (see [arcade-fbneo](../arcade-fbneo/) and [arcade-mame2003-plus](../arcade-mame2003-plus/)) to be installed too. This is how we installed it:

1. **Where the files go:** put both `.so` files in `/userdata/system/hanbang_cores/` on the SD card, check the md5s, then create **symlinks** with the same names in `/usr/lib/libretro/`. The real cores, `fbneo_libretro.so` and `mame2003_plus_libretro.so`, must be in that same folder **under those names**, because the path is compiled into the wrapper.
2. **Info files:** a new core name needs a `.info` file. We copied the real core's `.info` and changed only `display_name`: `Arcade (FinalBurn Neo Mahjong Pad)` and `Arcade (MAME 2003-Plus Mahjong Pad)` (as `/usr/share/libretro/info/fbneo_mj_libretro.info` and `mame2003_plus_mj_libretro.info`).
3. **Saving:** the symlinks and `.info` files under `/usr` live in KNULLI's overlay, so save them with `knulli-save-overlay`.
4. **Per-game lines** (`/userdata/system/knulli.conf`) for each game chosen as described below:
   ```
   # FBNeo mahjong-key game
   arcade["<ROM name>.zip"].core=fbneo_mj
   arcade["<ROM name>.zip"].emulator=libretro

   # MAME 2003-Plus mahjong-key game
   arcade["<ROM name>.zip"].core=mame2003_plus_mj
   arcade["<ROM name>.zip"].emulator=libretro
   arcade["<ROM name>.zip"].retroarchcore.mame2003-plus_input_interface=simultaneous
   ```
   If a game already has a different core line, check it before you touch it, and keep a copy of `knulli.conf` on the device before editing.
5. **Undo:** delete those lines for the game and it goes back to its original core.
6. It helps to list the controls (left / right, A, R2, B, X, Y, L, R, L2) in the game's menu description.

### Choosing games

Use the wrapper only for games where the core asks for the mahjong keys on the keyboard.

- FBNeo: games whose input list has names starting with `mah` (inside the core, `nMahjongKeyboards > 0`).
- MAME 2003-Plus: games with a mahjong keyboard input port (the input interface has to be `simultaneous`).
- We picked games by logging, in a virtual-machine test bench, which input codes the core asks for and looking for the mahjong keys (`A` to `N`). We check new games the same way.

### Other devices and systems

- **The files are for aarch64 Linux (glibc 2.34 or newer) only.** For any other system, build the source for that device. On Android, Windows or macOS you also have to adapt the `dlopen` path and the file extension (`.so`) to that OS.
- **The real core's path is compiled in.** Outside KNULLI, rebuild with `-DHB_MJ_REAL`, or point to the core with the environment variable `HB_MJ_REAL`.
- The real core does **not** have to be our patched build (a standard libretro core is fine, and the wrapper only makes sense for FBNeo or MAME 2003-Plus reading mahjong keys from the keyboard), but we only tested it with the two builds named above.
- The front end must be RetroArch (libretro), and the MAME build needs the core option `mame2003-plus_input_interface = simultaneous`.
- On a device with a keyboard you do not need it (this mode even blocks the real keyboard).

## Build from source

You need `libretro.h` (the libretro API header, which is part of [libretro-common](https://github.com/libretro/libretro-common) and the RetroArch sources). It is not included in this folder.

```sh
# FBNeo build (switches on when the real core first asks for the keyboard)
gcc -O2 -shared -fPIC -I<folder with libretro.h> \
    -DHB_MJ_REAL='"/userdata/system/hanbang_cores/fbneo_libretro.so"' \
    -o fbneo_mj_libretro.so patches/hb_mjpad.c

# MAME 2003-Plus build (on from the start)
gcc -O2 -shared -fPIC -I<folder with libretro.h> -DHB_MJ_ALWAYS \
    -DHB_MJ_REAL='"/userdata/system/hanbang_cores/mame2003_plus_libretro.so"' \
    -o mame2003_plus_mj_libretro.so patches/hb_mjpad.c
```

- The exact command line and optimization flags of our build were not recorded. The commands above are an example that does the same thing; identical file fingerprints are not guaranteed.
- Our files were built with GCC 12.2 (Debian 12, aarch64). The only library they need is `libc.so.6` (`GLIBC_2.34`). On an older glibc, add `-ldl` and build on that device.
- Checked: the source compiles without warnings in both configurations on a Mac (`-Wall -Wextra`, 2026-10-29).

## Patches

| Order | File | What it does |
|---|---|---|
| 1 | `patches/hb_mjpad.c` | The complete wrapper source (not a patch), md5 `7c721fac65a15a9649bd27464777bb3a`. Both cores are built from this one file; they differ only in the compile options (`-DHB_MJ_ALWAYS` and the compiled-in path of the real core). The comments in the source are in Korean. |

## Upstream status

Nothing in upstream does what this wrapper does, and there is **nothing to send** (`worth: false` in [`../MANIFEST.arcade.jsonl`](../MANIFEST.arcade.jsonl)). The gap is on the front-end side: a gamepad has to stand in for a keyboard, and we solved that with an external wrapper built around our handheld's buttons, so there is no place in the cores to fix. FBNeo's libretro input code maps the mahjong keys to keyboard keys only and gives them to player 1 only (see above), and MAME 2003-Plus reads them through its keyboard input interface (`simultaneous`). If upstream ever wants this, a gamepad mahjong input mode in the libretro port would be the natural place for it.

## License

`hb_mjpad.c` is code we wrote. It is released under the **same terms as the core it wraps**: built as `fbneo_mj`, it follows the FinalBurn Neo license; built as `mame2003_plus_mj`, it follows the MAME license. Both are non-commercial licenses, so **you may not sell them**.

- The wrapper contains no FBNeo or MAME source; it loads the real core with `dlopen` at run time. Even so, selling a device or memory card that carries the wrapper together with the real core is not allowed, because the real core's non-commercial license applies.
- The wrapped cores keep their own licenses: see [arcade-fbneo](../arcade-fbneo/README.md#license) and [arcade-mame2003-plus](../arcade-mame2003-plus/README.md#license).
- `libretro.h` (the libretro API header) is under the MIT license. It is not included in this folder.
