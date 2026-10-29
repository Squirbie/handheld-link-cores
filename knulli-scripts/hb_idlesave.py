#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_idlesave.py - Saves a state and sleeps after a long idle time in game; saves and powers off just before the battery runs out.
# (2026-10-13) 게임 중 오래 안 누르면 저장하고 잠자기 — KNULLI 절전을 켜면 같이 일함.
# 기기: /userdata/system/claude/hb_idlesave.py · 서비스: /userdata/system/services/hb_idlesave
# 왜: 게임을 켠 채 두면 밤새 배터리가 닳아 꺼짐(2번 기기 10/10). D9 에 KNULLI 절전(5분 어둡게·15분 잠자기)을 켜도,
#     잠든 채 배터리가 다 닳으면 마지막 게임 속 저장 뒤의 진행이 사라짐 → 잠들기 바로 전에 '상태 저장'을 해 둠.
# 하는 일:
#   - KNULLI 절전 설정(system.batterysaver.*·system.idlewatcher.*)을 읽어, 잠자기·끄기가 켜져 있을 때만 일함
#     → D9 전(지금 mode·extendedmode 둘 다 none)에는 입력만 지켜보고 아무것도 안 함.
#   - 입력은 KNULLI idlewatcher 와 같은 기준으로 봄: 버튼·십자키는 늘, 스틱은 25%(deadzone=25) 넘게 움직일 때만.
#   - 게임 중에 KNULLI 가 잠재울 때보다 LEAD 초 앞서: ① 상태 저장 ② 저장 파일이 생겼는지 확인 ③ 바로 knulli-suspend(끄기 설정이면 knulli-shutdown -s).
#     저장할 때 누르는 가짜 키를 KNULLI 가 '입력'으로 보고 시계를 처음부터 다시 세므로, 잠자기는 이 서비스가 바로 부름.
#     저장이 안 됐으면 아무것도 안 부르고 KNULLI 에 맡김(그대로 잠듦).
#   - 에뮬레이터별 저장:
#       레트로아크 = 명령 포트(UDP 55355) SAVE_STATE — 슬롯 번호가 저절로 늘어나는 설정(savestate_auto_index)이라 있던 저장을 안 덮음
#       DraStic   = 가상 키보드 '0'(drastic.cfg CONTROL_INDEX_SAVE_STATE = 48) → saves/nds/advanced_drastic/states/롬이름_슬롯.dss
#       PPSSPP    = 가상 키보드 F3(controls.ini Save State = 1-133) → saves/psp/롬이름_슬롯.ppst
#       DSperate  = 패드 guide(312)+y(306 — SDL 이 키 코드를 작은 것부터 번호 매겨 y = b5 = 306, 10/13 시험에서 307(x = 불러오기)로 잘못 눌렀다 바로잡음)
#       mupen64plus = 가상 키보드 F5(mupen64plus.cfg Kbd Mapping Save State = 286) → saves/n64/롬파일이름.st슬롯
#       flycast   = 가상 키보드 F9(mappings/SDL_Keyboard.cfg 66:btn_quick_save) → saves/dreamcast/flycast/롬이름.state(0번)·롬이름_n.state
#       → 이 다섯은 '지금 칸'에 저장함: 빈 칸이거나 지난 잠자기 저장이면 그대로 둠(다시 켜서 MENU+X 한 번이면 이어짐).
#         사용자 상태 저장이 있던 칸이면 미리 떠 둔 사본으로 되돌리고, 새 저장은 1번 칸(MENU+위 한 번) — 그것도 사용자 것이면 9번(PSP 5번째) 칸.
#         (게임 속 저장 .eep·vmu·nvmem 같은 건 손 안 댐)
#     그 밖(포트 게임 등)은 저장 없이 KNULLI 에 맡김.
#   - 잠자기 저장은 게임마다 하나만 남김(새로 만들면 그 게임의 지난 잠자기 저장을 지움 — 그 뒤 손대지 않은 것만).
#   - 충전 중 멈춤(/var/run/battery-saver/*.pause)이 있으면 KNULLI 처럼 쉼.
#   - (10/14) 배터리 바닥 직전: 하던 중(입력이 있어 잠자기가 안 옴) 배터리가 다 되면 전원이 그냥 끊김(2번 기기 10/10 04:48 DS 하던 중 3.25V)
#     → 마지막 게임 속 저장 뒤 진행이 사라지고 카드도 갑자기 끊김. 절전 설정과 상관없이 늘 봄(D9 전에도):
#     화면 배터리(/tmp/battery.percent — KNULLI batteryplus 전압 어림, 방전 중 3.25V = 0%) CRIT_PCT 이하 · 전압 CRIT_MV 아래 · 충전기 빠짐 · 방전 중
#     이 넷이 CRIT_EVERY 초 간격 CRIT_N 번 연달아이고 게임 중이면: ① 팝업 'ㅉ 3% 저장하고 꺼요'(MangoHud 쓰는 에뮬레이터만) ② 위와 같은 상태 저장
#     ③ 충전기 다시 확인 → 그대로 빠져 있으면 knulli-shutdown -s(게임 정상 종료 = 레트로아크는 게임 속 저장도 씀 → 전원 끔).
#     메뉴 화면이면 아무것도 안 함(남은 진행 없음 · 켜자마자 꺼지는 일 없게). 하나라도 못 읽으면 아무것도 안 함. 끄기: /userdata/system/claude/hb_lowbatt.off
#   - (10/14) 같이하기 중 기다리는 쪽: 번갈아 하는 게임·유니온룸·대전 기다리기처럼 한 사람이 오래 안 누르면 KNULLI 가 그 기기만
#     어둡게·소리 끔(mute=1)·잠재워 두 기기 연결이 끊김 → 같이하기 동안 KNULLI 멈춤 파일(MP_PAUSE)을 둠.
#     KNULLI idle·extended 훅은 /var/run/battery-saver/*.pause 가 하나라도 있으면 어둡게·잠자기를 건너뜀(충전 중 멈춤과 같은 길).
#     '같이하기 중' = MP_EVERY 초마다 봄: ① 게임(KNULLI 가 nice -4 로 켬)이 집 안 주소(사설·직접 연결 10.77)와 TCP 로 이어져 있음
#       (레트로아크 넷플레이 방장·손님, PPSSPP 통신 서버 27312, 포트 게임 LAN — 기다리기만 하는 방장(LISTEN)은 안 셈)
#       ② DSperate 기록(/tmp/hb_dsperate.log)에 손님 붙음('a guest joined'·'joined, player'·'was hosting alone') 뒤 떠남이 아직 없음,
#         또는 처음부터 손님(줄이 없음 — 'lan: lanfix' 뒤 6초 넘게 '혼자 방장' 줄이 없으면, hb_direct 와 같은 규칙 · 10/14 13:3x).
#       ③ 게임이 돌고 집 안 다른 기기와 UDP 를 양쪽으로 주고받음 — 스타듀(Lidgren)·마크(RakNet)·PSP 통신처럼 연결 없는 UDP 게임.
#         커널 연결 추적(/proc/net/nf_conntrack, KNULLI 4.9 에 들어 있음)의 ASSURED UDP 흐름 중 UDP_FRESH(30)초 안에 오간 것,
#         두 주소 모두 사설·직접 연결이고 서로 다름(자기 자신끼리·방송·바깥 이름 찾기·UDP_SKIP 서비스 포트는 뺌). DSperate 가 돌 때는 ②만 봄.
#         (10/14 16:5x 기기에서 잼: 스타듀 협동은 둘 다 가만히 있어도 초당 약 0.9개씩 오감 — 처음 판의 '초당 5개' 기준으로는 안 잡혔음 ·
#          마크 혼자는 LAN 찾기 방송과 자기 서버의 답(lo)만 초당 약 1.7개라 개수로 보면 같이하기로 잘못 잡힘 · 켤 때 이름 찾기도 잠깐 늘어남.)
#         연결 추적을 못 읽는 기기에서만 옛 방식: UDP 받기·보내기 둘 다 초당 MP_UDP(0.5)개 넘음(/proc/net/snmp·snmp6).
#     끝나고 MP_GRACE 초 지나면 파일을 지우고, 같이하기 동안 미룬 잠자기 저장을 다시 봄 — 마지막으로 누른 때부터 잠잘 때가 이미 지났으면
#     바로 저장하고 잠재움(KNULLI 는 같이하기 동안 건너뛴 어둡게·잠자기를 다시 안 부름), 아직이면 그때(KNULLI 보다 30초 앞서).
#     끄기: /userdata/system/claude/hb_mp_pause.off
# 기록: /tmp/hb_idlesave.log(램, 게임 이름·결과만) · 잠자기 저장 목록 /userdata/system/hb_idlesave/made.json
# 시험: HB_IDLESAVE_TEST=초 python3 hb_idlesave.py → KNULLI 설정과 상관없이 게임 중 그 초 동안 입력이 없으면 저장만 하고(잠자기 안 부름) 끝냄.
#       HB_LOWBATT_TEST=1 + HB_BATT_PCT·HB_BATT_SYS(가짜 파일) → 배터리 바닥 길을 끝까지 가되 끄기만 안 부르고 끝냄(CRIT_EVERY 는 HB_LOWBATT_EVERY 초로).
# 끄기: knulli.conf system.services 에서 hb_idlesave 를 빼고 재부팅.
import fnmatch
import glob
import ipaddress
import json
import os
import select
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import zipfile

