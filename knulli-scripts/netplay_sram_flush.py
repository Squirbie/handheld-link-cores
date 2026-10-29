# SPDX-License-Identifier: GPL-3.0-or-later
# netplay_sram_flush.py - Writes in-game saves to disk right away during netplay, with an optional CPU boost while a session runs.
"""Keeps in-game saves on the card during RetroArch netplay (any libretro game; made for the Pokemon gpSP link trades).
  python3 netplay_sram_flush.py CORE SYSTEM ROM   (started in the background by the ES gameStart hook for every libretro game)
RetroArch turns its 10-second SRAM autosave off as soon as netplay starts (retroarch.c CMD_EVENT_NETPLAY_INIT ->
autosave_deinit) and only writes the .srm again when the game is closed properly. A reset or a dead battery then loses
every in-game save of the session (device 2's LeafGreen, 10/4). This waits for this game's RetroArch; once netplay shows up
it asks RetroArch every 10 s to write its save files (network command SAVE_FILES, UDP 55355,
global.retroarch.network_cmd_enable; the hook drops that port for everything but localhost) and pushes them to the card.
Nothing is written outside netplay (RetroArch's own autosave covers that).
Who gets flushed:
- netpacket cores (gpSP link, melonDS DS, ...): host and guest, each runs its own game and keeps its own save.
- every other core (normal lockstep netplay): only the host. A guest's save RAM is replaced by the host's at connect.
  RetroArch already sends a guest that was launched with --connect (ES lobby) to <savedir>/.netplay/ (runloop.c,
  'Special save directory for netplay clients'), but one that joins from the in-game menu would write the host's
  save into its own .srm on exit, so for a guest this copies its own .srm to /userdata/saves/.netplay_backup/<system>/
  once.
After each flush whose content changed, the .srm is also kept as .netplay_backup/<system>/<name>.srm.bak; the hook puts it
back if a reset in the middle of a flush left a 0-byte .srm.
It keeps going after a disconnect, because RetroArch does not turn autosave back on when a guest loses the host. Exits
with RetroArch.
/userdata is exFAT through FUSE (mount.exfat): sync() does not reach it and its cluster bitmap is only written on fsync
or unmount, so every flush also fsyncs the .srm (FUSE_FSYNC flushes all dirty nodes and the bitmap). Outside netplay
it does the same commit every 30 s and once after RetroArch exits, so a reset can't leave RetroArch's own autosave
pointing at clusters the bitmap still calls free (KNULLI only fscks the card when it mounts read-only).
CPU boost (10/8, opt-in): for cores in BOOST_CORES, while this game is in netplay (host room open or guest
connected) the CPU goes to its highest step (1.704GHz, governor performance — KNULLI caps at 1.512GHz) like the Pokemon
Reborn hook, because netplay saves/rewinds the whole state every frame (Tekken 3: 53-56fps -> 58-60). The old values are
kept in /tmp/hb_np_cpu_saved and put back when RetroArch exits or this script is stopped (the ES hook pkills it at the next
game start). Off switch: /userdata/system/claude/netplay_boost.off"""
import hashlib
import os
import re
import shutil
import signal
import socket
import sys
import time

INTERVAL = 10
OWN_SAVE_CORES = {'gpsp', 'melondsds', 'virtualjaguar', 'dosbox_pure', 'gambatte'}  # register the netpacket interface (gambatte: 10/8, GB 통신선)
BOOST_CORES = {'pcsx_rearmed', 'melondsds'}  # netplay too heavy at 1.512GHz: PS1 3D fights, DS link (Gen 5 runs ~45%)
CPU = '/sys/devices/system/cpu/cpufreq/policy0'
CPU_SAVED = '/tmp/hb_np_cpu_saved'
BOOST_OFF = '/userdata/system/claude/netplay_boost.off'
core, system, rom = (sys.argv[1:] + ['', '', ''])[:3]
STEM = os.path.splitext(os.path.basename(rom))[0]
SRM = f'/userdata/saves/{system}/{STEM}.srm' if system and rom else ''
BAKDIR = f'/userdata/saves/.netplay_backup/{system}'


def netplay_port():
    try:
        m = re.search(r'(?m)^netplay_ip_port\s*=\s*"?(\d+)', open('/userdata/system/configs/retroarch/retroarchcustom.cfg').read())
        return int(m.group(1)) if m else 55435
    except OSError:
        return 55435


PORT = netplay_port()


def log(msg):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), core, msg, flush=True)


def retroarch_pid():
    """This game's RetroArch: comm 'retroarch' and this core's .so on its command line."""
    want = f'/{core}_libretro.so'.encode()
    for p in os.listdir('/proc'):
        if p.isdigit():
            try:
                if open(f'/proc/{p}/comm', 'rb').read().strip() == b'retroarch' and \
                        (not core or want in open(f'/proc/{p}/cmdline', 'rb').read()):
                    return p
            except OSError:
                pass
    return None


def role(pid):
    """'host' (listening on, or accepted on, the netplay port), 'guest' (connected to the netplay port) or None."""
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
                if local == PORT and st in ('0A', '01'):
                    host = True
                elif remote == PORT and st == '01':
                    guest = True
        except (OSError, ValueError, IndexError):
            pass
    return 'host' if host else 'guest' if guest else None


def save_files():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    try:
        s.sendto(b'SAVE_FILES', ('127.0.0.1', 55355))
        return s.recv(256).decode(errors='replace').strip()
    except OSError as e:
        return f'no reply ({e})'
    finally:
        s.close()


