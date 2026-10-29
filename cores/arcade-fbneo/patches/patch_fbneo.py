#!/usr/bin/env python3
"""기기 FBNeo 코어(fbneo_libretro.so md5 fa5feb62…, v1.0.0.03 74a979724)에 넷플레이 고침 셋을 바이트로 넣는다.
쓰는 법: python3 -I patch_fbneo.py <기기 코어> <내보낼 파일> [eeprom,dram,coin]   (기본 = 셋 다)

  eeprom  EEPROMScan: 'eeprom_data'(EEPROM 내용 1024바이트)를 미리 실행(ACB_RUNAHEAD, 비트 7) 대신
          넷플레이 맥락(ACB_NET_OPT, 비트 9)에서 상태에 넣음.  tbnz w24,#7 → tbnz w24,#9
          → 기기마다 다른 .nv(설정 · 최고 점수)가 넷플레이 상태 보내기로 맞춰짐. 보통 상태 저장 꼴은 그대로.
  dram    Taito F3 DrvScan: 'All Ram' 길이를 TaitoRamEnd 대신 TaitoES5510DRAM 까지(4MB DSP 지연 램 뺌).
          ldr x6,[x4,#2632] → ldr x6,[x4,#4560]  (FBNeo 의 ES5510 은 DSP 를 돌리지 않는 빈 껍데기라 이 램은 안 씀)
          → F3 상태 4,825,160 → 631,880바이트. F3 게임의 보통 상태 저장 꼴도 바뀜(옛 F3 상태 파일은 못 읽음).
  coin    Taito F3 DrvFrame: 동전 '앞 장 값'(previous_coin, 상태에 안 들어가는 정적 변수)을 늘 0 으로 읽음.
          ldrb w17,[x9,#48] → mov w17,#0   → 동전 = 누르는 동안 그대로(MAME taito_f3 와 같음) · 되감기에 안 흔들림.
"""
import hashlib
import struct
import sys

STOCK_MD5 = "fa5feb62b5d8c4f9a71786bc649409cd"
PATCHES = {
    "eeprom": (0x158ce60, 0x37380FF8, 0x37480FF8),
    "dram": (0x2743940, 0xF9452486, 0xF948E886),
    "coin": (0x2742F0C, 0x3940C131, 0x52800011),
}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    names = sys.argv[3].split(",") if len(sys.argv) > 3 else list(PATCHES)
    data = bytearray(open(src, "rb").read())
    md5 = hashlib.md5(data).hexdigest()
    if md5 != STOCK_MD5:
        sys.exit("기기 코어가 아님(md5 %s) — 넣지 않음" % md5)
    for name in names:
        off, old, new = PATCHES[name]
        cur = struct.unpack_from("<I", data, off)[0]
        if cur != old:
            sys.exit("%s 자리 값이 다름(%08x) — 넣지 않음" % (name, cur))
        struct.pack_into("<I", data, off, new)
    open(dst, "wb").write(data)
    print("넣음", ",".join(names), "→", dst, hashlib.md5(data).hexdigest())


if __name__ == "__main__":
    main()
