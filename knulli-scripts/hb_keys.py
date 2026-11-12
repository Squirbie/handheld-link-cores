#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""hb_keys.py - reads gamepad buttons for the Join / Solo prompt (hb_joinask.py imports it)

EvdevKeys opens the input devices that have the wanted key codes, read-only: no grab, no uinput, so the game
and EmulationStation keep getting the same presses. It needs python-evdev, which KNULLI ships.
FakeKeys reads "code value" lines from a text file instead, for tests away from the device.
Keep this file next to hb_joinask.py (default: /userdata/system/claude/).
"""
import os
import select
import sys
import time


def log(msg):
    """which devices were opened or lost, on stderr (the ES hook throws it away; run hb_joinask.py by hand to see it)"""
    try:
        sys.stderr.write('keys: %s\n' % msg)
    except OSError:
        pass


class EvdevKeys(object):
    """Opens every input device that has one of the wanted key codes, read-only (no grab).
    poll(timeout) returns the (code, value) pairs that arrived."""

    def __init__(self, want_codes):
        import evdev           # python-evdev: part of KNULLI. Away from the device use FakeKeys (--fake-keys)
        self.evdev = evdev
        self.want = set(want_codes)
        self.devs = {}
        self.next_scan = 0.0
        self._scan(0.0)

    def _scan(self, now):
        self.next_scan = now + 5.0
        for path in self.evdev.list_devices():
            if path in self.devs:
                continue
            try:
                dev = self.evdev.InputDevice(path)
                keys = set(dev.capabilities().get(self.evdev.ecodes.EV_KEY, []))
                if keys & self.want:
                    os.set_blocking(dev.fd, False)
                    self.devs[path] = dev
                    log('%s (%s)' % (path, dev.name))
                else:
                    dev.close()
            except OSError:
                pass

    def poll(self, timeout):
        now = time.monotonic()
        if not self.devs and now >= self.next_scan:
            self._scan(now)
        if not self.devs:
            time.sleep(timeout)
            return []
        by_fd = dict((d.fd, (p, d)) for p, d in self.devs.items())
        out = []
        try:
            ready = select.select(list(by_fd), [], [], timeout)[0]
        except (OSError, ValueError):
            ready = []
        for fd in ready:
            path, dev = by_fd[fd]
            try:
                for ev in dev.read():
                    if ev.type == self.evdev.ecodes.EV_KEY:
                        out.append((ev.code, ev.value))
            except BlockingIOError:
                pass
            except OSError:
                log('lost %s' % path)
                self.devs.pop(path, None)
                try:
                    dev.close()
                except OSError:
                    pass
        return out


class FakeKeys(object):
    """For tests away from the device: every "code value" line appended to the file (for example "304 1")
    is read as a key event."""

    def __init__(self, path):
        self.path = path
        self.pos = 0

    def poll(self, timeout):
        end = time.monotonic() + timeout
        while True:
            out = []
            try:
                with open(self.path) as f:
                    f.seek(self.pos)
                    data = f.read()
                    self.pos = f.tell()
            except OSError:
                data = ''
            for line in data.splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[0].lstrip('-').isdigit() and parts[1].lstrip('-').isdigit():
                    out.append((int(parts[0]), int(parts[1])))
            if out or time.monotonic() >= end:
                return out
            time.sleep(0.02)
