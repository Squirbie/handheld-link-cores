#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_pspadhoc.py - PSP ad-hoc multiplayer: a local relay server plus automatic host selection.
"""PSP 통신(애드혹) 집 안 서버 + 방장 자동 고르기 (기기: /userdata/system/claude/hb_pspadhoc.py)
왜: PPSSPP 기본 통신 서버 socom.cc(인터넷)는 같은 공유기 뒤 기기 둘이 같은 바깥 IP 라서 로비에서 서로 안 보임
    (10/8 철권 5 로 확인: 둘 다 접속은 되는데 0/15). 집 안 서버로 바꾸면 로비·대전까지 됨(같은 날 확인).
하는 일: 모든 기기에서 늘 켜져서
  1) PPSSPP 통신 서버(PRO Adhoc, TCP 27312) 노릇을 하고
  2) 같은 와이파이에서 이 서버가 도는 기기 중 IP 가 가장 작은 곳을 'hbpsp' 라는 이름으로 /etc/hosts 에 적는다.
  PPSSPP 는 knulli.conf 의 psp.ppsspp.Network.proAdhocServer=hbpsp 로 그 이름에 붙으니, 어느 기기들이 켜져 있든 모두 같은 서버로 모인다.
  찾기(10/13 14:0x 바꿈): 15초마다 'HBPSP1 내주소' 방송 한 번(UDP 27312 — TCP 서버와 같은 번호, 다른 길) + 처음 듣는 기기에는 바로 답.
    50초 동안 못 들은 기기는 꺼진 것으로 본다. 예전엔 같은 /24 의 253곳에 TCP 로 두드려 찾았는데, 없는 주소마다 '이 주소 누구?'(ARP)
    방송이 1초 간격 3번씩 나가(기기마다 16초마다 약 760개) 공유기가 그때마다 모든 기기를 0.05~0.2초 멈췄다
    (10/13 13:49~13:52 두 기기 0.02초 핑: 켬 1분 50ms 넘는 멈춤 21묶음 · 끔 0 — 공유기 탓으로 알았던 '몇 초마다 멈춤'의 큰 몫).
서버 동작은 PPSSPP 1.19.3 Core/HLE/proAdhocServer.cpp 를 그대로 옮김(로그인·그룹 접속/해제·방 찾기·채팅·15초 무응답 끊기).
다른 점 하나: 같은 IP 에서 다시 로그인하면 옛 연결을 끊고 새 것을 받음(원본은 새 연결을 거절해서 최대 15초 못 붙음).
  로그인 패킷을 보낸 연결만 그렇게 하므로, 방장 찾기용으로 잠깐 붙었다 끊는 연결은 아무도 안 끊는다. 지역판 묶음(crosslinks)은 안 옮김(두 기기는 같은 롬).
  python3 hb_pspadhoc.py           서비스로 실행
  python3 hb_pspadhoc.py --status  지금 방장·접속자 보기"""
import fcntl
import os
import select
import socket
import struct
import sys
import threading
import time

PORT = int(os.environ.get('HB_PSP_PORT', 27312))   # 시험할 때만 바꿈
USER_TIMEOUT = 15          # 초, PPSSPP 는 2초마다 핑을 보냄
SCAN_EVERY = 15            # 초, '나 여기' 방송 간격
PEER_EXPIRE = 3 * SCAN_EVERY + 5   # 초, 이만큼 방송을 못 들으면 그 기기는 꺼진 것으로
LEADER_EVERY = 3           # 초, 방장 다시 고르기(바깥으로 아무것도 안 보냄)
ANNOUNCE = b'HBPSP1'
HOSTS = os.environ.get('HB_PSP_HOSTS', '/etc/hosts')
NAME = 'hbpsp'
TAG = '# hanbang-psp'
STATUS = os.environ.get('HB_PSP_STATUS', '/tmp/hb_pspadhoc.status')

OP_PING, OP_LOGIN, OP_CONNECT, OP_DISCONNECT, OP_SCAN, OP_SCAN_COMPLETE, OP_CONNECT_BSSID, OP_CHAT = range(8)
LOGIN_LEN = 1 + 6 + 128 + 9    # opcode, MAC, 닉네임, 게임 번호
CONNECT_LEN = 1 + 8            # opcode, 그룹 이름
CHAT_LEN = 1 + 64

lock = threading.Lock()
users = []                     # User, 들어온 순서
groups = {}                    # (게임 번호, 그룹 이름) -> {'name': 8바이트, 'members': [새 사람이 앞]}
state = {'leader': None, 'me': None, 'found': [], 'net': None}   # net: (내 주소, 앞자리 길이, 방송 주소)
peers = {}                     # 다른 기기 주소 -> 마지막으로 '나 여기'를 들은 시각
serving = threading.Event()    # 27312 를 열었을 때만 알림(서버 노릇을 못 하는 기기가 방장으로 뽑히지 않게)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