from evdev import InputDevice, UInput, ecodes as e, list_devices

GET = '/usr/bin/knulli-settings-get'
LOG = os.environ.get('HB_IDLESAVE_LOG', '/tmp/hb_idlesave.log')
HOME = os.environ.get('HB_IDLESAVE_HOME', '/userdata/system/hb_idlesave')
MADE = os.path.join(HOME, 'made.json')
PAUSE_DIR = os.environ.get('HB_PAUSE_DIR', '/var/run/battery-saver')
PROC = os.environ.get('HB_PROC', '/proc')
PAD = '/dev/input/event1'
KBD_NAME = 'hb-idlesave-kbd'
LEAD = 30            # KNULLI 가 잠재우기 이만큼 앞서 저장
EXT_AFTER_IDLE = True  # KNULLI extended 시계는 idle 단계 뒤부터 셈 — 10/13 06:5x 1번 기기 시험(idle=60·extended=60 → idle 60초·extended 120초)
DEADZONE = 0.25
TEST = float(os.environ.get('HB_IDLESAVE_TEST', '0') or 0)
MAX_COPY = 300 << 20   # 덮는 에뮬레이터는 이 게임 상태 저장을 미리 떠 두는데, 이보다 크면 건너뜀
IMG = ('.png', '.jpg', '.jpeg')   # 상태 저장에 붙는 그림
BATT_PCT = os.environ.get('HB_BATT_PCT', '/tmp/battery.percent')
BATT_SYS = os.environ.get('HB_BATT_SYS', '/sys/class/power_supply')
LOWBATT_OFF = '/userdata/system/claude/hb_lowbatt.off'
LOWBATT_TEST = os.environ.get('HB_LOWBATT_TEST') == '1'
CRIT_PCT = 3          # 2번 기기 10/10 기록(DS 하던 중): 3% 3294mV 04:41 → 0% 3251mV 04:47 → 꺼짐 = 3% 부터 약 6분
CRIT_MV = 3350        # 화면 % 가 잘못 읽혀도(0 등) 실제 전압이 낮을 때만
CRIT_N = 3
CRIT_EVERY = float(os.environ.get('HB_LOWBATT_EVERY', '15') or 15)
OSD_TEXT = '/tmp/hb_osd.txt'      # hb_osd.py(MangoHud) 팝업 한 줄 — hb_osd 는 자기 글이 바뀔 때만 다시 써서 덮이지 않음
MSG_LOWBATT = 'ㅉ {}% 저장하고 꺼요'   # 31바이트 안(MangoHud exec 글자 한도) · 저·장·고·꺼를 MangoHud 글꼴(hb_osd_font)과 DS·flycast 글자판(hb_osd_atlas.bin) 둘 다에 더함
MP_PAUSE = os.path.join(PAUSE_DIR, '50hb-together.pause')   # 같이하기 동안 KNULLI 어둡게·잠자기 멈춤
MP_OFF = '/userdata/system/claude/hb_mp_pause.off'
MP_EVERY = float(os.environ.get('HB_MP_EVERY', '10') or 10)
MP_GRACE = float(os.environ.get('HB_MP_GRACE', '20') or 20)   # 잠깐 끊겼다 다시 붙는 동안은 그대로
DSP_LOG = os.environ.get('HB_DSP_LOG', '/tmp/hb_dsperate.log')
MP_UDP = float(os.environ.get('HB_MP_UDP', '0.5') or 0.5)    # (연결 추적을 못 읽을 때만) 초당 UDP 받기·보내기 둘 다 이만큼 넘으면 같이하기 — 위 ③
UDP_FRESH = float(os.environ.get('HB_MP_UDP_FRESH', '30') or 30)   # 이 초 안에 오간 UDP 흐름만(연결 추적 남은 시간 = 180 - 지난 초)
UDP_SKIP = {53, 67, 68, 123, 137, 138, 1900, 5353, 5355, 27312}     # 이름 찾기·주소 받기·시계·윈도 이름·UPnP·mDNS·LLMNR·hb_pspadhoc 알림
HELPERS = ('bash', 'sh', 'tee', 'gptokeyb', 'gptokeyb2', 'python', 'python3', 'sleep')   # 포트가 게임과 함께 nice -4 로 켜는 것 — 로그 이름에서 뺌


