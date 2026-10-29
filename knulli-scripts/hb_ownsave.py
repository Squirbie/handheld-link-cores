#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# hb_ownsave.py - Per-player saves for the dual-console link cores: the guest's own save plays in the host's P2 slot and goes back to the guest afterwards.
"""hb_ownsave.py — '각자 자기 세이브'(GBA Dual · 원더스완 Dual 같이하기) 4판 (10/21)
기기: /userdata/system/claude/hb_ownsave.py

흐름
1) 손님이 같이하기 창에서 A → send_save(): 자기 원본 세이브를 카드의 거래 폴더(original.bin)에 먼저 남기고 확인한 뒤
   방장(넷플레이 포트 + 1)으로 보냄. 방장 코어가 2P 세이브만 바꾸고 표(16바이트)로 받음을 알리면
   거래 폴더 sent.json 에 ack 를 적고 /tmp/hb_ownsave/intent 를 남김 → 손님 코어가 켤 때 이 거래에 묶임.
2) 손님 코어는 레트로아크 기록에서 '2 플레이어로 입장'을 확인한 경우에만 2P 세이브를
   거래 폴더에 남김: 중간 저장 checkpoint.bin(2P 세이브가 바뀐 뒤 300장 그대로) · 정상 종료 export.bin.
3) 게임 끝 훅(finish)·다음 게임 시작 훅(start)이 거래를 마무리: 표 · 롬 CRC · 2P 역할 · CRC32 · SHA-256 이 맞고
   지금 원본이 보낼 때와 같으면 원본을 <세이브>.srm.bak_link 로 남긴 뒤 결과로 바꿈(같은 결과면 다시 쓰지 않음).
   실패하면 거래 자료를 지우지 않고 다음 번에 다시. 보낸 뒤 원본이 바뀌었으면 '어긋남'으로 얼려 둠(자동 적용 안 함).

카드 거래 폴더: /userdata/saves/<기종>/.hb_ownsave/<세이브 파일 이름>/<표 32자>/
  sent.json · original.bin · checkpoint.bin · export.bin · done.json(적용) · closed.json(결과 없음) · conflict.json(어긋남)
  끝난 거래는 세이브마다 최근 3개만 둠(원본 사본 포함). 어긋난 거래는 지우지 않음.
램: /tmp/hb_ownsave (core · pair · request · ack · reject · intent · sent.json · export · guest)
기록: /tmp/hb_ownsave_finish.log (256KiB 넘으면 .1 로 돌림)
명령: start|finish|recover|ophdr <기종> <롬 경로> · clear

5판(10/21, GBA 두 대 코어 1.5 와 함께) — 짝 게임(다른 판끼리, GBA 만)
- 짝 표(PAIRS, 기기 롬 이름): 방장 방 게임 A 와 손님이 켠 게임 B 가 짝이면 손님은 B 세이브 + 2P 롬(B 경로 · CRC)을 보냄.
  머리 crc = A(콘텐츠) CRC, p2rom/p2crc = B. 거래(sent.json)의 crc 는 B(되쓰기 확인은 손님 자기 게임 롬 CRC 로).
- 방장은 자기 롬 폴더의 같은 이름 B 를 읽어 CRC 가 같고 코어가 짝을 알아들을 때(램 pair 파일)만 HBQ4 요청 →
  코어가 2P 롬을 바꾸고 손님 세이브를 넣음. 아니면 {"ok": false, "reason"} 로 바로 거절(손님 창이 알림 뒤 혼자 하기).
- 손님 도우미(hb_joinask)는 받음 확인 뒤 /tmp/hb_dual_p2rom(B 경로)을 쓰고 콘텐츠 A 로 손님 레트로아크를 켬.
- 짝이 아니면(머리에 p2rom 없음) 4판과 같은 길 · 같은 바이트.

6판(10/22, 네오지오 포켓 · 게임기어 두 대 코어 1.1-os4 와 함께) — 기종 둘 더
- 네오지오 포켓(기종 3, 시스템 ngp · ngpc): 세이브 = <롬 이름>.flash(코어가 직접 쓰는 원래 꼴 — 머리 0x0053 · 블록 수 · 길이),
  2P 칸 = <롬 이름>.p2.flash. 손님 세이브가 없으면 0바이트(새 카트). 짝 게임(카드 파이터즈 SNK판 ↔ 캡콤판 ·
  다이브 얼럿 베키 ↔ 매트) 도 GBA 와 같은 길이지만 코어가 ZIP 을 못 읽어 2P 롬은 /tmp 에 푼 보통 파일로 줌
  (방장: /tmp/hb_ownsave/p2rom.ngc · 손님: /tmp/hb_ngp_dual_p2rom.ngc 를 /tmp/hb_dual_p2rom 에 적음).
- 게임기어(기종 4, 시스템 gamegear): 세이브 = <롬 이름>.srm(레트로아크가 쓰는 길이 = 마지막 0xFF 아닌 바이트까지, 64KB 까지),
  2P 칸 = <롬 이름>.p2.sav. 짝 게임 없음.
- GBA · 원더스완 은 5판과 같은 길 · 같은 바이트.

7판(10/26, 원더스완 두 대 코어 1.9-os4 와 함께) — 원더스완 짝 게임
- 명탐정 코난 08(황혼의 황녀, 컬러 · roms/wswanc) ↔ 06(서쪽의 명탐정, 흑백 · roms/wswan): 다른 시스템 폴더라
  짝 롬은 내 폴더 + 짝 폴더(wswan ↔ wswanc)에서 찾음(partner_file). 코어가 ZIP 을 못 읽어 네오지오처럼 /tmp 에 푼 보통 파일
  (방장: /tmp/hb_ownsave/p2rom.ws · 손님: /tmp/hb_ws_dual_p2rom.ws 를 /tmp/hb_dual_p2rom 에 적음).
- 짝이 아니면 6판과 같은 길 · 같은 바이트.
"""
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import time
import zlib

