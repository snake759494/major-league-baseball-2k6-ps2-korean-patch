"""SLUS_212.35 (MLB 2K6) 한글 동적 글리프 캐시 패치 (메모리 절약형).
한글 코드(KBASE~)는 폰트의 원래 글리프 조회에서 '없음'이 된다.  폰트 범위표 2번째 (0x7fff, K, CB) 가 캐시 블록.
- HOOK1 (폰트 로더 0x4dbbac): 세트 데이터를 가진 폰트면 전역표 GT[세트] = 데이터 주소.
- HADV (글자 폭 0x4dbcf0): 한글이면 CB 의 전진폭.
- HOOK3 (글자 그리기 0x4dc39c): 글리프 없음 & 한글이면 LRU 슬롯에 비트맵 복사(비캐시 쓰기) 후 s1 = 슬롯 레코드.
텍스처는 매 프레임 RAM 에서 다시 올라가므로 별도 갱신 요청은 필요 없음.
코드 동굴: 어디서도 참조되지 않는 함수 0x32cea0~0x32d190, 0xb548a8~0xb54fe0."""
import os, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from asm import *
import kfont
VA0, OFF0 = 0x100000, 0x1000
CAVE, CAVE_END = 0x5941e0, 0x5941e0 + 0x510
CAVE2, CAVE2_END = 0x59c438, 0x59c438 + 0x888
KB = kfont.KBASE
H1, TEXINIT = 0x142ca4, 0x10cb90   # VCFont_Init 안 텍스처 초기화 호출(a0 = 폰트+0x20)
HW = 0x142de8                      # VCFont_GetCharWidth 시작
H3 = 0x143514                      # VCText_DrawCharInternal: 글리프 조회 직후 (s1=글리프, s2=VCTEXT, s4=문자)
HWBACK = 0x142dfc
ASC1, ASC2 = 0x107b10, 0x27cb50
U2A = 0x27cb90                     # UnicodeToAscii
PCHR_DONE = 0x27b5ec
PCHR = 0x27b5a0                    # KSprintf(char) '%c': lbu a0,(v0) / sb zero,0x1e(s1) / b DONE / sb a0,0x1d(s1)     # VCSystem_AsciiToUnicode, AsciiToUnicode

