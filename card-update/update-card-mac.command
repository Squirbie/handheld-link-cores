#!/bin/bash
# Double-click on a Mac: runs update-card.sh from this folder. 맥에서 두 번 클릭하면 이 폴더의 update-card.sh 를 돌려요.
cd "$(dirname "$0")" || exit 1
bash ./update-card.sh
echo
read -r -p "Enter 를 누르면 창이 닫혀요 · Press Enter to close " _
