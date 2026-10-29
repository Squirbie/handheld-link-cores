# SPDX-License-Identifier: GPL-3.0-or-later
# nds_save_sync.py - Keeps DS saves in step between DraStic, melonDS DS and DSperate.
"""KNULLI game hook helper: keeps DraStic (.dsv) and melonDS DS (.srm) saves of the same NDS game in sync.
Called by /userdata/system/scripts/nds_save_sync.sh with: gameStart|gameStop system emulator core rom.
On gameStart the save for the emulator about to run is refreshed from the other emulator's save
when that one is newer and different. The replaced file is kept once as <name>.sync-bak."""
import os
import shutil
import struct
import sys
import time

event, system, emulator, core, rom = (sys.argv[1:] + [''] * 5)[:5]
base = os.path.splitext(os.path.basename(rom))[0]
DSV = f'/userdata/saves/nds/advanced_drastic/saves/{base}.dsv'
SRM = f'/userdata/saves/nds/{base}.srm'
TEXT = b'|<--Snip above here to create a raw sav by excluding this DeSmuME savedata footer:'
TAG = b'|-DESMUME SAVE-|'


def raw_of(data):
    return data[:-122] if len(data) >= 122 and data.endswith(TAG) else data


def dsv_of(raw):
    n = len(raw)
    addr = 1 if n <= 512 else 2 if n <= 65536 else 3
    return raw + TEXT + struct.pack('<6I', n, n, 0, addr, n, 0) + TAG


def read(p):
    with open(p, 'rb') as f:
        return f.read()


def write(p, data):
    if os.path.exists(p):
        shutil.copy2(p, p + '.sync-bak')
    with open(p + '.sync-tmp', 'wb') as f:
        f.write(data)
    os.replace(p + '.sync-tmp', p)


def log(msg):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), emulator, base, msg)


if event == 'gameStart' and system == 'nds' and base:
    has_dsv, has_srm = os.path.isfile(DSV), os.path.isfile(SRM)
    if 'drastic' in emulator and has_srm:
        srm = read(SRM)
        if not has_dsv or (os.path.getmtime(SRM) > os.path.getmtime(DSV) and raw_of(read(DSV)) != srm):
            write(DSV, dsv_of(srm))
            log('melonDS save -> DraStic')
    elif 'drastic' not in emulator and has_dsv:
        raw = raw_of(read(DSV))
        if not has_srm or (os.path.getmtime(DSV) > os.path.getmtime(SRM) and read(SRM) != raw):
            os.makedirs(os.path.dirname(SRM), exist_ok=True)
            write(SRM, raw)
            log('DraStic save -> melonDS')
