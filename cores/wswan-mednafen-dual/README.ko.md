<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# Beetle WonderSwan Dual — 기기 두 대로 즐기는 원더스완 통신 케이블

> 원더스완 두 대를 통신 케이블로 이어 코어 하나 안에서 돌려서, 케이블로 둘이 하는 게임을 레트로아크 넷플레이로 기기 두 대에서 같이 할 수 있게 해 주는 코어예요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/wswan-mednafen-dual-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| **코어 파일** | `mednafen_wswan_dual_libretro.so` — aarch64 리눅스용, 2,312,664 바이트 (git 에는 없고 릴리스 zip 안에 있어요) |
| **버전** | `1.9-os4 f01a6988+ownsave+rot+pr` (코어 이름 `Beetle WonderSwan Dual`, 안쪽 코어 `v0.9.35.1`) |
| **md5** | `53e2b57da54e3af050614309872d7a4e` |
| **원본** | [libretro/beetle-wswan-libretro](https://github.com/libretro/beetle-wswan-libretro) @ [`4b01295`](https://github.com/libretro/beetle-wswan-libretro/commit/4b01295838ea89e3f1355bbe4cb5cf98aa6108cd) ("minor wording nitpick (#104)", 2026-07-31) |
| **라이선스** | GPL-2.0 이상 (GPL-2.0-or-later) |
| **시험한 환경** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (확인한 환경은 이것뿐이에요) |

## 무엇을 하나

순정 Beetle WonderSwan 은 기계를 한 대만 흉내 내서, 케이블로 둘이 하는 게임을 같이 할 수 없었어요. 원피스 그랜드 배틀 스완 콜로세움 · 뿌요뿌요 통 · 쿠루파라! · 상해 포켓 · 명탐정 코난 같은 게임이에요. 이 코어는 **원더스완 두 대를 코어 하나 안에** 넣고 직렬 포트를 서로 이어서, 기기 두 대가 레트로아크 넷플레이로 같이 할 수 있게 해요. 방장 기기 화면은 1P 기계, 손님 기기 화면은 2P 기계를 보여 줘요.

- **어긋나지 않아요.** 상태 저장을 바이트 단위로 일정하게 만들어서, 레트로아크 넷플레이(되감기 포함)에서도 두 기기가 같은 장면을 유지해요.
- **각자 자기 세이브.** 손님은 자기 세이브로 하고, 끝나면 그 세이브를 돌려받아요.
- **세로로 세워 하는 게임**은 세워서 보여 주고, 통신 박자에 까다로운 게임은 게임별로 박자를 맞춰요.
- **짝 게임.** 서로 다른 카트 두 개가 짝으로 통신하는 게임이 있어요. 2P 기계에 다른 롬을 꽂을 수 있어요(명탐정 코난 08 ↔ 06).
- **기기 두 대로 확인한 것:** 원피스 그랜드 배틀 같이하기(진짜 세이브 그대로), 상해 포켓 대전 시작, 코난 08 ↔ 06 전작 데이터 보내기 화면.

### 알아 두면 좋은 것

- 두 기기 모두 같은 코어 파일 · 같은 롬이어야 해요. 짝 게임은 정해진 짝 롬끼리만 돼요.
- `wswan_dual_link` 가 `on` 이면 혼자 해도 2P 기계가 돌아 CPU 를 더 써요. RG35XX Pro 에서 골든 액스로 재 보니 CPU 81% @1220MHz 였고, 순정은 71% @785MHz 였어요. 혼자 할 때는 `off` 로 두면 순정 속도예요.
- 알려진 한계: 센노 밀레니엄은 두 쪽이 제목에서 같은 장에 START 를 누르면 게임이 통신 에러를 내요(코어 문제 아님, 1장만 달라도 시작해요). 같은 롬끼리만 연결돼요(한글판 ↔ 일본판 불가). 세로 게임은 켤 때만 정해지고 SELECT 로 못 돌려요.

## 무엇을 고쳤나

1. **새 앞단 `dual/libretro_dual.c`.** 안쪽 코어(Beetle WonderSwan)의 바깥 이름 약 300개에 `wsA_` / `wsB_` 를 붙여 두 번 컴파일하고 한 `.so` 로 묶어요(`dual/build_dual.sh`). 두 기계가 **256 사이클(한 줄)씩 번갈아** 돌고, 줄마다 끝난 직렬 바이트를 상대 수신으로 넘겨요. 패드 포트 0 = 1P 기계(방장), 포트 1 = 2P 기계(손님)예요. 밖으로는 `retro_*` 25개만 내보내요.
2. **직렬 포트(`comm.c`)를 실제 기계처럼 다시 씀(패치 0001).** 0xB3 상태에 받음/넘침 비트를 늘 보여 줘요. 한 바이트는 10비트 시간이에요(9600bps 3200사이클 · 38400bps 800사이클). 송신 IRQ 도 수신처럼 레벨 방식이고, 보내는 중인 바이트까지 상태에 저장해요.
3. **줄 단위 실행 API `hb_ws_*`(0002).** `retro_run` 을 쪼갠 함수들이에요. 한 대짜리로 쓰면 순정과 똑같이 돌아요.
4. **상태를 일정하게(0003).** 60Hz 소리 캐시(`LRAV`)의 안 쓰는 뒷부분을 0 으로 비워서, 같은 장면이면 저장 바이트도 같아요. 전에는 저장할 때마다 달라서 넷플레이 CRC 가 어긋났어요.
5. **상태 모양.** 머리 64바이트 + 두 기계의 상태(게임마다 크기가 정해진 고정 크기)예요. 머리의 판 칸 비트로 세로(0x100) · 박자 half(0x200) · 짝 게임(0x400)을 표시해서, 설정이 다른 상태는 서로 거절해요.
6. **화면 파일(0006).** `/tmp/hb_dual_screen` 으로 1P/2P 화면 · 소리를 게임 도중에 골라요.
7. **각자 자기 세이브(0007, 0009).** 손님이 자기 세이브로 하고 끝나면 돌려받아요. 0009 가 원자적 쓰기 · 거래 폴더 · 손님이 2P 가 맞는지 확인하는 스레드로 보호를 마무리해요. 0008 은 넷플레이 판 글자가 끝 글자 포함 32바이트라서 빌드 때 길이를 검사해요.
8. **세로 게임(0010).** 세로 게임을 세워 보이고 단추를 바꿔 넘겨요.
9. **통신 박자(0013).** `wswan_dual_link_phase` 옵션(1.5)과, 손님 세이브를 받을 때 2P 60Hz 셈을 1P 와 맞추는 고침(1.6)이에요.
10. **직렬 덮어쓰기와 CPU 멈춤 막기(0014, 1.7).** 수신 버퍼가 찬 채 새 바이트가 오면 새 바이트가 덮어써요(쿠루파라!). 사이클이 안 줄어드는 명령이 이어지면 1사이클로 셈해서 무한 반복을 막아요.
11. **상해 포켓 모드(0015, 1.8).** 롬 머리가 상해 포켓이고 두 대일 때만 직렬 바이트를 정확한 사이클(800/3200)에 넘기고 인터럽트 우선순위 등을 맞춰요. 그 밖의 게임은 1.7 과 상태까지 같아요.
12. **짝 게임(0016, 1.9).** 2P 기계에 다른 롬을 올려요(요청 종류 HBQ4, 경로는 `/tmp/hb_dual_p2rom`). 짝이 아니면 1.8 과 상태 바이트까지 같아요.

이름이나 주석에 들어 있는 `hb_` · `hanbang` 은 우리가 고친 곳 표시일 뿐이에요. 이름을 바꾸지는 않았어요.

## 코어 옵션

첫 값이 기본이에요.

| 옵션 | 값 | 뜻 |
|---|---|---|
| `wswan_dual_screen` | `1P` · `2P` | 보이는 화면 · 소리 (방장/혼자 = 1P, 손님 = 2P) |
| `wswan_dual_link` | `on` · `off` | `off` 면 2P 기계를 안 돌려 한 대짜리 속도예요. 게임을 켤 때만 읽어요. |
| `wswan_dual_link_phase` | `same` · `half` | 2P 기계를 반 장 늦게 돌릴지 정해요. 뿌요뿌요 통 · 파이어 프로레슬링만 `half` 예요. 두 기기 값이 같아야 해요. |
| `wswan_rotate_display` | `manual` · `landscape` · `portrait` | 세로 게임 세우기예요(원래 코어와 같은 키). SELECT 로는 안 돌아가요. |
| `wswan_dual_pair_hold` | `off` · `1P` · `2P` | 짝 게임에서만: 그 기계를 켤 때 2초 동안 단추를 모두 누른 채로 둬요(코난 06 의 보내기 화면). |

**`/tmp` 파일 약속** (없으면 평소 동작이에요):

- `/tmp/hb_dual_screen` — `1P` 또는 `2P`. 옵션보다 우선해요.
- `/tmp/hb_ownsave/` — 각자 세이브 거래 폴더예요.
- `/tmp/hb_dual_p2rom` — 짝 게임에서 2P 롬 경로 한 줄이에요.

**세이브.** 1P 는 보통 `.srm`, 2P 는 방장 기기의 `<롬 이름>.p2.sav` 예요. 손님 기기는 1P/2P 세이브를 읽지도 쓰지도 않고(각자 세이브 모드), 끝날 때 2P 진행을 자기 세이브로 돌려받아요.

## KNULLI 에 넣기

두 기기에 **같은 `.so`** 를 넣어야 해요(판 글자가 다르면 레트로아크가 경고하고 어긋날 수 있어요). [최신 릴리스](https://github.com/Squirbie/handheld-link-cores/releases/latest)에서 `wswan-mednafen-dual-linux-aarch64.zip` 을 받아 풀고, 게임을 끈 상태에서 넣어요.

**시작하기 전에**

- 미리 빌드한 `.so` 는 **aarch64 리눅스**용이에요. glibc 2.34 이하 기호만 쓰고 `libc.so.6` 만 필요해요. 다른 CPU · OS 는 패치로 다시 빌드해야 해요. `dual/build_dual.sh` 에 맥 모드가 있고 맥 arm64 에서 시험 빌드했어요(시험용, 기기에 넣지 않았어요).
- 확인한 환경은 **KNULLI + RetroArch 1.22.2** 뿐이에요.
- 각자 세이브 · 짝 게임 · 화면 파일 기능은 **KNULLI 훅이 `/tmp` 에 파일을 써 줘야** 켜져요. 파일이 없으면 평소처럼 방장 기기의 1P `.srm` + `.p2.sav` 로 돌아요. 손님 판정은 실행 명령의 `--connect` 와 레트로아크 기록에서 2 플레이어로 들어왔다는 줄을 읽는 방식이라 KNULLI 의 실행기 모양에 기대요.
- 푼 파일을 확인하세요: md5 는 위 표와 같고, sha256 은 `8d0af05a909dc722e5920255c76d96bab62dd1e05f68f4ebf34c794346cc07ca` 예요.

**순서**

1. 코어 파일을 SD 쪽 `/userdata/system/hanbang_cores/` (미리 빌드한 파일이 쓰는 기본 자리)에 두고, 레트로아크가 찾는 자리에는 바로가기를 둬요. KNULLI 의 `/usr` 은 덧칠(overlay)이라 `knulli-save-overlay` 로 저장해야 재부팅 뒤에도 남아요. 순정 `mednafen_wswan_libretro.so` 는 건드리지 않는 새 이름이에요.
   ```sh
   mkdir -p /userdata/system/hanbang_cores
   cp mednafen_wswan_dual_libretro.so /userdata/system/hanbang_cores/ && chmod 755 /userdata/system/hanbang_cores/mednafen_wswan_dual_libretro.so
   mount -o remount,rw /
   ln -sfn /userdata/system/hanbang_cores/mednafen_wswan_dual_libretro.so /usr/lib/libretro/mednafen_wswan_dual_libretro.so
   knulli-save-overlay
   ```
2. **코어 정보 파일.** 없으면 실행기가 거절해요. 순정 정보 파일을 베껴 이름만 바꿔요.
   ```sh
   I=/usr/share/libretro/info
   sed -e 's/^display_name = .*/display_name = "Bandai - WonderSwan\/Color (Beetle WonderSwan Dual)"/' \
       -e 's/^corename = .*/corename = "Beetle WonderSwan Dual"/' $I/mednafen_wswan_libretro.info > $I/mednafen_wswan_dual_libretro.info
   knulli-save-overlay
   ```
3. **게임별 코어 지정.** `/userdata/system/knulli.conf` 에 (컬러 게임은 `wswanc`, 흑백은 `wswan`) 이렇게 적어요: `wswanc["<롬 파일 이름>.zip"].core=mednafen_wswan_dual`
4. **ES 에서 '넷플레이 게임 시작'이 보이게.** ES 기능 표(`es_features_*.cfg`)에 한 줄을 더해요: `<core name="mednafen_wswan_dual" features="netplay" />`
5. **게임 시작 훅.** 게임을 켤 때마다 훅이 그 게임의 코어 옵션 파일 `/userdata/system/configs/retroarch/config/Beetle WonderSwan Dual/<롬 이름>.opt` 를 써서, 방장/혼자 = `1P`, 손님 = `2P`, link `on` 으로 맞춰요. 훅은 [`knulli-scripts/nds_save_sync.sh`](../../knulli-scripts/) 의 19번 블록이에요.
   - `/userdata/system/scripts/nds_save_sync.sh` (미리 빌드한 파일이 쓰는 기본 자리)로 넣고, 그 폴더에는 이 파일 하나만 두세요. KNULLI 가 그 폴더의 모든 파일을 실행해요.
   - 같은 폴더의 도우미 스크립트는 `/userdata/system/claude/` (미리 빌드한 파일이 쓰는 기본 자리)에 넣어요: `hb_ownsave.py`(각자 세이브)와 `hb_joinask.py`('같이 / 혼자' 고르는 창)예요.
6. **화면 설정.** 순정 코어와 같은 셰이더 · 화면 위치를 쓰려면, 순정 코어의 레트로아크 설정 폴더(`config/<코어 이름>/`)에 있는 `wswanc.cfg` · `wswan.cfg` 같은 파일을 `config/Beetle WonderSwan Dual/` 로 복사해 두세요. 코어 이름이 다르면 설정을 못 읽어요.
7. **되돌리기.** `rm /usr/lib/libretro/mednafen_wswan_dual_libretro.so && knulli-save-overlay` 를 실행하고, `knulli.conf` 의 `core=mednafen_wswan_dual` 줄을 빼요. 2P 세이브 `.p2.sav` 는 순정 코어가 안 읽으니 그냥 두면 돼요.

## 소스에서 빌드

```sh
git clone https://github.com/libretro/beetle-wswan-libretro
cd beetle-wswan-libretro
git checkout 4b01295838ea89e3f1355bbe4cb5cf98aa6108cd
PATCHES=/path/to/handheld-link-cores/cores/wswan-mednafen-dual/patches
for p in "$PATCHES"/*.patch; do patch -p1 < "$p" || break; done
```

아래 빌드는 미리 빌드한 파일에 쓴 Debian 12 (aarch64, gcc 12.2.0) 기준 순서예요. 안쪽 코어를 한 번 보통으로 컴파일해 **이름 목록**을 뽑고, 그 목록으로 `wsA_` / `wsB_` 두 벌을 다시 컴파일해 묶어요.

```sh
B=$PWD/b; mkdir -p $B
# 코어가 알리는 판 글자. 두 기기가 같아야 하고, "1.9-os4" 와 합쳐 31자 이내여야 해요(빌드 때 검사)
printf '#define GIT_VERSION " f01a6988+ownsave+rot+pr"\n' > $B/ver.h
cat > $B/flags <<EOF
-O2 -DNDEBUG -fPIC -mcpu=cortex-a53 -I. -Imednafen -Imednafen/include -Ilibretro-common/include -DSIZEOF_DOUBLE=8
-DMEDNAFEN_VERSION_NUMERIC=931 -DMPC_FIXED_POINT -DSTDC_HEADERS -D__STDC_LIMIT_MACROS -D__LIBRETRO__ -D_LOW_ACCURACY_
-DINLINE=inline -DWANT_16BPP -DWANT_STEREO_SOUND -DFRONTEND_SUPPORTS_RGB565 -include $B/ver.h -w
EOF
SRCS="mednafen/wswan/sound.c mednafen/wswan/interrupt.c mednafen/wswan/comm.c mednafen/wswan/rtc.c mednafen/wswan/tcache.c
mednafen/wswan/gfx.c mednafen/wswan/wswan-memory.c mednafen/wswan/v30mz.c mednafen/wswan/eeprom.c mednafen/sound/Blip_Buffer.c
mednafen/mempatcher.c mednafen/state.c mednafen/settings.c libretro.c libretro-common/compat/compat_strl.c libretro-common/compat/compat_snprintf.c"
for s in $SRCS; do gcc @$B/flags -c -o $B/inner_$(echo $s | tr / _).o $s; done   # 1) 이름 목록용
CC=gcc NM=nm bash dual/build_dual.sh linux $B "$SRCS"                              # 2) 두 벌 + 묶기
strip --strip-unneeded $B/mednafen_wswan_dual_libretro.so
```

- `-mcpu=cortex-a53` 은 RG35XX 계열(H700) 맞춤이에요. 다른 CPU 면 바꾸세요.
- 같은 도구(Debian 12 aarch64, gcc 12.2.0-14+deb12u1)로 다시 빌드하면 개발 때 1.7 · 1.8 소스가 바이트까지 같은 코어로 나왔어요. 도구가 다르면 md5 는 달라도 동작은 같아요.
- 맥 arm64 시험 빌드는 `dual/build_dual.sh mac …` 로 해요(시험용이에요).

## 패치

`patches/` 안 파일을 **이름 순서대로** 한 번씩 걸어요.

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `0001-WonderSwan-UART-accurate-status-timing-and-level-IRQ.patch` | 직렬 포트(`comm.c`)를 실제 기계처럼 다시 쓰고, 앞단이 쓸 통신 입구를 더해요. |
| 2 | `0002-Libretro-run-a-frame-line-by-line-hb_ws_-API-for-a-t.patch` | `retro_run` 을 쪼갠 줄 단위 실행 API(`hb_ws_*`)를 더해요. 두 대 앞단용이에요. |
| 3 | `0003-Libretro-zero-the-unused-tail-of-the-60Hz-audio-cach.patch` | 상태 저장에서 60Hz 소리 캐시의 안 쓰는 뒷부분을 0 으로 비워, 같은 장면이면 저장 바이트도 같게 해요. |
| 4 | `0004-Libretro-add-Beetle-WonderSwan-Dual-two-WonderSwans-.patch` | 두 대 앞단 `dual/libretro_dual.c` 를 더해요(1.0). |
| 5 | `0005-Libretro-dual-trace-heartbeat-every-60-shown-frames-.patch` | 시험용 기록: 보이는 장 60개마다 심장박동 줄을 남겨요(`WSWAN_DUAL_TRACE` 일 때만). |
| 6 | `0006-screen-file-runtime-selection.patch` | `/tmp/hb_dual_screen` 으로 1P/2P 화면 · 소리를 실행 중에 골라요. |
| 7 | `0007-guest-own-save.patch` | 각자 자기 세이브: 손님이 자기 세이브로 해요(1.1-ownsave). |
| 8 | `0008-netplay-version-length.patch` | 넷플레이 판 글자는 끝 글자 포함 32바이트예요. 빌드 때 길이를 검사해요. |
| 9 | `0009-ownsave-harden.patch` | 세이브 보호 마무리: 원자적 쓰기 · 거래 폴더 · 손님이 2P 가 맞는지 확인하는 스레드. |
| 10 | `0010-rotate-portrait.patch` | 세로 게임을 세워 보이고 단추를 바꿔 넘겨요(1.3-os4). |
| 11 | `0013-ws16-from-0010.patch` | 통신 박자 옵션(1.5)과, 손님 세이브를 받을 때 2P 60Hz 셈을 1P 와 맞춤(1.6-os4). |
| 12 | `0014-ws17-serial-overwrite-cpu-guard.patch` | 직렬 덮어쓰기와 CPU 멈춤 막기, 쿠루파라!용이에요(1.7-os4). |
| 13 | `0015-ws18-shanghai-mode.patch` | 상해 포켓 모드(1.8-os4). |
| 14 | `0016-ws19-pair-game.patch` | 짝 게임, 명탐정 코난 08 ↔ 06(1.9-os4). |

- **0011 · 0012 가 빠진 까닭.** 0011 은 1.4(2P 장 끝을 줄 64 로)였는데 원피스를 깨뜨려서 되돌렸어요. 0012 는 1.5 단독판인데, 내용이 `0013-ws16-from-0010.patch`(0010 위에 바로 거는 누적 패치)에 이미 들어 있어요. 둘 다 최종 판에 안 쓰여서 넣지 않았어요.
- `0001` ~ `0005` 는 `git format-patch` 모양이라 `git am` 으로도 걸려요. `0015` · `0016` 은 `diff -ruN` 모양(`-p1`)이에요.
- 패치 속 주석 일부는 한국어예요. 쓴 그대로 두었어요.
- **확인한 것(2026-10-29, 맥에서).** 원본 `4b01295` 에 14개를 순서대로 걸면 어긋남(fuzz) 없이 모두 적용되고, 끝 소스의 `DUAL_VERSION` 이 `1.9-os4` 로 나와요. 0001 ~ 0005 는 건드리는 파일 14개의 git blob 지문이 우리 커밋과 같았어요. 개발 때 시험대 기록: 짝이 아닌 게임에서 1.9 는 1.8 과 상태 바이트까지 같고(3게임 × 설정 4가지 × 씨앗 2 = 24가지), 짝 게임 되감기 600장에서 불일치가 0 이었어요.
- 코어를 바꿀 때마다 기기에서 원피스 같이하기 한 판(손님 세이브 받기 → 그랜드 배틀 1P VS 2P)으로 되돌림이 없는지 확인했어요.

## 원본에 보내기

보낼 만한 고침이 있어요. 순정 한 대짜리 코어에도 있는 작고 서로 독립적인 버그 둘이에요.

1. **저장 바이트가 늘 같지 않은 것**(패치 0003). 60Hz 소리 캐시(`LRAV`)의 안 쓰는 뒷부분이 비워지지 않아 같은 장면도 저장 바이트가 달라지고, 넷플레이에서 CRC 어긋남으로 드러나요. 원본 master 에 `memset` 이 없는 것을 2026-10-29 에 확인했어요.
2. **V30MZ 반복이 끝나지 않을 수 있는 것**(패치 0014 의 `v30mz.c` 부분). 사이클이 안 줄어드는 명령에서 반복이 끝나지 않을 수 있어요. 원본 master 에 같은 보호가 없는 것도 확인했어요.

둘 다 몇 줄이라 따로 보낼 수 있어요. 제목 초안: "Fix non-deterministic savestates (unused LRAV tail) and guard the V30MZ loop against zero-cycle instructions". 영어 초안 글은 [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) 의 `upstream_pr_candidate` 에 있어요.

두 대 앞단 · 직렬 링크 · 각자 세이브는 이 구성 전용이라 보내지 않아요.

## 라이선스

- 원본 Beetle WonderSwan(Mednafen)은 **GPL-2.0 이상**이에요(`COPYING` = GPLv2, 파일 머리말은 "version 2 … or (at your option) any later version"). 라이선스 원문은 [`LICENSES/beetle-wswan-libretro_COPYING`](../../LICENSES/beetle-wswan-libretro_COPYING) 에 있어요. 이 폴더의 패치는 그 조건을 그대로 따르고, 새로 쓴 `dual/libretro_dual.c` 에도 같은 GPL 머리말을 달았어요.
- `dual/hb_ownsave.h` · `hb_storage.h` · `hb_romfile.h` 에는 별도 머리말이 없어요. 같은 코어에 합쳐져 배포되므로 코어와 같은 조건으로 공개해요(이 프로젝트에서 새로 쓴 파일이에요).
- 이 코어를 넣은 바이너리를 배포할 때는 **고친 소스(이 패치들)** 를 함께 공개해야 해요.
