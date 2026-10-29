#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_dsmac.py - Gives every device its own DS firmware MAC after an SD card was cloned.
"""DS 고유 번호(MAC) 기기마다 다르게 (기기: /userdata/system/claude/hb_dsmac.py)
왜: 카드를 통째로 복사하면 모든 기기의 DS 펌웨어 번호가 같아져서(00:16:56:xx:xx:xx) 두 기기가 DS 무선 방에 같이 못 들어감
    (10/8 마리오카트 DS '에러가 발생했습니다'). 짝 기기뿐 아니라 이 카드를 받은 다른 사람 기기에서도 저절로 달라지게 한다.
하는 일: 켤 때 한 번(hb_dsmac 서비스) 와이파이 장치 번호를 읽고, 지난번에 적어 둔 와이파이 번호와 다르면(= 다른 기기에 꽂힌 카드)
    DS 번호를 00:16:56 + 와이파이 번호 끝 3자리로 바꿔 멜론DS(/userdata/bios/firmware.bin)와 DraStic(nds_firmware.bin)
    두 펌웨어에 같이 적는다(체크섬 다시 계산). 같은 기기에서는 아무것도 안 함. 상태 파일: /userdata/system/claude/hb_dsmac.state
    (포켓몬 4세대는 DS 번호가 바뀌면 하루 동안 시간 이벤트를 막으니, 한 기기에서는 번호가 절대 안 바뀌어야 함)
    번호를 바꿀 때마다 그 전 상태 줄을 hb_dsmac.state.history 에 남긴다(10/13 더함).
  python3 hb_dsmac.py                켤 때 하는 일
  python3 hb_dsmac.py --status       지금 번호만 보기
  python3 hb_dsmac.py --adopt [번호]  기기 몸체를 새것으로 바꿨을 때(같은 카드를 옮겼거나, 그 사람 저장을 새 카드로 옮겼을 때)
                                     예전 몸체의 DS 번호를 그대로 이어받기 — 번호를 안 주면 기록에서 가장 최근의 '다른 몸체' 번호를 씀.
                                     DS 게임을 켜기 전에 한 번. 그 뒤로는 이 몸체에서 그 번호가 고정(켤 때 다시 안 바뀜).
                                     같은 번호를 쓰는 다른 기기가 같은 방에 있으면 둘이 같이 못 하니, 예전 몸체는 안 쓸 때만.
  (시험용 환경: HB_DSMAC_STATE · HB_DSMAC_FW(콜론으로 여러 개) · HB_DSMAC_WIFI — 맥에서 가짜 펌웨어로 시험할 때만)"""
import glob
import os
import re
import subprocess
import sys
import time

STATE = os.environ.get('HB_DSMAC_STATE', '/userdata/system/claude/hb_dsmac.state')
HISTORY = STATE + '.history'
FIRMWARES = (os.environ['HB_DSMAC_FW'].split(':') if os.environ.get('HB_DSMAC_FW')
             else ['/userdata/bios/firmware.bin', '/userdata/system/configs/advanced_drastic/system/nds_firmware.bin'])
TABLE = (0xC0C1, 0xC181, 0xC301, 0xC601, 0xCC01, 0xD801, 0xF001, 0xA001)
DS_EMUS = ('drastic', 'dsperate', 'dsperate_hbmp', 'retroarch')


def crc16(data, crc=0):
    for b in data:
        crc ^= b
        for j in range(8):
            crc = (crc >> 1) ^ (TABLE[j] << (7 - j)) if crc & 1 else crc >> 1
    return crc & 0xFFFF


def fw_mac(path):
    fw = open(path, 'rb').read()
    return ':'.join(f'{b:02X}' for b in fw[0x36:0x3C])


def fw_valid(path):
    fw = open(path, 'rb').read()
    n = int.from_bytes(fw[0x2C:0x2E], 'little')
    return len(fw) == 0x40000 and int.from_bytes(fw[0x2A:0x2C], 'little') == crc16(fw[0x2C:0x2C + n])


