# SPDX-License-Identifier: GPL-3.0-or-later
# hb_direct.py - DS link play: connects the two devices directly over Wi-Fi (no router hop) for lower latency.
"""같이하기 직접 연결 (10/12) — 기기: /userdata/system/claude/hb_direct.py

왜: 집 공유기(일부 공유기)가 몇 초마다 0.05~0.1초씩 모든 와이파이 기기를 멈춰서, 같이하기가 느리고 끊겼다
    (10/12 01:4x 잼). 기기끼리 바로 이으면 마리오 카트 DS 초당 14 → 54장, 포켓몬 블랙·화이트 대전이 됐다.
어떻게: 같이하는 동안만 한 기기의 두 번째 무선(wlan1)을 숨은 작은 공유기(방장)로, 다른 기기의 wlan1 을 거기에 붙인다.
    집 와이파이(wlan0)는 그대로 둔다. 그다음 '상대 기기 집 주소(192.168.0.x)로 가는 길'만 wlan1 로 돌린다
    (ip route <상대 주소>/32 dev wlan1 src <내 집 주소>). 게임은 아무것도 바꾸지 않는다 — 주소가 그대로라서
    이미 이어진 같이하기도 끊기지 않고 길만 바뀐다(리눅스는 wlan1 로 온 '내 집 주소' ARP 에도 답함, arp_ignore=0).
    찾기(방송)는 공유기로 그대로 가고, 실제 게임 데이터만 직접 간다.
누가 방장: 게임이 정한다. DSperate 는 손님이 붙었을 때 방장 기기가, 레트로아크 넷플레이는 방을 연 기기가 'ap',
    손님은 'sta'. 이 파일은 그 말을 받아서 무선을 켜고, 0.5초마다 wlan1 로 '나 여기(집 주소)' 인사를 주고받아
    인사가 들리는 짝 기기만 길을 돌린다. 1.5초 동안 인사가 끊기면 길을 바로 원래대로(공유기) 되돌린다.
이웃이 못 들어오게(사용자 01:5x '암호 없이 OK, 우리 기기만'): 이 칩은 방장 모드에서 WPA2 정보가 깨져서 암호 없이 쓰는 대신
    ① 이름 숨김(ignore_broadcast_ssid) ② 방장은 짝 기기 무선 주소만 받음(macaddr_acl, 같은 와이파이에 보이는 짝 기기 칩 주소에서
    wlan1 주소를 만들어 더함) ③ 손님은 짝 기기 칩 주소의 방장에만 붙음(bssid_whitelist) ④ wlan1 로 들어오는 것은
    인사와 인사한 짝 기기 것만 받고 나머지는 버림(iptables HBD 사슬 — ssh 등 다 막힘).
명령:
  python3 hb_direct.py ap | sta   이 역할로 켬(이미 그 역할로 돌고 있으면 그대로, 다른 역할이면 바꿈)
  python3 hb_direct.py stop       다 끄고 원래대로(길·방화벽·wlan1). 돌고 있지 않아도 남은 것을 치움
  python3 hb_direct.py status
  python3 hb_direct.py watch-dsperate PID LOG   DSperate 기록을 보며 역할을 정함(hb_dsperate_run.sh 가 띄움)
  python3 hb_direct.py watch-retroarch          레트로아크 넷플레이 방장/손님을 보며 정함(ES 게임 시작 훅이 레트로아크 게임마다 띄움)
끄기: 기기 메뉴 → 게임 설정 → '같이하기' → '기기끼리 직접 연결' 을 끄면(knulli.conf global.hb_direct=0, 10/14)
    또는 /userdata/system/claude/hb_direct.off 파일이 있으면 아무것도 안 함(늘 집 와이파이로). 다음 같이하기부터 적용.
기록: /tmp/hb_direct/daemon.log (램)
"""
import os
import re
import signal
import socket
import subprocess
import sys
import time

