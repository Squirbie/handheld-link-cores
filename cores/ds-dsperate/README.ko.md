<p align="center"><a href="README.md"><img src="../../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# DSperate — 와이파이로 두 기기를 잇는 DS 무선 통신

> 단독 실행형 DS 에뮬레이터 DSperate 를 고쳐서, 와이파이로 두 기기를 이을 때 덜 끊기고 더 빠르게 돌고, 같은 게임끼리만 붙고, DraStic 같은 팝업 화면을 쓰고, 펌웨어 덤프가 없어도 부팅 직후 흰 화면이 나오지 않게 한 판이에요.

[![Download](https://img.shields.io/badge/download-linux%20aarch64-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/ds-dsperate-linux-aarch64.zip) &nbsp; [← 전체 코어](../../README.ko.md)

| | |
|---|---|
| 코어 파일 | `dsperate` (단독 실행형 에뮬레이터, 레트로아크 코어 아님; 리눅스 aarch64, 4,923,120 바이트). 받는 파일에는 [`glue/`](glue/) 실행 스크립트도 들어 있어요. |
| 판 | `v3.0.3-hbipc` — `--version` 은 `DSperate v3.0.3-hbipc (f5fa35e-dirty)` 로 나와요 |
| md5 | `d1d7a7321f4ca6c1b977f2f1aacc2c4f` |
| 원본 | [beebono/DSperate](https://github.com/beebono/DSperate) v3.0.3 (`f5fa35e`) |
| 라이선스 | GPL-3.0 (원본과 같아요) |
| 시험한 기기 | Anbernic RG35XX Pro (H700) 두 대 · KNULLI |

## 무엇을 하나

DSperate 는 레트로아크 코어가 아니라 **따로 도는(standalone) DS 에뮬레이터**예요. 같이하기 통신 형식이 melonDS 와 같아서 melonDS 와도 붙어요. 이 판은 기기 두 대를 와이파이(또는 기기끼리 직접 연결)로 이어 DS 무선 통신 게임을 같이 하려는 거예요.

- **같이하기가 덜 끊겨요.** 방장이 상대 답을 기다리는 시간이 원래 25ms 라서, 느린 와이파이에서는 게임이 연결을 끊었어요. 이제 기다림을 명령 한 번에 통틀어 더 길게 잡고(기본 150ms, 우리 설정은 400ms), 묵은 패킷을 버리는 창도 늘렸어요. 통신 라이브러리(ENet)가 "믿을 수 없는" 패킷을 무작위로 버리던 것도 막았어요.
- **혼자일 때는 혼자 하기와 똑같아요.** 전에는 "자동"으로 켜면 아무도 없는데도 방장이 되는 순간부터 상태 저장 · 빨리 감기 · 메뉴 멈춤이 막혔어요. 이제 손님이 붙어 있는 동안만 막히고(`PLAYER JOINED` / `PLAYER LEFT` 알림), 손님이 나가면 다시 풀려요.
- **같은 게임끼리만 붙어요.** 방 이름에 `[그룹]` 꼬리표를 달아서, 포켓몬 블랙을 하는 방에 마리오 카트를 켠 기기가 잘못 붙지 않아요. 그룹은 `--lan-group`, 설정(`net.group`), 롬의 게임 코드 4글자, 파일 이름 순으로 정해요. `groups.txt` 로 포켓몬 4세대 · 5세대처럼 묶을 수도 있어요.
- **방장 둘이 만나면** 주소가 큰 쪽이 손님으로 붙어요. **방장이 나가면** 손님이 혼자 방장으로 돌아가서 다시 만날 수 있어요.
- **같이하기가 더 빨라요.** 조각 사이에 쉬는 동안 네트워크 소켓을 지켜보고 있다가 상대 신호가 오면 바로 깨요. 방장이 "이 시각 전엔 보낼 게 없다"를 알려 주면 손님이 미리 돌아요(지평선, `DSPERATE_MP_HORIZON=1`). 무선 칩의 8µs 타이머는 할 일이 없는 동안 몰아서 세요(상대가 붙어 있을 때만). 마리오 카트 DS 두 대는 약 58~59프레임, 포켓몬 블랙 2 대전은 57~58프레임으로 돌아요(와이파이가 좋을 때).
- **세이브가 안 깨져요.** 세이브 · 상태 저장 · 펌웨어 설정 파일을 쓸 때 `fsync` 한 뒤 이름 바꾸기(rename)를 해서, 배터리가 떨어지거나 전원 버튼으로 꺼도 빈 파일이 남지 않아요(exFAT 카드 기준).
- **DraStic 같은 팝업 · 작은 화면.** L2 를 누르는 동안 다른 화면이 반투명 창(75%, 둥근 모서리)으로 올라오고, 두 번 누르면 고정돼요. 작은 화면은 80% 비침에 초록 테두리이고, 오른쪽 스틱을 밀면 누르는 창이 저절로 떠요. 반투명 창이 뜬 프레임을 NEON 으로 섞어서, 두 대 경주 중 창을 고정해도 58.5프레임을 지켜요(전에는 52.5프레임).
- **`screen = auto`.** DS 디스플레이 엔진 A(3D 를 그리는 주 화면용 엔진)가 보여 주는 화면을 따라 큰 화면이 자동으로 바뀌어요(장면마다 보는 화면이 다른 게임용).
- **세 명 같이하기.** 손님끼리도 서로 보이고(손님도 7064 포트로 들어요), 다른 방 프레임이 손님의 시계를 붙잡지 않아요.
- **다운로드 플레이(받기).** 받는 쪽은 절대 방장이 되지 않고 기다렸다 붙어요. 받기가 끝나고 게임이 새로 켜질 때 손님 연결이 끊기던 것도 고쳤어요. 손님이 화면 줄 번호(VCOUNT)를 방장에 맞추는 쓰기를 받게 했어요. 슈퍼 마리오 64 DS 대전에서 게임 시간이 실제의 1/3 이하로 흐르던 것이 95% 로 정상이 됐어요(기기 두 대 시험, 2026-10-20).
- **펌웨어 파일 없이도 흰 화면이 안 나요.** 한국판 피크로스 DS 가 DS 펌웨어 덤프 없이 켜질 때 부팅 직후 하얀 화면에서 멈추던 것을 고쳤어요(슈퍼 마리오 64 DS 한국판의 흰 화면도 같은 박자 문제였어요). ARM9 가 ARM7 에 보낸 IPC FIFO 말을 ARM7 이 한 조각 일찍 보던 것이 원인이고, 순정 v3.0.3 에도 있어요.

## 무엇을 고쳤나

패치는 **쌓은 층의 합**이에요. 코드 주석에 층 이름표(`lanfix`, `hbfam` 등)가 붙어 있어서 패치 안에서 그 낱말로 찾을 수 있어요. `hb` 로 시작하는 이름과 `hanbang` 은 '우리가 고친 곳' 표시일 뿐이에요. 패치 · 파일 · 스크립트가 서로 맞도록 이름은 그대로 뒀어요. 쌓은 순서대로 적어요.

1. **`lanfix` — 통신 기다림** (`net/lan_mp`). 방장이 답을 기다리는 시간을 패킷당 25ms 에서 명령(CMD) 한 번에 통틀어 150ms 로 늘렸어요. 손님 기다림도 맞추고, 묵은 프레임 창을 64ms 에서 `max(250, TIMEOUT+100)` 으로 늘렸어요. 기다리는 중에 온 일반 프레임은 버리지 않고, ENet 패킷 조절(throttle)은 32/32 로 고정하고, 통계 기록을 남겨요.
2. **`hbfam` — 혼자인 방장과 안전한 저장.** 혼자인 방장은 세션이 아니에요(`lan_session_live`). `core/sync_file.h` 는 파일을 fwrite → fflush → fsync → rename → 폴더 fsync 순서로 써요. `screen_swap_hold` 는 키를 누르는 동안 다른 화면을 보여 줘요.
3. **`hbfam2` — LAN 그룹.** 방 이름이 `"<이름>'s game [<그룹>]"` 이 되고, 같은 꼬리표 방에만 자동으로 붙어요.
4. **`hbfam3` — 방장 되찾기.** 외로운 방장 둘이 만나면 주소가 큰 쪽이 붙고, 방장이 나가면 손님이 혼자 방장이 돼요. `--netplay`(자동)일 때만 해당돼요.
5. **`hbpop` — L2 팝업.** 팝업 창(`layout`: `inset_pos`, `display`: 둥근 모서리 · 미끄러짐)이에요. 350ms 안에 두 번 누르면 고정해요.
6. **`hbpip` · `hbpip2` — 작은 화면.** 80% 비침에 1px 초록 테두리(`video.pip_border`)예요. 반투명 작은 화면을 섞기 전에 일꾼 스레드를 기다리고, 팝업이 떠 있는 동안에도 작은 화면을 남겨요(유령).
7. **`hbmp` — 소켓을 보는 쉬기.** `idle_wait` 가 조각 사이에 쉬는 동안 ENet 소켓을 지켜보고, 상대가 기다리면 쉬지 않고, 쉬는 간격을 CPU 시간으로 맞추고, 지평선을 더해요.
8. **`hbaud` — 소리.** 같이하기 중에도 화면에 맞춘 limiter(58~61Hz)를 유지해서 소리 대기열이 비지 않아요.
9. **`hbwifi` · `hbtime` — 무선 타이머.** 무선 칩의 8µs 타이머를 할 일이 없는 구간 동안 몰아서 세요(`plan_idle_steps`). 통계 줄에는 µs 단위 계측이 들어가요.
10. **`hbmesh` · `hbbss` — 세 명.** 손님도 UDP 7064 로 듣고, 손님이 다른 방(BSS) 프레임 때문에 시계를 붙잡히지 않아요.
11. **`hbauto` — `video.screen = auto`.**
12. **`hbstick` — 스틱으로 뜨는 창.** 오른쪽 스틱을 20% 넘게 밀면 누르는 창(D)이 뜨고, 스틱을 쓰는 동안 L2 창은 흐려져요(C).
13. **`hbfix18` · `hbfix19` — 그리는 속도.** 창이 떠 있으면 늘 85%, 작은 화면은 쌍선형이에요. 반투명 창은 캐시 버퍼에 그려 한 번 복사하고, 섞기 · 유령은 NEON 으로 하고, 줄 내보내기 방식은 시간을 재서 골라요.
14. **`hbvc` — VCOUNT.** `io.cpp` 의 `write16` 에서 VCOUNT(0x04000006) 쓰기를, 지금 줄과 새 값이 모두 200~214(VBlank)일 때만 다음 줄 시작에서 적용해요.
15. **`hblink` — 붙어 있을 때만 몰아 세기.** 무선 타이머 몰아 돌기는 같이하기 상대가 붙어 있을 때(`LanMp::linked()`)만 해요.
16. **`hbguest` · `hbguest2` — 받기(다운로드 플레이).** 받기(펌웨어 부팅)는 `--netplay` 여도 방장이 되지 않고 기다렸다 붙어요. "무선 끔"을 알린 상대에게는 MP 프레임을 보내지 않고, ENet 에 쌓인 MP 프레임은 한 번에 꺼내요.
17. **`hbipc` — IPC FIFO 박자.** ARM9 가 `IPCFIFOSEND` 에 쓴 말을 `ipc9_pending` 에 잡아 두고, ARM9 조각을 거기서 끝내요(`yield`). ARM7 이 따라온 시각에 `Scheduler::fire_due()` 가 FIFO 에 넣고 IRQ 를 걸어요(`ipc_deliver`).

그 밖에: 시험 파일 2개 추가(`tests/lan_group_test.cpp`, `tests/lan_live_test.cpp`), `tests/input_test.cpp` 늘림(`ctest` 32개 통과), `configs/default.ini` 설명 줄.

## 코어 옵션

DSperate 는 따로 도는 에뮬레이터라서, 여기서 '코어 옵션'은 설정 파일 · 팝업 설정 파일 · 몇 가지 스위치를 뜻해요.

### `dsperate.ini`

중요한 줄만 적었어요(2026-10 기준 우리 설정).

```ini
[paths]
bios9 = /userdata/bios/bios9.bin
bios7 = /userdata/bios/bios7.bin
firmware = /userdata/bios/firmware.bin
firmware_override = /userdata/system/configs/dsperate/firmware.ovr   # 게임이 펌웨어에 쓰는 것은 여기에만
saves = /userdata/saves/nds/dsperate
states = /userdata/saves/nds/dsperate/states
cache = /userdata/system/configs/dsperate/cache
[video]
layout = pip
screen = bottom           # 게임별 ini 에서 top / bottom / auto
pip_corner = tl
pip_scale = 0.25          # 큰 화면 폭의 1/4 (160x120, DraStic 과 같게)
pip_alpha = 0.8
pip_border = 00cc00
layout_cycle = pip,single
[emu]
autosave = false
limiter = 59              # 기기 화면이 초당 59번 그려져서 맞췄어요
[net]
mode = off                # 같이하기는 실행 스크립트가 --netplay 로 켜요 (켤 때마다 off 로 되돌려 둠)
[cart]
cache = session
[padhotkeys]
modifier = guide
screen_swap = +righttrigger          # R2
screen_swap_hold = +lefttrigger      # L2 (hb_popup.cfg 에 mode=popup 이 없을 때)
```

`mac_suffix` 는 직접 적을 필요가 없어요. `hb_dsperate.py` 가 켤 때마다 그 기기 무선랜(`wlan0`) 주소의 끝 3바이트를 적어 줘서, 기기마다 다른 DS 무선 주소가 돼요.

### `hb_popup.cfg` (L2 팝업)

`/userdata/system/configs/advanced_drastic/hb_popup.cfg` 는 DraStic 팝업이 읽는 것과 같은 파일이에요. 다른 파일을 쓰려면 `HB_POPUP_CFG=<경로>` 를 주세요. 파일이나 줄이 없으면 기본값을 써요.

| 키 | 기본값 | 뜻 |
|---|---|---|
| `mode` | (꺼짐) | `mode=popup` 줄이 있어야 L2 가 팝업을 열어요. 없으면 L2 는 화면 바꾸기예요 |
| `size` | `75` | 팝업 창 크기(%) |
| `alpha` | `85` | 창 불투명도(%) |
| `pos` | `bottom` | 창 위치(`top`, `center`, `bottom`) |
| `radius` | `14` | 창 모서리 둥글기 |
| `auto` | `1` | 오른쪽 스틱을 밀면 누르는 창이 저절로 떠요 (`0` = 끔) |
| `fade` | `40` | 스틱을 쓰는 동안 L2 창의 불투명도(%) |

### 스위치 (환경 변수와 파일)

| 이름 | 층 | 하는 일 |
|---|---|---|
| `DSPERATE_MP_TIMEOUT_MS` (5~2000) | `lanfix` | 방장: 명령 한 번에 대한 손님 답을 통틀어 기다리는 시간(ms). 기본 150 (순정 25). |
| `DSPERATE_MP_CLIENT_WAIT_MS` | `lanfix` | 손님: 방장의 다음 프레임을 한 번 막고 기다리는 시간(ms). 기본은 답 기다림과 같아요 (순정 25). |
| `DSPERATE_MP_STALE_MS` | `lanfix` | 쌓인 프레임이 이보다 묵으면 버려요. 기본 `max(250, TIMEOUT + 100)` (순정 64). |
| `DSPERATE_MP_ENET_THROTTLE=1` | `lanfix` | ENet 패킷 조절을 원래대로 되돌려요. |
| `/tmp/dsperate_mp_stats` (파일) | `lanfix` | 이 파일이 있는 동안 1초마다 `/tmp/dsperate_mp_stats.log` 에 통계를 한 줄씩 남겨요. |
| `DSPERATE_MP_HBMP=0` | `hbmp` | 소켓을 보는 쉬기를 꺼요. |
| `DSPERATE_MP_HORIZON=1` | `hbmp` | 지평선을 켜요. 두 기기 모두에 줘야 켜져요. |
| `DS_WIFI_SKIP=0` | `hbwifi` | 무선 타이머 몰아 세기를 꺼요. |
| `DS_VCOUNT_WRITE=0` | `hbvc` | VCOUNT 쓰기 처리를 꺼요. |
| `DS_IPC_DEFER=0` | `hbipc` | IPC FIFO 말이 순정처럼 바로 보이게 해요. |
| `HB_PIP_NEAREST=1`, `HB_POPUP_DIRECT=1`, `HB_COPY_PLAIN=1`, `HB_GHOST_SCALAR=1`, `HB_BLEND_SCALAR=1`, `HB_COPY_WAY=memcpy\|neon` | `hbfix18`, `hbfix19` | 그리기 빠르게 하는 방법을 하나씩 끄거나, 줄 복사 방식을 정해요. |

## KNULLI 에 넣기

우리가 쓰는 방식이에요. [Releases](https://github.com/Squirbie/handheld-link-cores/releases) 에서 `ds-dsperate-linux-aarch64.zip` 을 받으면 `dsperate` 실행 파일과 `glue/` 파일이 들어 있어요. 롬 · BIOS · 펌웨어 · 세이브는 이 저장소에 없어요. 이 판은 **펌웨어 덤프가 없어도** 켜져요(DSperate 가 만든 펌웨어를 쓰고, 설정 값은 `firmware.ovr` 에만 써요).

```
/userdata/system/configs/dsperate/
  dsperate                  <- 실행 파일 (권한 755)
  dsperate.ini              <- 설정 (코어 옵션 참고)
  hb_dsperate_run.sh        <- glue/: ES -> launch.sh -> 이 스크립트가 DSperate 를 켜요
  hb_dsperate.py            <- glue/: 켜기 전 · 끈 뒤: DS 무선 주소 맞추기 + DraStic <-> DSperate 세이브 이어 주기
  games.txt  groups.txt  mpenv.txt  gamecontrollerdb_rg35xx.txt   <- glue/
  games/<롬 이름>.ini       <- 게임별 설정 (단축키로 고른 화면 배치를 DSperate 가 여기 기억해요)
/userdata/saves/nds/dsperate/   세이브(.sav) · states/ · backup/
/userdata/bios/{bios7.bin, bios9.bin, firmware.bin}   직접 준비하세요 (이 저장소에 없어요)
```

1. **DraStic 실행 스크립트에 갈림길 만들기.** ES 에는 계속 "DraStic 게임"으로 보이게 해요(그래야 세이브 맞추기 · 게임 안 팝업 훅이 그대로 돌아요). 그리고 `advanced_drastic/launch.sh` 맨 앞에서 `games.txt` 에 있는 게임만 넘겨요.
   ```sh
   HB_DSP=/userdata/system/configs/dsperate
   hb_base=`basename "$1"`; hb_base="${hb_base%.*}"
   [ ! -e $HB_DSP/off ] && [ -f $HB_DSP/dsperate ] && grep -qxF "$hb_base" $HB_DSP/games.txt 2>/dev/null && exec /bin/bash $HB_DSP/hb_dsperate_run.sh "$1"
   ```
   `games.txt` 에는 롬 이름(확장자 뺀 것)이 한 줄씩 있어요(89줄: 게임 88개 + 받기 메뉴 `BootMenu`). `BootMenu` 는 빈 파일(`roms/nds/BootMenu.nds`)이고, DSperate 가 본체 메뉴(펌웨어)로 켜서 다운로드 플레이 "받기" 쪽으로 써요. 폴더에 `off` 파일 하나를 만들면 모든 DS 게임이 DraStic 으로 가고, `net_off` 파일이면 같이하기 없이 혼자만 켜져요.
2. **설정.** [코어 옵션](#코어-옵션)에 적은 대로 `dsperate.ini` 를 고치고, L2 팝업을 쓰려면 `hb_popup.cfg` 도 만들어요.
3. **켤 때 쓰는 값.** `hb_dsperate_run.sh` 가 `DSPERATE_MP_HORIZON=1`, `DSPERATE_MP_TIMEOUT_MS=400` 을 정하고 `--netplay`, `--lan-group <그룹>`, `--clear-cache` 를 넘겨요. 게임마다 다르게 하려면 `mpenv.txt` 에 `롬이름<탭>DSPERATE_MP_*=숫자 …` 줄을 넣어요(받는 이름은 `DSPERATE_MP_*` 와 `DS_WIFI_SKIP` 뿐이에요). 지금 들어 있는 건 소닉 러시 두 게임이 원래 값(지평선 · hbmp 끔, 기다림 25ms)으로 도는 줄이에요.
4. **도우미 스크립트 (선택).** 실행 스크립트는 아래 파일이 있으면 쓰고, 없으면 그냥 건너뛰어요. [`knulli-scripts/`](../../knulli-scripts/) 에 있고, `/userdata/system/claude/`(미리 빌드한 파일이 쓰는 기본 자리)에 복사하면 돼요. 실행 스크립트가 `hb_direct.py` 와 `hb_joinask.py` 를 거기서 찾아요.
   - [`hb_direct.py`](../../knulli-scripts/hb_direct.py) — 같이하기 중 기기끼리 직접 연결해요(`watch-dsperate` 로 DSperate 기록을 보며 방장 / 손님 역할을 정해요).
   - [`hb_joinask.py`](../../knulli-scripts/hb_joinask.py) — 같은 그룹 방이 열려 있으면 켜기 전에 '같이 / 혼자' 고르는 창을 띄워요(`--ds`).
   - [`nds_save_sync.sh`](../../knulli-scripts/nds_save_sync.sh) · [`nds_save_sync.py`](../../knulli-scripts/nds_save_sync.py) — ES 시작 · 끝 훅과 DS 세이브 이어 주기예요. 훅은 `/userdata/system/scripts/nds_save_sync.sh`(미리 빌드한 파일이 쓰는 기본 자리)에 두는데, 그 폴더의 파일은 모두 실행되니 이 파일 하나만 두세요.
   - DSperate 는 게임마다 큰 화면을 스스로 기억해서 [`hb_ds_remember.py`](../../knulli-scripts/hb_ds_remember.py)(DraStic 용)는 쓰지 않아요.
5. **확인.** `grep -a -c -E 'hbguest: firmware boot|hblink: another|hbvc: VCOUNT|dr=hbguest2|hbipc: ARM9 IPC' dsperate` 가 **5** 를 내야 해요. 게임을 켠 뒤 `/tmp/hb_dsperate.log`(램)에 `hbipc: ARM9 IPC FIFO words reach the ARM7 at their send time` 한 줄이 보이면 이 판이에요.
6. **되돌리기.** 바꾸기 전 실행 파일을 같은 폴더에 `dsperate.<이전판>_<지문>` 으로 복사해 두었다가 다시 `dsperate` 로 덮어요. 게임이나 DSperate 가 도는 중에는 바꾸지 마세요. 층을 끄는 환경 변수(`DS_IPC_DEFER=0` 등)는 `dsperate` 를 손으로 켤 때만 줄 수 있어요. 실행 스크립트는 `mpenv.txt` 의 `DSPERATE_MP_*` 와 `DS_WIFI_SKIP` 만 받아요.

이 저장소에 없는 것: 시험 기기의 최종 `dsperate.ini`(기기 고유 값이 들어 있어서 위에 중요한 줄만 적었어요), `advanced_drastic/launch.sh` 전체, `hb_dsosd.so`(DraStic 쪽 게임 안 팝업 라이브러리 — `/userdata/system/claude/` 에 있으면 실행 스크립트가 `LD_PRELOAD` 로 불러요).

### 다른 기기 · OS 에서 쓸 때

- **실행 파일**은 aarch64 리눅스용이고 `glibc 2.38` 이상, `libstdc++ 3.4.30` 이상, `libSDL2-2.0.so.0` 이 있어야 해요(KNULLI 는 glibc 2.40 이라 문제없었어요). 더 오래된 OS 는 패치로 다시 빌드하세요. JIT 은 aarch64 리눅스 쪽이에요. JIT 이 안 되는 OS 는 `-DDSPERATE_JIT=OFF` 로 빌드하면 되는데, 해석기로 돌아서 느려요.
- **3D 는 소프트웨어**예요. `--gpu3d` 는 Vulkan 전용인데 H700 의 그래픽 드라이버(libmali)에는 Vulkan 이 없어서 못 써요.
- **같이하기 네트워크.** 방 찾기는 UDP 7063(방송), 게임 데이터는 UDP 7064(ENet)예요. 두 기기가 같은 네트워크에서 서로 이 포트로 닿아야 해요. 일부 공유기는 몇 초마다 모든 와이파이 기기를 0.05~0.1초 멈춰서 같이하기가 느려지고 끊겨요. 우리는 [`hb_direct.py`](../../knulli-scripts/hb_direct.py) 로 같이하는 동안만 기기끼리 직접 이었어요(한쪽의 두 번째 무선 `wlan1` 을 숨은 작은 공유기로 써요). 이 기기의 무선 칩 기준이라 다른 기기에서는 그대로 안 돼요.
- **양쪽이 이 판이어야 해요**(또는 그룹 꼬리표를 아는 판). 옛 판은 `--lan-group` 을 몰라 바로 꺼지고, 꼬리표 없는 방(순정 DSperate · melonDS)에는 자동으로 안 붙어요. 주소로 직접 `--lan-join` 하면 붙어요.
- **DS 무선 주소가 기기마다 달라야** 해요(`mac_suffix`). 카드를 통째로 복사하면 같아지는데, `hb_dsperate.py` 가 켤 때마다 맞춰 줘요.
- 실행 스크립트는 ssh 로 직접 켤 때 `XDG_RUNTIME_DIR=/var/run` 과 컨트롤러 표(`SDL_GAMECONTROLLERCONFIG`)를 스스로 넣어요. `glue/gamecontrollerdb_rg35xx.txt` 는 RG35XX Pro 패드 기준이에요.
- 고친 동작의 상당수(팝업 · 작은 창 · 자동 화면 · 그룹)는 우리 취향이에요. 필요 없으면 설정으로 끄거나, 그 층만 빼고 다시 빌드하세요.

## 소스에서 빌드

원본 CI 와 같은 순서로 빌드했어요. 순정 v3.0.3 으로 해 보면 공식 배포 파일과 **바이트까지 같게** 나와요(2026-10-12 확인). 패치를 건 판도 같은 방법이에요.

```sh
# 소스를 받고 패치를 걸어 두세요 (아래 "패치" 참고)

# 빌드 상자: ubuntu:24.04 + (gcc 13.3 · cmake 3.28 · ninja 1.11 · SDL2 2.30)
apt-get install --no-install-recommends cmake ninja-build g++ gcc pkg-config libsdl2-dev libvulkan-dev git ca-certificates file binutils make

# 소스를 원본 CI 와 같은 경로에 두세요: /home/runner/work/DSperate/DSperate
#   (실행 파일 안에 소스 경로가 들어가서, 다른 경로에서 빌드하면 크기는 같아도
#    23만 바이트쯤 달라져요)
cd /home/runner/work/DSperate/DSperate
cmake --preset host -DDSPERATE_PGO=use -DDSPERATE_PGO_STRICT=ON -DDSPERATE_VERSION=v3.0.3-hbipc
cmake --build --preset host -j 2
ctest --preset host                                   # 32개 통과
strip build/host/src/frontend/sdl/dsperate build/host/src/frontend/headless/dsperate-headless
```

- 컴파일러: Ubuntu 24.04 상자의 GCC 13.3. 결과물에는 glibc 2.38 이상과 `libSDL2-2.0.so.0` 이 필요해요.
- 우리 빌드용 가상 머신은 램이 3GB 라서, 위 `cmake` 두 줄을 `taskset -c 0,1 nice -n 10` 으로 CPU 2개에 묶었어요(`-flto=auto` 가 CPU 수만큼 일을 띄워서요). 코드 결과는 같아요.
- PGO(실행 결과로 최적화) 프로필은 gcc 13.3.0 용 지문이라, 다른 컴파일러에서는 `configure` 가 멈춰요. 그때는 `-DDSPERATE_PGO=off` 로 하세요(조금 느릴 수 있어요). 우리 층이 든 함수는 프로필을 잃지만 기기 속도는 그대로였어요(기록상).
- 헤드리스(`dsperate-headless`)는 기기에 안 썼어요.

## 패치

| 순서 | 파일 | 하는 일 |
|---|---|---|
| 1 | [`patches/dsperate-v3.0.3-hbipc-full.patch`](patches/dsperate-v3.0.3-hbipc-full.patch) | 원본 v3.0.3 에서 곧바로 걸리는 "전체" 패치 한 장이에요. 위에 적은 층이 모두 들어 있어요(28개 파일, +2619 −103줄, 새 파일 3개) |

```sh
git clone --depth 1 --branch v3.0.3 https://github.com/beebono/DSperate.git     # 태그 v3.0.3 = 커밋 f5fa35ea19f966543feae086798701f134d89619
cd DSperate
git apply /path/to/patches/dsperate-v3.0.3-hbipc-full.patch     # 새 파일 3개 포함
```

**최종 패치가 이것인 근거**

- 이 패치는 원본 v3.0.3 위에 모든 층을 쌓은 가상 머신 소스에서 `git diff HEAD` 로 뽑은 4,098줄짜리예요. 바로 앞 판(`hbguest2`, 그 `git diff HEAD` 결과의 md5 앞 8자리 `eca75cbe`) 위에 `hbipc` 를 얹은 결과이고, 이 패치로 빌드한 실행 파일이 `d1d7a732…`(위 md5)이에요.
- 실행 파일 안 글자와 맞아요. `v3.0.3-hbipc` · `f5fa35e-dirty` · `DS_IPC_DEFER` · `hbipc: ARM9 IPC FIFO words …`(hbipc), `hbguest: firmware boot…`(hbguest), `hblink: another console joined…`(hblink), `hbvc: VCOUNT write…`(hbvc), `hbfix18/19` 줄, `hbmesh` · `hbauto` · `hbaud` · `hbstick` 줄이 있고 `hbfix20` 은 없어요(그 갈래는 최종판에 안 들어갔어요). GLIBC 2.38 · GLIBCXX 3.4.30 이 요구돼요.
- 이 판이 시험 기기 두 대에 들어간 날은 2026-10-25 이고, 마리오 카트 DS 같이하기 제목 화면은 58.7/58.5프레임이었어요.
- 단계별(층별) 패치가 따로 여럿 있었지만 모두 이 패치 안에 들어 있으니 이 한 장이면 돼요.

**확인한 것과 못 한 것**

- 확인함: 패치의 시작 파일 지문 25개가 모두 v3.0.3 트리의 같은 파일 지문과 같고, 나머지 3개는 새 파일이에요(2026-10-29, 저장소 정보만 읽어 대조). 패치 형식(`git apply --numstat`: 28개 파일, +2619 −103)이 깨지지 않았고, 실행 파일 안 글자가 패치 층과 맞고, 필요 라이브러리를 확인했어요.
- 못 함: 이번 정리에서 원본 소스를 새로 받아 `git apply --check` 와 빌드를 다시 돌려 보지는 않았어요(빌드는 기록에 남은 그대로예요). 최신 `main` 과의 비교도 안 했어요.

**빌드에 쓴 패치와 다른 점.** 공개한 패치는 빌드에 쓴 패치(md5 `112bee98ee256be64f963249219c4333`)에서 공개용으로 글자 몇 곳을 손본 거예요. 새 시험 파일 `tests/lan_group_test.cpp` 의 `test_names` 함수에서 시험 입력으로 쓰던 **기기 이름표 글자 4자 13곳**을 같은 길이의 `DevA` 로 바꿨어요. 글자 수가 같아서 패치의 줄 수 표시는 그대로이고, 시험이 보는 값(63바이트 자르기 등)도 그대로예요. 패치에 보이는 `127.0.0.1` 은 자기 자신 주소(시험용)예요.

## 원본에 보내기

가장 분명한 것은 **`hbipc`**(IPC FIFO 박자)예요. ARM9 가 IPC FIFO 에 쓴 말을 ARM7 이 최대 한 조각(2048 사이클) 일찍 봐요. 순정 v3.0.3 에서도 그대로 일어나고(우리 포크로 한 48가지 조건 시험에서 고치기 전 흰 화면 8곳, 고친 뒤 0), 한국판 피크로스 DS 가 펌웨어 덤프 없이 켜질 때 흰 화면이던 원인이에요. 전체 패치 안에서 `io.cpp` · `io.h` · `scheduler.cpp` 의 `ipc9_pending` · `ipc_deliver` 부분만 따로 뽑아 `main` 에 맞춰야 해요.

따로 보낼 수 있는 작은 후보도 있어요.

- `hbvc` — VCOUNT 쓰기를 받게 하는 것(다운로드 플레이 대전 게임 시간이 실제의 1/3 이하로 흐르던 것).
- `lanfix` — LAN 답 기다림 25ms, 묵은 패킷 창 64ms, ENet throttle 이 패킷을 무작위로 버리던 것.
- `hbguest2` — 받기가 끝난 뒤 손님의 ENet 연결이 끊기던 것.
- `hbfam` 의 `fsync` 저장.

팝업 · 작은 창 · 그룹 · 자동 화면 · 스틱 창은 우리 취향이라 보내지 않아요. 웹은 원본 주소와 커밋 확인에만 썼고 최신 `main` 과는 비교하지 않았으니, 보내기 전에 이미 고쳐졌는지 확인해야 해요. 제목과 글 초안은 [`UPSTREAM.md`](../../UPSTREAM.md) 와 [`cores/MANIFEST.ds.jsonl`](../MANIFEST.ds.jsonl) 의 `upstream_pr_candidate` 에 있어요.

## 라이선스

DSperate 는 **GNU GPL v3.0** 이에요(원본 라이선스 원문은 [`LICENSES/DSperate_LICENSE`](../../LICENSES/DSperate_LICENSE)). 이 패치도 같은 조건으로 공개해요. `glue/` 와 `knulli-scripts/` 에 있는 우리가 쓴 스크립트는 파일마다 머리말에 라이선스를 적어 뒀어요. 저장소 맨 위 README 도 함께 보세요.
