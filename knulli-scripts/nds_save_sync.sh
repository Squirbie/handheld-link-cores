#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
# nds_save_sync.sh - EmulationStation game-start / game-end hook for KNULLI that calls the helpers below. Keep it as the only file in /userdata/system/scripts/.
# ES 게임 시작/종료 훅 (scripts/ 폴더에는 실행 파일이 하나만 있어야 함: exFAT이라 모든 파일이 실행돼서)
# 20) 각자 세이브(10/21 4판): 시작 때 지난 거래(강제 종료 · 배터리로 끝난 판의 중간 저장 포함)를 먼저 마무리하고 램만 정리,
#     끝날 때 이번 판 2P 결과를 확인해 자기 1P 세이브에 씀(표 · 롬 CRC · 2P 확인 · CRC32 · SHA-256 · 원본 그대로일 때만).
#     실패해도 카드 거래 폴더(saves/<기종>/.hb_ownsave)는 남겨 다음에 다시. 기록 /tmp/hb_ownsave_finish.log(램, 256KiB 상한).
#     다른 코어로 같은 롬을 켜도 그 롬의 거래 폴더가 있으면 시작 때 먼저 마무리(폴더가 없으면 아무것도 안 함).
#     (10/22 6판) 네오지오 포켓 두 대(21번) · 게임기어 두 대(22번)도 — 네오지오 세이브는 <롬>.flash, 게임기어는 <롬>.srm.
case "$4" in
  mgba_dual|mednafen_wswan_dual|mednafen_ngp_dual|genesisplusgx_gg_dual)
    if [ "$1" = gameStart ]; then
      python3 /userdata/system/claude/hb_ownsave.py start "$2" "$5" >/dev/null 2>&1
    elif [ "$1" = gameStop ]; then
      python3 /userdata/system/claude/hb_ownsave.py finish "$2" "$5" >/dev/null 2>&1
    fi
    ;;
  *)
    if [ "$1" = gameStart ]; then
      case "$2" in gba|wswan|wswanc|gamegear)
        n="${5##*/}"; n="${n%.*}"
        [ -d "/userdata/saves/$2/.hb_ownsave/$n.srm" ] && python3 /userdata/system/claude/hb_ownsave.py start "$2" "$5" >/dev/null 2>&1
        ;;
      ngp|ngpc)
        n="${5##*/}"; n="${n%.*}"
        [ -d "/userdata/saves/$2/.hb_ownsave/$n.flash" ] && python3 /userdata/system/claude/hb_ownsave.py start "$2" "$5" >/dev/null 2>&1
        ;;
      esac
    fi
    ;;
esac
# 1) Westonpack(아이작, 아이코노클라스트)이 만들고 안 지우는 가짜 /dev/dri/card0 정리.
#    남아 있으면 다른 gl4es 포트(스타듀밸리 등)가 GBM 방식으로 잘못 켜져서 바로 튕긴다. 진짜 DRM 장치(/sys/class/drm/card0)가 있으면 건드리지 않음.
if [ -c /dev/dri/card0 ] && [ ! -e /sys/class/drm/card0 ]; then rm -f /dev/dri/card0; rmdir /dev/dri 2>/dev/null; fi
# 3) 스타듀: 포트마스터에서 포트를 업데이트하면 실행 스크립트가 순정으로 덮어써진다. 순정 스크립트는 매번 패처를 돌리는데
#    패처(Cecil)가 R2R dll 에서 멈춰 게임이 안 켜지므로, 그때만 IL 원본을 돌려놓는다(속도는 순정, 게임은 켜짐).
#    낱개 R2R(hanbang/r2r)과 묶음 R2R(hanbang/r2r_bundle, 10/11) 둘 다 확인한다.
case "$5" in
  */StardewValleyMainline.sh)
    G="${5%/*}/stardewvalleymainline"
    if [ "$1" = "gameStart" ] && ! grep -q 'prep.stamp' "$5" 2>/dev/null; then
      for f in "Stardew Valley.dll" "MonoGame.Framework.dll" "xTile.dll" "StardewValley.GameData.dll" "BmFont.dll" \
        "System.Data.HashFunction.Core.dll" "System.Data.HashFunction.Interfaces.dll" "System.Data.HashFunction.xxHash.dll" \
        "Lidgren.Network.dll"; do
        [ -f "$G/hanbang/il/$f" ] && [ -f "$G/gamedata/$f" ] || continue
        cur="$(md5sum < "$G/gamedata/$f")"
        for d in r2r r2r_bundle; do
          [ -f "$G/hanbang/$d/$f" ] && [ "$cur" = "$(md5sum < "$G/hanbang/$d/$f")" ] &&
            cp -f "$G/hanbang/il/$f" "$G/gamedata/$f.hbtmp" && mv -f "$G/gamedata/$f.hbtmp" "$G/gamedata/$f" && break
        done
      done
    fi
    ;;
