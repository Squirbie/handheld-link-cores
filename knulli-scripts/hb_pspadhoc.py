#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_pspadhoc.py - PSP ad-hoc multiplayer: a local relay server plus automatic host selection.
#   2026-11-24 (v2): only a device that is running an ad-hoc game announces itself and can become the server; the game
#   hook tells this service when such a game starts and stops. Every device picks the same server by the same rules, a
#   server with players keeps the job (also after its own game ends), and a device with guests does not go to sleep.
#   Works together with v1 devices on the same Wi-Fi (same HBPSP1 message, same server protocol).
#   KNULLI setup in knulli.conf: psp.ppsspp.Network.proAdhocServer=hbpsp, plus
#   psp["<ROM file name>"].ppsspp.Network.EnableWlan=True for each ad-hoc game, and hb_pspadhoc in system.services.
"""PSP 같이하기(애드혹) 집 안 서버 + 서버 고르기 — v2 (판 2.1 · 11/24 · v1 과 같은 와이파이에서 섞여도 됨)
한 파일로 두 시스템: KNULLI(RG35XX 계열 · PPSSPP 1.19.3 단독) · 바나나(RG DS Plus · PPSSPP 1.20.4 단독). 말 · 고르기는 같고, 다른 것은 아래 '시스템마다' 셋뿐.
  판 2.1(2.0 과 말 · 고르기 차례 같음): KNULLI 갈래 · 로그인이 남은 채 L 만 내려놓을 때 B 를 안 보냄(받는 쪽이 바쁜 서버를 지우지 않게)
  · pid 없이 알린 게임은 찾은 PPSSPP 번호를 기억(0.5초마다 /proc 를 다 훑지 않게).
규칙 요약:
  말 (UDP 27312 · 같은 와이파이 방송 · 답은 그 기기에만)
    HBPSP1 <IP>   v1 과 같은 꼴. '서버 기기'(L 이거나 내 서버에 로그인 1 이상)만 15초마다 + 처음 듣는 HBPSP1 에 바로 답.
    HBPSP2 <IP> <표> <로그인> <손님> <따르는 IP> <닉네임> <꼬리>
                  게임 중(G) · 서버(L) · 로그인 1 이상이면 3초마다 + 바뀌면 바로. 쉬는 기기는 먼저 말하지 않고 H 에만 답.
                  표: G 게임 중 · L 서버 · H 답 주세요 · B 떠남 · N 27312 를 못 엶 · 없으면 '-'. v1 은 두 낱말만 받아 이 꼴은 버림.
  고르기 (모든 v2 가 같은 차례 · 게임 중이면 0.5초마다)
    1 로그인 있는 서버가 있으면 로그인 많은 곳(같으면 IP 작은 곳)          — 대전 중 고정 · 늦게 온 작은 IP 가 못 빼앗음
    2 v1 기기가 보이면 'HBPSP1 보낸 기기(+L 인 나)' + 그중 가장 작은 IP 보다 작은 게임 중 v2 → 가장 작은 IP — v1 과 같은 답
    3 게임 중이면서 L 인 기기가 있으면 그중 IP 작은 곳                       — 늦게 온 기기는 따르기만
    4 내가 게임 중이고 2초 듣기가 끝났으면 게임 중 기기 중 가장 작은 IP        — 그게 나면 L
    5 아니면 나(쉬는 기기의 자리 채움 · 먼저 말하지 않음)
  L 내려놓기: 답이 내가 아니고 로그인 0 · 게임이 아니고 로그인 0(바로) · 끌 때 → B 두 번(0.2초 사이). 로그인이 남은 채 L 만 내려놓으면 B 없음(바쁜 서버 그대로).
  손님이 있으면 게임을 꺼도 서버로 남음(/tmp/hb_pspadhoc.guests 에 손님 수).
  잠에서 깸(BOOTTIME-MONOTONIC 10초 넘게 늚) · 내 IP 바뀜: 들은 기록 지움 · 로그인 0 이면 L 내려놓음 · 게임 중이면 다시 듣기.
  PPSSPP 는 hbpsp 이름을 통신 한 판(Init)에 한 번만 풂 → hosts 의 hbpsp 줄을 늘 지금 답으로.
시스템마다 (HB_PSP_PLAT = b · k, 없으면 /data/banana → b · /userdata/system → k)
  게임 켬 · 끔 알림
    바나나: run-psp-sa 가 --game-start --pid <그 셸> (127.0.0.1 UDP HBPSPCTL) · 셸 번호가 사라지면 게임 끝.
    KNULLI: ES 훅(scripts/nds_save_sync.sh 24번)이 애드혹 게임(EnableWlan 이 True · 게임별 줄 → 기종 줄 → 둘 다 없으면 PPSSPP ppsspp.ini [Network])일 때만 /tmp/hb_pspadhoc.game 에
            'start <초> <롬>' · 끌 때 'stop <초>' 한 줄(기다리지 않음). 데몬은 이 파일을 1초 안에 읽고, PPSSPP 프로세스(comm)를 찾아 번호를 기억 →
            30초 안에 안 뜨거나 6초 넘게 없으면 게임 끝(끌 때 훅이 안 불리는 죽음 · 전원 · 잠도). 30초 넘은 귀띔은 무시(서비스를 늦게 켠 때).
  잠 막기(손님 1 이상인 동안)
    바나나: /run/banana/awake.pid 에 내 pid → bananad 가 메뉴에서 저절로 안 잠(비었을 때만 잡고 내 것일 때만 놓음 · 덮개 · 전원 단추 잠은 못 막음).
    KNULLI: /var/run/battery-saver/hbpsp.pause(idle · extended 훅이 건너뜀) → 지운 뒤 idlewatcher 를 다시 켬(안 그러면 다음 손 입력까지 안 잠 · 11/19).
            남이 둔 *.pause 는 안 건드림. 서비스가 죽어 남은 것은 다음에 켤 때 지움.
            게임을 끈 서버 기기에 손님이 남으면 메뉴 알림 한 줄(ES 127.0.0.1:1234/notify · 3초 뒤 · 한 번).
  hosts 쓰기: 바나나는 제자리(그 파일을 /etc/hosts 위에 겹쳐 붙여 둠) · KNULLI 는 v1 처럼 새 파일로 바꿔치기(읽는 쪽이 도중 것을 못 봄).
서버 동작(TCP 27312)은 v1 그대로(PPSSPP 1.19.3 proAdhocServer.cpp 를 옮김 · 같은 IP 다시 로그인은 옛 연결을 끊음).
  python3 hb_pspadhoc.py                                   서비스(서버 + 고르기)
  python3 hb_pspadhoc.py --game-start [--pid N] [--wait S]  애드혹 게임을 켬(S>0 이면 듣기가 끝날 때까지 S초 안에서 기다려 고른 IP 를 찍음)
  python3 hb_pspadhoc.py --game-stop                       게임 끝
  python3 hb_pspadhoc.py --status                          지금 상태"""
