#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_dsperate_run.sh - Starts a DS game with DSperate (link play, solo, join prompt).
# (2026-10-12): DS 게임을 DSperate 로 켜기
# 기기: /userdata/system/configs/dsperate/hb_dsperate_run.sh
# advanced_drastic/launch.sh 가 games.txt 에 있는 게임이면 이 스크립트로 넘긴다. ES 에게는 그대로 DraStic 게임으로 보여서
# ES 훅(nds_save_sync.sh: 세이브 맞추기·게임 안 팝업)이 그대로 돈다.
#  1) 켜기 전: hb_dsperate.py pre — 기기 무선 주소 맞추기 + DraStic 세이브(.dsv) ↔ DSperate 세이브(.sav) 새 쪽으로 맞추기
#  2) DSperate 실행. 설정은 이 폴더의 dsperate.ini(두 기기 공통)와 games/<롬이름>.ini(게임마다. 단축키로 고른 화면 배치가 여기 기억됨)
#     버튼: 기기 패드 매핑(gamecontrollerdb_rg35xx.txt, 10/12 시험한 것)을 ES 가 준 매핑 뒤에 붙임(같은 패드면 우리 것이 이김)
#     게임 안 팝업(볼륨·밝기·배터리): /userdata/system/claude/hb_dsosd.so 를 LD_PRELOAD — 화면 넘기기(FBIOPAN_DISPLAY) 직전에 글자를 그림
#  3) 끈 뒤: hb_dsperate.py post — .sav 를 .dsv 로 되돌려 씀(→ 다음에 DraStic·멜론으로 켜도 같은 진행)
# 같이하기(무선, hbfam2 판부터): games.txt 의 게임은 --netplay(자동)로 켬 — 2.5초 안에 같은 그룹 방이 들리면 손님으로 붙고,
#   없으면 방장. 방장은 손님이 붙기 전까지 혼자 하기와 똑같음(상태 저장·빨리 감기·멈춤 됨). 붙으면 PLAYER JOINED, 나가면 PLAYER LEFT.
#   그룹: groups.txt 에 '롬이름<탭>그룹' 줄이 있으면 그 그룹(예: 포켓몬 블랙·화이트 = pkm5), 없으면 게임 코드 4글자(같은 롬끼리만).
#   다른 게임끼리는 안 붙음. 같이하기를 끄려면 이 폴더에 net_off 파일 하나(그러면 늘 혼자 하기).
#   (10/19) 같은 그룹 방이 열려 있으면 켜기 전에 '같이 / 혼자' 창(hb_joinask.py --ds) — 혼자를 고르면 넷 없이 켬.
# 기록: /tmp/hb_dsperate.log (램, 마지막 한 판)
D=/userdata/system/configs/dsperate
ROM="$1"
LOG=/tmp/hb_dsperate.log
echo "== $(date '+%F %T') $ROM" > $LOG
python3 $D/hb_dsperate.py pre "$ROM" >> $LOG 2>&1
# (10/19) dsperate.ini [net] mode 는 늘 off — 같이하기는 아래 --netplay 로만 켬(위 14줄 · 설정 파일 주석과 같은 설계).
#   10/16 01:55 부터 두 기기 ini 가 auto 로 저장돼 있어서, 창에서 '혼자 하기'를 골라 인자 없이 켜도 같은 그룹 방에 손님으로 붙었음
#   (10/19 20:03 두 기기 테트리스 DS 시험). 멈춤 메뉴 NETWORK FEATURES 로 다시 바뀌어도 다음에 켤 때 off 로 되돌림.
python3 - "$D/dsperate.ini" >> $LOG 2>&1 <<'HBNET'
import os, sys
p = sys.argv[1]
try:
    with open(p, encoding='utf-8') as f:
        lines = f.read().split('\n')
except OSError:
    sys.exit(0)
out, sec, was = [], None, None
for line in lines:
    s = line.strip()
    if s.startswith('[') and s.endswith(']'):
        sec = s[1:-1].strip()
    elif sec == 'net' and '=' in s and s[:1] not in '#;' and s.split('=', 1)[0].strip() == 'mode':
        v = s.split('=', 1)[1].split('#')[0].split(';')[0].strip()
        if v != 'off':
            was, line = v, 'mode = off'
    out.append(line)
if was is not None:
    tmp = p + '.hbtmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)
    print('net: dsperate.ini mode %s -> off (같이하기는 --netplay 로만)' % was)