def log(msg):
    try:
        with open(LOG, 'a') as f:
            f.write(time.strftime('%m-%d %H:%M:%S ') + msg + '\n')
    except OSError:
        pass


def kget(key):
    try:
        r = subprocess.run([GET, key], capture_output=True, text=True, timeout=5)
        return r.stdout.strip()
    except Exception:
        return ''


def as_int(s, d):
    try:
        return int(s)
    except ValueError:
        return d


def plan():
    """[(입력 없는 초, 할 일)] — 할 일 'suspend'·'shutdown'·'save'(어둡게+멈춤 aggressive 때 저장만). 절전이 꺼져 있으면 []."""
    mode = kget('system.batterysaver.mode')
    ext = kget('system.batterysaver.extendedmode')
    t1 = as_int(kget('system.idlewatcher.timer'), 300)
    t2 = as_int(kget('system.idlewatcher.extendedtimer'), 900)
    aggr = kget('system.batterysaver.aggressive') == '1'
    out = []
    if mode in ('suspend', 'shutdown'):
        out.append((t1, mode))
    elif mode in ('dim', 'dispoff') and aggr:
        out.append((t1, 'save'))      # aggressive 는 어둡게 할 때 에뮬레이터를 멈춰서(kill -STOP) 그 전에 저장
    if ext in ('suspend', 'shutdown') and mode not in ('suspend', 'shutdown'):
        out.append(((t1 + t2) if EXT_AFTER_IDLE else t2, ext))
    return sorted(out)


def paused():
    return bool(glob.glob(os.path.join(PAUSE_DIR, '*.pause')))


def pause_file(on):
    try:
        if on:
            os.makedirs(PAUSE_DIR, exist_ok=True)
            if not os.path.exists(MP_PAUSE):
                open(MP_PAUSE, 'w').close()
        elif os.path.exists(MP_PAUSE):
            os.remove(MP_PAUSE)
    except OSError as ex:
        log(f'멈춤 파일 실패: {ex}')


def _addr(h):
    """/proc/net/tcp 주소(4바이트씩 작은 끝 16진) → ipaddress"""
    b = bytes.fromhex(h)
    if len(b) == 4:
        return ipaddress.IPv4Address(b[::-1])
    a = ipaddress.IPv6Address(b''.join(b[i:i + 4][::-1] for i in range(0, 16, 4)))
    return a.ipv4_mapped or a


def lan_tcp():
    """집 안 다른 주소와 이어진(ESTABLISHED) TCP 의 소켓 번호들 — ssh(22)는 뺌"""
    out = set()
    for table in ('tcp', 'tcp6'):
        try:
            with open(f'{PROC}/net/{table}') as f:
                rows = f.read().splitlines()[1:]
        except OSError:
            continue
        for row in rows:
            x = row.split()
            try:
                if x[3] != '01':
                    continue
                lport = int(x[1].rsplit(':', 1)[1], 16)
                rhost, rport = x[2].rsplit(':', 1)
                a = _addr(rhost)
            except (IndexError, ValueError):
                continue
            if 22 in (lport, int(rport, 16)) or a.is_loopback or a.is_unspecified or not a.is_private:
                continue
            out.add(x[9])
    return out


