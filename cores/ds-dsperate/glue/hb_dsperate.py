#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_dsperate.py - DSperate helper that runs before and after a game.
"""(2026-10-12): DSperate 켜기 전·끈 뒤 도우미
기기: /userdata/system/configs/dsperate/hb_dsperate.py
hb_dsperate_run.sh 가 부른다.

  pre ROM   켜기 전
    1) 기기마다 다른 DS 무선 주소: dsperate.ini [net] mac_suffix 를 이 기기 무선랜(wlan0) 주소 끝 3바이트로 맞춤.
       (비워 두면 DSperate 가 무작위 값을 하나 만들어 적는데, 그 카드를 복사하면 세 기기가 같은 값이 되어 같이하기가 꼬임)
    2) 세이브 맞추기: DraStic 세이브(.dsv = 원래 세이브 + 꼬리 122바이트)와 DSperate 세이브(.sav = 원래 세이브)가 다르면
       나중에 바뀐 쪽으로 맞춤. ES 훅(nds_save_sync.py)이 켜기 직전에 멜론 .srm → .dsv 를 먼저 맞춰 두므로 보통은 .dsv → .sav.
       DSperate 가 지난번에 끝까지 못 끝나(배터리·리셋) .sav 만 새것이면 .sav → .dsv.
  post ROM  끈 뒤: .sav 가 .dsv 와 다르면 .dsv 를 .sav 로 바꿈 → 다음에 DraStic·멜론으로 켜도 같은 진행.

바꾸기 전 파일은 /userdata/saves/nds/dsperate/backup/<롬이름>.<sav|dsv>.<시각> 에 남기고, 게임·종류마다 최근 5개만 둔다.
0바이트 파일은 없는 것으로 본다(덮어쓰지도, 퍼뜨리지도 않음). 카드에 쓸 때마다 fsync(exFAT 카드는 해야 리셋에도 남음).
"""
import glob
import os
import struct
import sys
import time

SAVES = '/userdata/saves/nds'
DSV_DIR = SAVES + '/advanced_drastic/saves'
SAV_DIR = SAVES + '/dsperate'
BAK_DIR = SAV_DIR + '/backup'
INI = '/userdata/system/configs/dsperate/dsperate.ini'
TEXT = b'|<--Snip above here to create a raw sav by excluding this DeSmuME savedata footer:'
TAG = b'|-DESMUME SAVE-|'
KEEP = 5


def log(msg):
    print(time.strftime('%H:%M:%S'), msg, flush=True)


def raw_of(data):
    return data[:-122] if len(data) >= 122 and data.endswith(TAG) else data


def dsv_of(raw):
    n = len(raw)
    addr = 1 if n <= 512 else 2 if n <= 65536 else 3
    return raw + TEXT + struct.pack('<6I', n, n, 0, addr, n, 0) + TAG


def read(p):
    with open(p, 'rb') as f:
        return f.read()


def has(p):
    return os.path.isfile(p) and os.path.getsize(p) > 0


def put(p, data):
    tmp = p + '.hbtmp'
    with open(tmp, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, p)
    try:
        fd = os.open(os.path.dirname(p), os.O_RDONLY)
        os.fsync(fd)
        os.close(fd)
    except OSError:
        pass


def backup(p, kind, base):
    if not has(p):
        return
    os.makedirs(BAK_DIR, exist_ok=True)
    put(os.path.join(BAK_DIR, '%s.%s.%s' % (base, kind, time.strftime('%Y%m%d-%H%M%S'))), read(p))
    old = sorted(glob.glob(os.path.join(BAK_DIR, glob.escape(base) + '.' + kind + '.*')))
    for q in old[:-KEEP]:
        try:
            os.remove(q)
        except OSError:
            pass


def ensure_mac():
    try:
        with open('/sys/class/net/wlan0/address') as f:
            mac = f.read().strip()
        want = int(mac.replace(':', '')[-6:], 16)
    except (OSError, ValueError):
        log('mac: no wlan0 address, left as is')
        return
    try:
        with open(INI, encoding='utf-8') as f:
            lines = f.read().split('\n')
    except OSError:
        log('mac: cannot read ' + INI)
        return
    out, sec, found, net_at = [], None, False, None
    for line in lines:
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            sec = s[1:-1].strip()
            if sec == 'net':
                net_at = len(out)
        elif sec == 'net' and '=' in s and s.split('=', 1)[0].strip() == 'mac_suffix':
            found = True
            v = s.split('=', 1)[1].split('#')[0].split(';')[0].strip()
            try:
                if int(v, 0) == want:
                    return
            except ValueError:
                pass
            line = 'mac_suffix = %d' % want
        out.append(line)
    if not found:
        if net_at is None:
            out += ['[net]', 'mac_suffix = %d' % want, '']
        else:
            out.insert(net_at + 1, 'mac_suffix = %d' % want)
    put(INI, '\n'.join(out).encode('utf-8'))
    log('mac_suffix = %d (wlan0 %s)' % (want, mac))


def sync(when, rom):
    base = os.path.splitext(os.path.basename(rom))[0]
    if not base:
        return
    dsv = os.path.join(DSV_DIR, base + '.dsv')
    sav = os.path.join(SAV_DIR, base + '.sav')
    os.makedirs(SAV_DIR, exist_ok=True)
    if when == 'pre':
        if has(dsv):
            raw = raw_of(read(dsv))
            if not has(sav):
                put(sav, raw)
                log('DraStic -> DSperate (first time) %s' % base)
            elif read(sav) != raw:
                if os.path.getmtime(sav) > os.path.getmtime(dsv):
                    backup(dsv, 'dsv', base)
                    put(dsv, dsv_of(read(sav)))
                    log('DSperate save is newer (last run did not finish) -> DraStic %s' % base)
                else:
                    backup(sav, 'sav', base)
                    put(sav, raw)
                    log('DraStic -> DSperate %s' % base)
        elif has(sav):
            put(dsv, dsv_of(read(sav)))
            log('DSperate -> DraStic (DraStic had none) %s' % base)
    elif when == 'post':
        if has(sav):
            cur = read(sav)
            if not has(dsv) or raw_of(read(dsv)) != cur:
                backup(dsv, 'dsv', base)
                put(dsv, dsv_of(cur))
                log('DSperate -> DraStic %s' % base)


def main():
    when, rom = (sys.argv[1:] + ['', ''])[:2]
    if when not in ('pre', 'post') or not rom:
        print('usage: hb_dsperate.py pre|post ROM')
        return 2
    if when == 'pre':
        try:
            ensure_mac()
        except Exception as e:  # 무선 주소를 못 맞춰도 게임은 켬
            log('mac: %r' % e)
    try:
        sync(when, rom)
    except Exception as e:
        log('save sync failed: %r' % e)
    return 0


if __name__ == '__main__':
    sys.exit(main())