esac
# 4) 넷플레이 세이브: RetroArch는 넷플레이 중 10초 자동 저장을 꺼서 리셋하면 그 판 저장이 다 날아간다(10/4 2번 기기 리프그린).
#    RetroArch 게임마다 /userdata/system/claude/netplay_sram_flush.py를 띄워 두고, 넷플레이가 보이면 10초마다 SAVE_FILES로 카드에 씀.
#    포켓몬 통신(gpSP)·멜론DS는 호스트·손님 둘 다, 다른 게임은 호스트만(손님은 내 세이브를 .netplay_backup에 한 번 복사만).
#    - 게임을 켤 때마다 지난 게임 것이 남아 있으면 먼저 끔(다른 게임에 잘못 붙지 않게).
#    - RetroArch 명령 포트(UDP 55355)는 기기 안(lo)에서만 받게 막음(같은 와이파이의 다른 기기가 못 보내게).
#    - 넷플레이 저장 도중 리셋으로 .srm이 0바이트가 됐으면 마지막 정상본(.netplay_backup/…/.srm.bak)으로 되돌림.
if [ "$1" = "gameStart" ]; then
  pkill -f netplay_sram_flush.py
  if [ "$3" = "libretro" ]; then
    iptables -C INPUT -p udp --dport 55355 ! -i lo -j DROP 2>/dev/null || iptables -I INPUT -p udp --dport 55355 ! -i lo -j DROP 2>/dev/null
    n="${5##*/}"; n="${n%.*}"; s="/userdata/saves/$2/$n.srm"; b="/userdata/saves/.netplay_backup/$2/$n.srm.bak"
    if [ -f "$b" ] && [ -f "$s" ] && [ ! -s "$s" ]; then
      cp -f "$b" "$s" && echo "$(date '+%F %T') restored $s from $b" >> /userdata/system/logs/netplay_sram_flush.log
    fi
    nohup python3 /userdata/system/claude/netplay_sram_flush.py "$4" "$2" "$5" >> /userdata/system/logs/netplay_sram_flush.log 2>&1 < /dev/null &
  fi
fi
# 6) 게임을 켤 때마다 같은 와이파이의 다른 기기 이름을 /etc/hosts에 적음 → 스타듀밸리 등에서 IP 대신 이름으로 접속(lan_names.sh 가 있을 때만).
if [ "$1" = "gameStart" ] && [ -f /userdata/system/claude/lan_names.sh ]; then
  nohup sh /userdata/system/claude/lan_names.sh >/dev/null 2>&1 < /dev/null &
fi
# 5) 게임이 끝날 때마다(모든 에뮬) 카드 기록을 확정: 이 카드는 exFAT(FUSE)라 fsync가 있어야 빈 칸 표(비트맵)까지 카드에 써짐.
#    안 하면 리셋 뒤 방금 저장한 파일 자리가 빈 칸으로 남아 나중에 다른 파일에 덮일 수 있음.
if [ "$1" = "gameStop" ]; then
  python3 -c "import os; f = os.open('/userdata/system/knulli.conf', os.O_RDONLY); os.fsync(f)" 2>/dev/null
fi
# 7) 게임 안 팝업(볼륨·밝기·배터리 경고·배터리 확인 버튼): hb_osd.py 가 /tmp/hb_osd.txt 에 글자를 쓰면 MangoHud(hud_custom)가 왼쪽 위에 보여 주고,
#    MangoHud 가 안 붙은 레트로아크 게임이면 UDP SHOW_MSG 로 보여 줌. 게임마다 하나만 띄우고 게임이 끝나면 끔. 카드에는 아무것도 안 씀(/tmp는 램).
#    못 켜져도 게임에는 영향 없음. 끄고 싶으면 /userdata/system/claude/hb_osd.off 파일을 하나 만들면 됨(훅은 그대로).
if [ "$1" = "gameStart" ]; then
  pkill -f hb_osd.py 2>/dev/null
  : > /tmp/hb_osd.txt 2>/dev/null
  if [ -f /userdata/system/claude/hb_osd.py ] && [ ! -e /userdata/system/claude/hb_osd.off ]; then
    nohup python3 /userdata/system/claude/hb_osd.py --system "$2" --emulator "$3" --core "$4" --rom "$5" >> /tmp/hb_osd.log 2>&1 < /dev/null &
  fi
elif [ "$1" = "gameStop" ]; then
  pkill -f hb_osd.py 2>/dev/null
  : > /tmp/hb_osd.txt 2>/dev/null
