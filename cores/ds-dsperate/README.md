<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# DSperate — two-device DS local wireless over Wi-Fi

> A patched build of the standalone DSperate emulator for linking two handhelds over Wi-Fi: fewer dropouts, faster link play, same-game matching, DraStic-style pop-up screens, and no white screen at boot when there is no firmware dump.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/ds-dsperate-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `dsperate` (standalone emulator, not a RetroArch core; linux aarch64, 4,923,120 bytes). The download also contains the [`glue/`](glue/) launcher files. |
| Version | `v3.0.3-hbipc`; `--version` prints `DSperate v3.0.3-hbipc (f5fa35e-dirty)` |
| md5 | `d1d7a7321f4ca6c1b977f2f1aacc2c4f` |
| Upstream | [beebono/DSperate](https://github.com/beebono/DSperate) v3.0.3 (`f5fa35e`) |
| License | GPL-3.0 (same as upstream) |
| Tested on | Two Anbernic RG35XX Pro (H700) units · KNULLI |

## What it does

DSperate is a standalone DS emulator rather than a RetroArch core. Its link-play packet format is the same as melonDS's, so it can also connect to melonDS. This build is for playing DS wireless games on two handhelds over Wi-Fi (or over a direct device-to-device link):

- **Link play drops less.** The host used to wait only 25 ms for the other side's reply, so on slow Wi-Fi the game cut the connection. The wait is now a single, longer budget per command (150 ms by default, 400 ms in our setup), the window for discarding stale packets is wider, and the networking library (ENet) no longer randomly drops packets it considers unreliable.
- **Playing alone is exactly like single-player.** Before, switching netplay to "auto" made you a host the moment the game started, even with nobody around, and that blocked save states, fast-forward and the pause menu. Now they are blocked only while a guest is actually connected (you see `PLAYER JOINED` / `PLAYER LEFT` notices) and work again as soon as the guest leaves.
- **Only the same game connects.** The room name carries a `[group]` tag, so a handheld running Mario Kart won't join a room playing Pokémon Black by mistake. The group comes from `--lan-group`, then the settings (`net.group`), then the ROM's 4-letter game code, then the file name, in that order. A `groups.txt` file can tie games together, for example all Gen 4 Pokémon games in one group and all Gen 5 games in another.
- **Hosts recover on their own.** When two hosts meet, the one with the larger address becomes the guest. When a host leaves, its guest goes back to hosting alone so the two can find each other again.
- **Faster link play.** The idle sleep between emulation slices now watches the network socket and wakes the moment the other side signals. The host can announce "nothing to send before this time" so the guest runs ahead (the "horizon", `DSPERATE_MP_HORIZON=1`), and the wireless chip's 8 µs timer is stepped in batches while there is nothing to do (only while a peer is connected). Mario Kart DS on two devices runs at about 58–59 fps, and a Pokémon Black 2 battle at 57–58 fps (with good Wi-Fi).
- **Saves don't get corrupted.** Saves, save states and firmware settings are written with `fsync` followed by a rename, so a dead battery or a power-button shutdown never leaves an empty file (on exFAT cards).
- **DraStic-style pop-up and small screen.** Holding L2 slides the other screen up as a translucent window (75%, rounded corners), and a double tap pins it. The small screen is 80% see-through with a green border, and pushing the right stick opens the touch window by itself. Frames with the translucent window are blended with NEON, so a two-device race holds 58.5 fps even with the window pinned (it used to drop to 52.5 fps).
- **`screen = auto`.** The big screen follows the screen that display engine A (the DS's main picture, the one that draws the 3D) is showing, for games that change which screen you look at from scene to scene.
- **Three-player link play.** Guests can see each other as well (guests also listen on port 7064), and frames from another room no longer hold a guest's clock.
- **Download Play.** The receiving side never becomes a host; it waits and then joins. We also fixed the guest connection dropping when the game restarts after the download finishes. Guests now accept the write that aligns the scanline counter (VCOUNT) with the host's. In Super Mario 64 DS versus matches, in-game time had been running at a third of real speed or less, and now runs at 95% (two-device test, 2026-10-20).
- **No white screen without a firmware file.** Picross DS (Korean release) used to freeze on a white screen right after boot when no DS firmware dump was present (the white screen in the Korean Super Mario 64 DS was the same timing problem). The cause: the ARM7 saw words the ARM9 had sent through the IPC FIFO one emulation slice too early. Stock v3.0.3 has the same bug.

## What we changed

The patch is the sum of stacked layers. Code comments in the patch carry a tag for each layer (`lanfix`, `hbfam`, and so on), so you can search the patch for that word. The `hb` prefix and the word `hanbang` are only our marker for "changed here"; we left the names as they are so that patches, binaries and scripts stay consistent. In the order they were stacked:

1. **`lanfix` — LAN timing** (`net/lan_mp`). The host's wait for replies goes from 25 ms per packet to 150 ms in total per command. The guest gets a matching wait, and the stale-frame window grows from 64 ms to `max(250, TIMEOUT+100)`. Ordinary frames that arrive while waiting are kept, the ENet packet throttle is pinned at 32/32, and statistics are logged.
2. **`hbfam` — solo host and safe saves.** A lone host is not a session (`lan_session_live`). `core/sync_file.h` writes files as fwrite, fflush, fsync, rename, then fsync of the directory. `screen_swap_hold` shows the other screen while a key is held.
3. **`hbfam2` — LAN groups.** The room name becomes `"<name>'s game [<group>]"`, and auto-join only matches rooms with the same tag.
4. **`hbfam3` — host recovery.** Of two lone hosts, the one with the larger address joins the other. When the host leaves, the guest becomes a solo host. This only applies with `--netplay` (auto).
5. **`hbpop` — L2 pop-up.** A pop-up window (`layout`: `inset_pos`; `display`: rounded corners and slide-in). Two presses within 350 ms pin it.
6. **`hbpip`, `hbpip2` — small screen.** 80% see-through with a 1 px green border (`video.pip_border`). The renderer waits for the worker thread before blending a translucent small screen, and the small screen stays visible while a pop-up is up (a "ghost").
7. **`hbmp` — socket-aware idle.** `idle_wait` watches the ENet socket during the rest between slices, skips the rest when the peer is waiting, bases the rest interval on CPU time, and adds the "horizon".
8. **`hbaud` — audio.** The display-matched frame limiter (58–61 Hz) stays on during link play, so the audio queue doesn't run dry.
9. **`hbwifi`, `hbtime` — wireless timer.** The wireless chip's 8 µs timer is stepped in batches over idle stretches (`plan_idle_steps`), and the statistics line gets microsecond timing.
10. **`hbmesh`, `hbbss` — three players.** Guests listen on UDP 7064 too, and a guest does not hold its clock for frames from another room (BSS).
11. **`hbauto` — `video.screen = auto`.**
12. **`hbstick` — stick-driven windows.** Pushing the right stick beyond 20% opens the touch window (D), and the L2 window fades while the stick is in use (C).
13. **`hbfix18`, `hbfix19` — drawing speed.** The window is always at 85% while shown, the small screen is bilinear, the translucent window is drawn into a cached buffer and copied once, blending and the ghost use NEON, and the row-copy method is chosen by timing it.
14. **`hbvc` — VCOUNT.** Writes to VCOUNT (0x04000006) in `io.cpp` `write16` are applied at the start of the next line, only when both the current line and the new value are in 200–214 (VBlank).
15. **`hblink` — batched wireless timer only when linked.** The batched stepping runs only while a link peer is attached (`LanMp::linked()`).
16. **`hbguest`, `hbguest2` — Download Play receiving.** Receiving (firmware boot) never becomes a host, even with `--netplay`; it waits and joins. No MP frames are sent to a peer that announced "wireless off", and MP frames queued in ENet are drained in one go.
17. **`hbipc` — IPC FIFO timing.** The ARM9's writes to `IPCFIFOSEND` are held in `ipc9_pending`, and the ARM9 slice ends there (`yield`). Once the ARM7 has caught up, `Scheduler::fire_due()` pushes them into the FIFO and raises the IRQ (`ipc_deliver`).

Also added: two test files (`tests/lan_group_test.cpp`, `tests/lan_live_test.cpp`), more cases in `tests/input_test.cpp` (all 32 `ctest` tests pass), and explanatory lines in `configs/default.ini`.

## Core options

DSperate is a standalone emulator, so "core options" here means its settings file, the pop-up file and a few switches.

### `dsperate.ini`

The lines that matter (our settings as of October 2026):

```ini
[paths]
bios9 = /userdata/bios/bios9.bin
bios7 = /userdata/bios/bios7.bin
firmware = /userdata/bios/firmware.bin
firmware_override = /userdata/system/configs/dsperate/firmware.ovr   # whatever a game writes to the firmware goes only here
saves = /userdata/saves/nds/dsperate
states = /userdata/saves/nds/dsperate/states
cache = /userdata/system/configs/dsperate/cache
[video]
layout = pip
screen = bottom           # top / bottom / auto in a per-game ini
pip_corner = tl
pip_scale = 0.25          # 1/4 of the big screen's width (160x120, same as DraStic)
pip_alpha = 0.8
pip_border = 00cc00
layout_cycle = pip,single
[emu]
autosave = false
limiter = 59              # the handheld's screen refreshes 59 times a second
[net]
mode = off                # the launcher script turns link play on with --netplay (and resets this to off at every launch)
[cart]
cache = session
[padhotkeys]
modifier = guide
screen_swap = +righttrigger          # R2
screen_swap_hold = +lefttrigger      # L2 (used when hb_popup.cfg has no mode=popup)
```

You don't need to set `mac_suffix`. `hb_dsperate.py` writes the last three bytes of the device's Wi-Fi (`wlan0`) address into it at every launch, so each device gets its own DS wireless address.

### `hb_popup.cfg` (L2 pop-up)

`/userdata/system/configs/advanced_drastic/hb_popup.cfg` is the same file DraStic's pop-up uses; set `HB_POPUP_CFG=<path>` to read another file. If the file or a line is missing, the default applies.

| Key | Default | Meaning |
|---|---|---|
| `mode` | (off) | `mode=popup` must be present for L2 to open the pop-up; without it, L2 swaps the screens |
| `size` | `75` | Pop-up window size (%) |
| `alpha` | `85` | Window opacity (%) |
| `pos` | `bottom` | Where the window sits (`top`, `center` or `bottom`) |
| `radius` | `14` | Corner radius of the window |
| `auto` | `1` | Pushing the right stick opens the touch window by itself (`0` = off) |
| `fade` | `40` | Opacity (%) of the L2 window while you use the stick |

### Switches (environment variables and files)

| Name | Layer | What it does |
|---|---|---|
| `DSPERATE_MP_TIMEOUT_MS` (5–2000) | `lanfix` | Host: total wait for the clients' replies to one command, in ms. Default 150 (stock: 25). |
| `DSPERATE_MP_CLIENT_WAIT_MS` | `lanfix` | Guest: one blocking wait for the next host frame, in ms. Default: same as the reply wait (stock: 25). |
| `DSPERATE_MP_STALE_MS` | `lanfix` | Queued frames older than this are dropped. Default `max(250, TIMEOUT + 100)` (stock: 64). |
| `DSPERATE_MP_ENET_THROTTLE=1` | `lanfix` | Back to ENet's original packet throttle. |
| `/tmp/dsperate_mp_stats` (a file) | `lanfix` | While this file exists, one statistics line per second is written to `/tmp/dsperate_mp_stats.log`. |
| `DSPERATE_MP_HBMP=0` | `hbmp` | Turns off the socket-aware idle wait. |
| `DSPERATE_MP_HORIZON=1` | `hbmp` | Turns on the horizon. It only takes effect if you give it to both devices. |
| `DS_WIFI_SKIP=0` | `hbwifi` | Turns off the batched stepping of the wireless timer. |
| `DS_VCOUNT_WRITE=0` | `hbvc` | Turns off the VCOUNT write handling. |
| `DS_IPC_DEFER=0` | `hbipc` | Makes IPC FIFO words visible at once, like stock. |
| `HB_PIP_NEAREST=1`, `HB_POPUP_DIRECT=1`, `HB_COPY_PLAIN=1`, `HB_GHOST_SCALAR=1`, `HB_BLEND_SCALAR=1`, `HB_COPY_WAY=memcpy\|neon` | `hbfix18`, `hbfix19` | Switch individual drawing optimizations off, or force a row-copy method. |

## Install on KNULLI

This is how we install it. Download `ds-dsperate-linux-aarch64.zip` from [Releases](https://github.com/Squirbie/handheld-link-cores/releases); it contains the `dsperate` executable and the `glue/` files. ROMs, BIOS files, firmware and saves are not part of this repository. This build also starts **without a firmware dump**: DSperate uses a generated firmware and writes settings only to `firmware.ovr`.

```
/userdata/system/configs/dsperate/
  dsperate                  <- the executable (mode 755)
  dsperate.ini              <- settings (see Core options)
  hb_dsperate_run.sh        <- glue/: ES -> launch.sh -> this script starts DSperate
  hb_dsperate.py            <- glue/: before launch and after exit: sets the DS wireless address and syncs DraStic <-> DSperate saves
  games.txt  groups.txt  mpenv.txt  gamecontrollerdb_rg35xx.txt   <- glue/
  games/<ROM name>.ini      <- per-game settings (DSperate remembers the screen layout you pick with the hotkey here)
/userdata/saves/nds/dsperate/   saves (.sav) · states/ · backup/
/userdata/bios/{bios7.bin, bios9.bin, firmware.bin}   bring your own (not in this repository)
```

1. **A fork in the DraStic launch script.** We keep these games listed in ES as DraStic games, so the save sync and the in-game pop-up hooks keep working, and hand them over at the very top of `advanced_drastic/launch.sh`:
   ```sh
   HB_DSP=/userdata/system/configs/dsperate
   hb_base=`basename "$1"`; hb_base="${hb_base%.*}"
   [ ! -e $HB_DSP/off ] && [ -f $HB_DSP/dsperate ] && grep -qxF "$hb_base" $HB_DSP/games.txt 2>/dev/null && exec /bin/bash $HB_DSP/hb_dsperate_run.sh "$1"
   ```
   `games.txt` lists ROM names (without the extension), one per line: 89 lines, 88 games plus `BootMenu`. `BootMenu` is an empty file (`roms/nds/BootMenu.nds`) that makes DSperate boot the console's own menu (the firmware); it is the "receive" side of Download Play. An empty file named `off` in that folder sends every DS game back to DraStic, and a file named `net_off` starts games solo, without link play.
2. **Settings.** Edit `dsperate.ini` and, if you want the L2 pop-up, `hb_popup.cfg`, as described under [Core options](#core-options).
3. **Launch-time values.** `hb_dsperate_run.sh` sets `DSPERATE_MP_HORIZON=1` and `DSPERATE_MP_TIMEOUT_MS=400`, and passes `--netplay`, `--lan-group <group>` and `--clear-cache`. To change them for one game, put a line `ROMname<TAB>DSPERATE_MP_*=number …` in `mpenv.txt` (only `DSPERATE_MP_*` and `DS_WIFI_SKIP` are accepted). The file currently holds lines that make two Sonic Rush games run with the original values (horizon and hbmp off, 25 ms waits).
4. **Helper scripts (optional).** The launcher uses these if they exist and skips them if not. They come from [`knulli-scripts/`](../../knulli-scripts/); copy them to `/userdata/system/claude/` (default path used by the prebuilt files), where the launcher looks for `hb_direct.py` and `hb_joinask.py`.
   - [`hb_direct.py`](../../knulli-scripts/hb_direct.py) — links the devices directly during link play (`watch-dsperate` follows DSperate's log and assigns the host and guest roles).
   - [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py) — if a room of the same group is open, shows a "join / play solo" window before launch (`--ds`).
   - [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) and [`nds_save_sync.py`](../../knulli-scripts/nds_save_sync.py) — the EmulationStation start/end hook and the DS save syncing. The hook goes to `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files). Keep only that one file in the `scripts` folder, because everything in it gets run.
   - DSperate remembers the big screen for each game by itself, so [`hb_ds_remember.py`](../../knulli-scripts/hb_ds_remember.py) (for DraStic) is not used.
5. **Check it.** `grep -a -c -E 'hbguest: firmware boot|hblink: another|hbvc: VCOUNT|dr=hbguest2|hbipc: ARM9 IPC' dsperate` should print **5**. After you start a game, `/tmp/hb_dsperate.log` (in RAM) should contain the line `hbipc: ARM9 IPC FIFO words reach the ARM7 at their send time`; that means this build is running.
6. **Undo.** Before swapping, copy the old executable into the same folder as `dsperate.<previous version>_<hash>` and copy it back over `dsperate` to undo. Don't swap while a game or DSperate is running. The switches that turn a layer off (`DS_IPC_DEFER=0` and so on) can only be given when you start `dsperate` by hand; the launcher script passes along only `DSPERATE_MP_*` and `DS_WIFI_SKIP` from `mpenv.txt`.

Not included in this repository: the final `dsperate.ini` of the test devices (it holds device-specific values, so only the important lines are listed above), the full `advanced_drastic/launch.sh`, and `hb_dsosd.so` (the in-game pop-up library on the DraStic side, which the launcher loads with `LD_PRELOAD` from `/userdata/system/claude/` if it is there).

### Other devices and operating systems

- **The executable** is for aarch64 Linux and needs glibc 2.38 or newer, libstdc++ 3.4.30 or newer and `libSDL2-2.0.so.0` (KNULLI has glibc 2.40, so there was no problem). On an older OS, rebuild from the patch. The JIT targets aarch64 Linux; on an OS without it, build with `-DDSPERATE_JIT=OFF` (it then runs as an interpreter and is slower).
- **3D is software.** `--gpu3d` is Vulkan-only, and the H700's graphics driver (libmali) has no Vulkan, so it can't be used.
- **Link-play network.** Room discovery uses UDP 7063 (broadcast) and game data uses UDP 7064 (ENet). The two devices must reach each other on these ports on the same network. Some routers freeze every Wi-Fi device for 0.05–0.1 s every few seconds, which makes link play slow and drop. We used [`hb_direct.py`](../../knulli-scripts/hb_direct.py) to link the devices directly, only while playing together (one side uses its second wireless interface, `wlan1`, as a hidden mini access point). That depends on this handheld's wireless chip, so it won't work as-is on other devices.
- **Both sides need this build** (or one that understands the group tag). Older builds don't know `--lan-group` and quit at once, and rooms without a tag (stock DSperate, melonDS) are not joined automatically; joining by address with `--lan-join` works.
- **Each device needs its own DS wireless address** (`mac_suffix`). Copying a whole card makes them identical; `hb_dsperate.py` fixes this at every launch.
- When started over ssh, the launcher script sets `XDG_RUNTIME_DIR=/var/run` and the controller table (`SDL_GAMECONTROLLERCONFIG`) by itself. `glue/gamecontrollerdb_rg35xx.txt` is for the RG35XX Pro's pad.
- Many of the changes (pop-up, small window, auto screen, groups) are our own preferences. If you don't want them, switch them off in the settings, or leave those layers out and rebuild.

## Build from source

We build it the same way as the upstream CI. With stock v3.0.3, this reproduces the official release file **byte for byte** (checked 2026-10-12), and the patched build uses the same method.

```sh
# get the source and apply the patch (see "Patches" below)

# build box: ubuntu:24.04 + (gcc 13.3, cmake 3.28, ninja 1.11, SDL2 2.30)
apt-get install --no-install-recommends cmake ninja-build g++ gcc pkg-config libsdl2-dev libvulkan-dev git ca-certificates file binutils make

# keep the source at the same path as upstream's CI: /home/runner/work/DSperate/DSperate
#   (the source path is baked into the executable; building from another path gives the same size
#    but about 230,000 bytes differ)
cd /home/runner/work/DSperate/DSperate
cmake --preset host -DDSPERATE_PGO=use -DDSPERATE_PGO_STRICT=ON -DDSPERATE_VERSION=v3.0.3-hbipc
cmake --build --preset host -j 2
ctest --preset host                                   # 32 tests pass
strip build/host/src/frontend/sdl/dsperate build/host/src/frontend/headless/dsperate-headless
```

- Compiler: GCC 13.3 in an Ubuntu 24.04 container. The result needs glibc 2.38 or newer and `libSDL2-2.0.so.0`.
- Our build VM has 3 GB of RAM, so we pinned the two `cmake` commands above to two CPUs with `taskset -c 0,1 nice -n 10` (`-flto=auto` starts as many jobs as there are CPUs). The code that comes out is the same.
- The PGO (profile-guided optimization) profile is fingerprinted for gcc 13.3.0, so `configure` stops with any other compiler. In that case use `-DDSPERATE_PGO=off` (it may be a little slower). Functions that our layers touch lose their profile, but speed on the device stayed the same (as recorded).
- We did not use the headless build (`dsperate-headless`) on the devices.

## Patches

| Order | File | What it does |
|---|---|---|
| 1 | [`patches/dsperate-v3.0.3-hbipc-full.patch`](patches/dsperate-v3.0.3-hbipc-full.patch) | One cumulative patch against upstream v3.0.3 with every layer listed above (28 files, +2619 −103, 3 of them new files) |

```sh
git clone --depth 1 --branch v3.0.3 https://github.com/beebono/DSperate.git     # tag v3.0.3 = commit f5fa35ea19f966543feae086798701f134d89619
cd DSperate
git apply /path/to/patches/dsperate-v3.0.3-hbipc-full.patch     # includes the 3 new files
```

**Why this is the final patch**

- It is the 4,098-line `git diff HEAD` of the build VM's source tree, where every layer was stacked on v3.0.3. It equals the previous build (`hbguest2`; the md5 of its `git diff HEAD` output starts with `eca75cbe`) plus `hbipc`. The executable built from this patch is `d1d7a732…` (the md5 above).
- The strings inside the executable match the layers: `v3.0.3-hbipc`, `f5fa35e-dirty`, `DS_IPC_DEFER` and `hbipc: ARM9 IPC FIFO words …` (hbipc), `hbguest: firmware boot…` (hbguest), `hblink: another console joined…` (hblink), `hbvc: VCOUNT write…` (hbvc), the `hbfix18/19` lines, and the `hbmesh`, `hbauto`, `hbaud` and `hbstick` lines are there. `hbfix20` is not (that branch did not make it into the final build). The executable requires GLIBC 2.38 and GLIBCXX 3.4.30.
- Both test devices got this build on 2026-10-25; Mario Kart DS link play on the title screen ran at 58.7/58.5 fps.
- Earlier there were several layer-by-layer patches, but all of them are contained in this one, so this single patch is all you need.

**What we checked, and what we didn't**

- Checked: the 25 starting file hashes in the patch equal the v3.0.3 tree's hashes for the same files, and the other 3 are new files (2026-10-29, compared from repository metadata only); the patch format is intact (`git apply --numstat`: 28 files, +2619 −103); the strings in the executable match the layers; the required libraries were checked.
- Not done: we did not fetch the upstream source again and rerun `git apply --check` or the build during this cleanup (the build is as it was recorded), and we did not compare with the latest upstream `main`.

**Differences from the patch used for the build.** The published patch is the build's patch (md5 `112bee98ee256be64f963249219c4333`) with a few text edits made for publication. In the new test file `tests/lan_group_test.cpp` (function `test_names`), 13 occurrences of a four-letter device label used as test input were replaced by the same-length `DevA`. The line counts in the patch headers are unchanged, and so are the values the test checks (such as truncation at 63 bytes). The `127.0.0.1` you will see in the patch is the loopback address (used by tests).

## Upstream status

The clearest candidate is **`hbipc`** (IPC FIFO timing). The ARM7 saw words the ARM9 wrote to the IPC FIFO up to one slice (2048 cycles) early. This reproduces on stock v3.0.3: white screens in 8 of 48 conditions in a sweep on our fork before the fix, 0 after it. It was the cause of the white screen when Picross DS (Korean release) boots without a firmware dump. Only the `ipc9_pending` / `ipc_deliver` parts of `io.cpp`, `io.h` and `scheduler.cpp` would be pulled out of the full patch and adapted to `main`.

Smaller candidates that could be sent separately:

- `hbvc` — accepting VCOUNT writes (Download Play versus game time ran at less than a third of real speed).
- `lanfix` — the 25 ms LAN reply wait, the 64 ms stale-packet window, and the ENet throttle dropping packets at random.
- `hbguest2` — the guest's ENet disconnect after Download Play finishes.
- The `fsync` saving from `hbfam`.

The pop-ups, small window, groups, auto screen and stick window are our own preferences, so we are not sending them. We only used the web to confirm the upstream address and commit, not to compare with the latest `main`, so check whether these are already fixed before sending anything. Draft titles and texts are in [`UPSTREAM.md`](../../UPSTREAM.md) and in `upstream_pr_candidate` of [`cores/MANIFEST.ds.jsonl`](../MANIFEST.ds.jsonl).

## License

DSperate is licensed under the **GNU GPL v3.0** (upstream license text in [`LICENSES/DSperate_LICENSE`](../../LICENSES/DSperate_LICENSE)). The patch is released under the same terms. Our own scripts in `glue/` and `knulli-scripts/` state their license in the header of each file; see also the top-level README.
