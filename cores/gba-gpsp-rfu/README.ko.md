<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# gpSP RFU — 와이파이에도 끊기지 않는 GBA 무선 어댑터

> gpSP의 무선 어댑터(RFU) 흉내를 RetroArch 넷플레이 와이파이에서도 버티게 고쳐서, 포켓몬 파이어레드 · 리프그린 · 에메랄드의 교환 · 배틀을 기기 두 대가 와이파이로 안정적으로 하게 해 주는 코어예요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/gba-gpsp-rfu-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| 코어 파일 | `gpsp_libretro.so` (aarch64 리눅스, 다이나렉 포함, 724,264바이트, strip 됨) |
| 버전 | `v1.1.0-5819380-hb4` (패치 이름에서는 v3) |
| md5 | `6c86b647977fafeea3a5cccfeb51d5a1` |
| sha256 | `e21bf6d425f6d7a0e4818f4655154621e3d99f5a5a1d68d4a1564dc662e944a4` |
| 원본 | [libretro/gpsp](https://github.com/libretro/gpsp) 커밋 `5819380`(2026-09-19, 이 판을 만들 때의 최신 `master`) |
| 라이선스 | GPL-2.0-or-later |
| 시험한 기기 | Anbernic RG35XX Pro · KNULLI, Anbernic RG DS Plus |

RG35XX Pro(KNULLI, aarch64 리눅스)에 실제로 들어간 최종판이에요.
완성된 코어 파일(`.so`)은 이 폴더가 아니라 릴리스 zip `gba-gpsp-rfu-linux-aarch64.zip` 안에 들어 있어요(위의 Download 버튼).
이 폴더에는 설명과 패치만 있고, 롬 · BIOS · 세이브는 들어 있지 않아요.

## 이번 판에서 바뀐 것 (2026-11)

- 우리 패치 세 개(v3)는 그대로이고, 밑에 깔린 원본만 2024-02 커밋 `4caf7a1`에서 최신 `master` `5819380`으로 옮겼어요.
  - 원본이 그사이 넣은 것도 함께 들어와요.
    - 통신 케이블 모드: `gpsp_serial` = `mul_poke`(포켓몬 3세대 케이블 교환 · 대전), `mul_aw1` · `mul_aw2`(어드밴스 워즈).
    - 새 코어 옵션 둘: `gpsp_rtc_time_source` · `gpsp_sound_rate`.
    - 무선 쪽의 메모리 안전 · 재진입 정리와 결정성 고침.
  - 옮길 때 손으로 맞춘 곳은 한 곳이에요(`0003` 머리말 참고). 옛 v3 소스에 원본의 변화만 합친 결과와 이 판의 소스는, 그 한 곳에 단 주석 한 줄 말고는 같아요.
- 빌드를 zig로 바꿔 glibc 2.17 기준으로 지었어요. 그래서 더 옛 시스템에서도 돌아요. 옛 판은 GLIBC_2.33까지 썼어요.
- 넷패킷 모양 · 버전 글자(`gpSP v1.0`)는 그대로라서, 옛 판(v3 · v2 · 순정)과 섞여도 무선으로 붙어요.

## 무엇을 하나

GBA 포켓몬 파이어레드 · 리프그린 · 에메랄드는 **무선 어댑터**(Wireless Adapter)로 교환 · 배틀을 해요.
gpSP는 이 어댑터를 흉내 내고, RetroArch 넷플레이로 두 기기를 이어요. 두 기기가 **각자 자기 게임 · 자기 세이브**를 돌리고 무선 신호만 주고받아요.

원본 gpSP는 와이파이 지연(수십 ~ 수백 ms, 가끔 0.5초 멈춤)이 있으면 **교환 중 통신 오류**가 났어요.
어댑터가 몇 ms 안에 답한다고 가정하는데 넷플레이는 훨씬 느리고, 받은 패킷을 담는 줄이 4칸뿐이라 한꺼번에 오면 버렸기 때문이에요.

이 판은 세 단계로 고쳤어요.

1. **v1:** 시간 제한을 1.2초로 늘려서 통신 오류는 없앴지만, 게임 안 리더가 답을 1.2초씩 기다려 **교환방이 많이 느려졌어요**(흔들릴 때 리더가 손님의 0.2배 속도).
2. **v2:** 답 기다림은 게임 원래 값으로 되돌리고, 패킷 줄을 128칸으로 늘려 늦은 답을 버리지 않게 했어요. 끊김은 남은 패킷을 다 읽은 뒤에 반영해요.
3. **v3(이 판):** 기다리는 동안의 받기 호출을 줄이고, 밀린 손님 줄을 따라잡게 해서 **프레임 드랍 · 답답함**을 줄였어요.

두 기기가 모두 v3일 때 효과가 가장 커요. 옛 판(순정 · v1 · v2)과 섞여도 붙기는 해요.

## 무엇을 고쳤나

이 폴더의 패치는 `rfu.c`와 `cpu_threaded.c`만 건드려요.

- **0001 arm64 리눅스 캐시 맞춤** — `platform_cache_sync`에서 `dc cvau → dsb ish → ic ivau → dsb ish; isb` 전체 순서를 직접 해요.
  zig로 빌드하면 `__clear_cache`에 `DSB ISH`가 빠져 Cortex-A53이 새로 만든 다이나렉 코드를 옛 캐시(0 = UDF)로 읽고 SIGILL이 났어요. 이 판은 zig로 지었기 때문에 꼭 필요해요. gcc로 빌드해도 해롭지 않아요.
- **0002 와이파이 넷플레이 견디기(v2)**
  - 끊김 판단은 소식 없이 1.2초(`RFU_NET_TIMEOUT_CYCLES`). 리더의 답 기다림은 게임 값(약 11ms) 그대로.
  - 받은 패킷 줄: 4칸 밀어내기 배열 → 128칸 돌림 줄(`RFU_QUEUE_LEN`). 빈 패킷은 줄에 넣지 않아요.
  - 손님 게임에는 리더 패킷을 한 장에 1개씩만 넘기고(`RFU_CLIENT_PER_FRAME`), 리더는 '받았음'(ACK)이 12개 넘게 밀리거나(`RFU_PIPE_MAX`) 줄이 10개 넘는다고 알려 온 손님의 패킷이 없으면(`RFU_PEER_Q_MAX`) 최대 1.2초 기다려요.
  - 손님의 ACK 넷째 칸(원래 늘 0)에 자기 줄 길이를 실어요(표시 `0x51000000` 'Q'). 순정 · v1은 0을 보내고 읽지 않아서 섞여도 붙어요.
  - DISCONNECT는 그 앞에 온 패킷을 게임이 다 읽은 뒤에 반영해요(마지막 인사를 받게).
  - `HOST_SEND` · `CLIENT_SEND` · ACK는 지금 상대(`client_id`)가 보낸 것만 받고, 손님 패킷 길이를 검사해요(`blen <= 16 && len >= blen + 12`; 원본은 16바이트 칸에 길이 검사 없이 복사해요).
- **0003 덜 기다리기(v3)**
  - 기다리는 동안 `netpacket_poll_receive()`를 CPU 이벤트마다(손님은 프레임당 약 600번) 부르지 않고 1/8 프레임마다 + 기다림 시작 때 한 번만(`RFU_POLL_CYCLES`).
  - 리더의 '응답 없음' 기다림 상한 1/360초(약 2.8ms, `RFU_RESP_CAP_CYCLES`; 게임 값이 더 짧으면 게임 값).
  - 손님 줄이 2개 이상 밀리면 한 장에 2개까지 넘겨 따라잡아요(`RFU_CLIENT_CATCHUP_Q`). 버리는 패킷은 없어요.
  - 시험용 계측(`HB_STATS`)은 기본으로 꺼져 있어요. 넷패킷 모양 · 버전 글자(`gpSP v1.0`)는 그대로예요.

패치된 코드 속 `hb_` · `HB_`로 시작하는 이름과 `hanbang` · `한방`이라는 글자(판 글자 `5819380-hb4`의 `hb` 포함)는 '여기를 고쳤다'는 우리 표시일 뿐이에요. 패치 안의 주석은 한국어이고 같은 표시가 들어 있어요. 패치 · 바이너리 · 스크립트가 서로 맞도록 모두 그대로 뒀어요.

### 확인한 것

- **이 판(바탕 `5819380`)**
  - RG35XX Pro 두 대(KNULLI, 집 와이파이 넷플레이): 파이어레드 ↔ 리프그린 다이렉트 코너 → 트레이드센터.
    - 교환방에 가만히 60초 있는 동안 두 기기 모두 게임 시간이 59.1초 흘렀어요(옛 바탕 v3 59.15초).
    - 이어서 교환 한 번을 끝까지 했고, 교환하는 45초 동안 게임 진행 비율은 0.916이었어요(옛 바탕 v3 0.917 — 교환 끝 저장 맞추기는 게임 구조).
  - RG DS Plus 두 대: 루비 ↔ 사파이어 케이블 교환(`mul_poke`)과 파이어레드 ↔ 리프그린 무선 교환이 모두 끝까지 됐고, 양쪽 세이브에서 포켓몬이 서로 바뀐 것까지 확인했어요. 통신 오류 0이었어요.
- **옛 바탕(`4caf7a1`)에서 잰 것** — RFU 코드는 이 판과 같아요.
  - 가상 머신에서 RetroArch 1.22.2 두 개를 127.0.0.1 넷플레이로 이어 시험했어요(`tc netem`으로 한 방향 20 ~ 80ms + 손실 1%).
    - 흔들리는 배틀 155초: 리더가 붙잡힌 시간 3.4 / 5.1초 → 2.2 / 1.2초, 멈춘 장 335 / 414 → 182 / 127, 손님 줄 평균 5.7 / 6.0 → 0.8(v3 앞 → 뒤).
    - 깨끗한 연결 교환방: 두 쪽 줄 합 4.5 → 1.2장(약 55ms 덜 늦음), 손님의 받기 호출 장당 606 → 8번.
    - 7분 넘게 이어진 흔들림 교환 · 배틀에서 통신 오류 0. 혼자 할 때는 순정 · v2와 장마다 화면 지문 · 세이브 · 플레이 시간이 같아요(3300장).
  - 기기 두 대 대표 한 판(교환방 가만히 60초 초당 59.1장, 33ms 넘는 틈 0 → 교환 끝까지, 양쪽 세이브에 반영)을 확인했어요.
- 한계: 흔들림 시험은 가상 머신, 포켓몬 롬은 한국어판(파이어레드 · 리프그린 · 루비 · 사파이어)으로 했어요.

## 코어 옵션

이 패치들은 옵션을 더하지 않아요. 여기서 중요한 gpSP 옵션이에요.

| 옵션 | 값 | 뜻 |
|---|---|---|
| `gpsp_serial` | `rfu` | GBA 무선 어댑터 흉내(게임별로 켜요, 아래 참고). 우리 고침은 이 모드에 들어 있어요. |
| `gpsp_serial` | `mul_poke` · `mul_aw1` · `mul_aw2` | 원본의 통신 케이블 모드(포켓몬 3세대 · 어드밴스 워즈 1 · 2). 우리가 고친 것은 아니에요. |
| `gpsp_serial` | `auto`(기본값) | 원본이 게임을 보고 모드를 골라요. 우리는 무선 게임에 `rfu`를 게임별로 적어 둬요. |
| `gpsp_bios` | `official` | 공식 GBA 바이오스 사용. 시험은 이 값으로 했어요. |

## KNULLI 에 넣기

RG35XX Pro에 우리가 한 방식이에요. 환경이 다르면 자리와 이름을 맞춰 고치세요.

1. **코어 파일.** `gpsp_libretro.so`를 SD 카드의 `/userdata/system/hanbang_cores/`(미리 빌드한 파일이 쓰는 기본 자리)에 넣어요.
   읽기 전용 루트의 `/usr/lib/libretro/gpsp_libretro.so`는 이 파일을 가리키는 바로가기로 두었어요(`mount -o remount,rw /` 뒤에 `ln -sfn`, `knulli-save-overlay`로 저장).
   바꿀 때는 게임이 돌고 있지 않을 때 옛 파일 옆에 새 파일을 올려 md5를 확인한 뒤 `mv`로 바꿔요.
2. **게임별 설정 줄**(`/userdata/system/knulli.conf`): 무선 교환을 하는 게임만 gpSP로 돌려요. 나머지 GBA 게임은 평소 코어 그대로예요.
   ```
   gba["<롬 파일 이름>.zip"].core=gpsp
   gba["<롬 파일 이름>.zip"].retroarchcore.gpsp_serial=rfu
   ```
   KNULLI는 게임별 코어 옵션을 `retroarchcore.<옵션 이름>` 키로 받아요(기기의 실행 기록에 `retroarchcore.gpsp_serial = rfu`로 보여요).
   코어 옵션은 `gpsp_serial = "rfu"`(무선 어댑터 흉내)이고, 시험은 공식 바이오스(`gpsp_bios = "official"`)로 했어요.
3. **두 기기를 함께** 이 판으로 바꿔요. 무선은 섞여도 붙지만 효과는 양쪽이 v3일 때 커요. 케이블 모드(`mul_*`)는 옛 판에 없으니 두 기기 모두 이 판이어야 해요.
4. **같이 쓰는 스크립트**(이 저장소의 [`knulli-scripts/`](../../knulli-scripts/) 폴더). 훅만 빼고 `/userdata/system/claude/`(미리 빌드한 파일이 쓰는 기본 자리)에 복사해요.
   - [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh)는 ES 게임 시작 · 종료 훅이고 `/userdata/system/scripts/nds_save_sync.sh`(미리 빌드한 파일이 쓰는 기본 자리)에 둬요. 아래 스크립트를 게임마다 띄워요.
   - [`netplay_sram_flush.py`](../../knulli-scripts/netplay_sram_flush.py)는 RetroArch가 넷플레이를 시작하면 SRAM 자동 저장을 끄므로, 10초마다 세이브를 카드에 써 줘요. gpSP는 방장 · 손님 모두 '각자 자기 세이브' 코어예요.
   - [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py)는 같은 게임 방(또는 파이어레드 · 리프그린 · 에메랄드 같은 짝 묶음)이 열려 있으면 '같이 / 혼자'를 고르는 창이에요.
5. 교환은 게임 안 다이렉트 코너 · 트레이드센터 · 유니온룸 등 원작 흐름대로 하면 돼요(리더와 그룹은 게임이 정해요).

### 다른 기기 · OS에서 쓸 때 주의

- 이 .so는 **aarch64 리눅스 전용**이에요(glibc 심볼 판은 GLIBC_2.17까지만 써요). 다른 곳에서는 소스 패치로 다시 빌드하세요. 맥 arm64 인터프리터 빌드는 시험 도구용으로 해 봤어요.
- 0001의 캐시 맞춤은 `ARM64_ARCH` + Linux일 때만 켜지고, 다른 플랫폼에는 영향이 없어요.
- RetroArch의 **넷패킷 인터페이스**를 지원하는 프런트엔드가 필요해요. 시험은 RetroArch 1.22.2에서 했어요.
- 세이브 형식은 바뀌지 않았어요. 넷플레이 중 상태 저장 · 불러오기는 통신을 끊을 수 있어요.
- 우리 고침은 **무선 어댑터 통신**에 있어요. 케이블 모드는 원본 것이고 포켓몬 3세대 · 어드밴스 워즈만 돼요. 다른 GBA 통신 케이블 게임은 [`gba-mgba-dual`](../gba-mgba-dual/README.ko.md) 코어를 쓰세요.
- 남은 한계(고치지 않은 것):
  - 교환 끝의 저장 동기(두 게임이 저장 칸마다 서로 기다림)로 4 ~ 6초 느려지는 구간은 게임 구조예요.
  - 흔들린 뒤 리더 쪽 줄(평균 약 11장, 0.18초)은 그대로예요. 줄이려면 게임 패킷을 버리거나 합쳐야 해서(처음 통신 오류의 원인과 같은 쪽) 건드리지 않았어요.
  - 1.2초를 넘는 정지가 이어지면 통신 오류가 날 수 있어요.

## 소스에서 빌드

기기에 넣은 파일을 지은 방식 그대로예요. 맥(arm64)에서 zig 0.17.1로 aarch64 리눅스(glibc 2.17)용을 지었어요. make 값은 원본 libretro 빌드와 같은 `platform=unix CPU_ARCH=arm64 HAVE_DYNAREC=1 MMAP_JIT_CACHE=1`이에요.

```sh
# 패치(이 저장소)
git clone https://github.com/Squirbie/handheld-link-cores.git
CORE="$PWD/handheld-link-cores/cores/gba-gpsp-rfu"

# 기준 커밋의 원본
git clone https://github.com/libretro/gpsp.git
cd gpsp
git checkout 5819380c2ffb0900219d700a382ee68c464ebb99

# (가) 개별 패치를 차례대로
for p in $(grep -v '^#' "$CORE/patches/series"); do git apply "$CORE/patches/$p"; done
# (나) 또는 한 덩어리(둘 다 하지 마세요)
# git apply "$CORE/patches/all-in-one/gpsp-rfu-v3-vs-5819380.patch"

# zig 를 C 컴파일러로 감싸기(경로에 빈칸이 없어야 해요)
printf '#!/bin/sh\nexec zig cc -target aarch64-linux-gnu.2.17 "$@"\n' > /tmp/zcc
printf '#!/bin/sh\nexec zig c++ -target aarch64-linux-gnu.2.17 "$@"\n' > /tmp/zcxx
chmod +x /tmp/zcc /tmp/zcxx

make -j8 platform=unix CPU_ARCH=arm64 HAVE_DYNAREC=1 MMAP_JIT_CACHE=1 CC=/tmp/zcc CXX=/tmp/zcxx \
  SHARED="-shared -s -Wl,--version-script=link.T" GIT_VERSION='"5819380-hb4"'
# 결과: ./gpsp_libretro.so  (다이나렉 포함, strip 됨)
```

- aarch64 리눅스에서 gcc로 지어도 돼요(`CC` · `CXX`를 빼면 돼요). 다만 바이트는 달라지고, 이 바탕에서 gcc 빌드는 해 보지 않았어요.
- 패치는 `patch -p1`로도 얹혀요.
- 폰(안드로이드 arm64)용 인터프리터 빌드는 옛 바탕(`4caf7a1`)으로만 만들었어요. 그 바이너리는 이 폴더에 없어요.

### 다시 만들 수 있는지

- 원본 `5819380`의 트리 해시는 `aa956b7c1f9bc3c0621b25de435f4b8916fc0976`이에요.
- git apply 차례 · git apply 한 덩어리 · patch -p1 차례, 세 방식 모두 같은 트리 `3042ea836b45fff3fecf3fb12508a568f217536f`가 나와요. 이때 `rfu.c`의 md5는 `14aba5dc04763e969628a554646e75f1`이에요.
- GitHub에서 새로 받은 원본에 이 폴더의 패치를 얹어 위 명령으로 다시 지으니 **기기에 넣은 .so와 바이트까지 같았어요**(sha256 `e21bf6d4…`). 두 번, 서로 다른 작업 폴더에서 확인했어요.
- .so 안의 판 글자는 `v1.1.0-5819380-hb4`이고, `ic ivau` 뒤에 `dsb ish`가 있어요.
- 옛 바탕(`4caf7a1`)용 패치 · 설명은 릴리스 `2026.11.18` 꼬리표의 저장소에 그대로 있어요.

## 패치

이 순서대로 얹어요. `patches/series`에 같은 순서가 적혀 있어요. 한 덩어리로 쓰려면 `patches/all-in-one/gpsp-rfu-v3-vs-5819380.patch` 하나만 쓰세요(개별 패치와 같이 쓰면 두 번 얹혀요).

기준: libretro/gpsp 커밋 `5819380c2ffb0900219d700a382ee68c464ebb99`(2026-09-19, "Keep the PSG status bits readable in SOUNDCNT_X"), 트리 해시 `aa956b7c1f9bc3c0621b25de435f4b8916fc0976`. 원본에는 RFU 흉내(`rfu.c`)와 넷패킷 방식이 이미 있고, 이 패치는 그 위의 견고성 고침이에요.

| 순서 | 파일 | 하는 일 | 옛 바탕에서 만든 판 |
|---|---|---|---|
| 1 | [`0001-arm64-linux-cache-sync.patch`](patches/0001-arm64-linux-cache-sync.patch) | arm64 리눅스 캐시 맞춤 | |
| 2 | [`0002-rfu-wifi-netplay-robustness-v2.patch`](patches/0002-rfu-wifi-netplay-robustness-v2.patch) | 와이파이 지연 · 몰아 오기에 견디기 | v2, md5 `f9379e50ff0538e9a5af9afa5422da58` |
| 3 | [`0003-rfu-less-waiting-v3.patch`](patches/0003-rfu-less-waiting-v3.patch) | 기다림 · 받기 호출 줄이기 | v3, md5 `8bdd8b56e895a9625cddc932c3e2f926` |

- 이 바탕에서는 세 개를 다 얹은 최종판(md5 `6c86b647977fafeea3a5cccfeb51d5a1`)만 만들었어요.
- 각 패치 머리말(`Subject` · `Origin` · 짧은 요약 · 설명)에 무엇을 왜 바꿨는지, 새 바탕으로 옮길 때 무엇을 했는지 있어요.
- v1은 `rfu.c`의 시간 제한 두 줄(6줄 추가 · 2줄 삭제)이 전부였고 v2가 그것을 대신해서 따로 넣지 않았어요(v1 .so: `3cbbd19b`).

## 원본에 보내기

2026-11-23에 확인한 libretro/gpsp `master`(= 이 판의 바탕 `5819380`)의 모습이에요.

- `rfu.c`는 지금도 받은 패킷 줄이 `pkts[4]`이고, 시간 제한은 `rfu_timeout * (16777216 / 60)` · `rfu_rtx_max * (16777216 / 60 / 6)` 그대로예요. `RFU_NET_TIMEOUT` · `RFU_QUEUE_LEN` 같은 상수는 없어요.
- `NET_RFU_DISCONNECT`는 슬롯을 바로 지우고, 손님 패킷(`NET_RFU_CLIENT_SEND`)은 길이를 16바이트 칸 크기와 견주지 않아요.

**원본에 보낼 만한가요? 일부는 네.** 분명한 버그가 있어요.

- 손님 패킷을 길이 검사 없이 16바이트 칸에 복사해요(범위 밖 쓰기).
- 4칸 줄이 몰려 온 패킷을 버려요.
- 끊김이 읽지 않은 패킷을 지워요.
- 현재 상대가 아닌 기기의 패킷을 받아들여요.
- 짧은 시간 제한이 와이파이 지연을 무선 신호 손실로 잘못 봐요.

v2 · v3의 상수는 시험한 와이파이 환경에 맞춘 값이고 ACK 넷째 칸 확장은 규약을 건드려서, 보낼 때는 견고성 고침만 따로 떼어 내야 해요.

- 길이 · 보낸 기기 확인만 떼어서 [libretro/gpsp#294](https://github.com/libretro/gpsp/pull/294)로 보냈어요(2026-11-23 기준 열려 있음).
- 나머지(돌림 줄 · 1.2초 시간 제한 · 끊김 전에 남은 패킷 읽기)의 영어 제목 · 본문 초안은 [`UPSTREAM.md`](../../UPSTREAM.md)와 [`cores/MANIFEST.gb.jsonl`](../MANIFEST.gb.jsonl)의 `upstream_pr_candidate`에 있어요.

## 라이선스

- 원본 gpSP(libretro 판)와 같은 **GPL-2.0-or-later**예요. 원본 파일 머리말에는 2판 또는 (원하면) 그 이후 어느 판이든 쓸 수 있다고 적혀 있고, 저장소의 `COPYING`은 GPL 2판 본문이에요(사본: [`LICENSES/gpsp_COPYING`](../../LICENSES/gpsp_COPYING)). 이 패치도 같은 조건으로 공개해요.
- 코어(.so)를 나눠 줄 때는 원본 커밋과 이 패치가 대응하는 소스가 돼요. 원본 파일 머리말의 저작권 표시는 그대로 둬야 해요.
