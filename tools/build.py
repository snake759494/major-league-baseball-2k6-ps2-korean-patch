"""MLB 2K6 한글 ISO 빌드: 원본 ISO -> '... (Korean).iso'
1) 실행파일: UTF-16/ASCII 문구 제자리 번역 + 한글 출력 코드 패치
2) 폰트 청크(FONT): 한글 동적 캐시 블록 추가
3) STBL(도움말·퀴즈 등) 재작성, MANU(매뉴얼) 제자리 번역, 기타 데이터 UTF-16 제자리 번역
바뀐 아카이브 항목은 '3.' 파트를 ISO 끝으로 옮긴 뒤 그 뒤에 덧붙이고 아카이브 표·ISO9660·UDF 갱신."""
import os, sys, struct, shutil, json, time, subprocess, re
sys.path.insert(0, os.path.dirname(__file__))
import iso, isoedit, vc, lz, kfont, ktext, codepatch, chunks, stbl
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SRC = os.path.join(ROOT, 'Major League Baseball 2K6 (USA).iso')
DST = os.path.join(ROOT, 'Major League Baseball 2K6 (USA) (Korean).iso')
VCX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin', 'vcx.exe')
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tmp')
SEC = 2048
ELFNAME = 'SLUS_212.35'
isoedit.UDF_PART = 269
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

def compress(data):
    os.makedirs(TMP, exist_ok=True)
    a, b = os.path.join(TMP, 'c_in.bin'), os.path.join(TMP, 'c_out.bin')
    open(a, 'wb').write(data); subprocess.run([VCX, 'c', a, b], check=True)
    r = open(b, 'rb').read(); os.remove(a); os.remove(b); return r

def is_comp(b, o): return struct.unpack_from('<I', b, o + 16)[0] == 0xfeedbeef

# ---------- UTF-16 제자리 ----------
U16 = re.compile(rb'(?:[\x09\x0a\x0d\x20-\x7e]\x00){1,}\x00\x00')
# 실행파일 안에서 화면 표시와 리소스 조회 키를 겸하는 이름들이 모인 구간(구장 노드, 유니폼 부위 등).
# 번역하면 구장/유니폼 모델을 못 찾음 → 이 구간의 한 단어 문자열은 원문 유지
ELF_KEYRANGES = [(0x4a9c00, 0x4b1400), (0x4bc780, 0x4bfd00), (0x538e00, 0x539800)]   # 3번째: LOADING/CAMERA 등 화면 요소 이름(v1.2)
def inplace16(data, tr, groups, lo=0, hi=None, room_pad=False, stats=None):
    d = bytearray(data); n = 0; hi = len(d) if hi is None else hi
    for m in U16.finditer(data, lo, hi):
        o = m.start()
        if o % 2: continue
        s = m.group()[:-2].decode('utf-16-le')
        v = None
        for g in groups:
            v = tr.get(g, s)
            if v is not None: break
        if v is None: continue
        if room_pad and ' ' not in s and any(a <= o < b for a, b in ELF_KEYRANGES): continue   # 모델/구장 노드 이름(조회 키)
        v = tr.enc16(v)
        room = len(s)
        if room_pad:      # 다음 문자열 전까지의 0 패딩(4바이트 경계 이내)도 사용
            e = o + 2 * len(s) + 2
            k = e
            while k + 2 <= len(d) and d[k:k + 2] == b'\0\0' and k < (e + 3) // 4 * 4: k += 2
            room = (k - o) // 2 - 1
        if len(v) > room:
            if stats is not None: stats.setdefault('long', []).append((s, len(v), room))
            continue
        d[o:o + 2 * len(s) + 2] = bytes(2 * len(s) + 2)
        d[o:o + 2 * len(v)] = v.encode('utf-16-le'); n += 1
    return bytes(d), n

