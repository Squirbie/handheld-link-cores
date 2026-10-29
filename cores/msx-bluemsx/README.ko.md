<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# blueMSX — 저장은 남고, 디스크는 바뀌고, 넷플레이는 어긋나지 않게

> libretro blueMSX 코어를 세 가지로 고쳤어요: 게임 안 저장이 파일로 남고, 레트로아크 1.22 에서 디스크 바꾸기가 먹고, 상태 저장 · 불러오기가 완전하고 일정해서 두 기기 넷플레이가 갈라지지 않아요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/msx-bluemsx-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| **코어 파일** | `bluemsx_libretro.so` — aarch64 리눅스용, 1,685,216 바이트 (git 에는 없고 릴리스 zip 안에 있어요) |
| **버전** | `git 572c918-hbnp1` |
| **md5** | `83032767d18ac489157269e56e770cd1` |
| **원본** | [libretro/blueMSX-libretro](https://github.com/libretro/blueMSX-libretro) @ [`572c918`](https://github.com/libretro/blueMSX-libretro/commit/572c91856a5288b7433c619af651e31f00f3ce7e) ("Merge pull request #182 from jfroco/master", 2024-12-04). KNULLI 순정 코어가 알리는 `git-572c918` 와 같은 커밋이에요. |
| **라이선스** | 파일마다 달라요: blueMSX 자체 파일은 BSD 계열, 일부 GPL · ZLIB · 프리웨어 (원본 `license.txt` 와 아래 '라이선스' 참고) |
| **시험한 환경** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (확인한 환경은 이것뿐이에요) |

## 무엇을 하나

MSX/MSX2 코어 blueMSX 의 libretro 판은 휴대기기에서 세 가지가 문제였어요. 이 빌드는 셋 다 고쳐요.

1. **게임 안 저장이 파일로 남아요.** 게임을 끌 때 카트리지 배터리 SRAM · 플래시를 파일에 쓰지 않아서, 코에이 게임 같은 게임 속 저장이 껐다 켜면 사라졌어요.
2. **디스크 바꾸기 단추가 먹어요.** 여러 장짜리 디스크 게임에서 레트로아크 1.22 의 '다음/이전 디스크'가 반응하지 않았어요.
3. **두 기기 같이하기에서 장면이 갈라지지 않아요.** 상태 저장 · 불러오기가 타이머 · 보드 · 플로피 헤드 · 소리칩 상태를 제대로 다루지 못해서, 넷플레이 중 두 기기의 장면이 서로 달라졌어요.

### 알아 두면 좋은 것

- 두 기기에 **같은 코어 · 같은 바이오스 · 같은 롬 DB · 같은 설정**이어야 해요. 예를 들어 60Hz 설정이 한쪽에만 있으면 다른 쪽은 50Hz 로 돌아요.
- 남은 위험:
  - MSX2 는 불러온 직후 화면 1~2장이 겉모습만 달라요.
  - 플래시/디스크 세이브 **내용**은 상태에 안 들어가요.
  - CMOS 는 방장 것을 받아서, 손님의 `MSX2.cmos` 도 방장 값으로 써져요.
  - 키 파일(`.keys`)로 넣는 키보드 입력은 넷플레이 중 코어에 안 갈 수 있어요(소스로 본 판단이고 확인은 못 했어요).
  - 고치지 않은 드문 소리 상태가 있어요: VLM5030 · Majutsushi · turboR PCM · 프린터 DAC.
- 넷플레이 방장 메모리는 약 217MB 로 전과 같아요.

## 무엇을 고쳤나

1. **끌 때 SRAM · 플래시 저장과 디스크 트레이 (패치 01, `libretro.c`).**
   - `retro_unload_game` 이 보드를 해체하지 않아 매퍼의 `destroy` 콜백(안에서 `sramSave()`)이 한 번도 안 불렸어요. `boardInfo.destroy()` 를 부르게 해서 배터리 SRAM · 플래시(코에이 · ASCII8/16 SRAM · MegaFlashROM 등)가 저장 폴더에 쓰여요. 원본 최신 master 에서도 이 호출은 없었어요(2026-10-29 확인).
   - `get_eject_state()` 를 늘 '열림'으로 돌려줘요. 레트로아크 1.22 는 트레이가 닫혀 있으면 디스크 번호를 바꾸지 않아서 단추 한 번으로는 안 바뀌었어요. (휴대기기 구성 전용 우회예요.)
2. **플래시 저장 불러오기 (패치 02, `AmdFlash.c` · `MegaromCartridge.c`).**
   - 켤 때 저장된 `.sram` 을 롬 복사 **뒤에** 읽도록 되살렸어요. `#if 0` 로 막혀 있어서, 지난번에 저장한 플래시가 롬 안의 빈 영역으로 덮였어요.
   - `MegaFlashRomSccPlus` 가 롬 1MB 를 넘으면 플래시를 2MB 로 잡아요(야마노오토식 플래시 카트 한글 변환판용).
3. **hbnp1: 넷플레이 / 되감기용 상태 고침 (패치 03).** 158개 파일, 약 750줄 추가 · 180줄 삭제예요. 그 가운데 `malloc` → `calloc`(초기화 안 된 메모리가 상태에 섞이던 것)이 153곳이고, 나머지는 상태 저장 항목 추가 · 타이머 정리 같은 것이에요.
   - 게임 진행이 갈리던 것:
     1. `retro_unserialize` 가 장치 상태만 불러오고 **타이머를 비우지 않아** 불러오기 전 시간줄의 타이머가 엉뚱한 때 터졌어요(blueMSX 자체 되감기는 `boardTimerCleanup` 을 먼저 불러요).
     2. 보드의 끼어들기 대기 칸 · 64비트 시각이 되살아나지 않았어요.
     3. '시각은 지났지만 아직 안 터진' 타이머를 불러올 때 버렸어요(소리 믹서 타이머가 영영 멈추기도 했어요).
     4. 플로피 제어기 WD2793 의 이름표가 틀렸어요. `diskTracks[0]` 로 저장하고 `diskTracks0` 으로 읽어서 헤드 위치가 늘 0 이 됐어요(뮬의 램이 갈라지던 까닭). **원본 최신 master 에도 그대로 있어요(2026-10-29 확인).**
     5. RTC 의 모드 · CMOS 기억이 상태에 없었어요.
   - 상태 바이트 · 소리가 일정하지 않던 것:
     6. 상태에 쓰레기가 섞였어요 — 파일 이름 칸, 4바이트 맞춤 빈칸, 기종 이름, 초기화 안 된 메모리(malloc 약 150곳 · C++ 소리칩 객체), 그리고 상태마다 넣던 '저장한 시각'(기기 · 초마다 달랐어요). C++ 객체는 **새 파일 `Src/Libretro/HbZeroNew.cpp`**(패치 안에 들어 있어요)로 전역 `operator new` 가 0 으로 채운 메모리를 주게 바꿨어요. 코어 안에서만 쓰이는 거친 우회라, 원본에는 생성자에서 칸을 비우는 쪽이 맞아요.
     7. 소리 쪽 칸이 상태에 없었어요 — 믹서(시각 · 남은 소리 · 타이머), DAC · 키 딸깍, SCC, MSX-AUDIO 다시 셈 위치, OPL 잡음(rand), 플로피 소리 모터, MSX-MUSIC 되먹임 · 출력 필터.
   - 안전:
     8. 저장할 때 버퍼 크기(2MB)를 확인하지 않았어요(MSX2 상태가 1.76MB 라 여유가 적어요).
     9. 메모리 zip 파일 수 한도가 64 여서, 넘으면 장치 상태가 말없이 빠졌어요.
   - 옛 상태 파일(이전 코어로 만든 저장 상태)도 새 코어에서 이어져요.

**레트로아크 1.22.2 의 상태 대조(소스로 확인).** 방장이 상태 버퍼 전체(2MB)의 CRC 를 보내고, 손님은 첫 대조가 틀리면 그 판 내내 대조를 꺼요. CRC 가 늦게 오면 틀릴 때마다 상태를 통째로 요청해요. 옛 코어는 상태 바이트가 늘 달라서 어긋남을 못 고치거나 계속 다시 맞췄어요.

이름이나 주석에 들어 있는 `hb_` · `hanbang` 은 우리가 고친 곳 표시일 뿐이에요. 이름을 바꾸지는 않았어요.

### 시험 결과 (개발 때 VM 시험대)

레트로아크 없이 코어를 직접 돌려 프레임마다 화면 · 소리 · 램 · 상태 지문을 적는 시험대로, 8게임(챔피언 프로레슬링 · 부타마루 팬츠 · 라이즈 아웃 · 형제의 모험 · 아르카노이드 2 · 홀 인 원 스페셜 · 뮬(디스크) · 룬 마스터 3)을 3600프레임씩 돌렸어요. 합류(손님이 방장 상태를 받음) · 되감기(손님꼴 · 방장꼴) · 저장 → 불러오기 · 기기 시계 1시간 차이를 포함해요.

- **고치기 전:** 같은 장면의 상태 바이트가 다르고, 합류 · 되감기에서 소리가 다르고, 뮬은 램이 1724프레임부터 계속 갈라졌어요.
- **고친 뒤:** MSX1 네 게임은 화면 · 램 · 소리 · 상태 바이트가 모두 같아요. MSX2 네 게임은 램 · 소리가 같고, **불러온 직후 화면 1~2장**만 달라요(화면 버퍼를 상태에 넣으면 2MB 를 넘어서 넣지 않았어요). RTC 시각은 합류 때 방장 것을 받아요.
- **기기 두 대로:** 챔피언 프로레슬링 같이하기 한 판에서 제목 · 경기 화면이 같고, 상태 대조 간격(600장)을 넘겨도 12초 동안 어긋남이 없었어요. 그 밖의 게임은 대표 한 판만 보고 게임마다 기기 시험은 하지 않았어요.

## 코어 옵션

이 빌드는 새 코어 옵션을 더하지 않았어요. 설정은 순정 blueMSX 옵션 그대로예요.

## KNULLI 에 넣기

**순정 이름 그대로 바꿔 넣어요.** 그러면 `.info` · ES 기능 · `knulli.conf` 를 손대지 않아도 모든 MSX 게임이 이 코어로 켜져요. 두 기기에 **같은 파일**을 넣어야 해요(판이 다르면 같이하기가 어긋나요). [최신 릴리스](https://github.com/Squirbie/handheld-link-cores/releases/latest)에서 `msx-bluemsx-linux-aarch64.zip` 을 받아 풀고, 게임을 끈 상태에서 넣어요.

**시작하기 전에**

- 미리 빌드한 `.so` 는 **aarch64 리눅스**용이에요. glibc 2.33 이하 기호만 쓰고 `libstdc++` · `libm` · `libc` 가 필요해요. 다른 CPU · OS 는 패치로 다시 빌드해야 해요.
- 확인한 환경은 **KNULLI + RetroArch 1.22.2** 뿐이에요.
- 넣기 전에 두 기기의 코어 · 레트로아크 · 바이오스 · 롬 DB · `blueMSX.cfg` 가 같은지 읽기만 하며 견줘 보세요. 우리는 108개 항목을 견줘서 다름 2개(한 기기에 롬이 없는 것과 CMOS 파일)를 확인하고 넣었어요.
- 푼 파일을 확인하세요: md5 는 위 표와 같고, sha256 은 `9186b7b9d2ca7149bf42cef2134e12fdef7f03ab98813096356ce669ebd37228` 예요.

**순서.** 파일을 `/userdata/system/hanbang_cores/` (미리 빌드한 파일이 쓰는 기본 자리)에 두고, 순정 이름이 그 파일을 가리키게 해요.

```sh
HB=/userdata/system/hanbang_cores/bluemsx_libretro.so
LINK=/usr/lib/libretro/bluemsx_libretro.so
mkdir -p /userdata/system/hanbang_cores
cat > $HB.hbnew < bluemsx_libretro.so          # 올린 파일의 md5 를 확인한 뒤에 다음 줄로
chmod 755 $HB.hbnew
[ -L $LINK ] || cp -p $LINK $HB.old            # 덧칠 안의 진짜 파일이면 옛 코어를 SD 에 남겨 둬요
mv -f $HB.hbnew $HB
mount -o remount,rw /
ln -sfn $HB $LINK
knulli-save-overlay                             # 바로가기를 재부팅 뒤에도 남겨요
```

- **되돌리기:** 남겨 둔 옛 코어를 같은 자리에 두고 바로가기를 다시 걸어요(`ln -sfn …`).
- 게임 안 저장은 `/userdata/saves/msx1` · `/userdata/saves/msx2` 의 `<롬 이름>.sram` 으로 남아요.

## 소스에서 빌드

```sh
git clone https://github.com/libretro/blueMSX-libretro
cd blueMSX-libretro
git checkout 572c91856a5288b7433c619af651e31f00f3ce7e
PATCHES=/path/to/handheld-link-cores/cores/msx-bluemsx/patches
for p in "$PATCHES"/*.patch; do patch -p1 < "$p" || break; done
make -f Makefile.libretro platform=unix GIT_VERSION=" 572c918-hbnp1" -j2     # Debian 12 aarch64, gcc 12.2.0 기준
# -> bluemsx_libretro.so
```

- `GIT_VERSION` 은 코어가 알리는 판 글자(`git` + 이 글자)가 돼요. 두 기기가 같아야 해요.
- 개발 때는 같은 소스를 VM(Debian 12 aarch64, gcc 12.2.0)에서 빌드했어요. 원본 `Makefile.libretro` 가 `CFLAGS` · `CXXFLAGS` 를 `:=` 로 정하기 때문에(`-std=gnu89` · `-std=gnu++98` 등) 환경 변수로는 못 바꿔요. CPU 플래그가 필요하면 그 파일에 더하세요. VM 빌드 스크립트는 이 저장소에 없어서, 위 명령은 원본 Makefile 을 읽고 정리한 것이에요(실제로 돌린 것과 글자가 조금 다를 수 있어요).

## 패치

`patches/` 안 파일을 **번호 순서대로** 한 번씩 걸어요(소스 맨 위 폴더에서 `patch -p1`).

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `01-sramflush-disk.patch` | 끌 때 SRAM · 플래시를 저장하고, 디스크 트레이가 늘 '열림'으로 보이게 해요. |
| 2 | `02-flashsave.patch` | 저장된 플래시를 롬 복사 뒤에 불러오고, 큰 `MegaFlashRomSccPlus` 롬에 2MB 플래시를 잡아요. |
| 3 | `03-hbnp1-netplay-sync.patch` | 넷플레이 · 되감기용 상태 고침(hbnp1)이에요. |

- 03 은 01 · 02 **위에** 걸어요. 개발 기록에는 "깨끗한 `572c918` 에 패치 01 · 02 · 03 을 넣고 새로 빌드하면 같은 `83032767` 이 나온다"고 적혀 있어요.
- 이전 코어는 01+02 를 zig/clang 으로 빌드한 것이고, 같은 소스를 gcc 로 빌드한 코어와 8게임 × 3600장에서 화면 · 램 지문이 모두 같았어요(MSX2 첫 프레임 소리 1장만 달랐어요). 같은 판이라는 확인이에요.
- `02-flashsave.patch` 맨 위의 `#` 로 시작하는 설명 세 줄은 `patch` 가 무시하는 머리말이에요.
- **확인하지 못한 것:** 이 폴더를 만들 때 원본 소스가 손에 없어서 **패치를 새로 걸어 보는 시험은 못 했어요.** 대신 원본 파일 내용을 웹에서 확인했어요(`libretro.c` 의 `retro_unload_game`, `WD2793.c` 의 `diskTracks` 이름표 — 원본 `572c918` 과 master 둘 다 위에 적은 대로예요). 패치는 `git apply --check` 나 `patch --dry-run -p1` 로 먼저 확인하세요.

## 원본에 보내기

보낼 만해요. 다만 패치 03 이 158개 파일이라 한 번에 보내면 받아들이기 어려워서, 세 부분으로 나눠 보내는 게 좋아요.

- **A. 끌 때 배터리 SRAM · 플래시 저장**(패치 01). 원본 `572c918` 과 master 둘 다 `boardInfo.destroy()` 호출이 없는 것을 2026-10-29 에 확인했어요.
- **B. WD2793 이 `diskTracks[0]` 로 저장하고 `diskTracks0` 으로 읽는 것**(패치 03). 두 판 모두 그대로인 것을 확인했어요.
- **C. 상태 저장을 완전하고 일정하게**(패치 03). 타이머 · 보드 · 소리칩 상태가 빠지거나 쓰레기가 섞여 넷플레이/되감기가 어긋나요.

보내기 전에 바꿀 것이 둘 있어요. 패치 01 의 '트레이 늘 열림'은 레트로아크 1.22 우회라 빼야 하고, 패치 03 의 `HbZeroNew.cpp`(전역 `operator new` 를 0 으로 채움)는 우리 쪽 우회라 생성자에서 칸을 비우는 식으로 바꿔 보내야 해요. 제목 초안: "Save battery-backed SRAM/flash on unload, fix the WD2793 state tag typo, and make savestates complete and byte-stable". 영어 초안 글은 [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) 의 `upstream_pr_candidate` 에 있어요.

## 라이선스

- 원본 blueMSX 소스 트리는 **파일마다 라이선스가 달라요**(원본 `license.txt`, 사본은 [`LICENSES/blueMSX-libretro_license.txt`](../../LICENSES/blueMSX-libretro_license.txt)): blueMSX 팀이 만든 파일은 BSD 계열 조항, `Fmopl` · `Ymdeltat` · openMSX 에서 온 `OpenMsx*` / `R800Dasm` 등은 GPL, `TinyXML` · `Unzip` 은 ZLIB, `V9938` 은 프리웨어, `Scale2x` 계열은 BSD 로 적혀 있어요.
- 패치는 고친 파일의 **원래 조건**을 그대로 따라요. 합쳐진 바이너리에는 GPL 파일이 들어 있으므로 GPL 조건(소스 공개)을 지키는 것으로 보고, 이 패치와 원본 커밋 정보를 소스로 공개해요.
