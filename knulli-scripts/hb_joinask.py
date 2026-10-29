#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""hb_joinask.py - 'Join / Solo' prompt for link play (KNULLI)

English summary: when a RetroArch game starts, this asks the local network (RetroArch LAN discovery,
UDP 55435) whether a netplay room for the same game is already open. If one is, it draws a small window on
/dev/fb0 - [A] Join / [B] Solo, solo after 10 s - and hands the choice to emulatorlauncher. It also handles
DSperate rooms (--ds), paired versions (two different games that link) and per-player saves (hb_ownsave).
UI language: HB_LANG, else system.language in knulli.conf (Korean when it starts with "ko", otherwise English).
The notes below are the original Korean design log.


10/19: 같은 게임을 켤 때 '같이 / 혼자'를 고르는 창
- 게임을 켤 때 emulatorlauncher 의 gameStart 훅(scripts/nds_save_sync.sh 17번 블록)이 부름:
  레트로아크 게임이고, 넷플레이로 켠 게 아닐 때만(방장 'A 길게 → 넷플레이 호스트'는 그대로).
- 같은 와이파이에 레트로아크 방 찾기 신호(RANQ, UDP 55435 방송)를 0 · 0.1 · 0.25초에 보내고 0.4초 동안 답(RANS)을 모음.
  '같은 게임' 방이 없으면 바로 끝남 → 평소처럼 혼자 켜짐(늘어나는 시간 0.4초 이하, 와이파이가 없으면 0초).
  같은 게임 = 답의 content(방장 롬 이름, 확장자 뺌)가 이 롬 이름과 같음. 이름이 달라도 content_crc 가 같으면 같은 게임
  (zip 은 안의 첫 파일 CRC, 32MB 이하 낱개 파일만 직접 계산 — 큰 CD 이미지는 이름으로만).
- 방이 있으면 화면(/dev/fb0, 640x480 BGRA 두 장)에 창: '같은 게임 방이 열려 있어요 · 방장 OO' + [A 같이하기] [B 혼자 하기],
  10초 안에 안 고르면 혼자. 창이 뜨기 전부터 눌려 있던 키(게임 켤 때 누른 A)는 무시하고, 창이 뜬 뒤 새로 누른 키만 셈.
  '같이'면 /tmp/hb_joinask.json 에 {rom, ip, port, nick, t} → emulatorlauncher.py(오버레이에 넣은 몇 줄)가 손님(--connect)으로 켬.
