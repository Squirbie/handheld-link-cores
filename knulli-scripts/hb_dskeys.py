#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_dskeys.py - DraStic button helper.
"""(2026-10-10): DS(DraStic) 버튼 도우미 (기기: /userdata/system/claude/hb_dskeys.py)

1) DS 메뉴 = M+B (레트로아크와 같게). 원래 DraStic 은 M 을 누르는 순간 메뉴를 열어서
   M+볼륨(밝기)·M 꾹(배터리)·M+START(끄기)를 쓸 때마다 메뉴가 떴다(사용자 10/10).
   drastic.cfg 에서 패드 M(controls_b[CONTROL_INDEX_MENU])을 65535(안 씀)로 바꾸고, 이 도우미가 M 을 누른 채 B 를 누르면
   가상 키보드 Home(drastic.cfg controls_a[CONTROL_INDEX_MENU] = 330 = Home)을 보낸다.
   (10/10 21:4x) 메뉴를 열기 전에 게임 안 팝업 글(/tmp/hb_osd.txt, M 꾹 배터리 등)을 비우고 2프레임 기다린다.
   DraStic 메뉴는 화면을 넘기지(pan) 않아서, 열 때 떠 있던 팝업 글이 메뉴 위에 그대로 남았다(사용자 10/10 21:2x).
2) 끄기 = M+START (10/10 21:4x 바꿈): ds_quit.py 가 /tmp/hb_dskeys.quit 를 만들면 가상 키보드 '3'
   (drastic.cfg controls_a[CONTROL_INDEX_QUIT] = 51 = '3', DraStic 원래 '끄기' 키)을 보낸다 → 메뉴를 거치지 않고 바로 꺼짐.
   예전에는 메뉴를 열고 맨 밑 Exit 까지 내려가서(3.5초, 메뉴가 보임) '기괴하다'(사용자 10/10 21:2x).
3) ds_quit.py 가 /tmp/hb_dskeys.menu 를 만들면 메뉴 열기(Home) — 키 '3' 이 안 먹을 때 쓰는 예비 길.
- (10/10 21:4x 뺌) 오른쪽 스틱(펜)을 쓰면 터치 화면을 자동으로 크게 바꾸던 것: 사용자가 'L2 팝업 확대가 기본, 자동 바꾸기는 없애자'.
- advanced_drastic/launch.sh 가 DraStic 보다 먼저 띄운다(가상 키보드가 DraStic 시작 전에 있어야 SDL 이 잡음).
- 패드는 막지(grab) 않는다. DraStic 이 30초 안에 안 뜨거나 뜬 뒤 꺼지면 스스로 끝난다.
끄기: /userdata/system/claude/hb_dskeys.off (그때는 drastic.cfg 의 controls_b[CONTROL_INDEX_MENU] 를 1035 로 되돌려야 M 으로 메뉴가 열림)
기록: /tmp/hb_dskeys.log (램)"""
import os
import select
import subprocess
import time
import xml.etree.ElementTree as ET
from evdev import InputDevice, UInput, ecodes as e, list_devices

OFF = '/userdata/system/claude/hb_dskeys.off'
ES_INPUT = '/userdata/system/configs/emulationstation/es_input.cfg'
REQ = '/tmp/hb_dskeys.menu'
REQ_QUIT = '/tmp/hb_dskeys.quit'
OSD_TEXT = '/tmp/hb_osd.txt'
LOG = '/tmp/hb_dskeys.log'


def log(msg):
    try:
        with open(LOG, 'a') as f:
            f.write(time.strftime('%H:%M:%S ') + msg + '\n')
    except OSError:
        pass


def pad_codes():
    """es_input.cfg 에서 이 기기 패드의 버튼 코드. 없으면 RG35XX Pro 값."""
    want = {'hotkey': 312, 'b': 305}
    found = {}
    try:
        for ic in ET.parse(ES_INPUT).getroot().iter('inputConfig'):
            if ic.get('type') != 'joystick':
                continue
            m = {}
            for i in ic.iter('input'):
                if i.get('name') in want and i.get('code'):
                    m[i.get('name')] = int(i.get('code'))
            found[ic.get('deviceName')] = m
    except (OSError, ET.ParseError):
        pass
    return want, found


def find_pad():
    want, found = pad_codes()
    for path in sorted(list_devices()):
        try:
            d = InputDevice(path)
        except OSError:
            continue
        if d.name in found:
            c = dict(want); c.update(found[d.name])
            return d, c
        d.close()
    try:
        return InputDevice('/dev/input/event1'), want
    except OSError:
        return None, None


def running():
    return subprocess.call(['pidof', 'drastic'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0


def clear_osd():
    """게임 안 팝업 글을 비움 → hb_dsosd.so 가 다음 화면 넘길 때 그 자리를 원래대로 되돌림."""
    try:
        if os.path.getsize(OSD_TEXT) > 0:
            open(OSD_TEXT, 'w').close()
            return True
    except OSError:
        pass
    return False


def take(path):
    if not os.path.exists(path):
        return False
    try:
        os.remove(path)
    except OSError:
        pass
    return True


def main():
    if os.path.exists(OFF):
        return
    pad, c = find_pad()
    if pad is None:
        log('no pad')
        return
    ui = UInput({e.EV_KEY: [e.KEY_HOME, e.KEY_7, e.KEY_3]}, name='hb-dskeys-kbd')
    take(REQ); take(REQ_QUIT)
    log('start pad=%s "%s" codes=%s' % (pad.path, pad.name, c))

    def tap(key):
        ui.write(e.EV_KEY, key, 1); ui.syn(); time.sleep(0.05)
        ui.write(e.EV_KEY, key, 0); ui.syn()

    def open_menu(why):
        if clear_osd():
            time.sleep(0.07)   # 2~3프레임: 떠 있던 팝업 글을 지운 화면이 넘어간 뒤 메뉴
        tap(e.KEY_HOME); log(why + ' -> menu')

    t0 = time.time()
    while not running():
        if time.time() - t0 > 30:
            log('drastic never started'); ui.close(); return
        time.sleep(0.3)
    menu_held = False
    last_check = time.time()
    log('drastic up')
    try:
        while True:
            r, _, _ = select.select([pad.fd], [], [], 0.1)
            now = time.time()
            if r:
                for ev in pad.read():
                    if ev.type == e.EV_KEY:
                        if ev.code == c['hotkey']:
                            menu_held = ev.value != 0
                        elif ev.code == c['b'] and ev.value == 1 and menu_held:
                            open_menu('M+B')
            if take(REQ_QUIT):
                clear_osd()
                tap(e.KEY_3); log('request -> quit key 3')
            if take(REQ):
                open_menu('request')
            if now - last_check > 1.0:
                last_check = now
                if not running():
                    break
    except OSError as ex:
        log('pad error %s' % ex)
    ui.close()
    log('end')


if __name__ == '__main__':
    main()