ROOT = Path(os.environ.get("HB_OWNSAVE_TMP", "/tmp/hb_ownsave"))
SAVES = Path(os.environ.get("HB_OWNSAVE_SAVES", "/userdata/saves"))
LOG = Path(os.environ.get("HB_OWNSAVE_LOG", str(ROOT.parent / "hb_ownsave_finish.log")))
LIMIT = 131072
PROTOCOL = 3
REQUEST = struct.Struct("<4sIIIIQ16s8s")       # HBQ3 pid crc 크기 포트 기한(ms) 표 방세대 = 52바이트
REQUEST4 = struct.Struct("<4sIIIIQ16s8sII4x")  # HBQ4 = HBQ3 + 2P 롬 CRC · 경로 길이 · 0 = 64바이트 (뒤에 경로 · 세이브)
P2ROM = Path(os.environ.get("HB_DUAL_P2ROM", "/tmp/hb_dual_p2rom"))
PAIR_PATH_MAX = 1023
# 짝 게임(다른 판끼리 케이블): 기기 롬 이름(확장자 뺌) · 창에 쓰는 짧은 이름. 이름은 대소문자 무시.
# 포켓몬 파이어레드 · 리프그린 · 에메랄드는 gpSP 무선이라 이번엔 넣지 않음.
PAIRS = (
    (("Mega Man - Battle Network 3 - Blue Version", "블랙"), ("Mega Man - Battle Network 3 - White Version", "화이트")),
    (("Mega Man - Battle Network 4 - Red Sun", "레드 선"), ("Mega Man - Battle Network 4 - Blue Moon", "블루 문")),
    (("Rockman EXE 5 - Team of Blues (K)", "블루스"), ("Rockman EXE 5 - Team of Colonel (K)", "커널")),
    (("Mega Man - Battle Network 5 - Team Protoman", "프로토맨"), ("Mega Man - Battle Network 5 - Team Colonel", "컬로넬")),
    (("Mega Man - Battle Network 6 - Cybeast Gregar", "그레이거"), ("Mega Man - Battle Network 6 - Cybeast Falzar", "팔저")),
    (("Bomberman Max 2 - Blue Advance", "블루"), ("Bomberman Max 2 - Red Advance", "레드")),
    (("Pokemon - Ruby Version", "루비"), ("Pocket Monsters - Sapphire", "사파이어")),
    # 10/21 3세대 케이블 짝: 루비 · 사파이어 방장(두 대 코어) ↔ 에메랄드 · 파이어레드 · 리프그린 손님(짝일 때만 두 대 코어) · 새 이름도
    (("Pokemon - Ruby (K)", "루비"), ("Pokemon - Sapphire (K)", "사파이어")),
    (("Pokemon - Ruby Version", "루비"), ("Pocket Monsters - Emerald", "에메랄드")),
    (("Pokemon - Ruby (K)", "루비"), ("Pokemon - Emerald (K)", "에메랄드")),
    (("Pokemon - Ruby Version", "루비"), ("Pocket Monsters - FireRed", "파이어레드")),
    (("Pokemon - Ruby (K)", "루비"), ("Pokemon - FireRed (K)", "파이어레드")),
    (("Pokemon - Ruby Version", "루비"), ("Pocket Monsters - Leaf Green", "리프그린")),
    (("Pokemon - Ruby (K)", "루비"), ("Pokemon - LeafGreen (K)", "리프그린")),
    (("Pocket Monsters - Sapphire", "사파이어"), ("Pocket Monsters - Emerald", "에메랄드")),
    (("Pokemon - Sapphire (K)", "사파이어"), ("Pokemon - Emerald (K)", "에메랄드")),
    (("Pocket Monsters - Sapphire", "사파이어"), ("Pocket Monsters - FireRed", "파이어레드")),
    (("Pokemon - Sapphire (K)", "사파이어"), ("Pokemon - FireRed (K)", "파이어레드")),
    (("Pocket Monsters - Sapphire", "사파이어"), ("Pocket Monsters - Leaf Green", "리프그린")),
    (("Pokemon - Sapphire (K)", "사파이어"), ("Pokemon - LeafGreen (K)", "리프그린")),
    (("Tennis no Ouji-sama 2003 Cool Blue", "쿨 블루"), ("Tennis no Ouji-sama 2003 Passion Red", "패션 레드")),   # 10/21 tennis
    (("Medabots AX - Metabee Ver", "카부토"), ("Medabots AX - Rokusho Ver", "쿠와가타")),   # 10/21 mdax
    (("Medabots - Metabee", "카부토"), ("Medabots - Rokusho", "쿠와가타")),   # 10/21 mdb
    # 10/22 네오지오 포켓(두 대 코어 1.1-os4): 다른 판끼리 케이블 — 카드 교환 · 대전, 잠수함 교환
    (("SNK vs. Capcom - Card Fighters' Clash - SNK Version", "SNK판"),
     ("SNK vs. Capcom - Card Fighters' Clash - Capcom Version", "캡콤판")),
    (("Dive Alert - Becky's Version", "베키판"), ("Dive Alert - Matt's Version", "매트판")),
    # 10/26 원더스완(두 대 코어 1.9-os4): 전작 데이터 보내기(06 → 08, 06 은 켤 때 단추 누름 — 게임별 옵션 wswan_dual_pair_hold)
    (("Meitantei Conan Yuugure no Koujo (k)", "황혼의 황녀"),
     ("Meitantei Conan Nishi no Meitantei Saidai no Kiki! (k)", "서쪽의 명탐정")),
)
PAIR_REJECT = {1: "방장 기기에서 2P 롬을 못 읽음", 2: "2P 롬 CRC 가 방장 것과 다름", 3: "2P 롬이 1P 와 같은 롬",
               4: "방장 코어가 2P 게임기를 못 켬"}
EXPORT = struct.Struct("<4sIII16sIII")         # 종류 CRC 기종 크기 표 장 역할 세이브CRC32 = 44바이트
KINDS = {"gba": 1, "wswan": 2, "wswanc": 2, "ngp": 3, "ngpc": 3, "gamegear": 4}
ROM_EXTS = {1: (".gba",), 2: (".ws", ".wsc", ".pc2"), 3: (".ngc", ".ngp", ".npc"), 4: (".gg", ".sms")}
SAVE_EXT = {1: ".srm", 2: ".srm", 3: ".flash", 4: ".srm"}           # 6판: 네오지오는 코어가 쓰는 .flash
P2_EXT = {1: ".p2.srm", 2: ".p2.sav", 3: ".p2.flash", 4: ".p2.sav"}  # 코어의 방장 2P 칸 이름
PAIR_KINDS = (1, 2, 3)                                              # 짝 게임(HBQ4)을 쓰는 기종: GBA · 원더스완(7판) · 네오지오
GG_MAX = 0x10000
NGP_P2ROM_HOST = ROOT / "p2rom.ngc"                                # 6판: 방장 코어에 줄 2P 짝 롬(푼 보통 파일)
NGP_P2ROM_GUEST = Path(os.environ.get("HB_NGP_P2ROM", "/tmp/hb_ngp_dual_p2rom.ngc"))
WS_P2ROM_HOST = ROOT / "p2rom.ws"                                  # 7판: 방장 원더스완 코어에 줄 2P 짝 롬(푼 보통 파일)
WS_P2ROM_GUEST = Path(os.environ.get("HB_WS_P2ROM", "/tmp/hb_ws_dual_p2rom.ws"))
WS_FOLDERS = ("wswan", "wswanc")                                   # 7판: 원더스완 짝은 두 시스템 폴더를 오감
GBA_SIZES = (512, 8192, 32768, 65536, 131072)
# 원피스 그랜드 배틀 스완 콜로세움: 롬 내용 CRC 로만 알아봄(이름 안 봄)
ONEPIECE_CRCS = {
    0x912BDE83: "From TV Animation One Piece - Grand Battle Swan Colosseum (Japan) (K MARK106) — 시험 롬, VM 시험",
    0xF8A1DD2B: "From TV Animation One Piece - Grand Battle Swan Colosseum (Japan) — 원판, 10/20 맥 통신 시험",
}
HEADER = bytes.fromhex(
    "10101120120000010060166005700680079008a009b00ac00bd00ce00df00e"
    "ffffffff000000ffffff03000000b009c00a")
HEADER_AT = 0x0F
ONEPIECE_SIZE = 32768
KEEP_FINISHED = 3
LOG_LIMIT = 256 * 1024
SEND_LIMIT = 3.8          # 창이 기다리는 가장 긴 시간(초)
TOKEN_RE = re.compile(r"[0-9a-f]{32}")


class Conflict(Exception):
    """보낸 뒤 원본이 바뀜 등 — 자동 적용하지 않고 얼려 둠"""


