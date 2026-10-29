<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# DOSBox Pure IPX — 레트로아크가 꺼지지 않는 IPX 넷플레이

> 레트로아크 넷플레이가 시작되면 DOS 를 IPX 를 켠 채로 다시 켜서, 휴대기기에서 헤러틱 · 헥센 같은 IPX 게임을 넷플레이로 열 때 레트로아크가 꺼지던 것을 피하는 DOSBox Pure 0.9.9 빌드예요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/dos-dosbox-pure-ipx-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| **코어 파일** | `dosbox_pure_hb_ipx_libretro.so` — aarch64 리눅스용, 2,627,720 바이트, strip 됨 (git 에는 없고 릴리스 zip 안에 있어요) |
| **버전** | `0.9.9` (고친 곳이 `[DOSBOX] hanbang: network requested` 로 시작하는 기록 글을 남겨요) |
| **md5** | `20380390bed1c8042b5264b259d16e85` |
| **원본** | Codeberg 의 [schelling/dosbox-pure](https://codeberg.org/schelling/dosbox-pure) @ [`6108e45`](https://codeberg.org/schelling/dosbox-pure/commit/6108e45e5f1c4ba7d66f32aa109027afa67d74a9) (태그 `0.9.9`, "Set version to 0.9.9", 2023-12-23). KNULLI 순정 코어도 0.9.9 예요. 옛 주소 `github.com/schellingb/dosbox-pure` 에는 '옮겼음' 안내만 남아 있어요. |
| **라이선스** | GPL-2.0 이상 (GPL-2.0-or-later) |
| **시험한 환경** | Anbernic RG35XX Pro · KNULLI · RetroArch 1.22.2 (확인한 환경은 이것뿐이에요) |

## 무엇을 하나

기기(RetroArch 1.22.2)에서 헤러틱 · 헥센을 둘이서 하려고 넷플레이 방을 열거나 들어갈 때 **레트로아크가 -11(SIGSEGV)로 꺼지는** 일이 있었어요.

- IPXSETUP 이 'IPX not detected' 로 한 번 실패한 뒤 방을 열거나 들어가면 꺼졌어요(손님이 없어도).
- 방장으로 켜자마자(1초 안) IPXSETUP 을 돌리면 꺼졌어요(1분 뒤에는 괜찮아요).

**원인 줄은 확정하지 못했어요.** 순정 0.9.9 로 맥 3세션 · VM(aarch64, gdb 아래) 31세션, 같은 길을 돌려도 한 번도 안 꺼졌어요. 기기에만 있는 조건(KNULLI 레트로아크 빌드 · 속도 · 와이파이 · 소리 …)이 겹쳐야 나는 것으로 보여요. 그래서 한 줄을 고치는 대신, 의심 가는 두 갈래를 **아예 타지 않게** 했어요.

**바뀐 동작:** 돌고 있는 DOS 에서 넷플레이가 시작되면 **DOS 를 1~2초 다시 켜요**(저장하지 않은 진행은 사라져요). 순정은 DOS 를 켠 지 10초 안에만 이랬고, 그 뒤에는 IPX 만 끼워 넣어서 게임이 그대로였지만 IPXSETUP 이 다시 돌지 않아 협동이 안 됐어요(VM 순정 손님 참가 10번 중 8번). 혼자 하는 DOS 게임은 순정과 똑같이 돌아요.

## 무엇을 고쳤나

`dosbox_pure_libretro.cpp` 의 `DBP_EnableNetwork()` 한 곳(14줄 추가 · 2줄 삭제)이에요. 0.9.9 는 넷플레이 시작 콜백 안에서 세 갈래로 움직여요.

1. DOS 를 켠 지 10초 안이면 콜백 **안에서** `retro_reset()` 을 불러 코어 전체를 다시 켜요.
2. 그 밖이면 DOS 스레드를 프레임 중간에 세워 둔 채 메인 스레드에서 `ipx` · `serial` 구역을 지웠다 다시 만들어요(IVT 0x7A/0x73, IRQ11, 콜백, 타이머, BIOS COM 값).
3. DOSBox 가 꺼진 상태(`control == NULL`)면 NULL 을 읽어요.

이 패치는 1 · 2 를 없애요. 돌고 있는 DOS 는 `dbp_state = DBPSTATE_REBOOT` 로 표시만 하고, 다음 `retro_run` 맨 앞에서 옵션을 바꿀 때 쓰는 원래 길(`DBP_ForceReset`)로 DOS 를 다시 켜요. `init_dosbox` 가 DOS 스레드를 시작하기 **전에** IPX · 모뎀을 켜요. OS 이미지로 부팅한 경우(`BOOT`)만 순정 동작 그대로예요. 3번은 표시만 하고 끝내요. 기기 기록에서 찾을 수 있게 `[DOSBOX] hanbang: network requested (state N, program X) - restarting DOS with IPX/modem` 한 줄이 남아요.

그 기록 글과 코드 주석에 들어 있는 `hanbang` 은 우리가 고친 곳 표시일 뿐이에요.

## 코어 옵션

이 빌드는 새 코어 옵션을 더하지 않았어요. 순정 `dosbox_pure_*` 옵션을 그대로 써요. KNULLI 설정기는 코어 이름이 `dosbox_pure` 일 때만 그 옵션(svga · 16MB · sb16 …)을 적용해서, 순정 이름 그대로 넣어요(아래 참고).

## KNULLI 에 넣기

**순정 이름 그대로 바꿔 넣어요.** KNULLI 설정기는 코어 이름이 `dosbox_pure` 일 때만 `dosbox_pure_*` 옵션을 쓰고, ES 기능(패드 → 키보드)도 코어 이름에 붙어 있어서 새 이름을 쓰면 둘 다 빠져요. 두 기기에 **같은 파일**을 넣어요. [최신 릴리스](https://github.com/Squirbie/handheld-link-cores/releases/latest)에서 `dos-dosbox-pure-ipx-linux-aarch64.zip` 을 받아 풀고, 게임을 끈 상태에서 넣어요.

**시작하기 전에**

- 미리 빌드한 `.so` 는 **aarch64 리눅스**(glibc 2.34 이하)용이에요. 다른 CPU · OS 는 패치로 다시 빌드해야 해요.
- 확인한 환경은 **KNULLI + RetroArch 1.22.2** 뿐이에요. 꺼짐 원인이 KNULLI 쪽 레트로아크 · 와이파이 · 소리 같은 다른 곳이면 이 패치로 안 없어질 수 있어요.
- **넷플레이를 시작하면 모든 DOS 게임이 다시 켜져요.** 저장하지 않은 진행은 사라져요. 혼자 하는 DOS 게임에는 영향이 없어요(넷플레이가 없으면 다시 켜기가 0번).
- `-nodes 2` 라 두 명만 시험했어요(세 대는 안 해 봤어요). 손님이 나가면 방장 게임이 멈춰요(둠 엔진 원래 동작, 핫키로 끄면 돼요).
- KNULLI 를 업데이트하면 바로가기가 덮여 순정으로 돌아가고 꺼짐도 다시 생길 수 있어요. 업데이트 뒤에 링크를 확인하세요.
- 푼 파일을 확인하세요: md5 는 위 표와 같고, sha256 은 `ade7d774f0ac78c7b41f1818b958576b22322067dc38e6fff577ef2e67cfec86` 예요.

**순서.** 파일을 `/userdata/system/hanbang_cores/` (미리 빌드한 파일이 쓰는 기본 자리)에 두고, 순정 이름이 그 파일을 가리키게 해요.

```sh
HC=/userdata/system/hanbang_cores
LIB=/usr/lib/libretro/dosbox_pure_libretro.so
mkdir -p $HC
# 1) 지금 코어가 0.9.9 순정인지 확인 (아니면 — 예: KNULLI 업데이트로 새 판 — 멈추고 새 판 바탕으로 다시 빌드)
# 2) 순정 사본을 처음 한 번만 남겨요 (바로가기가 아닐 때만)
[ -e $HC/dosbox_pure_libretro.so.stock_0.9.9 ] || [ -L $LIB ] || cp $LIB $HC/dosbox_pure_libretro.so.stock_0.9.9
# 3) 고친 파일을 올리고 md5 가 20380390bed1c8042b5264b259d16e85 인지 확인한 뒤
cat > $HC/dosbox_pure_hb_ipx_libretro.so.new < dosbox_pure_hb_ipx_libretro.so
mv -f $HC/dosbox_pure_hb_ipx_libretro.so.new $HC/dosbox_pure_hb_ipx_libretro.so && sync
mount -o remount,rw /
ln -sfn $HC/dosbox_pure_hb_ipx_libretro.so $LIB
knulli-save-overlay
```

- **되돌리기:** `ln -sfn $HC/dosbox_pure_libretro.so.stock_0.9.9 $LIB && knulli-save-overlay`.
- **자동 시작은 이 폴더에 넣지 않았어요.** 우리는 헤러틱 · 헥센 세이브 꾸러미에 `AUTOBOOT.DBP` → `HBNET.BAT` 를 넣어서 'IPX 없음 = 혼자 게임 / IPX 있음(넷플레이로 DOS 가 다시 켜짐) = `IPXSETUP.EXE -nodes 2`, 거기서 Esc 면 혼자 게임' 으로 이었어요(17바이트 기계어 `HBIPX.COM` 이 `INT 2F AX=7A00` 로 IPX 유무를 알려 줘요). 이 코어만 넣으면 넷플레이 시작 뒤 DOS 안에서 `IPXSETUP` 을 직접 돌려야 해요.

## 소스에서 빌드

```sh
git clone https://codeberg.org/schelling/dosbox-pure
cd dosbox-pure
git checkout 6108e45e5f1c4ba7d66f32aa109027afa67d74a9        # 태그 0.9.9
PATCHES=/path/to/handheld-link-cores/cores/dos-dosbox-pure-ipx/patches
git apply "$PATCHES"/0001-hanbang-restart-DOS-instead-of-live-IPX-modem-switch.patch     # 또는 patch -p1 < 같은 파일
make -j2 BUILD=RELEASE MAKE_CPUFLAGS='-mcpu=cortex-a53'       # Debian 12 aarch64, gcc 12.2.0 기준
# -> dosbox_pure_libretro.so   (기기에는 dosbox_pure_hb_ipx_libretro.so 이름으로 두었어요)
```

- `-mcpu=cortex-a53` 은 RG35XX 계열(H700) 맞춤이에요. 다른 CPU 면 바꾸세요.
- 개발 때 확인: `NEEDED` = `libstdc++` · `libm` · `libgcc_s` · `libc`, 필요한 glibc ≤ 2.34 · GLIBCXX ≤ 3.4.29, 내보낸 함수 = `retro_*` 25개 + C++ 템플릿 약한 기호 44개.

## 패치

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | `0001-hanbang-restart-DOS-instead-of-live-IPX-modem-switch.patch` | 넷플레이 시작 때 DOS 를 다시 켜서 IPX · 모뎀을 처음부터 켜요(커밋 `308cfebd`). |

- **확인한 것(2026-10-29, 맥에서).** 원본 `6108e45` 에 패치를 걸면 우리 갈래 `hb_ipx`(커밋 `308cfebd`)의 소스 트리와 **똑같아요.** 개발 때 빌드한 파일의 md5 가 `20380390bed1c8042b5264b259d16e85` 이고 소스가 `hb_ipx 308cfebd` 예요.
- **시험 결과(개발 기록).** 고친 판 넷플레이 **60세션**(VM 54 + 맥 6), 혼자 켜기 7번, **꺼짐 0번**. 두 대 세션 22번 중 20번이 협동이었어요. 기기에 넣을 바로 그 파일(`20380390`)로 VM 12세션 꺼짐 0, 협동 6. 기기 두 대로 헤러틱 · 헥센 같이하기를 확인했어요.
- **정상 협동의 근거.** 손님이 들어가고 3초 뒤 협동이 시작됐고, 지도에 초록 · 노랑 화살표 둘이 같은 자리에 보였고, 헥센에서는 한쪽이 앞으로 가면 다른 쪽 화면 속 그 사람이 멀어졌어요.

## 원본에 보내기

보내지 않아요. 꺼짐은 기기에서만 났고 원인 줄을 확정하지 못했어요(순정은 맥/VM 34세션에서 재현 안 됨). 넷플레이를 시작하면 돌던 DOS 가 다시 켜지는 동작 변경이라, 고침보다는 RG35XX + RetroArch 1.22.2 에 맞춘 우회에 가까워요. 함께 있던 NULL 읽기 막기(`control == NULL`)는 원본이 이미 넣었어요(개발 때 확인: 2026-02-05 `77061c2`). [`../MANIFEST.misc.jsonl`](../MANIFEST.misc.jsonl) 의 `upstream_pr_candidate` 도 '보낼 만하지 않음'으로 적혀 있어요.

개발 때 확인한 기록: 최신 원본(Codeberg `main` `468dad0`, 2026-10-19)도 나머지 두 갈래(콜백 안 리셋 · 실시간 끼우기)는 그대로였어요. 이번에는 Codeberg 쪽 페이지를 자동으로 읽을 수 없어 다시 확인하지 못했어요.

## 라이선스

- 원본 DOSBox Pure 는 **GPL-2.0 이상**이에요(`LICENSE` = GPLv2, 파일 머리말은 "version 2 … or (at your option) any later version", 코어 정보는 `GPLv2`). 라이선스 원문은 [`LICENSES/dosbox-pure_LICENSE`](../../LICENSES/dosbox-pure_LICENSE) 에 있어요. 고친 곳에는 'hanbang 2026-10-19' 주석을 달았고 원래 저작권 머리말은 그대로예요.
- 이 코어를 넣은 바이너리를 배포할 때는 **고친 소스(이 패치)** 를 함께 공개해야 해요.