fi
# 8) DS 안전장치: 기기를 오래 켜 두면 DraStic 이 화면용 연속 메모리를 못 받아 GPU 메모리를 계속 새로 잡다가 25~30초 만에
#    기기가 굳고 꺼진다(10/5 확인, 재부팅하면 정상). drastic_guard.py 가 그 상태를 몇 초 만에 알아채 DraStic 만 끄고
#    '재부팅해 주세요' 창을 띄운다. 정상일 때는 보기만 함. 끄기: /userdata/system/claude/drastic_guard.off
if [ "$1" = "gameStart" ] && [ "$2" = "nds" ] && [ "$3" = "advanced_drastic" ] && [ -f /userdata/system/claude/drastic_guard.py ]; then
  pkill -f drastic_guard.py 2>/dev/null
  nohup python3 /userdata/system/claude/drastic_guard.py >/dev/null 2>&1 < /dev/null &
fi
# 9) 마인크래프트: 켜기 직전에 같은 와이파이의 열린 방(다른 친구 기기 포함)을 2.5초 훑어서 서버 목록에 'LAN-이름 실제IP' 줄로 적음.
#    이 마인크래프트(mcpelauncher 1.16)는 방송으로 방을 못 찾고 서버 목록에 적힌 주소에만 물어봐서, 적힌 방만 친구 탭 'LAN 게임'에 뜸
#    (10/5 확인. 127.0.0.1·자기 IP로 대신 응답하는 중계 방식은 게임이 목록에 안 올려서 버림). 짝 기기 줄은
#    이름으로 빼고, 지난번 LAN- 줄은 이번 결과로 바꿈. 방장이 먼저 월드를 열어 둬야 손님 쪽에 뜸.
case "$5" in
  */"Minecraft Bedrock.sh")
    if [ "$1" = "gameStart" ] && [ -f /userdata/system/claude/mc_lan_relay.py ]; then
      for S in /userdata/ports/.minecraftbedrock-data/profiles/*/mcpelauncher/games/com.mojang/minecraftpe/external_servers.txt; do
        [ -f "$S" ] && timeout 8 python3 /userdata/system/claude/mc_lan_relay.py scan --wait 2.5 --servers-file "$S" --write-servers "$S" > /tmp/mc_lan_scan.log 2>&1
      done
    fi
    ;;
esac
# 10) 포켓몬 리본: 켤 때만 CPU 최고 속도를 1.512 → 1.704GHz(이 칩의 가장 높은 단계, KNULLI 기본은 위 2단계를 막아 둠) +
#     performance 로. 맵 29 측정 29~30 → 33fps(10/5, 사용자: 최적화 다 해 보고 부족하면 켜기). 끝나면 켜기 전 값으로 되돌림.
#     마인크래프트 포트도 게임 중 같은 방식(perf_mode)을 씀. 재부팅하면 어차피 원래대로. 끄기: /userdata/system/claude/reborn_fast.off
case "$5" in
  */"Pokemon Reborn.sh")
    C=/sys/devices/system/cpu/cpufreq/policy0
    if [ "$1" = "gameStart" ] && [ ! -e /userdata/system/claude/reborn_fast.off ] && grep -qw 1704000 $C/scaling_available_frequencies 2>/dev/null; then
      [ -f /tmp/hb_cpu_saved ] || echo "$(cat $C/scaling_max_freq) $(cat $C/scaling_governor)" > /tmp/hb_cpu_saved
      echo performance > $C/scaling_governor 2>/dev/null
      echo 1704000 > $C/scaling_max_freq 2>/dev/null
    elif [ "$1" = "gameStop" ] && [ -f /tmp/hb_cpu_saved ]; then
      read -r F G < /tmp/hb_cpu_saved
      echo "$F" > $C/scaling_max_freq 2>/dev/null
      echo "$G" > $C/scaling_governor 2>/dev/null
      rm -f /tmp/hb_cpu_saved
    fi
    ;;
esac
# 11) 닌자거북이(TMNT 슈레더의 복수): 켤 때만 GPU 를 가장 높은 클럭(696MHz)에 고정(scenectrl 1). 그냥 두면 240MHz 에 머물러
#     싸울 때 48~54fps → 고정하면 55~57fps(10/9 측정). CPU 는 그대로(1.704GHz 로 올리면 1~2장 더 나오지만 70도 가까이 올라
#     감속될 수 있어서 안 함). 어떤 게임이든 끝날 때 1 이면 0(자동)으로 되돌림. 끄기: /userdata/system/claude/tmnt_gpu.off
G=/sys/class/devfreq/gpu/device/scenectrl/command
case "$5" in
  */TMNTShreddersRevenge.sh)
    [ "$1" = "gameStart" ] && [ ! -e /userdata/system/claude/tmnt_gpu.off ] && [ -w $G ] && echo 1 > $G 2>/dev/null
    ;;