class PairRefused(ValueError):
    """5판 방장: 짝 요청 거절 — 손님에게 까닭을 돌려줌"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def log_line(path, message):
    """최신 기록 256KiB 와 직전 256KiB(.1)만 둔다."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size >= LOG_LIMIT:
            os.replace(path, str(path) + ".1")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(time.strftime("%m-%d %H:%M:%S ") + str(message)[:4000] + "\n")
    except OSError:
        pass


def read_regular(path, limit=LIMIT):
    """심볼릭 링크 · 장치 · 파이프를 세이브로 읽지 않는다."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError("보통 파일이 아니거나 크기 초과: %s" % path)
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError("읽는 동안 크기 초과: %s" % path)
        return data


def read_optional(path, limit=LIMIT):
    try:
        return read_regular(path, limit)
    except FileNotFoundError:
        return None


UNSUPPORTED = (errno.EINVAL, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS)


def sync_directory(path):
    """폴더 동기화. '지원 안 함'만 syncfs 로 대신한다(EIO·ENOSPC·EROFS 는 그대로 실패)."""
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            os.fsync(fd)
            return "directory_fsync"
        except OSError as error:
            if error.errno not in UNSUPPORTED:
                raise
            import ctypes
            libc = ctypes.CDLL(None, use_errno=True)
            if not hasattr(libc, "syncfs"):
                raise OSError(errno.ENOTSUP, "폴더 동기화를 대신할 syncfs 없음")
            if libc.syncfs(fd):
                code = ctypes.get_errno()
                raise OSError(code, os.strerror(code))
            return "syncfs"
    finally:
        os.close(fd)


def fsync_file(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic(path, data):
    """같은 폴더 고정 임시 이름(<이름>.hbtmp)에 쓰고 확인 뒤 이름 바꾸기. 원본을 잘라 쓰지 않는다."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".hbtmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(errno.EIO, "짧은 쓰기")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    if read_regular(temp, max(len(data), 1)) != data:
        os.unlink(temp)
        raise OSError(errno.EIO, "임시 파일 다시 읽기 불일치")
    os.replace(temp, path)
    fsync_file(path)
    if read_regular(path, max(len(data), 1)) != data:
        raise OSError(errno.EIO, "최종 파일 다시 읽기 불일치")
    return sync_directory(path.parent)


def json_write(path, value):
    return atomic(path, json.dumps(value, ensure_ascii=False, sort_keys=True).encode())


def json_read(path, limit=65536):
    value = json.loads(read_regular(path, limit))
    if not isinstance(value, dict):
        raise ValueError("JSON 형식 오류: %s" % path)
    return value


# ── 이름 규칙 ──
def outer_path(rom):
    """'바깥.zip#안쪽.gba' 같은 압축 표기만 나눈다. 보통 이름의 '#'는 그대로."""
    text = str(rom)
    match = re.search(r"\.(zip|7z|apk)#", text, re.I)
    return Path(text[:match.end() - 1] if match else text)


def save_path(system, rom):
    if system not in KINDS:
        raise ValueError("지원하지 않는 기종")
    name = outer_path(rom).stem
    if not name or name in (".", ".."):
        raise ValueError("잘못된 롬 이름")
    return SAVES / system / (name + SAVE_EXT[KINDS[system]])


def p2_name_collision(target):
    """'<이름>.p2.srm'(네오지오 '<이름>.p2.flash') 은 다른 게임의 2P 칸 이름과 겹친다 → 각자 세이브를 쓰지 않음"""
    return Path(target).stem.lower().endswith(".p2")


def tx_root(target):
    target = Path(target)
    return target.parent / ".hb_ownsave" / target.name


def rom_crc(rom, kind):
    """롬 내용 CRC(레트로아크·코어가 보는 값). zip 은 그 기종 롬이 정확히 하나일 때 그 항목의 CRC."""
    path = outer_path(rom)
    if path.suffix.lower() == ".zip":
        import zipfile
        with zipfile.ZipFile(path) as archive:
            members = [x for x in archive.infolist()
                       if not x.is_dir() and Path(x.filename).suffix.lower() in ROM_EXTS[kind]]
            if len(members) != 1 or members[0].file_size > 32 * 1024 * 1024:
                raise ValueError("압축 안 롬이 정확히 하나가 아님")
            return members[0].CRC & 0xFFFFFFFF
    if path.suffix.lower() not in ROM_EXTS[kind]:
        raise ValueError("지원하지 않는 롬 형식: " + path.suffix)
    return zlib.crc32(read_regular(path, 32 * 1024 * 1024)) & 0xFFFFFFFF


def p2_slot_path(system, rom):
    """코어(setP2SavePath)와 같은 이름: 압축이면 안쪽 롬 이름, 아니면 롬 이름 + .p2.sav(원더스완) / .p2.srm(GBA)"""
    path = outer_path(rom)
    name = path.stem
    if path.suffix.lower() == ".zip":
        import zipfile
        with zipfile.ZipFile(path) as archive:
            members = [x for x in archive.infolist()
                       if not x.is_dir() and Path(x.filename).suffix.lower() in ROM_EXTS[KINDS[system]]]
            if len(members) != 1:
                return None
            name = Path(Path(members[0].filename).name).stem
    return SAVES / system / (name + P2_EXT[KINDS[system]])


# ── 6판: 네오지오 .flash 꼴 · 짝 롬을 보통 파일로 ──
def flash_valid(data):
    """네오지오 코어 .flash 꼴(머리 0x0053 · 블록 수 · 전체 길이 · 블록마다 주소 4 · 길이 2 · 0 2 + 내용). 0바이트 = 새 카트."""
    if not data:
        return True
    if len(data) < 8:
        return False
    ident, count, total = struct.unpack_from("<HHI", data, 0)
    if ident != 0x0053 or total != len(data) or not 0 < count <= 256:
        return False
    at = 8
    for _ in range(count):
        if at + 8 > len(data):
            return False
        start, length = struct.unpack_from("<IH", data, at)
        at += 8 + length
        if at > len(data) or not (0x200000 <= start < 0x400000 or 0x800000 <= start < 0xA00000):
            return False
    return at == len(data)


def raw_rom(rom, kind, dest):
    """롬(.zip 이면 그 기종 롬이 정확히 하나인 항목)을 dest 에 보통 파일로 풀고 (dest, CRC). 코어가 ZIP 을 못 읽는 기종용."""
    path = outer_path(rom)
    if path.suffix.lower() == ".zip":
        import zipfile
        with zipfile.ZipFile(path) as archive:
            members = [x for x in archive.infolist()
                       if not x.is_dir() and Path(x.filename).suffix.lower() in ROM_EXTS[kind]]
            if len(members) != 1 or members[0].file_size > 8 * 1024 * 1024:
                raise ValueError("압축 안 롬이 정확히 하나가 아님")
            data = archive.read(members[0])
    else:
        if path.suffix.lower() not in ROM_EXTS[kind]:
            raise ValueError("지원하지 않는 롬 형식: " + path.suffix)
        data = read_regular(path, 8 * 1024 * 1024)
    dest = Path(dest)
    dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    atomic(dest, data)
    return dest, zlib.crc32(data) & 0xFFFFFFFF


