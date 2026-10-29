#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_wifimem.py - Remembers several Wi-Fi networks and reconnects on its own, like a phone.
# (2026-10-13) 와이파이 여러 개 기억 — 스마트폰처럼, 한 번 연결한 와이파이는 다음에 보이면 저절로 붙게
# 기기: /userdata/system/claude/hb_wifimem.py · 서비스: /userdata/system/services/hb_wifimem
# 왜: KNULLI 메뉴에서 와이파이에 연결하면 knulli.conf 의 wifi.ssid·wifi.key 한 쌍을 덮어써서 그 전 와이파이를 잊는다.
#     connman 의 기억(/var/lib/connman)은 램이라 재부팅하면 없어진다 → 집 → 다른 곳 → 집으로 오면 비밀번호를 다시 넣어야 했음.
# 하는 일(5초마다 knulli.conf 가 바뀌었는지만 봄):
#   1) 지금 와이파이(이름·비번)를 목록 맨 앞에 둔다. 같은 이름이면 비번만 새것으로. 8개까지(오래된 것부터 빠짐).
#   2) 목록에서 지금 것을 뺀 나머지를 와이파이마다 connman 설정 파일 하나씩(/var/lib/connman/hb_wifimem_<번호>.config, 램)으로
#      알려 준다 → connman 이 그 와이파이가 보이면 저절로 붙는다(KNULLI 가 wifi·wifi2·wifi3 칸으로 쓰는 것과 같은 꼴).
#   knulli.conf 에는 아무것도 안 쓴다(읽기만, 값은 KNULLI 와 같은 knulli-settings-get 으로).
# 조심(10/13 2번 기기 시험에서 배움): connman 은 설정 파일이 바뀌거나 지워지면 그 파일로 붙어 있던 연결을 끊는다.
#   그래서 켜져 있는 동안에는 '지금 와이파이'의 파일을 절대 지우거나 고치지 않는다(지금 것과 겹쳐도 그대로 둠).
#   겹친 파일은 다음 부팅 때(파일이 램이라 다 없어진 뒤) 지금 것을 빼고 새로 만들면서 저절로 정리된다.
# 비밀: 목록(/userdata/system/hb_wifi/known.json, 600)과 설정 파일에 와이파이 비밀번호가 들어 있음 → 맥으로 가져오지 않음.
#       기록(/tmp/hb_wifimem.log)에는 이름·비번을 쓰지 않고 개수만 쓴다.
# 끄기: knulli.conf system.services 에서 hb_wifimem 을 빼고 재부팅. 목록까지 지우려면 /userdata/system/hb_wifi 를 지움.
# 더함(10/13 14:2x) 붙어 있는 동안 주변 검색 끄기 — 같이하기 렉 줄이기: connman 은 와이파이에 붙을 때마다 wpa_supplicant 에
#   bgscan "simple:30:-65:300" 을 걸어서, 붙어 있는 동안에도 5분마다(신호가 -65dBm 보다 약하면 30초마다) 모든 채널을 훑는다.
#   그동안 이 기기 통신이 몇 초 끊기거나 0.4초씩 밀린다(10/13 13:50 2번 기기 핑 3.3초 끊김 · 14:10 시험 10초 동안 0.4초씩 밀림).
#   → 붙은 네트워크의 bgscan 을 'none'(없는 방식 이름 → wpa_supplicant 가 백그라운드 검색 없이 지냄)으로 바꾸고 Reattach(같은 공유기에
#   다시 붙기) 한 번으로 적용. 1번 기기 시험(14:16): 다시 붙는 5초 동안 핑 1500번 잃음 0 · connman 그대로 online · 같은 네트워크 그대로.
#   끊겼을 때 다시 찾는 검색(connman)과 메뉴의 와이파이 찾기는 그대로라 저장한 와이파이에 저절로 붙는 것은 안 바뀜.
#   connman 이 새로 붙을 때마다 다시 걸므로 5초마다 보고 다시 끔(10분에 3번까지 — 혹시 계속 다시 붙는 일이 생기면 그만).
#   끄기: /userdata/system/claude/hb_bgscan.on 파일이 있으면 이 일은 안 함(KNULLI 기본대로 5분 검색).
# 고침(10/26 사용자 M218 '핫스팟을 골랐는데 주소가 그대로'): 메뉴에서 다른 와이파이를 고르면 그 순간 옛 망들을 저절로 붙을 곳으로
#   다시 적고 35초 뒤 붙은 망에 Reattach 까지 해서, 신호가 센 옛 망(집)에 그대로 남았음 → 메뉴에서 고른 망이 바뀌면
#   ① 옛 망 설정 파일을 잠깐 치우고(connman 이 옛 망에서 떨어져 새 망으로) 새 망에 connmanctl connect ② 새 망에 붙거나 60초가 지나면
#   옛 망 파일을 다시 적음(다음에 그곳에 가면 저절로) ③ 그동안 검색 끄기(Reattach)도 쉼. 비밀번호 없는 와이파이는 기억하지 않음
#.
# 바꿈(10/26 03:4x 사용자 M220 '이 기능 넣지 말까? 너무 안 좋아 보여'): **비밀번호 기억 · 저절로 붙기는 뺌**(MEMORY=False) —
#   메뉴 비번 칸은 KNULLI 가 마지막 비번 하나만 보여 주는데 숨긴 목록 때문에 화면과 실제가 어긋나고 고른 망으로 안 옮겨 갔음.
#   켜질 때 · 설정이 바뀔 때 목록 파일(hb_wifi/known.json)을 지우고, 우리 connman 파일은 지금 붙은 망 것만 남김(지우면 끊김 — 다음 부팅에 사라짐).
#   남긴 것: 붙어 있는 동안 배경 검색 끄기(bgscan none + Reattach — 같이하기 렉 줄이기, 10/13). 비밀번호는 안 다룸.
import glob
import hashlib
import json
import re
import os
import subprocess
import sys
import time