HBNET
# 압축(zip) 게임은 cache/ 에 풀어서 켜고 끝나면 DSperate 가 지움(cache = session). 지난번에 비정상으로 꺼져 남은 것은 여기서 지움
rm -rf "$D/cache"; mkdir -p "$D/cache"
# 상태 저장 폴더가 없으면 DSperate 가 상태 저장에 실패함(10/12 기기 시험에서 찾음) → 켤 때마다 만들어 둠
mkdir -p /userdata/saves/nds/dsperate/states
cd $D || exit 1
# (2026-10-13): DSperate 는 화면 버퍼를 3장(640x1440)으로 늘려 쓰고 끝나도 그대로 둠. 그러면 ES 가 0·960줄을 번갈아 쓰는데,
#   그 뒤 처음 켜는 DraStic 이 두 번에 한 번꼴로 시작하자마자 죽음(세그폴트, 10/13 01:43·01:54 재현). → 켜기 전 크기를 적어 두었다가 끝나면 되돌림.
FB=/sys/class/graphics/fb0
FBV=$(cat $FB/virtual_size 2>/dev/null)
export XDG_CONFIG_HOME=/userdata/system/configs XDG_RUNTIME_DIR=/var/run
# (2026-10-13 13:4x): 두 기기 같이하기 기본값 — 두 기기 포켓몬 B/W 대전·마리오 카트로 고름
#   DSPERATE_MP_HORIZON=1: 방장이 '이 시각 전엔 더 보낼 것 없음'을 알려 손님이 미리 돎 → B/W 대전 초당 41.7 → 47.8장, 카트 경주 56.4장
#     (두 기기 모두 켜야 켜짐 — 한쪽만이면 예전 그대로 붙음)
#   DSPERATE_MP_TIMEOUT_MS=400: 상대 기기가 잠깐(0.3초) 멈춰도 '통신 에러' 없이 기다림(기본 150ms 는 0.25초 멈춤 한 번에 끊김, 12:49 시험)
#     — 묵은 패킷 버리는 시간도 500ms 로, 손님 기다림도 400ms 로 같이 늘어남. 혼자 하기엔 영향 없음
export DSPERATE_MP_HORIZON=1 DSPERATE_MP_TIMEOUT_MS=400
# 시험용(10/13): /tmp/hb_dsfps 파일이 있으면 1초마다 속도 기록을 로그에 씀(DS_FPS). 램 파일이라 껐다 켜면 없어짐
[ -e /tmp/hb_dsfps ] && export DS_FPS=1
NL='
'
export SDL_GAMECONTROLLERCONFIG="${SDL_GAMECONTROLLERCONFIG:+$SDL_GAMECONTROLLERCONFIG$NL}$(cat $D/gamecontrollerdb_rg35xx.txt)"
OSD=/userdata/system/claude/hb_dsosd.so
[ -f "$OSD" ] && export LD_PRELOAD="$OSD${LD_PRELOAD:+:$LD_PRELOAD}"
NAME=$(basename "$ROM"); NAME=${NAME%.*}
ARGS=()
if [ ! -e $D/net_off ]; then
  ARGS+=(--netplay)
  G=$(awk -F'\t' -v n="$NAME" '$1==n{print $2; exit}' $D/groups.txt 2>/dev/null)
  [ -n "$G" ] && ARGS+=(--lan-group "$G")
  # 같이 / 혼자 고르는 창(10/19): 같은 그룹 방 알림이 들리면(1.1초 듣기 — 방장은 1초마다 알림)
  #   화면에 'A 같이하기 · B 혼자 하기'. A → 그대로(--netplay 가 그 방에 붙음) · B · 10초 지남 → 넷 없이 혼자(내 쪽에 아무도 안 붙음, 상태 저장 됨)
  #   방이 없으면 그대로(--netplay: 찾다가 방장). 끄기: 기기 메뉴 → 게임 설정 → '같이하기 방 물어보기'(knulli.conf global.hb_joinask=0)
  if [ -f /userdata/system/claude/hb_joinask.py ]; then
    JIP=$(python3 /userdata/system/claude/hb_joinask.py nds "$ROM" --ds ${G:+--ds-group "$G"} 2>> $LOG < /dev/null); JR=$?
    echo "joinask: $JR ${JIP}" >> $LOG
    [ "$JR" = 2 ] && ARGS=()
  fi
fi
# 게임마다 같이하기 설정(10/20): mpenv.txt 에 '롬이름<탭>변수=값 …' 줄이 있으면 그 게임만 위 기본값 대신 그 값(DSPERATE_MP_* 와 DS_WIFI_SKIP 만 받음)
#   (10/20 02:5x) DS_WIFI_SKIP=0: 무선 칩 타이머 몰아 돌기(10/13 hbwifi 손질)를 그 게임만 끔 — 마리오 64 DS(한국판)가 켜질 때 펌웨어 읽기 답을 못 받아
#   흰 화면에서 멈추던 원인(VM: 원본 · hbpop 판 정상, hbwifi 뒤 판부터 흰 화면, 이 값만 0 이면 정상)
#   — 소닉 러시 · 드래곤볼 카이 2 는 위 손질(지평선 · 깨어 있기 · 길게 기다리기)과 대전 시작이 안 맞아 원래 값으로
#   두 기기에 같은 파일이어야 함. 파일이 없거나 줄이 없으면 위 기본값 그대로
for kv in $(awk -F'\t' -v n="$NAME" '$1==n{print $2; exit}' $D/mpenv.txt 2>/dev/null); do
  [[ "$kv" =~ ^(DSPERATE_MP_[A-Z_]+|DS_WIFI_SKIP)=[0-9]+$ ]] && { export "$kv"; echo "mpenv: $kv" >> $LOG; }
