import re,json
rows=[r for r in (l.rstrip('\n').split('\t',1) for l in open('elf_u16.txt',encoding='utf-8')) if len(r)==2]
keep=[]
BS=chr(92)
for o,s in rows:
    o=int(o,16)
    if o<0x4a6000: continue
    s2=s.replace(BS+'n','\n').replace(BS+'r','\r')
    if not re.search(r'[A-Za-z]{2}',s): continue
    if re.fullmatch(r'[a-z0-9_]+',s) or ('_' in s and ' ' not in s): continue
    if re.search(r'\.(png|tga|bin|dat|irx|elf|mrk|txt|ini|wav|vag)$',s,re.I) or (('/' in s or BS in s) and ' ' not in s): continue
    if re.fullmatch(r'[a-z]+[A-Z][A-Za-z0-9]*',s): continue
    if re.fullmatch(r'[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+',s): continue
    keep.append(s2)
u=list(dict.fromkeys(keep))
print(len(keep),len(u),sum(len(x) for x in u))
json.dump(u,open('tmp/elf_cand.json','w',encoding='utf-8'),ensure_ascii=False,indent=0)
import random;random.seed(1)
for s in random.sample(u,60): print(repr(s[:80]))
