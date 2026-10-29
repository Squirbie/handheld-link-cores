<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# mGBA Dual — 한 코어 안에 GBA 두 대와 통신 케이블

> GBA 두 대를 가상 통신 케이블로 이어 한 코어 안에서 돌려, 기기 두 대가 RetroArch 넷플레이만으로 GBA 통신 케이블 게임을 같이 하게 해 주는 libretro 코어예요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/gba-mgba-dual-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| 코어 파일 | `mgba_dual_libretro.so` (aarch64 리눅스, 1,248,696바이트, strip 됨) |
| 버전 | `1.6-os4 (mGBA 7a12d6d4)` (`os4`는 '각자 자기 세이브 4판'이라는 뜻의 이름표) |
| md5 | `df34be2b181f863497fa749d04d5c1c0` |
| 원본 | [libretro/mgba](https://github.com/libretro/mgba) 커밋 `7a12d6d` + [tangobattle/mgba](https://github.com/tangobattle/mgba)의 커밋 다섯 개 |
| 라이선스 | MPL-2.0 |
| 시험한 기기 | Anbernic RG35XX Pro · KNULLI |

RG35XX Pro(KNULLI, aarch64 리눅스)에 실제로 들어간 최종판이에요.
완성된 코어 파일(`.so`)은 이 폴더가 아니라 릴리스 zip `gba-mgba-dual-linux-aarch64.zip` 안에 들어 있어요(위의 Download 버튼).
이 폴더에는 설명과 패치만 있고, 롬 · BIOS · 세이브는 들어 있지 않아요.

## 무엇을 하나

GBA에는 **통신 케이블로 둘이 하는 게임**(젤다 4개의 검, 유희왕, 철권 어드밴스, 록맨 EXE, 봄버맨 …)이 많은데, 기기 하나에는 GBA가 하나뿐이에요.
이 코어는 **한 코어 안에서 GBA 둘(1P · 2P)을 돌리고** 가상 케이블로 이어 줘요.
두 기기가 RetroArch 넷플레이로 같은 입력을 주고받으면, 두 기기가 똑같은 계산을 해서 똑같은 장면을 만들어요.
방장은 1P 화면 · 소리를, 손님은 2P 화면 · 소리를 봐요(보여 주는 것만 달라요).

이 판으로 되는 것:

- **순서를 안 맞춰도 붙어요.** 누가 먼저 통신 메뉴에 들어가도(젤다 4개의 검 · 유희왕 …) 케이블이 이어져요(1.4부터).
- **각자 자기 세이브.** 손님의 세이브가 방장 기기의 2P 칸에 들어가서 놀고, 끝나면 손님 세이브로 돌아가요. 방장 세이브는 안 섞여요.
- **짝 게임.** 같은 시리즈의 서로 다른 판끼리(록맨 EXE 5 블루스 ↔ 컬로넬, 봄버맨 블루 ↔ 레드 …)도 이어져요(1.5부터).
- **싱글팩 게임.** 팩 하나로 여럿이 하는 게임(봄버맨 스토리 · 매지컬 퀘스트 · 샨테)은 손님 GBA를 **팩 없이 진짜 바이오스로** 켜서 방장의 프로그램을 받게 해요(1.6부터).
- **혼자 켜는 옵션**(`mgba_dual_link=off`), 게임 중에도 바꿀 수 있는 1P / 2P 화면 선택 파일.

두 기기가 **같은 판(1.6-os4)** 이어야 해요. 판이 다르면 상태 불러오기를 거절해서(몰래 어긋나지 않게) '불러오기 실패 · 어긋남' 알림만 떠요.

## 무엇을 고쳤나

1. **새 libretro 앞단** `src/platform/libretro/dual/libretro_dual.c`(패치 0006, CMake 옵션 `LIBRETRO_DUAL`).
   같은 롬의 GBA 둘과 `GBASIOLockstepCoordinator` 하나를 갖고, `retro_run`이 깨어 있는 코어를 한 스레드에서 번갈아 돌려 1P가 한 장을 마칠 때까지 진행해요(tangobattle/mgba-rollback과 같은 방식).
   그래서 전체가 두 패드 입력의 결정적 함수가 되고, RetroArch 넷플레이의 입력 동기 + 되감기만으로 맞아요. 포트 0 → 1P, 포트 1 → 2P예요.
   상태는 두 코어 + 두 lockstep 드라이버 + 두 세이브 + mGBA 상태가 잃어버리는 값(오디오 FIFO · DMA)을 고정 크기(1,058,208바이트)로 담아요.
   RTC는 고정 시각(2004-01-01 + 에뮬 시간)이에요.
2. **tangobattle/mgba에서 가져온 lockstep · 상태 정확성**(0001 ~ 0005): 한 스레드 협력 구동, 상태 복원이 비트까지 같게, 약 128초 뒤 시계 넘침 방지, 오디오 상태 정확 복원.
3. **상태 불러올 때 RCNT 아래 비트(연결선 핀) 복원**(0008): 이게 없으면 넷플레이 접속 · 재동기 뒤 CRC가 계속 달라, 확인할 때마다(30장마다) 상태를 다시 받았어요(5분에 490번 → 0번).
4. **통신 정확도**: SIOCNT 클록 · 속도 비트와 준비 안 된 상대 처리(0010), 되감기 때 VRAM 경합 마스크와 SIO 이벤트 순서(0011), **링크 박자(0016)**.
   링크 박자는 상대 GBA가 메뉴에 있어도 SD 선이 1로 읽히게 하고, 부모가 전송 중 시작 비트 0을 쓰면 그 전송을 멈추게 해요. 그래서 젤다 · 유희왕이 순서와 상관없이 붙어요.
5. **저장**: 2P 세이브 이름 · 쓰기(0007 · 0009), **각자 자기 세이브**(0014 · 0015). 손님 세이브를 방장 2P 칸에 넣고 끝나면 되돌려 써요. 실제로 2P로 입장했는지 확인하고, 임시 파일 + fsync로 쓰고, 데이터가 5초 동안 안정되면 중간 저장을 해요.
6. **짝 게임**(0018): 2P 게임기만 다른 롬(같은 시리즈의 다른 판)으로 켜요. 짝일 때만 상태 판 칸이 바뀌고, 짝이 아니면 1.4.1과 바이트까지 같아요.
7. **싱글팩**(0019): 게임별 옵션 `mgba_dual_p2_nocart = "enabled"`이면 2P를 롬 없이 바이오스로 켜서 방장의 멀티부트 신호(`0x6200`)를 기다려요. 바이오스를 못 쓰면 2P를 팩으로 켜고 기록만 남겨요. 옵션이 꺼져 있으면(기본) 1.5와 바이트까지 같아요.

패치된 코드 속 `hb_` · `HB_`로 시작하는 이름과 `hanbang`이라는 글자는 '여기를 고쳤다'는 우리 표시일 뿐이에요. 패치 · 바이너리 · 스크립트가 서로 맞도록 이름을 바꾸지 않고 그대로 뒀어요.

### 확인한 것

- **1.6 단계(싱글팩):** 하네스 18/18(봄버맨 스토리 · 매지컬 퀘스트 · 샨테). 실제 RetroArch 1.22.2 넷플레이에서 어긋남 0, 되감기 8,700번 · 실제 RetroArch 상태 2,700번에서 불일치 0. 옵션이 꺼져 있으면 1.5와 장마다 지문이 같아요(27,492장).
- **1.5 단계(짝 게임):** 봄버맨 블루 ↔ 레드, 록맨 EXE 5 블루스 ↔ 컬로넬이 대전 시작 · 칩 고르기까지 갔어요. 짝이 아니면 1.4.1과 바이트까지 같아요(22,899장).
- **1.4 단계(링크 박자, 시각차 하네스):** 젤다 4개의 검 361/361 · 유희왕 2006 346/361 · KOF EX2 161/161(통과 / 전체). 되감기 전체 비교 26,250번에서 불일치 0(GBA와 원더스완 합계).
- **한계:** 대부분 맥 · 가상 머신 하네스와 가상 머신 안의 실제 RetroArch 시험이에요. 기기 와이파이 위의 긴 시험과 모든 게임의 통신 메뉴는 보지 않았어요.

## 코어 옵션

`libretro_dual.c`에 있어요.

| 옵션 | 값 | 뜻 |
|---|---|---|
| `mgba_dual_link` | on / off | 케이블 연결(콘텐츠를 켤 때 한 번만 읽음). off면 GBA 한 대만 만들고 보통 `.srm` 세이브를 써요. |
| `mgba_dual_screen` | 1P / 2P | 보여 줄 화면 · 소리(방장 · 혼자 = 1P, 손님 = 2P). 에뮬 상태에는 영향이 없어요. |
| `mgba_dual_use_bios` | ON / OFF | 바이오스 파일이 있으면 사용(두 기기 같게). |
| `mgba_dual_skip_bios` | OFF / ON | 바이오스 첫 화면 건너뛰기(두 기기 같게). |
| `mgba_dual_p2_nocart` | disabled / enabled | 싱글팩: 2P를 팩 없이 켜기(두 기기 같게). |

런타임 파일(모두 램디스크 `/tmp`, 없으면 무시): `/tmp/hb_dual_screen`(`1P` / `2P`, 30장마다 확인) · `/tmp/hb_dual_p2rom`(짝 게임 2P 롬 경로) · `/tmp/hb_ownsave/*`(각자 세이브 교환).

## KNULLI 에 넣기

RG35XX Pro에 우리가 한 방식이에요. 환경이 다르면 자리와 이름을 맞춰 고치세요.

1. **코어 파일.** `mgba_dual_libretro.so`를 SD 카드의 `/userdata/system/hanbang_cores/`(미리 빌드한 파일이 쓰는 기본 자리)에 넣어요.
   그다음 읽기 전용 루트의 `/usr/lib/libretro/mgba_dual_libretro.so`가 그 파일을 가리키게 해요. `mount -o remount,rw /` 뒤에 `ln -sfn /userdata/system/hanbang_cores/mgba_dual_libretro.so /usr/lib/libretro/mgba_dual_libretro.so`, 이어서 `knulli-save-overlay`로 저장해요.
   새 이름이라 순정 mGBA 코어는 건드리지 않아요.
2. **코어 정보 파일.** `/usr/share/libretro/info/mgba_dual_libretro.info`: 순정 `mgba_libretro.info`를 복사해 `display_name = "Nintendo - Game Boy Advance (mGBA Dual)"`, `corename = "mGBA Dual"`로 고치고 `knulli-save-overlay`로 저장해요.
   없으면 에뮬 실행기가 'missing file …info'라며 코어를 켜지 않아요.
3. **ES 기능 표.** ES의 `es_features_*.cfg`(libretro 칸 `<cores>` 안)에 `<core name="mgba_dual" features="netplay" />` 한 줄을 더해 넷플레이 코어로 보이게 해요.
4. **게임별 코어 줄**(`/userdata/system/knulli.conf`): `gba["<롬 파일 이름>.zip"].core=mgba_dual`. 케이블 통신을 하는 GBA 게임에만 넣어요. 나머지는 평소 코어 그대로예요.
5. **게임별 옵션 파일** `/userdata/system/configs/retroarch/config/mGBA Dual/<롬 이름>.opt`: 게임 시작 훅이 켤 때마다 다시 써요.
   ```
   mgba_dual_screen = "1P"          # 손님이면 "2P"
   mgba_dual_use_bios = "ON"
   mgba_dual_skip_bios = "ON"
   mgba_dual_p2_nocart = "enabled"  # 싱글팩 게임만
   ```
6. **바이오스.** `/userdata/bios/gba_bios.bin`을 **두 기기에서 같은 파일**로 넣어요. 싱글팩은 진짜 바이오스가 꼭 필요해요.
7. **같이 쓰는 스크립트**(이 저장소의 [`knulli-scripts/`](../../knulli-scripts/) 폴더). 훅만 빼고 `/userdata/system/claude/`(미리 빌드한 파일이 쓰는 기본 자리)에 복사해요.
   - [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh)는 ES 게임 시작 · 종료 훅이고 `/userdata/system/scripts/nds_save_sync.sh`(미리 빌드한 파일이 쓰는 기본 자리)에 둬요. `.opt`를 쓰고 아래 스크립트들을 띄워요. 그 폴더에는 실행 파일이 이것 하나만 있어야 해요. exFAT라 모든 파일이 실행되기 때문이에요.
   - [`hb_direct.py`](../../knulli-scripts/hb_direct.py)는 방장 · 손님 역할을 보고 `/tmp/hb_dual_screen`에 1P / 2P를 써요.
   - [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py)는 손님 창('같은 게임 방이 열려 있어요')이에요. 짝 게임이면 2P 롬(`/tmp/hb_dual_p2rom`)도 챙기고 손님 세이브를 보내요.
   - [`hb_ownsave.py`](../../knulli-scripts/hb_ownsave.py)는 각자 자기 세이브를 주고받아요(요청 · 확인 · 되쓰기).
   - [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py)는 넷플레이 중 방장 세이브를 카드에 써 줘요.
8. **두 기기를 함께** 바꿔요. 판이 다르면 상태가 거절돼요. 게임 중이 아닐 때 옛 파일 옆에 새 파일을 올려 md5를 확인한 뒤 바꾸세요.

### 다른 기기 · OS에서 쓸 때 주의

- 이 .so는 **aarch64 리눅스 전용**이에요(glibc 심볼 판은 GLIBC_2.35까지만 써요). 다른 곳에서는 소스 패치로 다시 빌드하세요. 맥 arm64로 시험 도구용 빌드는 해 봤고, 윈도우 · 안드로이드는 해 보지 않았어요.
- 상태 형식이 **mGBA와 달라요**(고정 크기, 두 코어 + 드라이버 + 세이브). 순정 mGBA 코어와 상태를 주고받을 수 없고, 이 코어의 판끼리도 판 칸(`0x100` 링크 박자 · `0x200` 짝 · `0x400` 팩 없음)이 다르면 서로 거절해요.
- **같은 롬 두 대**가 기본이에요. 다른 판끼리(짝 게임)는 도우미 스크립트가 `/tmp/hb_dual_p2rom`과 방장 쪽 요청(`HBQ4`)을 만들어야 해요. 스크립트가 없으면 쓸 수 없는 기능이에요.
- **각자 자기 세이브 · 짝 게임 · 싱글팩의 손님 처리는 도우미 스크립트(`hb_ownsave.py` · `hb_joinask.py`)와 KNULLI 실행기(레트로아크 기록 파이프)를 전제로** 만들었어요.
  코어는 `/tmp/hb_ownsave`의 파일이 없으면 평범한 두 대 코어로 동작해요(손님은 `mgba_dual_screen=2P`로 직접 설정). 리눅스 전용 코드(`/proc/self/cmdline`, `/proc/net/tcp` 읽기)가 들어 있어 다른 OS에서는 시험하지 않았어요.
- 싱글팩은 **진짜 GBA 바이오스**(두 기기 같은 파일)와 `mgba_dual_use_bios=ON`이 필요해요. 없으면 2P를 팩으로 켜서 예전처럼(1.5와 같이) 돼요.
- 두 GBA를 한 코어에서 돌려 **한 대짜리 코어보다 무거워요**. H700 기준 실시간의 약 3.5배 속도로 추정하고, 되감기에 여유는 있었어요. 더 느린 기기는 직접 확인하세요.
- 3 · 4인 통신, 무선 어댑터(RFU) 게임, e-Reader, 게임큐브 연결은 이 코어의 대상이 아니고 시험하지도 않았어요(포켓몬 파이어레드 · 리프그린 무선은 [`gba-gpsp-rfu`](../gba-gpsp-rfu/README.ko.md) 코어).
- 기기 훅이 게임별 `.opt`를 통째로 다시 쓰면 싱글팩 줄이 사라질 수 있어요. 훅(`nds_save_sync.sh`)이 그 줄을 이어 쓰게 해 두었어요.
- 혼자 할 때 보이지 않는 2P가 '연결됨'으로 보이는 게임이 있어요(통신 메뉴에 들어가면 상대가 있는 것처럼 보임).

## 소스에서 빌드

기록된 방식 그대로예요. 빌드 기계는 Debian 12(aarch64, gcc 12.2, cmake 3.25)였어요.
결과 .so는 libc · libm만 쓰고, glibc 심볼 판은 GLIBC_2.35까지만 쓰고, `retro_*` 심볼 25개만 내보내요.

```sh
# 패치(이 저장소)
git clone https://github.com/Squirbie/handheld-link-cores.git
CORE="$PWD/handheld-link-cores/cores/gba-mgba-dual"

# 기준 커밋의 원본
git clone https://github.com/libretro/mgba.git
cd mgba
git checkout 7a12d6d4b9acb14c0ae62c9166b6a2f3d08007f6

# (가) 개별 패치를 차례대로
for p in $(grep -v '^#' "$CORE/patches/series"); do git apply "$CORE/patches/$p"; done
# (나) 또는 한 덩어리(둘 다 하지 마세요)
# git apply "$CORE/patches/all-in-one/mgba-dual-1.6-os4-vs-libretro-mgba-7a12d6d4.patch"

cmake -S . -B build -DLIBMGBA_ONLY=ON -DBUILD_LIBRETRO=ON -DLIBRETRO_DUAL=ON -DM_CORE_GB=OFF \
      -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS=-mcpu=cortex-a53
cmake --build build --target mgba_libretro -j2
strip --strip-unneeded build/mgba_dual_libretro.so
```

- `-mcpu=cortex-a53`은 RG35XX Pro(H700)용이에요. 다른 CPU에서는 빼거나 바꾸세요.
- 패치는 `patch -p1`로도 얹혀요.
- 컴파일러가 다르면 바이트까지 같은 .so는 안 나와요. 판 글자(`1.6-os4 (mGBA 7a12d6d4)`)로 확인하세요.

### 다시 만들 수 있는지

- 원본 트리 해시 `8ccf4fd1929aafd9211b19d6dec771a33f43299a`가 GitHub의 값과 같아요. 나중에 말투를 고친 코드 주석 몇 줄을 빼면, 패치를 얹은 소스가 기록된 빌드 소스와 같아요. 패치 0001 ~ 0009를 얹으면 빌드에 쓴 개발 가지의 트리와 같고, 중간 단계 결과는 파일 지문이 같아요(1.3-os4 단계의 `libretro_dual.c` · `sio.c` · `lockstep.h`, 1.5 · 1.6 단계의 `libretro_dual.c` · `hb_ownsave.h`).
- git apply 차례 · git apply 한 덩어리 · patch -p1 차례, 세 방식 모두 같은 트리가 나와요.
- **못 한 것:** 이 폴더를 만들 때 코어를 **다시 컴파일하지 않았어요**. 그래서 바이트까지 같은 .so가 나오는지는 확인하지 못했고, 대신 단계별 소스 파일 지문과 .so 안의 판 글자(`1.6-os4 (mGBA 7a12d6d4)`)를 확인했어요.
- 최종 소스 트리 통째의 사본이 남아 있지 않아서(개발 때 빌드용 가상 머신 안에만 있었어요), 바뀐 파일의 지문으로 대조했어요.
- 순정 mGBA 최신판으로 옮기는 일은 하지 않았어요.

## 패치

이 순서대로 얹어요. `patches/series`에 같은 순서가 적혀 있어요. 한 덩어리로 쓰려면 `patches/all-in-one/mgba-dual-1.6-os4-vs-libretro-mgba-7a12d6d4.patch` 하나만 쓰세요(개별 패치와 같이 쓰면 두 번 얹혀요).

기준: libretro/mgba 커밋 `7a12d6d4b9acb14c0ae62c9166b6a2f3d08007f6`(2026-09-16, "Libretro: Disable debug logging noise"), 트리 해시 `8ccf4fd1929aafd9211b19d6dec771a33f43299a`.

패치 0001 ~ 0005는 tangobattle/mgba(MPL-2.0)에서 가져온 커밋 다섯 개예요. 원작자는 그 저장소 기록에 있어요.

| 패치 | tangobattle/mgba 커밋 | 날짜 | 제목 |
|---|---|---|---|
| 0001 | `2db16a6053f7da68fc485589a4426825b6341f50` | 2026-07-17 | GBA SIO: cooperative-lockstep + savestate-exactness fork delta |
| 0002 | `7dc7c64a176bfcf4abfefe9aefe5e413246da771` | 2026-07-18 | GBA SIO: shared clocks survive the int32 cycle wrap (lockstep.c 부분만) |
| 0003 | `7bd57294a4af5b7998b043faacf80b2bb777cfcf` | 2026-07-20 | GBA Audio: savestates roundtrip the mix exactly |
| 0004 | `69a8ab2ee138c63449f17df0967adbe18760b560` | 2026-07-20 | GBA Audio: re-land the full decoded-PSG savestate exactness patch |
| 0005 | `89e7fd7ff21e369f325fba9ef8b486510a1eebc9` | 2026-07-20 | GBA Audio: restore the master-enable field on load |

| 순서 | 파일 | 하는 일 | 이 단계까지 만든 판 |
|---|---|---|---|
| 1 | [`0001-gba-sio-cooperative-lockstep-savestate-exactness.patch`](patches/0001-gba-sio-cooperative-lockstep-savestate-exactness.patch) | 협력식 lockstep + 상태 정확성 (tangobattle) | |
| 2 | [`0002-gba-sio-lockstep-int32-cycle-wrap.patch`](patches/0002-gba-sio-lockstep-int32-cycle-wrap.patch) | 시계 int32 넘침 방지 (tangobattle) | |
| 3 | [`0003-gba-audio-savestate-mix-roundtrip.patch`](patches/0003-gba-audio-savestate-mix-roundtrip.patch) | 소리 섞기 상태 왕복 (tangobattle) | |
| 4 | [`0004-gba-audio-decoded-psg-savestate.patch`](patches/0004-gba-audio-decoded-psg-savestate.patch) | PSG 해석값 전부 저장 (tangobattle) | |
| 5 | [`0005-gba-audio-restore-master-enable.patch`](patches/0005-gba-audio-restore-master-enable.patch) | 소리 켜짐 값 복원 (tangobattle) | |
| 6 | [`0006-libretro-add-mgba-dual-core.patch`](patches/0006-libretro-add-mgba-dual-core.patch) | 새 앞단 `mgba_dual_libretro` | 1.0 |
| 7 | [`0007-dual-p2-save-name-inside-archive.patch`](patches/0007-dual-p2-save-name-inside-archive.patch) | 압축 파일 안 롬 이름으로 2P 세이브 이름 | |
| 8 | [`0008-gba-io-restore-rcnt-link-pins-on-load.patch`](patches/0008-gba-io-restore-rcnt-link-pins-on-load.patch) | RCNT 연결선 비트 복원 | |
| 9 | [`0009-dual-p2-save-without-atomic-rename.patch`](patches/0009-dual-p2-save-without-atomic-rename.patch) | rename 안 되는 파일 시스템에서 2P 세이브 | |
| 10 | [`0010-gba-sio-clock-selection-and-unprepared-peers.patch`](patches/0010-gba-sio-clock-selection-and-unprepared-peers.patch) | 클록 선택 · 준비 안 된 상대 | |
| 11 | [`0011-gba-rollback-vram-contention-and-sio-events.patch`](patches/0011-gba-rollback-vram-contention-and-sio-events.patch) | 되감기: VRAM 경합 · SIO 이벤트 순서 | |
| 12 | [`0012-dual-link-off-single-gba.patch`](patches/0012-dual-link-off-single-gba.patch) | `mgba_dual_link` 옵션 | 1.1-rbfix |
| 13 | [`0013-dual-screen-file-runtime-selection.patch`](patches/0013-dual-screen-file-runtime-selection.patch) | 1P / 2P 화면을 파일로 고름 | 1.1-rbfix-screenfile |
| 14 | [`0014-dual-guest-own-save.patch`](patches/0014-dual-guest-own-save.patch) | 각자 자기 세이브 | 1.2-ownsave |
| 15 | [`0015-dual-ownsave-harden.patch`](patches/0015-dual-ownsave-harden.patch) | 각자 세이브 점검 12가지 | 1.3-os4, md5 `818fa42f` |
| 16 | [`0016-gba-sio-link-timing-sd-and-start-bit.patch`](patches/0016-gba-sio-link-timing-sd-and-start-bit.patch) | 링크 박자 (SD 선 · 시작 비트 0) | 1.4-os4, md5 `4d4ab1c7` |
| 17 | [`0017-dual-zero-current-samples-in-link-states.patch`](patches/0017-dual-zero-current-samples-in-link-states.patch) | 출력용 소리 샘플 수 0 | 1.4.1-os4, md5 `2af4a20c` |
| 18 | [`0018-dual-pair-game-different-rom-for-2p.patch`](patches/0018-dual-pair-game-different-rom-for-2p.patch) | 짝 게임 | 1.5-os4, md5 `2119a22f` |
| 19 | [`0019-dual-singlepak-2p-without-cartridge.patch`](patches/0019-dual-singlepak-2p-without-cartridge.patch) | 싱글팩 | 1.6-os4, md5 `df34be2b` |

- 각 패치 머리말(`Subject` · `Origin` · 짧은 요약 · 설명)에 무엇을 왜 바꿨는지 있어요.
- md5는 그 단계에서 만든 .so의 앞 8자리예요. `1.6-os4` 앞 판들의 값은 개발 기록에서 가져온 값이고, 최종판만 이 폴더의 대상 파일과 같아요.
- 개발 때의 패치 하나는 기기에 넣지 않은 판이라 뺐어요(2P 세이브가 없으면 1P 세이브를 복사하는 실험). 위 번호는 기기에 들어간 순서를 따라요.

## 원본에 보내기

- 확인하지 않은 것: libretro/mgba `master`가 기준 커밋(`7a12d6d`) 뒤에 어떻게 움직였는지.
- **원본에 보낼 만한가요? 아니요.** 원본에 보낼 만한 독립 버그 고침이 아니에요. 핵심(0001 ~ 0005)은 tangobattle/mgba의 협력식 lockstep 코드이고, 나머지 고침은 그 코드와 새 앞단(`mgba_dual`) 위에서만 뜻이 있어요.
  각자 세이브 · 짝 게임 · 싱글팩은 KNULLI 도우미 스크립트에 기대는 기능이고, 상태 형식의 예약 칸(VRAM 경합 마스크 등)을 써서 순정 mGBA와 상태가 호환되지 않아요.
- 굳이 제안한다면 tangobattle/mgba 쪽에 링크 박자(SD 선 · 시작 비트 0) 고침(패치 0010 · 0016) 정도예요.

## 라이선스

- mGBA와 같은 **MPL-2.0**이에요(원문: [`LICENSES/mgba_LICENSE`](../../LICENSES/mgba_LICENSE)). 새 파일(`src/platform/libretro/dual/*`)도 MPL-2.0 머리말을 달았고, tangobattle/mgba에서 가져온 부분도 MPL-2.0이에요. 패치는 원본 라이선스를 따라요.
- 원본 파일 머리말의 저작권 표시(예: mGBA 저작권자)는 그대로 둬야 해요. 코어(.so)를 나눠 줄 때는 수정한 파일의 소스를 함께 제공해야 하는데, 원본 커밋과 이 패치가 그 소스예요.