esac
# 13) PSP(PPSSPP)도 켤 때 GPU 를 696MHz 에 고정(11번과 같은 방법). 그냥 두면 3D 장면에서도 240MHz 에 머물러 느려짐
#     (10/12 피스 워커 첫 임무 걷기: 240MHz 17/20·82% → 고정 20/20·100%, 40초 녹음 소리 끊김 0번). 끝나면 아래 줄이 되돌림.
#     끄기: /userdata/system/claude/psp_gpu.off
[ "$1" = "gameStart" ] && [ "$2" = "psp" ] && [ ! -e /userdata/system/claude/psp_gpu.off ] && [ -w $G ] && echo 1 > $G 2>/dev/null
[ "$1" = "gameStop" ] && [ -w $G ] && [ "$(cat $G 2>/dev/null)" = 1 ] && echo 0 > $G 2>/dev/null
# 12) 같이하기 직접 연결(10/12): 같이하는 동안만 두 기기를 공유기 없이 바로 이어 게임 데이터가 직접 오가게 함(집 공유기가 몇 초마다
#     모든 와이파이 기기를 0.05~0.1초 멈춰서). 레트로아크 게임이면 넷플레이 감시를 띄움(방을 열면 이 기기가 숨은 작은 공유기,
#     남의 방에 들어가면 거기에 붙음). DSperate 는 hb_dsperate_run.sh 가 띄움. 게임이 끝나면 다 끄고 원래대로(남은 것도 치움).
#     끄기: /userdata/system/claude/hb_direct.off
if [ -f /userdata/system/claude/hb_direct.py ] && { [ "$1" = "gameStart" ] || [ "$1" = "gameStop" ]; }; then
  pkill -f "hb_direct.py watch-" 2>/dev/null
  rm -f /tmp/hb_dual_screen      # 10/20 20:5x: 감시가 쓰는 두 대 코어 화면(1P/2P) — 게임마다 새로(남은 2P 가 다음 혼자 게임에 안 먹게)
  if [ -e /tmp/hb_direct/daemon.pid ] || [ -e /tmp/hb_direct/fw_on ] || [ $(( $(cat /sys/class/net/wlan1/flags 2>/dev/null || echo 0) & 1 )) = 1 ]; then
    python3 /userdata/system/claude/hb_direct.py stop >/dev/null 2>&1
  fi
  if [ "$1" = "gameStart" ] && [ "$3" = "libretro" ]; then
    nohup python3 /userdata/system/claude/hb_direct.py watch-retroarch "$2" "$5" "$4" >/dev/null 2>&1 < /dev/null &
  fi
fi
# 14) DS 스틱 누르기 창 켜기/끄기(10/14 19:38): 기기 메뉴 → 게임 설정 → 'DS 게임' → 'DS 스틱 누르기 창'(knulli.conf global.hb_ds_autopop, 끔 = 0 · 켬 = 줄 없음).
#     DS 게임을 켤 때 hb_popup.cfg 의 auto=·fade= 두 줄을 맞춤 — 켬 = 1·40, 끔 = 0·(alpha 와 같은 값 = 흐리게도 안 함 → 예전과 똑같음).
#     DraStic(hb_dsosd.so)·멜론·DSperate(hb_dsperate_run.sh)가 켤 때 그 파일을 읽음. 이미 같으면 파일을 안 건드림.
#     knulli.conf 는 그 한 줄만 grep -q(와이파이 줄이 있어 아무것도 안 찍음).
if [ "$1" = "gameStart" ] && [ "$2" = "nds" ] && [ -f /userdata/system/configs/advanced_drastic/hb_popup.cfg ]; then
  P=/userdata/system/configs/advanced_drastic/hb_popup.cfg
  if grep -q '^global.hb_ds_autopop=0' /userdata/system/knulli.conf 2>/dev/null; then
    a=0; f=$(sed -n 's/^alpha=\([0-9][0-9]*\).*/\1/p' "$P" | head -n1); f=${f:-85}
  else
    a=1; f=40
  fi
  if ! grep -qx "auto=$a" "$P" || ! grep -qx "fade=$f" "$P"; then
    { grep -v -e '^auto=' -e '^fade=' "$P"; echo "auto=$a"; echo "fade=$f"; } > "$P.hbtmp" && mv -f "$P.hbtmp" "$P"
  fi
fi
# 17) 같이 / 혼자 고르는 창(10/19): 레트로아크 게임을 넷플레이가 아닌 보통으로 켤 때
#     같은 와이파이에 같은 게임 방(방장 = 게임 목록에서 A 길게 → 넷플레이 호스트)이 열려 있으면 화면에 'A 같이하기 · B 혼자 하기' 창.
#     A → /tmp/hb_joinask.json → emulatorlauncher(오버레이에 넣은 몇 줄)가 손님(--connect)으로 켬. B · 10초 지남 → 혼자.
#     방이 없으면 0.4초 안에 그냥 지나감(와이파이가 없으면 바로). 15번(TGB Dual)보다 먼저 돌아야 손님 화면(2번 게임보이)을 고름.
#     끄기: 기기 메뉴 → 게임 설정 → '같이하기 방 물어보기'(knulli.conf global.hb_joinask=0). DS 같이하기 게임은 hb_dsperate_run.sh 가 따로 물음.
#     기록 /tmp/hb_joinask.log (램)
if [ "$1" = "gameStart" ]; then
  rm -f /tmp/hb_joinask.json
  if [ "$3" = "libretro" ] && [ -f /userdata/system/claude/hb_joinask.py ]; then
    c="$(tr '\0' ' ' < /proc/$PPID/cmdline 2>/dev/null)"
    case "$c" in *emulatorlauncher*) ;; *) c="$(for p in /proc/[0-9]*; do tr '\0' ' ' < "$p/cmdline" 2>/dev/null; echo; done | grep emulatorlauncher)" ;; esac
    case "$c" in *"-netplaymode "*) ;; *) python3 /userdata/system/claude/hb_joinask.py "$2" "$5" --core "$4" < /dev/null > /dev/null 2>&1 ;; esac
  fi