A8 = re.compile(rb'[\x09\x0a\x0d\x20-\x7e]{2,}\x00')
def inplace8(data, tr, groups, lo, hi, stats=None):
    d = bytearray(data); n = 0
    for m in A8.finditer(data, lo, hi):
        o = m.start()
        if o > 0 and d[o - 1] != 0 and d[o - 1] < 0x80: continue   # 앞이 ASCII 면 긴 문자열의 꼬리. 0x80 이상(실수 상수 끝 0xff 등)은 별개 문자열
        s = m.group()[:-1].decode()
        if ' ' not in s.strip(): continue      # 한 단어 ASCII 는 조회 키일 수 있어 원문 유지
        v = None
        for g in groups:
            v = tr.get(g, s)
            if v is not None: break
        if v is None: continue
        v = tr.enc8(v)
        e = o + len(s) + 1; k = e
        while k < len(d) and d[k] == 0 and k < (e + 3) // 4 * 4: k += 1
        room = k - o - 1
        if len(v) > room:
            if stats is not None: stats.setdefault('long8', []).append((s, len(v), room))
            continue
        d[o:o + len(s) + 1] = bytes(len(s) + 1); d[o:o + len(v)] = v; n += 1
    return bytes(d), n

# ---------- 청크 묶음 ----------
def rebuild_chunks(b, fn):
    """fn(tag, name, header(bytes), payload(bytes)) -> (header, payload) 또는 None(그대로)."""
    ch, end = chunks.walk(b)
    out = bytearray()
    for o, t, A, nm in ch:
        h = b[o:o + 0x20]; p = b[o + 0x20:o + 0x20 + A]
        r = fn(t, nm, h, p)
        if r is None: out += h + p
        else:
            h2, p2 = r; out += h2 + p2
    return bytes(out + b[end:])

def font_chunk(h, p, sylls, rep):
    u = lz.decompress(p)[0]
    if os.environ.get('KO_FONTMODE') == 'same':
        B, C = struct.unpack_from('<2I', h, 8); nu = u; info = {}
    else:
        nu, B, C, info, _ = kfont.build(u, sylls)
    c = compress(nu); c += bytes((-len(c)) % 32)
    D = max(16, (lz.inplace_margin(c) + 16 + 15) & ~15)     # 제자리 해제 여유
    h = bytearray(h); struct.pack_into('<3I', h, 4, len(c), B, C); struct.pack_into('<I', h, 0x14, D)
    rep.append(info)
    return bytes(h), c

def stbl_chunk(h, p, tr, groups, cnt):
    """STBL 페이로드 재작성 (p = 청크 페이로드)."""
    nl = struct.unpack_from('<I', p, 0x14)[0]
    S = 0x20 + (nl & ~0xf)
    n = struct.unpack_from('<I', p, S)[0]
    offs = struct.unpack_from('<%dI' % n, p, S + 4)
    strs = [p[S + x:p.index(b'\0', S + x)] for x in offs]
    body = bytearray(); new = []; cache = {}
    for s in strs:
        k = s.decode('latin1'); v = None
        for g in groups:
            v = tr.get(g, k)
            if v is not None: break
        e = tr.enc8(v) if v is not None else s
        if v is not None: cnt[0] += 1
        new.append(4 + 4 * n + len(body)); body += e + b'\0'
    out = bytearray(p[:S]) + struct.pack('<I', n) + struct.pack('<%dI' % n, *new) + body
    out += bytes((-len(out)) % 32)
    h = bytearray(h); struct.pack_into('<I', h, 4, len(out))
    return bytes(h), bytes(out)

def manu_chunk(h, p, tr, cnt, stats):
    """MANU: 태그 사이 텍스트를 같은 길이(공백 채움)로 제자리 번역. 표의 오프셋은 그대로."""
    d = bytearray(p)
    base = 0x34 + 12 * struct.unpack_from('<I', p, 0x2c)[0]
    T = p[base:].decode('utf-16-le', 'surrogatepass')
    for m in re.finditer(r'[^<>\x00\r\n]+', T):
        s = m.group()
        st = s.strip()
        v = tr.get('manual', st)
        if v is None: continue
        v = tr.enc16(v)
        lead = len(s) - len(s.lstrip())
        if len(v) > len(st):
            stats.setdefault('longm', []).append((st, len(v), len(st))); continue
        v = v + ' ' * (len(st) - len(v))
        o = base + 2 * (m.start() + lead)
        d[o:o + 2 * len(v)] = v.encode('utf-16-le'); cnt[0] += 1
    return h, bytes(d)

