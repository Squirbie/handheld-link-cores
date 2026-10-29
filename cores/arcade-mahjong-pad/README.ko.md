<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# 마작 패드 — 키보드로만 되던 오락실 마작을 게임패드로

> FBNeo · MAME 2003-Plus 의 오락실 마작 게임을 키보드 없이 휴대 게임기의 패드로 칠 수 있게 하는, 얇은 레트로아크 감싸개 코어 둘이에요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/arcade-mahjong-pad-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| 코어 파일 | `fbneo_mj_libretro.so` · `mame2003_plus_mj_libretro.so`, 각각 72,584 바이트, aarch64 리눅스 (둘 다 릴리스 zip `arcade-mahjong-pad-linux-aarch64.zip` 안에 있어요) |
| 버전 | 소스 한 파일 [`patches/hb_mjpad.c`](patches/hb_mjpad.c) (md5 `7c721fac65a15a9649bd27464777bb3a`)을 컴파일 옵션만 달리해 두 번 빌드해요. 감싸는 진짜 코어는 `fbneo_libretro.so` ([arcade-fbneo](../arcade-fbneo/README.ko.md), md5 `c942499fc72a61400d4e6a486841fb37`)와 `mame2003_plus_libretro.so` ([arcade-mame2003-plus](../arcade-mame2003-plus/README.ko.md), md5 `5dbeaf459d9c05a5eb175a286c7ed4a7`)예요 |
| md5 | `fbneo_mj_libretro.so`: `92e23de148cb45fb645cc270cba95bfd`<br>`mame2003_plus_mj_libretro.so`: `fb23fd640ae81b3cbdde89ad3d43f4e5`<br>`fbneo_mj_libretro.so` 의 sha256: `543cc430544efda049cae8257d2a2fc185b667567eb878f235abfeb5a5be72e6`<br>`mame2003_plus_mj_libretro.so` 의 sha256: `294b11405fe9059a7c8936f577ac26fbec9bbe9384350180f5c71848dca47974` |
| 원본 | 없어요. 직접 쓴 소스예요. FBNeo · MAME 소스는 한 줄도 안 들어 있고, 실행할 때 진짜 코어 파일을 `dlopen` 으로 열어요 |
| 라이선스 | 감싸는 코어와 같은 조건이에요. `fbneo_mj` 는 FinalBurn Neo 라이선스, `mame2003_plus_mj` 는 MAME 라이선스예요. 둘 다 비상업이라 팔 수 없어요. [라이선스](#라이선스) 참고 |
| 시험한 기기 | Anbernic RG35XX Pro (H700, aarch64) · KNULLI · RetroArch 1.22 |

> ROM · BIOS · 세이브는 이 저장소에 없어요. ROM 은 직접 가진 것만 쓰세요.

## 무엇을 하나

오락실 마작 게임은 마작 키(패를 고르는 A ~ N, 깡 · 퐁 · 치 · 리치 · 론)를 **키보드로만** 읽어요. 휴대 게임기에는 키보드가 없어서 동전 · 시작 단추는 됐지만 패를 버릴 수가 없었어요. 이 감싸개 코어는 진짜 코어(FBNeo 또는 MAME 2003-Plus) 앞에 끼워져서, 코어가 키보드를 물으면 **1P 패드 단추로 대신 답하고**, 화면 아래에 A ~ N 선택 줄을 그려 줘요.

- 십자키 ←/→ 로 화면 아래 줄의 칸(A ~ N)을 고르고, A 단추로 그 패를 버려요.
- 화면 아래 줄은 14칸이에요. 고른 칸은 금색, 나머지는 어둡게 비쳐서 게임의 패 그림이 가려지지 않아요.
- 론 · 리치 · 퐁 · 치 · 깡도 단추 하나씩이에요. 동전(SELECT) · 시작(START)은 원래 코어 그대로예요.
- 마작 키를 키보드로 읽는 오락실 게임 27개(FBNeo 20 · MAME 2003-Plus 7)에 쓰고 있어요.

### 조작

| 단추 | 동작 |
|---|---|
| ← / → | 칸 한 칸씩 옮기기 (누르고 있으면 18장 뒤부터 6장마다 되풀이) |
| ↓ / ↑ | 맨 왼쪽(A) / 맨 오른쪽(N, 쯔모한 패) 칸으로 |
| A | 고른 칸의 키 누르기 (패 버리기 · 메뉴 고르기). 누르기 시작한 칸을 끝까지 붙잡아요 |
| R2 | N(쯔모한 패)을 바로 누르기 |
| B | 론 (`Z`) |
| X | 리치 (`왼쪽 Shift`) |
| Y | 퐁 (`왼쪽 Alt`) |
| L | 치 (`Space`) |
| R | 깡 (`왼쪽 Ctrl`) |
| L2 | 화면 아래 줄 보이기 / 숨기기 |
| SELECT · START | 동전 · 시작 — 진짜 코어 그대로 |

## 무엇을 고쳤나

코어를 고친 것이 아니에요. 코어 앞에 얇게 끼우는 감싸개 코어를 소스 한 파일로 직접 썼어요.

1. **구조**: 두 `.so` 모두 libretro 코어로서 `retro_*` 함수를 내보내요. 처음 불릴 때 진짜 코어를 `dlopen` 하고, `dlsym` 으로 얻은 함수에 모든 호출을 **그대로 넘겨요**(직렬화 · 메모리 · 치트 포함). 가로채는 것은 셋뿐이에요. `retro_set_environment`(화면 형식 `SET_PIXEL_FORMAT` 을 엿봄), `retro_set_video_refresh`(화면 아래 줄 그리기), `retro_set_input_poll` · `retro_set_input_state`(패드를 마작 키로 바꾸기)예요.
2. **입력**: 진짜 코어가 `RETRO_DEVICE_KEYBOARD` 로 묻는 키에 1P 패드(포트 0) 상태로 답해요. `A` ~ `N` 은 고른 칸(또는 R2 의 N)이고, `Z` · `LSHIFT` · `LALT` · `SPACE` · `LCTRL` 은 B · X · Y · L · R 이에요. 키보드가 아닌 질문(조이스틱 등)은 프런트엔드에 그대로 넘겨요. **이 모드에서는 진짜 키보드를 꽂아도 코어에는 안 들어가요**(패드만).
3. **화면**: 소프트웨어로 그려진 장(`XRGB8888` · `RGB565` · `0RGB1555`)을 복사해 맨 아래 7줄에 14칸을 그려요(3×5 점 글씨, 고른 칸은 `0xFEB713` 금색 바탕). 폭 70 미만이거나 높이 40 미만이거나 하드웨어 프레임버퍼면 그리지 않아요.
4. **켜는 조건 (두 판의 유일한 차이)**
   - **FBNeo 판**: 진짜 코어가 **처음 키보드를 물을 때** 켜져요. FBNeo 는 마작 키가 있는 게임에서만 키보드를 물어요. 컨트롤러 정보(`SET_CONTROLLER_INFO`)로는 가를 수 없었어요(FBNeo 가 키보드 칸을 스스로 지워요).
   - **MAME 2003-Plus 판** (`-DHB_MJ_ALWAYS`): 처음부터 켜져요. MAME 2003-Plus 는 입력 방식이 `simultaneous` 일 때 늘 키보드를 묻고(기본 `retropad` 는 키보드를 안 읽어요), 이 코어는 마작 게임에만 쓰니까요.
5. **진짜 코어 자리**: 컴파일 때 `HB_MJ_REAL`(문자열 경로)로 정하고, 실행할 때는 환경 변수 `HB_MJ_REAL` 이 있으면 그것을 써요(시험용). 기본값은 FBNeo 판 `/userdata/system/hanbang_cores/fbneo_libretro.so` (미리 빌드한 파일이 쓰는 기본 자리), MAME 판 `/userdata/system/hanbang_cores/mame2003_plus_libretro.so` 예요. 파일 · 기호 이름의 `hb_` · `HB_` 는 우리가 쓴 코드라는 표시일 뿐이고 이름은 바꾸지 않았어요.
6. **원본 코드 확인** (2026-10-29, `libretro/FBNeo` 의 `src/burner/libretro/retro_input.cpp`): FBNeo 는 입력 이름이 `mah a` ~ `mah n` 인 항목을 `RETROK_a` ~ `RETROK_n` 으로, `kan` = `LCTRL`, `pon` = `LALT`, `chi` = `SPACE`, `reach` = `LSHIFT`, `ron` = `z` 로 묶어요. 이 감싸개의 묶음과 같아요. 플레이어마다 키보드 하나씩(포트 `nMaxPlayers` + 플레이어 번호)으로 만들려던 코드지만 `if (nPlayer > 0) return 0;` 이 있어서 **1P 에게만** 키를 줘요. 바로 위 주석이 https://github.com/finalburnneo/FBNeo/issues/2117 을 가리켜요. 그래서 2인 마작 대전은 이 구성으로 안 돼요(이 게임들은 1인용으로 올려 뒀어요). 감싸개는 키보드 질문이 어느 포트로 오든 1P 패드로 답해요.

### 확인한 것과 못 한 것

- **확인함**: 키를 눌러 보는 가상 머신 시험대에서 마작 키 게임 32개(당시 목록)를 켜 마작 판이 나오는 것을 봤어요.
- **확인함**: 기기에서 FBNeo 마작 한 게임을 동전 넣기 · 1인 고르기부터 대국 진행 · 패 버리기까지(R2 · ←/→ · L2 포함), MAME 마작 두 게임을 크레디트부터 배패 · 대국 진행까지 해 봤어요.
- **확인함**: 이 소스가 두 옵션 모두 경고 없이 컴파일되는 것(맥, `-Wall -Wextra`, 2026-10-29). 원본 FBNeo 의 마작 키 묶음과 이 감싸개의 키 묶음이 같아요.
- **못 함**: 2P 마작, 넷플레이, FBNeo 의 나머지 마작 키(`ff` 등), 감싸개를 빼고 켰을 때와의 속도 비교, 정확한 컴파일 옵션 기록(남아 있지 않아요).

### 한계

- **2P 마작은 안 돼요.** FBNeo 가 2P 마작 키를 아예 안 읽어요.
- FBNeo 가 읽는 나머지 마작 키(`ff` · `lc` · `bet` · `score` · `big` · `small` · `wup`)는 이 감싸개가 답하지 않아요. 이 키가 꼭 필요한 게임은 못 쳐요.
- 조이스틱으로 치는 마작(키보드를 안 쓰는 것)과 조이스틱 모드가 있는 일부 기판 마작은 **감싸개 없이 원래 FBNeo** 가 나아요. 우리도 그렇게 되돌렸어요. KNULLI 설정 생성기가 FBNeo 게임마다 `fbneo-dipswitch-<롬>-Controls=Joystick` 줄을 써 주는데, 감싸개 코어로 켜면 이 줄이 안 써져요.
- 넷플레이는 시험하지 않았어요(2P 마작이 안 돼서 1인용으로 올려 뒀어요).

## 코어 옵션

| 어디서 | 이름 | 값 | 하는 일 |
|---|---|---|---|
| 레트로아크 코어 옵션 (MAME 판, 게임별로 설정) | `mame2003-plus_input_interface` | `simultaneous` | MAME 2003-Plus 는 이 입력 방식에서만 마작 키를 키보드로 읽어요. 기본값 `retropad` 는 키보드를 안 읽어요. |
| 환경 변수 (실행할 때) | `HB_MJ_REAL` | 진짜 코어 `.so` 파일의 경로 | 컴파일 때 박힌 경로를 덮어써요(시험용). |
| 컴파일 정의 | `HB_MJ_REAL` | 문자열 경로, 예: `"/userdata/system/hanbang_cores/fbneo_libretro.so"` | 진짜 코어의 기본 경로를 정해요. |
| 컴파일 정의 | `HB_MJ_ALWAYS` | 정의하거나 안 하거나 | 감싸개가 처음부터 켜져요. MAME 판에 써요. |

## KNULLI 에 넣기

[최신 릴리스](https://github.com/Squirbie/handheld-link-cores/releases/latest)에서 `arcade-mahjong-pad-linux-aarch64.zip` 을 받아 풀어 주세요. 안에 `fbneo_mj_libretro.so` 와 `mame2003_plus_mj_libretro.so` 두 파일이 있어요. 감싸개는 진짜 코어도 함께 넣어야 해요([arcade-fbneo](../arcade-fbneo/README.ko.md), [arcade-mame2003-plus](../arcade-mame2003-plus/README.ko.md) 참고). 우리가 넣은 방식은 이래요.

1. **파일 자리**: 두 `.so` 를 `/userdata/system/hanbang_cores/` (SD 카드 쪽)에 넣고 md5 를 맞춰 본 뒤, `/usr/lib/libretro/` 에 같은 이름의 **바로가기(심볼릭 링크)** 를 만들어요. 감싸는 진짜 코어 파일(`fbneo_libretro.so` · `mame2003_plus_libretro.so`)이 같은 폴더에 **그 이름으로** 있어야 해요(경로가 코어 안에 들어 있어요).
2. **정보 파일**: 새 코어 이름이라 `.info` 가 필요해요. 진짜 코어의 `.info` 를 복사하면서 `display_name` 만 바꿨어요. `Arcade (FinalBurn Neo Mahjong Pad)` · `Arcade (MAME 2003-Plus Mahjong Pad)` (`/usr/share/libretro/info/fbneo_mj_libretro.info`, `mame2003_plus_mj_libretro.info`)예요.
3. **저장**: 시스템 쪽(`/usr`) 바로가기와 `.info` 는 KNULLI 의 덧칠(overlay)에 있으니 `knulli-save-overlay` 로 저장해요.
4. **게임별 줄** (`/userdata/system/knulli.conf`): 아래 '게임 고르기'로 가린 게임마다 넣어요.
   ```
   # FBNeo 마작 키 게임
   arcade["<ROM 이름>.zip"].core=fbneo_mj
   arcade["<ROM 이름>.zip"].emulator=libretro

   # MAME 2003-Plus 마작 키 게임
   arcade["<ROM 이름>.zip"].core=mame2003_plus_mj
   arcade["<ROM 이름>.zip"].emulator=libretro
   arcade["<ROM 이름>.zip"].retroarchcore.mame2003-plus_input_interface=simultaneous
   ```
   이미 다른 코어 줄이 있는 게임은 건드리지 말고 먼저 확인하세요. 고치기 전에는 `knulli.conf` 사본을 기기 안에 남겨 두세요.
5. **되돌리기**: 그 게임의 위 줄들을 지우면 원래 코어로 돌아가요.
6. 메뉴 설명에 조작(←/→ · A · R2 · B · X · Y · L · R · L2)을 적어 두면 좋아요.

### 게임 고르기

코어가 그 게임에서 **마작 키를 키보드로 묻는** 경우에만 감싸개를 쓰세요.

- FBNeo: 입력 목록의 이름이 `mah` 로 시작하는 게임이에요(코어 안에서 `nMahjongKeyboards > 0`).
- MAME 2003-Plus: 마작 키보드 입력 포트가 있는 게임이에요(입력 방식 `simultaneous` 가 필요해요).
- 우리는 가상 머신 시험대에서 코어가 묻는 입력 코드를 기록해 마작 키(`A` ~ `N`)가 있는지로 가렸고, 새 게임을 넣을 때도 같은 방식으로 확인해요.

### 다른 기기 · OS 에서 쓸 때 주의

- **파일은 aarch64 리눅스(glibc 2.34 이상) 전용**이에요. 그 밖의 환경은 소스를 그 기기용으로 빌드하세요. 안드로이드 · 윈도우 · 맥에서는 `dlopen` 경로 · 확장자(`.so`)를 그 OS 에 맞춰야 해요.
- **진짜 코어 경로가 컴파일 때 박혀 있어요.** KNULLI 가 아니면 `-DHB_MJ_REAL` 로 다시 빌드하거나 환경 변수 `HB_MJ_REAL` 로 가리키세요.
- 진짜 코어는 **우리가 고친 판이 아니어도** 돼요(표준 libretro 코어면 되고, 마작 키를 키보드로 읽는 FBNeo / MAME 2003-Plus 에서만 뜻이 있어요). 다만 우리는 위 두 판에서만 시험했어요.
- 프런트엔드는 RetroArch(libretro)여야 하고, MAME 판은 코어 옵션 `mame2003-plus_input_interface = simultaneous` 가 필요해요.
- 키보드가 있는 기기에서는 필요 없어요(오히려 이 모드는 진짜 키보드를 막아요).

## 소스에서 빌드

`libretro.h`(libretro API 헤더, [libretro-common](https://github.com/libretro/libretro-common) · RetroArch 소스에 있어요)가 필요해요. 이 폴더에는 없어요.

```sh
# FBNeo 판 (진짜 코어가 처음 키보드를 물을 때부터 켬)
gcc -O2 -shared -fPIC -I<libretro.h 가 있는 폴더> \
    -DHB_MJ_REAL='"/userdata/system/hanbang_cores/fbneo_libretro.so"' \
    -o fbneo_mj_libretro.so patches/hb_mjpad.c

# MAME 2003-Plus 판 (처음부터 켬)
gcc -O2 -shared -fPIC -I<libretro.h 가 있는 폴더> -DHB_MJ_ALWAYS \
    -DHB_MJ_REAL='"/userdata/system/hanbang_cores/mame2003_plus_libretro.so"' \
    -o mame2003_plus_mj_libretro.so patches/hb_mjpad.c
```

- 우리 빌드의 정확한 명령줄 · 최적화 옵션은 기록에 남아 있지 않아요. 위는 같은 동작을 하는 예시예요(파일 지문이 같게 나온다는 보장은 없어요).
- 우리 파일은 GCC 12.2(Debian 12, aarch64)로 만들었고 필요한 라이브러리는 `libc.so.6` 하나(`GLIBC_2.34`)예요. 더 오래된 glibc 에서는 `-ldl` 을 더 붙여 그 기기에서 빌드하세요.
- 확인: 이 소스가 두 옵션 모두 경고 없이 컴파일되는 것을 맥에서 확인했어요(`-Wall -Wextra`, 2026-10-29).

## 패치

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `patches/hb_mjpad.c` | 감싸개 소스 전체예요(패치가 아니라 완성된 소스). md5 `7c721fac65a15a9649bd27464777bb3a`. 두 코어는 이 한 파일에서 컴파일 옵션(`-DHB_MJ_ALWAYS` 와 컴파일 때 박는 진짜 코어 경로)만 달리해 만들어요. 소스 속 주석은 한국어예요. |

## 원본에 보내기

이 감싸개와 같은 일을 하는 원본 기능은 없어요. 그리고 **보낼 것도 없어요**([`../MANIFEST.arcade.jsonl`](../MANIFEST.arcade.jsonl) 의 `worth` 는 `false` 예요). 문제는 프런트엔드 쪽에 있어요. 패드가 키보드를 대신해야 하는데, 우리 휴대 게임기 단추에 맞춘 외부 감싸개로 풀었기 때문에 코어 안에는 고칠 곳이 없어요. FBNeo 의 레트로아크 입력 코드는 마작 키를 키보드 키로만 묶고 1P 에게만 줘요(위 '원본 코드 확인'). MAME 2003-Plus 는 입력 방식 `simultaneous` 에서 마작 키를 키보드로 읽어요. 원본이 이런 기능을 원한다면 libretro 포트에 패드용 마작 입력 모드를 두는 것이 자연스러운 자리예요.

## 라이선스

`hb_mjpad.c` 는 우리가 쓴 코드이고, **감싸는 코어와 같은 조건**으로 내놓아요. `fbneo_mj` 로 빌드하면 FinalBurn Neo 라이선스, `mame2003_plus_mj` 로 빌드하면 MAME 라이선스를 따라요. 둘 다 비상업 라이선스라서 **팔 수 없어요.**

- 감싸개는 FBNeo · MAME 코드를 하나도 담지 않고 실행할 때 진짜 코어를 `dlopen` 으로 열어요. 그래도 감싸개와 진짜 코어를 함께 넣은 기기나 카드를 **돈 받고 파는 것**은 안 돼요. 진짜 코어의 비상업 라이선스에 걸려요.
- 감싸는 코어는 각자의 라이선스를 따라요. [arcade-fbneo](../arcade-fbneo/README.ko.md#라이선스) 와 [arcade-mame2003-plus](../arcade-mame2003-plus/README.ko.md#라이선스) 를 보세요.
- `libretro.h`(libretro API 헤더)는 MIT 라이선스예요. 이 폴더에는 없어요.
