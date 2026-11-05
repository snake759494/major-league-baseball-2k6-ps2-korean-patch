using System;using System.IO;using System.Collections.Generic;using System.Threading.Tasks;
// vcx dump <iso> <outdir> [skipmagic,...] : 모든 리소스 체인 단위를 풀어 저장
// vcx d <in> <out> : 단일 LZ 스트림 해제
static class P{
 const long SEC=2048, PART=0x80000;
 public static byte[] Dec(byte[] s,int p0){
  int us=BitConverter.ToInt32(s,p0);int nb=s[p0+8];int p=p0+9;var o=new byte[us];int q=0;int mo=(1<<nb)-1,ml=(1<<(16-nb))-1;
  while(q<us){int fl=s[p++];for(int b=0;b<8&&q<us;b++){ if(((fl>>b)&1)!=0){int w=s[p]|(s[p+1]<<8);p+=2;int off=w&mo,ln=((w>>nb)&ml)+3;
     for(int i=ln-1;i>=0;i--){int k=q+i;if(k<us)o[k]=(k-off>=0)?o[k-off]:(byte)0;} q+=ln;} else o[q++]=s[p++];}}
  return o;}
 // 겹치지 않는 매치(off>=len)만 사용 (원본 해제기가 뒤에서부터 복사하므로)
 public static byte[] Comp(byte[] d,int nb){
  int n=d.Length,maxoff=(1<<nb)-1,maxlen=(1<<(16-nb))-1+3;var o=new MemoryStream();var bw=new BinaryWriter(o);
  bw.Write(n);bw.Write(1);bw.Write((byte)nb);
  var head=new int[1<<16];var prev=new int[n];Array.Fill(head,-1);
  long fpos=-1;int bit=8;var buf=new List<byte>();byte flags=0;
  void Flush(){ if(fpos>=0){o.Position=fpos;o.WriteByte(flags);o.Position=o.Length;} }
  void Flag(int v){ if(bit==8){Flush();fpos=o.Length;o.WriteByte(0);flags=0;bit=0;} if(v!=0)flags|=(byte)(1<<bit); bit++; }
  int H(int i)=>((d[i]<<8)^(d[i+1]<<4)^d[i+2])&0xffff;
  void Ins(int i){ if(i+3<=n){int h=H(i);prev[i]=head[h];head[h]=i;} }
  int p=0;
  while(p<n){int bl=0,bo=0;
   if(p+3<=n){int j=head[H(p)];int cnt=0;
    while(j>=0&&cnt<256){int off=p-j;if(off>maxoff)break;int lim=Math.Min(Math.Min(maxlen,off),n-p);
      if(lim>=3&&d[j]==d[p]&&d[j+1]==d[p+1]&&d[j+2]==d[p+2]){int l=3;while(l<lim&&d[j+l]==d[p+l])l++;if(l>bl){bl=l;bo=off;if(l==maxlen)break;}}
      j=prev[j];cnt++;}}
   if(bl>=3){Flag(1);int w=bo|((bl-3)<<nb);o.WriteByte((byte)w);o.WriteByte((byte)(w>>8));for(int k=p;k<p+bl;k++)Ins(k);p+=bl;}
   else{Flag(0);o.WriteByte(d[p]);Ins(p);p++;}}
  Flush();return o.ToArray();}
 static int Main(string[] a){
  if(a[0]=="c"){var s=File.ReadAllBytes(a[1]);File.WriteAllBytes(a[2],Comp(s,a.Length>3?int.Parse(a[3]):12));return 0;}
  if(a[0]=="d"){var s=File.ReadAllBytes(a[1]);File.WriteAllBytes(a[2],Dec(s,0));return 0;}
  string iso=a[1],od=a[2];var skip=new HashSet<string>(a.Length>3?a[3].Split(','):new string[0]);Directory.CreateDirectory(od);
  var f=File.OpenRead(iso);var br=new BinaryReader(f);
  long[] parts=new long[4];
  // ISO9660 루트에서 0.~3. 찾기
  f.Seek(16*SEC+156+2,0);uint rl=br.ReadUInt32();f.Seek(16*SEC+156+10,0);uint rs=br.ReadUInt32();
  f.Seek(rl*SEC,0);var dir=br.ReadBytes((int)rs);int i0=0;
  while(i0<dir.Length){int n=dir[i0];if(n==0){i0=(i0/2048+1)*2048;continue;}uint l=BitConverter.ToUInt32(dir,i0+2);int nl=dir[i0+32];string nm=System.Text.Encoding.ASCII.GetString(dir,i0+33,nl);
   for(int k=0;k<4;k++) if(nm==k+".;1"||nm==k+".") parts[k]=l; i0+=n;}
  f.Seek(parts[0]*SEC,0);var hd=br.ReadBytes(0x9c+12*6000);int cnt=BitConverter.ToInt32(hd,0);
  var ents=new List<(uint,uint,uint)>();for(int i=0;i<cnt;i++)ents.Add((BitConverter.ToUInt32(hd,0x9c+12*i),BitConverter.ToUInt32(hd,0x9c+12*i+4),BitConverter.ToUInt32(hd,0x9c+12*i+8)));
  var lst=new List<string>();object lk=new object();
  Parallel.ForEach(ents,new ParallelOptions{MaxDegreeOfParallelism=12},e=>{
   var (h,sz,sec)=e;if(sz>300_000_000)return;byte[] d;
   using(var g=File.OpenRead(iso)){g.Seek(parts[sec/PART]*SEC+(sec%PART)*SEC,0);d=new byte[sz];int r=0;while(r<sz)r+=g.Read(d,r,(int)sz-r);}
   int o=0;bool any=false;
   while(o+0x20<=d.Length){uint F=BitConverter.ToUInt32(d,o+16);if(F!=0xfeedbeef)break;any=true;string mg=System.Text.Encoding.ASCII.GetString(d,o,4);int A=BitConverter.ToInt32(d,o+4);
     if(!skip.Contains(mg)){try{var u=Dec(d,o+0x20);File.WriteAllBytes(Path.Combine(od,$"{h:x8}_{o:x}.{mg}"),u);lock(lk)lst.Add($"{h:x8} {o:x} {mg} {u.Length}");}catch{lock(lk)lst.Add($"{h:x8} {o:x} {mg} ERR");}}
     o+=0x20+A;}
   if(!any){string mg=System.Text.Encoding.ASCII.GetString(d,0,4);mg=System.Text.RegularExpressions.Regex.IsMatch(mg,"^[A-Za-z0-9_]{4}$")?mg:"bin";if(!skip.Contains(mg)&&sz<60_000_000){File.WriteAllBytes(Path.Combine(od,$"{h:x8}_raw.{mg}"),d);lock(lk)lst.Add($"{h:x8} raw {mg} {sz}");}}
  });
  lst.Sort();File.WriteAllLines(Path.Combine(od,"_list.txt"),lst);Console.WriteLine(lst.Count);return 0;}}