CONF = os.environ.get('HB_WIFIMEM_CONF', '/userdata/system/knulli.conf')
LIST = os.environ.get('HB_WIFIMEM_LIST', '/userdata/system/hb_wifi/known.json')
OUTDIR = os.environ.get('HB_WIFIMEM_OUTDIR', '/var/lib/connman')
LOG = os.environ.get('HB_WIFIMEM_LOG', '/tmp/hb_wifimem.log')
GET = '/usr/bin/knulli-settings-get'
PREFIX = 'hb_wifimem_'
MAX = 8
BG_OFF = 'none'                    # bgscan 값: 없는 방식 이름 → 백그라운드 검색 없음(빈 값은 D-Bus 가 거절)
BG_KEEP = '/userdata/system/claude/hb_bgscan.on'
MEMORY = False                     # (10/26 M220) 비밀번호 기억 · 저절로 붙기 끔 — 배경 검색 끄기만 함
W = 'fi.w1.wpa_supplicant1'


def log(msg):
    try:
        with open(LOG, 'a') as f:
            f.write(time.strftime('%m-%d %H:%M:%S ') + msg + '\n')
    except OSError:
        pass


def conf_get(key):
    """knulli.conf 값(bytes) 또는 None — S08connman 과 같은 도구로 읽음(없으면 같은 꼴로 직접)."""
    if os.path.exists(GET):
        r = subprocess.run([GET, '-f', CONF, key], capture_output=True)
        if r.returncode != 0:
            return None
        return r.stdout.rstrip(b'\n')
    try:
        with open(CONF, 'rb') as f:
            for raw in f:
                line = raw.rstrip(b'\r\n')
                if line.startswith(key.encode() + b'='):
                    return line[len(key) + 1:]
    except OSError:
        pass
    return None


