import os
import sys, subprocess, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from ftr import ftr_lines
from fontTools.ttLib import TTFont
def summ(path,p,ids,iv=35):
    out=ftr_lines(path,p,11,iv,ids)
    return {int(l.split()[1]):tuple(map(int,l.split()[2:4])) for l in out if l.startswith('S ')}
path=sys.argv[1]; t=TTFont(path); go=t.getGlyphOrder(); cm=t.getBestCmap(); rev={v:k for k,v in cm.items()}
os2=t['OS/2']; ids=[go.index(n) for n in set(cm.values()) if t['glyf'][n].numberOfContours!=0]
clip=collections.defaultdict(list)
for p in range(8,41):
    A=math.ceil(os2.usWinAscent*p/1000); D=math.ceil(os2.usWinDescent*p/1000)
    for g,(top,bot) in summ(path,p,ids).items():
        if top==-999: continue
        if top>A or bot<-D: clip[g].append((p,top-A if top>A else bot+D))
print(path.split('/')[-1],'mapped glyphs clipped by GDI at some size 8-40:',len(clip))
for g,v in sorted(clip.items(),key=lambda kv:-len(kv[1]))[:15]:
    print('  ',go[g],chr(rev[go[g]]),v[:8])