def p2rom_for_core(kind, rom):
    """손님 도우미(hb_joinask)가 /tmp/hb_dual_p2rom 에 적을 2P 롬 경로: GBA = 롬 그대로(코어가 ZIP 도 읽음),
    네오지오 = /tmp 에 푼 보통 파일."""
    if kind == 3:
        return str(raw_rom(rom, 3, NGP_P2ROM_GUEST)[0])
    if kind == 2:
        return str(raw_rom(rom, 2, WS_P2ROM_GUEST)[0])   # 7판 원더스완: 코어가 ZIP 을 못 읽음
    return str(outer_path(rom))


# ── 짝 게임(5판) ──
def pair_info(host_rom, my_rom):
    """방장 롬 A · 내 롬 B 가 짝이면 (A 짧은 이름, B 짧은 이름), 아니면 None(같은 게임도 None)"""
    a, b = outer_path(host_rom).stem.lower(), outer_path(my_rom).stem.lower()
    for (n1, l1), (n2, l2) in PAIRS:
        if a == n1.lower() and b == n2.lower():
            return l1, l2
        if a == n2.lower() and b == n1.lower():
            return l2, l1
    return None


def pair_partners(my_rom):
    """내 롬과 짝인 게임 이름(확장자 뺌) 목록"""
    b = outer_path(my_rom).stem.lower()
    out = []
    for (n1, _), (n2, _) in PAIRS:
        if b == n1.lower():
            out.append(n2)
        elif b == n2.lower():
            out.append(n1)
    return out


def partner_file(folder, name, kind=1):
    """폴더에서 이름(확장자 뺌, 대소문자 무시)이 같은 .zip · 그 기종 롬 하나(없으면 None).
    7판: 원더스완은 그 폴더에 없으면 짝 폴더(wswan ↔ wswanc)에서도 찾음 — 코난 06 은 흑백 · 08 은 컬러 폴더."""
    found = _partner_in(folder, name, kind)
    if found is None and kind == 2 and Path(folder).name in WS_FOLDERS:
        other = Path(folder).parent / WS_FOLDERS[1 - WS_FOLDERS.index(Path(folder).name)]
        found = _partner_in(other, name, kind)
    return found


def _partner_in(folder, name, kind):
    folder = Path(folder)
    exts = (".zip",) + ROM_EXTS[kind]
    for ext in exts:
        candidate = folder / (name + ext)
        if candidate.is_file():
            return candidate
    try:
        for candidate in sorted(folder.iterdir()):
            if (candidate.suffix.lower() in exts and candidate.stem.lower() == name.lower()
                    and candidate.is_file()):
                return candidate
    except OSError:
        pass
    return None


# ── 거래 ──
class Lock:
    def __init__(self, root):
        self.path = Path(root) / "lock"

    def __enter__(self):
        import fcntl
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.stream = self.path.open("a+b")
        fcntl.flock(self.stream, fcntl.LOCK_EX)
        return self

    def __exit__(self, *_):
        self.stream.close()


def tx_status(tx):
    for name, state in (("done.json", "done"), ("conflict.json", "conflict"), ("closed.json", "closed")):
        if (tx / name).exists():
            return state
    return "open"


def transactions(target):
    """(거래 폴더, sent) 목록 — 오래된 것부터. 읽을 수 없는 폴더는 건너뜀(지우지 않음)."""
    root = tx_root(target)
    found = []
    if not root.is_dir():
        return found
    for tx in root.iterdir():
        if not tx.is_dir() or tx.is_symlink() or not TOKEN_RE.fullmatch(tx.name):
            continue
        try:
            sent = json_read(tx / "sent.json")
        except (OSError, ValueError):
            continue
        if (sent.get("v") != PROTOCOL or sent.get("token") != tx.name
                or sent.get("target") != str(target)):
            continue
        found.append((tx, sent))
    found.sort(key=lambda item: (item[1].get("t", 0), item[0].name))
    return found


def unpack_packet(packet, sent):
    if not EXPORT.size + 32 < len(packet) <= EXPORT.size + LIMIT + 32:
        raise ValueError("결과 묶음 크기 오류")
    magic, crc, kind, size, token, frame, role, checksum = EXPORT.unpack_from(packet)
    data = packet[EXPORT.size:-32]
    if (magic not in (b"HBE3", b"HBC3") or token.hex() != sent["token"] or not any(token)
            or crc != sent["crc"] or kind != sent["kind"] or role != 2
            or size != len(data) or not 0 < size <= LIMIT
            or zlib.crc32(data) & 0xFFFFFFFF != checksum
            or hashlib.sha256(packet[:-32]).digest() != packet[-32:]):
        raise ValueError("결과 묶음 표 · 2P 역할 · CRC · SHA-256 오류")
    if kind == 1 and size not in GBA_SIZES:
        raise ValueError("GBA 세이브 크기 오류")
    if kind == 2 and sent.get("transfer_size") and size != sent["transfer_size"]:
        raise ValueError("원더스완 세이브 크기가 보낸 것과 다름")
    if kind == 3 and not flash_valid(data):
        raise ValueError("네오지오 .flash 꼴 오류")
    if kind == 4 and size > GG_MAX:
        raise ValueError("게임기어 세이브 크기 오류")
    return data, dict(frame=frame, source=magic.decode(), packet_sha256=sha(packet))


def load_result(tx, sent):
    """export(카드) > export(램, 같은 표) > checkpoint 순. 없으면 None.
    검사에 떨어진 카드 묶음은 <이름>.bad 로 옮겨 둠(지우지 않음 · 자동 적용 안 함 · 다음 보내기를 막지 않음)."""
    ram = ROOT / "export"
    quarantined = []
    for path in (tx / "export.bin", ram, tx / "checkpoint.bin"):
        packet = read_optional(path, LIMIT + EXPORT.size + 32)    # 읽기 오류(EIO 등)는 그대로 실패 → 다음에 다시
        if packet is None:
            continue
        try:
            data, details = unpack_packet(packet, sent)
        except ValueError as error:
            if path != ram:          # 램 사본은 다른 거래 것일 수 있음 — 그냥 넘어감
                os.replace(path, path.with_name(path.name + ".bad"))
                quarantined.append("%s: %s" % (path.name, error))
            continue
        if path == ram:
            atomic(tx / "export.bin", packet)      # 램에만 있던 결과를 카드에 먼저 남김
            details["source"] += "(램)"
        if quarantined:
            details["quarantined"] = quarantined
        return data, details
    if quarantined:
        sync_directory(tx)
        return dict(quarantined=quarantined)
    return None


def apply_transaction(tx, sent, target, data, details):
    """중단된 단계부터 다시 해도 같은 결과. 원본이 보낼 때와 다르면 Conflict."""
    original = read_regular(tx / "original.bin")
    if sent["original_exists"]:
        if sha(original) != sent["original_sha256"]:
            raise ValueError("거래 원본 사본 손상")
    elif original:
        raise ValueError("원본 없음 표시인데 사본이 있음")
    current = read_optional(target)
    current_sha = None if current is None else sha(current)
    result_sha = sha(data)
    if current_sha not in (sent["original_sha256"], result_sha):
        raise Conflict("보낸 뒤 원본이 바뀜(%s)" % (current_sha or "없음")[:12])
    replaced = current_sha != result_sha
    if replaced and sent["original_exists"]:
        # 바꾸기 직전 원본을 한 개 남김(같은 결과면 바꾸지 않으니 지난 백업도 그대로 둠)
        backup = Path(str(target) + ".bak_link")
        if read_optional(backup) != original:
            atomic(backup, original)
    durability = atomic(target, data) if replaced else None
    fsync_file(target)
    if read_regular(target) != data:
        raise OSError(errno.EIO, "최종 세이브 다시 읽기 불일치")
    durability = durability or sync_directory(target.parent)
    result = dict(ok=True, target=str(target), token=tx.name, bytes=len(data), sha256=result_sha,
                  original_sha256=sent["original_sha256"], replaced=replaced,
                  durability=durability, t=time.time(), **details)
    try:
        json_write(tx / "done.json", result)
    except OSError as error:
        # 세이브 교체는 끝났다. 영수증만 실패 — 거래를 열어 둔 채 다음 번에 같은 결과를 확인하고 다시 적음.
        result["receipt_error"] = str(error)
        try:
            (tx / "done.json").unlink()
        except OSError:
            pass
        return result
    for name in ("export.bin", "checkpoint.bin"):
        try:
            (tx / name).unlink()
        except FileNotFoundError:
            pass
    sync_directory(tx)
    return result


