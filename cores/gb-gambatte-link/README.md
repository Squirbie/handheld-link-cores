<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# Gambatte Link — Game Boy link cable and GBC infrared over netplay

> A gambatte core that turns a RetroArch netplay room into a Game Boy / Game Boy Color link cable and infrared port, so two handhelds can play link games over Wi-Fi, each with its own game and its own save.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/gb-gambatte-link-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `gambatte_libretro.so` (aarch64 Linux, 4,367,384 bytes) |
| Version | `v0.5.0-netlink-4041d5a-hb-v5irh3` (link protocol `gambatte-hb-link-6`; called v5irh3 in the patch names) |
| md5 | `8c0eb89d9c157eda094b293a4aa0b976` |
| Upstream | [libretro/gambatte-libretro](https://github.com/libretro/gambatte-libretro) at commit `4041d5a` |
| License | GPL-2.0-only |
| Tested on | Anbernic RG35XX Pro · KNULLI |

This is the final build that is actually installed on the RG35XX Pro (KNULLI, aarch64 Linux).
The prebuilt `.so` is not stored in this folder. It comes in the release zip `gb-gambatte-link-linux-aarch64.zip` (see the Download button).
This folder holds the documentation and the patches only. No ROMs, BIOS files or saves are included.

## What it does

Game Boy and Game Boy Color games have link-cable battles and trades, and this core lets two devices play them over Wi-Fi.
One player opens a RetroArch netplay room and the other joins. Each device keeps running **its own game and its own save**, and only the bytes that would travel down the cable are exchanged. Saves never get mixed.

The Game Boy Color's **infrared port** works through the same room. These have been checked: the Mystery Gift in Pokémon Gold / Silver / Crystal, sending scores in Pokémon Pinball, Card Pop! in Pokémon Card GB, and item exchange in Boku no Camp-jou.

Why it needed work: games have a rule that the answer to a byte must arrive within a set time, so sending the bytes over the internet as they are ends in a link error.
This core sends the sender's Game Boy timing gap along with every byte, and the receiver waits or catches up to match it.

Games it has been checked with include: Yu-Gi-Oh! Duel Monsters 1, Pokémon Card GB 1 and 2, trading and the Colosseum in Pokémon Gold / Silver / Crystal, World Heroes 2 Jet, Tetris DX, Tetris 2, Nekketsu Beach Volleyball, Bikkuri Nekketsu Shin Kiroku, Monster Capsule GB, Hamster Paradise Ham Race, three beatmania GB titles, Super Robot Wars (GB) 1, and Pocket Battle.

**Use the same build on both devices.** Older builds (protocols 3 and 4) won't connect to this one.
Even within protocol 6, the rules added since v4bw only work as intended when both devices are updated together.
Infrared works only when both devices are v5ir or newer. If one side is older it silently doesn't work, but the game doesn't freeze.

## What we changed

Upstream gambatte-libretro supports link play only through a direct TCP connection (the "GB Link" option). These patches add the following on top of it.

1. **A transport layer that uses a netplay room as the link cable**, `libgambatte/libretro/hb_netpacket_serial.h` (`RETRO_ENVIRONMENT_SET_NETPACKET_INTERFACE`; two players only, a third is refused).
   - Every byte carries the Game Boy time its sender let pass since its previous byte (a 32-bit gap). The receiver guesses the next gap and either waits with its game paused (40 ms at most) or, if it is behind, runs on up to the time the byte was sent and then answers.
   - If no byte from the peer arrives within 5 seconds, `0xFF` ("no cable") is returned, and the peer drops that byte if it hasn't read it yet.
   - Core option `gambatte_netlink_timing` = `auto` | `v3j` | `bounded` (see Core options).
   - Start barrier: both devices restart together (20 seconds at most). RetroArch's netplay guest runs a few frames before the core's `start()` is called, so if `start()` arrives within 1800 frames of loading, the game restarts from scratch (SRAM and RTC are kept) and waits.
   - v4bw rules: a byte that arrives late counts as received at its due time (Bikkuri Nekketsu Shin Kiroku); a peer that isn't listening gets its answer two frames later; when both sides send at once, the host's byte goes first; and when the two sides take turns, the sender waits for the other's byte once it has run past one tick (240 Hz) (Monster Capsule GB).
2. **Two bugs in gambatte itself**
   - `Memory::updateSerial` (the `HAVE_NETWORK` side): if the game reads SB, SC or IF while a byte is in flight, the top bits of the incoming byte are shifted in again instead of the bits that follow the ones already shifted in, so the value comes out rotated (`0x20` became `0x08`). The remaining bits are now taken from the right place.
   - `GB::reset()`: resetting while the boot ROM is still mapped turns the boot ROM into the "cartridge backup", and the game can't come back (white screen). `bootloader.call_FF50()` now runs before `full_init()` to put the cartridge back first.
3. **Game Boy Color infrared (FF56).** Each side sends 20-byte 'I' packets with its time, LED state and on/off state. Once both ports are on, the two sides meet once (the host decides who pairs with whom), their Game Boy clocks are tied together, and an RP read sees the other side's LED 4096 units late (about 0.98 ms).
   If the other side's news hasn't arrived that far, the reader waits right there (up to 3 seconds). A long pulse (256 units or more) stays visible for 128 more units after it ends. A side that leaves its port on without reading it (the Pokémon Pinball menu) is reported as "not listening", so the other side doesn't freeze.
4. **Answering `00` when bytes cross or the peer isn't listening**, like a real cable (`FF` only when there is no Game Boy at all): Hamster Paradise Ham Race.
5. **Pokémon Card GB 2:** the second byte used to arrive in the same frame, before the receiver had read the first one, and overwrote it. When the sender's gap is a frame or more, the second byte is now held until the receiver's next frame has run half a tick (240 Hz).
6. **Boku no Camp-jou:** when a listening peer exists, the two sides meet just before the LED turns on (the hello pulse used to be missed), and the tail of a long pulse lingers only if the reader saw it lit two times or fewer (it used to stretch short bit lengths).

Names starting with `hb_` or `HB_`, and the word `hanbang`, in the patched code and in the version string (`-hb-v5irh3`) are only our marker for "changed here". We left them as they are so that patches, binaries and scripts stay consistent.

### How it was checked

- The final `.so` contains every marker string that the patches add (`hb-v5irh3`, `ir-tx-meet`, `hold2f`, `crossQ-00`, `unarmed00`, `ir-stop-timeout`, `gambatte-hb-link-6`) and none of the previous build's `crossQ-ff` and `unarmedFF`.
- Regression check at v5irh3 (same results as the previous build, v5irh2): Mystery Gift 4/4, Card Pop! 1/1, Pinball score send 3/3, and Tetris DX, Card GB 2 and Monster Capsule unchanged. Boku no Camp-jou trades: 6/6 in a virtual machine and 2/2 with the device build. On the devices, two Pokémon Pinball units started, the score transferred, and nothing froze.
- Limits: long runs over the devices' Wi-Fi, three or more players, and sound were not checked.

## Core options

| Option | Values | Meaning |
|---|---|---|
| `gambatte_netlink_timing` | `auto` (default) / `v3j` / `bounded` | How tightly the two sides' timelines are tied. `bounded` keeps a session-wide virtual time so that neither side can run ahead. `auto` uses `bounded` only for the three beatmania GB titles (identified by ROM size + CRC32) and the `v3j` rules for everything else. |

## Install on KNULLI

This is how we set it up on the RG35XX Pro. Adjust paths and names if your setup differs.

1. **Core file.** Put `gambatte_libretro.so` in `/userdata/system/hanbang_cores/` (default path used by the prebuilt files), which lives in the SD card's userdata.
   On the RG35XX Pro setup, the system's `/usr/lib/libretro/gambatte_libretro.so` is a symlink to this file, so swapping the file on the SD card is all it takes.
   If your device has no such symlink, the root is read-only: run `mount -o remount,rw /`, create it with `ln -sfn`, and save with `knulli-save-overlay`.
2. **How to swap it.** While no game is running, upload the new file next to the old one under a side name (`.hbnew`), check its md5, then `mv` it into place. Keep a backup of the old file.
3. **Update both devices together.** They only connect when both run the same build. Infrared works only when both are v5ir or newer.
4. **No per-game config lines are needed.** This file is a drop-in replacement for gambatte, KNULLI's default Game Boy / Game Boy Color core, so `knulli.conf` was not touched. The core option `gambatte_netlink_timing` stays at its default, `auto`. (The few games that run separately on TGB Dual are not related to this core.)
5. **Helper scripts** from this repository's [`knulli-scripts/`](../../knulli-scripts/) folder. Copy them to `/userdata/system/claude/` (default path used by the prebuilt files), except for the hook:
   - [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) is the ES game start / stop hook, and it goes to `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files). It launches the scripts below for each game.
   - [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py) writes the save to the card every 10 seconds, because RetroArch turns off SRAM autosave once netplay starts. gambatte is on the list of "each player keeps their own save" cores.
   - [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py) is the prompt that asks "play together / play alone" when a room for the same game is open. It knows paired sets such as Pokémon generations 1 and 2, Yu-Gi-Oh!, and Dragon Quest Monsters 2.
6. Open the room through ES's netplay flow (the host opens a room and the guest joins with the same game). When the two devices first start, syncing with each other can take up to 20 seconds.

### Other devices and operating systems

- This `.so` is for **aarch64 Linux only** (it uses glibc symbol versions up to GLIBC_2.33). On any other CPU or OS, rebuild from the patches (`platform=osx` and so on). A macOS arm64 build was made and run for test tooling; Windows and Android have not been tried.
- You need a frontend that supports RetroArch's **netpacket interface** (`RETRO_ENVIRONMENT_SET_NETPACKET_INTERFACE`). Testing was done with RetroArch 1.22.2.
- **Use the same build on both sides.** This core's protocol (`gambatte-hb-link-6`) doesn't connect to older builds (protocols 3 and 4, from before v3j).
  Builds that share protocol 6 do connect even if they differ, but the v4bw rules (late bytes, a peer that isn't listening, simultaneous sends) only work as intended when both devices are updated together.
- The on-screen notices (`GB 통신: 연결됐어요`, `상대가 없어 혼자 시작 …`, `상대 기다리는 중 · N초`; roughly "GB link: connected", "no partner, starting alone …", "waiting for partner · N s") are **Korean UTF-8** text in the code. A frontend without a Korean font shows boxes. Edit `HB_NP_MSG_*` in `libretro.cpp` to change them.
- After a state load, a rewind or a reset, the two devices have to sync up again (both devices reset). Rewinding during infrared breaks the pairing for that attempt, so press A again.
- If the Wi-Fi delay between the devices is over 10 ms one way, the game can slow down on infrared screens. (Setups with more than 15 ms were not tested.)
- Infrared and cable exchanges between Pokémon Gold / Silver and Crystal don't work, per the original games' rules: the region codes differ, so the game shows a link error.
- The three beatmania GB titles that `auto` switches to `bounded` are recognized by the size and CRC32 of the Japanese ROMs. ROMs of other versions run with the `v3j` rules.

## Build from source

This is exactly how it was built. The build machine was Debian 12 (aarch64, gcc 12.2, glibc 2.36). The resulting `.so` uses glibc symbol versions up to GLIBC_2.33 only, which is older than the device's 2.40, so it runs as is.

```sh
# the patches (this repository)
git clone https://github.com/Squirbie/handheld-link-cores.git
CORE="$PWD/handheld-link-cores/cores/gb-gambatte-link"

# upstream at the base commit
git clone https://github.com/libretro/gambatte-libretro.git
cd gambatte-libretro
git checkout 4041d5a6c474d2d01b4cb1e81324b06b51d0147b

# (a) apply the patches one by one, in order
for p in $(grep -v '^#' "$CORE/patches/series"); do git apply "$CORE/patches/$p"; done
# (b) or apply the single combined patch instead (never both)
# git apply "$CORE/patches/all-in-one/gambatte-link-v5irh3-vs-4041d5a.patch"

make -B -j2 platform=unix CC=gcc CXX=g++ 'GIT_VERSION="-4041d5a-hb-v5irh3"'
# result: ./gambatte_libretro.so  (the unstripped file is what went onto the devices)
```

- `platform=unix` turns on `HAVE_NETWORK=1`, which these patches need in order to compile.
- `GIT_VERSION` sets the version text shown in the core info (`v0.5.0-netlink-4041d5a-hb-v5irh3`). Any other text works the same way.
- The patches also apply with `patch -p1`.
- A different compiler will not produce a byte-identical `.so`. To confirm the behavior is the same, use the version string inside the core and the checks under "How it was checked".

### Reproducibility

- The upstream tree hash `a28a8644a1c4987b8407251547d3960b9422710a` matches GitHub's. Applying the patches in order gives a tree that matches the recorded final build source file by file. `git apply` in order, `git apply` with the combined patch, and `patch -p1` in order all produce the same tree: `f295e043e76a3096753490d3f501f379d2220b21`.
- **Not done:** the core was not recompiled when this folder was put together, so a byte-identical `.so` has not been confirmed. What was checked is that the source tree matches the record and that the marker strings are in the `.so`.
- Moving to the latest upstream `master` has not been done. The base is the 2024-02 commit `4041d5a`.

## Patches

Apply them in this order. `patches/series` lists the same order. To apply everything at once, use only `patches/all-in-one/gambatte-link-v5irh3-vs-4041d5a.patch` (using it together with the individual patches would apply the changes twice).

Base: libretro/gambatte-libretro commit `4041d5a6c474d2d01b4cb1e81324b06b51d0147b` (2024-02-23, "Fetch translations & Recreate libretro_core_options_intl.h"), tree hash `a28a8644a1c4987b8407251547d3960b9422710a`.

| Order | File | What it does | Build after this step |
|---|---|---|---|
| 1 | [`0001-netpacket-link-cable-with-timing-v4bw.patch`](patches/0001-netpacket-link-cable-with-timing-v4bw.patch) | Transport layer, timing compensation and the two gambatte bugs (v2 to v4bw rolled up into one patch on top of the base) | v4bw, md5 `444a461ad8ca7812d48ead0e2aae7495` |
| 2 | [`0002-gbc-infrared-over-netplay-v5ir.patch`](patches/0002-gbc-infrared-over-netplay-v5ir.patch) | Game Boy Color infrared | v5ir, md5 `60d41b7a85c4e1404640e3d3ad916a9a` |
| 3 | [`0003-reply-00-not-ff-to-unheard-byte-v5irh.patch`](patches/0003-reply-00-not-ff-to-unheard-byte-v5irh.patch) | Answer `00` to a peer that isn't listening | v5irh, md5 `2aa5548406d69c9f32f4bef5b13a72fa` |
| 4 | [`0004-hold-second-byte-to-next-frame-v5irh2.patch`](patches/0004-hold-second-byte-to-next-frame-v5irh2.patch) | Pokémon Card GB 2 handshake | v5irh2, md5 `ccf076adc253367aa2ec04b8c8ec954d` |
| 5 | [`0005-infrared-meet-before-led-and-pulse-tail-v5irh3.patch`](patches/0005-infrared-meet-before-led-and-pulse-tail-v5irh3.patch) | Boku no Camp-jou infrared | v5irh3, md5 `8c0eb89d9c157eda094b293a4aa0b976` |

- Each patch header (Subject, Origin, a short summary, then the description) says what was changed and why.
- The md5 values are those of the `.so` built at that step. They come from our development log, and only the final build matches the file described here.
- Version history (all 2026): v2 to v3j (Oct 15: byte slips, timing compensation, Beach Volleyball, Pokémon Card GB) → v4bm (Oct 15: beatmania) → v4bt to v4bv (Oct 18–19: restart during the boot ROM) → v4bw (Oct 21: Bikkuri Nekketsu Shin Kiroku, Monster Capsule GB) → v5ir (Oct 26: infrared) → v5irh → v5irh2 → v5irh3 (Oct 26). Everything up to v4bw is inside patch 0001.

## Upstream status

Checked on the web on 2026-10-29, on libretro/gambatte-libretro `master`:

- `Memory::updateSerial` (the `HAVE_NETWORK` side) still has the forms `serialize_value_ >> (8 - serialCnt_)` and `serialize_value_ >> (8 - (serialCnt_ - targetCnt))`. The bug of shifting the top bits in again is still there.
- `GB::reset()` calls only `p_->full_init(false)` and doesn't put the cartridge back first. (After the base commit, `full_init` gained an argument for erasing SRAM.)

**Worth sending upstream? Yes.** Two small fixes can be pulled out of patch 0001: (1) the bit shifting in `updateSerial`, and (2) taking the boot ROM out on reset.
Each is a few lines and has nothing to do with how the bytes travel. They have to be redone against `master` before sending.
The netpacket transport (`hb_netpacket_serial.h`) and the infrared support are big features built for these devices, so they are not candidates.

A draft pull request is ready: title "Fix partial serial shift under HAVE_NETWORK and restore ROM bank 0 before re-initialising on reset". The English title and body are in [`UPSTREAM.md`](../../UPSTREAM.md) and in the `upstream_pr_candidate` field of [`cores/MANIFEST.gb.jsonl`](../MANIFEST.gb.jsonl). Nothing has been sent yet.

## License

- **GPL-2.0-only**, the same as upstream gambatte (libretro's version). The upstream file headers specify version 2 of the GNU General Public License as published by the Free Software Foundation (license text: [`LICENSES/gambatte-libretro_COPYING`](../../LICENSES/gambatte-libretro_COPYING)). These patches are published under the same terms.
- If you distribute the core (`.so`), the upstream commit plus these patches are the corresponding source. Keep the copyright notices in the upstream file headers as they are.