def game_pids():
    """KNULLI 가 켠 게임(emulatorlauncher 'nice -n -4' — idlewatcher aggressive 도 이것으로 찾음)"""
    out = []
    for d in glob.glob(PROC + '/[0-9]*'):
        try:
            with open(d + '/stat') as f:
                st = f.read()
            if int(st[st.rindex(')') + 2:].split()[16]) == -4:
                out.append(d)
        except (OSError, ValueError, IndexError):
            continue
    return out


def sock_inodes(d):
    out = set()
    try:
        fds = os.listdir(d + '/fd')
    except OSError:
        return out
    for fd in fds:
        try:
            link = os.readlink(f'{d}/fd/{fd}')
        except OSError:
            continue
        if link.startswith('socket:['):
            out.add(link[8:-1])
    return out


class DspLog:
    """DSperate 기록을 이어 읽어 '손님이 붙어 있는지' — hb_direct.watch_dsperate 와 같은 규칙.
    (10/14 13:2x 2번 기기에서 찾음) 처음부터 손님으로 켜진 쪽은 붙었다는 줄이 없음('lan: joined, player' 는 자세한 기록 때만 씀)
    → hb_direct 처럼 'lan: lanfix' 줄 뒤 6초 넘게 '혼자 방장' 줄이 없으면 손님으로 봄."""
    ON = ('lan: a guest joined', 'lan: joined, player', '(was hosting alone)')
    OFF = ('lan: the last guest left', 'lan: the host left')
    GUEST_AFTER = 6                               # hb_direct.watch_dsperate 와 같은 6초

    def __init__(self):
        self.key, self.pos, self.on = None, 0, False
        self.lan_at, self.hosting = None, False

    def check(self, now):
        try:
            st = os.stat(DSP_LOG)
            with open(DSP_LOG, 'rb') as f:
                head = f.readline(300)            # '== 시각 롬' — 켤 때마다 새로 씀(같은 파일을 비우고)
                key = (st.st_ino, head)
                if key != self.key or st.st_size < self.pos:
                    self.key, self.pos, self.on = key, 0, False
                    self.lan_at, self.hosting = None, False
                f.seek(self.pos)
                data = f.read()
        except OSError:
            self.key, self.pos, self.on = None, 0, False
            self.lan_at, self.hosting = None, False
            return False
        cut = data.rfind(b'\n') + 1               # 끝난 줄까지만(쓰는 중인 줄은 다음 번에)
        self.pos += cut
        for line in data[:cut].decode('utf-8', 'replace').splitlines():
            if line.startswith('lan: lanfix') and self.lan_at is None:
                self.lan_at = now                 # 같이하기 켜짐(방장이면 곧 '혼자 방장' 줄이 따라옴)
            elif 'lan: hosting, nobody has joined' in line:
                self.hosting = True
            elif any(k in line for k in self.ON):
                self.on = True
            elif any(k in line for k in self.OFF):
                self.on = False
                if 'lan: the host left' in line:  # 손님이던 쪽이 혼자 방장이 됨
                    self.hosting = True
        if self.lan_at is not None and not self.hosting and not self.on and now - self.lan_at > self.GUEST_AFTER:
            self.on = True                        # 처음부터 손님
        return self.on


class UdpRate:
    """온 기기 UDP 주고받은 개수(/proc/net/snmp Udp·snmp6 Udp6)를 지난번과 비교해 초당 (받기, 보내기)"""

    def __init__(self):
        self.prev = None

    @staticmethod
    def counts():
        rx = tx = 0
        with open(PROC + '/net/snmp') as f:
            rows = [r.split() for r in f.read().splitlines() if r.startswith('Udp:')]
        head, vals = rows[0], rows[1]
        rx += int(vals[head.index('InDatagrams')])
        tx += int(vals[head.index('OutDatagrams')])
        try:
            with open(PROC + '/net/snmp6') as f:
                for r in f.read().splitlines():
                    k, _, v = r.partition(' ')
                    if k == 'Udp6InDatagrams':
                        rx += int(v)
                    elif k == 'Udp6OutDatagrams':
                        tx += int(v)
        except OSError:
            pass
        return rx, tx

    def rate(self, now):
        try:
            rx, tx = self.counts()
        except (OSError, ValueError, IndexError):
            self.prev = None
            return 0.0, 0.0
        prev, self.prev = self.prev, (now, rx, tx)
        if not prev or now <= prev[0]:
            return 0.0, 0.0
        dt = now - prev[0]
        return max(0, rx - prev[1]) / dt, max(0, tx - prev[2]) / dt


def comm_of(d):
    try:
        with open(d + '/comm') as f:
            return f.read().strip() or '게임'
    except OSError:
        return '게임'


def _lan_peer(h):
    """연결 추적의 주소가 집 안 다른 기기가 될 수 있는 주소인지(사설·직접 연결 · 방송·여럿·자기 고리·바깥은 아님)"""
    try:
        a = ipaddress.ip_address(h)
    except ValueError:
        return False
    if a.is_loopback or a.is_unspecified or a.is_multicast or not a.is_private:
        return False
    return not (a.version == 4 and int(a) & 0xFF == 255)       # x.x.x.255 = 방송(집·직접 연결 모두 /24)