D = '/tmp/hb_direct'
OFF = '/userdata/system/claude/hb_direct.off'
KCONF = '/userdata/system/knulli.conf'   # 메뉴 켜기/끄기(global.hb_direct) 한 줄만 읽음 — 와이파이 줄이 있어 아무것도 출력 안 함
MACS = '/userdata/system/claude/hb_direct_macs.txt'   # 짝 기기 wlan1 주소(한 줄에 하나, # 설명) — 없으면 보이는 짝 기기 칩에서 만든 것만
PIDF = f'{D}/daemon.pid'
ROLEF = f'{D}/role'
LOG = f'{D}/daemon.log'
SSID = 'hbd'
PORT = 7065
NET = '10.77.0'
FAMILY_OUI = ('68:8f:c9',)          # 짝 기기 무선 칩(8821cs) 주소 앞부분. wlan1 은 첫 바이트에 0x02 를 더한 6a:8f:c9:…
HELLO_EVERY = 0.5
PEER_GONE = 1.5


def turned_off():
    """메뉴(게임 설정 → 같이하기 → 기기끼리 직접 연결)에서 껐거나 hb_direct.off 가 있으면 True. 값이 없으면 켜짐(기본)."""
    if os.path.exists(OFF):
        return True
    val = ''
    try:
        with open(KCONF, encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.startswith('global.hb_direct='):
                    val = line.split('=', 1)[1].strip()
    except OSError:
        pass
    return val == '0'


LOG_LIMIT = 256 * 1024     # 10/21 기록 상한: 넘으면 .1 로 돌림(램)


def log(msg):
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) >= LOG_LIMIT:
            os.replace(LOG, LOG + '.1')
        with open(LOG, 'a') as f:
            f.write(time.strftime('%H:%M:%S ') + msg + '\n')
    except OSError:
        pass


def sh(cmd, check=False):
    r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if check and r.returncode:
        log(f'실패: {cmd} → {r.stderr.strip()[:200]}')
    return r


def wlan_mac(dev):
    try:
        return open(f'/sys/class/net/{dev}/address').read().strip().lower()
    except OSError:
        return ''


def la(mac):
    """칩 주소(wlan0) → wlan1 주소: 첫 바이트에 '내가 정한 주소' 비트(0x02)"""
    b = mac.split(':')
    return ':'.join([f'{int(b[0], 16) | 2:02x}'] + b[1:])


def home():
    """wlan0 의 (주소, 앞자리 길이, 주파수 MHz). 집 와이파이에 안 붙어 있으면 None"""
    a = sh('ip -4 -o addr show wlan0').stdout
    m = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', a)
    f = re.search(r'freq: (\d+)', sh('iw dev wlan0 link').stdout)
    if not m or not f:
        return None
    return m.group(1), int(m.group(2)), int(f.group(1))


def same_net(ip, base, plen):
    def n(x):
        p = [int(v) for v in x.split('.')]
        return (p[0] << 24) | (p[1] << 16) | (p[2] << 8) | p[3]
    mask = (0xffffffff << (32 - plen)) & 0xffffffff
    return (n(ip) & mask) == (n(base) & mask)


def family_wlan1_macs():
    """짝 기기 wlan1 주소: 적어 둔 것 + 집 와이파이에서 보이는 짝 기기 칩(68:8f:c9:…)에서 만든 것"""
    out = set()
    try:
        for line in open(MACS):
            line = line.split('#')[0].strip().lower()
            if re.fullmatch(r'([0-9a-f]{2}:){5}[0-9a-f]{2}', line):
                out.add(line)
    except OSError:
        pass
    for m in re.finditer(r'lladdr (([0-9a-f]{2}:){5}[0-9a-f]{2})', sh('ip neigh show dev wlan0').stdout):
        if m.group(1).startswith(FAMILY_OUI):
            out.add(la(m.group(1)))
    out.discard(la(wlan_mac('wlan0')))
    return out


def chan(freq):
    if 2412 <= freq <= 2472:
        return 'g', (freq - 2407) // 5
    if freq == 2484:
        return 'g', 14
    return 'a', (freq - 5000) // 5