import fcntl
import hashlib
import os
import random
import re
import select
import signal
import socket
import struct
import subprocess
import sys
import threading
import time

HB_PSPADHOC_V2 = '2.1'
PLAT = os.environ.get('HB_PSP_PLAT') or ('b' if os.path.isdir('/data/banana') else 'k' if os.path.isdir('/userdata/system') else 'b')
PORT = int(os.environ.get('HB_PSP_PORT', 27312))   # 시험할 때만 바꿈
HOSTS = os.environ.get('HB_PSP_HOSTS', '/etc/hosts')
STATUS = os.environ.get('HB_PSP_STATUS', '/tmp/hb_pspadhoc.status')
GUESTS = os.environ.get('HB_PSP_GUESTS', '/tmp/hb_pspadhoc.guests')
VERFILE = os.environ.get('HB_PSP_VER', '/tmp/hb_pspadhoc.ver')
AWAKE = os.environ.get('HB_PSP_AWAKE', '/run/banana/awake.pid')   # 바나나 bananad: 산 pid 가 적혀 있으면 메뉴에서 저절로 안 잠(그 폴더가 없으면 안 씀)
GAMEFILE = os.environ.get('HB_PSP_GAMEFILE', '/tmp/hb_pspadhoc.game')   # KNULLI ES 훅의 귀띔(start <초> <롬> · stop <초>)
PAUSE = os.environ.get('HB_PSP_PAUSE', '/var/run/battery-saver/hbpsp.pause')   # KNULLI 잠 막기(이 데몬만 쓰는 이름 · 남이 둔 *.pause 는 안 건드림)
IDLEWATCHER = os.environ.get('HB_PSP_IDLEWATCHER', '/etc/init.d/S96idlewatcher-daemon')
ES_NOTIFY = os.environ.get('HB_PSP_ES_NOTIFY', 'http://127.0.0.1:1234/notify')
PROC = os.environ.get('HB_PSP_PROC', '/proc')     # 시험할 때만 바꿈(가짜 /proc)
TAIL = os.environ.get('HB_PSP_TAIL', PLAT + '/' + HB_PSPADHOC_V2 + ('/1.19.3' if PLAT == 'k' else '/1.20.4'))   # 시스템/판/PPSSPP — 진단용(k = KNULLI · b = 바나나)
SIM_BUS = os.environ.get('HB_PSP_SIM_BUS')   # 맥 시험만: 가짜 와이파이(127.0.0.1:포트) · 이때 내 IP 는 HB_PSP_SIM_IP 파일
SIM_IP = os.environ.get('HB_PSP_SIM_IP')
NAME = 'hbpsp'
TAG = '# hanbang-psp'

USER_TIMEOUT = 15          # 초, PPSSPP 는 2초마다 핑을 보냄(serve 는 v1 처럼 벽시계)
V1_EVERY = 15              # HBPSP1(서버 기기만)
V2_EVERY = 3               # HBPSP2(G · L · 로그인 있을 때)
EXPIRE_V1 = 50             # v1 · 쉬는 기기
EXPIRE_GL = 12             # 게임 중 · L
EXPIRE_BUSY = 20           # 로그인 있는 서버
LISTEN = 2.0               # 게임을 켤 때 듣기
V1_GRACE = 0.6             # 처음 듣는 HBPSP1 기기에 H 를 물어보고 이만큼 HBPSP2 가 없으면 v1 기기로 봄
ASK_AT = (0.0, 0.5, 1.0, 1.5)
TICK_ACTIVE, TICK_IDLE = 0.5, 3.0
START_GRACE = 30           # pid 없이 알렸을 때 PPSSPP 가 뜨기를 기다리는 시간
GONE_AFTER = 6             # PPSSPP 가 이만큼 없으면 게임 끝
WAKE_JUMP = 10
GAME_COMMS = ('PPSSPP', 'PPSSPPSDL')
FLAG_OK = set('GLHBN-')

OP_PING, OP_LOGIN, OP_CONNECT, OP_DISCONNECT, OP_SCAN, OP_SCAN_COMPLETE, OP_CONNECT_BSSID, OP_CHAT = range(8)
LOGIN_LEN = 1 + 6 + 128 + 9
CONNECT_LEN = 1 + 8
CHAT_LEN = 1 + 64

lock = threading.Lock()
users = []
groups = {}
serving = threading.Event()


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ───────────────────────────── 서버(TCP) — v1 그대로 ─────────────────────────────
class User:
    def __init__(self, sock, ip):
        self.sock, self.ip = sock, ip
        self.rx, self.last = b'', time.time()
        self.mac = self.name = self.game = self.group = None

    def label(self):
        nick = (self.name or b'').split(b'\0')[0].decode('utf-8', 'replace')
        return f'{socket.inet_ntoa(self.ip)} {nick} {(self.game or b"").decode("ascii", "replace")}'


def send(u, data):
    try:
        u.sock.sendall(data)
    except OSError:
        pass


def connect_packet(u):
    return bytes([OP_CONNECT]) + u.name + u.mac + u.ip


def logout(u):
    if u not in users:
        return
    if u.group is not None:
        disconnect(u)
    users.remove(u)
    try:
        u.sock.close()
    except OSError:
        pass
    if u.game is not None:
        log('logout', u.label())


def login(u, pkt):
    mac, name, game = pkt[1:7], pkt[7:135], pkt[135:144]
    valid = (all(65 <= c <= 90 or 48 <= c <= 57 for c in game) and mac not in (b'\xff' * 6, b'\0' * 6) and name[0] != 0)
    if not valid:
        logout(u)
        return
    if SIM_BUS:                                   # 맥 시험만: 모든 연결이 127.0.0.1 이라 가짜 MAC 뒤 4바이트를 그 기기 IP 로
        u.ip = mac[2:6]
    for o in [o for o in users if o is not u and o.ip == u.ip and o.game is not None]:
        log('same device logged in again, dropping old session', o.label())
        logout(o)
    u.mac, u.name, u.game = mac, name, game
    log('login', u.label())