def set_fw_mac(path, mac):
    if not fw_valid(path):
        return f'skip (not a valid DS firmware) {path}'
    fw = bytearray(open(path, 'rb').read())
    n = int.from_bytes(fw[0x2C:0x2E], 'little')
    fw[0x36:0x3C] = mac
    fw[0x2A:0x2C] = crc16(fw[0x2C:0x2C + n]).to_bytes(2, 'little')
    tmp = path + '.hbtmp'
    with open(tmp, 'wb') as f:
        f.write(fw)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return f'set {fw_mac(path)} {path}'


def wifi_mac():
    if os.environ.get('HB_DSMAC_WIFI'):
        return os.environ['HB_DSMAC_WIFI'].lower()
    for _ in range(60):  # the wifi driver can appear a little after boot
        for d in sorted(glob.glob('/sys/class/net/*/wireless')):
            a = open(os.path.join(os.path.dirname(d), 'address')).read().strip().lower()
            if a and a != '00:00:00:00:00:00':
                return a
        time.sleep(1)
    return None


def read_state():
    return open(STATE).read().split() if os.path.isfile(STATE) else []


def write_state(wmac, mac, note=''):
    if os.path.isfile(STATE):  # keep the line we are replacing, so --adopt can find the old body's DS number
        with open(HISTORY, 'a') as f:
            f.write(open(STATE).read().rstrip('\n') + '\n')
    tmp = STATE + '.hbtmp'
    with open(tmp, 'w') as f:
        f.write(f"{wmac} {':'.join(f'{b:02X}' for b in mac)} {time.strftime('%Y-%m-%d %H:%M:%S')}{' ' + note if note else ''}\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STATE)


def ds_running():
    if os.environ.get('HB_DSMAC_STATE'):  # Mac test
        return []
    out = subprocess.run(['pidof'] + list(DS_EMUS), capture_output=True, text=True).stdout.split()
    return out


def adopt(wmac, fws, arg):
    if ds_running():
        print('refuse: a DS emulator (or RetroArch) is running — quit the game first')
        return 2
    if arg:
        if not re.fullmatch(r'00:16:56(:[0-9A-Fa-f]{2}){3}', arg):
            print('refuse: give the number as 00:16:56:XX:XX:XX')
            return 2
        mac = bytes(int(x, 16) for x in arg.split(':'))
    else:
        lines = [ln.split() for ln in (open(HISTORY).read().splitlines() if os.path.isfile(HISTORY) else []) if ln.strip()]
        cur = read_state()
        if cur:
            lines.append(cur)
        old = [ln for ln in lines if len(ln) >= 2 and ln[0] != wmac]
        if not old:
            print('refuse: no earlier body in the record — give the old number: --adopt 00:16:56:XX:XX:XX')
            return 2
        mac = bytes(int(x, 16) for x in old[-1][1].split(':'))
    bad = [p for p in fws if not fw_valid(p)]
    if bad:  # check every file first, so we never leave the two firmwares with different numbers
        print('refuse: not a valid DS firmware — nothing changed: ' + ' '.join(bad))
        return 2
    log = [set_fw_mac(p, mac) for p in fws]
    write_state(wmac, mac, 'adopted')
    print('\n'.join(log))
    return 0


def main():
    wmac = wifi_mac()
    fws = [p for p in FIRMWARES if os.path.isfile(p)]
    if '--status' in sys.argv:
        print('wifi', wmac, 'state', ' '.join(read_state()) or None)
        for p in fws:
            print(fw_mac(p), p)
        return 0
    if not wmac or not fws:
        return 0
    if '--adopt' in sys.argv:
        i = sys.argv.index('--adopt')
        return adopt(wmac, fws, sys.argv[i + 1] if len(sys.argv) > i + 1 else '')
    old = read_state()
    if old and old[0] == wmac:
        return 0  # same device as last time: never change the DS MAC
    new = bytes([0x00, 0x16, 0x56] + [int(x, 16) for x in wmac.split(':')[3:6]])
    log = [set_fw_mac(p, new) for p in fws]
    write_state(wmac, new)
    print('\n'.join(log))
    return 0


if __name__ == '__main__':
    sys.exit(main())
