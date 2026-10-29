<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# FBNeo — 가벼워진 넷플레이 상태와 고친 입력표

> 기계어 9바이트만 고친 FBNeo 레트로아크 코어예요. Taito F3 넷플레이 상태를 작고 안정적으로 만들고, 한 오락실 게임의 2P 입력표 오류를 바로잡았어요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/arcade-fbneo-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| 코어 파일 | `fbneo_libretro.so`, 77,036,704 바이트, aarch64 리눅스 (릴리스 zip `arcade-fbneo-linux-aarch64.zip` 안에 있어요) |
| 버전 | 버전 표시 `v1.0.0.03 74a979724` 그대로예요(바뀐 바이트는 9개뿐이에요). 원래 코어 `fa5feb62b5d8c4f9a71786bc649409cd` 를 두 단계로 고쳤고, 중간 판 `9e31af9441611566af6d61cee10a1e7b` 를 거쳐 이 파일이 나와요(기록 속 이름: "FBNeo c942499f") |
| md5 | `c942499fc72a61400d4e6a486841fb37`<br>sha256 `49dba24f3742618a8849deffd1ced19f6f4706154dc7df3fce837b54eb1f4d0b` |
| 원본 | [libretro/FBNeo](https://github.com/libretro/FBNeo) 커밋 `74a9797` ("(libretro) update files", 2025-03-01). 같은 커밋이 드라이버가 있는 [finalburnneo/FBNeo](https://github.com/finalburnneo/FBNeo) 에도 있어요. 전체 해시: `74a979724da9a3c4c8986076123c3293861614c5` |
| 라이선스 | FBNeo **비상업** 라이선스. 쓰는 것은 자유지만 **팔 수 없어요**. [라이선스](#라이선스) 참고 |
| 시험한 기기 | Anbernic RG35XX Pro (H700, aarch64, RAM 1GB) · KNULLI · RetroArch 1.22 |

> 이 코어는 FBNeo 의 **비공식 수정판**이에요. 이 판의 문제를 원본 개발자에게 물어보지 마세요. ROM · BIOS · 세이브는 이 저장소에 없어요. ROM 은 직접 가진 것만 쓰세요.

## 무엇을 하나

FBNeo 는 레트로아크의 올인원 오락실 코어예요. 우리는 이 코어를 다시 빌드하지 않고, 기기에 들어 있던 파일에서 9바이트만 직접 고쳐 두 가지 문제를 풀었어요.

- **Taito F3 넷플레이가 갈라지고 무거웠어요.** 넷플레이에서는 방장이 자기 상태를 손님에게 보내요. 그런데 게임 설정과 최고 점수가 든 작은 저장 칩(EEPROM)이 그 상태에 들어 있지 않아서 두 쪽의 값이 달랐고, 곧 화면과 진행이 어긋났어요. 상태도 쓸데없이 컸어요(4.8MB. FBNeo 의 F3 에뮬이 쓰지도 않는 4MB 짜리 DSP 지연 메모리까지 담았거든요). 되감기가 장마다 상태를 복사하기 때문에 방장은 메모리를 약 710MB(가상 머신에서 잰 값) 썼고, 램이 1GB 인 기기에는 버거웠어요. 게다가 되감기 뒤나 손님이 방장 상태를 불러올 때 동전이 사라지거나 어긋나기도 했어요.
- **한 오락실 게임(`grainbow`)에서 2P 위 · 아래가 안 먹었어요.** 2P 의 위(뛰기)와 아래(숙이기)가 아예 동작하지 않았어요. 게임의 입력표에서 다른 단추가 같은 비트를 가리키고 있었기 때문이에요.

고친 곳이 아주 작아서 패치는 소스 패치가 아니라 **파이썬 스크립트 2개**예요.

## 무엇을 고쳤나

원래 코어는 기기 이미지에 들어 있던 파일이에요. md5 `fa5feb62b5d8c4f9a71786bc649409cd`, 버전 표시 `v1.0.0.03 74a979724`, GCC `Ubuntu/Linaro 7.5.0` 로 빌드된 것이에요. 우리가 빌드한 게 아니고, 어느 빌드 서버에서 어떤 명령으로 나왔는지도 확인하지 못했어요. **그래서 바이트 패치는 이 정확한 파일에만 맞아요.**

순서는 원래 코어 `fa5feb62` → 1단계 `patch_fbneo.py` → `9e31af94` → 2단계 `patch_grainbow.py` → **`c942499f`** 예요. 아래 자리(파일 오프셋)는 0부터 센 값이에요.

1. **`eeprom`: EEPROM 이 넷플레이 상태에 실려요** (`patch_fbneo.py`, 파일 오프셋 `0x158ce60` 명령 1개, 실제로 바뀌는 바이트는 `0x158ce62` 하나). `EEPROMScan` 은 `eeprom_data`(EEPROM 1,024바이트)를 미리 실행 맥락(`ACB_RUNAHEAD`, 비트 7)에서만 상태에 담았어요. `tbnz w24,#7` 을 `tbnz w24,#9` 로 바꿔서 넷플레이용 상태 맥락(`ACB_NET_OPT`, 비트 9)으로 옮겼어요. 미리 실행을 안 쓰는 기기에서는 일반 상태 모양이 그대로예요. **이 고침은 F3 만이 아니라 EEPROM 을 쓰는 FBNeo 게임 모두에 적용돼요.**
2. **`dram`: 쓰지 않는 4MB 를 뺐어요** (`patch_fbneo.py`, 파일 오프셋 `0x2743940`, 바이트 2개). Taito F3 `DrvScan` 은 "All Ram" 을 시작부터 `TaitoRamEnd` 까지 담았는데, 여기에 4MB 짜리 `TaitoES5510DRAM` 지연 메모리가 들어 있어요. FBNeo 의 ES5510 은 DSP 를 돌리지 않아서 이 메모리를 쓰지 않아요. `ldr x6,[x4,#2632]` 를 `ldr x6,[x4,#4560]` 로 바꿔, 길이가 `TaitoES5510DRAM` 시작에서 끝나게 했어요. 상태가 4,825,160 에서 631,880 바이트로 줄어요. **F3 게임의 일반 상태 저장 모양도 바뀌어요.** 옛 F3 상태 파일은 못 읽어요.
3. **`coin`: 동전을 '누르는 동안' 신호로** (`patch_fbneo.py`, 파일 오프셋 `0x2742f0c`, 바이트 4개). F3 `DrvFrame` 은 `previous_coin`(앞 장의 동전 값. 상태에 안 담기는 정적 변수)을 써서 '앞 장에 안 눌렀을 때만' 동전을 인정했어요. 그래서 되감기 뒤나 손님이 방장 상태를 불러올 때 동전이 사라지거나 어긋났어요. `ldrb w17,[x9,#48]` 를 `mov w17,#0` 으로 바꿔 앞 장 값이 늘 0 으로 읽히게 했고, 누르는 동안 신호가 그대로 나가요(MAME 의 F3 와 같은 방식이에요).
4. **`grainbow`: 입력표** (`patch_grainbow.py`, 파일 오프셋 `0x29c768` · `0x29c9a8`, 바이트 1개씩). `d_legionna.cpp` 의 `GrainbowInputList` 에서 `P3 Start` · `P4 Start` 가 `P2 Up` · `P2 Down` 과 같은 비트(`DrvJoy1+8` · `DrvJoy1+9`)를 가리켰어요. 표의 재배치 덧셈값 두 개를 `DrvJoy1+8` · `DrvJoy1+9` 에서 `DrvJoy3+8` · `DrvJoy3+9` 로 바꿨어요(`f8` → `d8`, `f9` → `d9`). 진짜 START3 · START4 비트로, 시스템 포트 `0x10074c` 의 `0x0100` · `0x0200` 이고 `DrvJoy3` 비트 8 · 9 예요.

두 스크립트에는 **안전 장치**가 있어요. `patch_fbneo.py` 는 입력 파일 md5 가 `fa5feb62b5d8c4f9a71786bc649409cd` 이고 바꿀 자리의 옛 값이 맞을 때만 바꿔요. `patch_grainbow.py` 는 입력표를 찾아 정확히 하나로 정해질 때만 바꿔요. 아니면 아무것도 쓰지 않고 끝나요.

### 확인한 것 (측정)

| 무엇 | 결과 |
|---|---|
| 스크립트를 순서대로 돌리면 | 원래 코어 `fa5feb62` 가 `9e31af9441611566af6d61cee10a1e7b` 를 거쳐 **`c942499fc72a61400d4e6a486841fb37`** 이 정확히 나오고, 기기에 들어간 파일과 바이트까지 같아요(2026-10-29 다시 확인). |
| F3 넷플레이 (가상 머신에서 레트로아크 1.22.2 두 개를 이어 장마다 상태 CRC 비교) | 원래 코어: EEPROM 이 상태에 없어 손님이 갈라져요. `eeprom` 만: 동전으로 갈라져요. **셋 모두: 3,500장 넘게 게임 상태 갈라짐 없음**(소리 칩 쪽만 달랐어요). 상태 4,825,160 → 631,880 바이트, 방장 메모리 약 710MB → 약 200MB, 상태 저장 한 번 1.08ms → 0.13ms(가상 머신). |
| 함께 쓴 설정 | 게임별 `netplay_input_latency_frames_min=2` · `netplay_input_latency_frames_range=2` (입력 지연 2 / 2). 되감기 횟수가 44~61% 줄었어요. |
| F3 가 아닌 Taito 게임 1종 | 원래 코어에서도 게임 상태가 갈라지지 않았어요(소리 칩 속 값만 달랐어요). 이 패치 대상이 아니에요. |
| 두 기기 실기 | F3 대표 한 판: 동전 · 화면이 같고, 초당 54장(혼자 할 때와 같아요), 방장 램 약 330MB (2026-10-25). 입력표 고침판을 두 기기에 넣고 한 기기에서 켜 확인했어요(2026-10-26). |
| 입력표 고침 | 서비스 메뉴 입력 시험 화면에서 원래 코어는 P3 START 가 `P-2 UP` 칸을, P4 START 가 `P-2 DOWN` 칸을 켰고, 고친 코어는 ST3 · ST4 칸이 켜져요. 40장 입력 시험에서 2P 위 · 아래를 눌렀을 때의 화면 변화 점수가 원래 코어 0 에서 고친 코어 1221 · 1671 이 됐어요. 다른 9게임은 화면 · 상태 해시가 같았어요. |

### 한계

- `eeprom` 고침은 손님 기기의 EEPROM(설정 · 최고 점수)을 **방장 것으로 바꿔 놓아요.** 게임이 끝날 때 손님 기기에 방장 값이 저장될 수 있어서, 손님의 `.nv` · `.fs` 저장 파일을 끝난 뒤 되돌리는 훅을 같이 썼어요([같이 쓰는 스크립트](#같이-쓰는-스크립트) 참고).
- `coin` 고침은 동전 신호 방식이 바뀌어요. 두 기기 크레디트 수가 같아지는 것은 확인했지만, '한 번 누르면 정확히 1 크레디트'인지는 따로 확인한 기록이 없어요.
- `dram` 고침 뒤에는 **F3 게임의 옛 상태 파일을 못 읽어요**(넣기 전에 F3 상태 저장 파일이 두 기기에 0개인 것을 확인했어요).
- 입력표 고침으로 이 게임이 3인용이 되는 건 아니에요. 원작은 2인용이고, P3 · P4 START 는 서비스 메뉴 입력 시험 칸에만 보여요.
- 소스로 새로 빌드해 시험한 것이 아니라 **이미 빌드된 파일을 고친 것**이에요. [소스에서 빌드](#소스에서-빌드)의 소스 수정은 같은 뜻이지만 컴파일해 시험하지는 않았어요.

## 코어 옵션

추가하거나 바꾼 옵션은 없어요. 함께 쓴 게임별 레트로아크 설정은 아래 넣는 법 4번에 있어요.

## KNULLI 에 넣기

[최신 릴리스](https://github.com/Squirbie/handheld-link-cores/releases/latest)에서 `arcade-fbneo-linux-aarch64.zip` 을 받아 풀어 주세요. 우리가 넣은 방식은 이래요.

1. **파일 자리**: `/userdata/system/hanbang_cores/fbneo_libretro.so` (미리 빌드한 파일이 쓰는 기본 자리), SD 카드 쪽이에요. 레트로아크가 찾는 `/usr/lib/libretro/fbneo_libretro.so` 는 이 파일로 가는 **바로가기(심볼릭 링크)** 예요. 코어를 SD 쪽에 두는 이유와 폴더를 지우면 안 되는 이유는 [MAME 폴더](../arcade-mame2003-plus/README.ko.md#knulli-에-넣기)와 같아요.
2. **바꾸는 순서**: 게임이 안 돌고 있을 때(EmulationStation 의 로컬 웹 API `runningGame` 이 "NO GAME")만 바꿔요. 새 파일을 `fbneo_libretro.so.hbnew` 로 보내고 md5 를 확인한 뒤 `chmod 755`, `mv -f`, `sync` 해요. 원래 파일은 기기 안에 `fbneo_libretro.so.old_<md5 앞 8자리>` 로 보관해 두었어요.
3. **두 기기는 같은 파일**이어야 해요. F3 는 상태 크기가 달라지니 한쪽만 바뀌면 붙지 않거나 어긋나요.
4. **게임별 설정** (`knulli.conf`): 시험한 Taito 게임 세 개(F3 두 개 + 8비트 보드 한 개)에 두 줄을 넣었어요. `arcade["<ROM 이름>.zip"].retroarch.netplay_input_latency_frames_min=2` 와 `arcade["<ROM 이름>.zip"].retroarch.netplay_input_latency_frames_range=2`
5. **손님 저장 지키기**: `eeprom` 고침 때문에 손님의 EEPROM · NVRAM 이 방장 값으로 써지니 훅 스크립트도 같이 두세요([같이 쓰는 스크립트](#같이-쓰는-스크립트) 참고).
6. **확인**: md5. 되돌리려면 보관한 파일을 다시 놓으세요.

### 다른 기기 · OS 에서 쓸 때 주의

- **`patch_fbneo.py` 는 원래 코어 `fa5feb62b5d8c4f9a71786bc649409cd` 에만 맞아요.** 다른 FBNeo 빌드(버전 · 컴파일러 · 레트로아크 빌드 서버가 다른 것)는 오프셋이 달라 스크립트가 멈춰요. 억지로 값을 바꾸지 마세요. `patch_grainbow.py` 는 입력표를 찾는 방식이라 같은 구조의 다른 aarch64 FBNeo 빌드에서도 될 수 있지만, 이 빌드에서만 확인했어요.
- 파일은 aarch64 리눅스 전용이에요(glibc 2.17 이상이면 돼요). 다른 CPU · OS 는 소스를 그 기기용으로 빌드하세요.
- 두 기기는 **같은 파일**일 때만 시험했어요. `dram` 때문에 F3 상태 모양이 원본과 달라요.
- `eeprom` 고침 때문에 **손님 기기의 저장 파일이 방장 값으로 덮여요.** 각자 자기 휴대 게임기에 자기 저장을 지켜야 한다면 반드시 훅(또는 같은 일을 하는 것)이 필요해요.
- `eeprom` 은 EEPROM 을 쓰는 FBNeo 게임 모두에 영향을 주고(상태에 EEPROM 1KB 가 더 들어가요), `dram` · `coin` 은 Taito F3 에만 영향을 줘요. 네오지오는 `EEPROMScan` 을 부르지 않고 F3 도 아니라서 바뀐 코드가 돌지 않는다고 분석했어요(그쪽 게임을 따로 시험하지는 않았어요).
- 기기에는 이 코어와 별개로 더 새로운 공식 FBNeo 코어(`fbneo2026`)도 들어 있었어요. 그쪽은 안 고쳤어요.

### 같이 쓰는 스크립트

둘 다 저장소의 [`knulli-scripts/`](../../knulli-scripts/) 에 있어요.

- [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) — 게임 시작 · 끝 훅이에요. 그 안의 23번(FBNeo 넷플레이 손님의 `.nv` · `.fs` 지키기)이 `eeprom` 고침의 짝이에요. 훅은 `/userdata/system/scripts/nds_save_sync.sh` (미리 빌드한 파일이 쓰는 기본 자리)에, 나머지 스크립트는 `/userdata/system/claude/` (미리 빌드한 파일이 쓰는 기본 자리)에 두세요.
- [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py) — 넷플레이 중 게임 속 저장을 바로 파일로 써요(위 훅이 손님 표시를 이 파일로 넘겨요).

## 소스에서 빌드

컴파일할 것이 없어요. 올라가 있는 파일은 원래 바이너리에서 9바이트만 바꾼 것이라 패치가 파이썬 스크립트 2개예요. 파이썬 3 만 있으면 돼요(`python3 -I` 로 돌리면 돼요).

```sh
python3 -I patches/patch_fbneo.py    <원래 fbneo_libretro.so, md5 fa5feb62b5d8c4f9a71786bc649409cd>  step1.so            # md5 9e31af9441611566af6d61cee10a1e7b
python3 -I patches/patch_grainbow.py step1.so                                                         fbneo_libretro.so   # md5 c942499fc72a61400d4e6a486841fb37
```

- `patch_fbneo.py` 는 세 가지(`eeprom` · `dram` · `coin`)를 한꺼번에 넣어요. 셋째 인자(`eeprom,dram,coin` 중 골라서 쉼표로 이은 것)로 일부만 넣을 수도 있어요.
- 두 스크립트 모두 파일을 새로 써요(원래 파일은 그대로예요).
- 원래 코어 `fa5feb62` 는 기기 이미지에 들어 있던 미리 빌드된 파일이에요. 어느 빌드 서버에서 어떤 명령으로 나왔는지 모르기 때문에, 바이트 패치는 이 정확한 파일에만 맞아요.

### 소스로 고치려면 (참고)

바이트 패치를 쓸 수 없는 빌드라면 같은 뜻의 소스 수정이에요. 경로는 2026-10-29 원본 `master` 에서 확인했고, 컴파일 · 시험은 안 했어요.

- `src/burn/drv/pst90s/d_legionna.cpp` — `GrainbowInputList` 의 `P3 Start` · `P4 Start` 를 `DrvJoy3 + 8` · `DrvJoy3 + 9` 로.
- `src/burn/devices/eeprom.cpp` — `EEPROMScan` 이 `eeprom_data` 를 `ACB_RUNAHEAD` 뿐 아니라 `ACB_NET_OPT` 일 때도 담게(우리 바이너리 패치는 앞의 것을 뒤의 것으로 바꿨어요).
- `src/burn/drv/taito/d_taitof3.cpp` — `DrvScan` 의 "All Ram" 길이에서 `TaitoES5510DRAM` 블록을 빼고, `previous_coin` 을 상태에 넣거나(`SCAN_VAR`) 우리처럼 쓰지 않게.

## 패치

[`patches/series`](patches/series) 의 순서대로 돌려요. 스크립트 머리의 주석은 한국어예요.

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `patches/patch_fbneo.py` | 원래 코어의 세 자리(`eeprom` · `dram` · `coin`, 바이트 7개)를 바이트로 고쳐요. 입력 파일 md5 가 `fa5feb62b5d8c4f9a71786bc649409cd` 이고 바꿀 자리마다 옛 값이 맞을 때만 써요. 결과 md5: `9e31af9441611566af6d61cee10a1e7b`. |
| 2 | `patches/patch_grainbow.py` | `GrainbowInputList` 표를 스스로 찾아 재배치 덧셈값 두 개를 `DrvJoy1+8` · `DrvJoy1+9` 에서 `DrvJoy3+8` · `DrvJoy3+9` 로 바꿔요(바이트 2개). 표가 정확히 하나로 정해질 때만 써요. 결과 md5: `c942499fc72a61400d4e6a486841fb37`. |

### 확인한 것과 못 한 것

- **확인함**: 스크립트 두 개를 순서대로 돌려 원래 코어에서 기기 파일과 바이트까지 같은 결과가 나와요. 원본 `master` 에서 네 곳이 그대로예요. 두 저장소(libretro/FBNeo · finalburnneo/FBNeo)의 커밋 해시가 같아요(API 로 확인, 2026-10-29). 입력표 고침의 근거는 서비스 메뉴 시험 화면과 40장 입력 시험이에요.
- **못 함**: 원래 코어의 출처(빌드 서버 · 명령줄) 확인, 소스에서 새로 빌드해 같은 고침을 시험, `coin` 고침의 '한 번 = 1 크레디트' 확인, F3 넷플레이를 `dram` 만 또는 `coin` 만 따로 넣어 보는 시험(`eeprom` 단독 · `eeprom + dram` · 셋 모두는 해 봤어요).

## 원본에 보내기

2026-10-29 에 원본 `master`(finalburnneo/FBNeo)와 견줘 확인했어요. **네 가지 모두 아직 그대로예요.** 아직 아무것도 보내지 않았어요. 영어 PR 초안과 판단 이유는 [`../MANIFEST.arcade.jsonl`](../MANIFEST.arcade.jsonl) 의 `upstream_pr_candidate` · `more_pr_candidates` 에 있고, [`UPSTREAM.md`](../../UPSTREAM.md) 에 요약돼 있어요.

| 고침 | 원본에서 |
|---|---|
| 입력표 (`grainbow`) | `d_legionna.cpp` 의 `GrainbowInputList` 에 `P3 Start = DrvJoy1 + 8`, `P4 Start = DrvJoy1 + 9` 가 `P2 Up` · `P2 Down` 과 겹친 채 남아 있어요. 이 파일의 마지막 변경은 2026-10-02 예요. |
| `eeprom` | `EEPROMScan` 이 `eeprom_data` 를 `ACB_RUNAHEAD` 안에서만 담아요(녹화용 `ACB_EEPROM` 은 따로예요). `ACB_NET_OPT` 플래그는 있지만 여기엔 안 써요. |
| `dram` | F3 `DrvScan` 의 "All Ram" 이 `TaitoRamStart` ~ `TaitoRamEnd`(ES5510 DRAM 포함) 그대로예요. |
| `coin` | `previous_coin` 이 상태 밖의 `static UINT8` 이고 `SCAN_VAR` 로 안 담겨요. |

- **입력표 고침이 가장 분명한 버그 고침이고, 보낼 만해요.** 두 줄이고 원본에 아직 있어요. 근거는 서비스 메뉴 입력 시험 화면, 40장 입력 시험, MAME 시스템 포트 `0x10074c` 의 START3 · START4(`0x0100` · `0x0200` = `DrvJoy3` 비트 8 · 9), 다른 9게임 확인이에요. 주의할 점은 우리 검증이 미리 빌드된 코어의 2바이트를 바꾼 것이라, 보내기 전에 소스 빌드로 한 번 확인해야 한다는 거예요. 보낼 곳은 드라이버가 있는 finalburnneo/FBNeo 예요.
- **F3 넷플레이 세 가지는 아직 PR 로 보내지 않는 편이 좋아요.** 미리 빌드된 파일에 바이트 패치로 넣어 가상 머신 · 두 기기에서만 시험했고, `coin` 은 동전 신호의 뜻이 바뀌어요(누르는 동안 신호). 소스로 다시 만들어 시험한 뒤, 먼저 이슈로 현상(상태 크기 · 갈라짐 · EEPROM)과 의견을 묻는 편이 좋아요.

## 라이선스

FBNeo 는 **FBNeo 비상업 라이선스**예요(원본 `src/license.txt`. 이 저장소에도 [`LICENSES/FBNeo_src_license.txt`](../../LICENSES/FBNeo_src_license.txt) 로 사본을 두었어요). 이 스크립트 · 고친 코어도 같은 조건이에요. 요점은 이래요.

- 소스든 바이너리든 **팔거나 빌려주거나 돈을 벌려고 쓸 수 없어요.** 이 코어를 넣은 기기나 카드를 돈 받고 파는 것도 안 돼요.
- 소스에 한 **고침은 공개**해야 해요. 이 폴더의 스크립트와 위 설명이 우리 고침이에요.
- 나눌 때 **라이선스 전문을 그대로 함께** 넣어야 해요. 이 저장소의 `LICENSES/` 에 사본이 있으니, 바이너리를 넘길 때 같이 넣으세요.
- ROM 을 같이 나누면 안 돼요(나눌 권리가 있을 때만 괜찮아요). FBNeo 소스를 쓰는 프로젝트를 위해 후원을 요청하면 안 돼요.
- 원래 Final Burn 의 조건(비상업 · 저작권 표시 유지 · 소스 공개 또는 링크)과 MAME 의 라이선스(MAME 코드를 쓴 부분)도 같이 적용돼요.
- 이 폴더의 스크립트는 FBNeo 의 소스를 담지 않지만, 고친 바이너리는 FBNeo 의 파생물이라 위 조건을 따라요.
