#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_ds_remember.py - DraStic: remembers the large-screen layout per game.
"""(2026-10-14): DraStic 게임마다 큰 화면 기억 (기기: /userdata/system/claude/hb_ds_remember.py)

advanced_drastic/launch.sh 가 DraStic 이 끝난 뒤, /tmp/hb_ds_big 이 1 일 때만 부른다:
    python3 hb_ds_remember.py "<롬 이름(확장자 뺀 것)>"
hb_dsosd.so 는 게임 중 '켤 때와 다른 화면이 크게' 20프레임 넘게 이어지면 /tmp/hb_ds_big 에 1, 다시 같아지면 0 을 쓴다.
끝날 때 1 = 사용자가 R2 로 큰 화면을 바꾼 채로 끈 것 → config/<롬>.cfg 의 screen_swap 을 뒤집는다. 다음에 켜면 그 화면이 크게.
- 파일이 없으면 지금 drastic.cfg 를 복사하고 screen_swap = 1.
- 뒤집은 결과가 drastic.cfg 와 똑같아지면(아래 크게로 돌아옴) 그 파일을 지운다 → 나중에 drastic.cfg 를 고쳐도 옛 사본이 안 남음.
- DSperate(같이하기 48개)는 dsperate 가 스스로 기억해서 여기 안 옴.
끄기: /userdata/system/claude/hb_ds_remember.off · 기록: /tmp/hb_ds_remember.log (램)"""
import os
import re
import sys
import time

CFG_DIR = '/userdata/system/configs/advanced_drastic/config'
STATE = '/tmp/hb_ds_big'
OFF = '/userdata/system/claude/hb_ds_remember.off'
LOG = '/tmp/hb_ds_remember.log'
SWAP = re.compile(rb'^(screen_swap = )([01])(\r?)$', re.M)


def log(msg):
    try:
        with open(LOG, 'a') as f:
            f.write(time.strftime('%H:%M:%S ') + msg + '\n')
    except OSError:
        pass


def write_atomic(path, data):
    tmp = path + '.hbtmp'
    with open(tmp, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main():
    try:
        with open(STATE) as f:
            v = f.read().strip()
        os.remove(STATE)
    except OSError:
        return
    if len(sys.argv) != 2 or v != '1' or os.path.exists(OFF):
        return
    base = sys.argv[1]
    if not base or '/' in base or base.startswith('.') or base == 'drastic':
        log('skip name %r' % base)
        return
    path = os.path.join(CFG_DIR, base + '.cfg')
    main_cfg = os.path.join(CFG_DIR, 'drastic.cfg')
    try:
        with open(main_cfg, 'rb') as f:
            main_data = f.read()
        src = path if os.path.exists(path) else main_cfg
        with open(src, 'rb') as f:
            data = f.read()
    except OSError as ex:
        log('read error %s' % ex)
        return
    m = list(SWAP.finditer(data))
    if len(m) != 1:
        log('%s: screen_swap lines %d, not touching' % (src, len(m)))
        return
    new = b'0' if m[0].group(2) == b'1' else b'1'
    out = data[:m[0].start(2)] + new + data[m[0].end(2):]
    if out == main_data:
        os.remove(path)
        log('%s -> swap %s = same as drastic.cfg, removed' % (base, new.decode()))
    else:
        write_atomic(path, out)
        log('%s -> swap %s (%s)' % (base, new.decode(), 'new' if src == main_cfg else 'flipped'))


if __name__ == '__main__':
    main()
