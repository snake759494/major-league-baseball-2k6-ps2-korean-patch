"""번역 불러오기와 게임용 인코딩.
번역 파일: work/translation/*.json  {원문: 번역}  (번역이 null/빈 문자열이면 원문 유지)
한글 음절은 KBASE + 순번(자주 쓰는 순).
 - UTF-16 문자열: 그 코드 그대로
 - ASCII 문자열: 두 바이트 (0x80 | 순번>>7, 0x80 | 순번&0x7f)  — 실행파일의 ASCII→유니코드 변환을 패치해 해석"""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import kfont
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TR = os.path.join(ROOT, 'translation')
SUBST = {'·': '.', '…': '...', '“': '"', '”': '"', '‘': "'", '’': "'", '–': '-', '—': '-', '　': ' ', '×': 'x',
         '~': '~', '→': '->', '%': '%'}
def is_syl(ch): return 0xAC00 <= ord(ch) <= 0xD7A3

class Translator:
    def __init__(self):
        self.maps = {}
        for fp in sorted(glob.glob(os.path.join(TR, '*.json'))):
            name = os.path.splitext(os.path.basename(fp))[0].split('__')[0]
            m = json.load(open(fp, encoding='utf-8'))
            self.maps.setdefault(name, {}).update({k: v for k, v in m.items() if v})
        if os.environ.get('KO_NONAMES'):   # 최소판: 팀·선수 이름은 원문 유지(음절 수와 글자 메모리 감소)
            teams = set(self.maps.get('team', {}))
            for g in ('name', 'namepair', 'team'): self.maps.pop(g, None)
            for mp in self.maps.values():
                for k in [k for k in mp if k in teams]: del mp[k]
        used = {}
        for mp in self.maps.values():
            for v in mp.values():
                for ch in v:
                    if is_syl(ch): used[ch] = used.get(ch, 0) + 1
        self.sylls = sorted(used, key=lambda c: (-used[c], c))
        if os.environ.get('KO_PADSYL'):     # 시험: 음절 수를 n 개까지 KS X 1001 음절로 채움
            n = int(os.environ['KO_PADSYL'])
            for j in range(2350):
                if len(self.sylls) >= n: break
                c = bytes([0xb0 + j // 94, 0xa1 + j % 94]).decode('euc-kr')
                if c not in used: self.sylls.append(c); used[c] = 0
        if os.environ.get('KO_MAXSYL'): self.sylls = self.sylls[:int(os.environ['KO_MAXSYL'])]   # 시험용
        assert len(self.sylls) < 0x4000
        self.idx = {s: i for i, s in enumerate(self.sylls)}

    def _norm(self, s):
        out = []
        for ch in s:
            ch = SUBST.get(ch, ch)
            for c in ch:
                if not is_syl(c) and ord(c) > 0x7e and c not in '\r\n\t':
                    raise ValueError('unencodable %r in %r' % (c, s))
                out.append(c)
        return out

    def enc16(self, s):
        """UTF-16 문자열용(파이썬 str)."""
        return ''.join(chr(kfont.KBASE + self.idx.get(c, 0)) if is_syl(c) else c for c in self._norm(s))

    def enc8(self, s):
        """ASCII 문자열용(bytes)."""
        b = bytearray()
        for c in self._norm(s):
            if is_syl(c):
                i = self.idx.get(c, 0); b += bytes([0x80 | (i >> 7), 0x80 | (i & 0x7f)])
            else: b.append(ord(c))
        return bytes(b)

    def get(self, group, en):
        if os.environ.get('KO_SKIP') and en in os.environ['KO_SKIP'].split('|'): return None   # 시험용
        m = self.maps.get(group)
        if m is None: return None
        v = m.get(en)
        if v is None:      # 앞뒤 공백/줄바꿈이 추출 때 잘린 경우: 핵심으로 찾고 원래 공백을 다시 붙임
            core = en.strip()
            if core and core != en and m.get(core):
                v = en[:len(en) - len(en.lstrip())] + m[core].strip() + en[len(en.rstrip()):]
        return v