# ── 방화벽: wlan1 로 들어오는 것은 인사와 인사한 짝 기기 것만 ──
def fw_up():
    open(f'{D}/fw_on', 'w').close()
    sh('iptables -N HBD')
    sh('iptables -F HBD')
    sh(f'iptables -A HBD -p udp --dport {PORT} -s {NET}.0/24 -j ACCEPT')
    sh('iptables -A HBD -j DROP')
    if sh('iptables -C INPUT -i wlan1 -j HBD').returncode:
        sh('iptables -I INPUT -i wlan1 -j HBD', check=True)


def fw_allow(ip, on):
    if on:
        if sh(f'iptables -C HBD -s {ip} -j ACCEPT').returncode:
            sh(f'iptables -I HBD -s {ip} -j ACCEPT')
    else:
        while not sh(f'iptables -D HBD -s {ip} -j ACCEPT').returncode:
            pass


def fw_down():
    while not sh('iptables -D INPUT -i wlan1 -j HBD').returncode:
        pass
    sh('iptables -F HBD')
    sh('iptables -X HBD')
    try:
        os.remove(f'{D}/fw_on')
    except OSError:
        pass


# ── 무선 ──
def procs(name, needle):
    out = []
    for d in os.listdir('/proc'):
        if not d.isdigit():
            continue
        try:
            argv = [a.decode(errors='replace') for a in open(f'/proc/{d}/cmdline', 'rb').read().split(b'\0') if a]
        except OSError:
            continue
        if argv and os.path.basename(argv[0]) == name and needle in argv[1:]:
            out.append(int(d))
    return out


def radio_down():
    for pf in ('hostapd.pid', 'wpa.pid'):
        try:
            os.kill(int(open(f'{D}/{pf}').read()), signal.SIGTERM)
        except (OSError, ValueError):
            pass
        try:
            os.remove(f'{D}/{pf}')
        except OSError:
            pass
    # pid 파일이 없어진 경우만: 실행 파일 이름과 우리 설정 파일 인자로 정확히 찾음(pkill -f 는 다른 셸 명령 줄까지 맞아서 안 씀)
    for p in procs('hostapd', f'{D}/hostapd.conf') + procs('wpa_supplicant', f'{D}/wpa.conf'):
        try:
            os.kill(p, signal.SIGTERM)
        except OSError:
            pass
    time.sleep(0.5)
    sh('ip addr flush dev wlan1')
    sh('ip link set wlan1 down')


def ap_up(freq):
    mode, ch = chan(freq)
    acl = f'{D}/accept_mac'
    with open(acl, 'w') as f:
        f.write(''.join(m + '\n' for m in sorted(family_wlan1_macs())))
    conf = [f'interface=wlan1', 'driver=nl80211', f'ctrl_interface={D}/hapd_ctrl', f'ssid={SSID}', 'ignore_broadcast_ssid=1',
            f'hw_mode={mode}', f'channel={ch}', 'ieee80211n=1', 'wmm_enabled=1', 'auth_algs=1',
            'macaddr_acl=1', f'accept_mac_file={acl}']
    if mode == 'a':
        conf.append('ht_capab=[SHORT-GI-20]')
    open(f'{D}/hostapd.conf', 'w').write('\n'.join(conf) + '\n')
    sh('ip link set wlan1 up', check=True)
    r = sh(f'hostapd -B -P {D}/hostapd.pid -f {D}/hostapd.log {D}/hostapd.conf')
    if r.returncode:
        log('방장 켜기 실패: ' + (open(f'{D}/hostapd.log').read()[-300:] if os.path.exists(f'{D}/hostapd.log') else r.stderr[:300]))
        return False
    time.sleep(1.5)
    sh(f'ip addr replace {NET}.1/24 dev wlan1', check=True)
    log(f'방장 켬: 채널 {ch} ({freq}MHz), 받는 주소 {len(open(acl).read().split())}개')
    return True