def fsync_path(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def commit():
    """FUSE_FSYNC through the log file (on /userdata): mount.exfat writes dirty nodes + bitmap and syncs the card."""
    try:
        os.fsync(sys.stdout.fileno())
    except OSError:
        pass


def push_to_card():
    """fsync the .srm (or the log, also on /userdata) so mount.exfat writes nodes + bitmap, then sync the block device."""
    try:
        fsync_path(SRM)
    except OSError:
        try:
            os.fsync(sys.stdout.fileno())
        except OSError:
            pass
    os.sync()


def copy_safely(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst + '.tmp')
    fsync_path(dst + '.tmp')
    os.replace(dst + '.tmp', dst)
    fsync_path(dst)


def read_srm():
    try:
        return open(SRM, 'rb').read()
    except OSError:
        return None


def cpu_boost_on():
    """Highest CPU step while in netplay (only BOOST_CORES). Returns True if boosted."""
    if core not in BOOST_CORES or os.path.exists(BOOST_OFF):
        return False
    try:
        if '1704000' not in open(f'{CPU}/scaling_available_frequencies').read().split():
            return False
        if not os.path.exists(CPU_SAVED):
            with open(CPU_SAVED, 'w') as f:
                f.write(open(f'{CPU}/scaling_max_freq').read().strip() + ' ' + open(f'{CPU}/scaling_governor').read().strip())
        with open(f'{CPU}/scaling_governor', 'w') as f:
            f.write('performance')
        with open(f'{CPU}/scaling_max_freq', 'w') as f:
            f.write('1704000')
        log('CPU boost on: 1.704GHz performance while in netplay')
        return True
    except OSError as e:
        log(f'CPU boost failed ({e})')
        return False


def cpu_boost_off():
    """Put back the top speed saved by cpu_boost_on (also left over from a killed run).
    Only scaling_max_freq: the governor belongs to KNULLI's power-mode hook (10/13: psx/nds pinned to performance
    while playing, schedutil after). This runs a few seconds after RetroArch exits — after KNULLI's gameStop hook — so
    writing the saved governor back left the menu stuck on 'performance'."""
    try:
        freq, gov = open(CPU_SAVED).read().split()
    except (OSError, ValueError):
        return
    try:
        with open(f'{CPU}/scaling_max_freq', 'w') as f:
            f.write(freq)
        os.remove(CPU_SAVED)
        log(f'CPU boost off: top speed back to {freq} (governor left to KNULLI, now {open(f"{CPU}/scaling_governor").read().strip()})')
    except OSError as e:
        log(f'CPU restore failed ({e})')


def stop(*_):
    cpu_boost_off()
    raise SystemExit(0)


signal.signal(signal.SIGTERM, stop)
cpu_boost_off()  # a run killed before it could restore

pid = None
for _ in range(30):
    pid = retroarch_pid()
    if pid:
        break
    time.sleep(1)
if not pid:
    raise SystemExit(0)

flushing, guest_saved, flushes, last_reply, last_hash, stale, ticks = False, False, 0, '', None, 0, 0
boosted = False
while os.path.exists(f'/proc/{pid}'):
    time.sleep(INTERVAL)
    if not os.path.exists(f'/proc/{pid}'):
        break
    ticks += 1
    if not flushing and ticks % 3 == 0:
        commit()
    if not flushing:
        r = role(pid)
        if r and not boosted:
            boosted = cpu_boost_on()
        if r == 'host' or (r == 'guest' and core in OWN_SAVE_CORES):
            flushing = True
            log(f'netplay {r} (retroarch {pid}), writing saves every {INTERVAL} s: {SRM}')
        elif r == 'guest' and not guest_saved:
            guest_saved = True
            try:   # (10/25) 훅 23번: FBNeo 손님 .nv · .fs 를 끝날 때 되돌리라는 표시
                with open('/tmp/hb_np_guest', 'w') as f:
                    f.write(STEM)
            except OSError:
                pass
            if SRM and os.path.isfile(SRM) and os.path.getsize(SRM) > 0:
                dst = f'{BAKDIR}/{STEM}.srm.guest-{time.strftime("%Y%m%d-%H%M%S")}'
                try:
                    copy_safely(SRM, dst)
                    log(f'lockstep netplay guest: own save kept as {dst} (in case it joined from the in-game menu)')
                except OSError as e:
                    log(f'lockstep netplay guest: backup failed ({e})')
            else:
                log('lockstep netplay guest: no own .srm to keep')
    if flushing:
        before = os.path.getmtime(SRM) if SRM and os.path.exists(SRM) else None
        reply = save_files()
        time.sleep(1)
        push_to_card()
        flushes += 1
        after = os.path.getmtime(SRM) if SRM and os.path.exists(SRM) else None
        stale = 0 if after is not None and after != before else stale + 1
        data = read_srm()
        if data:
            h = hashlib.md5(data).hexdigest()
            if h != last_hash:
                last_hash = h
                try:
                    copy_safely(SRM, f'{BAKDIR}/{STEM}.srm.bak')
                except OSError as e:
                    log(f'backup copy failed ({e})')
        if reply != last_reply or flushes == 1 or stale == 3:
            log(f'SAVE_FILES -> {reply}, .srm {"written" if stale == 0 else "NOT changed"} ({len(data or b"")} bytes)')
            last_reply = reply
cpu_boost_off()
time.sleep(2)  # RetroArch writes the .srm on exit
commit()
if flushes or guest_saved:
    log(f'retroarch {pid} ended, {flushes} flushes')