fi
# 15) TGB Dual(게임보이 두 대를 한 에뮬에서 돌림, 10/15): 우리 게임보이 통신으로 안 붙는 게임만 게임별로 이 코어를 씀.
#     KNULLI 는 이 코어를 늘 '두 화면 나란히'로 켜서(화면이 납작해짐), 켤 때마다 이 게임 전용 설정(.opt)을 씀 —
#     혼자 · 방장 = 1번 게임보이 화면 · 소리, 손님(같이하기로 남의 방에 들어감) = 2번 게임보이 화면 · 소리. 통신 케이블은 늘 켬.
#     레트로아크는 게임 전용 .opt 를 전체 설정보다 먼저 읽음. 손님인지는 emulatorlauncher 의 '-netplaymode client' 로 앎.
if [ "$1" = "gameStart" ] && [ "$4" = "tgbdual" ]; then
  m=1; c="$(tr '\0' ' ' < /proc/$PPID/cmdline 2>/dev/null)"
  case "$c" in *emulatorlauncher*) ;; *) c="$(for p in /proc/[0-9]*; do tr '\0' ' ' < "$p/cmdline" 2>/dev/null; echo; done | grep emulatorlauncher)" ;; esac
  case "$c" in *"-netplaymode client"*) m=2 ;; esac
  [ -f /tmp/hb_joinask.json ] && m=2     # 17번 창에서 '같이'(손님)를 골랐음
  n="${5##*/}"; n="${n%.*}"; d="/userdata/system/configs/retroarch/config/TGB Dual"
  mkdir -p "$d" && printf 'tgbdual_audio_output = "Game Boy #%s"\ntgbdual_gblink_enable = "enabled"\ntgbdual_screen_placement = "left-right"\ntgbdual_single_screen_mp = "player %s only"\ntgbdual_switch_screens = "normal"\n' "$m" "$m" > "$d/$n.opt"
fi
# 18) mGBA Dual(GBA 두 대를 한 에뮬에서 돌림, 10/19): 통신 케이블로 같이하는 GBA 게임(록맨 EXE 4 · 매지컬 베케이션)만 게임별로 이 코어를 씀
#     (knulli.conf gba["<롬 파일 이름>"].core=mgba_dual). 켤 때마다 이 게임 전용 설정(.opt)을 씀 —
#     혼자 · 방장 = 1P 화면 · 소리, 손님(같이하기로 남의 방에 들어감 · 17번 창에서 '같이') = 2P 화면 · 소리(에뮬은 두 기기 모두 GBA 두 대를 같이 돌림).
#     바이오스 두 설정은 두 기기가 같아야 해서 늘 같은 값(10/20: 첫 화면 건너뛰기 ON — 평소 mgba 와 같게). 2P 세이브는 방장 기기의 /userdata/saves/gba/<롬 이름>.p2.srm(손님 기기는 안 씀).
if [ "$1" = "gameStart" ] && [ "$4" = "mgba_dual" ]; then
  m=1P; c="$(tr '\0' ' ' < /proc/$PPID/cmdline 2>/dev/null)"
  case "$c" in *emulatorlauncher*) ;; *) c="$(for p in /proc/[0-9]*; do tr '\0' ' ' < "$p/cmdline" 2>/dev/null; echo; done | grep emulatorlauncher)" ;; esac
  case "$c" in *"-netplaymode client"*) m=2P ;; esac
  [ -f /tmp/hb_joinask.json ] && m=2P     # 17번 창에서 '같이'(손님)를 골랐음
  n="${5##*/}"; n="${n%.*}"; d="/userdata/system/configs/retroarch/config/mGBA Dual"
  s=0; grep -q '^mgba_dual_p2_nocart = "enabled"' "$d/$n.opt" 2>/dev/null && s=1   # 10/21 GBA 1.6 싱글팩(팩 하나로 여럿이 — 손님 GBA 를 팩 없이 바이오스로 켬): 이 줄은 지우지 않고 이어 씀
  case "$n" in "Bomber Man Story"|"Magical Quest Starring Mickey & Minnie"|"Shantae Advance - Risky Revolution (k)") s=1 ;; esac
  mkdir -p "$d" && printf 'mgba_dual_screen = "%s"\nmgba_dual_use_bios = "ON"\nmgba_dual_skip_bios = "ON"\n' "$m" > "$d/$n.opt"
  if [ $s = 1 ]; then printf 'mgba_dual_p2_nocart = "enabled"\n' >> "$d/$n.opt"; fi
