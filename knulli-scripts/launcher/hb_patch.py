#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""hb_patch.py - put a unified diff into one file, or take it out again, without the `patch` command.

Some KNULLI builds ship no `patch`, but every build has Python (the launcher itself is Python), so install.sh
falls back to this helper for launcher/emulatorlauncher.patch. It is strict on purpose:
  - every hunk has to match its context lines exactly (no fuzz). Only the position may differ from the line
    numbers in the diff, so one patch fits the launchers of different KNULLI versions.
  - nothing is written unless every hunk fits. The file is then replaced in one step and keeps its mode.
  - a .py file must still compile after the change, otherwise it is left alone.

Usage:
  python3 hb_patch.py check   PATCH FILE     prints applied | clean | partial | mismatch
  python3 hb_patch.py apply   PATCH FILE     puts the patch in   (--dry-run: only says whether it fits)
  python3 hb_patch.py reverse PATCH FILE     takes the patch out (--dry-run: likewise)

FILE is the file to change. The file names inside the diff are ignored, so the diff must be for one file.
Exit code: 0 = done, would fit, or nothing to do; 1 = does not fit; 2 = wrong arguments or unreadable file.
"""
import os
import re
import stat
import sys
import warnings

HUNK = re.compile(rb'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


class Misfit(Exception):
    pass


def bare(line):
    """the line without its line ending"""
    if line.endswith(b'\r\n'):
        return line[:-2]
    if line.endswith(b'\n'):
        return line[:-1]
    return line


def parse(data):
    """-> [(old_start, new_start, [(tag, text, no_newline)])] with tag b' ', b'-' or b'+'"""
    lines = data.splitlines(True)
    hunks = []
    files = 0
    i = 0
    while i < len(lines):
        if lines[i].startswith(b'--- ') and i + 1 < len(lines) and lines[i + 1].startswith(b'+++ '):
            files += 1
            i += 2
            continue
        m = HUNK.match(lines[i]) if files else None
        if not m:
            i += 1
            continue
        old_left = int(m.group(2)) if m.group(2) is not None else 1
        new_left = int(m.group(4)) if m.group(4) is not None else 1
        body = []
        i += 1
        while i < len(lines) and (old_left > 0 or new_left > 0 or lines[i][:1] == b'\\'):
            tag = lines[i][:1]
            if tag == b'\\':                      # "\ No newline at end of file" belongs to the line before it
                if body:
                    body[-1] = (body[-1][0], body[-1][1], True)
                i += 1
                continue
            if tag in (b'\n', b'\r'):             # an empty context line that lost its leading space
                tag, text = b' ', b''
            else:
                text = bare(lines[i][1:])
            if tag == b' ':
                old_left -= 1
                new_left -= 1
            elif tag == b'-':
                old_left -= 1
            elif tag == b'+':
                new_left -= 1
            else:
                raise ValueError('line %d of the diff is not part of a hunk' % (i + 1))
            body.append((tag, text, False))
            i += 1
        if old_left or new_left:
            raise ValueError('the diff ends in the middle of a hunk')
        hunks.append((int(m.group(1)), int(m.group(3)), body))
    if files > 1:
        raise ValueError('the diff changes %d files; this helper takes one file per diff' % files)
    return hunks


def locate(have, block, start, expected):
    """where `block` sits in `have` at or after `start`; the place nearest to `expected` wins, -1 = nowhere"""
    if not block:
        return min(max(start, expected), len(have))
    best = -1
    for i in range(start, len(have) - len(block) + 1):
        if have[i] == block[0] and have[i:i + len(block)] == block:
            if best < 0 or abs(i - expected) < abs(best - expected):
                best = i
    return best


def sides(body, reverse):
    """-> (lines that must be there now, tag of the lines to drop)"""
    drop = b'+' if reverse else b'-'
    keep = b'-' if reverse else b'+'
    return [text for tag, text, _ in body if tag != keep], drop


def transform(lines, hunks, reverse):
    """-> (new lines, [how many lines each hunk sat away from its stated place]); Misfit when a hunk does not fit"""
    have = [bare(l) for l in lines]
    eol = b'\r\n' if sum(1 for l in lines if l.endswith(b'\r\n')) * 2 > len(lines) else b'\n'
    out = []
    moved = []
    pos = 0
    shift = 0
    for number, (old_start, new_start, body) in enumerate(hunks, 1):
        stated = (new_start if reverse else old_start) - 1
        want, drop = sides(body, reverse)
        at = locate(have, want, pos, stated + shift)
        if at < 0:
            raise Misfit(number)
        shift = at - stated
        moved.append(shift)
        out.extend(lines[pos:at])
        k = at
        for tag, text, no_newline in body:
            if tag == b' ':
                out.append(lines[k])              # the file's own bytes, line ending included
                k += 1
            elif tag == drop:
                k += 1
            else:
                out.append(text + (b'' if no_newline else eol))
        pos = k
    out.extend(lines[pos:])
    return out, moved


def state(lines, hunks):
    for reverse, name in ((True, 'applied'), (False, 'clean')):
        try:
            transform(lines, hunks, reverse)
            return name
        except Misfit:
            pass
    have = [bare(l) for l in lines]
    for old_start, new_start, body in hunks:
        if locate(have, sides(body, True)[0], 0, new_start - 1) >= 0:
            return 'partial'                      # some hunks are in, the others are not
    return 'mismatch'


def compiles(data, name):
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        try:
            compile(data, name, 'exec')
            return None
        except (SyntaxError, ValueError) as error:
            return str(error)


def main(argv):
    args = [a for a in argv[1:] if a != '--dry-run']
    dry = len(args) != len(argv) - 1
    if len(args) != 3 or args[0] not in ('check', 'apply', 'reverse'):
        sys.stderr.write(__doc__)
        return 2
    mode, patch_path, target = args
    target = os.path.realpath(target)
    try:
        with open(patch_path, 'rb') as f:
            hunks = parse(f.read())
        with open(target, 'rb') as f:
            old = f.read()
    except (OSError, ValueError) as error:
        print('hb_patch: %s' % error)
        return 2
    if not hunks:
        print('hb_patch: no hunks found in %s' % patch_path)
        return 2
    lines = old.splitlines(True)
    if mode == 'check':
        print(state(lines, hunks))
        return 0
    reverse = mode == 'reverse'
    try:
        new_lines, moved = transform(lines, hunks, reverse)
    except Misfit as miss:
        now = state(lines, hunks)
        if now == ('clean' if reverse else 'applied'):
            print('hb_patch: nothing to do, the patch is already %s %s' % ('out of' if reverse else 'in', target))
            return 0
        print('hb_patch: hunk %s does not fit %s (state: %s); nothing was changed' % (miss, target, now))
        return 1
    new = b''.join(new_lines)
    if target.endswith('.py') and compiles(old, target) is None:
        error = compiles(new, target)
        if error:
            print('hb_patch: the result would not compile (%s); nothing was changed' % error)
            return 1
    where = ', '.join('hunk %d %+d' % (n, s) for n, s in enumerate(moved, 1) if s) or 'at the stated lines'
    if dry:
        print('hb_patch: %s fits %s (%s)' % ('taking the patch out' if reverse else 'the patch', target, where))
        return 0
    info = os.stat(target)
    tmp = target + '.hbnew'
    try:
        with open(tmp, 'wb') as f:
            f.write(new)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, stat.S_IMODE(info.st_mode))
        try:
            os.chown(tmp, info.st_uid, info.st_gid)
        except OSError:
            pass
        os.replace(tmp, target)
    except OSError as error:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        print('hb_patch: cannot write %s (%s); nothing was changed' % (target, error))
        return 2
    print('hb_patch: %s %s (%s)' % ('took the patch out of' if reverse else 'patched', target, where))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
