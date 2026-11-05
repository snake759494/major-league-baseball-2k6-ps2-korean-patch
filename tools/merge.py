"""tr/<묶음>_<번호>.json ({i: 번역}) + src/batches -> translation/<묶음>__<번호>.json ({원문: 번역}) 및 검사."""
import json,glob,os,re,sys
sys.path.insert(0,os.path.dirname(__file__));import ktext
TOK=re.compile(r'%[A-Za-z0-9]{1,2}|\|[A-Z_0-9/]+\||\{\d\}')
def blen(s): return sum(2 if ktext.is_syl(c) else 1 for c in s)
bad=[];tot=0
for tp in sorted(glob.glob('tr/*.json')):
    name=os.path.splitext(os.path.basename(tp))[0]
    g,k=name.rsplit('_',1)
    src=json.load(open('src/batches/%s.json'%name,encoding='utf-8'))
    try: tr=json.load(open(tp,encoding='utf-8'))
    except Exception as e: print('BAD JSON',tp,e); continue
    out={}
    for it in src:
        v=tr.get(str(it['i']))
        if not v: continue
        en=it['en']
        try: ktext.Translator._norm(None,v)
        except ValueError as e: bad.append((name,it['i'],'char',v[:40])); continue
        if 'max' in it:
            L=len(v) if it['unit']=='char' else blen(v)
            if L>it['max']: bad.append((name,it['i'],'len %d>%d'%(L,it['max']),v[:40])); continue
        t1=sorted(t for t in TOK.findall(en) if not t.startswith('|') or t in ('|L1|',) or re.fullmatch(r'\|(L1|R1|L2|R2|L3|R3|CROSS|CIRCLE|SQUARE|TRIANGLE|START|SELECT|ANALOG|RANALOG|LANALOG|DPAD|BULLET|REG|TM|B|/B|U|/U|I|/I)\|',t))
        t2=sorted(t for t in TOK.findall(v) if t in t1 or not t.startswith('|'))
        if t1!=sorted(x for x in t2 if x in t1) or len([x for x in t2 if x.startswith('%')])!=len([x for x in t1 if x.startswith('%')]) and not (t1==['%ss'] and t2==['%s']):
            bad.append((name,it['i'],'tok %s|%s'%(t1,t2),v[:40])); continue
        out[en]=v
    tot+=len(out)
    json.dump(out,open('translation/%s__%s.json'%(g,k),'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print('merged',tot)
for b in bad: print('  ',b)
print('bad',len(bad))
