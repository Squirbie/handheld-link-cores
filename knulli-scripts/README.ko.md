<p align="center"><a href="README.md"><img src="../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# KNULLI 스크립트 — 코어를 둘러싼 붙이는 파일

> 코어만으로도 레트로아크 넷플레이 메뉴로 같이할 수 있어요. 이 스크립트들은 KNULLI 에서 그걸 단추 하나로 만들어요: **같이하기 창**, 손님 세이브 돌려보내기, DS 와이파이 직접 연결, PSP 애드혹 중계, 몇 가지 편의 서비스.

[![Download](https://img.shields.io/badge/download-knulli--scripts.zip-2f81f7?style=for-the-badge&logo=github)](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/knulli-scripts.zip) &nbsp; [← 전체 코어](../README.ko.md)

<p align="center">
  <img src="../docs/images/join-window-ko.png" width="420" alt="같이하기 창">
</p>

## 들어 있는 것

| 파일 | 하는 일 |
|---|---|
| `nds_save_sync.sh` | ES 게임 시작 · 끝 훅 — 아래 도우미들을 부르는 입구예요. `/userdata/system/scripts/` 에는 **이 파일 하나만** 두세요(KNULLI 가 그 폴더의 모든 파일을 실행해요). 지난 게임의 도우미는 띄울 때 적어 둔 번호로 끄고(프로세스 전체 훑기는 도우미마다 부팅 뒤 한 번만), 게임이 끝날 때 카드 기록 확정은 맨 마지막에 해요. 단독 PPSSPP 에서는 애드혹 게임을 켜고 끌 때 `hb_pspadhoc` 에 알려요. |
| `hb_joinask.py` | **같이하기 창**. 게임을 켤 때 같은 와이파이에 같은 게임 방이 열려 있는지 묻고, 있으면 같이할지 물어요(10초 뒤 혼자). DSperate 방 · 짝 게임도 다뤄요. `system.language` 가 `ko` 로 시작하면 한국어, 아니면 영어(`HB_LANG` 으로 바꿀 수 있어요). |
| `hb_keys.py` | 창에서 A · B 단추를 읽어요(읽기만 해요 · KNULLI 에 들어 있는 python-evdev 를 써요). `hb_joinask.py` 가 불러 쓰니 둘을 같이 두세요. |
| `launcher/emulatorlauncher.patch` | KNULLI `configgen/emulatorlauncher.py` 에 거는 작은 패치: 창에서 '같이'를 고르면 손님으로 켜고, ES 넷플레이 로비로 들어온 손님도 게임별 코어를 그대로 써요. |
| `launcher/hb_patch.py` | `patch` 명령 없이 그 패치를 넣고 빼요(`patch` 가 없는 KNULLI 빌드가 있어요). 앞뒤 줄이 글자 그대로 맞을 때만 넣어요. |
| `hb_ownsave.py` | 두 대 코어(GBA · 원더스완 · 네오지오 포켓 · 게임기어)의 각자 자기 세이브: 손님 세이브가 방장 2P 칸에서 놀고 끝나면 손님에게 돌아가요. 짝 게임 표도 여기 있어요. |
| `netplay_sram_flush.py` | 넷플레이 중 게임 속 저장을 바로 파일로 써요. 같이하는 동안 CPU 를 올리는 설정도 있어요. |
| `nds_save_sync.py` | DS 세이브를 DraStic · melonDS DS · DSperate 사이에서 이어 줘요. |
| `hb_direct.py` | DS 같이하기 때 두 기기를 공유기 없이 와이파이로 바로 이어 렉을 줄여요. |
| `hb_dsmac.py` | 카드를 통째로 복사해 같아진 DS 펌웨어 MAC 을 기기마다 다르게 해요. |
| `hb_pspadhoc.py` | PSP 애드혹: 집 안 중계 서버 + 방장 자동 고르기. 2026.11.24.1 릴리즈(v2)부터는 애드혹 게임을 켠 기기만 알리고 서버가 될 수 있어요. 모든 기기가 같은 서버를 고르고, 로그인한 사람이 있는 서버는 자기 게임을 꺼도 서버로 남고, 손님이 있는 동안 그 기기는 잠들지 않아요. 같은 와이파이의 옛 판(v1) 기기와 섞여도 돼요. 설정은 아래 **PSP 애드혹** 을 보세요. |
| `hb_dskeys.py` · `hb_dshold.py` · `hb_ds_remember.py` | DraStic 도우미: 버튼 도우미 · L2 누르는 동안 두 화면 바꾸기 · 게임마다 큰 화면 배치 기억. |
| `hb_idlesave.py` | 게임 중 오래 안 누르면 상태 저장하고 잠자기, 배터리가 바닥나기 직전 저장하고 끄기. |
| `hb_wifimem.py` | 와이파이에 붙어 있는 동안 배경 검색을 꺼서 같이하기 중 주기적으로 끊기는 것을 줄여요(이름과 달리 와이파이 기억 기능은 꺼 두었어요). 절전에서 깬 뒤에는 연결을 건드리지 않고, 1분쯤 지나도 와이파이가 안 붙으면 와이파이를 껐다 켜 줘요. |
| `services/` | `hb_idlesave` · `hb_wifimem` · `hb_dsmac` · `hb_pspadhoc` 를 켜는 KNULLI 서비스 파일. `hb_wifimem` · `hb_dsmac` · `hb_pspadhoc` 는 메뉴가 뜬 뒤(`/tmp/emulationstation.ready`, 늦어도 60초 뒤)에 켜져서 부팅을 늦추지 않아요. |

## 넣는 법

가장 쉬운 길은 `sh install.sh knulli-scripts` 예요([빠르게 시작](../README.ko.md#빠르게-시작-knulli)). 아래 순서를 그대로 해 주고, 빌드의 파이썬이 3.11 이든 3.12 든 실행기를 찾아내며, `patch` 명령이 없어도 돼요.

손으로 넣을 때는 기기에 SSH 로 들어가, 푼 `knulli-scripts` 폴더에서:

```sh
# 1) 스크립트 (기본 자리: DSperate 미리 빌드 파일이 여기서 hb_direct.py · hb_joinask.py 를 불러요)
mkdir -p /userdata/system/claude
cp *.py /userdata/system/claude/
cp -r fonts /userdata/system/claude/            # 창에 쓰는 갈무리 픽셀 글꼴(OFL-1.1) — 없어도 돼요

# 2) ES 훅 — 이 폴더에는 이 파일 하나만
mkdir -p /userdata/system/scripts
cp nds_save_sync.sh /userdata/system/scripts/
chmod +x /userdata/system/scripts/nds_save_sync.sh

# 3) 실행기 패치 — '같이'를 고르면 정말 손님으로 켜지게
mount -o remount,rw /
L=$(ls /usr/lib/python3*/site-packages/configgen/emulatorlauncher.py)    # 2024년 12월 빌드는 python3.11, 그 뒤는 python3.12
cp "$L" /userdata/system/emulatorlauncher.py.before_patch                 # 혹시 몰라 원본을 한 부 남겨요
python3 launcher/hb_patch.py apply launcher/emulatorlauncher.patch "$L"   # patch 명령이 없어도 돼요
knulli-save-overlay                                                       # 옛 KNULLI 빌드는 batocera-save-overlay

# 4) 서비스(원하면): 복사한 뒤 knulli.conf 의 system.services 에 이름을 더해요
mkdir -p /userdata/system/services
cp services/* /userdata/system/services/
```

- 창 끄기: `/userdata/system/knulli.conf` 에 `global.hb_joinask=0`, 또는 `/userdata/system/claude/hb_joinask.off` 파일을 만들어요.
- 실행기 패치 되돌리기: `L=$(ls /usr/lib/python3*/site-packages/configgen/emulatorlauncher.py); python3 launcher/hb_patch.py reverse launcher/emulatorlauncher.patch "$L"` 을 실행하고 오버레이를 한 번 더 저장해요.
- 기록은 `/tmp`(램)에 남아요. 예: `/tmp/hb_joinask.log`.

## 알아 두면 좋은 것

- **와이파이가 느릴 때.** 게임을 켜면 방이 답하기를 길게는 0.8초 기다려요(2026.11.13 릴리즈 전에는 0.4초). 방이 열려 있는데도 창이 안 뜨면 `knulli.conf` 에 `global.hb_joinask_wait=1.5` 처럼 적어 더 기다리게 하세요. 0.2 ~ 3.0초 사이면 돼요. 아무도 답하지 않을 때만 그만큼 늦게 켜지고, 같은 게임 방이 답하면 바로 창이 떠요. 찾는 데 걸린 시간과 답한 방은 `/tmp/hb_joinask.log` 에 남아요.
- **비밀번호를 건 방.** 넷플레이 비밀번호나 관전 비밀번호가 걸린 방은 창이 건너뛰어요. 창에서는 비밀번호를 넣을 수 없어서예요. 집에서는 비밀번호 없이 방을 열거나, 그 방에는 넷플레이 메뉴로 들어가세요.
- **짝 게임은 파일 이름으로 맞춰요.** `hb_ownsave.py` 의 `PAIRS` 에 짝마다 롬 파일 이름(확장자 뺌)이 적혀 있어요. 대소문자는 가리지 않지만 나머지는 `(U) (V1.1)` 같은 꼬리표까지 똑같아야 해요. 두 기기 모두 그 표의 이름을 가진 파일 이름으로 바꿔 주세요. 예: `(("Pokemon - Ruby Version (U) (V1.1)", "루비"), ("Pokemon - Sapphire Version (U) (V1.1)", "사파이어")),` — 칸마다 둘째 낱말은 창에 보이는 짧은 이름이에요. 손님 기기의 같은 롬 폴더에 방장 게임도 같은 파일로 있어야 해요. `hb_joinask.py` 의 `LINK_FAMILIES` 도 같은 식으로 파일 이름을 봐요. `install.sh` 로 업데이트하면 두 파일이 새것으로 바뀌어요. 고쳐 쓰던 파일은 `/userdata/system/hanbang_cores/backup/<이름>.previous` 로 남으니, 고친 줄을 거기서 다시 옮겨 주세요.
- **PSP 애드혹.** 기기마다 `hb_pspadhoc` 서비스를 켜고 `knulli.conf` 에 `psp.ppsspp.Network.proAdhocServer=hbpsp` 한 줄을 넣어요. 그리고 같이할 게임의 애드혹을 켜요: 게임마다 롬 파일 이름 그대로 `psp["<롬 파일 이름>"].ppsspp.Network.EnableWlan=True`(예: `psp["My Game (USA).iso"].ppsspp.Network.EnableWlan=True`), 또는 모든 PSP 게임에 `psp.ppsspp.Network.EnableWlan=True` 한 줄. 게임 훅은 `EnableWlan` 을 이 차례로 봐요. 그 게임의 게임별 줄이 있으면 그 값을 따르고(거기 `=False` 면 그 게임만 빠져요), 없으면 기종 전체 줄을 봐요(`True` · `true` · `1`). 두 줄이 다 없을 때만 PPSSPP 자기 설정 파일 `/userdata/system/configs/ppsspp/PSP/SYSTEM/ppsspp.ini` 의 `[Network]` 절 `EnableWlan` 을 봐요. PPSSPP 가 자기 네트워크 설정을 저장하는 곳이에요(그 파일의 다른 것은 읽지 않아요). 이 값은 실행기가 옛 `ppsspp.ini` 를 이어 쓰는 빌드(파이썬 3.11 이하 · 2024년 12월 빌드 등)에서만 남아요. 지금 KNULLI(파이썬 3.12)는 게임을 켤 때마다 이 파일을 새로 만들어서 PPSSPP 메뉴에서 바꾼 값이 다음 게임까지 가지 않아요. 훅은 새로 만들기 전에 불려서, 앞 게임이 남긴 값 때문에 바로 다음 게임 한 번은 애드혹 게임으로 칠 수 있어요. 그런 빌드에서는 `knulli.conf` 줄을 쓰세요. 기종 전체 줄(또는 PPSSPP 설정)로 켜면 단독 PPSSPP 로 켠 PSP 게임은 모두 애드혹 게임으로 쳐서, 그 게임을 하는 동안 그 기기가 서버가 될 수 있어요. 단독 PPSSPP 만 해당하고, 레트로아크 PPSSPP 코어는 아니에요. 게임을 먼저 켠 기기(같이 켜면 IP 가 가장 작은 기기)가 서버가 되고, 로그인한 사람이 있는 동안은 서버로 남아요. 다른 사람이 아직 하는 중에 서버 기기가 게임을 끄면 서버 노릇을 계속하며 메뉴에 한 줄 알림을 띄워요(알림 글은 아직 한국어만). 무엇을 골랐는지는 `python3 /userdata/system/claude/hb_pspadhoc.py --status` 와 `/tmp/hb_pspadhoc.log` 에서 볼 수 있어요.
- **옛 KNULLI 빌드(2024년 12월 ~ 2025년).** `knulli-save-overlay` 대신 `batocera-save-overlay`, `knulli.conf` 대신 `/userdata/system/batocera.conf` 를 써요. 2024년 12월 빌드는 파이썬도 3.11 이고 `patch` 명령이 없어요. `install.sh` 와 같이하기 창, 실행기 패치는 이걸 알아서 맞춰요(그 릴리즈의 실행기 소스로 확인했고, 그런 빌드가 깔린 기기는 우리에게 없어요). 2024년 12월보다 앞선 빌드는 실행기가 달라서 실행기 패치는 알리고 건너뛰어요. PSP 애드혹 줄은 `knulli.conf` 가 없으면 `batocera.conf` 에서 읽고, 그 줄이 없으면 PPSSPP 자기 네트워크 설정도 봐요(위 **PSP 애드혹**). 다른 스위치(`global.hb_direct` · `global.hb_ds_autopop`)는 아직 `knulli.conf` 만 읽고, `hb_idlesave` 서비스는 `knulli-settings-get` · `knulli-suspend` · `knulli-shutdown` 을 불러서 그 명령이 있는 빌드에서만 일해요.

## 쓰기 전에

- **RG35XX Pro 의 KNULLI** 와 그 자리에 맞춰 만들었어요. 다른 시스템에서는 경로와 훅부터 맞춰 주세요.
- 안에 든 게임 표(`hb_ownsave.py` 의 짝 게임, `hb_joinask.py` 의 짝 묶음 · 싱글팩, `../cores/ds-dsperate/glue/groups.txt` 의 DS 그룹)는 우리가 시험한 파일 이름에 맞춰져 있어요. 가진 파일 이름에 맞게 고쳐 쓰세요.
- 파일마다 맨 위에 짧은 영어 설명이 있고, 그 아래 자세한 메모는 처음 만들 때 적은 한국어 기록이에요.

## 라이선스

GPL-3.0-or-later([`LICENSE`](../LICENSE)). 릴리즈 zip 의 갈무리 글꼴은 SIL Open Font License 1.1 이에요(`fonts/Galmuri-OFL.txt`).