def ap_acl_refresh(known):
    for m in family_wlan1_macs() - known:
        sh(f'hostapd_cli -p {D}/hapd_ctrl accept_acl ADD_MAC {m}')
        known.add(m)
        log(f'방장 받는 주소 더함 {m}')


def my_sta_ip():
    b = int(wlan_mac('wlan0').split(':')[-1], 16)
    return f'{NET}.{2 + b % 250}'


def sta_up(freq):
    conf = (f'ctrl_interface={D}/wpa_ctrl\n'
            'network={\n'
            f'\tssid="{SSID}"\n\tscan_ssid=1\n\tkey_mgmt=NONE\n\tscan_freq={freq}\n\tfreq_list={freq}\n'
            '\tbssid_whitelist=' + ' '.join(f'{la(o + ":00:00:00")}/ff:ff:ff:00:00:00' for o in FAMILY_OUI) + '\n}\n')
    open(f'{D}/wpa.conf', 'w').write(conf)
    sh('ip link set wlan1 up', check=True)
    r = sh(f'wpa_supplicant -B -D nl80211 -i wlan1 -c {D}/wpa.conf -P {D}/wpa.pid -f {D}/wpa.log')
    if r.returncode:
        log('손님 켜기 실패: ' + r.stderr[:300])
        return False
    log(f'손님 켬: 짝 방장 찾는 중 ({freq}MHz)')
    return True


def sta_linked():
    m = re.search(r'Connected to (([0-9a-f]{2}:){5}[0-9a-f]{2})', sh('iw dev wlan1 link').stdout)
    return m.group(1) if m else None


# ── 길 ──
def route(peer, mine, on):
    if on:
        sh(f'ip route replace {peer}/32 dev wlan1 src {mine}', check=True)
    else:
        sh(f'ip route del {peer}/32 dev wlan1')


def clean_all():
    for r in re.findall(r'^(\d+\.\d+\.\d+\.\d+)\s', sh('ip route show dev wlan1').stdout, re.M):
        sh(f'ip route del {r}/32 dev wlan1')
    fw_down()
    radio_down()