def peer_udp():
    """집 안 다른 기기와 양쪽으로 오가는 UDP 흐름(연결 추적 ASSURED) 중 UDP_FRESH 초 안에 오간 것의 낮은 포트 —
    없으면 '', 연결 추적을 못 읽으면 None. 자기 자신끼리·방송·바깥(이름 찾기)·서비스 포트(UDP_SKIP)는 뺌."""
    try:
        with open(PROC + '/net/nf_conntrack') as f:
            rows = f.read().splitlines()
    except OSError:
        return None
    try:
        with open(PROC + '/sys/net/netfilter/nf_conntrack_udp_timeout_stream') as f:
            stream = int(f.read())
    except (OSError, ValueError):
        stream = 180
    for r in rows:
        p = r.split()
        if len(p) < 9 or p[2] != 'udp' or '[ASSURED]' not in p:
            continue
        kv = {}
        for x in p[5:]:
            k, eq, v = x.partition('=')
            if eq and k in ('src', 'dst', 'sport', 'dport') and k not in kv:   # 앞 묶음 = 처음 보낸 쪽
                kv[k] = v
        try:
            ttl, sport, dport = int(p[4]), int(kv['sport']), int(kv['dport'])
            src, dst = kv['src'], kv['dst']
        except (KeyError, ValueError):
            continue
        if ttl < stream - UDP_FRESH or src == dst or sport in UDP_SKIP or dport in UDP_SKIP:
            continue
        if _lan_peer(src) and _lan_peer(dst):
            return str(min(sport, dport))
    return ''


def together_now(dsp, udp, now):
    """같이하기 중이면 까닭 한 마디, 아니면 ''"""
    rx, tx = udp.rate(now)                      # 늘 읽어 둠(다음 번 비교)
    if pids('dsperate'):                        # DSperate 는 기록만 봄 — 혼자 방장이어도 방 알림 UDP 를 내보내서
        return 'DS' if dsp.check(now) else ''
    dsp.on = False
    lan = lan_tcp()
    if lan:
        for d in game_pids():
            if sock_inodes(d) & lan:
                return comm_of(d)
    names = [comm_of(d) for d in game_pids()]
    if not names:
        return ''
    name = next((n for n in names if n not in HELPERS), '')
    peer = peer_udp()
    if peer:
        return f'{name} UDP {peer}'.strip()
    if peer is None and rx >= MP_UDP and tx >= MP_UDP:   # 연결 추적을 못 읽는 기기만 — 초당 개수(마크 혼자도 걸릴 수 있음)
        return f'{name or names[0]} UDP {rx:.1f}·{tx:.1f}/초'
    return ''


class Together:
    """같이하기 동안 KNULLI 멈춤 파일을 둠. tick() 이 True 면 방금 끝남(미룬 잠자기 저장을 다시 봄)."""

    def __init__(self):
        self.on, self.seen, self.dsp, self.udp = False, 0.0, DspLog(), UdpRate()
        pause_file(False)                         # 지난번에 비정상으로 끝나 남은 것

    def tick(self, now):
        why = '' if os.path.exists(MP_OFF) else together_now(self.dsp, self.udp, now)
        if why:
            self.seen = now
            pause_file(True)
            if not self.on:
                self.on = True
                log(f'같이하기({why}) — KNULLI 어둡게·잠자기 멈춤')
        elif self.on and now - self.seen >= MP_GRACE:
            self.on = False
            pause_file(False)
            log('같이하기 끝 — 멈춤 풂')
            return True
        return False


def running_game():
    try:
        with urllib.request.urlopen('http://127.0.0.1:1234/runningGame', timeout=3) as r:
            d = json.loads(r.read().decode('utf-8', 'replace'))
        return d if isinstance(d, dict) and d.get('path') else None
    except Exception:
        return None


def pids(name):
    """이름이 name 인 프로그램(comm 또는 실행 파일 이름 — flycast 는 comm 을 'Flycast-rend'로 바꿈, 10/13)."""
    out = []
    for d in glob.glob(PROC + '/[0-9]*'):
        try:
            with open(d + '/comm') as f:
                hit = f.read().strip() == name
            if not hit:
                hit = os.path.basename(os.readlink(d + '/exe')) == name
        except OSError:
            continue
        if hit:
            out.append(int(os.path.basename(d)))
    return out


def emulator():
    for name, key in (('retroarch', 'ra'), ('dsperate', 'dsp'), ('drastic', 'drastic'), ('PPSSPP', 'ppsspp'), ('PPSSPPSDL', 'ppsspp'),
                      ('mupen64plus', 'mupen'), ('flycast', 'flycast')):
        if pids(name):
            return key
    return None


def snap(d, pat):
    """d 안 pat 에 맞는 '파일'만(폴더는 뺌) {경로: (바뀐 시각, 크기)}."""
    out = {}
    for p in glob.glob(os.path.join(d, pat)):
        try:
            if not os.path.isfile(p):
                continue
            st = os.stat(p)
            out[p] = (st.st_mtime_ns, st.st_size)
        except OSError:
            pass
    return out


def wait_new(d, pat, before, secs=12, settle=1.5):
    """d 안에서 새로 생기거나 바뀐 파일(쓰기가 끝나 크기가 멈춘 것) 하나. 없으면 None."""
    end = time.time() + secs
    while time.time() < end:
        time.sleep(0.5)
        now = snap(d, pat)
        hit = [p for p, v in now.items() if before.get(p) != v and not p.endswith('.tmp')]
        if hit:
            p = max(hit, key=lambda x: now[x][0])
            time.sleep(settle)
            again = snap(d, pat)
            if again.get(p) and again[p][1] == now[p][1] and again[p][1] > 0:
                return p
    return None


def load_made():
    try:
        with open(MADE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_made(m):
    os.makedirs(HOME, exist_ok=True)
    tmp = MADE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, MADE)


def remember(game_path, files):
    """이번 잠자기 저장을 적고, 같은 게임의 지난 잠자기 저장(그 뒤 손대지 않은 것)은 지움."""
    m = load_made()
    old = m.get(game_path, [])
    for o in old:
        p, mt, sz = o['p'], o['m'], o['s']
        if p in files:
            continue
        try:
            st = os.stat(p)
            if st.st_mtime_ns == mt and st.st_size == sz:
                os.remove(p)
        except OSError:
            pass
    rec = []
    for p in files:
        try:
            st = os.stat(p)
            rec.append(dict(p=p, m=st.st_mtime_ns, s=st.st_size))
        except OSError:
            pass
    m[game_path] = rec
    save_made(m)


