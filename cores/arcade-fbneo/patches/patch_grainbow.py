#!/usr/bin/env python3
"""FBNeo 코어(1번 기기의 9e31af94 = 순정 + 넷플레이 3바이트)에 SD 건담 레인보우(grainbow · grainbowk) 3P/4P START 고침.
원인(FBNeo d_legionna.cpp GrainbowInputList): P3 Start = DrvJoy1+8 · P4 Start = DrvJoy1+9 (= P2 위 · 아래와 같은 비트).
 실제(MAME legionna.cpp grainbow SYSTEM 0x10074c): START3 = 0x0100 · START4 = 0x0200 = DrvJoy3 의 비트 8 · 9.
고침: 표 두 칸의 포인터(R_AARCH64_RELATIVE 덧셈값) DrvJoy1+8 → DrvJoy3+8 · DrvJoy1+9 → DrvJoy3+9  (바이트 둘: f8→d8 · f9→d9)
쓰는 법: python3 -I patch_grainbow.py <코어 .so> <내보낼 파일>"""
import hashlib, re, struct, sys
src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, 'rb').read())
shoff = struct.unpack_from('<Q', d, 0x28)[0]
shentsize, shnum, shstrndx = struct.unpack_from('<HHH', d, 0x3a)
secs = {}
stro = struct.unpack_from('<IIQQQQIIQQ', d, shoff + shstrndx * shentsize)[4]
for i in range(shnum):
    n, typ, fl, addr, off, size, *_ = struct.unpack_from('<IIQQQQIIQQ', d, shoff + i * shentsize)
    e = d.index(b'\0', stro + n)
    secs[bytes(d[stro + n:e]).decode()] = (addr, off, size)
ra, rsz = secs['.rela.dyn'][1], secs['.rela.dyn'][2]
ro_addr, ro_off, ro_sz = secs['.rodata']
rel = {}
for i in range(rsz // 24):
    o, info, add = struct.unpack_from('<QQq', d, ra + i * 24)
    if info & 0xffffffff == 1027:
        rel[o] = (add, ra + i * 24)
ro = bytes(d[ro_off:ro_off + ro_sz])
sa = {ro_addr + m.start() for m in re.finditer(b'P3 Start\0', ro)}
ia = {ro_addr + m.start() for m in re.finditer(b'p3 start\0', ro)}
found = []
for o, (add, _) in rel.items():
    if add in sa and rel.get(o + 24, (0,))[0] in ia:
        pv3 = rel.get(o + 16); up2 = rel.get(o - 7 * 32 + 16); dn2 = rel.get(o - 6 * 32 + 16)
        pv4 = rel.get(o + 8 * 32 + 16); st1 = rel.get(o - 17 * 32 + 16)
        if pv3 and up2 and dn2 and pv4 and st1 and pv3[0] == up2[0] and pv4[0] == dn2[0] and \
           rel.get(o + 8 * 32) and rel[o + 8 * 32][0] in {ro_addr + m.start() for m in re.finditer(b'P4 Start\0', ro)}:
            found.append((o, pv3, pv4, st1[0]))
if len(found) != 1:
    sys.exit("표를 하나로 못 찾음(%d) — 넣지 않음" % len(found))
o, pv3, pv4, joy3 = found[0]
print("P3 Start 칸 %#x · 덧셈값 %#x → %#x · P4 Start %#x → %#x" % (o, pv3[0], joy3 + 8, pv4[0], joy3 + 9))
struct.pack_into('<q', d, pv3[1] + 16, joy3 + 8)
struct.pack_into('<q', d, pv4[1] + 16, joy3 + 9)
open(dst, 'wb').write(d)
print("넣음 →", dst, hashlib.md5(d).hexdigest())
