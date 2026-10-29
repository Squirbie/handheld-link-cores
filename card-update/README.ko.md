<p align="center"><a href="README.md"><img src="../docs/images/lang-en-off.svg" height="44" alt="English"></a><a href="README.ko.md"><img src="../docs/images/lang-ko-on.svg" height="44" alt="한국어 (선택됨)"></a></p>

# card-update — 윈도우 · 맥에서 KNULLI 카드 속 코어 바꾸기

이 코어들이 `system/hanbang_cores/` 에 들어 있는 카드용이에요([`install.sh`](../install.sh) 로 넣은 카드나, 이 코어로 만든 카드 이미지). 카드를 PC 에 꽂고 파일 하나만 실행하면 돼요.

- [최신 릴리스](https://github.com/Squirbie/handheld-link-cores/releases/latest)의 `card-updates.txt` 에 적힌 **아는 옛 판(md5)일 때만** 바꿔요. 모르는 파일은 건드리지 않아요.
- 새 파일은 먼저 확인하고(릴리스 `SHA256SUMS.txt` · 목록의 md5), 옛 파일 옆에 쓴 뒤 한 번 더 확인하고 나서야 바꿔치기해요.
- 옛 파일은 `system/hanbang_cores/backup/` 에 남겨요.

지금 바꾸는 것: **MAME 2003-Plus bf8 → bf9** (`mame2003_plus_libretro.so`).

## 윈도우

1. `system\hanbang_cores` 폴더가 있는 카드를 PC 에 꽂아요(카드가 두 장인 KNULLI 라면 게임 카드).
2. [`card-update.zip`](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/card-update.zip) 을 받아 **압축을 풀고** `update-card-windows.bat` 을 두 번 클릭해요.
   'Windows의 PC 보호' 창이 뜨면 **추가 정보 → 실행** 을 눌러요.
   아니면 PowerShell 에 이 한 줄을 붙여 넣어도 돼요.
   ```powershell
   irm https://raw.githubusercontent.com/Squirbie/handheld-link-cores/main/card-update/update-card-windows.ps1 | iex
   ```
3. Enter 를 누르면 바뀌어요. 카드를 꺼내고(하드웨어 안전하게 제거) 기기에 다시 꽂아요.

## 맥

1. 카드를 맥에 꽂아요.
2. **터미널**을 열고 이 한 줄을 붙여 넣어요.
   ```sh
   curl -fsSL https://raw.githubusercontent.com/Squirbie/handheld-link-cores/main/card-update/update-card.sh | bash
   ```
   zip 안의 `update-card-mac.command` 도 같은 일을 하지만, 맥은 인터넷에서 받은 서명 없는 스크립트를 시스템 설정 → 개인정보 보호 및 보안에서 허용하기 전까지 막아요. 그래서 터미널이 더 빨라요.
3. Enter 를 누르면 바뀌어요. 카드를 꺼내고 기기에 다시 꽂아요.

같은 `update-card.sh` 는 리눅스에서도 돼요(`/media` · `/run/media` · `/mnt` 아래를 찾아요).

## 알아 둘 것

- **같이하기는 두 기기가 같은 판이어야 해요.** 카드 두 장을 모두 바꿔 주세요.
- 새 판은 옛 판의 상태 저장을 못 불러와요(상태 모양이 바뀜). 게임 속 저장 · 하이스코어는 그대로예요.
- 되돌리려면 `system/hanbang_cores/backup/` 의 파일을 제자리에 다시 놓으면 돼요.
- 2026-10-29 시험: 맥(exFAT 카드 이미지 — Enter · n · 터미널 없음 · 이미 새 판 · 모르는 판 · `curl | bash` · `.command`), 윈도우 서버 2025 의 Windows PowerShell 5.1(`.bat` 으로 Enter · n, 이미 새 판, 모르는 판, 카드 없음). 맥에서 카드에 `._` 파일이 남지 않아요.