def email_chunk(h, p, tr, cnt):
    """EmailTemplates: MALT 레코드(0x18B: 4, 본문, 제목, 링크, 4, 4)의 오프셋(S 기준) 풀 재작성."""
    S = 0x40
    n = struct.unpack_from('<I', p, S + 4)[0]
    recs = [list(struct.unpack_from('<6I', p, S + 8 + 0x18 * k)) for k in range(n)]
    pool0 = S + 8 + 0x18 * n
    head = bytearray(p[:pool0]); body = bytearray(); memo = {}
    for k, r in enumerate(recs):
        for j in (1, 2, 3):
            s = p[S + r[j]:p.index(b'\0', S + r[j])]
            if s not in memo:
                v = tr.get('email', s.decode('latin1'))
                e = tr.enc8(v) if v is not None else s
                if v is not None: cnt[0] += 1
                memo[s] = pool0 - S + len(body); body += e + b'\0'
            r[j] = memo[s]
        struct.pack_into('<6I', head, S + 8 + 0x18 * k, *r)
    out = bytes(head) + bytes(body); out += bytes((-len(out)) % 32)
    h = bytearray(h); struct.pack_into('<I', h, 4, len(out))
    return bytes(h), out

# ---------- 엔트리별 처리 ----------
FONT_ENTRIES = (10, 78)
SCOUT = ('PLAYERFEEDBACKDATA', 'SCOUTINGFIELDINGDATA', 'SCOUTINGOVERALLDATA', 'SCOUTINGPITCHINGDATA', 'SCOUTINGPOTENTIALDATA',
         'SCOUTINGPOWERDATA', 'SCOUTINGSCRUBDATA', 'SCOUTINGSLUGGINGDATA', 'TEAMMEETINGDATA')
DATA16 = {(2, n): ['scout'] for n in SCOUT}
DATA16.update({(1, 'TEAMDATA'): ['team'], (140, 'TEAMDATA'): ['team'], (1, 'INJURIESDATA'): ['data'], (140, 'INJURIESDATA'): ['data'], (85, 'DATA'): ['data'], (139, 'COACHBIODATA'): ['data'], (4, 'eula'): ['data']})
STBL_GROUPS = {'HelpSTBL': ['help', 'ui'], 'PlayerSoundtrackTutorial': ['help', 'ui'], 'StadiumSoundtrackTutorial': ['help', 'ui'],
               'TrophyDescriptions': ['help', 'ui'], 'Credits': ['credits']}   # 'stringtable'(카메라 데이터 문자열표)은 카메라 조회 키라 번역 금지
def stbl_groups(nm):
    if nm.endswith('triviastringtable'): return ['trivia']
    return STBL_GROUPS.get(nm)

def player_chunk(p, tr, cnt):
    """PLAYERDATA: 0x138 바이트 레코드, +0 이름(UTF-16 16자), +0x20 성(16자). 한·일·대만 선수는 이름을 비우고 성 칸에 전체 이름."""
    d = bytearray(p)
    for r in range(0x7c, len(d) - 0x138 + 1, 0x138):
        a = d[r:r + 0x20].decode('utf-16-le').split('\0')[0]; c = d[r + 0x20:r + 0x40].decode('utf-16-le').split('\0')[0]
        full = tr.get('namepair', a + '|' + c)
        if full: na, nc = '', full
        else:
            na = tr.get('name', a) if a else ''; nc = tr.get('name', c) if c else ''
            na = a if na is None else na; nc = c if nc is None else nc
        if (na, nc) == (a, c): continue
        for off, v in ((0, na), (0x20, nc)):
            e = tr.enc16(v)[:15]
            d[r + off:r + off + 0x20] = (e.encode('utf-16-le') + bytes(0x20))[:0x20]
        cnt[0] += 1
    return bytes(d)