# ── 에뮬레이터별 저장 ──
def save_ra(game):
    d = os.path.join('/userdata/saves', game.get('systemName') or os.path.basename(os.path.dirname(game['path'])))
    stem = os.path.splitext(os.path.basename(game['path']))[0]
    pat = glob.escape(stem) + '.state*'
    before = snap(d, pat)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(b'SAVE_STATE', ('127.0.0.1', 55355))
    s.close()
    p = wait_new(d, pat, before)
    if not p:
        return None
    if p.endswith('.png'):
        p = p[:-4]
    files = [p] + ([p + '.png'] if os.path.exists(p + '.png') else [])
    return files


_ui = None


def kbd():
    global _ui
    if _ui is None:
        _ui = UInput({e.EV_KEY: [e.KEY_0, e.KEY_F3, e.KEY_F5, e.KEY_F9]}, name=KBD_NAME)
        time.sleep(2.5)   # 에뮬레이터(SDL)가 새 키보드를 알아챌 시간
    return _ui


def tap_key(code):
    ui = kbd()
    ui.write(e.EV_KEY, code, 1)
    ui.syn()
    time.sleep(0.15)
    ui.write(e.EV_KEY, code, 0)
    ui.syn()


def tap_pad(codes):
    with open(PAD, 'wb', buffering=0) as fd:
        def ev(t, c, v):
            n = time.time()
            s = int(n)
            fd.write(__import__('struct').pack('qqHHi', s, int((n - s) * 1e6), t, c, v))
            fd.write(__import__('struct').pack('qqHHi', s, int((n - s) * 1e6), 0, 0, 0))
        for c in codes:
            ev(1, c, 1)
            time.sleep(0.12)
        time.sleep(0.15)
        for c in reversed(codes):
            ev(1, c, 0)
            time.sleep(0.05)


def slot_save(d, pat, press, alt_names, prefix):
    """지금 칸에 저장하는 에뮬레이터: 이 게임 파일(이름이 prefix 로 시작)만 떠 두고 → 저장 →
    빈 칸이었거나 지난 잠자기 저장 자리면 그대로(MENU+X 로 바로 불러옴), 사용자 저장 자리면 그건 되돌리고 새 저장은 alt_names(p) 중 빈(또는 지난 잠자기) 칸으로.
    덮이거나 새로 생긴 상태 저장(pat)·그 그림·되돌리기 파일은 저장 전 그대로 되돌림. 게임 속 저장(.eep·vmu·nvmem 등)은 손 안 댐."""
    before = snap(d, '*')
    mine = sorted(q for q in before if os.path.basename(q).startswith(prefix))
    size = sum(before[q][1] for q in mine)
    if size > MAX_COPY:
        log(f'이 게임 상태 저장이 커서({size >> 20}MB) 사본 없이 덮을 수 없음 — 건너뜀')
        return None
    keep = os.path.join(HOME, 'keep')
    shutil.rmtree(keep, ignore_errors=True)
    os.makedirs(keep)
    copies = {}
    for i, q in enumerate(mine):
        c = os.path.join(keep, str(i))
        shutil.copy2(q, c)
        copies[q] = c
    try:
        press()
        p = wait_new(d, pat, before)
        if not p:
            return None
        time.sleep(1.0)                      # 같이 쓰는 그림(썸네일)까지 기다림
        changed = [q for q, v in snap(d, '*').items() if before.get(q) != v]
        states = {os.path.splitext(os.path.basename(q))[0] for q in changed if fnmatch.fnmatchcase(os.path.basename(q), pat)}

        def related(q):
            n = os.path.basename(q)
            b, ext = os.path.splitext(n)
            return fnmatch.fnmatchcase(n, pat) or (ext.lower() in IMG and b in states)
        changed = [q for q in changed if related(q)]   # flycast 는 저장하며 dc_nvmem.bin 도 씀 → 그대로 둠
        stem_p = os.path.splitext(p)[0]
        comp = [q for q in changed if q != p and os.path.splitext(q)[0] == stem_p]   # 같은 이름 그림(.jpg·.png)만 — .undo.* 는 아님
        res = None
        if p not in before or ours_unchanged(p, before.get(p)):
            res = [p] + comp                 # 빈 칸·지난 잠자기 저장 자리 → 지금 칸 그대로
        else:
            for target in alt_names(p):      # 사용자 저장이 있던 칸 → 그건 되돌리고 새 저장은 다음 칸으로
                if target == p or (os.path.exists(target) and not ours_unchanged(target, stat_of(target))):
                    continue                 # 그 칸에도 사용자 저장이 있으면 안 덮음
                os.replace(p, target)
                res = [target]
                stem_t = os.path.splitext(target)[0]
                for q in comp:
                    if os.path.exists(q):
                        nq = stem_t + q[len(stem_p):]
                        os.replace(q, nq)
                        res.append(nq)
                break
        for q in changed:
            if res and q in res:
                continue
            if q in copies:
                shutil.copy2(copies[q], q)   # 덮인 사용자 파일 되돌림
            elif os.path.exists(q):
                os.remove(q)                 # 저장하며 새로 생긴 군것(되돌리기 파일 등)
        return res
    finally:
        shutil.rmtree(keep, ignore_errors=True)


def stat_of(p):
    try:
        st = os.stat(p)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def ours_unchanged(p, st):
    """p 가 지난 잠자기 저장이고 그 뒤 손대지 않았나(st = (바뀐 시각, 크기))."""
    if not st:
        return False
    for recs in load_made().values():
        for o in recs:
            if o['p'] == p and (o['m'], o['s']) == tuple(st):
                return True
    return False


