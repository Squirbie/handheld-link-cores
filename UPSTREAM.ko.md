<p align="center"><a href="UPSTREAM.md"><img src="docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="UPSTREAM.ko.md"><img src="docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# 원본에 보낼 것

원본에 들어가면 모두에게 좋은 버그 고침과, 바로 보낼 PR 글(영어)을 모았어요.
2026-10-29 에 "보낸 것" 표의 고침을 원본 최신판에 맞춰 다시 떼어 빌드한 뒤 보냈어요. 보낸 것 · 아직인 것 모두 초안은 아래에 남겨요.
원본과 견준 날: 2026-10-29.

## 보낸 것

| PR | 무엇 |
|---|---|
| [libretro/beetle-wswan-libretro#105](https://github.com/libretro/beetle-wswan-libretro/pull/105) | LRAV 뒷부분 0 채우기 · V30MZ 멈춤 막기 |
| [libretro/beetle-ngp-libretro#121](https://github.com/libretro/beetle-ngp-libretro/pull/121) | iline · 플래시 블록 합치기 · 불러올 때 롬 · 플래시 |
| [finalburnneo/FBNeo#2845](https://github.com/finalburnneo/FBNeo/pull/2845) | Grainbow P3/P4 START 두 줄 |
| [libretro/gambatte-libretro#289](https://github.com/libretro/gambatte-libretro/pull/289) | 직렬 바이트 밀림 · 부트롬 중 리셋 |
| [libretro/mame2003-plus-libretro#2177](https://github.com/libretro/mame2003-plus-libretro/pull/2177) | H6280 · 배틀 레인저스 화면 칩(최신판 0/300 → 300/300) |
| [libretro/mame2003-plus-libretro#2178](https://github.com/libretro/mame2003-plus-libretro/pull/2178) | 읽기 전용 큰 뱅크 빼기 |
| [libretro/blueMSX-libretro#212](https://github.com/libretro/blueMSX-libretro/pull/212) | 끌 때 SRAM 저장 · WD2793 이름 |
| [libretro/gpsp#294](https://github.com/libretro/gpsp/pull/294) | 무선 어댑터 길이 · 보낸 기기 확인 |
| [beebono/DSperate#34](https://github.com/beebono/DSperate/pull/34) | IPC FIFO 박자(펌웨어 없을 때 흰 화면) |

준비만 하고 안 연 것: melonDS DS(기여 규칙이 PR 글을 사람이 직접 쓰라고 해요) — 가지 [`netpacket-wallclock-timeout`](https://github.com/Squirbie/melonds-ds/tree/netpacket-wallclock-timeout).

## 초안

| 꾸러미 | 원본 | 상태 | 준비한 PR |
|---|---|---|---|
| [`arcade-mame2003-plus`](cores/arcade-mame2003-plus/README.ko.md) | [libretro/mame2003-plus-libretro](https://github.com/libretro/mame2003-plus-libretro) | 우리 바탕 뒤로 원본 커밋 460개 · 우리 파일 5개가 원본에서 바뀜 | 5 |
| [`arcade-fbneo`](cores/arcade-fbneo/README.ko.md) | [libretro/FBNeo](https://github.com/libretro/FBNeo) | 우리 바탕 뒤로 원본 커밋 3389개 · 우리 파일은 안 바뀜 | 1 |
| [`ds-melonds-ds`](cores/ds-melonds-ds/README.ko.md) | [JesseTG/melonds-ds](https://github.com/JesseTG/melonds-ds) | 우리 바탕 뒤로 원본이 안 바뀜 | 1 |
| [`ds-dsperate`](cores/ds-dsperate/README.ko.md) | [beebono/DSperate](https://github.com/beebono/DSperate) | 우리 바탕 뒤로 원본 커밋 46개 · 우리 파일 1개가 원본에서 바뀜 | 1 |
| [`gb-gambatte-link`](cores/gb-gambatte-link/README.ko.md) | [libretro/gambatte-libretro](https://github.com/libretro/gambatte-libretro) | 우리 바탕 뒤로 원본 커밋 87개 · 우리 파일 5개가 원본에서 바뀜 | 1 |
| [`gba-gpsp-rfu`](cores/gba-gpsp-rfu/README.ko.md) | [libretro/gpsp](https://github.com/libretro/gpsp) | 우리 바탕 뒤로 원본 커밋 76개 · 우리 파일 2개가 원본에서 바뀜 | 1 |
| [`wswan-mednafen-dual`](cores/wswan-mednafen-dual/README.ko.md) | [libretro/beetle-wswan-libretro](https://github.com/libretro/beetle-wswan-libretro) | 우리 바탕 뒤로 원본이 안 바뀜 | 1 |
| [`ngp-mednafen-dual`](cores/ngp-mednafen-dual/README.ko.md) | [libretro/beetle-ngp-libretro](https://github.com/libretro/beetle-ngp-libretro) | 우리 바탕 뒤로 원본 커밋 4개 · 우리 파일은 안 바뀜 | 1 |
| [`msx-bluemsx`](cores/msx-bluemsx/README.ko.md) | [libretro/blueMSX-libretro](https://github.com/libretro/blueMSX-libretro) | 우리 바탕 뒤로 원본 커밋 101개 · 우리 파일 32개가 원본에서 바뀜 | 1 |

메모: MAME 2003-Plus 표시 비트 고침(우리 패치 0002, 2026-10-21)은 원본에 2026-10-24 [#2131](https://github.com/libretro/mame2003-plus-libretro/pull/2131)로 같은 고침이 들어갔고, 같은 달 원본이 타이머 상태도 담았어요([#2133](https://github.com/libretro/mame2003-plus-libretro/pull/2133)). 우리 큰 패치 0001 은 #2133 과 겹쳐 보내지 않고, 아래 MAME 작은 고침 다섯은 원본에 아직 없어요.

## 오락실 — `arcade-mame2003-plus`

원본: https://github.com/libretro/mame2003-plus-libretro · 우리 바탕 뒤로 원본 커밋 460개 · 우리 파일 5개가 원본에서 바뀜

- **H6280: register CPU state; battlera/actfancr: save HuC6270 VDC and driver state (netplay, rewind)** (패치 ['0003']) — H6280 CPU 코어는 상태 등록이 0이고, `battlera` 보드의 화면 칩(HuC6270)도 등록이 없어 같이하기 손님 화면이 깨져요(0/300 → 300/300). 작고 한 군데에 모인 고침이고 m6809_init 과 같은 방식이라 보내기 쉬워요. 2026-10-29 확인: h6280.c · battlera.c · battlera_vidhrdw.c 에 기준(2025-01-12) 이후 커밋이 없어 원본에 아직 없어요. 다만 원본이 같은 달에 타이머 상태를 바꿨으니(#2133) 최신 master 에서 다시 시험한 뒤 보내야 해요.
- **mame-memory: leave read-only banks of 1 MiB or more out of the save state** (패치 ['0004']) — 쓰기 지도에 한 번도 안 나오는 1MB 이상 뱅크(= 롬)를 상태에서 빼서 상태가 20~53MB 급에서 1.6~3.2MB 급이 돼요. 12줄. 2026-10-29 확인: mame-memory.c 의 register_banks() 에 건너뛰기가 없어요(마지막 커밋은 2026-10-25 NEC V25 · 2025-05 'Tidy'). 단점: 롬 뱅크를 쓰기 지도 없이 직접 바꾸는 드라이버가 있으면 그 바이트가 상태에서 빠져요 — 우리 시험에서는 못 봤지만 관리자의 의견이 필요해요.
- **Atari GT: save TMS32031, CAGE and sprite-engine state; atarigen: register UINT8 variables as UINT8** (패치 ['0005', '0006']) — Atari GT 계열(TMS32031 · CAGE · atarirle · atarigt)의 상태 등록 누락과 atarigen.c 의 UINT8 5개를 INT32 로 등록한 실수(옆 메모리 3바이트씩 덮어씀)가 분명한 버그예요. 되감기 때 소리 DSP 가 죽는 것도 고쳐요. 2026-10-29 확인: tms32031.c · cage_sndhrdw.c · atarigt*.c · atarigen.c 에 기준 이후 커밋 없음(atarirle_vidhrdw.c 는 난수 · 피 색 커밋만). 다만 원본의 새 타이머 상태(#2133)와 맞춰 다시 써야 하고, 롬이 없어 못 돌린 드라이버(`tmek` 등)가 있어요. UINT8 등록 실수만 따로 떼어 먼저 보낼 수도 있어요.
- **Atari: rebuild slapstic ROM copy, MO display-list cache and scroll after a state load; save Atari System 1 timers and pens** (패치 ['0007']) — 슬랩스틱 롬 사본 · 스프라이트 표시 목록 캐시 · 배경 스크롤을 불러온 뒤 다시 만들고 System 1 값을 등록해요(`gauntlet` 0 → 300). 에뮬 동작은 안 바꾸는 등록 · postload 만이라 위험이 작아요. 2026-10-29 확인: atarigen.c · atarimo_vidhrdw.c · gauntlet*.c · atarisy1*.c · slapstic.c 에 기준 이후 커밋이 없어요. 최신 master 에서 재시험 필요.
- **Vs. System: save MMC3 mapper state and protection counters, restore banking after a state load** (패치 ['0008']) — Vs. System MMC3 매퍼 값 · 숨은 정적 변수 · 보호 카운터 셋 등록과 불러온 뒤 뱅크 복원(보호 카운터 게임 0 → 300). 파일 하나. 2026-10-29 확인: vsnes_machine.c 에 기준 이후 커밋 없음. 최신 master 에서 재시험 필요.

## 오락실 — `arcade-fbneo`

원본: https://github.com/libretro/FBNeo · 우리 바탕 뒤로 원본 커밋 3389개 · 우리 파일은 안 바뀜

- **d_legionna: map Grainbow P3/P4 Start to DrvJoy3 bits 8/9 (they aliased P2 Up/Down)** (패치 ['patches/patch_fbneo.py', 'patches/patch_grainbow.py']) — 분명한 버그 고침은 입력표예요: GrainbowInputList 의 P3 Start / P4 Start 가 P2 Up / Down 과 같은 DrvJoy1 비트(8 · 9)라 2P 위/아래가 안 먹어요. 두 줄 고침(→ DrvJoy3 + 8 / + 9). 2026-10-29 원본 master(finalburnneo/FBNeo, d_legionna.cpp 의 마지막 변경은 2026-10-02)에 아직 그대로예요. 근거: 서비스 메뉴 입력 시험 화면(원래 P3 START 가 P-2 UP 칸을 켬 → 고친 뒤 ST3 칸) · 40장 입력 시험 · MAME 시스템 포트 0x10074c 의 START3/4 = 0x0100/0x0200 = DrvJoy3 비트 8 · 9 · 다른 9게임 되돌림 시험. 주의: 우리 검증은 미리 빌드된 코어의 입력표 포인터 2바이트를 바꾼 것이라 소스 빌드로 한 번 확인한 뒤 보내야 해요. 보내는 곳은 finalburnneo/FBNeo(드라이버가 있는 곳)이에요. 보내지는 않았어요.

## 닌텐도 DS — `ds-melonds-ds`

원본: https://github.com/JesseTG/melonds-ds · 우리 바탕 뒤로 원본이 안 바뀜

- **libretro netpacket MP: use a wall-clock reply timeout and stop waiting once every client has answered (even with a blank reply)** (패치 ['patches/0001-rom-file-mapping.patch', 'patches/0002-netplay-wallclock-timeout-and-blank-replies.patch', 'patches/0003-l2-popup.patch', 'patches/0004-lid-close-hotkey-off.patch', 'patches/0005-drastic-style-controls-and-pip.patch', 'patches/0006-ui-v2-auto-popup-badges-pip-quality-mp-stats.patch']) — 넷패킷 같이하기의 분명한 버그 두 가지(패치 0002 한 장, 57줄 추가 · 7줄 삭제): (1) 답 기다림을 std::clock(프로세스 CPU 시간, 스레드 합산)으로 재서 실제로는 25ms 보다 짧게 끝남 → 느린 기기 둘에서 방장이 답을 일찍 포기해 게임이 연결을 끊음, (2) '준비 안 됨' 빈 답(AID 0)을 답한 것으로 세지 않아 방장이 시간 초과까지 기다림(원본 melonDS 는 모두 답하면 빈 답이어도 끝냄). 두 기기 마리오 카트 DS 경주(약 22장, 시간 초과 0)로 확인. 보내기 전에 최신 main 에 이미 고쳐졌는지 확인·재시험이 필요함(이번 정리에서는 웹을 원본 주소·커밋 확인에만 써서 main 과 비교하지 않았음). 나머지(롬 파일 매핑 = glibc 가정, L2 팝업·작은 화면·버튼 바꾸기·덮개 끄기·진단 기록)는 우리 기기에 맞춘 것이라 보내지 않음. 멤버 초기화(ScreenLayoutData/JoypadState)는 실제로 문제가 되는 길인지 확인 못 해 제외.

## 닌텐도 DS — `ds-dsperate`

원본: https://github.com/beebono/DSperate · 우리 바탕 뒤로 원본 커밋 46개 · 우리 파일 1개가 원본에서 바뀜

- **Deliver ARM9 IPC FIFO words to the ARM7 at their send time (fixes boot-time white screens, e.g. with a generated firmware)** (패치 ['patches/dsperate-v3.0.3-hbipc-full.patch']) — 가장 분명한 것은 hbipc(ARM9 가 IPC FIFO 에 쓴 말을 ARM7 이 최대 한 조각(2048 사이클) 일찍 보던 박자 문제): 순정 v3.0.3 에서도 재현되고(우리 포크 48조건 시험에서 흰 화면 8곳 → 0), 한국판 피크로스 DS 가 펌웨어 덤프 없이 켜질 때 흰 화면이던 원인. 전체 패치 안에서 io.cpp/io.h/scheduler.cpp 의 ipc9_pending·ipc_deliver 부분만 따로 뽑아 main 에 맞춰야 함. 따로 보낼 수 있는 작은 후보: hbvc(VCOUNT 쓰기 받기 — 다운로드 플레이 대전 게임 시간이 1/3 이하로 흐르던 것), lanfix(LAN 답 기다림 25ms·묵은 패킷 창 64ms·ENet throttle 무작위 버림), hbguest2(받기 끝난 뒤 손님 ENet 끊김), hbfam 의 fsync 저장. 팝업·작은 창·그룹·자동 화면·스틱 창은 우리 기기 취향이라 보내지 않음. 이번 정리에서는 웹을 원본 주소·커밋 확인에만 써서 최신 main 과 비교하지 않았으니, 보내기 전에 이미 고쳐졌는지 확인이 필요함.

## 게임보이 · 컬러 — `gb-gambatte-link`

원본: https://github.com/libretro/gambatte-libretro · 우리 바탕 뒤로 원본 커밋 87개 · 우리 파일 5개가 원본에서 바뀜

- **Fix partial serial shift under HAVE_NETWORK and restore ROM bank 0 before re-initialising on reset** (패치 ['patches/0001-netpacket-link-cable-with-timing-v4bw.patch', 'patches/0002-gbc-infrared-over-netplay-v5ir.patch', 'patches/0003-reply-00-not-ff-to-unheard-byte-v5irh.patch', 'patches/0004-hold-second-byte-to-next-frame-v5irh2.patch', 'patches/0005-infrared-meet-before-led-and-pulse-tail-v5irh3.patch']) — 패치 안에서 떼어 낼 수 있는 원본 버그가 둘 있어요: (1) HAVE_NETWORK 쪽 Memory::updateSerial 이 바이트가 오가는 도중 SB/SC/IF 를 읽으면 비트를 맨 위부터 또 밀어 넣어 값이 돌아감(0x20 → 0x08), (2) 부트롬이 매핑된 동안 GB::reset() 하면 부트롬이 카트리지 백업이 되어 흰 화면. 둘 다 몇 줄이고 전송 방식과 상관없으며, 웹으로 확인한 원본 master 에도 두 곳이 그대로예요(master 는 reset 이 full_init(false) 로 바뀌어 다시 맞춰야 해요). 넷패킷 전송 계층 자체는 우리 기기용 큰 기능이라 후보가 아니에요.

## GBA — `gba-gpsp-rfu`

원본: https://github.com/libretro/gpsp · 우리 바탕 뒤로 원본 커밋 76개 · 우리 파일 2개가 원본에서 바뀜

- **RFU: survive netplay latency and bursts (ring queues, 1.2 s no-news time-out), bound client packet length, drain queued data before DISCONNECT, accept only the current peer** (패치 ['patches/0001-arm64-linux-cache-sync.patch', 'patches/0002-rfu-wifi-netplay-robustness-v2.patch', 'patches/0003-rfu-less-waiting-v3.patch']) — 원본 master 의 rfu.c 도 pkts[4] 줄과 같은 시간 제한이라 같은 문제가 남아 있어요(웹으로 확인). 일부는 분명한 버그예요: 손님 패킷 길이 검사 없이 16바이트 칸에 복사(범위 밖 쓰기), 4칸 줄이 몰려 온 패킷을 버림, 끊김이 읽지 않은 패킷을 지움, 현재 상대가 아닌 기기 패킷 수용. 다만 v2 · v3 에는 우리 와이파이에 맞춘 상수와 ACK 넷째 칸 확장이 섞여 있어서 보낼 때는 견고성 고침만 따로 떼어 내야 해요.

## 원더스완 — `wswan-mednafen-dual`

원본: https://github.com/libretro/beetle-wswan-libretro · 우리 바탕 뒤로 원본이 안 바뀜

- **Fix non-deterministic savestates (unused LRAV tail) and guard the V30MZ loop against zero-cycle instructions** (패치 ['patches/0001-WonderSwan-UART-accurate-status-timing-and-level-IRQ.patch', 'patches/0002-Libretro-run-a-frame-line-by-line-hb_ws_-API-for-a-t.patch', 'patches/0003-Libretro-zero-the-unused-tail-of-the-60Hz-audio-cach.patch', 'patches/0004-Libretro-add-Beetle-WonderSwan-Dual-two-WonderSwans-.patch', 'patches/0005-Libretro-dual-trace-heartbeat-every-60-shown-frames-.patch', 'patches/0006-screen-file-runtime-selection.patch', 'patches/0007-guest-own-save.patch', 'patches/0008-netplay-version-length.patch', 'patches/0009-ownsave-harden.patch', 'patches/0010-rotate-portrait.patch', 'patches/0013-ws16-from-0010.patch', 'patches/0014-ws17-serial-overwrite-cpu-guard.patch', 'patches/0015-ws18-shanghai-mode.patch', 'patches/0016-ws19-pair-game.patch']) — 두 대 앞단 · 직렬 링크 · 각자 세이브는 우리 구성 전용이라 보내지 않아요. 하지만 순정에도 있는 작은 버그 둘은 분명해요: (1) 저장 상태의 60Hz 소리 캐시(LRAV) 뒷부분이 비워지지 않아 같은 장면도 저장 바이트가 달라져요(넷플레이 CRC 어긋남) — 원본 master 에 memset 이 없는 것을 2026-10-29 에 확인(패치 0003). (2) V30MZ 반복이 사이클이 안 줄어드는 명령에서 끝나지 않을 수 있어요 — master 에 같은 보호가 없는 것을 확인(패치 0014 의 v30mz.c 부분). 둘 다 몇 줄이라 따로 보낼 수 있어요.

## 네오지오 포켓 — `ngp-mednafen-dual`

원본: https://github.com/libretro/beetle-ngp-libretro · 우리 바탕 뒤로 원본 커밋 4개 · 우리 파일은 안 바뀜

- **Savestate fixes for rollback/run-ahead: save the Z80 IRQ line, fix flash block merging, restore ROM/flash on load** (패치 ['patches/0001-NGP-save-the-Z80-IRQ-line-in-savestates.patch', 'patches/0002-NGP-Dual-link-cable-for-two-consoles-in-one-core.patch', 'patches/0003-NGP-deterministic-flash-state-rollback-netplay.patch', 'patches/0004-NGP-Dual-refuse-states-made-with-other-ROMs.patch', 'patches/0005-NGP-Dual-option-descriptions-use-instead-of.patch', 'patches/0006-NGP-Dual-BIOS-default-serial-handlers-at-COMINIT.patch', 'patches/0007-NGP-Dual-1.1-os4-guest-own-save-kind-3-and-NGP-partner-pairs.patch', 'patches/0008-NGP-Dual-1.2-os5-INTTX0-when-the-transmit-buffer-emp.patch', 'patches/0009-NGP-Dual-1.2-os5-COMRECIVESTART-asserts-RTS.patch', 'patches/0010-NGP-Dual-1.2-os5-COMCREATEDATA-returns-FF-when-the-s.patch', 'patches/0011-os5rtc-p2-rtc-skew.patch']) — 두 대 앞단 · 링크 · 각자 세이브는 보내지 않아요. 하지만 순정 코어(한 대)에도 있는 상태 저장 버그가 분명해요: Z80 IRQ 선(iline)이 상태에 없고(패치 0001), flash_optimise_blocks 의 'FIXME std::max' 때문에 지운 32KB 칸이 줄어들며(패치 0003) — 이 둘은 원본 master 에 그대로인 것을 2026-10-29 에 확인했어요 — 플래시 없는 상태를 불러올 때 롬 · 블록 목록이 안 돌아와요(패치 0003, master 확인은 안 함). 되감기 · 런어헤드 · 넷플레이에서 어긋남으로 드러나요. 패치 0003 은 우리 hb_link.c 부분이 섞여 있어 flash.c · system.c · rom.c 만 추려 보내야 해요.

## MSX — `msx-bluemsx`

원본: https://github.com/libretro/blueMSX-libretro · 우리 바탕 뒤로 원본 커밋 101개 · 우리 파일 32개가 원본에서 바뀜

- **Save battery-backed SRAM/flash on unload, fix the WD2793 state tag typo, and make savestates complete and byte-stable** (패치 ['patches/01-sramflush-disk.patch', 'patches/02-flashsave.patch', 'patches/03-hbnp1-netplay-sync.patch']) — 분명한 버그 고침이 여럿이에요. (A) retro_unload_game 이 보드를 해체하지 않아 배터리 SRAM · 플래시가 저장되지 않아요 — 원본 572c918 과 master 둘 다 boardInfo.destroy() 호출이 없는 것을 2026-10-29 에 확인. (B) WD2793 이 'diskTracks[0]' 로 저장하고 'diskTracks0' 으로 읽어요 — 두 판 모두 그대로인 것을 확인. (C) 타이머 · 보드 · 소리칩 상태가 상태 저장에서 빠지거나 쓰레기가 섞여 넷플레이/되감기가 어긋나요. 패치 03 이 158개 파일이라 한 번에 보내면 받아들이기 어려우니 A · B · C 로 나눠 보내는 게 좋아요. 패치 01 의 get_eject_state 항상 '열림'은 레트로아크 1.22 우회라 빼야 하고, 패치 03 의 HbZeroNew.cpp(전역 operator new 를 0 으로 채움)는 우리 쪽 우회라 생성자에서 칸을 비우는 식으로 바꿔 보내야 해요.

## 보내지 않는 것

- `arcade-mahjong-pad` — 프런트엔드 쪽 패드 → 키보드 대체 문제라 우리 기기 단추에 맞춘 외부 래퍼로 풀었고, 원본 코어에 고칠 곳이 없어요. 2026-10-29 소스 확인: FBNeo 레트로아크 입력은 마작 키를 키보드 키로만 묶고 1P 에게만 줘요(retro_input.cpp, 주석이 finalburnneo/FBNeo#2117 을 가리킴). 원본에 같은 기능은 없지만 보낼 패치도 없어요.
- `gba-mgba-dual` — 원본에 보낼 만한 독립 버그 고침이 아니에요. 핵심(0001 ~ 0005)은 tangobattle/mgba 의 협력식 lockstep 코드이고, 나머지 고침은 그 코드와 새 libretro 앞단(mgba_dual) 위에서만 뜻이 있어요. 각자 세이브 · 짝 게임 · 싱글팩은 KNULLI 도우미 스크립트에 기대는 우리 기기용 기능이고, 상태 형식의 예약 칸(VRAM 경합 마스크 등)을 써서 순정 mGBA 와 상태가 호환되지 않아요. 굳이 제안한다면 tangobattle/mgba 쪽에 링크 박자(SD 선 · 시작 비트 0) 고침 정도예요.
- `gg-genesisplusgx-dual` — 한 기기 안에 코어 두 벌(ggA_/ggB_)과 케이블 모델을 얹는 구성 전용 기능이라 상류 코어(한 대 에뮬)에 넣을 단독 버그 고침이 아니에요. 확장 포트 통신은 두 인스턴스를 잇는 프런트엔드가 있어야 쓸 수 있어 받아 줄 가능성이 낮고, 옵션 글 ';' → ',' 수정(패치 0003)은 우리 옵션 이름에만 해당돼요.
- `nes-fceumm-mapper14` — 63643ba 의 옛 구현(src/mappers/mapper014.c)에서는 분명한 결함(작업용 램 없음 · $6000~$7FFF 쓰기를 레지스터가 가로챔)이었지만, 원본이 그 뒤에 파일을 src/boards/14.c 로 옮기고 매퍼 14 를 asic_mmc3.h 기반 새 구현으로 다시 써서(2026-10-11 ac0d00a 확인) 이 패치는 더 걸리지 않아요. 새 구현에서도 같은 한글 롬이 검은 화면이면 그때 새 코드에 맞춰 작은 PR 이나 이슈로 보내면 돼요.
- `dos-dosbox-pure-ipx` — 기기에서 난 꺼짐의 원인 줄을 확정하지 못했고(순정은 맥/VM 34세션에서 재현 안 됨) 넷플레이를 시작하면 돌던 DOS 가 다시 켜지는 동작 변경이라, RG35XX + RetroArch 1.22.2 에 맞춘 우회에 가까워요. 함께 있던 NULL 읽기 막기(control == NULL)는 원본이 이미 넣었어요(개발 때 확인: 2026-02-05 77061c2).