def close_tx(tx, reason, keep_original=False):
    json_write(tx / "closed.json", dict(reason=reason, t=time.time()))
    if not keep_original:
        try:
            (tx / "original.bin").unlink()
        except FileNotFoundError:
            pass
    sync_directory(tx)


def freeze_tx(tx, reason, target):
    current = read_optional(target)
    json_write(tx / "conflict.json", dict(reason=reason, t=time.time(),
                                          current_sha256=None if current is None else sha(current)))


def prune(target, keep_tokens=()):
    """끝난(done · closed) 거래는 세이브마다 최근 KEEP_FINISHED 개만. 열린 · 어긋난 거래는 지우지 않는다."""
    import shutil
    finished = [(tx, sent) for tx, sent in transactions(target)
                if tx_status(tx) in ("done", "closed") and tx.name not in keep_tokens
                and not any(p.name.endswith(".bad") for p in tx.iterdir())]   # 격리한 묶음은 지우지 않음
    removed = []
    for tx, _ in finished[:-KEEP_FINISHED] if len(finished) > KEEP_FINISHED else []:
        shutil.rmtree(tx)
        removed.append(tx.name)
    if removed:
        sync_directory(tx_root(target))
    return removed


def recover(system, rom, check_crc=True):
    """지난 거래 마무리: 결과가 있으면 적용, 결과 없으면 닫기, 실패는 남겨 둠. 게임이 꺼져 있을 때만 부름."""
    target = save_path(system, rom)
    root = tx_root(target)
    results = []
    if not root.is_dir():
        return dict(ok=True, applied=0, results=results)
    current_crc = None
    with Lock(root):
        for tx, sent in transactions(target):
            if tx_status(tx) != "open":
                continue
            try:
                if not sent.get("ack"):
                    close_tx(tx, "방장 받음 확인 없음(보내기 실패)")
                    results.append(dict(ok=True, token=tx.name, closed="보내기 실패"))
                    continue
                found = load_result(tx, sent)
                if found is None:
                    close_tx(tx, "남은 2P 결과 없음(2P 확인 전 종료 · 저장 전 강제 종료 등)")
                    results.append(dict(ok=True, token=tx.name, closed="결과 없음"))
                    continue
                if isinstance(found, dict):
                    # 검사에 떨어진 결과만 있음: .bad 로 보관하고 원본 사본도 남긴 채 닫음(자동 적용 안 함)
                    close_tx(tx, "잘못된 결과 묶음 격리: " + "; ".join(found["quarantined"]), keep_original=True)
                    results.append(dict(ok=False, token=tx.name, closed="잘못된 결과 격리",
                                        quarantined=found["quarantined"], retained=True))
                    continue
                if check_crc:
                    if current_crc is None:
                        current_crc = rom_crc(rom, KINDS[system])
                    if sent["crc"] != current_crc:
                        raise Conflict("같은 이름의 다른 롬(CRC %08x → %08x)" % (sent["crc"], current_crc))
                results.append(apply_transaction(tx, sent, target, *found))
            except Conflict as error:
                try:
                    freeze_tx(tx, str(error), target)
                except OSError:
                    pass
                results.append(dict(ok=False, token=tx.name, conflict=str(error), retained=True))
            except (OSError, ValueError, KeyError, TypeError) as error:
                results.append(dict(ok=False, token=tx.name, reason=str(error), retained=True))
        try:
            removed = prune(target)
        except OSError as error:
            removed = ["정리 실패: " + str(error)]
    return dict(ok=all(x.get("ok") for x in results),
                applied=sum(1 for x in results if x.get("ok") and "sha256" in x),
                pruned=removed, results=results)


def finish(system, rom):
    """게임 끝 훅: 방금 끝난 거래(램 sent.json)와 남은 거래를 마무리."""
    pointer = None
    try:
        pointer = json_read(ROOT / "sent.json")
    except (OSError, ValueError):
        pass
    session_rom = rom
    if pointer and pointer.get("system") == system and isinstance(pointer.get("pair"), dict):
        # 5판 짝 게임: 끝 훅이 콘텐츠(방장 게임 A)로 불려도 거래는 손님 자기 게임 B 쪽에서 마무리
        try:
            if (pointer.get("rom") and outer_path(pointer["pair"].get("content", "")) == outer_path(rom)
                    and pointer.get("target") == str(save_path(system, pointer["rom"]))):
                session_rom = pointer["rom"]
        except (ValueError, TypeError, AttributeError):
            pass
    try:
        summary = recover(system, rom)
        if session_rom != rom:
            extra = recover(system, session_rom)
            summary = dict(ok=summary["ok"] and extra["ok"], applied=summary["applied"] + extra["applied"],
                           pruned=summary.get("pruned", []) + extra.get("pruned", []),
                           results=summary["results"] + extra["results"])
    except (OSError, ValueError, KeyError, TypeError) as error:
        return dict(ok=False, reason=str(error), retained=True)
    token = None
    if pointer and pointer.get("system") == system and pointer.get("target") == str(save_path(system, session_rom)):
        token = pointer.get("token")
    for item in summary["results"]:
        if token and item.get("token") == token:
            return dict(item, others=[x for x in summary["results"] if x is not item])
    if token:
        tx = tx_root(save_path(system, session_rom)) / token
        for name in ("done.json", "closed.json", "conflict.json"):
            try:
                return dict(json_read(tx / name), token=token, state=name[:-5], others=summary["results"])
            except (OSError, ValueError):
                continue
    return dict(summary, ok=summary["ok"] and token is None, session=token)


def core_running():
    """램 core 파일의 pid 가 아직 레트로아크면 True(같은 번호를 다른 프로그램이 다시 써도 속지 않게)"""
    try:
        pid = int((ROOT / "core").read_text().split()[1])
        return Path("/proc/%d/comm" % pid).read_text().strip() == "retroarch"
    except (OSError, ValueError, IndexError):
        return False


def clear():
    """램 파일만 정리(카드 거래는 그대로). 레트로아크가 돌고 있으면 아무것도 안 함."""
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    if core_running():
        return False
    for path in ROOT.iterdir():
        if path.is_file() and (path.name in ("core", "request", "ack", "guest", "sent.json", "intent",
                                             "export", "receipt.json", "pair", "reject")
                               or path.name.endswith((".tmp", ".hbtmp"))):
            path.unlink()
    try:
        P2ROM.unlink()          # 5판: 지난 짝 게임 2P 롬 표시가 다음 게임에 안 먹게
    except OSError:
        pass
    return True


