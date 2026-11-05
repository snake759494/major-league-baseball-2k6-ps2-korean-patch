import sys,struct
sys.path.insert(0,'tools');import iso,vc
def walk(b):
    o=0;out=[]
    while o+0x20<=len(b):
        tag=b[o:o+4];sz=struct.unpack_from('<I',b,o+4)[0]
        if not (tag.isalnum() or tag[:1].isalpha()): break
        nm=''
        if b[o+0x2c:o+0x30]==tag:
            nm=b[o+0x40:o+0x80].decode('utf-16le','replace').split('\0')[0]
        out.append((o,tag.decode('latin1'),sz,nm));o+=0x20+sz
    return out,o
if __name__=='__main__':
    T=vc.table();P=vc.parts();f=open(iso.ISO,'rb')
    from collections import Counter;C=Counter()
    for i,e in enumerate(T):
        f.seek(vc.iso_off(e[2],P=P));b=f.read(min(e[1],64<<20))
        ch,end=walk(b)
        for c in ch: C[c[1]]+=1
        print(i,'%08x'%e[0],e[1],end,' '.join('%s:%s'%(c[1],c[3]) for c in ch)[:300])
    print(C,file=sys.stderr)