fi
# 19) Beetle WonderSwan Dual(원더스완 두 대를 한 에뮬에서 돌림, 10/20): 통신 케이블로 같이하는 원더스완 게임(원피스 그랜드 배틀
#     스완 콜로세움)만 게임별로 이 코어를 씀(knulli.conf wswanc["<롬 파일 이름>"].core=mednafen_wswan_dual). 켤 때마다 이 게임 전용 설정(.opt)을 씀 —
#     방장(ES 에서 A 길게 → 넷플레이 게임 시작 = -netplaymode host) = 1P 화면 · 소리 + 2P 기계 켬(link on),
#     손님(-netplaymode client · 17번 창에서 '같이') = 2P 화면 · 소리 + link on, 혼자(넷플레이 아님) = 1P 화면 + link on.
#     (10/20 20:2x M178: 예전엔 혼자 = link off(2P 기계를 안 돌림)였는데, link 는 켤 때만 읽어서 설명서의 '게임 하다가 MENU+B 로 방 열기'
#      길이 깨짐 → 늘 link on — 혼자 해도 2P 기계가 같이 돎. GBA Dual 도 늘 link on.)
#     2P 세이브는 방장 기기의 /userdata/saves/wswanc/<롬 이름(zip 이면 대개 안 파일 이름)>.p2.sav(없으면 새 카트, 손님 자기 세이브는 17번에서 따로 보냄).
if [ "$1" = "gameStart" ] && [ "$4" = "mednafen_wswan_dual" ]; then
  m=1P; l=on; c="$(tr '\0' ' ' < /proc/$PPID/cmdline 2>/dev/null)"   # 10/20 M178: 혼자도 link on(MENU+B 방 열기 길)
  case "$c" in *emulatorlauncher*) ;; *) c="$(for p in /proc/[0-9]*; do tr '\0' ' ' < "$p/cmdline" 2>/dev/null; echo; done | grep emulatorlauncher)" ;; esac
  case "$c" in *"-netplaymode client"*) m=2P; l=on ;; *"-netplaymode "*) l=on ;; esac
  [ -f /tmp/hb_joinask.json ] && { m=2P; l=on; }     # 17번 창에서 '같이'(손님)를 골랐음
  n="${5##*/}"; n="${n%.*}"; d="/userdata/system/configs/retroarch/config/Beetle WonderSwan Dual"
  # (10/21 세로 게임) 이 파일에 이미 있는 화면 돌리기 줄(wswan_rotate_display · wswan_rotate_keymap)은 남기고 두 줄만 새로 씀 —
  #  세로 다섯(건페이 EX · 타레 판다 건페이 · 매지컬 드롭 · 퍼즐 보블 · 레인보우 아일랜드)은 넣기 스크립트가 원래 코어 .opt 와 같은 내용을 넣음.
  #  코어 1.3-os4 는 portrait 면 원래 코어처럼 세워 보이고 단추도 세로 기준(manual · landscape · 없음 = 예전처럼 가로).
  #  (10/21 박자) 게임별 박자 줄(wswan_dual_link_phase)도 남김 — 뿌요뿌요 통 · 파이어 프로레슬링은 넣기 스크립트가
  #  "half"(1.4 박자)를 넣음. 줄이 없으면 코어 1.5-os4 기본 same(0010 박자 — 원피스 등).
  #  (10/26 코난 짝) 짝 단추 누름 줄(wswan_dual_pair_hold — 코난 08 "2P" · 06 "1P", 코어 1.9-os4)도 남김.
  r="$(grep -E '^wswan_(rotate_(display|keymap)|dual_link_phase|dual_pair_hold) = ' "$d/$n.opt" 2>/dev/null)"
  mkdir -p "$d" && { printf 'wswan_dual_screen = "%s"\nwswan_dual_link = "%s"\n' "$m" "$l"; [ -z "$r" ] || printf '%s\n' "$r"; } > "$d/$n.opt"
  # (10/20 17:5x) 원피스: 세이브 머리(0x0F~0x3F 49바이트)가 비면 통신 대전이 캐릭터 선택 뒤 멈춤 → 없거나 0 일 때만 채움.
  #  10/21: 이름 대신 롬 내용 CRC 로 원피스인지 봄(claude/hb_ownsave.py ophdr — 1P 세이브와 있는 2P 칸, 고칠 것이 없으면 롬을 안 읽음).
  [ "$m" = 2P ] || python3 /userdata/system/claude/hb_ownsave.py ophdr "$2" "$5" >/dev/null 2>&1
