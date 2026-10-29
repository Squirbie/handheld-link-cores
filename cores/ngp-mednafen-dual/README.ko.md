<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# Beetle NeoPop Dual — 기기 두 대로 즐기는 네오지오 포켓 통신 케이블

> 네오지오 포켓(컬러) 두 대를 통신 케이블로 이어 코어 하나 안에서 돌려서, 통신 대전을 레트로아크 넷플레이로 기기 두 대에서 같이 할 수 있게 해 주는 코어예요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/ngp-mednafen-dual-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| **코어 파일** | `mednafen_ngp_dual_libretro.so` — aarch64 리눅스용, 831,096 바이트 (git 에는 없고 릴리스 zip 안에 있어요) |
| **버전** | `1.2-os5 os5rtc` (코어 이름 `Beetle NeoPop Dual`, 안쪽 코어 `v1.29.0.0 os5rtc`) |
| **md5** | `91b8d251fbd72d776d1b2616b2a2b111` |
| **원본** | [libretro/beetle-ngp-libretro](https://github.com/libretro/beetle-ngp-libretro) @ [`139fe34`](https://github.com/libretro/beetle-ngp-libretro/commit/139fe34c8dfc5585d6ee1793a7902bca79d544de) ("tvos: properly set min supported version (#114)", 2024-10-21). KNULLI 순정 코어가 알리는 `Beetle NeoPop v1.29.0.0-139fe34` 와 같은 커밋이에요. |
| **라이선스** | GPL-2.0 이상 (GPL-2.0-or-later) |
| **시험한 환경** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (확인한 환경은 이것뿐이에요) |

## 무엇을 하나

순정 Beetle NeoPop 은 통신 케이블을 흉내 내지 않아서, KOF R-1 · R-2 · SvC 밀레니엄 · 카드 파이터즈 같은 통신 게임을 같이 할 수 없었어요. 이 코어는 **네오지오 포켓(컬러) 두 대를 코어 하나 안에** 넣고, 직렬 채널 0 과 바이오스의 통신 함수를 흉내 내서 서로 이어요. 그래서 기기 두 대가 레트로아크 넷플레이로 같이 할 수 있어요. 방장 기기 화면은 1P 기계, 손님 기기 화면은 2P 기계를 보여 줘요.

- **어긋나지 않아요.** 레트로아크 넷플레이(되감기)에서 어긋나지 않게 **시계(RTC) · 플래시(세이브) · Z80 상태**를 결정적으로 만들었어요. 이 가운데 Z80 IRQ 선과 플래시 블록 합치기는 순정 한 대짜리 코어에도 있던 버그예요.
- **각자 자기 세이브.** 손님은 자기 세이브로 해요. **짝 게임**은 2P 기계에 다른 롬을 꽂아요(카드 파이터즈 SNK판 ↔ 캡콤판, 다이브 얼러트 베키판 ↔ 매트판).
- **까다로운 게임 맞춤:** 델타 워프(시간 꾸러미) · 카드 파이터즈(VS 시작) · 유니트론(선공 뽑기).
- **확인한 것:** 기기 두 대로 SvC 밀레니엄 대전과 츠나게테 퐁 배틀을 확인했어요. 델타 워프 · 카드 파이터즈 · 유니트론은 VM 시험대에서 확인했고, 코어는 두 기기에 들어 있어요.

### 알아 두면 좋은 것

- 두 기기 모두 같은 코어 파일 · 같은 롬이어야 해요. 짝 게임은 정해진 짝 판끼리만 돼요.
- `ngp_dual_link` 가 `on` 이면 혼자 해도 2P 기계가 돌아요. KOF R-2 처럼 통신 칸이 켜지는 게임은 화면이 순정과 조금 달라져요(게임이 상대 기계를 알아봐요). `off` 면 순정 NeoPop 과 같은 동작이에요.
- 알려진 한계: 롬이 바이오스 통신 함수로 하는 게임만 흉내 냈어요. 코이코이 마작은 한 사람이 1P, 다른 사람이 2P 를 고르면 돼요. 한글 패치 롬은 통신 안내 글이 넘치는 경우가 있어요(카드 파이터즈 2 한글판은 롬을 한 바이트 고쳐야 했어요. 코어 문제는 아니에요).

## 무엇을 고쳤나

1. **`mednafen/ngp/hb_link.c` — 통신 케이블.** 링크가 켜지면 직렬 채널 0(SC0BUF · SC0CR · SC0MOD · BR0CR, 0xB2 RTS, CTS 악수, INTRX0 `0x6FE4` · INTTX0 `0x6FE8`)을 흉내 내고, 게임이 쓰는 바이오스 통신 함수(COM*)를 바이오스 작업 램의 링 버퍼(`0x6C80` · `0x6CC0` · `0x6D00`~`0x6D06`) 위에 구현해요. RTC 는 호스트 시계 대신 '기준 시각 + 에뮬 사이클'(상태에 저장)을 읽어요. 링크가 꺼져 있으면 순정 NeoPop 과 같은 동작이에요.
2. **`dual/` 앞단.** 안쪽 오브젝트를 `ld -r` 로 하나로 묶고 `objcopy --redefine-syms` 로 모든 전역 이름에 `ngpA_` / `ngpB_` 를 붙여 두 벌을 만들어요(`dual/Makefile.dual`). 줄 단위로 번갈아 돌리고, 상태는 고정 크기이고, 1P/2P 화면 옵션이 있어요. 밖으로는 `retro_*` 25개만 내보내요.
3. **상태를 일정하게.** Z80 IRQ 선(`iline`)을 상태에 넣어요(0001). `flash_optimise_blocks` 의 `FIXME std::max`(지운 32KB 칸이 몇백 바이트로 줄던 것)를 고치고, 플래시 없는 상태를 불러올 때 롬과 블록 목록을 되돌리고, 대기 중인 플래시 명령을 저장해요(0003). 상태 머리에 롬 지문을 넣어서 다른 롬이나 다른 2P 판으로 만든 상태는 거절해요(0004).
4. **옵션 설명 글(0005).** 옵션 설명의 `;` 를 `,` 로 바꿨어요. 레트로아크가 설명과 값 목록을 첫 `;` 에서 자르는데, 엉뚱한 곳에서 잘리던 것을 고쳐요.
5. **BIOS 기본 직렬 처리기(0006).** `COMINIT` 이 사용자 벡터 `0x6FE4` / `0x6FE8` 에 HLE 처리기를 깔고 `INTES0=0x66` 으로 둬요. COMINIT 만 부르는 게임(포켓 테니스 · 츠나게테 퐁 · 매지컬 드롭 · 사무라이 쇼다운 2 등)이 첫 바이트 뒤에 멈추던 것을 고쳐요.
6. **각자 자기 세이브와 짝 게임(0007, 1.1-os4).** 손님이 자기 세이브로 하고, 짝 게임이면 2P 기계에 다른 롬을 올려요.
7. **os5(0008~0010).** INTTX0 을 '보낼 칸이 빌 때' 걸어요(델타 워프 시간 꾸러미). `COMRECIVESTART` 가 RTS 도 켜요(카드 파이터즈 '어느 쪽이든 A'). 보낼 고리(64바이트)가 가득이면 `COMCREATEDATA` 가 `RA3=0xFF` 를 돌려줘요(카드 파이터즈 VS 시작).
8. **os5rtc(0011).** 2P 기계 시계를 1P 보다 3초 늦게 해요(`HB_P2_RTC_SKEW`). RTC 로 난수 씨앗을 정하는 게임(유니트론)이 두 기계에서 같은 난수로 선공 뽑기를 끝없이 비기던 것을 막아요.

이름이나 주석에 들어 있는 `hb_` · `hanbang` 은 우리가 고친 곳 표시일 뿐이에요. 이름을 바꾸지는 않았어요.

## 코어 옵션

첫 값이 기본이에요.

| 옵션 | 값 | 뜻 |
|---|---|---|
| `ngp_dual_screen` | `1P` · `2P` | 보이는 화면 · 소리 (방장/혼자 = 1P, 손님 = 2P) |
| `ngp_dual_link` | `on` · `off` | 2P 기계를 통신 케이블에 이어 돌려요. `off` = 혼자, 한 대. 다시 켜야 바뀌어요. |
| `ngp_dual_language` | `english` · `japanese` | 두 기계의 언어예요. 다시 켜야 바뀌어요. |
| `ngp_dual_p2_rom` | `same` · `partner` | 2P 카트리지예요. `partner` = 짝 게임의 상대 판(`/tmp/hb_ngp_dual_p2.ngc` 에서 읽어요). 다시 켜야 바뀌어요. |

**`/tmp` 파일 약속** (없으면 평소 동작이에요): `/tmp/hb_ownsave/`(각자 세이브 거래 폴더) · `/tmp/hb_dual_p2rom`(짝 게임의 2P 롬) · `/tmp/hb_dual_screen`(화면 · 소리 고르기). 코어는 롬을 보통 파일로만 읽어서, ZIP 은 훅이 `/tmp` 에 풀어 줘야 해요.

**세이브.** 1P 는 순정과 같은 `.flash`, 2P 는 방장 기기의 `.p2.flash` 예요. 손님 기기는 끝낼 때 세이브를 쓰지 않아요. 자기 세이브는 각자 세이브 모드(기종 3)로 방장의 2P 칸에 갔다가 돌아와요.

## KNULLI 에 넣기

두 기기에 **같은 `.so`** 를 넣어요. [최신 릴리스](https://github.com/Squirbie/handheld-link-cores/releases/latest)에서 `ngp-mednafen-dual-linux-aarch64.zip` 을 받아 풀고, 게임을 끈 상태에서 넣어요.

**시작하기 전에**

- 미리 빌드한 `.so` 는 **aarch64 리눅스**용이에요. glibc 2.34 이하 기호만 쓰고 `libstdc++` · `libgcc_s` · `libc` 가 필요해요. 다른 CPU · OS 는 패치로 다시 빌드해야 해요.
- 확인한 환경은 **KNULLI + RetroArch 1.22.2** 뿐이에요.
- 각자 세이브 · 짝 게임 · 화면 파일 기능은 **KNULLI 훅이 `/tmp` 에 파일을 써 줘야** 켜져요. 파일이 없으면 평소처럼 방장 기기의 1P `.flash` + `.p2.flash` 로 돌아요.
- 푼 파일을 확인하세요: md5 는 위 표와 같고, sha256 은 `3eb30e50c31cbd6d8c92794969736507454ff905d54e42096ea42aa65c54d5a3` 예요.

**순서**

1. 코어 파일을 SD 쪽 `/userdata/system/hanbang_cores/` (미리 빌드한 파일이 쓰는 기본 자리)에 두고, `/usr/lib/libretro/` 에는 바로가기를 둬요. 순정 `mednafen_ngp_libretro.so` 는 건드리지 않는 새 이름이에요.
   ```sh
   mkdir -p /userdata/system/hanbang_cores
   cp mednafen_ngp_dual_libretro.so /userdata/system/hanbang_cores/ && chmod 755 /userdata/system/hanbang_cores/mednafen_ngp_dual_libretro.so
   mount -o remount,rw /
   ln -sfn /userdata/system/hanbang_cores/mednafen_ngp_dual_libretro.so /usr/lib/libretro/mednafen_ngp_dual_libretro.so
   ```
2. **코어 정보 파일.** 없으면 실행기가 거절해요. 순정 정보 파일을 베껴 이름만 바꾸고 덧칠을 저장해요(KNULLI 의 `/usr` 은 덧칠이라, 1번의 바로가기도 이때 저장해야 재부팅 뒤에 남아요).
   ```sh
   I=/usr/share/libretro/info
   sed -e 's/^display_name = .*/display_name = "SNK - Neo Geo Pocket \/ Color (Beetle NeoPop Dual)"/' \
       -e 's/^corename = .*/corename = "Beetle NeoPop Dual"/' $I/mednafen_ngp_libretro.info > $I/mednafen_ngp_dual_libretro.info
   knulli-save-overlay
   ```
3. **게임별 코어 지정.** `/userdata/system/knulli.conf` 에 이렇게 적어요: `ngpc["<롬 파일 이름>.zip"].core=mednafen_ngp_dual` (흑백이면 `ngp[...]`).
4. **ES 에서 '넷플레이 게임 시작'이 보이게.** ES 기능 표(`es_features_*.cfg`)에 한 줄을 더해요: `<core name="mednafen_ngp_dual" features="netplay" />`. 그러면 'A 길게 → 넷플레이 게임 시작'이 보여요.
5. **게임 시작 훅.** 게임을 켤 때마다 훅이 `config/Beetle NeoPop Dual/<롬 이름>.opt` 에 방장/혼자 = `1P`, 손님 = `2P`, `ngp_dual_link = "on"`, `ngp_dual_p2_rom = "same"` 을 써요. 짝 게임이면 손님의 '같이 / 혼자' 창이 자기 판 세이브와 상대 롬을 보내고, 방장 코어가 그때 2P 롬을 바꿔요. 훅은 [`knulli-scripts/nds_save_sync.sh`](../../knulli-scripts/) 의 21번 블록이에요.
   - `/userdata/system/scripts/nds_save_sync.sh` (미리 빌드한 파일이 쓰는 기본 자리)로 넣고, 그 폴더에는 이 파일 하나만 두세요. KNULLI 가 그 폴더의 모든 파일을 실행해요.
   - 같은 폴더의 도우미 스크립트는 `/userdata/system/claude/` (미리 빌드한 파일이 쓰는 기본 자리)에 넣어요: `hb_ownsave.py`(각자 세이브)와 `hb_joinask.py`('같이 / 혼자' 고르는 창)예요.
6. **화면 설정.** 순정 코어의 화면 설정(`Beetle NeoPop.cfg` 와 `.glslp` 파일)을 `Beetle NeoPop Dual.` 로 시작하는 이름으로 복사해 두면 셰이더 · 화면 위치가 그대로예요.
7. **되돌리기.** 바로가기를 지우고 `knulli-save-overlay` 를 실행한 다음 `knulli.conf` 줄을 빼요. 순정 코어는 그대로예요.

## 소스에서 빌드

```sh
git clone https://github.com/libretro/beetle-ngp-libretro
cd beetle-ngp-libretro
git checkout 139fe34c8dfc5585d6ee1793a7902bca79d544de
PATCHES=/path/to/handheld-link-cores/cores/ngp-mednafen-dual/patches
for p in "$PATCHES"/*.patch; do patch -p1 < "$p" || break; done
nice make -j1 -f dual/Makefile.dual GIT_VERSION=os5rtc      # Debian 12 aarch64, gcc 12 기준
# -> build_dual/mednafen_ngp_dual_libretro.so   (같은 곳에 시험용 한 대짜리 mednafen_ngp_hb_libretro.so 도 생겨요)
```

- `ARCH_FLAGS` 기본값은 `-mcpu=cortex-a53`(RG35XX 계열 H700 맞춤)이에요. 다른 CPU 면 `ARCH_FLAGS=` 로 바꾸세요.
- `GIT_VERSION` 글자가 `1.2-os5 <글자>` 로 코어 판에 들어가요. 두 기기가 같아야 하고, `1.2-os5` 와 합쳐 끝 글자 포함 32바이트 이하여야 해요(컴파일 때 검사).
- GNU binutils(`ld -r` · `objcopy`)에 기대는 Makefile 이라 리눅스에서만 확인했어요.

## 패치

`patches/` 안 파일을 **이름 순서대로** 한 번씩 걸어요.

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `0001-NGP-save-the-Z80-IRQ-line-in-savestates.patch` | Z80 IRQ 선을 상태에 저장해요. |
| 2 | `0002-NGP-Dual-link-cable-for-two-consoles-in-one-core.patch` | 직렬 채널 0 · 바이오스 통신 함수 · 결정적 시계 · 줄 단위 API · 두 대 앞단을 더해요. |
| 3 | `0003-NGP-deterministic-flash-state-rollback-netplay.patch` | 되감기 넷플레이용으로 플래시 상태를 결정적으로 만들어요. |
| 4 | `0004-NGP-Dual-refuse-states-made-with-other-ROMs.patch` | 상태 머리에 롬 지문을 넣어, 다른 롬으로 만든 상태는 거절해요. |
| 5 | `0005-NGP-Dual-option-descriptions-use-instead-of.patch` | 옵션 설명의 `;` 를 `,` 로 바꿔, 레트로아크가 값 목록을 엉뚱한 곳에서 자르지 않게 해요. |
| 6 | `0006-NGP-Dual-BIOS-default-serial-handlers-at-COMINIT.patch` | `COMINIT` 이 바이오스 기본 직렬 처리기를 깔아요. |
| 7 | `0007-NGP-Dual-1.1-os4-guest-own-save-kind-3-and-NGP-partner-pairs.patch` | 각자 자기 세이브(기종 3)와 짝 게임이에요(1.1-os4). |
| 8 | `0008-NGP-Dual-1.2-os5-INTTX0-when-the-transmit-buffer-emp.patch` | 보낼 칸이 빌 때 INTTX0 을 걸어요(1.2-os5). |
| 9 | `0009-NGP-Dual-1.2-os5-COMRECIVESTART-asserts-RTS.patch` | `COMRECIVESTART` 가 RTS 도 켜요. |
| 10 | `0010-NGP-Dual-1.2-os5-COMCREATEDATA-returns-FF-when-the-s.patch` | 보낼 고리가 가득이면 `COMCREATEDATA` 가 `0xFF` 를 돌려줘요. |
| 11 | `0011-os5rtc-p2-rtc-skew.patch` | 2P 기계 시계를 1P 보다 3초 늦게 해요(`os5rtc`, 최종 판). |

- `0011` 의 원래 파일 이름은 `os5_p2_rtc_skew.patch` 예요. 순서대로 걸리게 번호를 붙였고, 내용은 같아요.
- 소스 출처: `139fe34` + 패치 0001~0010 = 갈래 `hb_dual` 의 `7b5d908` 이고, 이 위에 0011 을 얹은 소스가 최종 코어예요.
- 패치 속 주석 일부는 한국어예요. 쓴 그대로 두었어요.
- **확인한 것(2026-10-29, 맥에서).** 패치 10개를 거꾸로 풀어 얻은 원본 파일 12개의 git blob 지문이 패치의 `index` 줄과 모두 같았고, 다시 앞으로 걸면 파일 37개의 지문이 모두 맞았어요. `0011` 도 어긋남 없이 걸리고 결과 지문이 패치의 `516a654` 와 같아요. 개발 때 `GIT_VERSION=7b5d908` 로 두 번 빌드해 같았고(md5 가 `3c1499b5` 로 시작), os5rtc 는 같은 도구로 다시 빌드해 `91b8d251` 이 나왔어요.

## 원본에 보내기

보낼 만한 고침이 있어요. 순정 한 대짜리 코어에도 있는 상태 저장 버그예요. 되감기 · 런어헤드 · 넷플레이에서 어긋남으로 드러나요.

1. **Z80 IRQ 선이 상태에 없는 것**(패치 0001). 원본 master 에 그대로인 것을 2026-10-29 에 확인했어요.
2. **`flash_optimise_blocks` 가 지운 32KB 칸을 줄이는 것**(패치 0003). `FIXME std::max` 때문이에요. 이것도 원본 master 에 그대로인 것을 2026-10-29 에 확인했어요.
3. **플래시 없는 상태를 불러올 때** 롬 · 블록 목록이 안 돌아와요(패치 0003, master 확인은 안 했어요).

패치 0003 은 우리 `hb_link.c` 부분이 섞여 있어서, `flash.c` · `system.c` · `rom.c` 만 추려 보내야 해요. 제목 초안: "Savestate fixes for rollback/run-ahead: save the Z80 IRQ line, fix flash block merging, restore ROM/flash on load". 영어 초안 글은 [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) 의 `upstream_pr_candidate` 에 있어요.

두 대 앞단 · 링크 · 각자 세이브는 이 구성 전용이라 보내지 않아요.

## 라이선스

- 원본 Beetle NeoPop(Mednafen NeoPop)은 **GPL-2.0 이상**이에요(`COPYING` = GPLv2, 파일 머리말은 "version 2 … or (at your option) any later version"). 라이선스 원문은 [`LICENSES/beetle-ngp-libretro_COPYING`](../../LICENSES/beetle-ngp-libretro_COPYING) 에 있어요. 패치는 그 조건을 따르고, 새로 쓴 `hb_link.c` · `hb_link.h` · `dual/libretro_dual.c` 에도 같은 GPL 머리말을 달았어요.
- `dual/hb_ownsave.h` · `hb_storage.h` · `hb_romfile.h` 에는 별도 머리말이 없어요. 같은 코어에 합쳐져 배포되므로 코어와 같은 조건으로 공개해요(이 프로젝트에서 새로 쓴 파일이에요).
- 이 코어를 넣은 바이너리를 배포할 때는 **고친 소스(이 패치들)** 를 함께 공개해야 해요.
