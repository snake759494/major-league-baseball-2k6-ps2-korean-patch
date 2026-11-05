"""PCSX2 16:9 와이드 패치(pnach) 생성.
게임은 화면비 함수(0x35d228)가 전역 플래그 0x8C0360 을 보고 16:9(0x3FE38E39) 또는 4:3 을 돌려준다.
플래그는 0x35cde8 함수가 BIOS 화면 설정(syscall 0x4B GetOsdConfigParam, screenType==2 '16:9')으로 정한다.
그 판정(xori v0,v0,2 / sltiu v0,v0,1)을 v0=1 로 바꿔 게임 내장 16:9 모드를 항상 켠다.
사용: python tools/widescreen.py <SLUS_212.35 경로> [출력 폴더]"""
import struct, sys, os

PATCH = [(0x35CDF8, 0x38420002, 0x24020001),   # xori v0,v0,2  -> addiu v0,zero,1
         (0x35CE00, 0x2C420001, 0x00000000)]   # sltiu v0,v0,1 -> nop

def elf_crc(e):
    c = 0
    for (w,) in struct.iter_unpack('<I', e[:len(e) // 4 * 4]): c ^= w
    return c

def word(e, va):
    ph = struct.unpack_from('<I', e, 28)[0]
    for k in range(struct.unpack_from('<H', e, 44)[0]):
        _, o, v, _, fs = struct.unpack_from('<5I', e, ph + k * 32)
        if v <= va < v + fs: return struct.unpack_from('<I', e, o + va - v)[0]

def main():
    e = open(sys.argv[1], 'rb').read(); out = sys.argv[2] if len(sys.argv) > 2 else '.'
    for va, old, new in PATCH:
        assert word(e, va) == old, 'unexpected code at %x' % va
    crc = '%08X' % elf_crc(e)
    lines = ['gametitle=Major League Baseball 2K6 (USA) (SLUS-21235)', '',
             '[Widescreen 16:9]', 'gsaspectratio=16:9',
             "description=Enables the game's built-in 16:9 mode (forces the BIOS 16:9 screen check).",
             'author=Claude', '',
             '// 0x35CDF8: xori v0,v0,2 / sltiu v0,v0,1  ->  v0 = 1 (widescreen flag 0x8C0360 on)']
    lines += ['patch=1,EE,%08X,word,%08X' % (va, new) for va, old, new in PATCH]
    p = os.path.join(out, 'SLUS-21235_%s.pnach' % crc)
    open(p, 'wb').write(('\r\n'.join(lines) + '\r\n').encode())
    print(p)

if __name__ == '__main__':
    main()