def _b(op, rs, rt, src, dst):
    return (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (((dst - src - 4) >> 2) & 0xffff)

class Asm:
    def __init__(self, base): self.base = base; self.code = []; self.lab = {}; self.fix = []
    def pc(self): return self.base + 4 * len(self.code)
    def L(self, name): self.lab[name] = self.pc()
    def __call__(self, *ws):
        for w in ws: self.code.append(w)
    def br(self, op, rs, rt, name):
        self.fix.append((len(self.code), op, rs, rt, name)); self.code.append(0)
    def beq(self, rs, rt, name): self.br(4, rs, rt, name)
    def bne(self, rs, rt, name): self.br(5, rs, rt, name)
    def blez(self, rs, name): self.br(6, rs, 'zero', name)
    def b(self, name): self.br(4, 'zero', 'zero', name)
    def done(self):
        for i, op, rs, rt, name in self.fix:
            self.code[i] = _b(op, rs, rt, self.base + 4 * i, self.lab[name])
        return b''.join(struct.pack('<I', w) for w in self.code)

def OR(rd, rs, rt): return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | 0x25
def sra(rd, rt, sa): return (R[rt] << 16) | (R[rd] << 11) | (sa << 6) | 3
def sh(rt, off, base): return (41 << 26) | (R[base] << 21) | (R[rt] << 16) | (off & 0xffff)
def hi_lo(a):
    lo = a & 0xffff; hi = (a >> 16) + (1 if lo & 0x8000 else 0)
    return hi & 0xffff, lo

def patch(elf):
    d = bytearray(elf)
    def w32(va, v): struct.pack_into('<I', d, va - VA0 + OFF0, v)
    def r32(va): return struct.unpack_from('<I', d, va - VA0 + OFF0)[0]
    assert r32(H1) == jal(TEXINIT)
    assert r32(HW) == move('t0', 'a0')
    assert r32(H3) == cvt_w_s(6, 2) and r32(H3 + 4) == mfc1('v0', 6), (hex(r32(H3)), hex(r32(H3+4)))
    assert r32(CAVE) & 0xffff0000 == 0x27bd0000 and r32(CAVE2) & 0xffff0000 == 0x27bd0000
    GT = CAVE_END - 0x20
    gh, gl = hi_lo(GT)
    # ---------- 동굴 1: HOOK1, HADV ----------
    a = Asm(CAVE)
    a.L('hook1')
    a(addiu('sp', 'sp', -0x20), sd('ra', 0, 'sp'), sd('s0', 8, 'sp'), move('s0', 'a0'), jal(TEXINIT), NOP,
      lw('t0', -0x1c, 's0'), addiu('t1', 'zero', 2))
    a.bne('t0', 't1', 'h1d'); a(NOP)
    a(lw('t2', -0x18, 's0'), lhu('t0', 8, 't2'), ori('t1', 'zero', 0x7fff))
    a.bne('t0', 't1', 'h1d'); a(NOP)
    a(lw('t6', 0xc, 't2'), lhu('t0', 0xa, 't6'))
    a.beq('t0', 'zero', 'h1d'); a(NOP)
    a(lw('t1', 0xc, 't6'), addu('t1', 't1', 't6'), addiu('t1', 't1', 0xc),
      lhu('t0', 8, 't6'), sll('t0', 't0', 2), lui('t3', gh), addiu('t3', 't3', gl), addu('t3', 't3', 't0'), sw('t1', 0, 't3'))
    a.L('h1d')
    a(ld('ra', 0, 'sp'), ld('s0', 8, 'sp'), jr('ra'), addiu('sp', 'sp', 0x20))
    a.L('hadv')                                               # (지연 슬롯에서 t0 = a0 됨)
    a(andi('a0', 'a1', 0xffff))
    a.beq('t0', 'zero', 'ret0'); a(sltiu('t2', 'a0', KB))
    a.bne('t2', 'zero', 'back'); a(NOP)
    a(lw('t3', 4, 't0'), addiu('t4', 'zero', 2))
    a.bne('t3', 't4', 'back'); a(NOP)
    a(lw('t3', 8, 't0'), lhu('t4', 8, 't3'), ori('t5', 'zero', 0x7fff))
    a.bne('t4', 't5', 'back'); a(NOP)
    a(lw('t3', 0xc, 't3'), lhu('t4', 0x10, 't3'), addiu('t5', 'a0', -KB), sltu('t6', 't5', 't4'))
    a.beq('t6', 'zero', 'back'); a(NOP)
    a(jr('ra'), lhu('v0', 0x14, 't3'))
    a.L('back')
    a(j(HWBACK), NOP)
    a.L('ret0')
    a(jr('ra'), move('v0', 'zero'))
    # ---------- ASCII→유니코드 변환 2종: 0x80 이상 두 바이트 = 한글 (KB + ((b1&0x7f)<<7 | (b2&0x7f))) ----------
    a.L('asc1')            # VCSystem_AsciiToUnicode(src a0, dst a1, n a2): dst 끝 = a1 + 2n
    a(sll('a2', 'a2', 1), addu('a2', 'a1', 'a2'))
    a.beq('a0', 'zero', 'a1end'); a(NOP)
    a.L('a1lp')
    a(lbu('t0', 0, 'a0'))
    a.beq('t0', 'zero', 'a1end'); a(sltu('t1', 'a1', 'a2'))
    a.beq('t1', 'zero', 'a1end'); a(sltiu('t1', 't0', 0x80))
    a.bne('t1', 'zero', 'a1st'); a(addiu('a0', 'a0', 1))
    a(lbu('t1', 0, 'a0'))
    a.beq('t1', 'zero', 'a1st'); a(NOP)
    a(addiu('a0', 'a0', 1), andi('t0', 't0', 0x7f), sll('t0', 't0', 7), andi('t1', 't1', 0x7f), OR('t0', 't0', 't1'), addiu('t0', 't0', KB))
    a.L('a1st')
    a(sh('t0', 0, 'a1'))
    a.b('a1lp'); a(addiu('a1', 'a1', 2))
    a.L('a1end')
    a(jr('ra'), sh('zero', 0, 'a1'))
    a.L('asc2')            # AsciiToUnicode(src a0, dst a1, n a2): n==0 이면 제한 없음
    a.L('a2lp')
    a(lbu('t0', 0, 'a0'))
    a.beq('t0', 'zero', 'a2end'); a(sltiu('t1', 't0', 0x80))
    a.bne('t1', 'zero', 'a2st'); a(addiu('a0', 'a0', 1))
    a(lbu('t1', 0, 'a0'))
    a.beq('t1', 'zero', 'a2st'); a(NOP)
    a(addiu('a0', 'a0', 1), andi('t0', 't0', 0x7f), sll('t0', 't0', 7), andi('t1', 't1', 0x7f), OR('t0', 't0', 't1'), addiu('t0', 't0', KB))
    a.L('a2st')
    a(sh('t0', 0, 'a1'), addiu('a1', 'a1', 2))
    a.beq('a2', 'zero', 'a2lp'); a(NOP)
    a(addiu('a2', 'a2', -1))
    a.bne('a2', 'zero', 'a2lp'); a(NOP)
    a.L('a2end')
    a(jr('ra'), sh('zero', 0, 'a1'))
    # UnicodeToAscii(src a0, dst a1, n a2): 한글(KB~) -> 두 바이트 (0x80|i>>7, 0x80|i&0x7f)
    a.L('u2a')
    a(lhu('v0', 0, 'a0'))
    a.beq('v0', 'zero', 'u2aend'); a(addiu('a0', 'a0', 2))
    a(sltiu('t0', 'v0', KB))
    a.bne('t0', 'zero', 'u2aone'); a(NOP)
    a(addiu('t1', 'v0', -KB), srl('t2', 't1', 7), ori('t2', 't2', 0x80), sb('t2', 0, 'a1'), addiu('a1', 'a1', 1),
      andi('v0', 't1', 0x7f), ori('v0', 'v0', 0x80))
    a.L('u2aone')
    a(sb('v0', 0, 'a1'), addiu('a1', 'a1', 1))
    a.beq('a2', 'zero', 'u2a'); a(NOP)
    a(addiu('a2', 'a2', -1))
    a.bne('a2', 'zero', 'u2a'); a(NOP)
    a.L('u2aend')
    a(jr('ra'), sb('zero', 0, 'a1'))
    # KSprintf %c: 한글이면 출력 생략 (선수 이니셜 'J. 이름' → '이름'; 서식 '%c. %s' 는 '%c%s' 로 바꿈)
    a.L('pchr')
    a(lhu('a0', 0, 'v0'), sltiu('at', 'a0', KB))
    a.bne('at', 'zero', 'pc1'); a(NOP)
    a(sb('zero', 0x1d, 's1'), move('s0', 'zero'), j(PCHR_DONE), NOP)     # 한글 이니셜은 출력하지 않음
    a.L('pc1')
    a(sb('zero', 0x1e, 's1'), j(PCHR_DONE), sb('a0', 0x1d, 's1'))
    c1 = a.done(); assert CAVE + len(c1) <= GT, hex(CAVE + len(c1))
    labs = dict(a.lab)
    # ---------- 동굴 2: HOOK3 ----------
    a = Asm(CAVE2)
    a.L('hook3')
    a(addiu('sp', 'sp', -0x40), sd('ra', 0, 'sp'), swc1(0, 8, 'sp'), swc1(2, 0xc, 'sp'), swc1(4, 0x10, 'sp'))
    a.bne('s1', 'zero', 'done'); a(slti('t0', 's4', KB))
    a.bne('t0', 'zero', 'done'); a(NOP)
    a(lw('t9', 0, 's2'), lw('t0', 4, 't9'), addiu('t1', 'zero', 2))
    a.bne('t0', 't1', 'done'); a(NOP)
    a(lw('t8', 8, 't9'), lhu('t0', 8, 't8'), ori('t1', 'zero', 0x7fff))
    a.bne('t0', 't1', 'done'); a(NOP)
    a(lw('t6', 0xc, 't8'),
      addiu('t5', 's4', -KB), lhu('t0', 0x10, 't6'), sltu('t1', 't5', 't0'))
    a.beq('t1', 'zero', 'done'); a(NOP)
    a(lhu('t7', 0x12, 't6'),
      lhu('a0', 0x18, 't6'), addu('a0', 'a0', 't6'),         # OWN
      lhu('a1', 0x1a, 't6'), addu('a1', 'a1', 't6'),         # ST
      lhu('a2', 0x1c, 't6'), addu('a2', 'a2', 't6'),         # MAP
      lhu('a3', 0x1e, 't6'), addu('a3', 'a3', 't6'),         # REC
      lw('t4', 0, 't6'), addiu('t4', 't4', 1), sw('t4', 0, 't6'),
      addiu('v1', 't5', 1),
      sll('t0', 't5', 1), addu('t0', 't0', 'a2'), lhu('t3', 0, 't0'))
    a.beq('t3', 'zero', 'miss'); a(addiu('t3', 't3', -1))
    a(sll('t1', 't3', 1), addu('t1', 't1', 'a0'), lhu('t2', 0, 't1'))
    a.bne('t2', 'v1', 'miss'); a(NOP)
    a(sll('t1', 't3', 2), addu('t1', 't1', 'a1'), sw('t4', 0, 't1'))
    a.b('setrec'); a(NOP)
    a.L('miss')
    a(move('t3', 'zero'), lw('t2', 0, 'a1'), addiu('t1', 'zero', 1))
    a.L('loop')
    a(slt('at', 't1', 't7'))
    a.beq('at', 'zero', 'found'); a(sll('t0', 't1', 2))
    a(addu('t0', 't0', 'a1'), lw('t0', 0, 't0'), sltu('at', 't0', 't2'))
    a.beq('at', 'zero', 'next'); a(NOP)
    a(move('t2', 't0'), move('t3', 't1'))
    a.L('next')
    a.b('loop'); a(addiu('t1', 't1', 1))
    a.L('found')
    a(sll('t0', 't3', 1), addu('t0', 't0', 'a0'), lhu('t1', 0, 't0'))
    a.beq('t1', 'zero', 'noold'); a(addiu('t1', 't1', -1))
    a(sll('t1', 't1', 1), addu('t1', 't1', 'a2'), sh('zero', 0, 't1'))
    a.L('noold')
    a(sh('v1', 0, 't0'),
      sll('t1', 't5', 1), addu('t1', 't1', 'a2'), addiu('t2', 't3', 1), sh('t2', 0, 't1'),
      sll('t1', 't3', 2), addu('t1', 't1', 'a1'), sw('t4', 0, 't1'),
      lhu('t0', 8, 't6'), sll('t0', 't0', 2), lui('t1', gh), addiu('t1', 't1', gl), addu('t1', 't1', 't0'), lw('t8', 0, 't1'),
      lhu('t2', 4, 't6'), lhu('t0', 6, 't6'), lhu('v0', 0x16, 't6'), srl('at', 't2', 1), srlv('at', 'at', 'v0'), mult('at', 't0'), mflo('t0'), mult('t0', 't5'), mflo('t0'), addu('t8', 't8', 't0'),
      addiu('t0', 'a3', 0x70),
      sll('t1', 't3', 2), addu('t0', 't0', 't1'), lhu('a0', 0, 't0'), lhu('a1', 2, 't0'),
      lw('t0', 0x38, 't9'), lhu('t1', 0x4c, 't9'), srl('t1', 't1', 1),
      mult('a1', 't1'), mflo('a1'), srl('a0', 'a0', 1), addu('t0', 't0', 'a1'), addu('t0', 't0', 'a0'),
      lui('at', 0x2000), OR('t0', 't0', 'at'),
      lhu('t5', 6, 't6'))
    # v0 = 모드(0: 2bpp, 1: 1bpp). t2 = 4bpp 행 바이트, t1 = 텍스처 행 바이트
    a.bne('v0', 'zero', 'row1'); a(NOP)
    a.L('row')
    a.blez('t5', 'setrec'); a(move('t4', 'zero'))
    a.L('col')
    # 2bpp 원본 1바이트(4픽셀) -> 4bpp 2바이트, 값 v -> v*5
    a(srl('a0', 't4', 1), addu('a0', 't8', 'a0'), lbu('a1', 0, 'a0'), addu('a0', 't0', 't4'),
      srl('a2', 'a1', 0), andi('a2', 'a2', 3), sll('t6', 'a2', 2), addu('a2', 'a2', 't6'),
      srl('t7', 'a1', 2), andi('t7', 't7', 3), sll('t6', 't7', 2), addu('t7', 't7', 't6'), sll('t7', 't7', 4), OR('a2', 'a2', 't7'), sb('a2', 0, 'a0'),
      srl('a2', 'a1', 4), andi('a2', 'a2', 3), sll('t6', 'a2', 2), addu('a2', 'a2', 't6'),
      srl('t7', 'a1', 6), andi('t7', 't7', 3), sll('t6', 't7', 2), addu('t7', 't7', 't6'), sll('t7', 't7', 4), OR('a2', 'a2', 't7'), sb('a2', 1, 'a0'),
      addiu('t4', 't4', 2), slt('at', 't4', 't2'))
    a.bne('at', 'zero', 'col'); a(NOP)
    a(srl('at', 't2', 1), addu('t8', 't8', 'at'), addu('t0', 't0', 't1'), addiu('t5', 't5', -1))
    a.b('row'); a(NOP)
    a.L('row1')
    a.blez('t5', 'setrec'); a(move('t4', 'zero'))
    a.L('col1')
    # 1bpp 원본 1바이트(8픽셀) -> 4bpp 4바이트
    a(srl('a0', 't4', 2), addu('a0', 't8', 'a0'), lbu('a1', 0, 'a0'), addu('a0', 't0', 't4'),
      srl('a2', 'a1', 0), andi('t6', 'a2', 1), andi('a2', 'a2', 2), sll('a2', 'a2', 3), OR('a2', 'a2', 't6'),
      sll('t6', 'a2', 4), subu('a2', 't6', 'a2'), sb('a2', 0, 'a0'),
      srl('a2', 'a1', 2), andi('t6', 'a2', 1), andi('a2', 'a2', 2), sll('a2', 'a2', 3), OR('a2', 'a2', 't6'),
      sll('t6', 'a2', 4), subu('a2', 't6', 'a2'), sb('a2', 1, 'a0'),
      srl('a2', 'a1', 4), andi('t6', 'a2', 1), andi('a2', 'a2', 2), sll('a2', 'a2', 3), OR('a2', 'a2', 't6'),
      sll('t6', 'a2', 4), subu('a2', 't6', 'a2'), sb('a2', 2, 'a0'),
      srl('a2', 'a1', 6), andi('t6', 'a2', 1), andi('a2', 'a2', 2), sll('a2', 'a2', 3), OR('a2', 'a2', 't6'),
      sll('t6', 'a2', 4), subu('a2', 't6', 'a2'), sb('a2', 3, 'a0'),
      addiu('t4', 't4', 4), slt('at', 't4', 't2'))
    a.bne('at', 'zero', 'col1'); a(NOP)
    a(srl('at', 't2', 2), addu('t8', 't8', 'at'), addu('t0', 't0', 't1'), addiu('t5', 't5', -1))
    a.b('row1'); a(NOP)
    a.L('setrec')
    # 폰트당 레코드 1개: 슬롯 좌표로 UV 를 계산해 채운다 (REC+0x60: 1/W, 1/H, 칸 폭, 칸 높이 / +0x70: 슬롯 xy)
    a(sll('t0', 't3', 2), addu('t0', 't0', 'a3'), lhu('a0', 0x70, 't0'), lhu('a1', 0x72, 't0'),
      swc1(8, 0x18, 'sp'), swc1(10, 0x1c, 'sp'), swc1(12, 0x20, 'sp'),
      mtc1('a0', 8), cvt_s_w(8, 8), mtc1('a1', 10), cvt_s_w(10, 10),
      lwc1(12, 0x68, 'a3'), add_s(12, 8, 12), lwc1(6, 0x60, 'a3'), mul_s(8, 8, 6), mul_s(12, 12, 6),
      swc1(8, 0x50, 'a3'), swc1(12, 0x58, 'a3'),
      lwc1(12, 0x6c, 'a3'), add_s(12, 10, 12), lwc1(6, 0x64, 'a3'), mul_s(10, 10, 6), mul_s(12, 12, 6),
      swc1(10, 0x54, 'a3'), swc1(12, 0x5c, 'a3'),
      lwc1(8, 0x18, 'sp'), lwc1(10, 0x1c, 'sp'), lwc1(12, 0x20, 'sp'), move('s1', 'a3'))
    a.L('done')
    a(lwc1(0, 8, 'sp'), lwc1(2, 0xc, 'sp'), lwc1(4, 0x10, 'sp'), cvt_w_s(6, 2), mfc1('v0', 6),
      ld('ra', 0, 'sp'), jr('ra'), addiu('sp', 'sp', 0x40))
    c2 = a.done(); assert CAVE2 + len(c2) <= CAVE2_END, hex(CAVE2 + len(c2))
    labs.update(a.lab)
    for cav, end, code in ((CAVE, CAVE_END, c1), (CAVE2, CAVE2_END, c2)):
        o = cav - VA0 + OFF0
        d[o:o + (end - cav)] = bytes(end - cav)
        d[o:o + len(code)] = code
    if not os.environ.get('KO_NOASC'):
        assert r32(ASC1) == 0x10800014 and r32(ASC2) == move('v1', 'a1'), (hex(r32(ASC1)), hex(r32(ASC2)))
        w32(ASC1, j(labs['asc1'])); w32(ASC1 + 4, NOP)
        w32(ASC2, j(labs['asc2'])); w32(ASC2 + 4, NOP)
        assert r32(U2A) == move('v1', 'a1'), hex(r32(U2A))
        w32(U2A, j(labs['u2a'])); w32(U2A + 4, NOP)
        assert r32(PCHR) == lbu('a0', 0, 'v0'), hex(r32(PCHR))
        w32(PCHR, j(labs['pchr'])); w32(PCHR + 4, NOP)
    # 메모리 카드 화면: 슬롯 이름·저장 이름의 0x80 이상 글자를 '|BOX|'(네모 아이콘)로 바꾸는 검사(sltiu x, y, 0x80)
    #   → 0xffff(부호 확장 = 항상 참)로 바꿔 한글 코드를 그대로 통과시킴
    for va in (0x33d7a0, 0x33d854, 0x33e668):
        w = r32(va); assert w >> 26 == 0x0b and w & 0xffff == 0x80, hex(w)
        w32(va, (w & 0xffff0000) | 0xffff)
    w32(H1, jal(labs['hook1']))
    w32(HW, j(labs['hadv'])); w32(HW + 4, move('t0', 'a0'))
    w32(H3, jal(labs['hook3'])); w32(H3 + 4, NOP)
    return bytes(d), {k: hex(v) for k, v in labs.items() if k in ('hook1', 'hadv', 'hook3')}
