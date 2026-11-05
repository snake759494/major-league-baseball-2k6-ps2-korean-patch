"""번역 원문 추출 -> src/<묶음>.json : [{"en":원문, "max":허용길이(없으면 제한 없음), "unit":"char|byte"}]"""
import sys,os,re,json,struct
sys.path.insert(0,os.path.dirname(__file__));import vc,chunks,stbl
T=vc.table();P=vc.parts()
def ent(i): return vc.read(T[i],P=P)
def dump(name,items):
    seen={};out=[]
    for it in items:
        k=it['en']
        if k in seen:
            j=seen[k]
            if 'max' in it and 'max' in out[j]: out[j]['max']=min(out[j]['max'],it['max'])
            continue
        seen[k]=len(out);out.append(it)
    json.dump(out,open('src/%s.json'%name,'w',encoding='utf-8'),ensure_ascii=False,indent=0)
    print(name,len(out),sum(len(x['en']) for x in out))
# 1) ELF UTF-16
BS=chr(92)
el=json.load(open('tmp/elf_cand.json',encoding='utf-8'))
items=[]
for s in el:
    if re.fullmatch(r'[A-Z0-9]{8,}',s) or s.lower().endswith('.iff'): continue
    items.append({'en':s,'max':len(s),'unit':'char'})
dump('elf',items)
# 2) STBL
def stbl_items(i,pred=None):
    b=ent(i);out=[]
    for o,t,A,nm in chunks.walk(b)[0]:
        if t=='STBL':
            for s in stbl.parse(b,o):
                s=s.decode('latin1')
                if re.search('[A-Za-z]{2}',s) and (pred is None or pred(s)): out.append({'en':s})
    return out
dump('help',stbl_items(55)+stbl_items(82)+stbl_items(83)+stbl_items(89)+stbl_items(86,lambda s:' ' in s or s[0].isupper())+stbl_items(87,lambda s:' ' in s or s[0].isupper())+stbl_items(88,lambda s:' ' in s or s[0].isupper()))
tri=[]
for i in [129]+list(range(98,128)): tri+=stbl_items(i)
dump('trivia',tri)
# 3) MANU
b=ent(78);man=[]
for o,t,A,nm in chunks.walk(b)[0]:
    if t!='MANU': continue
    p=b[o+0x20:o+0x20+A];base=0x34+12*struct.unpack_from('<I',p,0x2c)[0]
    Tx=p[base:].decode('utf-16-le','surrogatepass')
    for m in re.finditer(r'[^<>\x00\r\n]+',Tx):
        st=m.group().strip()
        if not re.search('[A-Za-z]{2}',st) or re.fullmatch(r'/?[a-z0-9]+',st) : continue
        man.append({'en':st,'max':len(st),'unit':'char','page':nm})
dump('manual',man)
# 4) Email (풀 재작성, 제한 없음)
b=ent(135);p=b[0x20:];S=0x40;n=struct.unpack_from('<I',p,S+4)[0];em=[]
for k in range(n):
    r=struct.unpack_from('<6I',p,S+8+0x18*k)
    for x in r[1:4]:
        s=p[S+x:p.index(b'\0',S+x)].decode('latin1')
        if re.search('[A-Za-z]{2}',s): em.append({'en':s})
dump('email',em)
# 5) GMMSG (제자리, 바이트 제한)
b=ent(136);p=b[0x20:];gm=[]
for m in re.finditer(rb'[\x20-\x7e]{4,}(?=\0)',p):
    s=m.group().decode()
    if ' ' in s: gm.append({'en':s,'max':len(s),'unit':'byte'})
dump('gm',gm)
# 6) UTF-16 데이터 (제자리, 글자 제한)
def u16(i,names=None):
    b=ent(i);out=[]
    for o,t,A,nm in chunks.walk(b)[0]:
        if names and nm not in names: continue
        p=b[o+0x20:o+0x20+A]
        for m in re.finditer(rb'(?:[\x09\x0a\x0d\x20-\x7e]\x00){2,}(?=\x00\x00)',p):
            if m.start()%2: continue
            s=m.group().decode('utf-16le')
            if re.search('[a-z]{2}',s) and (' ' in s or len(s)>3): out.append({'en':s,'max':len(s),'unit':'char','src':'%d/%s'%(i,nm)})
    return out
dump('scout',u16(2,{'PLAYERFEEDBACKDATA','SCOUTINGFIELDINGDATA','SCOUTINGOVERALLDATA','SCOUTINGPITCHINGDATA','SCOUTINGPOTENTIALDATA','SCOUTINGPOWERDATA','SCOUTINGSCRUBDATA','SCOUTINGSLUGGINGDATA','TEAMMEETINGDATA'}))
dump('data',u16(1,{'INJURIESDATA'})+u16(85)+u16(139)+u16(4))