def connect(u, gname):
    key_name = gname.split(b'\0')[0]
    if u.group is not None or not all(c in b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789' for c in key_name):
        logout(u)
        return
    key = (u.game, key_name)
    g = groups.setdefault(key, {'name': gname, 'members': []})
    bssid = u.mac
    for p in g['members']:
        send(p, connect_packet(u))
        send(u, connect_packet(p))
    if g['members']:
        bssid = g['members'][-1].mac
    g['members'].insert(0, u)
    u.group = key
    send(u, bytes([OP_CONNECT_BSSID]) + bssid)
    log('join group', key_name.decode('ascii', 'replace'), u.label(), 'members', len(g['members']))


def disconnect(u):
    if u.group is None:
        logout(u)
        return
    g = groups[u.group]
    g['members'].remove(u)
    for p in g['members']:
        send(p, bytes([OP_DISCONNECT]) + u.ip)
    if not g['members']:
        del groups[u.group]
    u.group = None


def scan(u):
    if u.group is not None:
        logout(u)
        return
    for (game, _), g in reversed(list(groups.items())):
        if game == u.game:
            send(u, bytes([OP_SCAN]) + g['name'] + g['members'][-1].mac)
    send(u, bytes([OP_SCAN_COMPLETE]))


def chat(u, message):
    if u.group is None:
        logout(u)
        return
    msg = message.split(b'\0')[0][:63].ljust(64, b'\0')
    for p in groups[u.group]['members']:
        if p is not u:
            send(p, bytes([OP_CHAT]) + msg + u.name)


def handle(u):
    while u in users and u.rx:
        op = u.rx[0]
        if u.game is None:
            if op != OP_LOGIN:
                logout(u)
                return
            if len(u.rx) < LOGIN_LEN:
                return
            pkt, u.rx = u.rx[:LOGIN_LEN], u.rx[LOGIN_LEN:]
            login(u, pkt)
        elif op == OP_PING:
            u.rx = u.rx[1:]
        elif op == OP_CONNECT:
            if len(u.rx) < CONNECT_LEN:
                return
            pkt, u.rx = u.rx[:CONNECT_LEN], u.rx[CONNECT_LEN:]
            connect(u, pkt[1:9])
        elif op == OP_DISCONNECT:
            u.rx = u.rx[1:]
            disconnect(u)
        elif op == OP_SCAN:
            u.rx = u.rx[1:]
            scan(u)
        elif op == OP_CHAT:
            if len(u.rx) < CHAT_LEN:
                return
            pkt, u.rx = u.rx[:CHAT_LEN], u.rx[CHAT_LEN:]
            chat(u, pkt[1:])
        else:
            logout(u)
            return


def serve():
    while True:
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(('127.0.0.1' if SIM_BUS else '0.0.0.0', PORT))
            srv.listen(64)
            break
        except OSError as e:
            log('cannot listen on', PORT, e, '- retry in 10s')
            srv.close()
            time.sleep(10)
    log('listening on', PORT)
    serving.set()
    while True:
        with lock:
            socks = [srv] + [u.sock for u in users]
        r, _, _ = select.select(socks, [], [], 1.0)
        with lock:
            now = time.time()
            for s in r:
                if s is srv:
                    try:
                        c, addr = srv.accept()
                    except OSError:
                        continue
                    c.settimeout(2)
                    c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    users.append(User(c, socket.inet_aton(addr[0])))
                    continue
                u = next((x for x in users if x.sock is s), None)
                if u is None:
                    continue
                try:
                    data = s.recv(4096)
                except OSError:
                    data = b''
                if not data:
                    logout(u)
                    continue
                u.rx += data
                u.last = now
                handle(u)
            for u in [u for u in users if now - u.last >= USER_TIMEOUT]:
                logout(u)


def count_users(me):
    """(로그인 수 · 그중 내 IP 가 아닌 것)"""
    mine = socket.inet_aton(me) if me else None
    with lock:
        us = [u for u in users if u.game is not None]
        return len(us), sum(1 for u in us if u.ip != mine)


def user_lines():
    with lock:
        return ['  login ' + u.label() + (' in ' + u.group[1].decode('ascii', 'replace') if u.group else '')
                for u in users if u.game is not None]


# ───────────────────────────── 이름 · 주소 ─────────────────────────────
BASE_NAMES = {'knulli', 'batocera', 'banana', 'rocknix', 'localhost', 'ppsspp'}


def psp_mac(wlan):
    """md5('hanbang-psp-' + wlan0 주소(소문자 · 콜론 17자)) 앞 6바이트 · 첫 바이트 & 0xfc (configgen · run-psp-sa 와 같은 식)"""
    if not wlan:
        return ''
    h = bytearray(hashlib.md5(('hanbang-psp-' + wlan).encode()).digest()[:6])
    h[0] &= 0xfc
    return ':'.join(f'{b:02x}' for b in h)


def psp_nick(host, mac):
    """기기 이름(영문 · 숫자 · - · _ 만 16자) · 3자 아래나 기본 이름이면 HB-<PSP MAC 끝 4자리> · MAC 도 없으면 PPSSPP"""
    n = re.sub(r'[^A-Za-z0-9_-]', '', host or '')[:16]
    if len(n) < 3 or n.lower() in BASE_NAMES:
        n = ('HB-' + mac.replace(':', '')[-4:].upper()) if mac else 'PPSSPP'
    return n


def ipkey(a):
    return tuple(int(x) for x in a.split('.'))


def is_ip(a):
    p = a.split('.')
    return len(p) == 4 and all(x.isdigit() and len(x) <= 3 and int(x) <= 255 for x in p)


def _if_addr(sock, name, req):
    return fcntl.ioctl(sock.fileno(), req, struct.pack('256s', name.encode()[:15]))[20:24]


def wlan_net():
    """(내 주소, 앞자리 길이, 방송 주소) — 기본 길로 나가는 주소(패킷은 안 나감). 와이파이에 안 붙어 있으면 None."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        try:
            s.connect(('192.0.2.1', 9))
            me = s.getsockname()[0]
        except OSError:
            return None
        if not me or me.startswith('127.') or me == '0.0.0.0':
            return None
        raw = socket.inet_aton(me)
        for _, name in socket.if_nameindex():
            try:
                if _if_addr(s, name, 0x8915) != raw:            # SIOCGIFADDR
                    continue
                mask = int.from_bytes(_if_addr(s, name, 0x891b), 'big')   # SIOCGIFNETMASK
            except OSError:
                continue
            plen = bin(mask).count('1')
            brd = (int.from_bytes(raw, 'big') & mask) | (~mask & 0xffffffff)
            return me, plen, socket.inet_ntoa(brd.to_bytes(4, 'big'))
        return me, 24, me.rsplit('.', 1)[0] + '.255'
    finally:
        s.close()


def same_net(ip, net):
    mask = (0xffffffff << (32 - net[1])) & 0xffffffff
    return (int.from_bytes(socket.inet_aton(ip), 'big') & mask) == (int.from_bytes(socket.inet_aton(net[0]), 'big') & mask)


def set_hosts(ip, path=HOSTS, swap=(PLAT == 'k')):
    """hosts 의 hbpsp 줄을 ip 로(바뀔 때만). IP 칸을 15자로 채워 줄 길이가 늘 같게.
    바나나(swap=False): 파일을 바꿔치지 않고 제자리에 씀 — 이 파일을 /etc/hosts 위에 겹쳐 붙여 둠.
    KNULLI(swap=True): v1 처럼 옆에 새로 쓰고 바꿔치기(/etc/hosts · lan_names.sh 도 같은 식) — 읽는 쪽이 쓰는 도중 것을 못 봄."""
    try:
        with open(path) as f:
            cur = f.read()
    except OSError:
        cur = None
    keep = [l for l in (cur or '').splitlines() if not l.rstrip().endswith(TAG)]
    want = '\n'.join(keep + [f'{ip:<15}\t{NAME} {TAG}']) + '\n'
    if want == cur:
        return False
    if swap:
        tmp = path + '.hbpsp'
        with open(tmp, 'w') as f:
            f.write(want)
        if cur is not None:
            try:
                os.chmod(tmp, os.stat(path).st_mode & 0o7777)
            except OSError:
                pass
        os.replace(tmp, path)
        return True
    with open(path, 'r+' if cur is not None else 'w') as f:
        f.write(want)
        f.truncate()
    return True


def hold_awake(on, path=AWAKE):
    """손님이 있는 동안 바나나 메뉴의 저절로 잠(bananad autosleep_minutes · 기본 15분)을 막음.
    잡기: 파일이 없거나 죽은 pid 일 때만 내 pid 를 씀(다른 일이 잡고 있으면 그대로 · 그 일도 기기를 깨워 둠).
    놓기: 내 pid 일 때만 지움. 바나나 update 스크립트 · banana-ui 의 awake 와 같은 식. 바뀌었으면 True."""
    me = os.getpid()
    try:
        with open(path) as f:
            cur = int((f.read().split() or ['0'])[0])
    except (OSError, ValueError):
        cur = 0
    if not on:
        if cur != me:
            return False
        try:
            os.remove(path)
            return True
        except OSError:
            return False
    if cur == me:
        return False
    if cur > 0:
        try:
            os.kill(cur, 0)
            return False
        except ProcessLookupError:
            pass
        except OSError:
            return False
    if not os.path.isdir(os.path.dirname(path) or '.'):
        return False
    try:
        with open(path, 'w') as f:
            f.write(f'{me}\n')
        return True
    except OSError:
        return False


def idle_restart():
    """KNULLI idlewatcher 를 다시 켬(시계 새로 시작 → 그 뒤 5분 어둡게 · 15분 잠). 기다리지 않음(새 세션 · 끝나면 거둠)."""
    try:
        p = subprocess.Popen([IDLEWATCHER, 'restart'], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
        threading.Thread(target=p.wait, daemon=True).start()
        log('idlewatcher restart')
    except OSError as e:
        log('idlewatcher restart error', e)


def hold_pause(on, path=PAUSE):
    """KNULLI: 손님이 있는 동안 *.pause 하나(idle · extended 훅이 있으면 건너뜀). 이 이름은 이 데몬만 씀.
    놓을 때는 지운 뒤 idlewatcher 를 다시 켬 — 멈춘 동안 건너뛴 어둡게 · 잠을 idlewatcher 는 새 입력이 올 때까지 다시 안 부름(11/19).
    바뀌었으면 True."""
    have = os.path.exists(path)
    if on:
        if have:
            return False
        try:
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            with open(path, 'w') as f:
                f.write(f'{os.getpid()}\n')
            return True
        except OSError:
            return False
    if not have:
        return False
    try:
        os.remove(path)
    except OSError:
        return False
    idle_restart()
    return True


# ───────────────────────────── 고르기 ─────────────────────────────
class Peer:
    __slots__ = ('t1', 'first1', 't2', 'flags', 'users', 'guests', 'follow', 'nick', 'tail')

    def __init__(self):
        self.t1 = self.t2 = self.first1 = None
        self.flags, self.users, self.guests, self.follow, self.nick, self.tail = '-', 0, 0, '-', '-', '-'


class Node:
    """한 기기의 고르기. 바깥(소켓 · 파일 · 시계)은 io 로만 — 맥 시험이 같은 코드를 가짜 io 로 돌림."""

    def __init__(self, io):
        self.io = io
        self.net = None
        self.me = None
        self.last_ip = None            # 와이파이가 잠깐 끊겼다 다른 주소로 붙어도 알게
        self.peers = {}
        self.G = self.L = False
        self.game_pid = None
        self.game_t = 0.0
        self.game_seen = None          # pid 없이 알렸을 때: PPSSPP 를 마지막으로 본 때
        self.found_pid = None          # pid 없이 알렸을 때: 찾은 PPSSPP 번호(기억해 두고 그것만 봄)
        self.next_scan = 0.0           # /proc 훑기는 1초에 한 번까지
        self.kept = 0                  # 게임을 끈 서버 기기에 남은 손님 수(알림용)
        self.listen_until = 0.0
        self.asks = []
        self.leader, self.why = None, '-'
        self.next1 = self.next2 = 0.0
        self.next_full = 0.0
        self.next_status = 0.0
        self.pending = []              # (때, 받는 IP, 말)
        self.waiters = []              # (마감, 주소)
        self.last_sig = None
        self.last_seq = None
        self.dirty = True
        self.boot_off = io.boot_offset()
        self.sent = 0                  # 보낸 방송 수(시험용)

    # ── 상태
    def listening(self, now):
        return self.G and now < self.listen_until

    def active(self, now):
        return self.G or self.L or self.io.users(self.me)[0] >= 1

    def flags(self, extra=''):
        f = ('G' if self.G else '') + ('L' if self.L else '') + ('' if self.io.serving() else 'N') + extra
        return f or '-'

    def msg2(self, extra=''):
        u, g = self.io.users(self.me)
        return f'HBPSP2 {self.me} {self.flags(extra)} {u} {g} {self.leader or self.me} {self.io.nick} {TAIL}'.encode()

    def bcast(self, data):
        self.sent += 1
        self.io.bcast(data)

    def fresh2(self, p, now):
        if p.t2 is None:
            return False
        age = now - p.t2
        if p.users >= 1:
            return age <= EXPIRE_BUSY
        if 'G' in p.flags or 'L' in p.flags:
            return age <= EXPIRE_GL
        return age <= EXPIRE_V1

    def choose(self, now):
        me, ok_me = self.me, self.io.serving()
        u, _ = self.io.users(me)
        live = [(ip, p) for ip, p in self.peers.items() if self.fresh2(p, now) and 'N' not in p.flags]
        busy = [(p.users, ip) for ip, p in live if p.users >= 1]
        if ok_me and u >= 1:
            busy.append((u, me))
        if busy:
            return min(busy, key=lambda x: (-x[0], ipkey(x[1])))[1], 'busy'
        G = [ip for ip, p in live if 'G' in p.flags]
        me_g = self.G and ok_me and not self.listening(now)
        if me_g:
            G.append(me)
        v1dev = [ip for ip, p in self.peers.items() if p.t1 is not None and now - p.t1 <= EXPIRE_V1
                 and (p.t2 is None or now - p.t2 > EXPIRE_V1) and now - p.first1 >= V1_GRACE]
        if v1dev:
            V1 = {ip for ip, p in self.peers.items() if p.t1 is not None and now - p.t1 <= EXPIRE_V1}
            V1 |= {ip for ip, p in live if 'L' in p.flags or p.users >= 1}
            if self.L and ok_me:
                V1.add(me)
            m = min(V1, key=ipkey)
            return min(list(V1) + [ip for ip in G if ipkey(ip) < ipkey(m)], key=ipkey), 'v1'
        GL = [ip for ip, p in live if 'G' in p.flags and 'L' in p.flags]
        if self.G and self.L and ok_me:
            GL.append(me)
        if GL:
            return min(GL, key=ipkey), 'gl'
        if me_g:
            return min(G, key=ipkey), 'g'
        return me, 'self'

    def knows_server(self, now):
        return any(self.fresh2(p, now) and 'N' not in p.flags and (p.users >= 1 or ('G' in p.flags and 'L' in p.flags))
                   for p in self.peers.values())

    # ── 사건
    def game_start(self, pid, now):
        self.G, self.game_pid, self.game_t, self.game_seen = True, pid, now, None
        self.found_pid, self.next_scan = None, 0.0
        if self.knows_server(now):
            self.listen_until, self.asks = 0.0, []
            log('game start', f'pid {pid}', 'follow known server')
        else:
            self.listen_until = now + LISTEN
            self.asks = [now + a for a in ASK_AT]
            log('game start', f'pid {pid}', f'listen {LISTEN}s')
        self.dirty = True

    def game_end(self, why):
        if self.G:
            log('game end', why)
        self.G, self.game_pid, self.listen_until, self.asks = False, None, 0.0, []
        self.dirty = True

    def reset(self, why, now):
        log('reset', why)
        self.peers.clear()
        if self.io.users(self.me)[0] == 0 and self.L:
            self.L = False
            if why == 'wake':
                self.say_bye()
        if self.G:
            self.listen_until = now + LISTEN
            self.asks = [now + a for a in ASK_AT]
        self.leader = None
        self.dirty = True

    def say_bye(self, now=None):
        if not self.me:
            return
        self.bcast(self.msg2('B'))
        self.pending.append(((now or self.io.now()) + 0.2, None, self.msg2('B')))

    def on_ctl(self, words, addr, now):
        """HBPSPCTL start <pid|-> <wait> <seq> · stop <seq> — 127.0.0.1 에서 온 것만(부르는 쪽이 확인)"""
        if len(words) < 2:
            return
        cmd, seq = words[1], words[-1]
        dup = seq == self.last_seq
        self.last_seq = seq
        if cmd == b'start' and len(words) >= 5:
            try:
                pid = int(words[2]) if words[2] != b'-' else None
                wait = min(float(words[3]), 10.0)
            except ValueError:
                return
            if not dup:
                self.game_start(pid, now)
                self.tick(now, force=True)
            if wait > 0 and self.listening(now):
                self.waiters.append((min(self.listen_until, now + wait), addr, seq))
            else:
                self.reply(addr, seq)
        elif cmd == b'stop':
            if not dup:
                self.game_end('stop')
                self.tick(now, force=True)
            self.reply(addr, seq)

    def reply(self, addr, seq):
        self.io.ctl_reply(addr, f'HBPSPCTL ok {seq.decode("ascii", "replace")} {self.leader or "-"} {self.why}'.encode())

    def on_udp(self, src, data, now):
        net = self.net
        if not net or src == self.me or not is_ip(src) or not same_net(src, net) or len(data) > 160:
            return
        p = data.split()
        if not p:
            return
        if p[0] == b'HBPSP1':
            if len(p) != 2 or p[1] != src.encode():
                return
            pr = self.peers.setdefault(src, Peer())
            new = pr.t1 is None or now - pr.t1 > EXPIRE_V1
            pr.t1 = now
            if new:
                pr.first1 = now
                log('found', src, '(HBPSP1)')
                self.dirty = True
                if self.is_server():
                    self.io.send(src, f'HBPSP1 {self.me}'.encode())
                if pr.t2 is None or now - pr.t2 > EXPIRE_V1:     # v2 인지 물어봄(v1 은 이 꼴을 버림)
                    self.pending.append((now, src, self.msg2('H')))
                    self.next_full = min(self.next_full, now + V1_GRACE + 0.01)
        elif p[0] == b'HBPSP2':
            if len(p) < 7 or p[1] != src.encode():
                return
            try:
                flags = p[2].decode('ascii')
                u, g = int(p[3]), int(p[4])
                follow = p[5].decode('ascii')
                nick = p[6].decode('ascii', 'replace')[:16]
                tail = p[7].decode('ascii', 'replace')[:24] if len(p) > 7 else '-'
            except (UnicodeDecodeError, ValueError):
                return
            if not set(flags) <= FLAG_OK or not 0 <= u <= 64 or not 0 <= g <= 64:
                return
            if 'B' in flags and 'G' not in flags:     # 떠남
                if self.peers.pop(src, None) is not None:
                    log('bye', src)
                    self.dirty = True
                return
            pr = self.peers.get(src)
            if 'B' in flags and pr is not None:        # 서버만 내려놓음(게임은 계속) → HBPSP1 기록을 지움
                pr.t1 = pr.first1 = None
                self.dirty = True
            if pr is None:
                pr = self.peers[src] = Peer()
                log('found', src, flags, nick, tail)
            old = (pr.flags, pr.users)
            pr.t2, pr.flags, pr.users, pr.guests, pr.follow, pr.nick, pr.tail = (
                now, flags.replace('H', '').replace('B', '') or '-', u, g, follow, nick, tail)
            if old != (pr.flags, pr.users):
                self.dirty = True
            if 'H' in flags:
                self.pending.append((now + random.uniform(0, 0.15), src, None))

    def is_server(self):
        return self.L or (self.io.serving() and self.io.users(self.me)[0] >= 1)

    # ── 0.5초(쉬면 3초)마다 · 무엇이 바뀌면 바로
    def tick(self, now, force=False):
        if force or self.dirty or now >= self.next_full:
            self.full(now)
        if not self.me:
            return
        for item in [x for x in self.pending if now >= x[0]]:
            self.pending.remove(item)
            t, dest, data = item
            data = data or self.msg2()
            if dest is None:
                self.bcast(data)
            else:
                self.io.send(dest, data)
        while self.asks and now >= self.asks[0]:
            self.asks.pop(0)
            self.bcast(self.msg2('H'))
        if self.waiters and not self.listening(now):
            self.full(now)
        for w in [w for w in self.waiters if now >= w[0] or not self.listening(now)]:
            self.waiters.remove(w)
            self.reply(w[1], w[2])

    def full(self, now):
        self.dirty = False
        net = self.io.net()
        off = self.io.boot_offset()
        if off is not None and self.boot_off is not None and off - self.boot_off > WAKE_JUMP:
            self.boot_off = off
            self.reset('wake', now)
        self.boot_off = off
        if net and self.last_ip and net[0] != self.last_ip:
            old = self.last_ip
            self.net, self.me = net, net[0]
            self.reset(f'my ip {old} -> {net[0]}', now)
        self.net, self.me = net, (net[0] if net else None)
        if net:
            self.last_ip = net[0]
        if self.G:
            self.watch_game(now)
        for ip in [ip for ip, p in self.peers.items()
                   if (p.t1 is None or now - p.t1 > EXPIRE_V1) and not self.fresh2(p, now)]:
            del self.peers[ip]
            log('gone', ip)
        if not net:
            self.L, self.leader = False, None
            self.next_full = now + TICK_IDLE
            self.write_status(now)
            return
        leader, why = self.choose(now)
        u, g = self.io.users(self.me)
        L = leader == self.me and why != 'self' and self.io.serving() and (self.G or u >= 1)
        if L != self.L:
            self.L = L
            log('server' if L else 'not server', f'({why})')
            if L:
                self.next1 = 0.0
            elif u == 0:                               # (2.1) 로그인이 남았으면 아직 바쁜 서버(HBPSP1 · HBPSP2 계속) → B 를 안 보냄
                self.say_bye(now)                      #   (2.0 은 보냈음 → 받는 쪽이 바쁜 서버를 지웠다가 3초 안에 다시 넣음)
        if leader != self.leader or why != self.why:
            if leader != self.leader:
                log('hbpsp ->', leader, f'({why})')
            self.leader, self.why = leader, why
        try:
            self.io.set_hosts(leader)
        except OSError as e:
            log('hosts error', e)
        sig = (self.flags(), u, g, leader)
        if (self.G or self.L or u >= 1) and (now >= self.next2 or sig != self.last_sig):
            self.bcast(self.msg2())                    # HBPSP2 를 먼저(받는 쪽이 v2 서버를 v1 으로 잘못 보지 않게)
            self.next2 = now + V2_EVERY
        self.last_sig = sig
        if self.is_server():
            if now >= self.next1:
                self.bcast(f'HBPSP1 {self.me}'.encode())
                self.next1 = now + V1_EVERY
        else:
            self.next1 = 0.0
        self.io.guests(g)
        kept = g if (g >= 1 and not self.G) else 0     # 게임을 끈 서버 기기에 손님이 남음 → 메뉴 알림(KNULLI) · 한 번
        if (kept >= 1) != (self.kept >= 1):
            notify = getattr(self.io, 'notify', None)
            if notify:
                notify(kept)
        self.kept = kept
        self.next_full = now + (TICK_ACTIVE if (self.G or self.L or u >= 1) else TICK_IDLE)
        if self.listening(now):
            self.next_full = min(self.next_full, self.listen_until + 0.01)
        if self.L or self.G or now >= self.next_status or sig != getattr(self, '_st_sig', None):
            self._st_sig = sig
            self.write_status(now)

    def watch_game(self, now):
        if self.game_pid is not None:                  # 부른 쪽이 준 번호(바나나 run-psp-sa 셸) — 사라지면 끝
            if not self.io.pid_alive(self.game_pid):
                self.game_end(f'pid {self.game_pid} gone')
            return
        # pid 없이 알림(KNULLI 훅 · --game-start 만): PPSSPP 를 찾아 번호를 기억 → 그 번호만 봄(0.5초마다 /proc 를 다 훑지 않게)
        alive = getattr(self.io, 'game_alive', None)
        if self.found_pid is not None and alive is not None and alive(self.found_pid):
            self.game_seen = now
            return
        self.found_pid = None
        seen = False
        if now >= self.next_scan:
            self.next_scan = now + 1.0
            r = self.io.game_running()                 # 기기: 찾은 번호(없으면 None) · 맥 모의: True/False
            if r:
                seen = True
                if r is not True and alive is not None:
                    self.found_pid = r
                    log('PPSSPP pid', r)
        if seen:
            self.game_seen = now
        elif self.game_seen is None:
            if now - self.game_t > START_GRACE:
                self.game_end('no PPSSPP')
        elif now - self.game_seen > GONE_AFTER:
            self.game_end('PPSSPP gone')

    def on_hint(self, words, age, now):
        """KNULLI ES 훅 귀띔 /tmp/hb_pspadhoc.game: start <초> <롬> · stop <초>. age = 적힌 뒤 지난 초(벽시계)."""
        if not words:
            return
        if words[0] == 'start':
            if age is None or not -5 <= age <= START_GRACE:
                log('old game hint ignored', ' '.join(words[:2]))
                return
            log('hook start', ' '.join(words[2:])[:60])
            self.game_start(None, now)
            self.tick(now, force=True)
        elif words[0] == 'stop':
            if self.G:
                self.game_end('hook stop')
                self.tick(now, force=True)

    def write_status(self, now):
        self.next_status = now + TICK_IDLE
        u, g = self.io.users(self.me)
        st = ('G' if self.G else '') + ('L' if self.L else '') + ('(listen)' if self.listening(now) else '')
        lines = [f'v2 me {self.me} leader {self.leader} why {self.why} state {st or "-"} users {u} guests {g}']
        for ip in sorted(self.peers, key=ipkey):
            p = self.peers[ip]
            a1 = f'{now - p.t1:.0f}s' if p.t1 is not None else '-'
            a2 = f'{now - p.t2:.0f}s' if p.t2 is not None else '-'
            kind = 'v2' if p.t2 is not None else 'v1'
            lines.append(f'  {ip} {kind} {p.flags} users {p.users} guests {p.guests} follow {p.follow} {p.nick} {p.tail} heard1 {a1} heard2 {a2}')
        self.io.status(lines)


# ───────────────────────────── 바깥(기기) ─────────────────────────────
class DeviceIO:
    def __init__(self):
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.ctl = None
        self._net = None
        if SIM_BUS:                                  # 맥 시험: 방송은 가짜 와이파이로, 알림은 127.0.0.1:PORT 로
            self.udp.bind(('127.0.0.1', 0))
            h, p = SIM_BUS.rsplit(':', 1)
            self.bus = (h, int(p))
            self.ctl = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.ctl.bind(('127.0.0.1', PORT))
            self.ctl.setblocking(False)
        else:
            self.udp.bind(('', PORT))
        self.udp.setblocking(False)
        try:
            wlan = open('/sys/class/net/wlan0/address').read().strip().lower()
        except OSError:
            wlan = ''
        self.nick = psp_nick(os.environ.get('HB_PSP_NICK') or socket.gethostname(), psp_mac(wlan))
        self._guests = -1

    def now(self):
        return time.monotonic()

    def net(self):
        if SIM_BUS:
            try:
                me = open(SIM_IP).read().split()[0]
            except (OSError, IndexError):
                me = None
            n = (me, 24, me.rsplit('.', 1)[0] + '.255') if me else None
            if n:
                self._sim(b'REG ' + me.encode())
        else:
            n = wlan_net()
        self._net = n
        return n

    def _sim(self, data):
        try:
            self.udp.sendto(data, self.bus)
        except OSError:
            pass

    def bcast(self, data):
        if not self._net:
            return
        if SIM_BUS:
            return self._sim(b'BC ' + self._net[0].encode() + b' ' + data)
        try:
            self.udp.sendto(data, (self._net[2], PORT))
        except OSError as e:
            log('send error', e)

    def send(self, ip, data):
        if not self._net:
            return
        if SIM_BUS:
            return self._sim(b'TO ' + self._net[0].encode() + b' ' + ip.encode() + b' ' + data)
        try:
            self.udp.sendto(data, (ip, PORT))
        except OSError:
            pass

    def ctl_reply(self, addr, data):
        try:
            (self.ctl or self.udp).sendto(data, addr)
        except OSError:
            pass

    def recv(self, sock):
        """(보낸 IP, 말, 127.0.0.1 에서 온 알림인가)"""
        data, (src, port) = sock.recvfrom(512)
        if SIM_BUS and sock is self.udp:
            p = data.split(b' ', 2)
            if len(p) < 3 or p[0] != b'FROM':
                return None
            return p[1].decode('ascii', 'replace'), p[2], None
        if src == '127.0.0.1' and data.startswith(b'HBPSPCTL '):
            return src, data, (src, port)
        return src, data, None

    def users(self, me):
        return count_users(me)

    def serving(self):
        return serving.is_set()

    def boot_offset(self):
        try:
            return time.clock_gettime(time.CLOCK_BOOTTIME) - time.clock_gettime(time.CLOCK_MONOTONIC)
        except (AttributeError, OSError):
            return None

    def pid_alive(self, pid):
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def game_alive(self, pid):
        """찾아 둔 PPSSPP 번호가 아직 PPSSPP 인가(번호를 다시 쓴 다른 프로그램이면 아님)"""
        try:
            with open(f'{PROC}/{pid}/comm') as f:
                return f.read().strip() in GAME_COMMS
        except OSError:
            return False

    def game_running(self):
        """PPSSPP 프로세스 번호(comm 기준 · 없으면 None)"""
        try:
            ds = os.listdir(PROC)
        except OSError:
            return None
        for d in ds:
            if d.isdigit():
                try:
                    with open(f'{PROC}/{d}/comm') as f:
                        if f.read().strip() in GAME_COMMS:
                            return int(d)
                except OSError:
                    pass
        return None

    def hint(self):
        """KNULLI 훅 귀띔이 바뀌었으면 (낱말들, 적힌 뒤 지난 초) · 아니면 None(파일이 없으면 None)"""
        try:
            st = os.stat(GAMEFILE)
        except OSError:
            return None
        sig = (st.st_ino, st.st_mtime_ns, st.st_size)
        if sig == getattr(self, '_hint_sig', None):
            return None
        self._hint_sig = sig
        try:
            with open(GAMEFILE) as f:
                words = f.read(512).split()
        except (OSError, UnicodeDecodeError):
            return None
        try:
            age = time.time() - float(words[1])
        except (IndexError, ValueError):
            age = None
        return words, age

    def set_hosts(self, ip):
        if set_hosts(ip):
            pass

    def guests(self, g):
        if g >= 1:
            if g != self._guests or int(time.monotonic()) % 3 == 0:
                try:
                    with open(GUESTS, 'w') as f:
                        f.write(f'{g}\n')
                except OSError:
                    pass
        elif self._guests != 0:
            try:
                os.remove(GUESTS)
            except OSError:
                pass
        if (hold_pause if PLAT == 'k' else hold_awake)(g >= 1):
            log('sleep hold', f'on (guests {g})' if g >= 1 else 'off')
        self._guests = g

    def notify(self, kept):
        """KNULLI: 게임을 끈 서버 기기에 손님이 남으면 3초 뒤(ES 가 메뉴로 돌아온 뒤) 메뉴 알림 한 줄 · 그사이 0 이 되면 안 띄움."""
        self._kept = kept
        if PLAT != 'k' or kept < 1:
            return

        def later():
            time.sleep(3)
            n = getattr(self, '_kept', 0)
            if n < 1:
                return
            import urllib.request
            text = f'PSP 같이하기 서버예요 · 다른 기기 {n}대 연결 중 — 끄지 말아 주세요'
            try:
                req = urllib.request.Request(ES_NOTIFY, data=text.encode('utf-8'), method='POST',
                                             headers={'Content-Type': 'text/plain; charset=utf-8'})
                with urllib.request.urlopen(req, timeout=1.0) as r:
                    r.read()
                log('menu notice', n)
            except Exception as e:
                log('menu notice error', repr(e))
        threading.Thread(target=later, daemon=True).start()

    def status(self, lines):
        try:
            with open(STATUS + '.new', 'w') as f:
                f.write('\n'.join(lines + user_lines()) + '\n')
            os.replace(STATUS + '.new', STATUS)
        except OSError:
            pass


class Stop(Exception):
    pass


def _stop(*_):
    raise Stop


def main():
    io = DeviceIO()
    node = Node(io)
    try:
        with open(VERFILE, 'w') as f:
            f.write(f'{HB_PSPADHOC_V2} {os.getpid()}\n')
    except OSError:
        pass
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    threading.Thread(target=serve, daemon=True).start()
    log('hb_pspadhoc v2', HB_PSPADHOC_V2, 'plat', PLAT, 'nick', io.nick, 'port', PORT, 'sim' if SIM_BUS else '')
    if PLAT == 'k' and hold_pause(False):              # 지난번 데몬이 죽으며 남긴 잠 막기(이 이름은 이 데몬만 씀) → 지우고 idlewatcher 다시 켬
        log('sleep hold', 'old file removed')
    socks = [io.udp] + ([io.ctl] if io.ctl else [])
    try:
        while True:
            try:
                h = io.hint()                          # KNULLI 훅 귀띔(파일 하나 stat · 1초 안에 한 번 이상)
                if h:
                    node.on_hint(h[0], h[1], io.now())
            except Stop:
                raise
            except Exception as e:
                log('hint error', repr(e))
            now = io.now()
            due = [node.next_full] + [x[0] for x in node.pending] + node.asks[:1] + [w[0] for w in node.waiters]
            timeout = max(0.02, min(1.0, min(due) - now))
            try:
                r, _, _ = select.select(socks, [], [], timeout)
            except OSError:
                r = []
            now = io.now()
            for s in r:
                for _ in range(64):                    # 쌓인 말을 모두 읽고 나서 고름(한 기기의 HBPSP2 · HBPSP1 사이에 고르지 않게)
                    try:
                        got = io.recv(s)
                    except (BlockingIOError, InterruptedError):
                        break
                    except OSError:
                        break
                    if not got:
                        continue
                    src, data, ctl_addr = got
                    try:
                        if ctl_addr or (s is io.ctl):
                            if data.startswith(b'HBPSPCTL '):
                                node.on_ctl(data.split(), ctl_addr or (src, PORT), now)
                        else:
                            node.on_udp(src, data, now)
                    except Stop:
                        raise
                    except Exception as e:           # 엉뚱한 말 하나로 서비스가 죽지 않게
                        log('message error', src, repr(e))
            try:
                node.tick(io.now())
            except Stop:
                raise
            except Exception as e:                   # 서비스는 절대 죽지 않게
                log('tick error', repr(e))
                node.next_full = io.now() + 1
    except Stop:
        pass
    finally:
        if node.me:
            node.G = node.L = False
            node.bcast(node.msg2('B'))
            time.sleep(0.2)
            node.bcast(node.msg2('B'))
        io._kept = 0
        (hold_pause if PLAT == 'k' else hold_awake)(False)
        try:
            os.remove(VERFILE)
        except OSError:
            pass
        log('stopped')


def ctl_main(cmd, pid, wait):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', 0))
    seq = f'{os.getpid()}.{random.randrange(1 << 30)}'
    msg = (f'HBPSPCTL start {pid if pid else "-"} {wait:g} {seq}' if cmd == 'start' else f'HBPSPCTL stop {seq}').encode()
    end = time.monotonic() + wait + 4.0                 # (부팅 뒤 처음 띄운 데몬은 파이썬이 늦게 뜰 수 있음 · 답이 오면 바로 끝)
    nxt = 0.0
    while time.monotonic() < end:
        if time.monotonic() >= nxt:
            try:
                s.sendto(msg, ('127.0.0.1', PORT))
            except OSError:
                pass
            nxt = time.monotonic() + 0.3                # 데몬이 막 뜨는 중이면 앞 것은 사라짐 → 다시(같은 번호라 두 번 켜지지 않음)
        r, _, _ = select.select([s], [], [], 0.1)
        if r:
            try:
                data = s.recv(512).split()
            except OSError:
                continue
            if len(data) >= 5 and data[:2] == [b'HBPSPCTL', b'ok'] and data[2] == seq.encode():
                ip = data[3].decode('ascii', 'replace')
                if is_ip(ip):
                    print(ip)
                return 0
    return 1


def arg(name, default=None):
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


if __name__ == '__main__':
    if '--status' in sys.argv:
        print(open(STATUS).read() if os.path.isfile(STATUS) else 'not running', end='')
        try:
            print(''.join(l + '\n' for l in open(HOSTS).read().splitlines() if l.rstrip().endswith(TAG)), end='')
        except OSError:
            pass
        sys.exit(0)
    if '--game-start' in sys.argv or '--game-stop' in sys.argv:
        try:
            pid = int(arg('--pid', '0'))
            wait = float(arg('--wait', '0'))
        except ValueError:
            sys.exit(2)
        sys.exit(ctl_main('start' if '--game-start' in sys.argv else 'stop', pid, wait))
    main()