fi
# 16) PS1 이어받기 메모리카드(10/19): 뒷편을 처음 켤 때(뒷편 세이브가 아직 없을 때) 앞 편 메모리카드(.srm)를 복사해 와서 시작 —
#     슈로대 F → F 완결편 · 아크 더 래드 1 → 2. 레트로아크 PS1(pcsx_rearmed)은 게임마다 메모리카드가 따로라 그대로는 뒷편이 앞 편 클리어 데이터를 못 읽음.
#     뒷편 세이브가 이미 있으면 아무것도 안 함(덮지 않음). 기록 /userdata/system/logs/hb_memcard_carry.log
if [ "$1" = "gameStart" ] && [ "$2" = "psx" ]; then
  n="${5##*/}"; n="${n%.*}"; pv=""
  case "$n" in
    "Super Robot Taisen F - Kanketsu-hen") pv="Super Robot Taisen F" ;;
    "Arc the Lad II") pv="Arc the Lad" ;;
  esac
  s=/userdata/saves/psx
  if [ -n "$pv" ] && [ ! -e "$s/$n.srm" ] && [ -s "$s/$pv.srm" ]; then
    cp "$s/$pv.srm" "$s/$n.srm" && echo "$(date '+%m-%d %H:%M') $pv → $n 메모리카드 복사" >> /userdata/system/logs/hb_memcard_carry.log
  fi
fi
# 21) Beetle NeoPop Dual(네오지오 포켓 두 대를 한 에뮬에서 돌림, 10/21): 통신 케이블로 같이하는 NGP 게임만 게임별로 이 코어를 씀
#     (knulli.conf ngpc["<롬 파일 이름>"].core=mednafen_ngp_dual). 켤 때마다 이 게임 전용 설정(.opt)을 씀 —
#     방장(ES 에서 A 길게 → 넷플레이 게임 시작 = -netplaymode host) · 혼자 = 1P 화면 · 소리,
#     손님(-netplaymode client · 17번 창에서 '같이') = 2P 화면 · 소리. link 는 늘 on(19번과 같은 까닭 — 켤 때만 읽어서 MENU+B 방 열기 길).
#     세이브: 1P = /userdata/saves/ngpc/<롬 이름>.flash(순정 코어와 같은 파일), 2P = 방장 기기 <롬 이름>.p2.flash
#     (10/22 1.1-os4: 없으면 새 카트 — 1P 세이브를 복사하지 않음, 원칙 '각자 자기 세이브').
#     손님 기기(2P 화면 · 넷플레이 손님)는 끝낼 때 세이브를 쓰지 않음(그 기기 1P 기계엔 방장 세이브가 들어 있어서).
#     (10/22 각자 세이브 6판) 손님이 17번 창에서 '같이'를 고르면 자기 <롬>.flash 를 보내 2P 에 넣고, 끝나면 20번이 손님 기기
#     <롬>.flash 로 되씀. 카드 파이터즈 SNK판 ↔ 캡콤판 · 다이브 얼럿 베키 ↔ 매트는 '짝 게임'(hb_ownsave PAIRS) —
#     손님 창이 자기 판 세이브 + 2P 롬을 보내고 방장 코어가 그때 2P 롬을 바꿈. 그래서 예전처럼 켤 때 2P 를 상대 판으로
#     고정하지 않음(same — 손님이 같은 판이면 같은 판끼리, 짝 판이면 짝).
if [ "$1" = "gameStart" ] && [ "$4" = "mednafen_ngp_dual" ]; then
  m=1P; c="$(tr '\0' ' ' < /proc/$PPID/cmdline 2>/dev/null)"
  case "$c" in *emulatorlauncher*) ;; *) c="$(for p in /proc/[0-9]*; do tr '\0' ' ' < "$p/cmdline" 2>/dev/null; echo; done | grep emulatorlauncher)" ;; esac
  case "$c" in *"-netplaymode client"*) m=2P ;; esac
  [ -f /tmp/hb_joinask.json ] && m=2P     # 17번 창에서 '같이'(손님)를 골랐음
  n="${5##*/}"; n="${n%.*}"; d="/userdata/system/configs/retroarch/config/Beetle NeoPop Dual"
  r=same
  rm -f /tmp/hb_ngp_dual_p2.ngc
  mkdir -p "$d" && printf 'ngp_dual_screen = "%s"\nngp_dual_link = "on"\nngp_dual_p2_rom = "%s"\n' "$m" "$r" > "$d/$n.opt"
