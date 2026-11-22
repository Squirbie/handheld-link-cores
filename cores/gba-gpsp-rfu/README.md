<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# gpSP RFU — a GBA Wireless Adapter that survives Wi-Fi

> gpSP with a hardened Wireless Adapter (RFU) emulation, so Pokémon FireRed, LeafGreen and Emerald trades and battles between two handhelds hold up over Wi-Fi netplay.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/gba-gpsp-rfu-linux-aarch64.zip) &nbsp; [← All cores](../../README.md)

| | |
|---|---|
| Core file | `gpsp_libretro.so` (aarch64 Linux, dynarec included, 724,264 bytes, stripped) |
| Version | `v1.1.0-5819380-hb4` (called v3 in the patch names) |
| md5 | `6c86b647977fafeea3a5cccfeb51d5a1` |
| sha256 | `e21bf6d425f6d7a0e4818f4655154621e3d99f5a5a1d68d4a1564dc662e944a4` |
| Upstream | [libretro/gpsp](https://github.com/libretro/gpsp) at commit `5819380` (2026-09-19, the latest `master` when this build was made) |
| License | GPL-2.0-or-later |
| Tested on | Anbernic RG35XX Pro · KNULLI, Anbernic RG DS Plus |

This is the final build that is actually installed on the RG35XX Pro (KNULLI, aarch64 Linux).
The prebuilt `.so` is not stored in this folder. It comes in the release zip `gba-gpsp-rfu-linux-aarch64.zip` (see the Download button).
This folder holds the documentation and the patches only. No ROMs, BIOS files or saves are included.

## What changed in this build (2026-11)

- Our three patches (v3) are the same. Only the upstream base moved, from the 2024-02 commit `4caf7a1` to the latest `master`, `5819380`.
  - Whatever upstream added in between comes along:
    - link-cable modes: `gpsp_serial` = `mul_poke` (Pokémon Gen 3 cable trades and battles), `mul_aw1` and `mul_aw2` (Advance Wars);
    - two new core options, `gpsp_rtc_time_source` and `gpsp_sound_rate`;
    - memory-safety and re-entrancy cleanups and determinism fixes on the wireless side.
  - One spot needed a hand merge while moving (see the header of `0003`). The old v3 source with only upstream's changes merged in is identical to this build's source, apart from one comment line at that spot.
- The build now uses zig and targets glibc 2.17, so it also runs on older systems. The old build needed up to GLIBC_2.33.
- The netpacket layout and the version string (`gpSP v1.0`) are unchanged, so older builds (v3, v2, stock) still connect over the wireless link.

## What it does

Pokémon FireRed, LeafGreen and Emerald on the GBA trade and battle through the **Wireless Adapter**. gpSP emulates that adapter, and RetroArch netplay connects two devices.
Each device runs **its own game and its own save**, and only the wireless signal travels between them.

Stock gpSP produced **communication errors during trades** once Wi-Fi delay came into play (tens to hundreds of milliseconds, with the occasional half-second stall).
It assumes the adapter answers within a few milliseconds, which netplay can't match, and its queue for received packets holds only four entries, so a burst of packets was thrown away.

This build fixes that in three steps:

1. **v1:** raised the time limit to 1.2 seconds. That got rid of the communication errors, but the **trade room became much slower**, because the in-game leader waited 1.2 seconds for each answer (when the connection was jittery, the leader ran at 0.2 times the guest's speed).
2. **v2:** went back to the game's own value for the answer wait, and enlarged the packet queue to 128 entries so that late answers aren't thrown away. A disconnect is applied only after the remaining packets have been read.
3. **v3 (this build):** fewer receive calls while waiting, and a backed-up guest queue is allowed to catch up. That cuts **frame drops and sluggishness**.

The gain is biggest when both devices run v3. Older builds (stock, v1, v2) still connect, even in a mixed pair.

## What we changed

The patches in this folder touch only `rfu.c` and `cpu_threaded.c`.

- **0001, arm64 Linux cache sync.** `platform_cache_sync` now performs the whole sequence itself: `dc cvau → dsb ish → ic ivau → dsb ish; isb`.
  When built with zig, `__clear_cache` lacks the `DSB ISH`, so a Cortex-A53 read freshly generated dynarec code through the old cache (zeros, which decode as UDF) and died with SIGILL. This build is made with zig, so it needs this patch. It does no harm when built with gcc.
- **0002, surviving Wi-Fi netplay (v2).**
  - A link is treated as lost after 1.2 seconds without any news (`RFU_NET_TIMEOUT_CYCLES`). The leader's wait for an answer stays at the game's own value (about 11 ms).
  - The received-packet queue goes from a four-entry shifting array to a 128-entry ring queue (`RFU_QUEUE_LEN`). Empty packets are not queued.
  - The guest game gets only one leader packet per frame (`RFU_CLIENT_PER_FRAME`). The leader waits up to 1.2 seconds while more than 12 of its packets are unacknowledged (`RFU_PIPE_MAX`), or while a guest that reported a queue longer than 10 (`RFU_PEER_Q_MAX`) has no packet queued.
  - The guest puts its own queue length into the fourth slot of its ACK, which used to be always 0, with the marker `0x51000000` ('Q'). Stock and v1 send 0 there and don't read it, so mixed pairs still connect.
  - DISCONNECT takes effect after the game has read the packets that arrived before it, so the last greeting gets through.
  - `HOST_SEND`, `CLIENT_SEND` and ACK are accepted only from the current peer (`client_id`), and the length of a guest packet is checked (`blen <= 16 && len >= blen + 12`; the original copies into a 16-byte slot with no length check).
- **0003, less waiting (v3).**
  - While waiting, `netpacket_poll_receive()` is no longer called on every CPU event (about 600 times per frame on the guest). It is called once per 1/8 frame and once when the wait starts (`RFU_POLL_CYCLES`).
  - The leader's "no response" wait is capped at 1/360 s (about 2.8 ms, `RFU_RESP_CAP_CYCLES`; the game's own value if that is shorter).
  - When two or more packets are queued on the guest side, up to two per frame are handed over so it can catch up (`RFU_CLIENT_CATCHUP_Q`). No packet is dropped.
  - The test counters (`HB_STATS`) are off by default. The netpacket layout and the version string (`gpSP v1.0`) are unchanged.

Names starting with `hb_` or `HB_`, and the words `hanbang` and `한방`, in the patched code (and the `hb` in the version string `5819380-hb4`) are only our marker for "changed here". The comments inside the patched code are in Korean and carry the same marker. We left all of it as it is so that patches, binaries and scripts stay consistent.

### How it was checked

- **This build (base `5819380`)**
  - Two RG35XX Pro (KNULLI, home Wi-Fi netplay): FireRed ↔ LeafGreen, Direct Corner → Trade Center.
    - Standing in the trade room for 60 s, the game clock advanced 59.1 s on both devices (old-base v3: 59.15 s).
    - One trade then went through to the end. During the 45 s of the trade the game ran at 0.916 of real time (old-base v3: 0.917; the save sync at the end of a trade is part of the game).
  - Two RG DS Plus: a Ruby ↔ Sapphire link-cable trade (`mul_poke`) and a FireRed ↔ LeafGreen wireless trade both went through to the end, and reading the saves afterwards showed the Pokémon had swapped. 0 communication errors.
- **Measured on the old base (`4caf7a1`)**, with the same RFU code:
  - Two RetroArch 1.22.2 instances in a virtual machine, joined over 127.0.0.1 netplay (`tc netem`: 20–80 ms in one direction plus 1% loss):
    - Jittery battle, 155 s: leader held back for 3.4 / 5.1 s → 2.2 / 1.2 s, stalled frames 335 / 414 → 182 / 127, guest queue average 5.7 / 6.0 → 0.8 (before → after v3).
    - Clean-connection trade room: the two queues together 4.5 → 1.2 frames (about 55 ms less delay), guest receive calls per frame 606 → 8.
    - Jittery trades and battles lasting over 7 minutes: 0 communication errors. Solo play matches stock and v2 frame by frame in screen fingerprint, save and play time (3300 frames).
  - One representative run on two devices: sitting in the trade room for 60 s ran at 59.1 frames per second with 0 gaps over 33 ms, and then went through to the end of the trade, which showed up in both saves.
- Limits: the jitter tests ran in a virtual machine, and the Pokémon ROMs were Korean versions (FireRed, LeafGreen, Ruby, Sapphire).

## Core options

These patches add no options. The gpSP options that matter here are:

| Option | Value | Meaning |
|---|---|---|
| `gpsp_serial` | `rfu` | Emulate the GBA Wireless Adapter (set per game, see below). Our fixes live in this mode. |
| `gpsp_serial` | `mul_poke`, `mul_aw1`, `mul_aw2` | Upstream's link-cable modes (Pokémon Gen 3, Advance Wars 1 and 2). Not changed by us. |
| `gpsp_serial` | `auto` (default) | Upstream picks a mode from the game. We still set `rfu` per game for the wireless games. |
| `gpsp_bios` | `official` | Use the official GBA BIOS. This is what the tests were run with. |

## Install on KNULLI

This is how we set it up on the RG35XX Pro. Adjust paths and names if your setup differs.

1. **Core file.** Put `gpsp_libretro.so` in `/userdata/system/hanbang_cores/` (default path used by the prebuilt files) on the SD card.
   The read-only root's `/usr/lib/libretro/gpsp_libretro.so` is made a symlink to this file (`mount -o remount,rw /`, then `ln -sfn`, then save with `knulli-save-overlay`).
   To replace the core, upload the new file next to the old one while no game is running, check its md5, then `mv` it into place.
2. **Per-game config lines** in `/userdata/system/knulli.conf`. Only games that use wireless trading run on gpSP. All other GBA games keep their usual core.
   ```
   gba["<ROM file name>.zip"].core=gpsp
   gba["<ROM file name>.zip"].retroarchcore.gpsp_serial=rfu
   ```
   KNULLI takes per-game core options as `retroarchcore.<option name>` keys (the device's launch log shows `retroarchcore.gpsp_serial = rfu`).
   The core option is `gpsp_serial = "rfu"` (emulate the Wireless Adapter), and the tests were run with the official BIOS (`gpsp_bios = "official"`).
3. **Update both devices to this build together.** Mixed pairs still connect over the wireless link, but the gain is much bigger when both run v3. The cable modes (`mul_*`) are missing from the old builds, so both devices need this build for them.
4. **Helper scripts** from this repository's [`knulli-scripts/`](../../knulli-scripts/) folder. Copy them to `/userdata/system/claude/` (default path used by the prebuilt files), except for the hook:
   - [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) is the ES game start / stop hook, and it goes to `/userdata/system/scripts/nds_save_sync.sh` (default path used by the prebuilt files). It launches the script below for each game.
   - [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py) writes the save to the card every 10 seconds, because RetroArch turns off SRAM autosave when netplay starts. gpSP is an "each player keeps their own save" core for both the host and the guest.
   - [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py) is the prompt that asks "play together / play alone" when a room for the same game is open (or for a paired set such as FireRed / LeafGreen / Emerald).
5. Trades follow the games' normal flow: the Direct Corner, the Trade Center, the Union Room and so on. The game decides who leads and who is in the group.

### Other devices and operating systems

- This `.so` is for **aarch64 Linux only** (it uses glibc symbol versions up to GLIBC_2.17). On anything else, rebuild from the patches. A macOS arm64 interpreter build was made for test tooling.
- The cache sync in 0001 is switched on only for `ARM64_ARCH` on Linux and has no effect on other platforms.
- You need a frontend that supports RetroArch's **netpacket interface**. Testing was done with RetroArch 1.22.2.
- The save format is unchanged. Saving or loading a state during netplay can break the link.
- Our fixes are for the **Wireless Adapter link**. The cable modes are upstream's and cover only Pokémon Gen 3 and Advance Wars. For other GBA link-cable games, use the [`gba-mgba-dual`](../gba-mgba-dual/) core.
- Remaining limits (not fixed):
  - The 4–6 second slowdown at the end of a trade, while the two games wait for each other at every save block, comes from the game's own design.
  - After a jittery stretch, the leader-side queue (about 11 frames on average, 0.18 seconds) stays. Shrinking it would mean dropping or merging game packets, which is the same kind of thing that caused the original communication error, so it was left alone.
  - A stall that lasts longer than 1.2 seconds can still cause a communication error.

## Build from source

This is exactly how the installed file was built: on a Mac (arm64) with zig 0.17.1, targeting aarch64 Linux with glibc 2.17. The make values are the same as libretro's usual build: `platform=unix CPU_ARCH=arm64 HAVE_DYNAREC=1 MMAP_JIT_CACHE=1`.

```sh
# the patches (this repository)
git clone https://github.com/Squirbie/handheld-link-cores.git
CORE="$PWD/handheld-link-cores/cores/gba-gpsp-rfu"

# upstream at the base commit
git clone https://github.com/libretro/gpsp.git
cd gpsp
git checkout 5819380c2ffb0900219d700a382ee68c464ebb99

# (a) apply the patches one by one, in order
for p in $(grep -v '^#' "$CORE/patches/series"); do git apply "$CORE/patches/$p"; done
# (b) or apply the single combined patch instead (never both)
# git apply "$CORE/patches/all-in-one/gpsp-rfu-v3-vs-5819380.patch"

# wrap zig as the C compiler (the path must not contain spaces)
printf '#!/bin/sh\nexec zig cc -target aarch64-linux-gnu.2.17 "$@"\n' > /tmp/zcc
printf '#!/bin/sh\nexec zig c++ -target aarch64-linux-gnu.2.17 "$@"\n' > /tmp/zcxx
chmod +x /tmp/zcc /tmp/zcxx

make -j8 platform=unix CPU_ARCH=arm64 HAVE_DYNAREC=1 MMAP_JIT_CACHE=1 CC=/tmp/zcc CXX=/tmp/zcxx \
  SHARED="-shared -s -Wl,--version-script=link.T" GIT_VERSION='"5819380-hb4"'
# result: ./gpsp_libretro.so  (dynarec included, stripped)
```

- Building with gcc on aarch64 Linux works too (leave out `CC` and `CXX`), but the bytes will differ, and a gcc build on this base has not been tried.
- The patches also apply with `patch -p1`.
- The Android (arm64) interpreter build was only made on the old base (`4caf7a1`). That binary is not in this folder.

### Reproducibility

- The upstream tree hash of `5819380` is `aa956b7c1f9bc3c0621b25de435f4b8916fc0976`.
- `git apply` in order, `git apply` with the combined patch, and `patch -p1` in order all produce the same tree, `3042ea836b45fff3fecf3fb12508a568f217536f`, where `rfu.c` has the md5 `14aba5dc04763e969628a554646e75f1`.
- Applying this folder's patches to a fresh clone from GitHub and building with the commands above gave a `.so` **byte-identical to the installed one** (sha256 `e21bf6d4…`). This was checked twice, in two separate working folders.
- The version string inside the `.so` is `v1.1.0-5819380-hb4`, and there is a `dsb ish` after `ic ivau`.
- The patches and notes for the old base (`4caf7a1`) are still in the repository at the release tag `2026.11.18`.

## Patches

Apply them in this order. `patches/series` lists the same order. To apply everything at once, use only `patches/all-in-one/gpsp-rfu-v3-vs-5819380.patch` (using it together with the individual patches would apply the changes twice).

Base: libretro/gpsp commit `5819380c2ffb0900219d700a382ee68c464ebb99` (2026-09-19, "Keep the PSG status bits readable in SOUNDCNT_X"), tree hash `aa956b7c1f9bc3c0621b25de435f4b8916fc0976`. Upstream already has the RFU emulation (`rfu.c`) and a netpacket mode. These patches harden it.

| Order | File | What it does | Build on the old base |
|---|---|---|---|
| 1 | [`0001-arm64-linux-cache-sync.patch`](patches/0001-arm64-linux-cache-sync.patch) | arm64 Linux cache sync | |
| 2 | [`0002-rfu-wifi-netplay-robustness-v2.patch`](patches/0002-rfu-wifi-netplay-robustness-v2.patch) | Survive Wi-Fi latency and bursts | v2, md5 `f9379e50ff0538e9a5af9afa5422da58` |
| 3 | [`0003-rfu-less-waiting-v3.patch`](patches/0003-rfu-less-waiting-v3.patch) | Wait and poll less | v3, md5 `8bdd8b56e895a9625cddc932c3e2f926` |

- On this base, only the final build with all three patches was made (md5 `6c86b647977fafeea3a5cccfeb51d5a1`).
- Each patch header (Subject, Origin, a short summary, then the description) says what was changed and why, and what was done when moving to the new base.
- v1 was only the two time-limit lines in `rfu.c` (6 lines added, 2 removed). v2 replaced it, so it is not included separately (the v1 `.so` was `3cbbd19b`).

## Upstream status

Checked on 2026-11-23, on libretro/gpsp `master` (which is this build's base, `5819380`):

- `rfu.c` still keeps received packets in `pkts[4]`, and the time limits are still `rfu_timeout * (16777216 / 60)` and `rfu_rtx_max * (16777216 / 60 / 6)`. Constants such as `RFU_NET_TIMEOUT` or `RFU_QUEUE_LEN` don't exist there.
- `NET_RFU_DISCONNECT` clears the slot immediately, and guest packets (`NET_RFU_CLIENT_SEND`) are not checked against the size of the 16-byte slot.

**Worth sending upstream? Partly.** These are plain bugs:

- a guest packet is copied into the 16-byte slot without a length check (an out-of-bounds write);
- the four-entry queue drops packets when they arrive in a burst;
- a disconnect erases packets that haven't been read yet;
- packets from a device that isn't the current peer are accepted;
- the short time limit mistakes Wi-Fi delay for lost radio signal.

The v2 and v3 constants are tuned to the Wi-Fi environment we tested in, and the ACK fourth-slot extension touches the protocol, so only the robustness fixes should be split out when sending.

- The length and sender checks were split out and sent as [libretro/gpsp#294](https://github.com/libretro/gpsp/pull/294) (still open on 2026-11-23).
- An English title and body for the rest (ring queues, the 1.2 s time-out, draining queued packets before a disconnect) are in [`UPSTREAM.md`](../../UPSTREAM.md) and in the `upstream_pr_candidate` field of [`cores/MANIFEST.gb.jsonl`](../MANIFEST.gb.jsonl).

## License

- **GPL-2.0-or-later**, the same as upstream gpSP (libretro's version). The upstream file headers say version 2 of the License or, at your option, any later version, and the repository's `COPYING` is the text of GPL version 2 (copy: [`LICENSES/gpsp_COPYING`](../../LICENSES/gpsp_COPYING)). These patches are published under the same terms.
- If you distribute the core (`.so`), the upstream commit plus these patches are the corresponding source. Keep the copyright notices in the upstream file headers as they are.
