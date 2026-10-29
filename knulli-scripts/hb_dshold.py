#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_dshold.py - DraStic: shows the two screens swapped while L2 is held (the small bottom screen becomes large).
"""(2026-10-09): DS(DraStic) — L2 를 누르고 있는 동안만 두 화면을 바꿔 보여 줌(작은 아래 화면을 크게).
(기기: /userdata/system/claude/hb_dshold.py)

- advanced_drastic/launch.sh 가 DraStic 보다 먼저 띄운다(가상 키보드가 DraStic 시작 전에 있어야 SDL 이 잡음).
- L2 를 누를 때·뗄 때 한 번씩 키보드 '7' 을 보낸다. drastic.cfg 의 화면 바꾸기 키(controls_a[CONTROL_INDEX_SWAP_SCREENS])를
  Backspace(8, 메뉴 '뒤로'와 겹침) 대신 '7'(55)로 바꿔 둠. R2(누를 때마다 바꾸기)는 그대로.
- L2 버튼 번호는 es_input.cfg 에서 이 패드 이름의 l2 코드를 읽는다(없으면 314). 패드는 막지(grab) 않는다.
- DraStic 이 30초 안에 안 뜨거나, 뜬 뒤 꺼지면 스스로 끝난다. 끄기: /userdata/system/claude/hb_dshold.off
기록: /tmp/hb_dshold.log (램, 켜고 끈 것만)"""
import os
import select
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from evdev import InputDevice, UInput, ecodes as e, list_devices

OFF = '/userdata/system/claude/hb_dshold.off'
ES_INPUT = '/userdata/system/configs/emulationstation/es_input.cfg'
LOG = '/tmp/hb_dshold.log'


def log(msg):
    try:
        with open(LOG, 'a') as f:
            f.write(time.strftime('%H:%M:%S ') + msg + '\n')
    except OSError:
        pass


def l2_codes():
    out = {}
    try:
        for ic in ET.parse(ES_INPUT).getroot().iter('inputConfig'):
            for i in ic.iter('input'):
                if i.get('name') == 'l2' and i.get('type') == 'button' and i.get('code'):
                    out[ic.get('deviceName')] = int(i.get('code'))
    except (OSError, ET.ParseError):
        pass
    return out


def find_pad():
    codes = l2_codes()
    for path in sorted(list_devices()):
        try:
            d = InputDevice(path)
        except OSError:
            continue
        if d.name in codes:
            return d, codes[d.name]
        d.close()
    try:
        d = InputDevice('/dev/input/event1')
        return d, 314
    except OSError:
        return None, None


def running():
    return subprocess.call(['pidof', 'drastic'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def main():
    if os.path.exists(OFF):
        return
    pad, l2 = find_pad()
    if pad is None:
        log('no pad'); return
    ui = UInput({e.EV_KEY: [e.KEY_7]}, name='hb-dshold-kbd')
    log(f'start pad={pad.path} "{pad.name}" l2={l2}')

    def tap():
        ui.write(e.EV_KEY, e.KEY_7, 1); ui.syn(); time.sleep(0.04)
        ui.write(e.EV_KEY, e.KEY_7, 0); ui.syn()

    t0 = time.time()
    while not running():
        if time.time() - t0 > 30:
            log('drastic never started'); ui.close(); return
        time.sleep(0.5)
    held = False
    last_check = time.time()
    try:
        while True:
            r, _, _ = select.select([pad.fd], [], [], 1.0)
            if r:
                for ev in pad.read():
                    if ev.type == e.EV_KEY and ev.code == l2:
                        if ev.value == 1 and not held:
                            held = True; tap()
                        elif ev.value == 0 and held:
                            held = False; tap()
            if time.time() - last_check > 1.0:
                last_check = time.time()
                if not running():
                    break
    except OSError as ex:
        log(f'pad error {ex}')
    ui.close()
    log('end')


if __name__ == '__main__':
    main()