- 켜는 동안 로딩 그림(hb_gamesplash.py)은 SIGSTOP 으로 잠깐 멈추고, 창을 닫을 때 화면 두 장을 창 뜨기 전 그대로 되돌린 뒤 SIGCONT.
- 끄기: knulli.conf 에 global.hb_joinask=0 (기기 메뉴 → 게임 설정 → '같이하기 방 물어보기') 또는 /userdata/system/claude/hb_joinask.off
- 기록: /tmp/hb_joinask.log (램). 시험: --fake-fb 파일(화면 대신 파일) · --fake-keys 파일(hb_osd FakeKeys 형식) · --bcast 주소 · --png 저장 경로.
- DS 같이하기(--ds, hb_dsperate_run.sh 가 부름): DSperate 방장은 1초마다 UDP 7063 으로 방 알림(80바이트, 이름 '<이름>'s game [<그룹>]')을 보냄.
  1.1초 듣고 같은 그룹(groups.txt 그룹 > 롬 게임 코드 4글자 > 파일 이름 — DSperate hbfam2 와 같은 규칙) 방이 있으면 같은 창.
  '같이'면 방장 주소를 화면에 안 쓰고 stdout 한 줄로 → 스크립트가 --lan-join 주소로 켬. '혼자'면 넷 없이 켬.
- 끝 코드: 0 = 같이(json 씀) · 1 = 방 없음 · 꺼 둠 · 오류(평소대로) · 2 = 창에서 혼자 고름(B · 10초 지남)
- 10/20 M158: 창을 로딩 그림처럼 픽셀 디자인으로
  다시 그림 — 갈무리 픽셀 글꼴(OFL, /userdata/system/claude/fonts/ + Galmuri-OFL.txt) · 계단 모서리 금색 테 · 단추 글자 · 그림을
  실제 점 상자로 재서 정가운데. 글꼴이 없으면 예전 글꼴(FONT)로 같은 자리.
- 10/21 짝 게임(new3, GBA 두 대 코어 1.5 · hb_ownsave 5판): 같은 게임 방이 없어도 방장 방 게임 A 가 내가 켠 게임 B 의 짝
  (hb_ownsave.PAIRS)이고, A 가 내 롬 폴더에 방장과 같은 CRC 로 있고, 방장 코어가 'mGBA Dual' 이고 나도 mgba_dual 이면
  창 제목 '같이(짝: 방장 A · 나 B)'. A → B 세이브 + 2P 롬(B)을 보내고, 받음 확인이 오면 /tmp/hb_dual_p2rom = B,
  /tmp/hb_dual_screen = 2P, json rom = A(콘텐츠 = 방장 게임) · p2rom = B → 손님 레트로아크는 콘텐츠 A 로 켜짐.
  못 보냄 · 거절(2P 롬 CRC 다름 · 옛 방장 등)이면 2초 알림 뒤 혼자 하기(B 그대로). 같은 게임 방이 있으면 늘 그쪽이 먼저.
- 10/22 각자 세이브 6판(hb_ownsave 6판 · 네오지오 포켓 · 게임기어 두 대 코어 1.1-os4): 손님 세이브 보내기를 mednafen_ngp_dual ·
  genesisplusgx_gg_dual 에도. 네오지오 짝 게임(카드 파이터즈 SNK판 ↔ 캡콤판 · 다이브 얼럿 베키 ↔ 매트)도 GBA 와 같은 길 —
  방장 코어가 'Beetle NeoPop Dual' 이고 나도 네오지오 코어면 짝. 다만 네오지오 코어는 ZIP 을 못 읽어 /tmp/hb_dual_p2rom 에
  /tmp 에 푼 보통 파일 경로(hb_ownsave.p2rom_for_core)를 적음.
- 10/26 원더스완 짝(hb_ownsave 7판 · 두 대 코어 1.9-os4): 명탐정 코난 08 ↔ 06 — 방장 코어가 'Beetle WonderSwan Dual' 이고
  나도 원더스완 코어면 짝. 방장 게임 롬은 내 폴더 + 짝 폴더(wswan ↔ wswanc)에서 찾고, 2P 롬은 /tmp 에 푼 보통 파일.
"""
import argparse
import json
import os
import re
import signal
import socket
import struct
import sys
import time
import zlib

CLAUDE = '/userdata/system/claude'
OFF = CLAUDE + '/hb_joinask.off'
CONF = '/userdata/system/knulli.conf'


def ui_lang():
    """Window language: HB_LANG > system.language in knulli.conf > English ('ko...' = Korean)"""
    v = os.environ.get('HB_LANG', '')
    if not v:
        try:
            with open(CONF, errors='replace') as f:
                for line in f:
                    if line.startswith('system.language='):
                        v = line.split('=', 1)[1].strip()
                        break
        except OSError:
            pass
    return 'ko' if v.lower().startswith('ko') else 'en'


LANG = ui_lang()
TEXT = {   # key: (Korean, English)
    'room': ('같은 게임 방이 열려 있어요', 'A room for this game is open'),
    'room_family': ('짝 게임 방이 열려 있어요', 'A linked-version room is open'),
    'singlepak': ('팩 하나로 같이하는 방이에요', 'Single-Pak room: one cartridge for two'),
    'host': ('방장', 'Host'),
    'join': ('같이하기', 'Join'),
    'solo': ('혼자 하기', 'Solo'),
    'left': ('%d초 뒤 혼자 하기로 켜져요', 'Starting solo in %d s'),
    'notice_title': ('세이브를 못 보냈어요', "Couldn't send the save"),
    'notice_line': ('이번 2P 진행은 저장 안 돼요', "P2 progress won't be saved"),
    'pair_title': ('짝 게임: %s · %s', 'Pair: %s + %s'),
    'pair_notice_title': ('짝 게임으로 못 붙었어요', "Couldn't join as a pair"),
    'pair_notice_line': ('혼자 하기로 켜져요', 'Starting solo'),
}
LABEL_EN = {'파이어레드': 'FireRed', '리프그린': 'LeafGreen', '에메랄드': 'Emerald', '루비': 'Ruby', '사파이어': 'Sapphire',
            '골드': 'Gold', '실버': 'Silver', '크리스탈': 'Crystal', '레드': 'Red', '그린': 'Green', '블루': 'Blue', '옐로': 'Yellow',
            '블랙': 'Black', '화이트': 'White', '이루': 'Iru', '루카': 'Luka', '적의 서': 'Red Book', '흑의 서': 'Black Book',
            '죠노우치': 'Jonouchi', '카이바': 'Kaiba', '유우기': 'Yugi', '유희왕 1': 'Yu-Gi-Oh! 1', '유희왕 2': 'Yu-Gi-Oh! 2',
            '유희왕 3': 'Yu-Gi-Oh! 3', 'SNK판': 'SNK', '캡콤판': 'Capcom', '베키판': 'Becky', '매트판': 'Matt',
            '레드 선': 'Red Sun', '블루 문': 'Blue Moon', '블루스': 'Blues', '컬로넬': 'Colonel', '커널': 'Colonel',
            '프로토맨': 'ProtoMan', '그레이거': 'Gregar', '팔저': 'Falzar', '카부토': 'Kabuto', '쿠와가타': 'Kuwagata',
            '쿨 블루': 'Cool Blue', '패션 레드': 'Passion Red', '서쪽의 명탐정': 'Detective of the West',
            '황혼의 황녀': 'Princess of Twilight'}


def tr(key):
    return TEXT[key][0 if LANG == 'ko' else 1]


def label(name):
    """Short version label (FireRed, Capcom ...) in the window language"""
    return name if LANG == 'ko' else LABEL_EN.get(name, name)
OUT = os.environ.get('HB_JOINASK_OUT', '/tmp/hb_joinask.json')
PRESS = '/tmp/hb_joinask.press'   # 10/20 21:0x 시험 길(위 ask 참고)
LOG = os.environ.get('HB_JOINASK_LOG', '/tmp/hb_joinask.log')
FONT = os.environ.get('HB_JOINASK_FONT', '/usr/share/emulationstation/resources/GmarketSansTTFMedium.ttf')   # 맥 시험은 환경 변수로
FALLBACK_FONTS = ('/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
FONT_DIR = os.environ.get('HB_JOINASK_FONTDIR', CLAUDE + '/fonts')   # 10/20 갈무리 픽셀 글꼴(OFL, LICENSE 같이) — 없으면 FONT
TITLE_FONT = ('Galmuri11-Bold.ttf', 24)
SMALL_FONT = ('Galmuri11.ttf', 24)
KEY_FONT = ('Galmuri11-Bold.ttf', 24)
BADGE = (2, 4, 5, 6, 7, 7, 8, 8, 8, 8, 8, 7, 7, 6, 5, 4, 2)   # 단추 그림 원: 줄마다 가운데 칸에서 양쪽 칸 수(지름 17칸)
PORT = 55435
RANQ, RANS = 0x52414E51, 0x52414E53
SENDS = (0.0, 0.1, 0.25)      # 방 찾기 신호 보내는 때(초)
WAIT = 0.4                    # 답을 기다리는 가장 긴 시간(초) — 같은 게임 방 답이 오면 그 자리에서 끝
ASK_SEC = 10                  # 창에서 안 고르면 혼자
IGNORE_SEC = 0.25             # 창이 뜬 뒤 이 시간 동안은 키를 안 셈(켤 때 누른 A 가 튀는 것 막기)
A_KEY, B_KEY = 304, 305       # 기기 패드 A · B (es_input.cfg, hb_osd.py 와 같음)
W, H, STRIDE = 640, 480, 2560
HALF = STRIDE * H
FAMILY = {}   # optional nickname -> label map (empty: the RetroArch nickname is shown as is)
# ad_packet(RetroArch 1.20 netplay_frontend.c): header crc port has_password nick[32] frontend core core_version ra_version[32 씩] content subsystem[256 씩]
AD = struct.Struct('!IiiI32s32s32s32s32s256s256s')


LOG_LIMIT = 256 * 1024       # 10/21 기록 상한: 넘으면 .1 로 돌림(램)
NOTICE_TITLE = tr('notice_title')               # 10/21 각자 세이브 4판: 보내기 실패 · 받음 확인 못 받음
NOTICE_LINE = tr('notice_line')
NOTICE_SEC = 2.0
P2ROM = '/tmp/hb_dual_p2rom'        # 10/21 짝 게임: 손님 코어가 켤 때 읽는 2P 롬 경로(한 줄)
SCREEN = '/tmp/hb_dual_screen'      # 두 대 코어 화면 고르기(코어 설정보다 먼저) — 짝 손님은 콘텐츠가 A 라 A 의 .opt 대신 이것으로 2P
PAIR_TITLE = tr('pair_title')
PAIR_NOTICE_TITLE = tr('pair_notice_title')
PAIR_NOTICE_LINE = tr('pair_notice_line')


def log(msg):
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) >= LOG_LIMIT:
            os.replace(LOG, LOG + '.1')
        with open(LOG, 'a') as f:
            f.write(time.strftime('%H:%M:%S ') + msg + '\n')
    except OSError:
        pass


def turned_off():
    if os.path.exists(OFF):
        return True
    try:
        with open(CONF, errors='replace') as f:
            for line in f:
                if line.startswith('global.hb_joinask='):      # 이 줄만 봄
                    return line.split('=', 1)[1].strip() == '0'
    except OSError:
        pass
    return False


def stem(p):
    # 10/21: '바깥.zip#안쪽' 같은 압축 표기만 나눔 — 보통 이름의 '#'는 그대로(hb_ownsave 와 같은 규칙)
    m = re.search(r'\.(zip|7z|apk)#', p, re.I)
    b = os.path.basename(p[:m.end() - 1] if m else p)
    return os.path.splitext(b)[0].strip().lower()


def rom_crcs(rom):
    """이 롬의 CRC 후보(zip 은 안의 파일들, 32MB 이하 낱개 파일은 전체). 비싼 계산은 안 함."""
    out = set()
    try:
        if rom.lower().endswith('.zip'):
            import zipfile
            with zipfile.ZipFile(rom) as z:
                for i in z.infolist()[:8]:
                    out.add(i.CRC & 0xffffffff)
        elif os.path.getsize(rom) <= 32 * 2 ** 20:
            with open(rom, 'rb') as f:
                out.add(zlib.crc32(f.read()) & 0xffffffff)
    except (OSError, ValueError, ImportError, RuntimeError):
        pass
    return out


def family_name(ip):
    """lan_names.sh 가 게임 켤 때마다 /etc/hosts 에 적는 짝 기기 이름으로 바꿈(없으면 None)"""
    try:
        with open('/etc/hosts') as f:
            for line in f:
                a = line.split()
                if len(a) >= 2 and a[0] == ip:
                    for n in a[1:]:
                        if n.lower() in FAMILY:
                            return FAMILY[n.lower()]
    except OSError:
        pass
    return None


HOSTS = '/etc/hosts'


def family_ips():
    """10/21 lan_names.sh 가 적은 다른 기기 주소('# hanbang-lan' 줄) — 방 찾기를 이 주소로도 직접 물음"""
    out = []
    try:
        with open(HOSTS) as f:
            for line in f:
                if 'hanbang-lan' in line:
                    a = line.split()
                    if a and a[0].count('.') == 3 and a[0] not in out:
                        out.append(a[0])
    except OSError:
        pass
    return out


def my_ips():
    ips = set()
    try:
        import subprocess
        out = subprocess.run(['ip', '-4', '-o', 'addr'], capture_output=True, text=True, timeout=1).stdout
        for line in out.splitlines():
            a = line.split()
            if 'inet' in a:
                ips.add(a[a.index('inet') + 1].split('/')[0])
    except (OSError, ValueError, Exception):
        pass
    return ips


GBA_CORES_PAIR = ('mgba_dual', 'gpsp', 'mgba', 'vba_next', 'vbam', 'meteor')   # 10/21 3세대 케이블 짝: 평소 다른 코어여도 짝이면 두 대 코어로 켬
NGP_CORES_PAIR = ('mednafen_ngp_dual', 'mednafen_ngp')
WS_CORES_PAIR = ('mednafen_wswan_dual', 'mednafen_wswan')   # 10/26 원더스완 짝(코난 08 ↔ 06)   # 10/22 네오지오 짝(카드 파이터즈 · 다이브 얼럿): 평소 순정 코어여도 짝이면 두 대 코어로
OWNSAVE_CORES = ('mgba_dual', 'mednafen_wswan_dual', 'mednafen_ngp_dual', 'genesisplusgx_gg_dual')   # 10/22 각자 세이브를 보내는 두 대 코어
# 짝 게임: (내 코어 묶음, 방장 방 코어 이름(레트로아크 library_name), hb_ownsave 기종, 짝 판에 쓰는 두 대 코어)
PAIR_SYSTEMS = ((GBA_CORES_PAIR, 'mGBA Dual', 1, 'mgba_dual'), (NGP_CORES_PAIR, 'Beetle NeoPop Dual', 3, 'mednafen_ngp_dual'),
                (WS_CORES_PAIR, 'Beetle WonderSwan Dual', 2, 'mednafen_wswan_dual'))


def pair_room(rom, my_core, room_core, content, crc):
    """10/21 짝 게임: 방장 방 게임이 내 게임의 짝이면 {content: 내 기기의 방장 게임 경로, host_label, my_label}
    방장 게임이 내 롬 폴더에 방장과 같은 CRC 로 있어야 함(콘텐츠가 같아야 넷플레이가 됨). 두 쪽 다 GBA(10/22 네오지오) 두 대 코어."""
    kind = next((k for cores, rcore, k, _ in PAIR_SYSTEMS if my_core in cores and room_core == rcore), None)
    if kind is None:
        return None
    try:
        import hb_ownsave as own
        names = own.pair_partners(rom)
    except Exception as e:           # 도우미가 없으면 짝 게임 없이 평소대로
        log('짝 표 못 읽음 %r' % (e,))
        return None
    for name in names:
        local = own.partner_file(own.outer_path(rom).parent, name, kind) if kind != 1 else own.partner_file(own.outer_path(rom).parent, name)
        if local is None:
            continue
        try:
            local_crc = own.rom_crc(local, kind)
        except (OSError, ValueError) as e:
            log('짝 게임 롬 못 읽음 %s %r' % (local.name, e))
            continue
        if (crc and local_crc == crc) or (not crc and stem(content) == name.lower()):
            labels = own.pair_info(local, rom)
            return dict(content=str(local), host_label=label(labels[0]), my_label=label(labels[1]), crc=local_crc, kind=kind)
        if stem(content) == name.lower():
            log('짝 게임 방이지만 방장 롬(%08x)이 내 %s(%08x)와 다름 → 짝 안 함' % (crc, local.name, local_crc))
    return None


# (10/21 Claude) 짝 묶음 — 넷패킷 코어(각자 자기 게임을 돌리고 통신만 주고받음)라 다른 판끼리 붙음. 롬 이름(확장자 뺌)으로.
LINK_FAMILIES = [
    {'Pocket Monsters - FireRed', 'Pocket Monsters - Leaf Green', 'Pocket Monsters - Emerald',
     'Pokemon - FireRed (K)', 'Pokemon - LeafGreen (K)', 'Pokemon - Emerald (K)'},
    # GB · GBC 1 · 2세대(Gambatte 통신 케이블) — 금 · 은 = 한국 정식판(해외판 바탕), 크리스탈 · 레드 · 그린 · 블루 · 옐로 = 해외판 바탕
    #   한글 패치(롬 머리 dest=01 · 1MB/2MB, 10/21 확인). 한국판은 해외판 1 · 2세대와 교환됨(일본판만 안 됨 — Bulbapedia
    #   'Korean character encoding (Generation II)'). 1 ↔ 2세대는 타임캡슐. 한글 이름은 상대 게임에서 깨져 보일 수 있음(진짜 팩도 같음).
    {'포켓 몬스터 - 골드 (한글판)', 'Pokemon - Silver Version (USA, Europe)', 'Pokemon - Crystal Version (USA, Europe) (Rev A)',
     '포켓 몬스터 - 레드 (한글판)', '포켓 몬스터 - 그린 (한글판)', '포켓 몬스터 - 블루 (한글판)', 'Pocket Monster Yellow Versionv (Korea)',
     'Pokemon - Gold (Korea)', 'Pokemon - Silver (Korea)', 'Pokemon - Crystal (K)',
     'Pokemon - Red (K)', 'Pokemon - Green (K)', 'Pokemon - Blue (K)', 'Pokemon - Yellow (K)'},
    # (추가) Dragon Quest Monsters 2 - Maruta no Fushigi na Kagi - Iru no Bouken ↔ Dragon Quest Monsters 2 - Maruta no Fushigi na Kagi - Ruka no Tabidachi
    {'Dragon Quest Monsters 2 - Maruta no Fushigi na Kagi - Iru no Bouken', 'Dragon Quest Monsters 2 - Maruta no Fushigi na Kagi - Ruka no Tabidachi'},
    # (추가) Shin Megami Tensei Devil Children Aka no Sho (k) ↔ Shin Megami Tensei Devil Children Kuro no Sho (k)
    {'Shin Megami Tensei Devil Children Aka no Sho (k)', 'Shin Megami Tensei Devil Children Kuro no Sho (k)'},
    # (추가) Yu-Gi-Oh! Duel Monsters 4 - Saikyou Kettousha Senki - Jounouchi Deck (K) ↔ Yu-Gi-Oh! Duel Monsters 4 - Saikyou Kettousha Senki - Kaiba Deck (K) ↔ Yu-Gi-Oh! Duel Monsters 4 - Saikyou Kettousha Senki - Yuugi Deck (K)
    # (10/21 19:56) 유희왕 1 · 2 · 3 · 4 — 카드 교환은 어느 편끼리도(새 편 메뉴 'DM1とトレード' 등 · 원작 설명서), 대전은 같은 편끼리만(4 는 세 판끼리)
    {'Yu-Gi-Oh! Duel Monsters 4 - Saikyou Kettousha Senki - Jounouchi Deck (K)', 'Yu-Gi-Oh! Duel Monsters 4 - Saikyou Kettousha Senki - Kaiba Deck (K)', 'Yu-Gi-Oh! Duel Monsters 4 - Saikyou Kettousha Senki - Yuugi Deck (K)',
     'Yu-Gi-Oh! Duel Monsters', 'Yu-Gi-Oh! Duel Monsters II - Dark Duel Stories (K)', 'Yu-Gi-Oh! Duel Monsters III - Sanseisenshin Kourin (K)'},
]
LINK_FAMILY_CORES = ('gpsp', 'gambatte')
ROOM_TITLE = [tr('room')]
# 10/21 19:45 싱글팩(팩 하나로 여럿이 — GBA 두 대 코어 1.6 이 손님 GBA 를 팩 없이 켬): 손님 창 제목으로 알림(손님 화면은 'GAME BOY' 로고에서 기다림)
SINGLEPAK = {'bomber man story', 'magical quest starring mickey & minnie', 'shantae advance - risky revolution (k)'}
SINGLEPAK_TITLE = tr('singlepak')
SINGLEPAK_OPT = '/userdata/system/configs/retroarch/config/mGBA Dual/%s.opt'


def is_singlepak(rom):
    """(10/21 new10) 싱글팩 = 하드코딩 셋 또는 게임별 .opt 에 '팩 없이' 줄이 있는 게임(기기 훅 §18 이 이 줄을 지우지 않고 이어 씀) — 새 싱글팩은 .opt 한 줄로"""
    if stem(rom) in SINGLEPAK:
        return True
    try:
        with open(SINGLEPAK_OPT % os.path.splitext(os.path.basename(rom))[0], encoding='utf-8', errors='replace') as f:
            return any(l.strip() == 'mgba_dual_p2_nocart = "enabled"' for l in f)
    except OSError:
        return False
FAMILY_LABELS = (('firered', '파이어레드'), ('leaf green', '리프그린'), ('leafgreen', '리프그린'), ('emerald', '에메랄드'),
                 ('골드', '골드'), ('gold', '골드'), ('silver', '실버'), ('crystal', '크리스탈'), ('레드', '레드'), ('red (k)', '레드'),
                 ('그린', '그린'), ('green (k)', '그린'), ('블루', '블루'), ('blue (k)', '블루'), ('yellow', '옐로'),
                 ('iru no bouken', '이루'), ('ruka no tabidachi', '루카'),
                 ('aka no sho', '적의 서'), ('kuro no sho', '흑의 서'), ('jounouchi deck', '죠노우치'), ('kaiba deck', '카이바'), ('yuugi deck', '유우기'),
                 ('duel monsters ii - ', '유희왕 2'), ('duel monsters iii', '유희왕 3'), ('yu-gi-oh! duel monsters', '유희왕 1'))   # 10/21 데빌 칠드런 · 유희왕 DM4 · 1 · 2 · 3(교환)


def family_label(name):
    n = (name or '').lower()
    for k, v in FAMILY_LABELS:
        if k in n:
            return v
    return ''


def link_family(name):
    name = (name or '').lower()          # stem() 이 소문자로 돌려줌 — 묶음도 소문자로 견줌
    for i, fam in enumerate(LINK_FAMILIES):
        if name in {x.lower() for x in fam}:
            return i + 1
    return 0


def find_rooms(rom, bcast='255.255.255.255', port=PORT, wait=WAIT, core=''):
    """같은 게임 방 목록 [(ip, port, nick, content, None)] — 같은 게임 방이 하나라도 오면 바로 돌려줌.
    10/21: 같은 게임 방이 없고 짝 게임 방만 있으면 [(ip, port, nick, content, 짝 정보)](기다림 끝까지 같은 게임 방을 먼저 찾음)"""
    want = stem(rom)
    crcs = None
    pairs = []
    my_core = core
    mine = my_ips()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', 0))
        s.setblocking(False)
    except OSError as e:
        log('socket ' + str(e))
        return []
    t0 = time.monotonic()
    sent = 0
    rooms = []
    seen = set()
    direct = [ip for ip in family_ips() if ip not in mine] if bcast == '255.255.255.255' else []
    import select
    while True:
        now = time.monotonic() - t0
        while sent < len(SENDS) and now >= SENDS[sent]:
            for ip in direct:                 # 10/21 짝 기기에 직접(실패는 넘김 — 방송이 그대로 있음)
                try:
                    s.sendto(struct.pack('!I', RANQ), (ip, port))
                except OSError:
                    pass
            try:
                s.sendto(struct.pack('!I', RANQ), (bcast, port))
            except OSError as e:          # 와이파이 없음 등 → 바로 끝
                log('send ' + str(e))
                s.close()
                return []
            sent += 1
        if now >= wait:
            break
        nxt = min([SENDS[sent] for _ in [0] if sent < len(SENDS)] + [wait]) - now
        r = select.select([s], [], [], max(0.0, nxt))[0]
        if not r:
            continue
        while True:
            try:
                data, addr = s.recvfrom(2048)
            except (BlockingIOError, OSError):
                break
            if len(data) < AD.size or struct.unpack('!I', data[:4])[0] != RANS:
                if len(data) >= 4 and struct.unpack('!I', data[:4])[0] == RANS:
                    log('답 크기 다름 %d (기대 %d) %s' % (len(data), AD.size, addr[0]))
                continue
            if addr[0] in mine:
                continue
            f = AD.unpack(data[:AD.size])
            crc = f[1] & 0xffffffff
            hport = f[2]
            has_pw = f[3]
            nick = f[4].split(b'\0', 1)[0].decode('utf-8', 'replace')
            room_core = f[6].split(b'\0', 1)[0].decode('utf-8', 'replace')
            content = f[9].split(b'\0', 1)[0].decode('utf-8', 'replace')
            key = (addr[0], hport)
            if key in seen:
                continue
            seen.add(key)
            same = stem(content) == want
            if not same and crc:
                if crcs is None:
                    crcs = rom_crcs(rom)
                same = crc in crcs
            fam = False
            if not same and not has_pw:
                fam_no = link_family(want)
                if fam_no and link_family(stem(content)) == fam_no and any(k in room_core.lower() for k in LINK_FAMILY_CORES):
                    same = fam = True                # 짝 묶음: 내 롬 그대로 붙음(같은 게임 길)
                    lab = family_label(content)
                    ROOM_TITLE[0] = tr('room_family') + ('(%s)' % label(lab) if lab else '')
            pair = None if same or has_pw else pair_room(rom, my_core, room_core, content, crc)
            log('방 %s:%d nick=%s core=%s content=%s crc=%08x pw=%d → %s' % (addr[0], hport, nick, room_core, content, crc, has_pw,
                                                                         '짝 묶음' if fam else '같은 게임' if same else '짝 게임' if pair else '다른 게임'))
            if same and not has_pw:
                rooms.append((addr[0], hport, nick, content, None))
            elif pair:
                pairs.append((addr[0], hport, nick, content, pair))
        if rooms:
            break
    s.close()
    log('찾기 %.2f초 · 같은 게임 방 %d · 짝 게임 방 %d' % (time.monotonic() - t0, len(rooms), len(pairs)))
    return rooms or pairs


DS_PORT = 7063                # DSperate(melonDS LAN) 방 알림 포트 · 방은 7064
DS_WAIT = 1.1                 # DS 방장은 1초마다 알림을 보냄
DS_GROUP_MAX = 40             # DSperate lan_group_fit: 그룹은 40바이트까지(UTF-8 글자 경계)


def ds_group(rom, given=None):
    """DSperate(hbfam2)와 같은 규칙: groups.txt 그룹(--ds-group) > 롬 머리 게임 코드 4글자(0x0C) > 파일 이름(확장자 뺌)"""
    g = (given or '').strip()
    if not g:
        code = b''
        try:
            if rom.lower().endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(rom) as z:
                    cand = [i for i in z.infolist() if i.filename.lower().endswith(('.nds', '.dsi', '.srl'))] or z.infolist()[:1]
                    with z.open(cand[0]) as f:
                        code = f.read(16)[12:16]
            else:
                with open(rom, 'rb') as f:
                    code = f.read(16)[12:16]
        except (OSError, ValueError, ImportError, IndexError, RuntimeError):
            code = b''
        if len(code) == 4 and all(0x21 <= c <= 0x7e for c in code) and code != b'####':
            g = code.decode('ascii')
        else:
            g = os.path.splitext(os.path.basename(rom))[0].strip()
    return g.encode('utf-8')[:DS_GROUP_MAX].decode('utf-8', 'ignore')


def find_ds_rooms(group, port=DS_PORT, wait=DS_WAIT):
    """같은 그룹 DS 방 [(ip, 7064, 방장 이름, 방 이름)] — 하나라도 들리면 바로"""
    tag = ' [' + group + ']'
    mine = my_ips()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, 'SO_REUSEPORT'):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', port))
    except OSError as e:
        log('ds socket ' + str(e))
        return []
    import select
    t0 = time.monotonic()
    rooms, seen = [], set()
    while not rooms:
        left = wait - (time.monotonic() - t0)
        if left <= 0:
            break
        if not select.select([s], [], [], left)[0]:
            continue
        try:
            data, addr = s.recvfrom(256)
        except OSError:
            continue
        if len(data) < 78 or addr[0] in mine:
            continue
        name = data[12:76].split(b'\0', 1)[0].decode('utf-8', 'replace')
        nump, maxp = data[76], data[77]
        if (addr[0], name) not in seen:
            seen.add((addr[0], name))
            same = name.endswith(tag)
            log('DS 방 %s "%s" %d/%d → %s' % (addr[0], name, nump, maxp, '같은 그룹' if same else '다른 그룹'))
            if same and (maxp == 0 or nump < maxp):
                i = name.rfind("'s game")
                rooms.append((addr[0], 7064, name[:i] if i > 0 else name, name))
    s.close()
    log('DS 찾기 %.2f초 · 그룹 %s · 같은 그룹 방 %d' % (time.monotonic() - t0, group, len(rooms)))
    return rooms


class Screen(object):
    """화면 두 장(fb0)을 통째로 기억했다가 창을 그리고, 끝나면 되돌림"""

    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.saved = f.read(HALF * 2)
        if len(self.saved) < HALF * 2:
            self.saved = self.saved + bytes(HALF * 2 - len(self.saved))

    def shown(self):
        y = 0
        try:
            with open('/sys/class/graphics/fb0/pan') as f:
                y = int(f.read().strip().split(',')[1])
        except (OSError, ValueError, IndexError):
            pass
        off = HALF if y >= H else 0
        return self.saved[off:off + HALF]

    def put(self, frame):
        with open(self.path, 'r+b') as f:
            f.write(frame)
            f.write(frame)

    def restore(self):
        with open(self.path, 'r+b') as f:
            f.write(self.saved)


def make_painter(screen):
    """Pixel-style window (stepped corners, 2-dot pixels). Neutral palette for the public version;
    labels and pictures are centred on their real ink box. Falls back to a system font when the
    Galmuri pixel fonts (OFL) are not in FONT_DIR."""
    from PIL import Image, ImageDraw, ImageFont
    bg = Image.frombytes('RGBA', (W, H), screen.shown(), 'raw', 'BGRA').convert('RGB')
    bg = Image.blend(bg, Image.new('RGB', (W, H), (8, 10, 16)), 0.62)
    S = 2                                       # 픽셀 한 칸 = 화면 2점

    def font(name, size, old_size):
        try:
            return ImageFont.truetype(os.path.join(FONT_DIR, name), size), True
        except OSError:
            for p in (FONT,) + FALLBACK_FONTS:
                try:
                    return ImageFont.truetype(p, old_size), False
                except OSError:
                    pass
            return ImageFont.load_default(), False

    f_title, pixel = font(TITLE_FONT[0], TITLE_FONT[1], 28)
    f_host = font('Galmuri11.ttf', 24, 22)[0]
    f_btn = font('Galmuri11-Bold.ttf', 24, 24)[0]
    f_key = font(KEY_FONT[0], KEY_FONT[1], 18)[0]
    f_small = font(SMALL_FONT[0], SMALL_FONT[1], 18)[0]
    LINE = (8, 10, 16)                          # outline / text edge
    FRAME, FRAME_D = (96, 165, 250), (37, 99, 235)
    TEXT_HI, MUTE = (241, 245, 249), (148, 163, 184)
    PANEL, PANEL_HI = (30, 36, 48), (51, 60, 77)
    SHADOW = (3, 4, 8)
    BTN_A = ((96, 165, 250), (147, 197, 253), (37, 99, 235), (8, 18, 40))     # face · top light · bottom shade · label
    BTN_B = ((71, 85, 105), (100, 116, 139), (45, 55, 72), TEXT_HI)
    SPARKLE = False                             # no '+' sparkles in the neutral look
    X0, Y0, X1, Y1 = 72, 116, 568, 380         # 창 [X0, X1) x [Y0, Y1) — 로고 아래 ~ '+ 로딩 중 +' 위
    CX = (X0 + X1) // 2
    BW, BH, BY = 208, 62, Y0 + 124             # 단추 크기 · 위치(앞면 27칸 = 그림 17칸 + 위아래 5칸씩)
    boxes = {}

    def box(d, a, b, c, e, fill, cut=1):
        """Box [a, c) x [b, e) with corners cut into `cut` pixel steps"""
        d.rectangle((a, b + cut * S, c - 1, e - cut * S - 1), fill=fill)
        for i in range(cut):
            k = (cut - i) * S
            d.rectangle((a + k, b + i * S, c - k - 1, b + (i + 1) * S - 1), fill=fill)
            d.rectangle((a + k, e - (i + 1) * S, c - k - 1, e - i * S - 1), fill=fill)

    def inkbox(d, text, f):
        """Real ink box (l, t, r, b) of the text, measured by drawing it alone; r, b are exclusive"""
        k = (id(f), text)
        if k not in boxes:
            l, t, r, b = d.textbbox((0, 0), text, font=f)
            m = Image.new('L', (r - l + 8, b - t + 8), 0)
            dm = ImageDraw.Draw(m)
            dm.fontmode = d.fontmode
            dm.text((4 - l, 4 - t), text, font=f, fill=255)
            q = m.getbbox() or (4, 4, 4, 4)
            boxes[k] = (q[0] - 4 + l, q[1] - 4 + t, q[2] - 4 + l, q[3] - 4 + t)
        return boxes[k]

    def at_center(d, x, y, text, f):
        """Text position that puts the centre of its ink box at (x, y)"""
        l, t, r, b = inkbox(d, text, f)
        return int(round(x - (r + l) / 2)), int(round(y - (b + t) / 2))

    def ink(d, xy, text, f, fill, edge=None):
        if edge:                                # 로고 글자처럼 둘레 한 칸 테 + 아래로 한 칸 더
            x, y = xy
            for dx in (-S, 0, S):
                for dy in (-S, 0, S, 2 * S):
                    if dx or dy:
                        d.text((x + dx, y + dy), text, font=f, fill=edge)
        d.text(xy, text, font=f, fill=fill)

    def fit(d, text, f, maxw):
        if d.textlength(text, font=f) <= maxw:
            return text
        while text and d.textlength(text + '…', font=f) > maxw:
            text = text[:-1]
        return text + '…'

    def plus(d, x, y, n=2):
        """'+' sparkle centred at (x, y), arms n pixels long (off in the neutral look)"""
        if not SPARKLE:
            return
        a, b = int(round(x - S / 2)), int(round(y - S / 2))
        d.rectangle((a - n * S, b, a + (n + 1) * S - 1, b + S - 1), fill=FRAME)
        d.rectangle((a, b - n * S, a + S - 1, b + (n + 1) * S - 1), fill=FRAME)

    ROWS = BADGE
    KD = len(ROWS)                              # 단추 그림 지름(칸)

    def badge(d, a, b, letter, ring, fill, letter_ink):
        """Pad button badge: KD x KD pixel circle at (a, b) with its letter centred"""
        c = KD // 2
        for j, h in enumerate(ROWS):
            x, y = a + (c - h) * S, b + j * S
            d.rectangle((x, y, x + (2 * h + 1) * S - 1, y + S - 1), fill=ring)
            if 0 < j < len(ROWS) - 1:
                w = min(h - 1, ROWS[j - 1], ROWS[j + 1])
                x = a + (c - w) * S
                d.rectangle((x, y, x + (2 * w + 1) * S - 1, y + S - 1), fill=fill)
        d.text(at_center(d, a + KD * S / 2, b + KD * S / 2, letter, f_key), letter, font=f_key, fill=letter_ink)

    def button(d, bx, key, label, colors, kfill, kink):
        base, hi, dk, txt = colors
        box(d, bx + S, BY + 2 * S, bx + BW + S, BY + BH + 2 * S, SHADOW, 2)
        box(d, bx, BY, bx + BW, BY + BH, LINE, 2)
        box(d, bx + S, BY + S, bx + BW - S, BY + BH - S, dk, 1)
        box(d, bx + S, BY + S, bx + BW - S, BY + BH - 3 * S, base, 1)
        d.rectangle((bx + 3 * S, BY + S, bx + BW - 3 * S - 1, BY + 2 * S - 1), fill=hi)
        # 앞면 = [bx+S, bx+BW-S) x [BY+S, BY+BH-3S) — 단추 그림 + 글자 묶음을 이 가운데로
        fx, fy = bx + BW / 2, BY + S + (BH - 4 * S) / 2
        l, t, r, b = inkbox(d, label, f_btn)
        kw, gap = KD * S, 5 * S
        if (int(BW - 2 * S - (kw + gap + r - l)) // S) % 2:
            gap += S                            # 양쪽 여백이 같은 칸 수가 되게
        gx = int(round(fx - (kw + gap + r - l) / 2))
        badge(d, gx, int(round(fy - kw / 2)), key, LINE, kfill, kink)
        d.text((gx + kw + gap - l, int(round(fy - (b + t) / 2))), label, font=f_btn, fill=txt)

    def paint(host, left, title=None):
        im = bg.copy()
        d = ImageDraw.Draw(im)
        if pixel:
            d.fontmode = '1'                    # 픽셀 글꼴은 번지지 않게
        box(d, X0 + 2 * S, Y0 + 3 * S, X1 + 2 * S, Y1 + 3 * S, SHADOW, 3)   # 그림자
        box(d, X0, Y0, X1, Y1, LINE, 3)
        box(d, X0 + S, Y0 + S, X1 - S, Y1 - S, FRAME, 2)
        box(d, X0 + 3 * S, Y0 + 3 * S, X1 - 3 * S, Y1 - 3 * S, FRAME_D, 1)
        box(d, X0 + 4 * S, Y0 + 4 * S, X1 - 4 * S, Y1 - 4 * S, PANEL, 1)
        d.rectangle((X0 + 5 * S, Y0 + 4 * S, X1 - 5 * S - 1, Y0 + 5 * S - 1), fill=PANEL_HI)
        plus(d, X0 + 14 * S, Y0 + 14 * S)
        plus(d, X1 - 14 * S, Y0 + 14 * S)
        title = fit(d, title or ROOM_TITLE[0], f_title, (X1 - X0) - 48)
        ink(d, at_center(d, CX, Y0 + 44, title, f_title), title, f_title, TEXT_HI, LINE)
        # '방장 OO' — 이름만 금색, 길면 … 로 줄임
        name = fit(d, host, f_host, (X1 - X0) - 160)
        lab, gap = tr('host'), 6 * S
        wl = d.textlength(lab, font=f_host)
        ll, rn = inkbox(d, lab, f_host)[0], inkbox(d, name, f_host)[2]
        hx = int(round(CX - (ll + wl + gap + rn) / 2))      # '방장' 첫 점 ~ 이름 끝 점의 가운데 = 창 가운데
        hy = at_center(d, 0, Y0 + 86, lab + name, f_host)[1]
        ink(d, (hx, hy), lab, f_host, MUTE)
        ink(d, (int(round(hx + wl + gap)), hy), name, f_host, FRAME, LINE)
        button(d, CX - 10 * S - BW, 'A', tr('join'), BTN_A, (239, 246, 255), (8, 18, 40))
        button(d, CX + 10 * S, 'B', tr('solo'), BTN_B, (51, 60, 77), TEXT_HI)
        msg = left if isinstance(left, str) else tr('left') % left
        msg = fit(d, msg, f_small, (X1 - X0) - 40)
        my = Y1 - 42
        d.text(at_center(d, CX, my, msg, f_small), msg, font=f_small, fill=MUTE)
        l, t, r, b = inkbox(d, msg, f_small)
        if r - l <= 400:                        # 긴 알림 줄은 반짝이가 창 밖으로 나가서 뺌
            plus(d, CX - (r - l) / 2 - 10 * S, my)
            plus(d, CX + (r - l) / 2 + 10 * S, my)
        return im

    def frame(host, left, title=None):
        return paint(host, left, title).convert('RGBA').tobytes('raw', 'BGRA')

    frame.png = paint
    return frame


def splash_pids():
    out = []
    me = os.getpid()
    for d in os.listdir('/proc'):
        if not d.isdigit() or int(d) == me:
            continue
        try:
            with open('/proc/%s/cmdline' % d, 'rb') as f:
                c = f.read()
            if b'hb_gamesplash.py' in c and b'python' in c:
                out.append(int(d))
        except OSError:
            pass
    return out


def ws_has_save(core, rom):
    """10/21 원더스완: 롬 끝 머리 세이브 칸(끝에서 5번째 바이트)이 0 이면 세이브 없는 게임 → False(각자 세이브 안 보냄).
    GBA · 못 읽으면 True(지금처럼 보냄)."""
    if core != 'mednafen_wswan_dual':
        return True
    try:
        tail = b''
        if rom.lower().endswith('.zip'):
            import zipfile
            with zipfile.ZipFile(rom) as z:
                items = [i for i in z.infolist() if not i.is_dir()]
                if len(items) != 1:
                    return True
                with z.open(items[0]) as f:
                    while True:
                        b = f.read(1 << 20)
                        if not b:
                            break
                        tail = (tail + b)[-16:]
        else:
            with open(rom, 'rb') as f:
                f.seek(-16, 2)
                tail = f.read(16)
        if len(tail) < 16:
            return True
        if tail[-5] == 0:
            log('세이브 없는 게임(롬 머리) → 각자 세이브 안 보냄 · 보통 접속')
            return False
        return True
    except Exception as e:
        log('롬 머리 못 읽음 %r → 평소대로' % (e,))
        return True


def ask(host, args):
    """창을 띄우고 A/B 를 기다림 → True(같이) / False(혼자)"""
    fbpath = args.fake_fb or '/dev/fb0'
    stopped = []
    if not args.fake_fb:
        for pid in splash_pids():
            try:
                os.kill(pid, signal.SIGSTOP)
                stopped.append(pid)
            except OSError:
                pass
    try:
        screen = Screen(fbpath)
        frame = make_painter(screen)
        pair = getattr(args, 'pair', None)
        title = PAIR_TITLE % (pair['host_label'], pair['my_label']) if pair else None
        if args.png:
            frame.png(host, ASK_SEC, title).save(args.png)
        if args.fake_keys:
            sys.path.insert(0, CLAUDE)
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import hb_osd as HO
            keys = HO.FakeKeys(args.fake_keys)
        else:
            sys.path.insert(0, CLAUDE)
            import hb_osd as HO
            keys = HO.EvdevKeys([A_KEY, B_KEY])
        try:
            os.remove(PRESS)   # 지난 시험이 남긴 시험 파일이 같이하기 창을 저절로 고르지 않게(창이 뜬 뒤에 쓴 것만 셈)
        except OSError:
            pass
        t0 = time.monotonic()
        held = set()           # 창 뜨기 전부터 눌려 있던 키
        left_shown = None
        choice = False
        while True:
            el = time.monotonic() - t0
            left = max(0, ASK_SEC - int(el))
            if left != left_shown:
                screen.put(frame(host, left, title))
                left_shown = left
            if el >= ASK_SEC:
                log('시간 끝 → 혼자')
                break
            done = False
            # 10/20 21:0x 시험 길: 시험 도구(pk2)의 단추는 이 창이 읽는 진짜 패드 장치에 안 닿아서, /tmp/hb_joinask.press 에 'A' 나 'B' 를 쓰면 그 단추로 봄(읽고 지움)
            try:
                with open(PRESS) as pf:
                    pv = pf.read().strip().upper()
                os.remove(PRESS)
                if pv in ('A', 'B') and el >= IGNORE_SEC:
                    choice = pv == 'A'
                    log('고름(시험 파일) ' + ('A 같이' if choice else 'B 혼자'))
                    break
            except OSError:
                pass
            for code, val in keys.poll(0.05):
                if code not in (A_KEY, B_KEY):
                    continue
                if val == 0:
                    held.discard(code)
                    continue
                if val == 2 or el < IGNORE_SEC:
                    held.add(code)
                    continue
                if code in held:
                    continue
                choice = code == A_KEY
                log('고름 ' + ('A 같이' if choice else 'B 혼자'))
                done = True
                break
            if done:
                break
        # 고른 키를 놓을 때까지 잠깐(최대 0.5초) 기다림 → 레트로아크가 켜지며 A 를 받지 않게
        t1 = time.monotonic()
        while time.monotonic() - t1 < 0.5:
            evs = keys.poll(0.05)
            if any(c in (A_KEY, B_KEY) and v == 0 for c, v in evs):
                break
        if choice and pair:
            # 10/21 짝 게임: 내 게임(B) 세이브 + 2P 롬을 보냄. 받음 확인이 없으면 콘텐츠 A 로 붙지 않고 혼자 하기(B)
            screen.put(frame(host, '세이브 보내는 중', title))
            if args.core not in OWNSAVE_CORES:     # 10/21 다른 코어로 켠 짝 손님: 훅이 두 대 코어 때 하던 시작 정리(지난 거래 마무리 · 램 정리)
                try:
                    import hb_ownsave as own
                    own.prepare_start(args.system, args.rom)
                except Exception as e:
                    log('짝 손님 시작 정리 못 함 %r' % (e,))
            args.ownsave_result = send_ownsave(args.system, args.rom, *args.ownsave_room, content=pair['content'])
            if not args.ownsave_result.get('ok'):
                screen.put(frame(host, PAIR_NOTICE_LINE, PAIR_NOTICE_TITLE))
                time.sleep(NOTICE_SEC)
                choice = False
        elif choice and not args.ds and args.core in OWNSAVE_CORES and ws_has_save(args.core, args.rom):
            screen.put(frame(host, '세이브 보내는 중'))
            args.ownsave_result = send_ownsave(args.system, args.rom, *args.ownsave_room)
            if not args.ownsave_result.get('ok'):
                # 10/21 R07: 못 보냈거나 받음 확인을 못 받음 → 2초 알림 뒤 보통 접속(이번 판 2P 진행은 되쓰지 않음)
                screen.put(frame(host, NOTICE_LINE, NOTICE_TITLE))
                time.sleep(NOTICE_SEC)
        screen.restore()
        return choice
    finally:
        for pid in stopped:
            try:
                os.kill(pid, signal.SIGCONT)
            except OSError:
                pass


def send_ownsave(system, rom, ip, port, content=None):
    """A를 고른 길과 VM 시험이 함께 쓰는 전송 함수. content = 짝 게임일 때 방장 게임 A 의 이 기기 경로."""
    try:
        import hb_ownsave as own
        if content is None:
            result = own.send_save(system, rom, ip, port)
            log('자기 세이브 ' + ('받음' if result['ok'] else '실패 → 보통 접속') +
                ' %.3f초' % result['elapsed'])
        else:
            result = own.send_save(system, rom, ip, port, content=content)
            log('짝 게임 세이브 · 2P 롬 ' + ('받음' if result['ok'] else '실패 → 혼자 하기 (%s)' % result.get('reason')) +
                ' %.3f초' % result['elapsed'])
        return result
    except Exception as error:
        log('자기 세이브 오류 → 보통 접속 ' + repr(error))
        return {'ok': False, 'reason': str(error)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('system')
    ap.add_argument('rom')
    ap.add_argument('--core', default='')
    ap.add_argument('--bcast', default='255.255.255.255')
    ap.add_argument('--port', type=int, default=PORT)
    ap.add_argument('--fake-fb')
    ap.add_argument('--fake-keys')
    ap.add_argument('--png')
    ap.add_argument('--find-only', action='store_true')
    ap.add_argument('--ds', action='store_true', help='DS 같이하기(DSperate) 방 알림을 들음')
    ap.add_argument('--ds-group', help='groups.txt 의 그룹(없으면 롬 게임 코드)')
    ap.add_argument('--ds-port', type=int, default=DS_PORT)
    args = ap.parse_args()
    if not args.ds:
        for path in (OUT, P2ROM):        # 10/21: 지난 짝 게임 2P 롬 표시도 지움
            try:
                os.unlink(path)
            except OSError:
                pass
    if turned_off():
        return 1
    t0 = time.monotonic()
    if args.ds:
        rooms = [r + (None,) for r in find_ds_rooms(ds_group(args.rom, args.ds_group), args.ds_port)]
    else:
        rooms = find_rooms(args.rom, args.bcast, args.port,
                           core=args.core if args.system in ('gba', 'ngp', 'ngpc', 'wswan', 'wswanc') else '')
    if args.find_only:
        print(json.dumps(rooms, ensure_ascii=False))
        return 0 if rooms else 1
    if not rooms:
        return 1
    ip, port, nick, content, args.pair = rooms[0]
    if not args.ds and not args.pair and is_singlepak(args.rom):
        ROOM_TITLE[0] = SINGLEPAK_TITLE
    args.ownsave_room = (ip, port)
    host = family_name(ip) or FAMILY.get(nick.strip().lower()) or nick or ip.rsplit('.', 1)[-1]
    log('창: %s %s 방장=%s (%s:%d)' % (args.system, os.path.basename(args.rom), host, ip, port))
    try:
        together = ask(host, args)
    except Exception as e:           # 창이 안 되면 혼자(평소대로) — 게임 켜기를 막지 않음
        log('창 오류 %r → 혼자' % (e,))
        return 1
    if not together:
        return 2
    if args.ds:
        print(ip)
        log('DS 같이 → %s (%.1f초)' % (ip, time.monotonic() - t0))
        return 0
    record = {'rom': args.rom, 'ip': ip, 'port': port, 'nick': nick, 'host': host, 't': time.time()}
    if args.pair:
        # 10/21 짝 게임: 콘텐츠 = 방장 게임 A(내 기기 경로), 2P = 내 게임 B. 코어가 읽는 2P 롬 · 화면 파일을 json 보다 먼저.
        p2 = args.rom
        if args.pair.get('kind') in (2, 3):
            # 10/22 네오지오 · 10/26 원더스완: 코어가 ZIP 을 못 읽음 — /tmp 에 푼 보통 파일 경로(못 풀면 혼자 하기)
            try:
                import hb_ownsave as own
                p2 = own.p2rom_for_core(args.pair['kind'], args.rom)
            except Exception as e:
                log('짝 2P 롬 못 풂 %r → 혼자' % (e,))
                return 2
        write_atomic(P2ROM, p2 + '\n')
        write_atomic(SCREEN, '2P\n')
        record.update(rom=args.pair['content'], p2rom=args.rom, launched=args.rom, pair=True)
        dual_core = next((d for _, _, k, d in PAIR_SYSTEMS if k == args.pair.get('kind', 1)), 'mgba_dual')
        if args.core != dual_core:
            record['core'] = dual_core       # 10/21 켜기 코드가 이 판만 두 대 코어로(평소 gpSP · 순정 네오지오 등)
    write_atomic(OUT, json.dumps(record, ensure_ascii=False))
    log('같이 → %s:%d%s (%.1f초)' % (ip, port, ' 짝 게임 콘텐츠 %s · 2P %s' % (
        os.path.basename(args.pair['content']), os.path.basename(args.rom)) if args.pair else '', time.monotonic() - t0))
    return 0


def write_atomic(path, text):
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        f.write(text)
    os.replace(tmp, path)


if __name__ == '__main__':
    sys.exit(main())
