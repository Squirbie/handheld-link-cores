<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# Gambatte Link — 넷플레이로 잇는 게임보이 통신 케이블과 게임보이 컬러 적외선

> RetroArch 넷플레이 방을 게임보이 · 게임보이 컬러의 통신 케이블과 적외선 포트로 써서, 기기 두 대가 각자 자기 게임 · 자기 세이브로 와이파이 통신 게임을 하게 해 주는 gambatte 코어예요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/gb-gambatte-link-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| 코어 파일 | `gambatte_libretro.so` (aarch64 리눅스, 4,367,384바이트) |
| 버전 | `v0.5.0-netlink-4041d5a-hb-v5irh3` (통신 규약 이름 `gambatte-hb-link-6`, 패치 이름에서는 v5irh3) |
| md5 | `8c0eb89d9c157eda094b293a4aa0b976` |
| 원본 | [libretro/gambatte-libretro](https://github.com/libretro/gambatte-libretro) 커밋 `4041d5a` |
| 라이선스 | GPL-2.0-only |
| 시험한 기기 | Anbernic RG35XX Pro · KNULLI |

RG35XX Pro(KNULLI, aarch64 리눅스)에 실제로 들어간 최종판이에요.
완성된 코어 파일(`.so`)은 이 폴더가 아니라 릴리스 zip `gb-gambatte-link-linux-aarch64.zip` 안에 들어 있어요(위의 Download 버튼).
이 폴더에는 설명과 패치만 있고, 롬 · BIOS · 세이브는 들어 있지 않아요.

## 무엇을 하나

게임보이(컬러) 게임의 **통신 케이블 대전 · 교환**을 두 기기가 와이파이로 할 수 있게 한 코어예요.
한 사람이 RetroArch 넷플레이 방을 열고 다른 사람이 들어오면, 각 기기는 **자기 게임 · 자기 세이브**를 그대로 돌리고 통신 케이블로 오가는 바이트만 주고받아요. 그래서 세이브가 서로 섞이지 않아요.

게임보이 컬러의 **적외선**도 같은 방으로 이어요. 포켓몬 금 · 은 · 크리스탈의 '이상한 소포(Mystery Gift)', 포켓몬 핀볼의 점수 보내기, 포켓몬 카드 GB의 '카드 뿅!', 나의 캠프장(Boku no Camp-jou)의 물품 교환을 확인했어요.

왜 손봐야 했나: 게임마다 "바이트와 바이트 사이에 정해진 시간 안에 답이 와야 한다"는 규칙이 있어서, 그냥 인터넷으로 보내면 '통신 오류'로 끊겼어요.
이 코어는 보내는 쪽의 게임보이 시간 간격을 바이트마다 함께 보내고, 받는 쪽이 그 시간에 맞춰 기다리거나 따라잡아서 고쳤어요.

확인한 게임 예: 유희왕 듀얼 몬스터즈 1, 포켓몬 카드 GB 1 · 2, 포켓몬 금 · 은 · 크리스탈 교환과 콜로세움, 월드 히어로즈 2 제트, 테트리스 DX · 테트리스 2, 열혈 비치발리볼, 열혈 신기록(びっくり熱血新記録), 몬스터 캡슐 GB, 햄스터 파라다이스 햄 레이스, 비트매니아 GB 세 편, 슈퍼로봇대전(GB) 1, 포켓 배틀.

**두 기기는 같은 판을 쓰세요.** 옛 판(규약 3 · 4)과는 붙지 않아요.
같은 규약 6 안에서도 v4bw 이후 규칙은 두 기기가 함께 바뀌어야 의도대로 돼요.
적외선은 두 기기 모두 v5ir 이상일 때만 되고, 한쪽이 옛 판이면 조용히 안 돼요(게임이 멈추지는 않아요).

## 무엇을 고쳤나

원본 gambatte-libretro는 통신을 TCP 직접 연결('GB Link' 옵션)으로만 지원해요. 이 패치는 그 위에 다음을 더했어요.

1. **넷플레이 방을 통신선으로 쓰는 전송 계층** `libgambatte/libretro/hb_netpacket_serial.h`(`RETRO_ENVIRONMENT_SET_NETPACKET_INTERFACE`, 두 명만, 세 번째는 거절).
   - 바이트마다 보낸 쪽이 지난 바이트 뒤 흘려보낸 게임보이 시간(32비트 간격)을 싣고, 받는 쪽은 다음 간격을 짐작해 게임을 멈춘 채 기다리거나(최대 40ms), 뒤처졌으면 보낸 시각까지 먼저 돌린 뒤 답해요.
   - 5초 안에 상대 바이트가 없으면 `0xFF`(케이블 없음)를 돌려주고, 상대는 아직 안 읽은 그 바이트를 버려요.
   - 코어 옵션 `gambatte_netlink_timing` = `auto` | `v3j` | `bounded`(아래 '코어 옵션' 참고).
   - 시작 장벽: 두 기기가 같이 다시 켜져요(최대 20초). RetroArch 넷플레이 손님은 코어의 `start()`보다 먼저 몇 장을 돌리기 때문에, 불러온 지 1800장 안에 `start()`가 오면 SRAM · RTC는 두고 처음부터 다시 켜고 기다려요.
   - v4bw 규칙: 늦게 받은 바이트는 '받을 때'로 쳐서 기준을 당기고(열혈 신기록), 듣지 않는 상대에게는 두 장 뒤 응답을 돌려주고, 동시에 보내면 방장 바이트가 먼저이고, 번갈아 보내는 흐름에서는 한 틱(240Hz)을 넘겨 달린 뒤에 상대 바이트를 기다려요(몬스터 캡슐 GB).
2. **감바테 자체 버그 둘**
   - `Memory::updateSerial`(`HAVE_NETWORK` 쪽): 바이트가 오가는 도중 게임이 SB · SC · IF를 읽으면, 이미 밀어 넣은 비트 뒤의 비트가 아니라 맨 위 비트를 또 밀어 넣어 값이 돌아가 버려요(`0x20`이 `0x08`로). 남은 비트를 올바른 자리에서 가져오게 고쳤어요.
   - `GB::reset()`: 부트롬이 아직 매핑된 동안 리셋하면 부트롬이 '카트리지 백업'이 되어 게임이 되살아나지 못해요(흰 화면). `full_init()` 앞에서 `bootloader.call_FF50()`으로 카트리지를 먼저 되돌려요.
3. **게임보이 컬러 적외선(FF56)** — 'I' 꾸러미(20바이트)로 시각 · LED · 켜짐을 주고받아요. 두 쪽 포트가 다 켜지면 한 번 만나(방장이 짝을 정함) 두 게임보이 시간을 묶고, RP를 읽을 때 상대 LED를 4096단위(약 0.98ms) 늦게 봐요.
   상대 소식이 그만큼 안 왔으면 그 자리에서 기다려요(최대 3초). 긴 펄스(256단위 이상)는 끝난 뒤 128단위 더 보여요. 포트를 켜 두고 안 읽는 쪽(핀볼 메뉴)은 '듣지 않음'으로 알려서 상대가 멈추지 않아요.
4. **엇갈림 · 듣지 않음에 `00`으로 답하기**(실제 케이블처럼, `FF`는 아예 게임보이가 없을 때만) — 햄스터 파라다이스 햄 레이스.
5. **포켓몬 카드 GB 2**: 받는 쪽이 첫 바이트를 읽기 전에 같은 장 안에 둘째 바이트가 와서 덮어쓰던 것을, 보낸 쪽 틈이 한 장 이상일 때 다음 장 반 틱까지 붙잡아 고쳤어요.
6. **나의 캠프장**: 듣는 상대가 있으면 LED를 켜기 직전에 만나고(인사 펄스를 놓치던 것), 긴 펄스 꼬리는 받는 쪽이 2번 이하 읽었을 때만 남겨요(짧은 비트 길이를 늘리던 것).

패치된 코드와 판 글자(`-hb-v5irh3`) 속 `hb_` · `HB_`로 시작하는 이름과 `hanbang`이라는 글자는 '여기를 고쳤다'는 우리 표시일 뿐이에요. 패치 · 바이너리 · 스크립트가 서로 맞도록 이름을 바꾸지 않고 그대로 뒀어요.

### 확인한 것

- 최종 .so 안에 각 패치가 넣은 표시 글자(`hb-v5irh3`, `ir-tx-meet`, `hold2f`, `crossQ-00`, `unarmed00`, `ir-stop-timeout`, `gambatte-hb-link-6`)가 모두 있고, 이전 판의 `crossQ-ff` · `unarmedFF`는 없어요.
- v5irh3 단계에서 앞 판 기능이 그대로인지 다시 확인했어요(앞 판 v5irh2와 같은 결과): 이상한 소포 4/4, 카드 뿅 1/1, 핀볼 점수 3/3, 테트리스 DX · 카드 GB2 · 몬스터 캡슐 같음. 나의 캠프장 교환은 가상 머신 6/6, 기기용 빌드 2/2. 기기에서는 핀볼 두 대 켜짐 · 점수 전송 · 멈춤 없음을 확인했어요.
- 한계: 기기 와이파이 아래의 장시간 시험, 3인 이상, 소리는 보지 않았어요.

## 코어 옵션

| 옵션 | 값 | 뜻 |
|---|---|---|
| `gambatte_netlink_timing` | `auto`(기본) / `v3j` / `bounded` | 두 기기의 시간선을 얼마나 단단히 묶을지. `bounded`는 세션 전체 가상 시각으로 한쪽이 앞서 달리는 걸 막아요. `auto`는 비트매니아 GB 세 편(롬 크기 + CRC32로 판별)만 `bounded`로, 나머지는 `v3j` 규칙으로 해요. |

## KNULLI 에 넣기

RG35XX Pro에 우리가 한 방식이에요. 환경이 다르면 자리와 이름을 맞춰 고치세요.

1. **코어 파일.** `gambatte_libretro.so`를 SD 카드 userdata의 `/userdata/system/hanbang_cores/`(미리 빌드한 파일이 쓰는 기본 자리)에 넣어요.
   RG35XX Pro 쪽에서는 시스템의 `/usr/lib/libretro/gambatte_libretro.so`가 이 파일을 가리키는 바로가기로 되어 있어서, SD의 파일만 바꾸면 돼요.
   바로가기가 없는 기기라면 루트가 읽기 전용이라 `mount -o remount,rw /` 뒤에 `ln -sfn`으로 만들고 `knulli-save-overlay`로 저장해야 해요.
2. **바꾸는 순서.** 게임이 돌고 있지 않을 때, 새 파일을 옆 이름(`.hbnew`)으로 올려 md5를 확인한 뒤 `mv`로 바꿔요. 옛 파일은 따로 백업해 두세요.
3. **두 기기를 같이** 바꿔요. 같은 판이어야 붙어요. 적외선은 두 기기 모두 v5ir 이상일 때만 돼요.
4. **게임별 설정 줄은 필요 없어요.** 게임보이 · 게임보이 컬러의 기본 코어인 gambatte를 그대로 대신하는 파일이라 `knulli.conf`를 건드리지 않았어요. 코어 옵션 `gambatte_netlink_timing`은 기본값 `auto` 그대로예요. (TGB Dual로 따로 돌리는 몇몇 게임은 이 코어와 상관없어요.)
5. **같이 쓰는 스크립트**(이 저장소의 [`knulli-scripts/`](../../knulli-scripts/) 폴더). 훅만 빼고 `/userdata/system/claude/`(미리 빌드한 파일이 쓰는 기본 자리)에 복사해요.
   - [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh)는 ES 게임 시작 · 종료 훅이고 `/userdata/system/scripts/nds_save_sync.sh`(미리 빌드한 파일이 쓰는 기본 자리)에 둬요. 아래 스크립트들을 게임마다 띄워요.
   - [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py)는 넷플레이가 시작되면 RetroArch가 끄는 SRAM 자동 저장 대신 10초마다 세이브를 카드에 써 줘요. gambatte는 '각자 자기 세이브' 코어 목록에 들어 있어요.
   - [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py)는 같은 게임 방이 열려 있으면 '같이 / 혼자'를 고르는 창이에요. 포켓몬 1 · 2세대, 유희왕, 드래곤 퀘스트 몬스터즈 2 같은 '짝 묶음'을 알아요.
6. 방은 ES의 넷플레이 흐름으로 열어요(방장이 방을 열고 손님이 같은 게임으로 들어옴). 두 기기가 처음 켜질 때 서로 맞추느라 최대 20초 걸릴 수 있어요.

### 다른 기기 · OS에서 쓸 때 주의

- 이 .so는 **aarch64 리눅스 전용**이에요(glibc 심볼 판은 GLIBC_2.33까지만 써요). 다른 CPU · OS에서는 소스 패치로 다시 빌드하세요(`platform=osx` 등). 맥 arm64로는 시험 도구용으로 빌드해 돌려 봤고, 윈도우 · 안드로이드는 해 보지 않았어요.
- RetroArch의 **넷패킷 인터페이스**(`RETRO_ENVIRONMENT_SET_NETPACKET_INTERFACE`)를 지원하는 프런트엔드가 필요해요. 시험은 RetroArch 1.22.2에서 했어요.
- **두 쪽 모두 같은 판**을 쓰세요. 이 코어의 규약(`gambatte-hb-link-6`)은 옛 판(v3j 이전의 규약 3 · 4)과 붙지 않아요.
  같은 규약 6끼리는 판이 달라도 이어지지만, v4bw 이후의 규칙(늦게 받은 바이트 · 듣지 않는 상대 · 동시 보내기)은 두 기기가 함께 바뀌어야 의도대로 돼요.
- 화면 알림 글(`GB 통신: 연결됐어요` · `상대가 없어 혼자 시작 …` · `상대 기다리는 중 · N초`)은 **한국어 UTF-8**로 코드에 들어 있어요. 한글 글꼴이 없는 프런트엔드에서는 네모로 보여요(`libretro.cpp`의 `HB_NP_MSG_*`를 고치면 돼요).
- 상태 불러오기 · 되감기 · 리셋 뒤에는 두 기기가 다시 맞춰져야 해요(두 기기 모두 리셋). 적외선 중에 되감으면 그 판의 묶음이 풀리니 A를 다시 눌러야 해요.
- 두 기기 사이 와이파이 지연이 한쪽 10ms를 넘으면 적외선 화면에서 게임이 느려질 수 있어요(15ms 넘는 환경은 시험하지 않았어요).
- 포켓몬 금 · 은과 크리스탈 사이 적외선 · 케이블 교환은 원작 규칙대로 안 돼요(지역 코드가 달라 '통신 에러').
- `auto`가 `bounded`로 고르는 비트매니아 GB 세 편은 일본판 롬의 크기와 CRC32로 구분해요. 다른 판 롬은 `v3j` 규칙으로 돌아요.

## 소스에서 빌드

기록된 방식 그대로예요. 빌드 기계는 Debian 12(aarch64, gcc 12.2, glibc 2.36)였고, 결과 .so는 glibc 심볼 판을 GLIBC_2.33까지만 써요(기기의 2.40보다 낮아 그대로 돌아요).

```sh
# 패치(이 저장소)
git clone https://github.com/Squirbie/handheld-link-cores.git
CORE="$PWD/handheld-link-cores/cores/gb-gambatte-link"

# 기준 커밋의 원본
git clone https://github.com/libretro/gambatte-libretro.git
cd gambatte-libretro
git checkout 4041d5a6c474d2d01b4cb1e81324b06b51d0147b

# (가) 개별 패치를 차례대로
for p in $(grep -v '^#' "$CORE/patches/series"); do git apply "$CORE/patches/$p"; done
# (나) 또는 한 덩어리(둘 다 하지 마세요)
# git apply "$CORE/patches/all-in-one/gambatte-link-v5irh3-vs-4041d5a.patch"

make -B -j2 platform=unix CC=gcc CXX=g++ 'GIT_VERSION="-4041d5a-hb-v5irh3"'
# 결과: ./gambatte_libretro.so  (strip 하지 않은 상태가 기기에 들어간 파일이에요)
```

- `platform=unix`는 `HAVE_NETWORK=1`을 켜서 이 패치가 컴파일되게 해요.
- `GIT_VERSION`은 코어 정보의 판 글자(`v0.5.0-netlink-4041d5a-hb-v5irh3`)를 정해요. 다른 글자를 써도 동작은 같아요.
- 패치는 `patch -p1`로도 얹혀요.
- 컴파일러가 다르면 바이트까지 같은 .so는 안 나와요. 동작이 같은지는 코어 안의 판 글자와 위 '확인한 것'으로 보세요.

### 다시 만들 수 있는지

- 원본 트리 해시 `a28a8644a1c4987b8407251547d3960b9422710a`가 GitHub의 값과 같아요. 패치를 차례대로 얹으면 기록된 최종 빌드 소스와 파일마다 같은 트리가 나와요. git apply 차례 · git apply 한 덩어리 · patch -p1 차례, 세 방식 모두 같은 트리 `f295e043e76a3096753490d3f501f379d2220b21`이에요.
- **못 한 것:** 이 폴더를 만들 때 코어를 **다시 컴파일하지 않았어요**. 그래서 바이트까지 같은 .so가 나오는지는 확인하지 못했고, '소스 트리가 기록과 같다'와 '.so 안의 표시 글자'까지만 확인했어요.
- 최신 원본(`master`)으로 옮기는 일은 하지 않았어요. 기준은 2024-02 커밋 `4041d5a`예요.

## 패치

이 순서대로 얹어요. `patches/series`에 같은 순서가 적혀 있어요. 한 덩어리로 쓰려면 `patches/all-in-one/gambatte-link-v5irh3-vs-4041d5a.patch` 하나만 쓰세요(개별 패치와 같이 쓰면 두 번 얹혀요).

기준: libretro/gambatte-libretro 커밋 `4041d5a6c474d2d01b4cb1e81324b06b51d0147b`(2024-02-23, "Fetch translations & Recreate libretro_core_options_intl.h"), 트리 해시 `a28a8644a1c4987b8407251547d3960b9422710a`.

| 순서 | 파일 | 하는 일 | 이 단계까지 만든 판 |
|---|---|---|---|
| 1 | [`0001-netpacket-link-cable-with-timing-v4bw.patch`](patches/0001-netpacket-link-cable-with-timing-v4bw.patch) | 전송 계층 · 시간 맞춤 · 감바테 버그 둘 (v2 ~ v4bw 누적, 원본 위 한 번에) | v4bw, md5 `444a461ad8ca7812d48ead0e2aae7495` |
| 2 | [`0002-gbc-infrared-over-netplay-v5ir.patch`](patches/0002-gbc-infrared-over-netplay-v5ir.patch) | 게임보이 컬러 적외선 | v5ir, md5 `60d41b7a85c4e1404640e3d3ad916a9a` |
| 3 | [`0003-reply-00-not-ff-to-unheard-byte-v5irh.patch`](patches/0003-reply-00-not-ff-to-unheard-byte-v5irh.patch) | 듣지 않는 상대에 `00` 답 | v5irh, md5 `2aa5548406d69c9f32f4bef5b13a72fa` |
| 4 | [`0004-hold-second-byte-to-next-frame-v5irh2.patch`](patches/0004-hold-second-byte-to-next-frame-v5irh2.patch) | 포켓몬 카드 GB2 손잡기 | v5irh2, md5 `ccf076adc253367aa2ec04b8c8ec954d` |
| 5 | [`0005-infrared-meet-before-led-and-pulse-tail-v5irh3.patch`](patches/0005-infrared-meet-before-led-and-pulse-tail-v5irh3.patch) | 나의 캠프장 적외선 | v5irh3, md5 `8c0eb89d9c157eda094b293a4aa0b976` |

- 각 패치 머리말(`Subject` · `Origin` · 짧은 요약 · 설명)에 무엇을 왜 바꿨는지 있어요.
- md5는 그 단계에서 만든 .so의 지문이에요. 개발 기록에서 가져온 값이고, 최종판만 이 폴더의 대상 파일과 같아요.
- 버전 이력(모두 2026년): v2 ~ v3j(10/15, 바이트 밀림 · 시간 맞춤 · 비치발리볼 · 포켓몬 카드 GB) → v4bm(10/15, 비트매니아) → v4bt ~ v4bv(10/18 ~ 10/19, 부트롬 중 재시작) → v4bw(10/21, 열혈 신기록 · 몬스터 캡슐 GB) → v5ir(10/26, 적외선) → v5irh → v5irh2 → v5irh3(10/26). v4bw까지는 모두 0001에 들어 있어요.

## 원본에 보내기

2026-10-29 웹으로 확인한 libretro/gambatte-libretro `master`의 모습이에요.

- `Memory::updateSerial`(`HAVE_NETWORK` 쪽)은 지금도 `serialize_value_ >> (8 - serialCnt_)` · `serialize_value_ >> (8 - (serialCnt_ - targetCnt))` 꼴이에요. 맨 위 비트를 또 밀어 넣는 버그가 그대로 남아 있어요.
- `GB::reset()`은 `p_->full_init(false)`만 부르고 그 앞에서 카트리지를 되돌리지 않아요. (기준 커밋 뒤에 `full_init`에 SRAM 지움 인자가 생겼어요.)

**원본에 보낼 만한가요? 네.** 패치 0001 안에서 떼어 낼 수 있는 작은 고침 둘이 있어요. (1) `updateSerial`의 비트 밀기, (2) 리셋 때 부트롬 걷어 내기.
둘 다 몇 줄이고 바이트를 어떻게 보내는지와 상관없어요. 보내기 전에 `master`에 맞게 다시 만들어야 해요.
넷패킷 전송 계층(`hb_netpacket_serial.h`)과 적외선은 이 기기들을 위한 큰 기능이라 후보가 아니에요.

풀 리퀘스트 초안이 있어요. 제목은 "Fix partial serial shift under HAVE_NETWORK and restore ROM bank 0 before re-initialising on reset"예요. 영어 제목 · 본문 초안은 [`UPSTREAM.md`](../../UPSTREAM.md)와 [`cores/MANIFEST.gb.jsonl`](../MANIFEST.gb.jsonl)의 `upstream_pr_candidate`에 있어요. 아직 보내지 않았어요.

## 라이선스

- 원본 gambatte(libretro 판)와 같은 **GPL-2.0-only**예요. 원본 파일 머리말에는 자유 소프트웨어 재단이 낸 GNU 일반 공중 사용 허가서 2판이라고 적혀 있어요(원문: [`LICENSES/gambatte-libretro_COPYING`](../../LICENSES/gambatte-libretro_COPYING)). 이 패치도 같은 조건으로 공개해요.
- 코어(.so)를 나눠 줄 때는 원본 커밋과 이 패치가 대응하는 소스가 돼요. 원본 파일 머리말의 저작권 표시는 그대로 둬야 해요.
