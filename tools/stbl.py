"""STBL 청크(o=청크 시작, u=o+0x20): u+0x14 nl, 표 위치 S=u+0x20+(nl&~0xf): count, offsets(S 기준), ASCII 문자열."""
import struct
def head(b,o):
    u=o+0x20; nl=struct.unpack_from('<I',b,u+0x14)[0]; return u+0x20+(nl&~0xf)
def parse(b,o):
    S=head(b,o); n=struct.unpack_from('<I',b,S)[0]
    offs=struct.unpack_from('<%dI'%n,b,S+4)
    return [b[S+x:b.index(b'\0',S+x)] for x in offs]
