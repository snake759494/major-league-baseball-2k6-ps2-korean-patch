"""빠른 경기 진입 후 일정 간격으로 캡처 (멈춤 재현)."""
import sys, time, os
sys.path.insert(0, os.path.dirname(__file__)); import emu
iso = sys.argv[1]; tag = sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
emu.start(os.path.abspath(iso))
time.sleep(50); emu.keys('start w2 start w3 x w8 x w3 x w5 x w5 x w8 x w10 x w2 x w2 x')
for i in range(n):
    time.sleep(20); emu.shot('work/%s_%02d.png' % (tag, i))
    emu.keys('x w1 sq w1 x')
emu.stop()
