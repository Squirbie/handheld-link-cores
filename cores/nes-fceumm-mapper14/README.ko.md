<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# FCEUmm 매퍼 14 — SL1632 보드용 작업용 램

> 패미컴 매퍼 14(SL1632)에 작업용 램 8KB 를 붙인 FCEUmm 이에요. 프로그램 512KB · 그림 512KB 인 'Downtown Special - Kunio-kun no Jidaigeki Da yo Zenin Shuugou!' 한글화 롬이 검은 화면에서 멈추지 않고 켜져요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/nes-fceumm-mapper14-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| 코어 파일 | `fceumm_libretro.so` (리눅스 aarch64, 4,261,840 바이트, strip 안 한 파일) |
| 판 | 코어가 알리는 판 `(SVN)-63643ba-hb1` (코어 이름 `FCEUmm`) |
| md5 | `d944c5c6451efea1aaab950317886426` |
| sha256 | `0edc2c13f987394f5a7dbbd05c2ce49ec3fadd3f560452ebbfe59ee0c6584f90` |
| 원본 | [libretro/libretro-fceumm](https://github.com/libretro/libretro-fceumm) `63643ba` ("Remove FCEUD_SoundToggle", 2024-01-25). 시험한 기기에 든 순정 FCEUmm 도 같은 커밋이에요 |
| 라이선스 | GPL-2.0-or-later (GPL 2.0 이상) |
| 시험한 기기 | Anbernic RG35XX Pro · KNULLI |

## 무엇을 하나

작업용 램은 게임 카트리지 보드에 달린 여분의 메모리예요. 게임이 임시 작업장으로 쓰고, 배터리가 있는 보드에서는 세이브를 담기도 해요. 순정 FCEUmm 은 패미컴 매퍼 14(SL1632 보드)에 이 램을 붙여 주지 않아서, 롬 하나가 아예 켜지지 않았어요.

- **뭐가 문제였나.** 'Downtown Special - Kunio-kun no Jidaigeki Da yo Zenin Shuugou!' 한글화 롬(매퍼 14, 프로그램 512KB · 그림 512KB)은 작업용 램 자리(`$6000`~`$7FFF`)를 1만 1,735번 읽고 써요. 그런데 순정 FCEUmm 의 매퍼 14 는 **작업용 램이 0바이트**이고, 게다가 `$4100`~`$FFFF` 쓰기를 전부 매퍼 레지스터로 받아서, 램을 붙여도 `$6000`~`$7FFF` 쓰기가 사라졌어요. 그래서 검은 화면에서 멈췄어요.
- **고친 것.** 작업용 램 8KB 를 붙이고(배터리 표시가 있는 롬이면 저장도 돼요), 매퍼 레지스터 쓰기를 `$4100`~`$5FFF` 와 `$8000`~`$FFFF` 로 나눠서 `$6000`~`$7FFF` 는 램으로 보냈어요.
- **결과.** 한글 타이틀부터 게임 모드(1P와 COM · 1P와 2P · 협력 · 대전)와 싸움 화면까지 초당 60~61프레임으로 돌아요.
- **코어 하나로 다 돌아요.** 이 롬만 따로 메센(Mesen) 코어로 켜던 것을 없앴어요. 메센은 이 기기에서 무거워서 혼자 해도 초당 45~49프레임이었고, 두 기기 코어가 달라 같이하기도 안 붙었어요. 이제 다른 패미컴 게임처럼 FCEUmm 으로 돌아요.

## 무엇을 고쳤나

고친 것은 전부 패치 [`patches/mapper14_wram.patch`](patches/mapper14_wram.patch) 한 장, `src/mappers/mapper014.c` 두 곳이에요. 우리가 넣은 주석은 `hanbang:` 으로 시작하는데, '우리가 고친 곳' 표시일 뿐이에요.

1. `UNLSL1632_Init` 에서 `GenMMC3_Init(info, 256, 512, 0, 0)` 를 `GenMMC3_Init(info, 512, 512, 8, info->battery)` 로 바꿔요. 프로그램 크기는 256 → 512KB, 작업용 램은 0 → 8KB 이고, 배터리는 롬 머리 값을 따라요.
2. `UNLSL1632Power` 에서 쓰기 처리 `SetWriteHandler(0x4100, 0xFFFF, UNLSL1632CMDWrite)` 를 `0x4100`~`0x5FFF` 와 `0x8000`~`0xFFFF` 둘로 나눠요. 그러면 `$6000`~`$7FFF` 는 `GenMMC3Power` 가 정해 둔 작업용 램 처리에 맡겨져요.
3. 메센의 `MMC3_14` 는 MMC3 기본 램을 붙여서 이 롬이 원래 돌았어요. 같은 동작이에요.

```diff
--- a/src/mappers/mapper014.c
+++ b/src/mappers/mapper014.c
@@ -98,11 +98,14 @@
 
 static void UNLSL1632Power(void) {
 	GenMMC3Power();
-	SetWriteHandler(0x4100, 0xFFFF, UNLSL1632CMDWrite);
+	/* hanbang: leave $6000-$7FFF to the work RAM handlers set by GenMMC3Power */
+	SetWriteHandler(0x4100, 0x5FFF, UNLSL1632CMDWrite);
+	SetWriteHandler(0x8000, 0xFFFF, UNLSL1632CMDWrite);
 }
 
 void UNLSL1632_Init(CartInfo *info) {
-	GenMMC3_Init(info, 256, 512, 0, 0);
+	/* hanbang: 8KB work RAM at $6000 (Downtown Special Korean 512K/512K hack uses it; Mesen gives it too) */
+	GenMMC3_Init(info, 512, 512, 8, info->battery);
 	cwrap = UNLSL1632CW;
 	info->Power = UNLSL1632Power;
 	GameStateRestore = StateRestore;
```

## KNULLI 에 넣기

우리가 쓰는 방식이에요. [Releases](https://github.com/Squirbie/handheld-link-cores/releases) 에서 `nes-fceumm-mapper14-linux-aarch64.zip` 을 받아 풀어 주세요.

**순정 이름 그대로 바꿔 넣어요.** 그러면 `.info` · ES 기능 · `knulli.conf` 를 손대지 않아도 패미컴 모든 게임이 이 코어로 켜져요. 파일은 `/userdata/system/hanbang_cores/`(미리 빌드한 파일이 쓰는 기본 자리)에 두고, 레트로아크가 찾는 코어 자리에는 바로가기(심볼릭 링크)를 걸어요. 게임을 끈 상태에서 아래처럼 해요.

```sh
HB=/userdata/system/hanbang_cores/fceumm_libretro.so
mkdir -p /userdata/system/hanbang_cores
cat > $HB.new < fceumm_libretro.so       # md5 가 d944c5c6… 인지 먼저 확인하세요
chmod 755 $HB.new && mv -f $HB.new $HB && sync
mount -o remount,rw /
ln -sfn $HB /usr/lib/libretro/fceumm_libretro.so
knulli-save-overlay
```

- **되돌리기.** 덧칠(overlay) 쪽 파일을 **덧칠 경로로** 지워요. `rm /overlay/overlay/usr/lib/libretro/fceumm_libretro.so && knulli-save-overlay` 를 하고 재부팅하세요. 겉 경로(`/usr/lib/libretro/…`)를 지우면 덧칠이 '지움 표시'를 남겨서 파일이 아예 사라지니 조심하세요. 원래 코어는 따로 받아 두세요(시험한 기기의 순정 코어는 md5 `4661bc574366aa7a1bd10f388f555544` 였어요).
- 이 롬을 메센 코어로 켜게 해 둔 `knulli.conf` 줄이 있으면 지워요. 이 코어로 충분해요.
- 같이하기를 하려면 두 기기에 **같은 파일**을 넣어야 가장 안전해요. 판 글자가 달라도 붙기는 하지만, 에뮬레이션 상태가 어긋날 수 있어요.

### 다른 기기 · OS 에서 쓸 때

- `.so` 는 **aarch64 리눅스**(glibc 2.33 이하 기호, `libm` · `libc` 필요)용이에요. 다른 CPU · OS 는 패치로 다시 빌드해야 해요.
- **최신 원본에는 이 패치가 그대로 걸리지 않아요.** 원본은 그 뒤에 `src/mappers/` 를 `src/boards/` 로 옮기고, 매퍼 14 를 `asic_mmc3.h` 기반 새 구현(`src/boards/14.c`)으로 다시 썼어요(2026-10-11 의 `ac0d00a` 에서 확인). 새 구현에서도 이 롬이 도는지는 확인하지 않았어요.
- 알려진 한계(이 패치와 무관): 여신전생 2(Megami Tensei II) 한글판은 시험한 세 코어 모두 제목 그림이 깨져요. 그림 램을 256KB 로 늘린 특이한 패치라서 그래요. 한글 글은 FCEUmm 에서만 바르게 나와서 FCEUmm 그대로 쓰고 있어요. 오리사냥(Duck Hunt)처럼 빛총(Zapper)은 마우스로만 받아서 이 기기에서는 못 써요.

## 소스에서 빌드

```sh
git clone https://github.com/libretro/libretro-fceumm
cd libretro-fceumm
git checkout 63643ba02c8eaea15dbe167ef907f3da7a3e6fd7
patch -p1 < /path/to/patches/mapper14_wram.patch
make -f Makefile.libretro platform=unix GIT_VERSION="-63643ba-hb1"      # Debian 12 aarch64, gcc 12, -O2
# → fceumm_libretro.so
```

- 코어가 알리는 판 글자 `(SVN)-63643ba-hb1` 은 `GIT_VERSION` 으로 넣은 거예요. 레트로아크 넷플레이는 코어 **이름**(`FCEUmm`)만 같으면 붙고 판 글자가 다르면 경고만 하므로(레트로아크 소스 확인), 아직 순정인 기기와도 붙어요.
- 개발 때 가상 머신(Debian 12, gcc 12.2.0, `-O2`)에서 빌드했어요. CPU 플래그는 따로 주지 않았어요. 위 명령은 원본 `Makefile.libretro` 를 읽고 정리한 것이라, 우리 가상 머신 스크립트와 글자가 조금 다를 수 있어요.

## 패치

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | [`mapper14_wram.patch`](patches/mapper14_wram.patch) | 매퍼 14 에 작업용 램 8KB 를 붙이고 매퍼 레지스터 쓰기 구간을 나눠 `$6000`~`$7FFF` 가 램에 닿게 해요(`src/mappers/mapper014.c` 두 곳). 이 빌드의 이름은 `hb1` 이고 md5 는 `d944c5c6451efea1aaab950317886426` 이에요 |

- **확인함**(웹, 2026-10-29): 원본 `63643ba` 의 `src/mappers/mapper014.c`(110줄)에 패치가 지우는 두 줄 — `SetWriteHandler(0x4100, 0xFFFF, UNLSL1632CMDWrite);` 와 `GenMMC3_Init(info, 256, 512, 0, 0);` — 이 그대로 있어요.
- **못 함**: 이번 정리에서 패치를 새로 걸어 보는 시험은 못 했어요. 해당 커밋 소스가 손에 없었어요. `d944c5c6` 을 만든 빌드는 개발 때 이 소스로 가상 머신에서 한 거예요.
- **다른 게임이 안 망가졌나?**(개발 때) 시험 기기의 패미컴 234개 중 44개를 골랐어요. 매퍼별로 롬 1개씩, 매퍼 14 롬, 디스크 시스템이에요. 순정 코어와 이 코어로 각각 600프레임을 돌려 마지막 화면을 비교했더니 **43개는 한 픽셀도 안 달랐어요.** 다른 하나는 이 롬이에요(순정은 검은 화면, 여기서는 타이틀 화면 — 고친 것). 43개 가운데 여신전생 2 한글판은 처음에 앞서 돈 순정이 만든 세이브를 읽은 차이로 달랐고, 세이브를 지우고 둘 다 다시 돌리니 같았어요. 같은 장면에서 CPU 사용량도 순정과 같았어요(레트로아크 메인 스레드 44~47% 대 40~48%).

## 원본에 보내기

지금은 보내지 않아요. `63643ba` 의 옛 구현(`src/mappers/mapper014.c`)에서는 분명한 결함이었어요(작업용 램이 없고, `$6000`~`$7FFF` 쓰기를 레지스터가 가로챔). 하지만 원본이 그 뒤에 파일을 `src/boards/14.c` 로 옮기고 매퍼 14 를 `asic_mmc3.h` 기반 새 구현으로 다시 써서(2026-10-11 `ac0d00a` 확인) 이 패치는 더 걸리지 않아요. 새 구현에서도 같은 한글 롬이 검은 화면이면 그때 새 코드에 맞춰 작은 PR 이나 이슈로 보내면 돼요. 자세한 것은 [`cores/MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) 의 `upstream_pr_candidate` 에 있어요.

## 라이선스

원본 FCEUmm 은 **GPL-2.0 이상(GPL-2.0-or-later)** 이에요(`Copying` 은 GPLv2 이고 [`LICENSES/libretro-fceumm_Copying`](../../LICENSES/libretro-fceumm_Copying) 에 같이 뒀어요. 파일 머리말은 "version 2 … or (at your option) any later version"). 이 패치도 같은 조건이고, 코어 바이너리를 배포할 때는 고친 소스(이 패치)를 함께 공개해요.