def save_drastic(game):
    # advanced_drastic/savestates 는 이 폴더를 묶어 씀(bind) — 이름: 롬이름_슬롯.dss (10/13 1번 기기 시험)
    d = '/userdata/saves/nds/advanced_drastic/states'
    stem = os.path.splitext(os.path.basename(game['path']))[0]
    return slot_save(d, glob.escape(stem) + '_*.dss', lambda: tap_key(e.KEY_0),
                     lambda p: [os.path.join(d, stem + '_1.dss'), os.path.join(d, stem + '_9.dss')], stem + '_')


def nds_code(path):
    try:
        if path.lower().endswith('.zip'):
            with zipfile.ZipFile(path) as z:
                n = [x for x in z.namelist() if x.lower().endswith('.nds')][0]
                with z.open(n) as f:
                    h = f.read(16)
        else:
            with open(path, 'rb') as f:
                h = f.read(16)
        c = h[12:16].decode('ascii')
        return c if c.isalnum() else None
    except Exception:
        return None


def save_ppsspp(game):
    # KNULLI 는 상태 저장을 /userdata/saves/psp 에 롬이름_슬롯.ppst(+ 같은 이름 .jpg)로 둠(10/13 1번 기기 시험) · PPSSPP 칸은 0~4
    d = '/userdata/saves/psp'
    stem = os.path.splitext(os.path.basename(game['path']))[0]
    return slot_save(d, glob.escape(stem) + '_*.ppst', lambda: tap_key(e.KEY_F3),
                     lambda p: [os.path.join(d, stem + '_1.ppst'), os.path.join(d, stem + '_4.ppst')], stem + '_')


def save_dsp(game):
    # 이름: 게임코드.슬롯.dss (예 AMCK.0.dss) · 칸 0~9
    d = '/userdata/saves/nds/dsperate/states'
    code = nds_code(game['path'])
    if not code:
        log('DS 게임 코드를 못 읽음 — 건너뜀')
        return None
    return slot_save(d, code + '.*.dss', lambda: tap_pad([312, 306]),
                     lambda p: [os.path.join(d, code + '.1.dss'), os.path.join(d, code + '.9.dss')], code + '.')


def save_mupen(game):
    # mupen64plus(N64 따로 프로그램): 키보드 F5(mupen64plus.cfg Kbd Mapping Save State = 286) → saves/n64/<롬파일이름>.st<칸> · 칸 바꾸기는 MENU+위(늘리기)뿐
    # (같은 폴더의 롬파일이름.eep·.srm·.mpk 는 게임 속 저장 — 안 건드림, 10/13 1번 기기 시험)
    d = '/userdata/saves/n64'
    rom = os.path.basename(game['path'])
    return slot_save(d, glob.escape(rom) + '.st[0-9]', lambda: tap_key(e.KEY_F5), lambda p: [p[:-1] + '1', p[:-1] + '9'], rom + '.st')


def save_flycast(game):
    # flycast(드림캐스트·아토미스웨이브 따로 프로그램): 키보드 F9(mappings/SDL_Keyboard.cfg 66:btn_quick_save)
    # 이름: 0번 칸 롬이름.state, n번 칸 롬이름_n.state(10/13 1번 기기 F9 시험 · flycast getSavestatePath) · MENU+X = F8(지금 칸 불러오기)
    d = '/userdata/saves/dreamcast/flycast'
    stem = os.path.splitext(os.path.basename(game['path']))[0]
    return slot_save(d, glob.escape(stem) + '*.state', lambda: tap_key(e.KEY_F9),
                     lambda p: [os.path.join(d, stem + '_1.state'), os.path.join(d, stem + '_9.state')], stem)


SAVERS = {'ra': save_ra, 'drastic': save_drastic, 'ppsspp': save_ppsspp, 'dsp': save_dsp, 'mupen': save_mupen, 'flycast': save_flycast}


# ── 입력 지켜보기 ──
class Inputs:
    def __init__(self):
        self.devs = {}
        self.quiet_until = 0.0

    def rescan(self):
        have = {d.path for d, _ in self.devs.values()}
        for path in list_devices():
            if path in have:
                continue
            try:
                d = InputDevice(path)
                if d.name == KBD_NAME:
                    d.close()
                    continue
                ab = {}
                for code, info in d.capabilities(absinfo=True).get(e.EV_ABS, []):
                    ab[code] = info
                self.devs[d.fd] = (d, ab)
            except OSError:
                pass

    def wait(self, timeout):
        """timeout 초 동안 기다리며 '사람 입력'이 있었으면 True."""
        fds = list(self.devs)
        if not fds:
            time.sleep(timeout)
            return False
        try:
            r, _, _ = select.select(fds, [], [], timeout)
        except (OSError, ValueError):
            self.devs = {}
            return False
        act = False
        for fd in r:
            d, ab = self.devs.get(fd, (None, None))
            if d is None:
                continue
            try:
                evs = list(d.read())
            except BlockingIOError:
                continue
            except OSError:
                self.devs.pop(fd, None)
                continue
            if time.monotonic() < self.quiet_until:
                continue   # 제가 누른 가짜 키
            for ev in evs:
                if ev.type == e.EV_KEY:
                    act = True
                elif ev.type == e.EV_ABS:
                    info = ab.get(ev.code)
                    if ev.code in (e.ABS_HAT0X, e.ABS_HAT0Y) or info is None:
                        act = act or ev.value != 0
                    else:
                        half = (info.max - info.min) / 2.0
                        mid = (info.max + info.min) / 2.0
                        if half > 0 and abs(ev.value - mid) > DEADZONE * half:
                            act = True
        return act