def prepare_start(system, rom):
    """게임 시작 훅: 지난 거래(강제 종료 · 배터리로 끝난 판 포함)를 먼저 마무리하고 램 정리."""
    try:
        result = recover(system, rom)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = dict(ok=False, reason=str(error), retained=True)
    result["ram_cleared"] = clear()
    return result


# ── 손님: 보내기 ──
def verify_isolation(target):
    """레트로아크 손님 저장 폴더(.netplay)가 보통 폴더이고 쓸 수 있어야 각자 세이브를 씀."""
    directory = target.parent / ".netplay"
    if directory.is_symlink():
        raise ValueError(".netplay 가 링크임")
    try:
        directory.mkdir(mode=0o755)
    except FileExistsError:
        pass
    if not directory.is_dir():
        raise ValueError(".netplay 가 폴더가 아님")
    probe = directory / ".hb_ownsave_probe"
    atomic(probe, b"HB4")
    probe.unlink()


def private_peer(peer, local):
    """같은 사설 /24 만. 루프백 · 공인 주소 · 끝자리 0/255 는 거절."""
    import ipaddress
    try:
        a, b = ipaddress.IPv4Address(peer), ipaddress.IPv4Address(local)
        networks = [ipaddress.IPv4Network(s) for s in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
        return (any(a in n and b in n for n in networks) and int(a) >> 8 == int(b) >> 8
                and int(a) & 255 not in (0, 255) and int(b) & 255 not in (0, 255))
    except ipaddress.AddressValueError:
        return False


def recv_exact(sock, size, deadline):
    data = bytearray()
    while len(data) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("시간 초과")
        sock.settimeout(remaining)
        part = sock.recv(size - len(data))
        if not part:
            raise ConnectionError("연결 끝")
        data.extend(part)
    return bytes(data)


def recv_json(sock, deadline):
    size = struct.unpack("!I", recv_exact(sock, 4, deadline))[0]
    if not 1 <= size <= 2048:
        raise ValueError("머리 크기 초과")
    value = json.loads(recv_exact(sock, size, deadline))
    if not isinstance(value, dict):
        raise ValueError("잘못된 머리")
    return value


def send_json(sock, value, deadline):
    data = json.dumps(value, separators=(",", ":")).encode()
    sock.settimeout(max(0.001, deadline - time.monotonic()))
    sock.sendall(struct.pack("!I", len(data)) + data)


def transfer_copy(kind, crc, data):
    """보낼 사본만 고침: 원피스(롬 CRC 로 확인)는 세이브가 없거나 0x0F~0x3F 가 비면 49바이트 머리 채움."""
    if kind == 2 and crc in ONEPIECE_CRCS:
        if not data:
            data = bytes(ONEPIECE_SIZE)
        if len(data) == ONEPIECE_SIZE and not any(data[HEADER_AT:HEADER_AT + len(HEADER)]):
            patched = bytearray(data)
            patched[HEADER_AT:HEADER_AT + len(HEADER)] = HEADER
            data = bytes(patched)
    return data


def _exchange(ip, port, header, data, deadline):
    import socket
    with socket.create_connection((ip, port + 1), timeout=max(0.05, deadline - time.monotonic())) as connection:
        if not private_peer(ip, connection.getsockname()[0]):
            raise ValueError("같은 사설 /24 가 아님")
        send_json(connection, header, deadline)
        connection.settimeout(max(0.001, deadline - time.monotonic()))
        connection.sendall(data)
        return recv_json(connection, deadline)


def _send_worker(system, rom, ip, port, started, content=None):
    deadline = started + SEND_LIMIT - 0.15
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    kind = KINDS[system]
    target = save_path(system, rom)
    if p2_name_collision(target):
        raise ValueError("'.p2' 로 끝나는 롬 이름은 2P 칸 이름과 겹쳐 각자 세이브를 쓰지 않음")
    pair = None
    if content is not None:
        # 5판 짝 게임: 콘텐츠 = 방장 게임 A(이 기기에 있는 같은 롬), 2P = 내 게임 B
        if kind not in PAIR_KINDS or not pair_info(content, rom):
            raise ValueError("짝 게임 표에 없는 조합")
        if len(os.fsencode(str(outer_path(rom)))) > PAIR_PATH_MAX:
            raise ValueError("2P 롬 경로가 너무 김")
        pair = dict(content=str(content), content_crc=rom_crc(content, kind), p2rom=str(outer_path(rom)))
    target.parent.mkdir(parents=True, exist_ok=True)
    verify_isolation(target)
    root = tx_root(target)
    with Lock(root):
        for tx, sent in transactions(target):
            if tx_status(tx) == "open" and sent.get("ack") and any(
                    (tx / name).exists() for name in ("export.bin", "checkpoint.bin")):
                raise ValueError("지난 판 결과가 아직 적용되지 않음 — 이번 판은 보통 접속")
        original = read_optional(target)
        crc = rom_crc(rom, kind)
        token = os.urandom(16)
        tx = root / token.hex()
        tx.mkdir(parents=True)
        sync_directory(root)
        sent = dict(v=PROTOCOL, token=token.hex(), system=system, rom=str(rom), target=str(target),
                    crc=crc, kind=kind, ack=False, original_exists=original is not None,
                    original_sha256=None if original is None else sha(original), t=time.time())
        if pair:
            sent["pair"] = pair
        atomic(tx / "original.bin", original if original is not None else b"")
        json_write(tx / "sent.json", sent)
    data = transfer_copy(kind, crc, original or b"")
    if kind == 3 and not flash_valid(data):
        raise ValueError("내 네오지오 세이브가 .flash 꼴이 아님")
    if kind == 4 and len(data) > GG_MAX:
        raise ValueError("내 게임기어 세이브가 64KB 보다 큼")
    header = dict(v=PROTOCOL, crc=crc, kind=kind, token=token.hex(), size=len(data), sha256=sha(data))
    if pair:
        header.update(crc=pair["content_crc"], p2rom=pair["p2rom"], p2crc=crc)
    if time.monotonic() >= deadline:
        raise TimeoutError("카드 준비 시간 초과")
    reply = None
    for attempt in (1, 2):
        try:
            reply = _exchange(ip, port, header, data, deadline)
            break
        except (OSError, ValueError) as error:
            # 같은 표로 한 번만 다시(방장이 이미 받았으면 같은 받음 확인만 다시 옴)
            if attempt == 2 or deadline - time.monotonic() < 0.6 or isinstance(error, ValueError):
                raise
    if pair and isinstance(reply, dict) and reply.get("ok") is False:
        raise ValueError("방장 거절: " + str(reply.get("reason", ""))[:200])
    if reply != {"ok": True, "token": token.hex()}:
        raise ValueError("받음 표가 다름")
    sent.update(ack=True, transfer_sha256=sha(data), transfer_size=len(data))
    json_write(tx / "sent.json", sent)
    json_write(ROOT / "sent.json", sent)
    # 손님 코어가 켤 때 거래에 묶임(실행 명령 --connect 와 함께, 180초 안)
    atomic(ROOT / "intent", b"HBI3" + token + struct.pack("<IIQ", crc, kind, int(time.time()))
           + os.fsencode(str(tx)) + b"\n")
    return dict(ok=True, token=token.hex(), transaction=str(tx))


def _child_send(pipe, args):
    try:
        pipe.send(_send_worker(*args))
    except BaseException as error:          # 자식 안의 모든 실패는 '못 보냄'
        pipe.send(dict(ok=False, reason=str(error) or type(error).__name__))
    finally:
        pipe.close()


def send_save(system, rom, ip, port, content=None):
    """카드 읽기 · 쓰기와 통신을 따로 작업에 두어 창은 SEND_LIMIT 초 안에 답을 받는다.
    content(5판) = 짝 게임일 때 방장 게임 A 의 이 기기 경로(rom = 내 게임 B, 2P 롬)."""
    import multiprocessing
    started = time.monotonic()
    for name in ("intent", "sent.json"):
        try:
            (ROOT / name).unlink()
        except FileNotFoundError:
            pass
    context = multiprocessing.get_context("fork")
    parent, child = context.Pipe(duplex=False)
    args = (system, rom, ip, port, started) + ((content,) if content is not None else ())
    process = context.Process(target=_child_send, args=(child, args), daemon=True)
    process.start()
    child.close()
    try:
        if parent.poll(max(0.0, SEND_LIMIT - (time.monotonic() - started))):
            result = parent.recv()
        else:
            result = dict(ok=False, reason="카드 또는 통신 시간 초과")
    except (EOFError, OSError):
        result = dict(ok=False, reason="보내기 작업이 끝나 버림")
    finally:
        parent.close()
        if process.is_alive():
            process.kill()
        process.join(timeout=0.2)
    if not result.get("ok"):
        # 손님 코어가 이번 거래에 묶이지 않게(카드의 원본 사본은 남김 → 다음 시작 때 닫힘)
        for name in ("intent", "sent.json"):
            try:
                (ROOT / name).unlink()
            except FileNotFoundError:
                pass
    result["elapsed"] = time.monotonic() - started
    log_line(LOG, "보내기 " + json.dumps(result, ensure_ascii=False))
    return result


# ── 원피스 머리(롬 CRC 로만) ──
def _needs_header(data):
    return data is not None and len(data) == ONEPIECE_SIZE and not any(data[HEADER_AT:HEADER_AT + len(HEADER)])


def _with_header(data):
    patched = bytearray(data if data is not None else bytes(ONEPIECE_SIZE))
    patched[HEADER_AT:HEADER_AT + len(HEADER)] = HEADER
    return bytes(patched)


def ophdr(system, rom):
    """게임 시작 훅(혼자 · 방장): 원피스면 1P 세이브(없으면 만듦)와 있는 2P 칸의 빈 머리만 채움.
    고칠 것이 없으면 롬을 읽지 않는다(시작 시간 그대로). 고치기 전 원본은 .bak_ophdr 로 한 번."""
    if KINDS.get(system) != 2:
        return dict(ok=True, changed=[])
    target = save_path(system, rom)
    slots = [(target, True)]
    try:
        slot = p2_slot_path(system, rom)
        if slot:
            slots.append((slot, False))
    except (OSError, ValueError):
        pass
    todo = []
    for path, create in slots:
        data = read_optional(path)
        if (data is None and create) or _needs_header(data):
            todo.append((path, data))
    if not todo:
        return dict(ok=True, changed=[])
    crc = rom_crc(rom, 2)
    if crc not in ONEPIECE_CRCS:
        return dict(ok=True, changed=[], crc="%08x" % crc)
    changed = []
    for path, data in todo:
        if data is not None:
            backup = Path(str(path) + ".bak_ophdr")
            if not backup.exists():
                atomic(backup, data)
        atomic(path, _with_header(data))
        changed.append(str(path))
    log_line(LOG, "원피스 머리 채움 " + json.dumps(changed, ensure_ascii=False))
    return dict(ok=True, changed=changed, crc="%08x" % crc)


# ── 방장: 받기 ──
def tcp_rows(pid):
    inodes = set()
    for fd in Path("/proc/%d/fd" % pid).iterdir():
        try:
            link = os.readlink(fd)
            if link.startswith("socket:["):
                inodes.add(link[8:-1])
        except OSError:
            pass
    rows = []
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            for line in Path(table).read_text().splitlines()[1:]:
                fields = line.split()
                rows.append((int(fields[1].rsplit(":", 1)[1], 16), int(fields[2].rsplit(":", 1)[1], 16),
                             fields[3], fields[9] in inodes))
        except FileNotFoundError:
            pass
    return rows


def host_waiting(pid, port):
    """방장 레트로아크가 넷플레이 포트에서 듣고 있고 접속(또는 접속 시도) 중인 손님이 없음"""
    try:
        rows = tcp_rows(pid)
        return (any(l == port and st == "0A" and mine for l, _, st, mine in rows)
                and not any(l == port and st not in ("0A", "06") for l, _, st, _ in rows))
    except (OSError, ValueError, IndexError):
        return False


class Server:
    """hb_direct 감시가 방장일 때 띄움. 레트로아크 한 번 실행에 손님 세이브 하나만 받는다."""

    def __init__(self, pid, port, system, rom, bind="0.0.0.0"):
        import socket
        import threading
        self.pid, self.port, self.system, self.rom = pid, port, system, rom
        self.kind = KINDS[system]
        self.crc = rom_crc(rom, self.kind)
        self.used = False
        self.accepted = None
        self.stop_event = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((bind, port + 1))
        self.sock.listen(2)
        self.sock.settimeout(0.1)
        self.thread = threading.Thread(target=self.run, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def close(self):
        self.stop_event.set()
        self.sock.close()
        self.thread.join(timeout=4)

    def capability(self):
        values = (ROOT / "core").read_text().split()
        magic, pid, crc, maximum, kind, generation = values
        generation = bytes.fromhex(generation)
        if (magic != "HBO3" or int(pid) != self.pid or int(crc) != self.crc or len(generation) != 8
                or int(kind) != self.kind or not 0 < int(maximum) <= LIMIT):
            raise ValueError("코어 확인 실패")
        return int(maximum), generation

    def pair_rom(self, header, generation):
        """5판 짝 요청: 이 기기 롬 폴더의 같은 이름 2P 롬 → (경로, CRC). 안 되면 PairRefused."""
        name = header.get("p2rom")
        if self.kind not in PAIR_KINDS or not isinstance(name, str) or not isinstance(header.get("p2crc"), int):
            raise PairRefused("짝 게임은 GBA · 원더스완 · 네오지오만")
        name = Path(name).name
        if not name or name in (".", "..") or Path(name).suffix.lower() not in (".zip",) + ROM_EXTS[self.kind]:
            raise PairRefused("2P 롬 이름 오류")
        if not pair_info(self.rom, name):
            raise PairRefused("짝 게임 표에 없는 조합(방장 %s · 손님 %s)" % (outer_path(self.rom).stem, Path(name).stem))
        local = partner_file(outer_path(self.rom).parent, Path(name).stem, self.kind)
        if local is None:
            raise PairRefused("방장 기기에 2P 롬이 없음: " + name)
        if len(os.fsencode(str(local))) > PAIR_PATH_MAX:
            raise PairRefused("2P 롬 경로가 너무 김")
        try:
            if self.kind == 3:
                # 6판 네오지오: 코어가 ZIP 을 못 읽음 — 램에 보통 파일로 풀어 그 경로를 줌(CRC 도 푼 내용으로)
                local, crc = raw_rom(local, 3, NGP_P2ROM_HOST)
            elif self.kind == 2:
                # 7판 원더스완: 네오지오와 같이 램에 보통 파일로 풀어 그 경로를 줌
                local, crc = raw_rom(local, 2, WS_P2ROM_HOST)
            else:
                crc = rom_crc(local, self.kind)
        except (OSError, ValueError) as error:
            raise PairRefused("방장 기기 2P 롬을 못 읽음: %s" % error)
        if crc != header["p2crc"]:
            raise PairRefused("2P 롬 CRC 가 다름(손님 %08x · 방장 %08x)" % (header["p2crc"] & 0xFFFFFFFF, crc))
        try:
            values = (ROOT / "pair").read_text().split()
        except OSError:
            values = []
        if values != ["HBP5", str(self.pid), generation.hex()]:
            raise PairRefused("방장 코어가 짝 게임을 모름(옛 판) — 두 기기 모두 새 판으로")
        return local, crc

    def handle(self, connection, peer):
        deadline = time.monotonic() + 3.5
        if not private_peer(peer[0], connection.getsockname()[0]):
            raise ValueError("같은 사설 /24 가 아님")
        header = recv_json(connection, deadline)
        if (header.get("v") != PROTOCOL or header.get("crc") != self.crc
                or header.get("kind") != self.kind):
            raise ValueError("다른 판 · 다른 게임")
        token = bytes.fromhex(header["token"])
        size = header["size"]
        maximum, generation = self.capability()
        if (len(token) != 16 or not any(token) or type(size) is not int
                or size < 0 or size > maximum or size > LIMIT):
            raise ValueError("표 또는 크기 오류")
        if self.kind == 1 and size not in (0,) + GBA_SIZES:
            raise ValueError("GBA 세이브 크기 오류")
        if self.kind == 2 and size not in (0, maximum):
            raise ValueError("원더스완 세이브 크기 오류")
        if self.kind == 4 and size > GG_MAX:
            raise ValueError("게임기어 세이브 크기 오류")
        data = recv_exact(connection, size, deadline)
        if sha(data) != header.get("sha256"):
            raise ValueError("내용 지문 오류")
        if self.kind == 3 and not flash_valid(data):
            raise ValueError("네오지오 .flash 꼴 오류")
        if "p2rom" in header:
            # 5판 짝 요청: 세이브까지 다 받은 뒤 거절이면 까닭을 바로 알려 줌(손님은 다시 보내지 않음)
            try:
                return self.handle_pair(connection, peer, header, token, size, data, generation, deadline)
            except PairRefused as error:
                send_json(connection, {"ok": False, "reason": str(error)}, deadline)
                raise
        identity = (token.hex(), header["sha256"], size, peer[0])
        if self.used:
            # 같은 손님의 같은 표 다시 보내기(받음 확인을 못 받은 경우)만 다시 확인해 줌
            if identity != self.accepted:
                raise ValueError("이미 다른 손님 세이브를 받은 방")
            send_json(connection, {"ok": True, "token": token.hex()}, deadline)
            return
        if not host_waiting(self.pid, self.port):
            raise ValueError("방장이 대기 중이 아님(이미 손님이 붙었거나 붙는 중)")
        try:
            (ROOT / "ack").unlink()
        except FileNotFoundError:
            pass
        atomic(ROOT / "request", REQUEST.pack(b"HBQ3", self.pid, self.crc, size, self.port,
                                              int(deadline * 1000), token, generation) + data)
        try:
            while time.monotonic() < deadline and not self.stop_event.is_set():
                try:
                    acknowledgement = (ROOT / "ack").read_bytes()
                except FileNotFoundError:
                    acknowledgement = b""
                if acknowledgement == b"HBA3" + token:
                    self.used = True
                    self.accepted = identity
                    log_line(LOG, "방장 받음 %s %d바이트 %s" % (token.hex()[:8], size, peer[0]))
                    send_json(connection, {"ok": True, "token": token.hex()}, deadline)
                    return
                time.sleep(0.01)
            raise TimeoutError("코어 받음 확인 없음")
        finally:
            try:
                (ROOT / "request").unlink()
            except FileNotFoundError:
                pass

    def handle_pair(self, connection, peer, header, token, size, data, generation, deadline):
        """5판: 2P 롬(이 기기 같은 이름 · 같은 CRC)과 손님 세이브를 HBQ4 로 코어에 → 받음 확인 · 거절"""
        identity = (token.hex(), header["sha256"], size, peer[0], header.get("p2rom"), header.get("p2crc"))
        if self.used:
            if identity != self.accepted:
                raise PairRefused("이미 다른 손님 세이브를 받은 방")
            send_json(connection, {"ok": True, "token": token.hex()}, deadline)
            return
        local, crc = self.pair_rom(header, generation)
        if not host_waiting(self.pid, self.port):
            raise PairRefused("방장이 대기 중이 아님(이미 손님이 붙었거나 붙는 중)")
        for name in ("ack", "reject"):
            try:
                (ROOT / name).unlink()
            except FileNotFoundError:
                pass
        path = os.fsencode(str(local))
        atomic(ROOT / "request", REQUEST4.pack(b"HBQ4", self.pid, self.crc, size, self.port, int(deadline * 1000),
                                               token, generation, crc, len(path)) + path + data)
        try:
            while time.monotonic() < deadline and not self.stop_event.is_set():
                try:
                    acknowledgement = (ROOT / "ack").read_bytes()
                except FileNotFoundError:
                    acknowledgement = b""
                if acknowledgement == b"HBA3" + token:
                    self.used = True
                    self.accepted = identity
                    log_line(LOG, "방장 받음(짝 %s) %s %d바이트 %s" % (local.name, token.hex()[:8], size, peer[0]))
                    send_json(connection, {"ok": True, "token": token.hex()}, deadline)
                    return
                try:
                    refusal = (ROOT / "reject").read_bytes()
                except FileNotFoundError:
                    refusal = b""
                if len(refusal) == 24 and refusal[:20] == b"HBR4" + token:
                    code = struct.unpack_from("<I", refusal, 20)[0]
                    raise PairRefused("방장 코어 거절: " + PAIR_REJECT.get(code, str(code)))
                time.sleep(0.01)
            raise PairRefused("코어 받음 확인 없음(시간 초과)")
        finally:
            try:
                (ROOT / "request").unlink()
            except FileNotFoundError:
                pass

    def run(self):
        import socket
        while not self.stop_event.is_set() and Path("/proc/%d" % self.pid).exists():
            try:
                connection, peer = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with connection:
                try:
                    self.handle(connection, peer)
                except (OSError, ValueError, KeyError, TypeError) as error:
                    log_line(LOG, "방장 거절 %s: %s" % (peer[0], error))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("clear", "finish", "recover", "start", "ophdr"))
    parser.add_argument("system", nargs="?")
    parser.add_argument("rom", nargs="?")
    args = parser.parse_args()
    if args.action == "clear":
        print(json.dumps(dict(ok=True, ram_cleared=clear())))
        return
    if args.system not in KINDS or not args.rom:
        parser.error("기종과 롬 경로가 필요함")
    fn = {"finish": finish, "recover": recover, "start": prepare_start, "ophdr": ophdr}[args.action]
    try:
        result = fn(args.system, args.rom)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = dict(ok=False, reason=str(error))
    log_line(LOG, "%s %s %s" % (args.action, Path(str(args.rom)).name, json.dumps(result, ensure_ascii=False)))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
