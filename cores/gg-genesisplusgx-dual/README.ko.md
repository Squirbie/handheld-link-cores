<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# Genesis Plus GX GG Dual — 기기 두 대로 하는 기어 투 기어 케이블 대전

> 게임기어 두 대를 기어 투 기어 케이블로 이어 코어 하나 안에서 돌려서, 케이블로 둘이 하는 게임을 레트로아크 넷플레이로 기기 두 대에서 같이 할 수 있게 해 주는 코어예요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/gg-genesisplusgx-dual-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| **코어 파일** | `genesisplusgx_gg_dual_libretro.so` — aarch64 리눅스용, 11,984,232 바이트 (git 에는 없고 릴리스 zip 안에 있어요) |
| **버전** | `1.1-os4-302fe82` (안쪽 코어 `v1.7.4-302fe82`) |
| **md5** | `2db4468dac16b8754d268e90348639a0` |
| **원본** | [libretro/Genesis-Plus-GX](https://github.com/libretro/Genesis-Plus-GX) @ [`302fe82`](https://github.com/libretro/Genesis-Plus-GX/commit/302fe82fccbe2e036c3e13891db6513982a497ac) ("[Core/MD] improved invalid SRAM header info detection", 2024-02-27). KNULLI 의 genesisplusgx 패키지가 가리키는 커밋(순정 코어 판 글자 `v1.7.4-302fe82`)과 같아요. 만든 분의 저장소 [ekeeke/Genesis-Plus-GX](https://github.com/ekeeke/Genesis-Plus-GX) 에도 같은 커밋이 있어요. |
| **라이선스** | Genesis Plus GX 라이선스: **비상업 조건이라 돈을 받고 팔 수 없어요.** 고친 판은 소스 전체를 함께 공개해야 해요(원본 `LICENSE.txt` 와 아래 '라이선스' 참고) |
| **시험한 환경** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (확인한 환경은 이것뿐이에요) |

## 무엇을 하나

순정 Genesis Plus GX 는 게임기어 확장 포트(0x01~0x06)에 쓴 값을 저장만 하고 상대에게 보내지 않으며 NMI 도 없어서, 케이블로 둘이 하는 게임이 같이 되지 않았어요. 이 코어는 **게임기어 두 대를 코어 하나 안에** 넣고 기어 투 기어 케이블(병렬 포트 엇갈림 · 직렬 UART · NMI)을 흉내 내서, 기기 두 대가 레트로아크 넷플레이로 같이 할 수 있게 해요. 방장 기기 화면은 1P 기계, 손님 기기 화면은 2P 기계를 보여 줘요.

- **어긋나지 않아요.** 두 기계가 줄 단위로 번갈아 돌고, 같은 장에 같은 단추를 누르면 2P 를 1장 늦춰서 넷플레이(되감기)에서 어긋나지 않게 했어요.
- **각자 자기 세이브.** 손님이 자기 세이브로 하는 '각자 자기 세이브'(기종 4)가 있어요. 라스트 바이블 스페셜처럼 세이브가 있어야 통신이 열리는 게임용이에요.
- **기기 두 대로 확인한 것:** 소닉 드리프트 2 VERSUS(각자 자기 차를 조작). VM 시험대에서는 슈퍼 컬럼스 · 팩 어택 · 슈퍼 모나코 GP · 아랑전설 스페셜 LINK GAME 등이 통신 대전 시작과 각자 조작까지 됐어요.

### 알아 두면 좋은 것

- 두 기기 모두 같은 코어 파일 · 같은 롬이어야 해요.
- `gg_dual_link` 가 `on` 이면 혼자 해도 2P 기계가 돌아요. 슈퍼 모나코 GP 처럼 케이블이 있으면 메뉴가 바뀌는 게임은 '1PLAYER / 2PLAYERS' 고르기가 생겨요. 혼자 할 때 속도는 기기에서 초당 약 59장으로 문제없었어요. 순정 동작을 원하면 `off` 로 두세요.
- 알려진 한계: 병렬 손잡기 · 직렬 모델은 문서를 근거로 했고 실물 게임기어와 대조하지는 못했어요. 라스트 바이블 스페셜처럼 세이브가 있어야 통신이 열리는 게임은 세이브가 필요해요.

## 무엇을 고쳤나

1. **케이블과 줄 단위 실행(0001).** 케이블 모델 `core/hb_gglink.h`, `io_ctrl.c` 의 포트 0x01~0x05, `system.c` 의 줄 단위 `system_frame_sms`, `libretro/libretro.c` 의 `retro_run` 쪼개기와 `hb_gg_*` 함수, 그리고 `dual/` 의 두 대 앞단(`libretro_dual.c` · `build_dual.sh` · `link_dual.T`)이에요. 앞단은 안쪽 오브젝트를 `ld -r` 로 묶고 `objcopy --redefine-syms` 로 전역 이름에 `ggA_` / `ggB_` 를 붙여 두 벌을 만들어요. 밖으로는 `retro_*` 25개만 내보내요.
2. **직렬을 보통 UART 로(0002).** 받은 바이트는 덮어쓰고, NMI 는 '받음 & 허용'이 0→1 로 바뀔 때만 걸어요. 같은 장에 누르면 2P 를 1장 미뤄요. 줄 단위 시험 길과 통계도 있어요.
3. **옵션 설명 글(0003).** 설명 속 `;` 를 `,` 로 바꿨어요(1바이트). 레트로아크가 첫 `; ` 에서 값 목록을 잘라 메뉴에 `restart); on` 으로 보이던 것을 고쳐요.
4. **각자 자기 세이브(0004, 1.1-os4).** `dual/hb_ownsave.h` · `hb_storage.h` · `hb_romfile.h`(네오지오 · 원더스완 두 대 코어와 같은 모듈)와 `libretro_dual.c` 변경이에요. 방장은 요청(HBQ3)을 받으면 2P 세이브 램에 손님의 `.srm` 을 넣고 2P 를 다시 켜요. 손님(`--connect`)은 `RETRO_MEMORY_SAVE_RAM` 크기를 0 으로 알려 레트로아크가 손님의 1P 세이브를 읽지도 쓰지도 않게 하고, 2P 로 확인된 뒤에만 중간 저장 · 끝 내보내기를 해요.

이름이나 주석에 들어 있는 `hb_` · `hanbang` 은 우리가 고친 곳 표시일 뿐이에요. 이름을 바꾸지는 않았어요.

## 코어 옵션

첫 값이 기본이에요.

| 옵션 | 값 | 뜻 |
|---|---|---|
| `gg_dual_screen` | `1P` · `2P` | 보이는 화면 · 소리 (방장/혼자 = 1P, 손님 = 2P) |
| `gg_dual_link` | `on` · `off` | `off` 면 순정과 같은 한 대 동작이에요. 게임을 켤 때만 읽어요. |

**세이브.** 1P 는 `.srm`, 2P 는 방장 기기의 `<롬 이름>.p2.sav` 예요. 상태 = 두 대 + 롬 지문(약 295KB 고정)이에요.

## KNULLI 에 넣기

두 기기에 **같은 `.so`** 를 넣어요. [최신 릴리스](https://github.com/Squirbie/handheld-link-cores/releases/latest)에서 `gg-genesisplusgx-dual-linux-aarch64.zip` 을 받아 풀고, 게임을 끈 상태에서 넣어요.

**시작하기 전에**

- 미리 빌드한 `.so` 는 **aarch64 리눅스**용이에요. glibc 2.34 이하 기호만 쓰고 `libm` · `libc` 가 필요해요. 다른 CPU · OS 는 패치로 다시 빌드해야 해요. GNU binutils 의 `ld -r` · `objcopy` 에 기대서 리눅스에서만 확인했어요.
- 확인한 환경은 **KNULLI + RetroArch 1.22.2** 뿐이에요.
- 각자 세이브 기능은 KNULLI 훅이 `/tmp/hb_ownsave/` 에 파일을 써 줘야 켜져요. 없으면 평소처럼 방장 기기의 1P `.srm` + `.p2.sav` 로 돌아요.
- 푼 파일을 확인하세요: md5 는 위 표와 같고, sha256 은 `5232650917d039247e0f67e2dea0bd0c579287a3ec56b0b39fa6a5151c5ef595` 예요.

**순서**

1. 코어 파일을 SD 쪽 `/userdata/system/hanbang_cores/` (미리 빌드한 파일이 쓰는 기본 자리)에 두고, `/usr/lib/libretro/` 에는 바로가기를 둬요. 순정 `genesisplusgx_libretro.so` 는 건드리지 않는 새 이름이에요.
   ```sh
   mkdir -p /userdata/system/hanbang_cores
   cp genesisplusgx_gg_dual_libretro.so /userdata/system/hanbang_cores/ && chmod 755 /userdata/system/hanbang_cores/genesisplusgx_gg_dual_libretro.so
   mount -o remount,rw /
   ln -sfn /userdata/system/hanbang_cores/genesisplusgx_gg_dual_libretro.so /usr/lib/libretro/genesisplusgx_gg_dual_libretro.so
   ```
2. **코어 정보 파일.** 없으면 실행기가 거절해요. 순정 Genesis Plus GX 의 정보 파일을 `/usr/share/libretro/info/genesisplusgx_gg_dual_libretro.info` 로 베끼고 `display_name` 을 `"Sega - Game Gear (Genesis Plus GX GG Dual)"` 로 바꾼 뒤 `knulli-save-overlay` 를 실행해요(KNULLI 의 `/usr` 은 덧칠이라, 1번의 바로가기도 이때 저장해야 재부팅 뒤에 남아요).
3. **게임별 코어 지정.** `/userdata/system/knulli.conf` 에 이렇게 적어요: `gamegear["<롬 파일 이름>.zip"].core=genesisplusgx_gg_dual`
4. **ES 에서 '넷플레이 게임 시작'이 보이게.** ES 기능 표(`es_features_*.cfg`)에 한 줄을 더해요: `<core name="genesisplusgx_gg_dual" features="netplay" />`
5. **게임 시작 훅.** 게임을 켤 때마다 훅이 `config/Genesis Plus GX GG Dual/<롬 이름>.opt` 에 방장/혼자 = `1P`, 손님 = `2P`, `gg_dual_link = "on"` 을 써요. 훅은 [`knulli-scripts/nds_save_sync.sh`](../../knulli-scripts/) 의 22번 블록이에요.
   - `/userdata/system/scripts/nds_save_sync.sh` (미리 빌드한 파일이 쓰는 기본 자리)로 넣고, 그 폴더에는 이 파일 하나만 두세요. KNULLI 가 그 폴더의 모든 파일을 실행해요.
   - 같은 폴더의 도우미 스크립트는 `/userdata/system/claude/` (미리 빌드한 파일이 쓰는 기본 자리)에 넣어요: `hb_ownsave.py`(각자 세이브)와 `hb_joinask.py`('같이 / 혼자' 고르는 창)예요.
6. **화면 설정.** 순정 코어의 화면 설정(`gamegear.cfg` 와 `.glslp` 파일)을 `config/Genesis Plus GX GG Dual/` 로 복사해 두면 셰이더 · 화면 위치가 그대로예요.
7. **되돌리기.** 바로가기와 정보 파일을 지우고 `knulli-save-overlay` 를 실행한 다음 `knulli.conf` 줄을 빼요. 순정 코어는 그대로예요.

## 소스에서 빌드

```sh
git clone https://github.com/libretro/Genesis-Plus-GX
cd Genesis-Plus-GX
git checkout 302fe82fccbe2e036c3e13891db6513982a497ac
PATCHES=/path/to/handheld-link-cores/cores/gg-genesisplusgx-dual/patches
for p in "$PATCHES"/*.patch; do patch -p1 < "$p" || break; done
nice bash dual/build_dual.sh "-302fe82"     # Debian 12 aarch64, gcc 12 기준
# -> build_dual/genesisplusgx_gg_dual_libretro.so   (같은 곳에 시험용 한 대짜리 genesis_plus_gx_hb_libretro.so 도 생겨요)
```

- 스크립트는 ① 원래 `Makefile.libretro`(`platform=unix`, `-mcpu=cortex-a53`, `-j1`)로 안쪽 오브젝트를 만들고 ② 두 벌로 이름을 바꾸고 ③ 래퍼와 묶어요. `ARCH_FLAGS` 환경 변수로 CPU 플래그를 바꿀 수 있어요.
- 각자 세이브 모듈이 스레드를 하나 써서, glibc 2.34 보다 오래된 환경에서는 `dual/build_dual.sh` 의 래퍼 링크 줄에 `-lpthread` 를 더하세요(미리 빌드한 파일은 `-lm -lpthread` 로 묶었어요).
- 같은 소스를 다시 빌드하면 build-id 20바이트만 다르고 나머지는 같았어요(개발 기록). 그래서 직접 빌드한 파일의 md5 는 위 표와 다를 수 있어요.

## 패치

`patches/` 안 파일을 **이름 순서대로** 한 번씩 걸어요.

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `0001-GG-Dual-Gear-to-Gear-link-hooks-line-stepped-SMS-GG-.patch` | 케이블 모델 · 줄 단위 실행 · 두 대 앞단을 더해요. |
| 2 | `0002-GG-Dual-plain-UART-serial-NMI-on-RX-ready-enable-edg.patch` | 직렬을 보통 UART 로 바꾸고, 같은 장 누름을 1장 미뤄요. |
| 3 | `0003-GG-Dual-option-description-uses-comma-instead-of-semicolon.patch` | 옵션 설명의 `;` 를 `,` 로 바꿔요. |
| 4 | `0004-GG-Dual-1.1-os4-guest-own-save.patch` | 각자 자기 세이브(기종 4), 최종 판(1.1-os4)이에요. |

- **`0003` 은 되살려 만든 패치예요.** 이 한 바이트 수정은 2026-10-22 에 소스 폴더에서 바로 고쳐 코어에 넣었고 커밋은 안 했어요(바이너리의 같은 글을 바이트 단위로 바꾸는 스크립트로도 한 번 적용했어요). 2026-10-29 에 소스 폴더의 `git diff`(커밋 `3ef1895` 기준)를 뽑아 패치 모양으로 만들었어요. `0004` 는 이 수정이 들어간 소스 위에서 만들어졌어요.
- `0004` 의 원래 파일 이름은 `0003-GG-Dual-1.1-os4-guest-own-save.patch` 예요. 0003 을 위에 끼워 넣으며 번호만 밀렸고, 내용은 같아요.
- 소스 출처: `302fe82` + 갈래 `hb_gg_dual` 커밋 둘 = 패치 0001~0002 예요.
- 패치 속 주석 일부는 한국어예요. 쓴 그대로 두었어요.
- **확인한 것(2026-10-29, 맥에서).** 원본 `302fe82` 에 4개를 순서대로 걸면 어긋남(fuzz) 없이 모두 적용되고, 결과 소스가 개발 때 소스 폴더(0001+0002+옵션 수정+0004 적용본)와 똑같아요. 판 글자는 `DUAL_VERSION "1.1-os4"` + `GIT_VERSION` 이에요. 개발 때 0001~0002 는 두 번 빌드해 같았고, 0004 판은 래퍼만 다시 묶어 두 번 빌드해 같았어요(안쪽 오브젝트는 md5 가 `303ef6a0` 으로 시작하는 빌드와 같은 소스).

## 원본에 보내기

보내지 않아요. 한 기기 안에 코어 두 벌(`ggA_` / `ggB_`)과 케이블 모델을 얹는 구성 전용 기능이라, 원본 코어(한 대 에뮬)에 넣을 단독 버그 고침이 아니에요. 확장 포트 통신은 두 인스턴스를 잇는 프런트엔드가 있어야 쓸 수 있어서 받아 줄 가능성이 낮고, 옵션 글 `;` → `,` 수정(패치 0003)은 우리 옵션 이름에만 해당돼요. ([`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) 의 `upstream_pr_candidate` 도 '보낼 만하지 않음'으로 적혀 있어요.)

## 라이선스

- 원본 Genesis Plus GX 는 자체 라이선스(`LICENSE.txt`, 사본은 [`LICENSES/Genesis-Plus-GX_LICENSE.txt`](../../LICENSES/Genesis-Plus-GX_LICENSE.txt))를 써요. 요지는 **비상업**이라는 거예요. 다시 배포는 할 수 있지만 **팔거나 상업 제품 · 활동에 쓸 수 없어요.** 이 코어를 넣은 기기나 이미지를 돈을 받고 파는 것도 포함이에요. 고친 판은 **고친 소스(쓰인 구성 요소 소스까지) 전부를 함께 공개**해야 하고, 저작권 표시와 면책 문구를 그대로 둬야 해요. 자세한 조건은 원본 `LICENSE.txt` 를 따르세요.
- 이 폴더의 패치(와 새로 쓴 `dual/` · `core/hb_gglink.h`)도 같은 조건으로 공개해요. 안쪽에 합쳐진 zlib · FLAC 등은 각자 조건을 따라요.
- `dual/hb_ownsave.h` · `hb_storage.h` · `hb_romfile.h` 는 별도 머리말 없이 이 코어와 같은 조건으로 공개해요(이 프로젝트에서 새로 쓴 파일이에요).