def do_save(game, emu):
    name = os.path.basename(game['path'])
    if emu not in SAVERS:
        log(f'저장 방법 없음({emu or "?"}) — KNULLI 에 맡김: {name}')
        return False
    try:
        files = SAVERS[emu](game)
    except Exception as ex:
        log(f'저장 실패 {emu} {type(ex).__name__}: {name}')
        return False
    if not files:
        log(f'저장 파일이 안 생김 {emu}: {name}')
        return False
    remember(game['path'], files)
    log(f'저장함 {emu}: {name} → {os.path.basename(files[0])}')
    return True


def _rd(p):
    with open(p) as f:
        return f.read().strip()


def batt_low():
    """(바닥인지, '3% 3290mV'). 화면 % ≤ CRIT_PCT · 전압 < CRIT_MV · 충전기 빠짐 · 방전 중 — 하나라도 못 읽으면 (False, '')."""
    try:
        pct = int(_rd(BATT_PCT))
        mv = int(_rd(os.path.join(BATT_SYS, 'axp2202-battery', 'voltage_now'))) // 1000
        usb = _rd(os.path.join(BATT_SYS, 'axp2202-usb', 'online'))
        st = _rd(os.path.join(BATT_SYS, 'axp2202-battery', 'status'))
    except (OSError, ValueError):
        return False, ''
    return (pct <= CRIT_PCT and 0 < mv < CRIT_MV and usb == '0' and st == 'Discharging'), f'{pct}% {mv}mV'


def osd(text):
    try:
        with open(OSD_TEXT + '.tmp', 'wb') as f:
            f.write(text.encode('utf-8'))
        os.replace(OSD_TEXT + '.tmp', OSD_TEXT)
    except OSError:
        pass


def lowbatt(inp, val):
    """배터리 바닥: 게임 중이면 팝업 → 상태 저장 → 충전기 다시 확인 → 정상 종료. 끝까지 갔으면 True."""
    game = running_game()
    if not game:
        log(f'배터리 바닥 {val} — 메뉴 화면이라 그대로 둠')
        return False
    name = os.path.basename(game['path'])
    log(f'배터리 바닥 {val} — 저장하고 끔: {name}')
    try:
        pct = int(_rd(BATT_PCT))
    except (OSError, ValueError):
        pct = CRIT_PCT
    osd(MSG_LOWBATT.format(pct))
    emu = emulator()
    inp.quiet_until = time.monotonic() + 20
    do_save(game, emu)       # 저장 방법이 없는 게임(포트 등)도 정상 종료는 함(마인크래프트 월드 등 갑자기 끊기는 것보다 나음)
    still, val2 = batt_low()
    if not still:
        log(f'끄기 안 함 — 충전기 꽂힘 등({val2 or "못 읽음"})')
        osd('')
        return False
    if LOWBATT_TEST:
        log('시험 — knulli-shutdown 안 부름')
        return True
    log('knulli-shutdown -s 부름')
    subprocess.run(['/usr/bin/knulli-shutdown', '-s'])
    return True


def main():
    os.makedirs(HOME, exist_ok=True)
    inp = Inputs()
    inp.rescan()
    last = time.monotonic()
    done = False          # 이번 '입력 없는 동안' 이미 처리함
    steps = []
    next_plan = 0.0
    next_scan = time.monotonic() + 10
    next_batt = time.monotonic() + CRIT_EVERY
    low_n = 0
    log('시작' + (f' (시험 {TEST:.0f}초)' if TEST else '') + (' (배터리 바닥 시험)' if LOWBATT_TEST else ''))
    tog = Together()
    next_mp = 0.0
    try:
        signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))   # 서비스 끄기 → 아래 finally 로 멈춤 파일 지움
    except ValueError:
        pass                                  # 맥 시험(스레드 안)
    try:
        while True:
            now = time.monotonic()
            if now >= next_scan:
                inp.rescan()
                next_scan = now + 10
            if now >= next_mp:
                next_mp = now + MP_EVERY
                if tog.tick(now):
                    done = False            # 같이하기 동안 '쉼'으로 넘긴 것을 마지막 입력 기준으로 다시 봄
            if now >= next_batt:
                next_batt = now + CRIT_EVERY
                low, val = batt_low()
                low_n = low_n + 1 if low else 0
                if low_n >= CRIT_N and not os.path.exists(LOWBATT_OFF):
                    low_n = 0
                    if lowbatt(inp, val) and LOWBATT_TEST:
                        return
                    next_batt = time.monotonic() + CRIT_EVERY
            if not TEST and now >= next_plan:
                steps = plan()
                next_plan = now + 20
            if inp.wait(1.0):
                last = time.monotonic()
                done = False
                continue
            idle = time.monotonic() - last
            if done:
                continue
            if TEST:
                due = [(TEST, 'save')] if idle >= TEST else []
            else:
                due = [(t, act) for t, act in steps if idle >= max(60, t - LEAD)]
            if not due:
                continue
            done = True
            act = due[0][1]
            if paused():
                log('같이하기 중 — 쉼' if tog.on else '충전 중 멈춤 — 쉼')
                continue
            game = running_game()
            if not game:
                continue           # 메뉴 화면 — KNULLI 에 맡김
            emu = emulator()
            inp.quiet_until = time.monotonic() + 20
            ok = do_save(game, emu)
            if TEST:
                log('시험 끝')
                return
            if ok and act in ('suspend', 'shutdown'):
                log(f'{act} 부름')
                if act == 'suspend':
                    subprocess.run(['/usr/bin/knulli-suspend'])
                else:
                    subprocess.run(['/usr/bin/knulli-shutdown', '-s'])
                last = time.monotonic()      # 깨어난 뒤 다시 처음부터
                done = False
    finally:
        pause_file(False)


if __name__ == '__main__':
    main()
