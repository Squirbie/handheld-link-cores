<p align="center"><a href="UPSTREAM.md"><img src="docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="UPSTREAM.ko.md"><img src="docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# Upstream pull requests

Bug fixes from this repository that would help everyone if they lived upstream, with ready-to-send PR texts.
On 2026-10-29 the fixes listed under "Sent" were re-extracted against the latest upstream, built and sent. All drafts, sent or not, are kept below for reference.
Upstream comparison as of 2026-10-29.

## Sent

| PR | What |
|---|---|
| [libretro/beetle-wswan-libretro#105](https://github.com/libretro/beetle-wswan-libretro/pull/105) | Fix non-deterministic savestates (LRAV tail) and guard the V30MZ loop |
| [libretro/beetle-ngp-libretro#121](https://github.com/libretro/beetle-ngp-libretro/pull/121) | Save the Z80 IRQ line, fix flash block merging, restore ROM and flash on load |
| [finalburnneo/FBNeo#2845](https://github.com/finalburnneo/FBNeo/pull/2845) | d_legionna: Grainbow P3/P4 Start on DrvJoy3 bits 8/9 |
| [libretro/gambatte-libretro#289](https://github.com/libretro/gambatte-libretro/pull/289) | Partial serial shift under HAVE_NETWORK; restore the cartridge before re-init on reset |
| [libretro/mame2003-plus-libretro#2177](https://github.com/libretro/mame2003-plus-libretro/pull/2177) | H6280 CPU state; battlera/actfancr HuC6270 and driver state |
| [libretro/mame2003-plus-libretro#2178](https://github.com/libretro/mame2003-plus-libretro/pull/2178) | Leave read-only banks of 1 MiB or more out of the save state |
| [libretro/blueMSX-libretro#212](https://github.com/libretro/blueMSX-libretro/pull/212) | Save cartridge SRAM/flash on unload; WD2793 track-position tags |
| [libretro/gpsp#294](https://github.com/libretro/gpsp/pull/294) | RFU: validate packet sizes and senders (out-of-bounds write, missing break) |
| [beebono/DSperate#34](https://github.com/beebono/DSperate/pull/34) | Deliver ARM9 IPC FIFO words to the ARM7 at their send time |

Prepared but not opened: melonDS DS (its contributing guide asks for PR text written by a person) — branch [`netpacket-wallclock-timeout`](https://github.com/Squirbie/melonds-ds/tree/netpacket-wallclock-timeout).

## Drafts

| Package | Upstream | State | PRs drafted |
|---|---|---|---|
| [`arcade-mame2003-plus`](cores/arcade-mame2003-plus/) | [libretro/mame2003-plus-libretro](https://github.com/libretro/mame2003-plus-libretro) | 460 upstream commits since our base; 5 of our files changed upstream | 5 |
| [`arcade-fbneo`](cores/arcade-fbneo/) | [libretro/FBNeo](https://github.com/libretro/FBNeo) | 3389 upstream commits since our base; none touch our files | 1 |
| [`ds-melonds-ds`](cores/ds-melonds-ds/) | [JesseTG/melonds-ds](https://github.com/JesseTG/melonds-ds) | upstream unchanged since our base | 1 |
| [`ds-dsperate`](cores/ds-dsperate/) | [beebono/DSperate](https://github.com/beebono/DSperate) | 46 upstream commits since our base; 1 of our files changed upstream | 1 |
| [`gb-gambatte-link`](cores/gb-gambatte-link/) | [libretro/gambatte-libretro](https://github.com/libretro/gambatte-libretro) | 87 upstream commits since our base; 5 of our files changed upstream | 1 |
| [`gba-gpsp-rfu`](cores/gba-gpsp-rfu/) | [libretro/gpsp](https://github.com/libretro/gpsp) | 76 upstream commits since our base; 2 of our files changed upstream | 1 |
| [`wswan-mednafen-dual`](cores/wswan-mednafen-dual/) | [libretro/beetle-wswan-libretro](https://github.com/libretro/beetle-wswan-libretro) | upstream unchanged since our base | 1 |
| [`ngp-mednafen-dual`](cores/ngp-mednafen-dual/) | [libretro/beetle-ngp-libretro](https://github.com/libretro/beetle-ngp-libretro) | 4 upstream commits since our base; none touch our files | 1 |
| [`msx-bluemsx`](cores/msx-bluemsx/) | [libretro/blueMSX-libretro](https://github.com/libretro/blueMSX-libretro) | 101 upstream commits since our base; 32 of our files changed upstream | 1 |

Notes: the MAME 2003-Plus flag-bit fix (our patch 0002, 2026-10-21) landed upstream on 2026-10-24 as [#2131](https://github.com/libretro/mame2003-plus-libretro/pull/2131), and upstream also saved the timer system that month ([#2133](https://github.com/libretro/mame2003-plus-libretro/pull/2133)). Our large patch 0001 overlaps #2133 and is not planned; the five smaller MAME fixes below are still missing upstream.

## Arcade — `arcade-mame2003-plus`

Upstream: https://github.com/libretro/mame2003-plus-libretro · 460 upstream commits since our base; 5 of our files changed upstream

### H6280: register CPU state; battlera/actfancr: save HuC6270 VDC and driver state (netplay, rewind)

Patches: ['0003']

```markdown
## Summary

The H6280 core registers nothing with the save-state system, and the HuC6270 video chip of the `battlera` board (128 KiB VRAM, 20 registers, palette, scanline/IRQ bookkeeping) and the driver's port-select/ADPCM toggle are not registered either. After `retro_unserialize()` the CPU keeps running from its own PC, registers, MMR bank map and timer, and the screen is drawn from the old VRAM of whoever loads the state. For `battlera` (and `actfancr`, which uses the same CPU as its sound CPU) that means a blank or diverging screen when a netplay guest loads the host's state, and a diverging replay after rewind or run-ahead.

## Changes

- `src/cpu/h6280/h6280.c`: register PPC/PC/SP/ZP/EA, A/X/Y/P, the 8 MMR registers, IRQ mask, timer status/ack/value/load, extra cycles and the NMI/IRQ1/IRQ2/timer-IRQ lines (plus NZ when `LAZY_FLAGS`) in `h6280_init()`, per CPU instance, the way `m6809_init()` does.
- `src/vidhrdw/battlera_vidhrdw.c`: register VRAM, the 20 VDC registers, VDC_register, vram_ptr, current_scanline, inc_value, the enable flags, `last_line` (moved out of a function-local static) and the palette RAM. A postload handler marks every tile/sprite/VRAM dirty flag and recomputes the 512 palette entries.
- `src/drivers/battlera.c`: register `control_port_select`, `msm5205next` and the ADPCM toggle (moved out of a function-local static) from a new `DRIVER_INIT`.

## Testing

Headless harness: the host runs 20 s or 60 s and calls `retro_serialize`; a fresh process loads the same ROM, runs 2 frames, calls `retro_unserialize` and runs 300 frames while we compare a SHA-256 of every raw frame against the host. `battlera`: 0/300 -> 300/300 (state 23,656 -> 156,010 bytes). `actfancr`: 92/300 (20 s) and 7/300 (60 s) -> 300/300 (56,672 -> 56,735 bytes). A driver that does not use the H6280 produces a byte-identical state. Host-side video is unchanged. Not covered: the PC Engine sound chip (C6280) and the MSM5205 internals are still not saved.

The patch was written against 61305d60 on top of our own timer/scheduler work, so it needs a rebase and a re-test on current master (which now saves the timers itself, #2133).
```

### mame-memory: leave read-only banks of 1 MiB or more out of the save state

Patches: ['0004']

```markdown
## Problem

`register_banks()` registers the RAM behind every bank that appears in a memory map. Banks that only ever show up in *read* maps are ROM (for example the ST-V cartridge bank, 48 MB, or the CAGE sound-board ROM banks, 2 + 16 MB), but they are still copied into every save state. A state is then 20-53 MB for those boards, and netplay, rewind and run-ahead keep dozens of states at once (44 on the host in our RetroArch build), which runs a 1 GB handheld out of memory.

## Change

Remember whether each bank appears in a write map (`bankwrite[]`) and skip registering a bank of 0x100000 bytes or more that never does. RAM banks and smaller banks are unchanged, so the state layout of every other driver stays the same. An INFO log line reports each skipped bank.

## Testing

State size: about 20 MB -> 1.6 MB (CAGE-based board) and about 50 MB -> 3.2 MB (an ST-V set). The state sizes of the other drivers we measured are unchanged.

Caveat: a driver that modifies a ROM bank without going through a write map would no longer have those bytes in its state. We did not find such a driver in our tests, but the heuristic deserves a maintainer's eye. Written against 61305d60; needs a re-test on current master.
```

### Atari GT: save TMS32031, CAGE and sprite-engine state; atarigen: register UINT8 variables as UINT8

Patches: ['0005', '0006']

```markdown
## Summary

The Atari GT board (TMS32031 sound DSP, CAGE sound board, `atarirle` sprite engine) has large parts of its state unregistered, so a guest that loads a host state starts with different sprites from the first frame, and a rewind inside one process kills it (`Unimplemented op` from the sound DSP). `atarigen.c` also registers five UINT8 variables as INT32, so a save/load overwrites three neighbouring bytes of each.

## Changes

- `tms32031.c`: register PC, the 36 registers (40-bit values as two 32-bit halves), BKMASK, PPC, OP, delayed-branch/IRQ/MCU state, interrupt cycles.
- `cage_sndhrdw.c`: latches, buffer position, serial rate, DMA/timer enable bits, command/control values, the DMA and two timers via `timer_save_register`, the 16,384-sample sound buffer (zero-filled at start; it was uninitialised).
- `atarirle_vidhrdw.c`: the internal sprite copy (256 x 8 words), `partial_scanline`, `control_bits`, `command`, `is32bit` and the four 336x240 sprite buffers.
- `atarigt_vidhrdw.c` / `atarigt.c`: tile/colour banks, scroll registers, TRAM checksum, protection state (`protaddr[4]`, `protmode`, `protresult`, `protdata[0x800]`, `ignore_writes`); a postload handler rebuilds `expanded_mram` and the tilemap scroll/colour offsets.
- `atarigen.c`: UINT8 registered as UINT8; the VBLANK/scanline callbacks of `atarigt` use persistent timers that are part of the state. Other Atari boards keep the original `timer_set()` path (using persistent timers for all of them changed the host picture of two other Atari games).

## Testing

Same harness as above. `primrage`: states taken at 20/60/120/180 s all give 300/300 (before: 0-16/300); a rewind loop inside one process (save every frame, every 7th frame go back 1/3/6 frames and replay) is identical, where the old code died with `Unimplemented op`. Host video is unchanged for 19 Atari/other drivers. State size 1,589,080 -> 2,273,679 bytes (the four sprite buffers are 645,120 of the difference). The `tmek` driver and Midway V-Unit (same DSP core) were not tested because we have no ROMs.

Written against 61305d60 with our own timer work underneath; it must be rebased on the new timer save-state code (#2133).
```

### Atari: rebuild slapstic ROM copy, MO display-list cache and scroll after a state load; save Atari System 1 timers and pens

Patches: ['0007']

```markdown
## Summary

Several Atari drivers keep state outside the registered variables, so a loaded state does not reproduce the host's screen: the slapstic bank is restored as a number but the ROM copy that CPU reads is not; `atarimo` caches the sprite display list ("same link as last time, do not rebuild"); `gauntlet` only pushes its scroll and tile bank into the tilemap when the value *changes*; Atari System 1 misses the priority pens, tile bank, Y-scroll bookkeeping and its three MO interrupt timers.

## Changes (behaviour of normal emulation is unchanged: registrations and postload handlers only)

- `atarigen.c`: `atarigen_slapstic_postload()` re-copies the ROM bank from the saved slapstic bank.
- `atarimo_vidhrdw.c`: postload invalidates the display-list cache (`last_link = -1`).
- `gauntlet.c` / `gauntlet_vidhrdw.c`: register `speech_val`, `last_speech_write`, `sound_reset_val`, `playfield_tile_bank`; postload pushes the X/Y scroll from RAM back into the tilemap and marks it dirty.
- `atarisy1.c` / `atarisy1_vidhrdw.c`: joystick timer/interrupt/6522 registers, priority pen, tile bank, next-timer scanline, the INT3 timers (`timer_save_register`), the applied Y scroll; postload re-applies scroll and dirties the playfield. The trackball's function-local static moves to file scope so it can be registered.

## Testing

Host runs 20/60 s, a fresh process loads the state, 300 frames compared by SHA-256 of the raw frame: `gauntlet` 0/300 -> 300/300, `marble` 299/300 -> 300/300, `roadblst` 294/300 -> 300/300, also after reloading the same state twice. 19 regression drivers: host video identical to the previous build in all of them. State size grows by 5 bytes (`gauntlet`) and 170 bytes (System 1). Input-free tests only; trackball/wheel values are barely exercised by them.

Written against 61305d60; rebase on current master needed.
```

### Vs. System: save MMC3 mapper state and protection counters, restore banking after a state load

Patches: ['0008']

```markdown
## Summary

The Vs. System (NES-based) MMC3 mapper does not save its registers, a function-local `static last_bank`, the mirroring register, nor the protection counters of three games, and nothing rebuilds the PRG window (a `memcpy` into the ROM area) or the IRQ callback after a load. A guest that loads a host state therefore sees a broken background/banking, and the two protection-counter games diverge at once.

## Changes

- `vsnes_machine.c`: register `MMC3_cmd`, `MMC3_prg0/1`, `MMC3_chr[6]`, `IRQ_enable/count/count_latch`, a file-scope `MMC3_last_bank` (was a static inside `mapper4_w`) and `MMC3_mirror_reg`; `mapper4_postload()` re-applies PRG/CHR banking and mirroring and reinstalls the scanline callback; the protection counters (`supxevs_prot_index`, `security_counter`, `VSindex`) are registered. Normal emulation is unchanged.

## Testing

24 Vs. System sets, state taken at 20 s: 22 already matched 300/300; the two protection-counter games went 0/300 -> 300/300 (also at 60 s). Host-side video is identical to the previous build for those 24 and four other drivers. Input-free tests only.

Written against 61305d60; needs a re-test on current master.
```

## Arcade — `arcade-fbneo`

Upstream: https://github.com/libretro/FBNeo · 3389 upstream commits since our base; none touch our files

### d_legionna: map Grainbow P3/P4 Start to DrvJoy3 bits 8/9 (they aliased P2 Up/Down)

Patches: ['patches/patch_fbneo.py', 'patches/patch_grainbow.py']

```markdown
## Problem

In `GrainbowInputList` (`src/burn/drv/pst90s/d_legionna.cpp`) the entries

    {"P3 Start",  BIT_DIGITAL,  DrvJoy1 + 8,  "p3 start"},
    {"P4 Start",  BIT_DIGITAL,  DrvJoy1 + 9,  "p4 start"},

use the same `DrvJoy1` bits as `P2 Up` / `P2 Down` (`DrvJoy1 + 8` / `DrvJoy1 + 9`). On the hardware these two are the START3/START4 bits (0x0100 / 0x0200) of the system port at 0x10074c, which the driver reads from `DrvInputs[2]`, i.e. `DrvJoy3` (P1 Start, P2 Start and Service already live at `DrvJoy3 + 0/1/3`).

Symptoms (`grainbow` / its clones, libretro core):
- `P2 Up` and `P2 Down` never reach the game. As far as we can tell the later, idle P3/P4 Start entries write 0 over the shared bits on every poll. In a scripted 40-frame test the screen change caused by P2 up/down was 0 with the stock build and 1221 / 1671 (arbitrary units) after the fix.
- In the service-mode I/O test the cells are wrong: pressing P3 Start lights the "P-2 UP" cell and P4 Start lights "P-2 DOWN"; after the fix they light the ST3 / ST4 cells.

## Fix

    -	{"P3 Start",		BIT_DIGITAL,	DrvJoy1 + 8,	"p3 start"	},
    -	{"P4 Start",		BIT_DIGITAL,	DrvJoy1 + 9,	"p4 start"	},
    +	{"P3 Start",		BIT_DIGITAL,	DrvJoy3 + 8,	"p3 start"	},
    +	{"P4 Start",		BIT_DIGITAL,	DrvJoy3 + 9,	"p4 start"	},

(whitespace approximate). The driver declares 2 players, so P3/P4 Start only matter for the test menu and for hardware fidelity; if you prefer to drop the two entries, that also removes the aliasing.

## Testing

I have not rebuilt from source. I verified the equivalent change on a prebuilt aarch64 libretro core (v1.0.0.03, 74a979724) by editing the two relocation addends of the input table (`DrvJoy1+8/+9` -> `DrvJoy3+8/+9`, two bytes) and testing on an Anbernic RG35XX Pro / RetroArch 1.22: P2 up/down work, the I/O test cells are right, and state hashes of nine other drivers are unchanged. Please treat the diff above as untested at source level; I am happy to rebuild and retest if you want it that way. Still present on `master` as of 2026-10-29.
```

## Nintendo DS — `ds-melonds-ds`

Upstream: https://github.com/JesseTG/melonds-ds · upstream unchanged since our base

### libretro netpacket MP: use a wall-clock reply timeout and stop waiting once every client has answered (even with a blank reply)

Patches: ['patches/0001-rom-file-mapping.patch', 'patches/0002-netplay-wallclock-timeout-and-blank-replies.patch', 'patches/0003-l2-popup.patch', 'patches/0004-lid-close-hotkey-off.patch', 'patches/0005-drastic-style-controls-and-pip.patch', 'patches/0006-ui-v2-auto-popup-badges-pip-quality-mp-stats.patch']

```markdown
## Summary

Two fixes to the libretro netpacket multiplayer path. Without them, two slow ARM handhelds playing DS wireless games over Wi-Fi regularly dropped the link.

## Problems

1. `MpState::NextPacketBlock()` waits for a packet with `std::clock()` and a 25 ms budget. `std::clock()` is process CPU time (summed over all threads on glibc), not wall-clock time, so the real wait is shorter than 25 ms whenever other threads (threaded renderer, audio) are busy. On a slow core the host gave up on a client's reply too early and the DS game dropped the link.
2. `Platform::MP_RecvReplies()` only stops once every client in `aidmask` has sent a non-empty reply. A client that is not ready answers a CMD with an empty reply (AID 0, see `SendMPReply` in melonDS's `Wifi.cpp`), which is dropped here, so the host always waits out the full timeout. Standalone melonDS stops waiting once every client has answered, blank or not.

## Changes

- Wait until a `std::chrono::steady_clock` deadline instead of CPU time (150 ms in our build), and `std::this_thread::yield()` while polling. (We also read `MELONDSDS_MP_TIMEOUT_MS`, 5-2000, for experiments; happy to drop that or turn it into a core option.)
- Tag each received packet with the netplay client id (`Packet::Sender`) and remember the AID each client last replied with (`MpState::ReplyAid`), so a blank reply can be attributed to its client. A blank reply counts as "answered" for the wait loop, but its data is not copied and it is not set in the returned mask.

## Testing

Two Anbernic RG35XX Pro handhelds (Cortex-A53, 1 GB RAM) over Wi-Fi, same core build on both, RetroArch netpacket: Mario Kart DS races (about 22 fps in the race and 29 fps in the lobby on this hardware, no reply timeouts) and Pokemon Gen 4/5 trades (with our other, unrelated patches applied). Not tested on other hardware, and not yet rebased or retested against current `main`.

The patch is written against v1.4.0 (f394adba) and touches `src/libretro/net/mp.{cpp,hpp}`, `src/libretro/libretro.cpp` and `src/libretro/core/core.hpp`.
```

## Nintendo DS — `ds-dsperate`

Upstream: https://github.com/beebono/DSperate · 46 upstream commits since our base; 1 of our files changed upstream

### Deliver ARM9 IPC FIFO words to the ARM7 at their send time (fixes boot-time white screens, e.g. with a generated firmware)

Patches: ['patches/dsperate-v3.0.3-hbipc-full.patch']

```markdown
## Summary

The ARM9 runs each scheduling slice first and the ARM7 catches up afterwards, so a word the ARM9 writes to `IPCFIFOSEND` in the middle of a slice is pushed into the FIFO at once and the ARM7 sees it up to a slice (2048 cycles) before the ARM9 actually sent it. This exposes a boot-time race in the NitroSDK and can leave some titles on a white screen.

## Symptom

With the generated firmware (no firmware dump), some titles hang on a white screen right after boot; we saw it with Picross DS (Korean release). Stock v3.0.3 reproduces it headlessly (real BIOS, generated firmware, `--rtc-host`, JIT). It is a cycle-level timing race: JIT vs. interpreter, moving vs. fixed RTC, fast vs. exact and similar choices decide which runs hang (8 of 48 combinations hung in a sweep on our fork before this fix), so it is easy to miss when a firmware dump is present. We believe the same race caused white screens with Super Mario 64 DS (Korean release) in some timing conditions.

## Cause

Korean titles read the firmware user area from the ARM9 through PXI NVRAM (tag 4) right after boot. In the NitroSDK ARM7 `SPI_Init`, the PXI receive callbacks are registered before the message queue and its entry ring exist. When the ARM7 sees the word early it handles it before the queue exists: `SendMessage` fails with EXCLUSIVE, the ARM9 retries, the retry lands in the queue but is then wiped by the ring clearing and answered as a touch-panel result (wrong tag), so the ARM9 waits forever.

## Fix

When the ARM9 (running, not a DMA) writes `IPCFIFOSEND`, hold the word in `Io::ipc9_pending`, end the ARM9 slice there (`Scheduler::yield`), and push it into the FIFO from `Scheduler::fire_due()` once the ARM7 has caught up (`Io::ipc_deliver()`), raising the IRQ then. The ARM9's own view of its send FIFO (empty/full flags, send-empty IRQ) counts the held words. ARM7->ARM9 traffic, IPCSYNC and DSi are unchanged. The save-state format is unchanged (held words are flushed before saving; a slice boundary never has any). `DS_IPC_DEFER=0` restores the old behaviour.

## Results

- 48-condition sweep on our fork (JIT/interpreter x moving/fixed RTC x fast/exact x idle-skip modes x firmware language), once with no firmware file and once with a generated firmware passed as a file: white screens 8/48 -> 0/48 in both; `DS_IPC_DEFER=0` brings them back. Super Mario 64 DS (Korean) also booted in all 48 conditions.
- Normal conditions (JIT, fixed RTC, fast): the 1800-frame screen hash is bit-identical to before; median frame time 0.43 ms vs 0.47 ms in our VM. Cost: about 4.3 extra slice ends per frame (7,826 ARM9 FIFO sends in 1800 frames).
- Tested on aarch64 Linux only; ctest passes (32 tests).

The change lives in `src/core/io/io.{cpp,h}` and `src/core/sched/scheduler.cpp` (search for `ipc9_pending` in the full patch of our fork). It is written against v3.0.3 (f5fa35e) and would need rebasing on `main`.
```

## Game Boy / Color — `gb-gambatte-link`

Upstream: https://github.com/libretro/gambatte-libretro · 87 upstream commits since our base; 5 of our files changed upstream

### Fix partial serial shift under HAVE_NETWORK and restore ROM bank 0 before re-initialising on reset

Patches: ['patches/0001-netpacket-link-cable-with-timing-v4bw.patch', 'patches/0002-gbc-infrared-over-netplay-v5ir.patch', 'patches/0003-reply-00-not-ff-to-unheard-byte-v5irh.patch', 'patches/0004-hold-second-byte-to-next-frame-v5irh2.patch', 'patches/0005-infrared-meet-before-led-and-pulse-tail-v5irh3.patch']

```markdown
Two small, independent fixes in the emulation core, found while putting a different serial transport (RetroArch netpacket) on top of SerialIO. Happy to split this into two PRs. They are written against 4041d5a; both spots look unchanged on master, so I would rebase before sending (GB::reset() now calls full_init(false)).

1) Memory::updateSerial (HAVE_NETWORK): wrong bits are shifted in when SB/SC/IF is read while a byte is on the wire.
Both the completion path and the partial path shift in `serialize_value_ >> (8 - n)`, i.e. the top n bits of the incoming byte, every time. After a first partial update (serialCnt_ < 8) the top bits are already in SB, so the remaining n bits must come from the low bits: `((serialize_value_ << (8 - serialCnt_)) & 0xFF) >> (8 - n)`. A game that polls SB/SC/IF mid-transfer therefore receives a rotated byte (0x20 arrived as 0x08 and 0x60 as 0x30 in the Yu-Gi-Oh! Duel Monsters link handshake). Writing SC during the transfer still sets serialCnt_ back to 8 and delivers the byte whole, as before. The arithmetic does not depend on the transport; the TCP "GB Link" mode uses the same Memory code.

2) GB::reset(): a reset while the boot ROM is mapped turns the boot ROM into the "cartridge backup".
full_init() calls bootloader.reset()/load(), and load() copies the first 0x100/0x900 bytes of ROM bank 0 into rombackup before overlaying the boot ROM. If reset() runs before the FF50 write, bank 0 already contains the boot ROM, so after FF50 the cartridge head never comes back (white screen with a CGB boot ROM; found with a CGB game that was restarted while the logo was still spinning). Calling bootloader.call_FF50() first (it only acts while the boot ROM is mapped and in use) restores the cartridge before it is snapshotted.

Testing: (1) found and checked with a two-instance harness over netplay (Yu-Gi-Oh! Duel Monsters link handshake); (2) a restart during the CGB logo of three beatmania GB titles went from a white screen to 54/54 passing harness runs. Not tested on real hardware.
```

## Game Boy Advance — `gba-gpsp-rfu`

Upstream: https://github.com/libretro/gpsp · 76 upstream commits since our base; 2 of our files changed upstream

### RFU: survive netplay latency and bursts (ring queues, 1.2 s no-news time-out), bound client packet length, drain queued data before DISCONNECT, accept only the current peer

Patches: ['patches/0001-arm64-linux-cache-sync.patch', 'patches/0002-rfu-wifi-netplay-robustness-v2.patch', 'patches/0003-rfu-less-waiting-v3.patch']

```markdown
Netplay over Wi-Fi exposes several weak spots in the RFU emulation. This PR is the part I believe is plain bug fixing or robustness work; the tuning-heavy parts of my local patches (extra back-pressure constants, an ACK queue-length hint, fewer receive polls) are left out and can be proposed separately.

1) Time-outs are in emulated RF time. rfu_timeout (32 frames, ~533 ms) and rfu_resp_timeout (~11 ms) come from the radio, but a netplay round trip takes tens to hundreds of ms and sometimes stalls for half a second. After such a stall the leader reports "no response", the game takes it for RF packet loss and ends in a link error. Use at least 1.2 s for the "no news at all" time-out (RFU_NET_TIMEOUT_CYCLES) and keep late answers instead of dropping them.
2) Packet queues overflow and drop data. rfu_host.clients[].pkts[] and rfu_client.pkts[] hold four entries and are shifted with memmove. When the Wi-Fi releases a burst, entries beyond the fourth are dropped ("Client dropped a host packet" / "Host dropped a client packet") and the game, which expects every RF packet, ends in a link error (after about five minutes of trading in our case). Use 128-entry ring queues and do not queue empty packets.
3) Out-of-bounds copy from the network. NET_RFU_CLIENT_SEND copies `blen = hdata >> 24` (0..255) bytes into a 16-byte slot and reads that many bytes from the packet without checking the packet length. Check `blen <= 16 && len >= blen + 12`.
4) DISCONNECT discards unread data. The slot is cleared immediately, so packets that arrived before it and were not yet read by the game are lost and the game misses the last greeting. Mark the slot pending and drop it once its queue is drained.
5) Packets from other peers. HOST_SEND / CLIENT_SEND / ACK are accepted from any client_id; with three or more peers a late packet from a previous leader can end up in the current queue. Accept them only from the current host / client slot.

Testing: two RetroArch 1.22.2 instances (Korean FireRed / LeafGreen, Direct Corner -> Trade Center trades, plus Colosseum battles). (a) Stock core: with 20-300 ms of injected jitter plus 2% 500 ms stalls per direction, FireRed shows the link error during the first walk after entering the room. (b) With the full local patch set (these fixes plus the tuning parts), a seven-minute session under tc netem (delay 50 ms +-30 ms, 1% loss) ended without link errors, and solo play is frame-identical to stock over 3300 frames. I have not run the trimmed subset on its own, and only the FireRed / LeafGreen / Emerald pairs have been tried.
```

## WonderSwan — `wswan-mednafen-dual`

Upstream: https://github.com/libretro/beetle-wswan-libretro · upstream unchanged since our base

### Fix non-deterministic savestates (unused LRAV tail) and guard the V30MZ loop against zero-cycle instructions

Patches: ['patches/0001-WonderSwan-UART-accurate-status-timing-and-level-IRQ.patch', 'patches/0002-Libretro-run-a-frame-line-by-line-hb_ws_-API-for-a-t.patch', 'patches/0003-Libretro-zero-the-unused-tail-of-the-60Hz-audio-cach.patch', 'patches/0004-Libretro-add-Beetle-WonderSwan-Dual-two-WonderSwans-.patch', 'patches/0005-Libretro-dual-trace-heartbeat-every-60-shown-frames-.patch', 'patches/0006-screen-file-runtime-selection.patch', 'patches/0007-guest-own-save.patch', 'patches/0008-netplay-version-length.patch', 'patches/0009-ownsave-harden.patch', 'patches/0010-rotate-portrait.patch', 'patches/0013-ws16-from-0010.patch', 'patches/0014-ws17-serial-overwrite-cpu-guard.patch', 'patches/0015-ws18-shanghai-mode.patch', 'patches/0016-ws19-pair-game.patch']

```markdown
Two small, independent fixes found while running two WonderSwan instances in lockstep under RetroArch rollback netplay. I can split them into two PRs if you prefer.

### 1. Make savestates reproducible (libretro.c, `StateAction`)

The `LRAV` section stores all 8192 entries of the static `lrav_60hz_stage` array, but on save only the first `lrav_60hz_pos` entries are refreshed. The remaining entries keep bytes left over from earlier saves or from the last loaded state, so two runs with the same emulation state can serialize different bytes. With RetroArch netplay this shows up as CRC mismatches and a resync after every rollback; it also makes state files non-reproducible.

Fix: clamp `lrav_60hz_pos` to >= 0 and zero the unused tail (`memset(lrav_60hz_stage + lrav_60hz_pos, 0, (8192 - lrav_60hz_pos) * sizeof(int16_t))`) before the section is written. Emulation itself is unaffected.

### 2. Guarantee forward progress in `v30mz_execute` (mednafen/wswan/v30mz.c)

`v30mz_execute` loops `while (v30mz_ICount > 0)`. If the CPU runs into a region of opcodes that consume no cycles in this core (we hit it with the undefined `FF /7` form after a game's stack frame had been corrupted), `v30mz_ICount` never decreases and the loop never ends, which freezes the whole frontend.

Fix: remember `v30mz_ICount` before executing an instruction and, if it did not decrease, charge one cycle. In every flow we compared (several games, solo and linked) the state fingerprints were identical before and after, i.e. normal code never takes this path; it is only a safety net.
```

## Neo Geo Pocket — `ngp-mednafen-dual`

Upstream: https://github.com/libretro/beetle-ngp-libretro · 4 upstream commits since our base; none touch our files

### Savestate fixes for rollback/run-ahead: save the Z80 IRQ line, fix flash block merging, restore ROM/flash on load

Patches: ['patches/0001-NGP-save-the-Z80-IRQ-line-in-savestates.patch', 'patches/0002-NGP-Dual-link-cable-for-two-consoles-in-one-core.patch', 'patches/0003-NGP-deterministic-flash-state-rollback-netplay.patch', 'patches/0004-NGP-Dual-refuse-states-made-with-other-ROMs.patch', 'patches/0005-NGP-Dual-option-descriptions-use-instead-of.patch', 'patches/0006-NGP-Dual-BIOS-default-serial-handlers-at-COMINIT.patch', 'patches/0007-NGP-Dual-1.1-os4-guest-own-save-kind-3-and-NGP-partner-pairs.patch', 'patches/0008-NGP-Dual-1.2-os5-INTTX0-when-the-transmit-buffer-emp.patch', 'patches/0009-NGP-Dual-1.2-os5-COMRECIVESTART-asserts-RTS.patch', 'patches/0010-NGP-Dual-1.2-os5-COMCREATEDATA-returns-FF-when-the-s.patch', 'patches/0011-os5rtc-p2-rtc-skew.patch']

```markdown
Found while running two Neo Geo Pocket instances under RetroArch rollback netplay (SNK vs. Capcom: Card Fighters' Clash went out of sync after a few minutes and right after "New Game"). All three problems are in the single-instance core. I can split them into separate PRs if you prefer.

1. **Z80 IRQ line missing from the savestate** (mednafen/ngp/Z80_interface.c). `iline` (z80_ops.c) is not part of the Z80 section, so after a load the Z80 can take a different path than the original run. Fix: add `{ &(iline), sizeof(iline), 0x80000000, "iline" }` to the state table.

2. **`flash_optimise_blocks()` shrinks blocks** (mednafen/ngp/flash.c). When a block lies inside the previous one, the old code sets the merged length from the *next* block's end (see the existing `FIXME: std::max`), so an erased 32 KB save sector can shrink to a few hundred bytes after a later write. Because every savestate calls this function, loading a state restores a different save area. Fix: use the larger of the two ends and never merge past the 16-bit length.

3. **Loading a state that has no flash data** (mednafen/ngp/system.c, `FLASH_StateAction`). The ROM image (which contains the flash writes) and the flash block list from the newer timeline were left as they were. Now the ROM is restored from `orig_data` (re-applying `rom_hack()`) and the block list is cleared. A pending flash command (`memory_flash_command`, the 0x5555/0x2AAA sequence) is also not part of any state section today and is worth saving.

Each change is small and does not alter normal single-player behaviour.
```

## MSX — `msx-bluemsx`

Upstream: https://github.com/libretro/blueMSX-libretro · 101 upstream commits since our base; 32 of our files changed upstream

### Save battery-backed SRAM/flash on unload, fix the WD2793 state tag typo, and make savestates complete and byte-stable

Patches: ['patches/01-sramflush-disk.patch', 'patches/02-flashsave.patch', 'patches/03-hbnp1-netplay-sync.patch']

```markdown
This comes from running blueMSX under RetroArch rollback netplay on handhelds, and from noticing that in-game saves were lost. It is a lot of small changes; I'm happy to split it into the three parts below.

### A. Write battery-backed cartridge SRAM / flash when the content is unloaded (libretro.c)

`retro_unload_game()` frees `image_buffer` and destroys the properties, but never tears the emulated board down, so the mapper `destroy` callbacks that call `sramSave()` never run. In-game saves of Koei, ASCII8/16 SRAM and MegaFlashROM cartridges are lost on every restart. Fix: call `boardInfo.destroy()` (and clear the pointer) at the start of `retro_unload_game()`.

### B. WD2793 save/load tag mismatch (Src/IoDevice/WD2793.c)

`wd2793SaveState()` writes `"diskTracks[0]"` .. `"diskTracks[3]"` but `wd2793LoadState()` reads `"diskTracks0"` .. `"diskTracks3"`, so the head positions are always restored as 0. In our tests this made the RAM of a disk game (M.U.L.E.) diverge from frame 1724 on after a state load. Fix: read the name that is actually written and fall back to the old name, so old states still load.

### C. Make savestates complete and byte-stable (Src/Board, Src/IoDevice, Src/Memory, Src/Emulator)

For rollback netplay / run-ahead / rewind, a load has to reproduce the exact machine state and a save has to be byte-stable. We found and fixed:

- `retro_unserialize` did not clear the timer list before loading device state (blueMSX's own rewind calls `boardTimerCleanup` first), so timers of the pre-load timeline fired at wrong times. Timers whose time had passed but had not fired yet were dropped on load (the mixer timer could stop forever), and the board's pending-interrupt queue and 64-bit time were not restored.
- RTC mode and CMOS contents, the audio mixer (time, pending samples, timer), DAC / key click, SCC, the MSX-AUDIO resample position, the OPL noise generator, the floppy sound motor and the MSX-MUSIC feedback / output filter were missing from the state.
- Uninitialised memory leaked into the state bytes (about 150 `malloc` calls changed to `calloc`; for the C++ sound-chip objects we used a zero-filling global `operator new`, but initialising the members in their constructors would be the cleaner upstream fix), as did file-name fields, alignment padding, the machine name and a per-second "saved at" timestamp, so identical emulation could serialize differently.
- Safety: the 2 MB state buffer size was not checked (an MSX2 state is about 1.76 MB), and the in-memory zip file-count limit of 64 silently dropped device state when exceeded.

RetroArch 1.22 netplay has the host send a CRC of the whole state buffer; before this change the CRC never matched, so the guest either gave up checking or requested the full state again and again.

Testing: a headless harness ran 8 games (MSX1, MSX2, one disk game) for 3600 frames each with random input, twice, with a state save every frame, with a one-hour clock difference, with a late-joining guest and with rollback. Before: state bytes differed and sound/RAM diverged after a join or rollback. After: MSX1 is identical everywhere; MSX2 is identical except for the first 1-2 video frames after a load (the video buffer is not part of the state).
```

## Not sent

- `arcade-mahjong-pad` — setup-specific feature or no stand-alone upstream fix; see the package README.
- `gba-mgba-dual` — setup-specific feature or no stand-alone upstream fix; see the package README.
- `gg-genesisplusgx-dual` — setup-specific feature or no stand-alone upstream fix; see the package README.
- `nes-fceumm-mapper14` — setup-specific feature or no stand-alone upstream fix; see the package README.
- `dos-dosbox-pure-ipx` — setup-specific feature or no stand-alone upstream fix; see the package README.