# ── 데몬 ──
def daemon(role):
    os.makedirs(D, exist_ok=True)
    open(PIDF, 'w').write(str(os.getpid()))
    open(ROLEF, 'w').write(role)
    stop = {'v': False}
    signal.signal(signal.SIGTERM, lambda *a: stop.update(v=True))
    signal.signal(signal.SIGINT, lambda *a: stop.update(v=True))
    log(f'시작: {role}')
    peers = {}            # 상대 집 주소 → [직접 주소, 마지막 인사 시각, 이름]
    up_freq = None
    known_acl = set()
    sock = None
    last_hello = 0.0
    myip10 = f'{NET}.1' if role == 'ap' else my_sta_ip()
    name = socket.gethostname()
    next_house = 0.0
    linked = role == 'ap'
    mine = plen = None
    try:
        fw_up()
        while not stop['v']:
            now = time.time()
            if now >= next_house:                      # 1초마다: 집 와이파이·채널·붙음·받는 주소 (바깥 명령은 여기서만)
                next_house = now + 1.0
                h = home()
                if not h:                              # 집 와이파이가 없으면 직접 연결도 쉼(찾기가 공유기로 가니까)
                    if up_freq:
                        log('집 와이파이 없음 → 쉼')
                        for p in list(peers):
                            route(p, '', False); fw_allow(p, False)
                        peers.clear(); radio_down(); up_freq = None; linked = role == 'ap'
                        if sock:
                            sock.close(); sock = None
                    time.sleep(1)
                    continue
                mine, plen, freq = h
                if up_freq != freq:                    # 처음, 또는 공유기가 채널을 바꿈 → 같은 채널로 다시
                    if up_freq:
                        log(f'채널 바뀜 {up_freq} → {freq}MHz → 다시 켬')
                    for p in list(peers):
                        route(p, mine, False); fw_allow(p, False)
                    peers.clear()
                    if sock:
                        sock.close(); sock = None
                    radio_down()
                    linked = role == 'ap'
                    if not (ap_up(freq) if role == 'ap' else sta_up(freq)):
                        next_house = time.time() + 5
                        continue
                    up_freq = freq
                    known_acl = set(open(f'{D}/accept_mac').read().split()) if role == 'ap' else set()
                if role == 'sta':
                    b = sta_linked()
                    if not b:
                        if linked or peers:
                            log('방장과 끊김 → 길 되돌림')
                        for p in list(peers):
                            route(p, mine, False); fw_allow(p, False)
                        peers.clear()
                        linked = False
                    else:
                        if not linked:
                            sh(f'ip addr replace {myip10}/24 dev wlan1', check=True)
                            log(f'방장에 붙음 {b} → {myip10}')
                        linked = True
                else:
                    ap_acl_refresh(known_acl)
            if not up_freq or not linked:
                time.sleep(0.2)
                continue
            if sock is None:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.setsockopt(socket.SOL_SOCKET, 25, b'wlan1\0')     # SO_BINDTODEVICE
                    sock.bind(('', PORT))
                    sock.settimeout(0.1)
                except OSError as e:
                    log(f'인사 소켓 실패: {e}')
                    sock = None
                    time.sleep(1)
                    continue
            now = time.time()
            if now - last_hello >= HELLO_EVERY:
                try:
                    sock.sendto(f'HBD1 {mine} {role} {name}'.encode(), (f'{NET}.255', PORT))
                except OSError:
                    pass
                last_hello = now
            try:
                data, (src, _) = sock.recvfrom(256)
                p = data.decode(errors='replace').split()
                if len(p) >= 4 and p[0] == 'HBD1' and src != myip10 and src.startswith(NET + '.'):
                    peer = p[1]
                    if re.fullmatch(r'\d+\.\d+\.\d+\.\d+', peer) and peer != mine and same_net(peer, mine, plen):
                        if peer not in peers:
                            fw_allow(peer, True)
                            route(peer, mine, True)
                            log(f'직접 연결: {p[3]} ({peer}, {src}) → 이 기기로 가는 길을 직접으로')
                        peers[peer] = [src, time.time(), p[3]]
            except socket.timeout:
                pass
            except OSError:
                pass
            for peer, (src, seen, nm) in list(peers.items()):
                if time.time() - seen > PEER_GONE:
                    route(peer, mine, False)
                    fw_allow(peer, False)
                    del peers[peer]
                    log(f'인사 끊김: {nm} ({peer}) → 공유기 길로 되돌림')
    except Exception as e:                                   # 무엇이 잘못돼도 길은 꼭 되돌림
        log(f'오류: {e!r}')
    finally:
        try:
            if sock:
                sock.close()
        except OSError:
            pass
        clean_all()
        for f in (PIDF, ROLEF):
            try:
                os.remove(f)
            except OSError:
                pass
        log('끝: 원래대로')


def running():
    try:
        pid = int(open(PIDF).read())
        os.kill(pid, 0)
        return pid, open(ROLEF).read().strip()
    except (OSError, ValueError):
        return None, None


def wlan1_up():
    try:
        return int(open('/sys/class/net/wlan1/flags').read(), 16) & 1 == 1
    except (OSError, ValueError):
        return False


def stop_daemon():
    pid, _ = running()
    if not pid and not os.path.exists(f'{D}/fw_on') and not wlan1_up():
        return
    if pid:
        os.kill(pid, signal.SIGTERM)
        for _ in range(40):
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except OSError:
                break
        else:
            os.kill(pid, signal.SIGKILL)
    clean_all()


def start(role):
    if turned_off():
        return
    pid, cur = running()
    if pid and cur == role:
        return
    if pid:
        stop_daemon()
    os.makedirs(D, exist_ok=True)
    subprocess.Popen([sys.executable, os.path.abspath(__file__), '_daemon', role], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=open(LOG, 'a'), start_new_session=True)


def ra_port():
    try:
        m = re.search(r'(?m)^netplay_ip_port\s*=\s*"?(\d+)', open('/userdata/system/configs/retroarch/retroarchcustom.cfg').read())
        return int(m.group(1)) if m else 55435
    except OSError:
        return 55435