def patch_entry(i, b, tr, sylls, rep, cnt, stats, data_entries):
    def fn(t, nm, h, p):
        if t == 'DATA' and nm == 'PLAYERDATA' and not is_comp(h, 0):
            return h, player_chunk(p, tr, cnt)
        if t == 'FONT' and not os.environ.get('KO_NOFONT'):
            return font_chunk(h, p, sylls, rep)
        if t == 'STBL' and stbl_groups(nm):
            return stbl_chunk(h, p, tr, stbl_groups(nm), cnt)
        if t == 'MANU':
            return manu_chunk(h, p, tr, cnt, stats)
        if t == 'DATh' and nm == 'EmailTemplates':
            return email_chunk(h, p, tr, cnt)
        if t == 'DATh' and nm == 'GMMSG':
            p2, k = inplace8(p, tr, ['gm'], 0, len(p), stats=stats); cnt[0] += k
            return h, p2
        g = DATA16.get((i, nm))
        if g and not is_comp(h, 0):
            p2, k = inplace16(p, tr, g, stats=stats); cnt[0] += k
            return h, p2
        return None
    return rebuild_chunks(b, fn)

def patch_elf(elf, tr, stats):
    # 문자열 데이터 구간(.rodata/.data)만: 코드 영역의 우연한 바이트열은 건드리지 않음
    lo, hi = 0x4a6000, 0x6ac6b4
    if os.environ.get('KO_ELFR'): lo, hi = (int(x, 16) for x in os.environ['KO_ELFR'].split(','))   # 시험용
    e2, n16 = (elf, 0) if os.environ.get('KO_NOE16') else inplace16(elf, tr, ['elf', 'ui'], lo, hi, room_pad=True, stats=stats)   # 시험용 끄기
    e3, n8 = (e2, 0) if os.environ.get('KO_NOE8') else inplace8(e2, tr, ['elfa'], lo, hi, stats=stats)
    e3 = bytearray(e3)
    for o in (0x4c0528, 0x4dcaf0, 0x4e2e99, 0x53f000):    # 선수 이니셜 서식 '%c. %s' -> '%c%s'
        assert e3[o:o + 7] == b'%c. %s' + bytes(1); e3[o:o + 7] = b'%c%s' + bytes(3)
    assert e3[0x4ee5d8:0x4ee5e4] == b'%c. %s (%c)' + bytes(1); e3[0x4ee5d8:0x4ee5e4] = b'%c%s (%c)' + bytes(3)
    e3 = bytes(e3)
    return e3, n16, n8