def load():
    try:
        with open(LIST) as f:
            return [(bytes.fromhex(e['ssid']), bytes.fromhex(e['key'])) for e in json.load(f)['known']]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def write_private(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def save(known):
    data = {'note': 'hanbang hb_wifimem: Wi-Fi used before, newest first (hex). Contains passwords: never copy off the device.',
            'known': [{'ssid': s.hex(), 'key': k.hex()} for s, k in known]}
    write_private(LIST, json.dumps(data, indent=1).encode())


def keyfile_value(b):
    """GKeyFile(connman 설정) 값으로: 역슬래시·줄바꿈·탭·앞 공백을 이스케이프. UTF-8 이 아니면 None."""
    try:
        s = b.decode('utf-8')
    except UnicodeDecodeError:
        return None
    s = s.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
    if s.startswith(' '):
        s = '\\s' + s[1:]
    return s


def path_for(ssid):
    return os.path.join(OUTDIR, PREFIX + hashlib.sha1(ssid).hexdigest()[:12] + '.config')


def render(ssid, key):
    kv = keyfile_value(key) if key else ''
    if kv is None:
        return None
    tag = hashlib.sha1(ssid).hexdigest()[:12]
    out = ['[global]', f'Name=hanbang_wifimem_{tag}', 'Description=hanbang: a Wi-Fi network used before (hb_wifimem)', '',
           f'[service_hb_wifimem_{tag}]', 'Type=wifi', f'SSID={ssid.hex()}', 'Hidden=false']
    if kv:
        out.append(f'Passphrase={kv}')
    out += ['Autoconnect=true', 'IPv6=off', '']
    return '\n'.join(out).encode()


def file_ssid(path):
    try:
        with open(path, 'rb') as f:
            for line in f:
                if line.startswith(b'SSID='):
                    return bytes.fromhex(line[5:].strip().decode())
    except (OSError, ValueError):
        pass
    return None


SW = {'last': None, 'until': 0.0, 'target': None}   # (10/26) 메뉴에서 고른 망이 바뀐 뒤 옮겨 가는 동안


def svc_list():
    """connmanctl services → [(붙음 여부 'O'/'R'/'', SSID bytes, 서비스 이름)] — 이름 · 비번은 기록에 안 씀."""
    try:
        out = subprocess.run(['connmanctl', 'services'], capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return []
    rows = []
    for l in out.splitlines():
        m = re.search(r'(wifi_[0-9a-f]+_([0-9a-f]+)_managed_[a-z]+)\s*$', l)
        if m:
            try:
                rows.append((l[2:3].strip(), bytes.fromhex(m.group(2)), m.group(1)))
            except ValueError:
                pass
    return rows


def on_target(ssid):
    return any(st in ('O', 'R') and s == ssid for st, s, _ in svc_list())


def memory_off_cleanup():
    """(10/26) 기억 끔: 목록 파일 지움 · 우리 connman 파일은 지금 붙은 망 것만 남김(지우면 connman 이 끊음). 이름 · 비번은 기록에 안 씀."""
    if os.path.exists(LIST):
        try:
            os.remove(LIST)
            log('memory off: saved Wi-Fi list removed')
        except OSError:
            pass
    cur = set(s for st_, s, _ in svc_list() if st_ in ('O', 'R'))
    kept = removed = 0
    for p in glob.glob(os.path.join(OUTDIR, PREFIX + '*.config')):
        if file_ssid(p) in cur:
            kept += 1
            continue
        try:
            os.remove(p)
            removed += 1
        except OSError:
            pass
    if kept or removed:
        log(f'memory off: connman files -{removed} (kept {kept} of the joined network until reboot)')


def step():
    """knulli.conf 를 읽어 목록·connman 설정 파일을 맞춤. 지금 와이파이의 파일은 건드리지 않음."""
    if not MEMORY:
        memory_off_cleanup()
        SW['target'] = None
        return
    ssid, key = conf_get('wifi.ssid'), conf_get('wifi.key')
    enabled = conf_get('wifi.enabled') == b'1'
    known = [(s, k) for s, k in load() if k]          # (10/26) 비밀번호 없는 와이파이는 기억 안 함
    if ssid and key:
        new = [(ssid, key)] + [(s, k) for s, k in known if s != ssid]
        new = new[:MAX]
    else:
        new = known
    if new != load():
        save(new)
        log(f'list updated: {len(new)} known')
    known = new
    now = time.time()
    if enabled and ssid and SW['last'] is not None and ssid != SW['last']:
        SW['until'], SW['target'] = now + 60, ssid      # (10/26) 사용자가 메뉴에서 다른 망을 고름 → 60초 동안 옛 망 파일을 치워 둠
        log('menu network changed: moving to it (old networks held 60 s)')
    SW['last'] = ssid
    moving = enabled and SW['target'] == ssid and now < SW['until'] and not on_target(ssid)
    if moving:
        for st_, s, name in svc_list():
            if s == ssid and st_ not in ('O', 'R'):
                subprocess.run(['connmanctl', 'connect', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25)
                break
    elif SW['target'] is not None:
        log('moved to the menu network' if on_target(ssid) else 'menu network not joined in 60 s — old networks back')
        SW['target'] = None
    want = {} if (not enabled or moving) else {s: k for s, k in known if s != ssid}
    made = changed = removed = 0
    for s, k in want.items():
        p, data = path_for(s), render(s, k)
        if data is None:
            continue
        try:
            with open(p, 'rb') as f:
                same = f.read() == data
        except OSError:
            same, made = False, made + 1
        if not same:
            changed += os.path.exists(p)
            write_private(p, data)
    for p in glob.glob(os.path.join(OUTDIR, PREFIX + '*.config')):
        s = file_ssid(p)
        if s is not None and s in want:
            continue
        if enabled and ssid and s == ssid:
            continue   # 지금 와이파이 — 켜져 있는 동안은 그대로(지우면 connman 이 연결을 끊음)
        os.remove(p)
        removed += 1
    if made or changed or removed:
        log(f'connman files: +{made} ~{changed} -{removed} (now {len(glob.glob(os.path.join(OUTDIR, PREFIX + "*.config")))})')


def uptime():
    try:
        with open('/proc/uptime') as f:
            return float(f.read().split()[0])
    except (OSError, ValueError):
        return 0.0


def wifi_cycle():
    """10/19: 메뉴에서 와이파이를 껐다 켠 것과 같은 일(connman). 출력은 버림(이름 · 비번 없음)."""
    subprocess.run(['connmanctl', 'disable', 'wifi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    time.sleep(2)
    subprocess.run(['connmanctl', 'enable', 'wifi'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)


def bgscan_off(st):
    """붙어 있는 와이파이의 bgscan 이 켜져 있으면 'none' 으로 + Reattach. 네트워크 속성 중 bgscan 만 보고 다른 값(이름·비번)은 안 씀.
    10/19 고침: 2번 기기가 부팅 23초에 붙자마자 Reattach 한 뒤 와이파이가 안 돌아옴(사용자가 메뉴에서 껐다 켜서 붙음) →
      ① 켜진 지 120초 안 · 붙은 지 30초 안에는 건드리지 않음 ② Reattach 뒤 60초 안에 다시 안 붙으면 와이파이를 한 번 껐다 켜고
      그 부팅 동안은 검색 끄기를 그만둠(같은 일이 되풀이되지 않게)."""
    if os.path.exists(BG_KEEP) or st.get('gaveup'):
        return
    now = time.time()
    import dbus
    if 'bus' not in st:
        st['bus'] = dbus.SystemBus()
    bus = st['bus']
    ipath = dbus.Interface(bus.get_object(W, '/fi/w1/wpa_supplicant1'), W).GetInterface('wlan0')
    iobj = bus.get_object(W, ipath)
    iprops = dbus.Interface(iobj, 'org.freedesktop.DBus.Properties')
    state = str(iprops.Get(W + '.Interface', 'State'))
    if state != 'completed':
        st['since'] = None
        ra = st.get('reattach_at')
        if ra and now - ra > 60 and not st.get('cycled'):
            st['cycled'] = True
            st['gaveup'] = True          # 이번 부팅 동안은 검색 끄기를 더 안 함(KNULLI 기본 5분 검색으로)
            log('reattach 뒤 60초 안 붙음 → 와이파이 껐다 켬 · 이번 부팅엔 검색 끄기 그만')
            wifi_cycle()
        return
    if st.get('reattach_at'):
        st.pop('reattach_at', None)
        st.pop('cycled', None)
    if uptime() < 120:
        return
    if not st.get('since'):
        st['since'] = now
        return
    if now - st['since'] < 30:
        return
    st['tries'] = [t for t in st.get('tries', []) if now - t < 600]
    if len(st['tries']) >= 3:
        return
    nprops = dbus.Interface(bus.get_object(W, iprops.Get(W + '.Interface', 'CurrentNetwork')), 'org.freedesktop.DBus.Properties')
    if str(nprops.Get(W + '.Network', 'Properties').get('bgscan', '')).strip('"') == BG_OFF:
        return
    nprops.Set(W + '.Network', 'Properties', dbus.Dictionary({'bgscan': dbus.String(BG_OFF)}, signature='sv'))
    dbus.Interface(iobj, W + '.Interface').Reattach()
    st['tries'].append(now)
    st['reattach_at'] = now
    log('bgscan off (reattach)' + (' — 3rd time in 10 min, stop for now' if len(st['tries']) >= 3 else ''))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'once':
        step()
        return
    last = None
    bg = {}
    while True:
        try:
            m = os.stat(CONF).st_mtime_ns
        except OSError:
            m = None
        if m != last or SW['target'] is not None:     # (10/26) 옮기는 동안은 5초마다 다시 봄
            last = m
            try:
                step()
            except Exception as e:  # 기록에 값은 안 씀
                log(f'error: {type(e).__name__}')
        if SW['target'] is not None:                   # (10/26) 새 망으로 옮기는 동안엔 검색 끄기(Reattach) 쉼
            time.sleep(5)
            continue
        try:
            bgscan_off(bg)
            bg.pop('err', None)
        except Exception as e:      # 와이파이가 꺼졌거나 wpa_supplicant 가 다시 켜지는 중 등 — 같은 오류는 한 번만 적음
            bg.pop('bus', None)
            if bg.get('err') != type(e).__name__:
                bg['err'] = type(e).__name__
                log(f'bgscan check: {type(e).__name__}')
        time.sleep(5)


if __name__ == '__main__':
    main()