def ra_role(pid, port):
    """netplay_sram_flush.py 와 같은 방법: 넷플레이 포트에서 듣거나 받았으면 'host', 그 포트로 이어 갔으면 'guest'"""
    inodes = set()
    try:
        for fd in os.listdir(f'/proc/{pid}/fd'):
            try:
                link = os.readlink(f'/proc/{pid}/fd/{fd}')
            except OSError:
                continue
            if link.startswith('socket:['):
                inodes.add(link[8:-1])
    except OSError:
        return None
    host = guest = False
    for table in ('/proc/net/tcp', '/proc/net/tcp6'):
        try:
            for line in open(table).read().splitlines()[1:]:
                f = line.split()
                if f[9] not in inodes:
                    continue
                local, remote, st = int(f[1].rsplit(':', 1)[1], 16), int(f[2].rsplit(':', 1)[1], 16), f[3]
                if local == port and st in ('0A', '01'):
                    host = True
                elif remote == port and st == '01':
                    guest = True
        except (OSError, ValueError, IndexError):
            pass
    return 'host' if host else 'guest' if guest else None


SCREEN_FILE = '/tmp/hb_dual_screen'   # 10/20 20:5x: 두 대 코어(원더스완 · GBA Dual)가 30장마다 읽는 화면(1P/2P)


def set_screen(v):
    """방장이면 1P · 손님이면 2P 를 두 대 코어에 알림(None = 지움 → 코어 옵션대로). 한 대짜리 코어는 이 파일을 안 봄"""
    try:
        if v is None:
            os.remove(SCREEN_FILE)
        else:
            tmp = SCREEN_FILE + '.tmp'
            with open(tmp, 'w') as f:
                f.write(v + '\n')
            os.replace(tmp, SCREEN_FILE)
    except OSError:
        pass


def ownsave_server(pid, port, system, rom):
    """실제 방장 소켓을 확인하는 세이브 받는 곳. 무선 설정과는 별개."""
    import hb_ownsave as own
    return own.Server(pid, port, system, rom).start()


def ownsave_guest(pid):
    import hb_ownsave as own
    own.atomic(own.ROOT / 'guest', (str(pid) + '\n').encode())


def watch_ownsave(pid, port, system, rom):
    """VM 시험도 같은 받는 코드를 쓴다. 무선과 설정 파일은 열지 않음."""
    server = None
    try:
        while os.path.exists(f'/proc/{pid}'):
            role = ra_role(pid, port)
            if role == 'host' and server is None:
                server = ownsave_server(pid, port, system, rom)
            if role == 'guest':
                ownsave_guest(pid)
            time.sleep(.1)
    finally:
        if server:
            server.close()


def watch_retroarch(system=None, rom=None, core=None):
    """레트로아크 게임마다(ES 훅이 띄움): 넷플레이 방을 열면 방장(ap), 남의 방에 들어가면 손님(sta), 레트로아크가 끝나면 끔.
    10/20 20:5x: 직접 연결을 꺼 두었어도 역할은 계속 봐서 /tmp/hb_dual_screen 에 1P/2P 를 씀 — 혼자로 켠 뒤 게임 안 메뉴로
    남의 방에 들어간 손님도 두 대 코어가 2P 화면으로 바뀌게(체크리스트 O). 끝나거나 끌려 나가면(SIGTERM) 파일을 지움."""
    off = turned_off()
    set_screen(None)
    signal.signal(signal.SIGTERM, lambda *_: (set_screen(None), sys.exit(0)))
    pid = None
    for _ in range(40):
        r = sh('pidof retroarch').stdout.split()
        if r:
            pid = int(r[0]); break
        time.sleep(1)
    if not pid:
        return
    port = ra_port(); role = None; gone_at = None; scr = None
    ownserver = None
    owncore = core in ('mgba_dual', 'mednafen_wswan_dual', 'mednafen_ngp_dual', 'genesisplusgx_gg_dual')   # 10/22 6판: 네오지오 · 게임기어
    while os.path.exists(f'/proc/{pid}'):
        r = ra_role(pid, port)
        if owncore:
            try:
                if r == 'host' and ownserver is None:
                    ownserver = ownsave_server(pid, port, system, rom)
                if r == 'guest':
                    ownsave_guest(pid)
                if r != 'host' and ownserver:
                    ownserver.close(); ownserver = None
            except (OSError, ValueError):
                pass
        s = {'host': '1P', 'guest': '2P'}.get(r)
        if s and s != scr:
            scr = s; set_screen(s)
        if not off:
            want = {'host': 'ap', 'guest': 'sta'}.get(r)
            if want and want != role:
                role = want; gone_at = None; start(want)
            elif not want and role:
                gone_at = gone_at or time.time()
                if time.time() - gone_at > 15:          # 넷플레이를 끝낸 뒤 15초 → 끔
                    role = None; gone_at = None; stop_daemon()
        time.sleep(1)
    if ownserver:
        ownserver.close()
    set_screen(None)
    if not off:
        stop_daemon()