class User:
    def __init__(self, sock, ip):
        self.sock, self.ip = sock, ip              # ip: 4바이트(네트워크 순서), 상대에게 그대로 알려 줌
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
        bssid = g['members'][-1].mac                # 방을 처음 만든 사람
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
    for (game, _), g in reversed(list(groups.items())):   # 원본처럼 새 방부터
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
        if u.game is None:                          # 로그인 기다리는 중
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
            srv.bind(('0.0.0.0', PORT))
            srv.listen(64)
            break
        except OSError as e:                        # 예: PPSSPP 내장 서버가 이 포트를 쓰는 중
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
                    c.settimeout(2)                 # 보낼 때만 막힘 방지; 받기는 select 로
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


def ipkey(a):
    return tuple(int(x) for x in a.split('.'))


def _if_addr(sock, name, req):
    return fcntl.ioctl(sock.fileno(), req, struct.pack('256s', name.encode()[:15]))[20:24]


def wlan_net():
    """(내 주소, 앞자리 길이, 방송 주소) — 바깥(기본 길)으로 나가는 주소. 와이파이에 안 붙어 있으면 None.
    바깥 프로그램을 안 띄움(3초마다 부르므로): 주소는 '연결만 해 보기'(패킷 안 나감), 길이·방송 주소는 ioctl."""
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


def say_here(sock, dest):
    net = state['net']
    if net and serving.is_set():
        try:
            sock.sendto(ANNOUNCE + b' ' + net[0].encode(), (dest, PORT))
        except OSError:
            pass


def announce_loop():
    """같은 와이파이의 다른 기기 찾기: SCAN_EVERY 마다 '나 여기' 방송 한 번 + 처음 듣는 기기에는 바로 답(새로 켠 기기가 15초 안 기다리게)."""
    sock, next_send = None, 0.0
    while True:
        try:
            if sock is None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.bind(('', PORT))
                sock.settimeout(1.0)
            net = state['net']
            if time.time() >= next_send:
                if net and serving.is_set():
                    say_here(sock, net[2])
                    next_send = time.time() + SCAN_EVERY
                else:
                    next_send = time.time() + 1         # 와이파이·서버 준비 전 → 곧 다시
            try:
                data, (src, _) = sock.recvfrom(64)
            except socket.timeout:
                continue
            p = data.split()
            if len(p) != 2 or p[0] != ANNOUNCE or p[1] != src.encode() or not net or src == net[0] or not same_net(src, net):
                continue
            with lock:
                new = time.time() - peers.get(src, 0) > PEER_EXPIRE
                peers[src] = time.time()
            if new:
                log('found', src)
                say_here(sock, src)
        except OSError as e:
            log('announce error', e)
            if sock:
                sock.close()
            sock = None
            time.sleep(5)


def set_hosts(ip):
    try:
        cur = open(HOSTS).read()
    except OSError:
        cur = ''
    keep = [l for l in cur.splitlines() if not l.rstrip().endswith(TAG)]
    want = '\n'.join(keep + [f'{ip}\t{NAME} {TAG}']) + '\n'
    if want != cur:
        tmp = HOSTS + '.hbpsp'
        with open(tmp, 'w') as f:
            f.write(want)
        os.replace(tmp, HOSTS)
        log('hbpsp ->', ip)


def leader_loop():
    while True:
        try:
            net = wlan_net()
            state['net'] = net
            if net:
                me, now = net[0], time.time()
                with lock:
                    for ip in [ip for ip, t in peers.items() if now - t > PEER_EXPIRE or not same_net(ip, net)]:
                        del peers[ip]
                        log('gone', ip)
                    found = sorted(peers, key=ipkey)
                leader = min(found + [me], key=ipkey)
                set_hosts(leader)
                state.update(me=me, found=found, leader=leader)
            with lock:
                lines = [f'me {state["me"]} leader {state["leader"]} other_servers {" ".join(state["found"]) or "-"}',
                         f'users {sum(1 for u in users if u.game is not None)} groups {len(groups)}']
                lines += ['  ' + u.label() + (' in ' + u.group[1].decode('ascii', 'replace') if u.group else '') for u in users if u.game is not None]
            with open(STATUS, 'w') as f:
                f.write('\n'.join(lines) + '\n')
        except Exception as e:                      # 서비스는 절대 죽지 않게
            log('leader loop error', e)
        time.sleep(LEADER_EVERY)


if '--status' in sys.argv:
    print(open(STATUS).read() if os.path.isfile(STATUS) else 'not running')
    print(''.join(l + '\n' for l in open(HOSTS).read().splitlines() if l.rstrip().endswith(TAG)), end='')
    sys.exit(0)
threading.Thread(target=leader_loop, daemon=True).start()
threading.Thread(target=announce_loop, daemon=True).start()
serve()
