<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# melonDS DS — 큰 롬 · 안정적인 같이하기 · DraStic 같은 조작

> KNULLI 를 쓰는 Anbernic RG35XX Pro 용 melonDS DS 레트로아크 코어를 고친 판이에요. 256~512MB 큰 롬이 메모리 부족으로 꺼지지 않고, 두 기기 통신이 끊기지 않고, 팝업 화면과 조작이 DraStic 과 같아요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/ds-melonds-ds-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| 코어 파일 | `melondsds_libretro.so` (리눅스 aarch64, 5,546,496 바이트) |
| 판 | 원본 v1.4.0 + 패치 6장 (이 최종 빌드를 "v2"라고 불러요) |
| md5 | `e0f45595139d4c81ce8b442498c4f6ad`(릴리즈 사본 · 기기 판은 `5443e0001602467348f4df9ea42c5849` — 코어 안 빌드 경로 글줄 8개만 중립 경로로 바꿔 달라요) |
| 원본 | [JesseTG/melonds-ds](https://github.com/JesseTG/melonds-ds) v1.4.0 (`f394adb`)<br>엔진(원본 빌드가 받아 오는 것, **고치지 않았어요**): [JesseTG/melonDS](https://github.com/JesseTG/melonDS) 가지 `jtg/fix-uninitialized-opengl` (`16f127d`) |
| 라이선스 | GPL-3.0 (원본과 같아요) |
| 시험한 기기 | Anbernic RG35XX Pro (H700, Cortex-A53, RAM 1GB) · KNULLI |

## 무엇을 하나

[melonDS DS](https://github.com/JesseTG/melonds-ds) 는 닌텐도 DS 에뮬레이터 melonDS 의 레트로아크 판이에요. 이 빌드는 RG35XX Pro 에서 부딪힌 문제를 고치고, DraStic 에 익숙한 조작을 더했어요.

- **큰 롬이 꺼지지 않아요.** 포켓몬 블랙 · 화이트 · 블랙 2 · 화이트 2, 드래곤퀘스트 9 같은 256~512MB 롬이 메모리 부족으로 꺼졌어요. 롬을 레트로아크 · 코어 · 에뮬레이터가 세 번 복사해서 그랬어요. 이제 롬 파일을 복사 없이 파일 그대로 메모리에 얹어요. 포켓몬 블랙이 쓰는 메모리가 775MB 에서 557MB 로 줄었고, 블랙 2 도 켜져요(2026-10-07 기기 측정).
- **두 기기 통신이 끊기지 않아요.** 느린 기기 둘이 와이파이로 이으면 방장이 상대 답을 너무 일찍 포기해서 게임이 연결을 끊었어요. 이제 기다리는 시간을 진짜 시계로 150ms 로 재고, 상대가 "준비 안 됨" 빈 답을 보내도 "답했다"고 세어서 기다림을 끝내요(원본 melonDS 와 같은 동작). 마리오 카트 DS 두 대 경주가 시간 초과 0 으로 돌았어요(경주 중 초당 약 22프레임 · 대기실 29프레임, 2026-10-08).
- **L2 = 팝업 화면.** 한 화면만 보이는 배치에서 L2 를 누르고 있는 동안 다른 화면이 반투명 창(75% 크기, 둥근 모서리)으로 아래에서 올라와요. 350ms 안에 L2 를 두 번 누르면 손을 떼도 떠 있고(고정), 다음 L2 로 풀려요. 안드로이드 melonDS 의 '팝업 화면' 모양을 따랐어요.
- **조작이 DraStic 과 같아요.** R2 는 위/아래 큰 화면 바꾸기, R3 은 펜 누르기(펜은 오른쪽 스틱으로 움직여요), SELECT + ←/→ 는 화면 배치 돌리기예요. L2 를 누르면 펜이 두 배 빨라지던 것은 껐고, L2 + Y 로 DS 덮개가 닫혀 게임이 잠들던 것도 껐어요(L2 가 팝업 키라 실수로 눌리기 쉬워서요).
- **왼쪽 위 작은 화면.** 한쪽 화면을 크게 보는 동안 다른 화면이 왼쪽 위에 1/4 크기, 초록 테두리로 늘 보여요. DraStic 기본 모양과 같아요.
- **(v2) 스틱만 밀어도 창이 저절로 떠요.** 위 화면이 클 때 오른쪽 스틱을 밀면 '누르는 창'(아래 화면)이 저절로 뜨고, 아래 화면이 클 때 스틱을 쓰면 L2 창이 흐려져서 밑의 펜이 보여요. 창 모서리에 작은 그림(손가락 = 누르는 창, 눈 = 보기 창, 핀 = 고정)이 떠요. 작은 화면 글자가 뭉개지지 않게 하는 선택지(`pip=`)도 있어요.
- **작은 버그도 고쳤어요.** 스틱을 같은 힘으로 밀고 있으면 3초 뒤 펜이 꺼지던 것, 몇몇 변수가 초기화되지 않던 것을 고쳤어요.

이 기기(H700)에서는 DraStic 보다 느려서(게임에 따라 초당 25~60프레임), DS 게임은 대부분 DraStic 이나 [DSperate](../ds-dsperate/) 로 하고 게임별로 이 코어를 골라 써요.

## 무엇을 고쳤나

패치는 모두 원본 저장소의 `src/libretro/` 안 파일만 건드려요. 원본 빌드가 받아 오는 melonDS 엔진은 고치지 않았어요. 패치 안의 `hb_` · `hanbang` 같은 이름(`hanbang.hpp`, `hb_popup.cfg`, 기록 앞머리 `[hanbang]`)은 '우리가 고친 곳' 표시일 뿐이에요. 패치 · 파일 · 스크립트가 서로 맞도록 이름은 그대로 뒀어요.

1. **롬 파일 메모리 매핑** (`retro/info.{cpp,hpp}`, `info.cpp`, `core/core.cpp`, `config/console.cpp`). NDS 내용 설정을 `need_fullpath=true`, `persistent_data=false` 로 바꿨어요(GBA 는 그대로). 프런트엔드가 경로만 주면 `GameInfo` 가 파일을 읽기 전용 `mmap` 으로 열어요. 32MiB 이상 롬은 `posix_memalign` 으로 2의 거듭제곱 크기 칸을 잡고 그 위에 롬 파일을 `MAP_PRIVATE|MAP_FIXED` 로 덮어 카트 버퍼로 써요. 그래서 복사 두 번(`CopyToUnique`, `PadToPowerOf2`)이 없어져요. 어느 단계든 실패하면 예전처럼 복사해요.
2. **넷플레이 기다림** (`net/mp.{cpp,hpp}`, `libretro.cpp`, `core/core.hpp`). 답 기다림을 `std::clock`(프로세스 CPU 시간) 25ms 로 재던 것을 `steady_clock` 150ms 로 바꿨어요(`MELONDSDS_MP_TIMEOUT_MS` 로 5~2000ms 까지 바꿀 수 있어요). 기다리는 동안에는 `yield` 해요. 받은 패킷마다 보낸 클라이언트 번호를 달고, `MpState::ReplyAid()` 가 빈 답(AID 0)을 그 클라이언트에 이어 줘요. 그래서 `MP_RecvReplies` 가 빈 답도 "답함"으로 세지만 데이터는 복사하지 않아요.
3. **L2 팝업** (`render/software.{cpp,hpp}`, `input/{input,joypad}.hpp`). 한 화면 배치(위만/아래만)에서 L2 를 누르는 동안 `DrawPopup()` 이 다른 화면을 그려요. 75% 크기, 약 85% 불투명, 둥근 모서리(반지름 6), 쌍선형 확대로 9장 동안 아래에서 올라와요. 위만 배치에서는 창 안에 터치 커서도 그려요.
4. **덮개 닫기 단축키 끄기** (`input/{joypad,input}.cpp`). L2 + Y 덮개 닫기를 늘 끄고, 조작 이름표 `Y / Close Lid` 를 `Y` 로 바꿨어요.
5. **DraStic 같은 조작과 작은 화면** (`input/{joypad,input}.{cpp,hpp}`, `screenlayout.{cpp,hpp}`, `render/software.{cpp,hpp}`, `core/tasks.cpp`). R2 = `SwapScreens`(배치 번호 `^1`), R3 = 터치예요. SELECT + →/← 는 다음/이전 배치(작은 화면 켜고 끄기 포함)이고, SELECT 를 누르는 동안 ←/→ 는 DS 로 보내지 않아요. L2 를 350ms 안에 두 번 누르면 팝업이 고정돼요(`steady_clock`). `DrawPictureInPicture()` 는 다른 화면을 1/4 크기, 불투명 초록 테두리(`0xFF03CF03`), 터치 커서와 함께 그려요. 배치 안내 글자는 껐고, `_layoutIndex` 와 `_layouts` 는 초기화해요.
6. **UI v2** (위 파일들 + 새 `hanbang.hpp`, `input/cursor.cpp`, `platform/mp.cpp`, `libretro.cpp`, `net/mp.cpp`, `core/core.cpp`). 그리는 차례를 정리했어요(큰 화면 → 작은 화면 → 펜 → 창 → 모서리 그림 → 창 안 펜). 자동 누르는 창(D), 흐리기(C), 모서리 그림(11×11 점), 작은 화면 넓이 평균(`pip=0/1/2`, 2 는 512×384 로 내보내고 같이하기 중엔 자동으로 1), 창 가로 표본 표를 더했고, L2 펜 가속을 껐고, 스틱 펜 숨김 시계를 고쳤어요. `hb_popup.cfg` 읽기와 같이하기 재는 기록도 들어 있어요.

세부는 패치 안 주석(한국어 · 영어 섞임)에 있어요.

## 코어 옵션

### `nds.opt`

`/userdata/system/configs/retroarch/config/melonDS DS/nds.opt` — 우리가 바꾸거나 신경 쓴 옵션이에요.

| 옵션 | 쓰는 값 | 메모 |
|---|---|---|
| `melonds_number_of_screen_layouts` | `"2"` | |
| `melonds_screen_layout1` | `"bottom"` | 전에는 `"top"` |
| `melonds_screen_layout2` | `"top"` | 전에는 `"bottom"` |
| `melonds_render_mode` | `"software"` | 팝업 · 작은 화면은 소프트웨어 렌더러에서만 그려요 |
| `melonds_jit_enable` | 켜 둠 | |
| `melonds_threaded_renderer` | 켜 둠 | |
| `melonds_mac_address_mode` | 쓰지 마세요 | 게임을 끌 때 `firmware.bin` 을 다시 써요 |

기본 화면은 "아래 화면 크게 + 왼쪽 위에 작은 위 화면"이에요. SELECT + → 로 `아래 + 작은 화면 → 위 + 작은 화면 → 아래만 → 위만` 을 돌아요.

### 팝업 설정 파일 (선택)

`/userdata/system/configs/advanced_drastic/hb_popup.cfg` 는 DraStic 쪽 팝업이 읽는 것과 같은 파일이에요. 코어는 게임을 켤 때 한 번 읽고, 파일이나 줄이 없으면 아래 기본값을 써요. 모르는 줄은 그냥 넘겨요. 다른 위치의 파일을 쓰려면 환경 변수 `MELONDSDS_HB_POPUP_CFG=<경로>` 를 주세요.

| 키 | 기본값 | 뜻 |
|---|---|---|
| `auto` | `1` | 위 화면이 클 때 오른쪽 스틱을 밀면 누르는 창이 저절로 떠요 (`0` = 끔) |
| `fade` | `40` | 아래 화면이 클 때 스틱을 쓰는 동안 L2 창의 불투명도(%) |
| `alpha` | `85` | 창 불투명도(%) |
| `pip` | `1` | 작은 화면 줄이는 방식: `0` 가까운 점만, `1` 넓이 평균, `2` 두 배로 내보내고 평균(가장 또렷하고 약간 무거움) |

### 조작 (이 코어에서 바뀐 것)

| 버튼 | 동작 |
|---|---|
| L2 꾹 | 다른 화면이 반투명 창으로 올라와요 (한 화면 배치에서) |
| L2 두 번 (350ms 안) | 창 고정 — 다음 L2 로 풀려요 |
| R2 | 위/아래 큰 화면 바꾸기 |
| 오른쪽 스틱 · R3 | 펜 움직이기 · 펜 누르기 |
| SELECT + → / ← | 화면 배치 다음 / 이전 (그동안 ←/→ 는 게임에 안 들어가요) |
| L2 + Y | 아무 일 없어요 (덮개 닫기를 껐어요) |

### 진단용 스위치

게임을 끄지 않아도 1~2초 안에 바뀌어요.

| 스위치 | 하는 일 |
|---|---|
| `echo 2 > /tmp/melonds_pip` | 작은 화면 방식을 바로 바꿔요(0, 1, 2). `rm /tmp/melonds_pip` 하면 설정 파일 값으로 돌아가요. 환경 변수 `MELONDSDS_PIP` 도 돼요. |
| `touch /tmp/melonds_mp_stats` | 1초마다 `/tmp/melonds_mp_stats.log` 에 같이하기 기록을 한 줄씩 남겨요(프레임 수 · 에뮬 계산 · 통신 기다림 · 보낸/받은 패킷 · 시간 초과 등). 파일을 `rm` 하면 멈추고, 20MB 가 넘으면 스스로 멈춰요. 파일이 없을 때 드는 비용은 60프레임마다 `stat` 두 번뿐이에요. 각 칸의 뜻은 기록 맨 위 `#` 줄에 적혀 있어요. |
| `MELONDSDS_MP_TIMEOUT_MS=<5~2000>` | 같이하기 답 기다림 시간(밀리초, 기본 150). |

## KNULLI 에 넣기

우리가 쓰는 방식이에요. [Releases](https://github.com/Squirbie/handheld-link-cores/releases) 에서 `ds-melonds-ds-linux-aarch64.zip` 을 받아 풀어 주세요.

1. **파일 자리.** `melondsds_libretro.so` 를 SD 카드 쪽 `/userdata/system/hanbang_cores/`(미리 빌드한 파일이 쓰는 기본 자리)에 복사하고, 레트로아크가 찾는 `/usr/lib/libretro/melondsds_libretro.so` 는 그 파일로 가는 **바로가기(심볼릭 링크)** 로 둬요. KNULLI 의 시스템 부분은 읽기 전용이라 바로가기를 만든 뒤 `knulli-save-overlay` 로 덧칠(overlay)에 저장해요. (코어를 SD 카드 쪽에 둔 건 덧칠이 램 디스크라서 큰 파일을 넣으면 메모리를 먹기 때문이에요. 이 폴더를 지우면 코어가 안 켜져요.) 처음 바꾸기 전에 원래 파일을 `melondsds_libretro.so.orig` 로 백업해 두세요(우리가 쓰던 것은 공식 v1.4.0 linux-arm64 빌드였어요). 코어 이름은 그대로예요. 기록으로 `.info` 의 버전 표시도 1.4.0 으로 맞춰 뒀는데, 꼭 필요하지는 않아요.
2. **게임별로 이 코어 쓰기.** ES 메뉴에서 그 게임의 코어를 "melonDS DS" 로 고르거나 `knulli.conf` 에 두 줄을 넣어요.
   ```
   nds["<롬 파일 이름>.zip"].emulator=libretro
   nds["<롬 파일 이름>.zip"].core=melondsds
   ```
3. **코어 옵션 맞추기.** [코어 옵션](#코어-옵션)에 적은 대로 `nds.opt` 를 고쳐요.
4. **팝업 설정 (선택).** 기본값이 아닌 값을 쓰고 싶으면 `hb_popup.cfg` 를 만들어요.
5. **확인.** 파일 md5 를 견줘 보세요. 게임을 켤 때 표준 오류(stderr) 기록에 `[hanbang] popup cfg …: auto=… fade=… alpha=… pip=…` 한 줄이 찍히면 이 판이에요.
6. **되돌리기.** 백업해 둔 `melondsds_libretro.so.orig` 를 다시 놓으세요. 팝업 동작만 끄려면 `hb_popup.cfg` 에 `auto=0`, `fade=85`, `pip=0` 을 적어요.

### 같이 쓰는 스크립트 (선택)

두 기기 같이하기와 세이브 맞추기에는 이 저장소 [`knulli-scripts/`](../../knulli-scripts/) 의 도우미 스크립트 몇 개를 써요. `/userdata/system/claude/`(미리 빌드한 파일이 쓰는 기본 자리)에 복사하고, ES 훅은 `/userdata/system/scripts/nds_save_sync.sh`(미리 빌드한 파일이 쓰는 기본 자리)에 둬요. 그 `scripts` 폴더의 파일은 모두 실행되니 이 파일 하나만 두세요.

- [`nds_save_sync.py`](../../knulli-scripts/nds_save_sync.py) · [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) — DraStic 세이브(`.dsv`)와 이 코어 세이브(`.srm`)를 같은 게임끼리 이어 줘요.
- [`hb_dsmac.py`](../../knulli-scripts/hb_dsmac.py) — 기기마다 DS 무선 주소를 다르게 해 줘요.
- [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py) — 넷플레이 중 게임 속 저장을 바로 파일로 써 줘요.
- [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py) — 같은 게임 방이 열려 있으면 '같이 / 혼자' 고르는 창을 띄워요.
- [`hb_direct.py`](../../knulli-scripts/hb_direct.py) — 같이하기 중 기기끼리 직접 연결해요(공유기를 안 거쳐요).
- DraStic 쪽 팝업(`hb_dsosd`)은 같은 `hb_popup.cfg` 를 읽어요. 이 저장소에는 없어요.

### 다른 기기 · OS 에서 쓸 때

- **빌드 환경.** 파일은 GCC 12.2(Debian 12)로 빌드해서 `glibc 2.34` 이상, `libstdc++ 3.4.29` 이상이 필요해요. 그보다 오래된 리눅스에서는 패치로 다시 빌드하세요. KNULLI(glibc 2.40)에서는 문제없었어요. 안드로이드 · 윈도우 · 맥은 이 파일을 못 써요. 패치를 원본 소스에 걸어 그 기기용으로 빌드해야 해요.
- **CPU.** `-mcpu=cortex-a53` 으로 빌드했어요. 다른 ARMv8 CPU 에서도 돌 가능성이 크지만 Cortex-A53 에서만 시험했어요. ARM64 JIT 를 쓰므로 실행 가능한 메모리(`PROT_EXEC`)를 못 만드는 OS 에서는 `melonds_jit_enable = "disabled"` 로 해야 하고, 그러면 많이 느려져요.
- **롬 메모리 매핑(패치 0001)은 glibc 를 가정해요.** `posix_memalign` 으로 잡은 큰 칸 위에 파일을 덮은 다음 `free()` 가 통째로 `munmap` 해 준다는 점에 기대요. musl · bionic(안드로이드) · 윈도우 · 맥에서는 패치 0001 을 고치거나 빼야 해요. 프런트엔드가 **파일 경로**(`need_fullpath`)를 넘겨줘야 하고, 경로가 없거나 매핑이 실패하면(32MB 미만 롬 포함) 예전처럼 복사해요.
- **`hb_popup.cfg` 위치와 `/userdata/...` 경로는 KNULLI 기준**이에요. 다른 OS 에서는 `MELONDSDS_HB_POPUP_CFG` 로 가리키세요.
- 팝업 · 작은 화면은 **소프트웨어 렌더러**에서만 그려요(이 빌드는 OpenGL 을 껐어요).
- **같이하기**는 레트로아크 넷플레이(netpacket)로 두 기기가 이어져요. 같은 패치 코어끼리, 같은 네트워크에서만 돼요. 기기마다 **DS 무선 주소(MAC)가 달라야** 해요. 펌웨어 파일을 통째로 복사하면 같아져서 입장 오류가 나요(`knulli-scripts/hb_dsmac.py` 가 기기마다 다르게 해 줘요). 코어 옵션 `melonds_mac_address_mode` 는 쓰지 마세요(끌 때 `firmware.bin` 을 다시 써요). 같이하기는 양쪽이 같은 패치 코어일 때만 시험했어요.
- **속도.** 이 기기(H700)에서 DraStic 보다 느려요(게임에 따라 초당 25~60프레임).

## 소스에서 빌드

Debian 12 (aarch64, glibc 2.36) 가상 머신에서 CMake + Ninja 로 빌드했어요.

```sh
git clone https://github.com/JesseTG/melonds-ds.git
cd melonds-ds
git checkout v1.4.0            # f394adbacb5722ee97c1b37c8064da9a25818310
while read -r p; do git apply --check "/path/to/patches/$p" && git apply "/path/to/patches/$p" || break; done < /path/to/patches/series

# 엔진은 CMake 가 받아 와요. 원본 가지가 움직였으면 16f127db 로 고정하세요.
#   -DFETCHCONTENT_SOURCE_DIR_MELONDS=<melonDS 를 16f127dbb587a73371827ce79689c5d237c4b59b 로 받은 폴더>
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS="-mcpu=cortex-a53" -DCMAKE_CXX_FLAGS="-mcpu=cortex-a53" \
  -DCMAKE_C_FLAGS_RELEASE="-O3 -DNDEBUG" -DCMAKE_CXX_FLAGS_RELEASE="-O3 -DNDEBUG" \
  -DCMAKE_SHARED_LINKER_FLAGS="-Wl,-z,nodelete" -DCMAKE_MODULE_LINKER_FLAGS="-Wl,-z,nodelete" \
  -DENABLE_JIT=ON -DENABLE_LTO_RELEASE=ON -DENABLE_NETWORKING=ON \
  -DENABLE_OPENGL=OFF -DENABLE_OGLRENDERER=OFF -DENABLE_THREADED_RENDERER=ON
cmake --build build --target melondsds_libretro
readelf -d build/src/libretro/melondsds_libretro.so | grep FLAGS_1     # NODELETE 가 보여야 해요
```

- 엔진은 [JesseTG/melonDS](https://github.com/JesseTG/melonDS) 의 `jtg/fix-uninitialized-opengl` 가지예요. v1.4.0 의 `cmake/FetchDependencies.cmake` 44번 줄이 가리켜요. 우리가 빌드한 때의 커밋은 `16f127dbb587a73371827ce79689c5d237c4b59b`(부모 `906e9ebb27da8c6a715cd7abab4abfe8a8d29427`)이고, 2026-10-29 에도 가지 끝이 같은 커밋이었어요. 가지는 움직일 수 있으니 다시 빌드할 때는 이 커밋으로 고정하세요.
- 컴파일러와 옵션: GCC 12.2 (Debian 12, aarch64), `-O3 -mcpu=cortex-a53`, JIT 켬, OpenGL 끔, `-Wl,-z,nodelete`.
- 위 `cmake` 줄은 우리 빌드 폴더의 CMake 설정값(`CMakeCache.txt`)을 옮겨 정리한 거예요. 처음 설정할 때 친 명령줄 자체는 기록에 남아 있지 않아요.
- **`-Wl,-z,nodelete` 는 그대로 넣으세요.** RG35XX Pro 에서 이 플래그가 없는 빌드(zig 로 빌드해 본 것)는 게임을 끌 때마다 레트로아크 종료 값 -11 로 끝났고, 이 플래그로 0 이 됐어요. GCC 빌드에도 같은 이유로 남겨 뒀어요. 다 빌드한 뒤 `NODELETE` 가 있는지 확인하세요.
- 메모리가 3GB 정도뿐인 기기 · 가상 머신에서는 마지막 링크(LTO)가 `-flto=auto` 로 CPU 를 다 써서 모자랄 수 있어요. 우리는 컴파일을 `ninja -j2` 로, 링크 명령의 `-flto=auto` 를 `-flto=2` 로 바꿔 직접 실행했어요.
- 같은 환경에서도 파일 지문(md5)이 똑같이 나온다는 보장은 없어요(LTO · 빌드 경로).

## 패치

번호 순서대로 걸어요(순서는 [`patches/series`](patches/series) 에도 적어 뒀어요). 뒤 패치가 기대하는 시작 파일 지문(패치 안 `index` 줄에 git 이 적은 지문)이 앞 패치 뒤에 적힌 지문과 모두 이어져요(끊긴 곳 0).

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | [`0001-rom-file-mapping.patch`](patches/0001-rom-file-mapping.patch) | 큰 롬 파일을 복사하지 않고 메모리에 얹어서, 포켓몬 블랙 · 화이트(1, 2) 같은 롬이 메모리 부족으로 꺼지지 않게 해요 |
| 2 | [`0002-netplay-wallclock-timeout-and-blank-replies.patch`](patches/0002-netplay-wallclock-timeout-and-blank-replies.patch) | 넷플레이 답 기다림을 진짜 시계(150ms)로 재고, 빈 답도 답으로 세요 |
| 3 | [`0003-l2-popup.patch`](patches/0003-l2-popup.patch) | L2 를 누르면 다른 화면이 반투명 팝업으로 올라오고, 두 번 누르면 고정돼요 |
| 4 | [`0004-lid-close-hotkey-off.patch`](patches/0004-lid-close-hotkey-off.patch) | L2 + Y 덮개 닫기 단축키를 꺼요 |
| 5 | [`0005-drastic-style-controls-and-pip.patch`](patches/0005-drastic-style-controls-and-pip.patch) | DraStic 같은 조작(R2 바꾸기, R3 터치, SELECT + ←/→ 배치)과 왼쪽 위 작은 화면을 더해요 |
| 6 | [`0006-ui-v2-auto-popup-badges-pip-quality-mp-stats.patch`](patches/0006-ui-v2-auto-popup-badges-pip-quality-mp-stats.patch) | UI v2: 스틱으로 뜨는 팝업, 모서리 그림, 더 또렷한 작은 화면, `hb_popup.cfg`, 같이하기 재는 기록 |

**최종 패치가 이 여섯 장인 근거**

- 하나로 된 "전체" 패치는 없어요. 코어는 패치를 차례로 쌓아 만들었어요. 마지막 판(`5443e000`, "v2")과 바로 앞 판(`aa068ff8`, 패치 0001~0005 까지)의 소스 차이가 `0006` 이고, `0006` 의 시작 지문이 `0001`~`0005` 를 거친 파일 지문과 이어져요.
- `0006` 은 작업용 가상 머신 안 비공개 저장소의 한 가지에 있는 커밋 2개(`1c90e0b`, `688ed5a`, 기준 `88bf8ab`)의 차이예요. `88bf8ab` 는 바로 앞 판이에요. 이 커밋들은 공개 저장소에 없어서 diff 를 패치로 둬요.
- 코어 파일 안 글자와 맞아요. `hanbang: mapped … ROM file`(0001), `MELONDSDS_MP_TIMEOUT_MS`(0002), `Pop-up Screen (hold, double-tap = pin)` · `Swap Screens`(0005 · 0006), `MELONDSDS_PIP` · `/tmp/melonds_mp_stats` · `[hanbang] popup cfg …`(0006)이 들어 있고, 옛 `Y / Close Lid`(0004 가 지움)와 배치 안내 글 `Layout {}/{}`(0005 가 지움)는 없어요. `readelf` 로 보면 `FLAGS_1` 에 `NODELETE` 가 있어요(`5443e000` 확인).
- 이 파일을 시험 기기에 넣고 써 본 날은 2026-10-12 예요.

**확인한 것과 못 한 것**

- 확인함: 패치 6장의 시작 파일 지문 20개가 모두 v1.4.0 트리의 같은 파일 지문과 같아요(2026-10-29, 저장소 정보만 읽어 대조). 패치 사이 지문 사슬 끊김은 0 이에요. 코어 파일 안 글자가 마지막 판과 맞고, `NODELETE` 와 필요 라이브러리도 확인했고, 패치 형식(`git apply --numstat`)이 깨지지 않았어요.
- 못 함: 이번 정리에서 원본 소스를 새로 받아 `git apply --check` 를 돌려 보지는 않았어요(지문으로만 확인). 최신 `main` 과의 비교도 안 했어요.

<details>
<summary>파일별 지문 사슬 (확인용)</summary>

패치의 `index` 줄에 git 이 적은 파일 지문이에요. `v1.4.0` 의 파일 지문과, 그 파일을 마지막으로 고친 패치 뒤의 지문이에요(경로는 `src/libretro/` 기준). 같은 파일을 여러 패치가 고치는 곳은 번호를 모두 적었어요. 적힌 값은 빌드할 때의 파일 기준이에요. 빌드 뒤 공개하면서 패치 주석 글자를 조금 고쳤기 때문에, 패치를 걸어 얻은 파일의 지문은 적힌 최종 지문과 다를 수 있어요.

| 파일 | v1.4.0 | 적힌 최종 | 거친 패치 |
|---|---|---|---|
| `config/console.cpp` | `73b7e24` | `722a08c` | 0001 |
| `core/core.cpp` | `df32f07` | `91de02b` | 0001, 0006 |
| `core/core.hpp` | `bb52319` | `7e382dc` | 0002 |
| `core/tasks.cpp` | `87bfa2a` | `d3d1dc9` | 0005 |
| `hanbang.hpp` | (새 파일) | `62a22da` | 0006 |
| `info.cpp` | `9ba200b` | `c5b1fca` | 0001 |
| `input/cursor.cpp` | `98b8766` | `d69063a` | 0006 |
| `input/input.cpp` | `0b0b101` | `a805d5c` | 0004, 0005, 0006 |
| `input/input.hpp` | `c37e7a6` | `2d6c188` | 0003, 0006 |
| `input/joypad.cpp` | `fabccaa` | `7d6b4a7` | 0004, 0005, 0006 |
| `input/joypad.hpp` | `6a571be` | `10bd6e9` | 0003, 0005, 0006 |
| `libretro.cpp` | `b56f23a` | `388d36d` | 0002, 0006 |
| `net/mp.cpp` | `caa185d` | `f714193` | 0002, 0006 |
| `net/mp.hpp` | `f6b5dfc` | `807b7b4` | 0002 |
| `platform/mp.cpp` | `30ee4c2` | `432d88b` | 0006 |
| `render/software.cpp` | `0884b70` | `91bb791` | 0003, 0005, 0006 |
| `render/software.hpp` | `c08c753` | `cd8c1d8` | 0003, 0005, 0006 |
| `retro/info.cpp` | `c55aa81` | `e885d9c` | 0001 |
| `retro/info.hpp` | `f5e8175` | `470a180` | 0001 |
| `screenlayout.cpp` | `fb727c9` | `6684326` | 0005 |
| `screenlayout.hpp` | `6edc64e` | `06f531d` | 0005 |

</details>

## 원본에 보내기

원본에 보낼 만한 것은 패치 **0002**(넷플레이 기다림을 진짜 시계로, 빈 답도 답으로 셈) 하나예요. 넷패킷 같이하기의 분명한 버그 두 가지를 고쳐요(57줄 추가, 7줄 삭제).

1. 답 기다림을 `std::clock`(스레드를 모두 합친 프로세스 CPU 시간)으로 재서, 실제로는 25ms 보다 훨씬 일찍 끝나곤 했어요. 느린 기기 둘에서 방장이 답을 너무 일찍 포기해 게임이 연결을 끊었어요.
2. "준비 안 됨" 빈 답(AID 0)을 답한 것으로 세지 않아서, 방장이 늘 시간 초과까지 기다렸어요. 원본 melonDS 는 모두 답하면 빈 답이어도 기다림을 끝내요.

두 기기 마리오 카트 DS 경주(초당 약 22프레임, 시간 초과 0)로 확인했어요. 보내기 전에 최신 `main` 에서 이미 고쳐졌는지 확인하고 다시 시험해야 해요. 이번 정리에서는 웹을 원본 주소와 커밋 확인에만 써서 `main` 과 비교하지 않았어요.

나머지(롬 파일 매핑은 glibc 가정, L2 팝업, 작은 화면, 버튼 바꾸기, 덮개 끄기, 진단 기록)는 RG35XX Pro 에 맞춘 것이라 보내지 않아요. 멤버 초기화(`ScreenLayoutData` / `JoypadState`)는 실제로 문제가 되는 길인지 확인하지 못해 뺐어요. 0002 의 제목과 글 초안은 [`UPSTREAM.md`](../../UPSTREAM.md) 와 [`cores/MANIFEST.ds.jsonl`](../MANIFEST.ds.jsonl) 의 `upstream_pr_candidate` 에 있어요.

## 라이선스

- melonDS DS 는 **GNU GPL v3.0** 이에요(원본 `LICENSE`, [`LICENSES/melonds-ds_LICENSE`](../../LICENSES/melonds-ds_LICENSE) 에 같이 뒀어요). 이 패치들도 같은 조건으로 공개해요.
- melonDS 엔진도 GPL-3.0 이에요.