def watch_dsperate(pid, path):
    """DSperate 기록으로 역할 정하기: 'a guest joined' → 방장(ap), 'the last guest left' → 15초 뒤 끔,
    'lan: lanfix' 줄 뒤 6초 안에 'hosting' 줄이 없으면 손님(sta). DSperate 가 끝나면 끔."""
    if turned_off():
        return
    pos = 0; role = None; lan_at = None; hosting = False; left_at = None
    while True:
        try:
            os.kill(pid, 0)
        except OSError:
            break
        lines = []
        try:
            with open(path, 'rb') as f:                 # 바이트로 읽고 끝난 줄까지만(쓰는 중인 줄은 다음 번에)
                f.seek(pos)
                data = f.read()
            cut = data.rfind(b'\n') + 1
            pos += cut
            lines = data[:cut].decode(errors='replace').splitlines()
        except OSError:
            pass
        for line in lines:
            if line.startswith('lan: lanfix') and lan_at is None:
                lan_at = time.time()
            elif 'lan: hosting, nobody has joined' in line:
                hosting = True
            elif 'lan: a guest joined' in line:
                left_at = None
                if role != 'ap':
                    role = 'ap'; start('ap')
            elif 'lan: the last guest left' in line:
                left_at = time.time()
            elif '(was hosting alone)' in line:            # hbfam3: 혼자 방장이다가 다른 방장에 손님으로 붙음
                left_at = None
                if role != 'sta':
                    role = 'sta'; start('sta')
            elif 'lan: the host left' in line:              # hbfam3: 방장이 나가서 혼자 방장으로 돌아감
                left_at = None; role = None; hosting = True; stop_daemon()
        if lan_at and not hosting and role is None and time.time() - lan_at > 6:
            role = 'sta'; start('sta')
        if left_at and time.time() - left_at > 15:
            left_at = None; role = None; stop_daemon()
        time.sleep(0.5)
    stop_daemon()


if __name__ == '__main__':
    a = sys.argv[1:] or ['status']
    if a[0] in ('ap', 'sta'):
        start(a[0])
    elif a[0] == 'stop':
        stop_daemon()
    elif a[0] == '_daemon':
        daemon(a[1])
    elif a[0] == 'watch-dsperate':
        watch_dsperate(int(a[1]), a[2])
    elif a[0] == 'watch-retroarch':
        watch_retroarch(*(a[1:4] if len(a) >= 4 else []))
    elif a[0] == 'ownsave-watch':
        watch_ownsave(int(a[1]), int(a[2]), a[3], a[4])
    else:
        pid, role = running()
        print('끔(메뉴 또는 hb_direct.off)' if turned_off() else '켜짐' if pid else '쉼', role or '', 'pid', pid or '-')
        print(sh('iw dev wlan1 info').stdout.strip())
        print(sh('ip route show dev wlan1').stdout.strip())
        print(sh('iptables -S HBD').stdout.strip())