def main():
    tr = ktext.Translator(); sylls = tr.sylls
    log('syllables', len(sylls))
    ents = {p: (l, s) for p, l, s, r in iso.walk(SRC)}
    T = vc.table(SRC); P = vc.parts(SRC)
    rows = [list(e) for e in T]
    stats = {}; rep = []; cnt = [0]
    data_entries = set(json.load(open(os.path.join(os.path.dirname(__file__), 'data_entries.json')))) if os.path.exists(os.path.join(os.path.dirname(__file__), 'data_entries.json')) else set()
    targets = set(FONT_ENTRIES) | data_entries
    # STBL 을 가진 항목
    targets |= {55, 79, 82, 83, 86, 87, 88, 89, 129, 135, 136} | set(range(98, 128)) | {k[0] for k in DATA16}
    if os.environ.get('KO_TARGETS') is not None:   # 시험용: 지정 항목만
        targets = {int(x) for x in os.environ['KO_TARGETS'].split(',') if x}
    targets -= {int(x) for x in os.environ.get('KO_EXCL', '').split(',') if x}   # 시험용: 제외할 항목
    new = {}
    for i in sorted(targets):
        b = vc.read(tuple(rows[i]), SRC, P)
        nb = patch_entry(i, b, tr, sylls, rep, cnt, stats, data_entries)
        if nb != b: new[i] = nb
    for r in rep: log('font', r)
    log('data strings', cnt[0], 'entries', len(new))
    el, es = ents[ELFNAME]
    elf = iso.read(el, es, SRC)
    elf2, n16, n8 = (elf, 0, 0) if os.environ.get('KO_NOELF') else patch_elf(elf, tr, stats); log('elf strings', n16, n8)
    if not os.environ.get('KO_NOCODE'):
        elf2, labs = codepatch.patch(elf2); log('code', labs)
    assert len(elf2) == len(elf)
    for k in ('long', 'long8', 'longm'):
        for s, a, r in stats.get(k, [])[:400]: print('  [too long %s] %r %d>%d' % (k, s[:60], a, r))
    json.dump({k: v for k, v in stats.items()}, open(os.path.join(TMP, '..', 'build_stats.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    # 배치: VCDATA/3. 은 제자리(게임이 0.의 LBA + 절대 섹터로 직접 읽음) — 3. 뒤에 바뀐 항목을 이어 붙여 3. 을 늘리고,
    # 3. 뒤에 있던 파일들(IRX, 실행파일, SYSTEM.CNF)은 그 뒤로 옮긴다(이름으로 여는 파일들).
    fast = os.path.exists(DST) and os.path.getsize(DST) >= os.path.getsize(SRC) - SEC
    if not fast:
        log('copy iso'); shutil.copyfile(SRC, DST)
    l3, s3 = ents['VCDATA/3.']
    n3 = (s3 + SEC - 1) // SEC
    after = sorted((v[0], p, v[1]) for p, v in ents.items() if v[0] > l3)
    with open(DST, 'r+b') as f:
        hdr_off = ents['VCDATA/0.'][0] * SEC
        with open(SRC, 'rb') as g:
            g.seek(hdr_off); f.seek(hdr_off); f.write(g.read(0x9c + 12 * len(rows)))
        sec3 = n3
        for i in sorted(new):
            d = new[i]
            f.seek((l3 + sec3) * SEC); f.write(d); f.write(bytes((-len(d)) % SEC))
            rows[i][1] = len(d); rows[i][2] = 3 * vc.PART + sec3
            sec3 += (len(d) + SEC - 1) // SEC
        assert sec3 < vc.PART
        for i, e in enumerate(rows):
            f.seek(hdr_off + 0x9c + 12 * i); f.write(struct.pack('<3I', *e))
        f.seek(hdr_off + 0xc + 3 * 4); old = struct.unpack('<I', f.read(4))[0]
        assert old == n3, (old, n3)
        f.seek(hdr_off + 0xc + 3 * 4); f.write(struct.pack('<I', sec3))
        isoedit.relocate(f, DST, 'VCDATA/3.', l3, sec3 * SEC)
        pos = l3 + sec3
        with open(SRC, 'rb') as g:
            plan = []
            for ol, pth, sz in after:
                plan.append((pth, pos, sz, ol)); pos += (sz + SEC - 1) // SEC
            for pth, np_, sz, ol in reversed(plan):     # 뒤에서부터(옮길 자리와 아직 안 옮긴 파일 위치가 겹치지 않게)
                g.seek(ol * SEC); d = g.read(sz)
                if pth == ELFNAME: d = elf2
                f.seek(np_ * SEC); f.write(d); f.write(bytes((-len(d)) % SEC))
                isoedit.relocate(f, DST, pth, np_, sz)
        nsec = max(pos + 1, os.path.getsize(SRC) // SEC)
        with open(SRC, 'rb') as g:
            g.seek(os.path.getsize(SRC) - SEC); avdp = bytearray(g.read(SEC))
        f.seek(pos * SEC); f.write(bytes((nsec - 1 - pos) * SEC))
        struct.pack_into('<I', avdp, 12, nsec - 1)
        isoedit._fix_tag(avdp, 0, struct.unpack_from('<H', avdp, 10)[0])
        f.seek((nsec - 1) * SEC); f.write(avdp)
        f.truncate(nsec * SEC)
        isoedit.set_volume_size(f, nsec)
    log('done', nsec, 'sectors')

if __name__ == '__main__':
    main()