fi
# 22) Genesis Plus GX GG Dual(게임기어 두 대를 한 에뮬에서 돌림, 10/22): 기어 투 기어 케이블로 같이하는 게임기어 게임만 게임별로
#     이 코어를 씀(knulli.conf gamegear["<롬 파일 이름>"].core=genesisplusgx_gg_dual). 켤 때마다 이 게임 전용 설정(.opt)을 씀 —
#     방장(ES 에서 A 길게 → 넷플레이 게임 시작 = -netplaymode host) · 혼자 = 1P 화면 · 소리,
#     손님(-netplaymode client · 17번 창에서 '같이') = 2P 화면 · 소리. link 는 늘 on(19 · 21번과 같은 까닭 — 켤 때만 읽어서
#     혼자로 켠 뒤 게임 안 메뉴로 방을 열어도 두 기기가 같게).
#     세이브: 1P = /userdata/saves/gamegear/<롬 이름>.srm(순정 코어와 같은 파일), 2P = 방장 기기 <롬 이름>.p2.sav
#     (없으면 새 카트 — 1P 세이브를 복사하지 않음). 대표 네 게임(소닉 드리프트 2 · 슈퍼 컬럼스 · 팩 어택 · 슈퍼 모나코 GP)은 세이브 없음.
#     (10/22 각자 세이브 6판) 손님(--connect)은 레트로아크가 손님 .srm 을 읽지도 쓰지도 않음(코어가 세이브 램 크기 0) ·
#     17번 창에서 '같이'면 자기 .srm 을 보내 2P 에 넣고 끝나면 20번이 손님 기기 <롬>.srm 으로 되씀(라스트 바이블 스페셜 등).
if [ "$1" = "gameStart" ] && [ "$4" = "genesisplusgx_gg_dual" ]; then
  m=1P; c="$(tr '\0' ' ' < /proc/$PPID/cmdline 2>/dev/null)"
  case "$c" in *emulatorlauncher*) ;; *) c="$(for p in /proc/[0-9]*; do tr '\0' ' ' < "$p/cmdline" 2>/dev/null; echo; done | grep emulatorlauncher)" ;; esac
  case "$c" in *"-netplaymode client"*) m=2P ;; esac
  [ -f /tmp/hb_joinask.json ] && m=2P     # 17번 창에서 '같이'(손님)를 골랐음
  n="${5##*/}"; n="${n%.*}"; d="/userdata/system/configs/retroarch/config/Genesis Plus GX GG Dual"
  mkdir -p "$d" && printf 'gg_dual_screen = "%s"\ngg_dual_link = "on"\n' "$m" > "$d/$n.opt"
fi
# 23) (10/25) FBNeo 넷플레이 손님의 .nv(EEPROM — 설정 · 최고 점수) · .fs(NVRAM) 지키기(원칙 '각자 자기 세이브'):
#     고친 FBNeo(9e31af94)는 EEPROM 을 넷플레이 상태에 실어 두 기기를 맞추므로, 손님 기기의 이 파일은 끝날 때 방장 것으로 써짐.
#     → 켤 때 사본(.pre, 없던 파일은 .none) · netplay_sram_flush.py 가 손님(guest)을 보면 /tmp/hb_np_guest 에 롬 이름을 적음 ·
#     끝날 때 그 표시가 이 롬이면 사본으로 되돌림(없던 파일은 지움). 방장 · 혼자는 그대로(사본만 지움). 사본 자리 saves/.netplay_backup/fbneo_guest/<기종>/
if [ "$3" = "libretro" ] && [ "$4" = "fbneo" ]; then
  n="${5##*/}"; n="${n%.*}"; d="/userdata/saves/$2/fbneo"; k="/userdata/saves/.netplay_backup/fbneo_guest/$2"
  if [ "$1" = "gameStart" ]; then
    rm -f /tmp/hb_np_guest; mkdir -p "$k"
    for e in nv fs; do
      rm -f "$k/$n.$e.pre" "$k/$n.$e.none"
      if [ -f "$d/$n.$e" ]; then cp -p "$d/$n.$e" "$k/$n.$e.pre"; else : > "$k/$n.$e.none"; fi
    done
  elif [ "$1" = "gameStop" ]; then
    if [ "$(cat /tmp/hb_np_guest 2>/dev/null)" = "$n" ]; then
      for e in nv fs; do
        if [ -f "$k/$n.$e.pre" ]; then cp -p "$k/$n.$e.pre" "$d/$n.$e"; elif [ -f "$k/$n.$e.none" ]; then rm -f "$d/$n.$e"; fi
      done
      sync; echo "$(date '+%F %T') fbneo guest: own .nv/.fs of $n restored" >> /userdata/system/logs/netplay_sram_flush.log
    fi
    rm -f /tmp/hb_np_guest "$k/$n.nv.pre" "$k/$n.nv.none" "$k/$n.fs.pre" "$k/$n.fs.none"
  fi
fi
# 2) Keeps DraStic and melonDS DS saves of NDS games in sync (see /userdata/system/claude/nds_save_sync.py).
[ "$2" = "nds" ] || exit 0
python3 /userdata/system/claude/nds_save_sync.py "$@" >> /userdata/system/logs/nds_save_sync.log 2>&1
exit 0