done
# (10/20 08:1x Claude) 푼 롬 캐시 남은 것 비우기: zip 롬은 DSperate 가 <롬 폴더>/.dsperate/ 에 풀고, 공통 설정 [cart] cache = session 이라 정상 종료면 지우지만
#   강제로 꺼지면(배터리 방전 · 멈춤 · 시험 kill) 그대로 남아 cache_mb 한도(2GB)까지 쌓임(10/20 기기에 드퀘 9 237MB 남아 있었음).
#   DSperate 자체 옵션 --clear-cache = 켜려는 롬 것만 빼고 .dsperate · paths.cache 를 비운 뒤 그대로 실행(기록에 "cache: cleared N MB").
ARGS+=(--clear-cache)
echo "args: ${ARGS[*]}" >> $LOG
HB_T0=$(date +%s)
./dsperate "${ARGS[@]}" "$ROM" >> $LOG 2>&1 &
P=$!
# 같이하기 직접 연결(10/12, /userdata/system/claude/hb_direct.py): 손님이 붙으면 방장 기기는 숨은 작은 공유기를 켜고 손님 기기는 거기 붙어
#   게임 데이터만 공유기를 안 거치고 오감(집 공유기가 몇 초마다 멈춰서). DSperate 가 끝나면 원래대로. 끄기: /userdata/system/claude/hb_direct.off
[ ${#ARGS[@]} -gt 0 ] && [ -f /userdata/system/claude/hb_direct.py ] && setsid nohup python3 /userdata/system/claude/hb_direct.py watch-dsperate $P $LOG > /dev/null 2>&1 < /dev/null &
# 롬을 못 읽으면 DSperate 가 'could not read' 를 적고 끝나다가 제 일꾼 스레드를 기다리며 멈춤(끄라는 신호도 안 들음, 10/12 시험에서 찾음)
#   → 켠 뒤 120초 안에 그 줄이 보이면 2초 뒤 강제로 꺼서 메뉴로 돌아가게 함(깨진 롬, 또는 zip 을 푸는 중에 끄면 생기는 일 — 드퀘 9 는 푸는 데 40초)
( for i in $(seq 1 120); do sleep 1; kill -0 $P 2>/dev/null || exit 0; grep -q '^could not read' $LOG && { sleep 2; kill -9 $P 2>/dev/null; exit 0; }; done ) &
# ES 나 다른 곳에서 이 스크립트를 끄라고 하면 DSperate 에게 넘김(DSperate 는 SIGTERM 을 받으면 세이브를 쓰고 끝남)
trap 'kill -TERM $P 2>/dev/null' TERM INT HUP
RC=0
while :; do wait $P; RC=$?; kill -0 $P 2>/dev/null || break; done
echo "== $(date '+%T') exit $RC" >> $LOG
# 화면 버퍼 되돌리기(위 FBV). 켜기 전부터 3장이었으면(이 고침 전에 남은 것) 화면 높이 x2(ES 기본 2장)로
FBY=$(sed -n 's/^[^:]*:[0-9]*x\([0-9]*\).*/\1/p' $FB/modes 2>/dev/null | head -n1)
[ -n "$FBY" ] && [ "${FBV#*,}" -gt $((FBY*2)) ] 2>/dev/null && FBV="${FBV%,*},$((FBY*2))"
if [ -n "$FBV" ] && [ "$(cat $FB/virtual_size 2>/dev/null)" != "$FBV" ]; then
  echo 0,0 > $FB/pan 2>/dev/null; echo "$FBV" > $FB/virtual_size 2>/dev/null
fi
echo "fb: $(cat $FB/virtual_size 2>/dev/null) pan $(cat $FB/pan 2>/dev/null)" >> $LOG
python3 $D/hb_dsperate.py post "$ROM" >> $LOG 2>&1
# (10/20 22:0x Claude) 켠 뒤 40초 안에 끝난 판은 기록을 남김 — 성검전설 '처음 켤 때 가끔 일찍 꺼짐'(8번 중 1번, 그때 기록은 다음 게임이 덮어 못 봄)이
#   다시 생기면 원인을 보려고. /userdata/system/logs/hb_dsperate_short_<월일_시분초>.log · 최근 5개만 남김
if [ -n "${HB_T0:-}" ] && [ $(( $(date +%s) - HB_T0 )) -lt 40 ]; then
  mkdir -p /userdata/system/logs && cp -f $LOG "/userdata/system/logs/hb_dsperate_short_$(date +%m%d_%H%M%S).log" 2>/dev/null
  ls -1t /userdata/system/logs/hb_dsperate_short_*.log 2>/dev/null | tail -n +6 | while IFS= read -r f; do rm -f "$f"; done
fi
exit $RC
