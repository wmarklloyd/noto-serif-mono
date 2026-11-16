import os
import sys, subprocess, numpy as np, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from ftr import ftr_lines
from fontTools.ttLib import TTFont
def summ(path,p,mode,iv,ids):
    out=ftr_lines(path,p,mode,iv,ids)
    r={}
    for l in out:
        if l.startswith('S '):
            _,g,top,bot,ink,adv=l.split(); r[int(g)]=(int(top),int(bot),int(ink))
    return r
S=sys.argv[1]; path=sys.argv[2] if len(sys.argv)>2 else f'fonts/ttf/NotoSerifMono-{S}.ttf'
t=TTFont(path); go=t.getGlyphOrder(); cm=t.getBestCmap(); rev={v:k for k,v in cm.items()}
ids=[i for i,n in enumerate(go) if t['glyf'][n].numberOfContours!=0]
flag=collections.defaultdict(list)
H=go.index(cm[ord('H')]); x=go.index(cm[ord('x')])
for p in range(10,25):
    h=summ(path,p,11,40,ids); u=summ(path,p,10,40,ids)
    for i in ids:
        if i not in h or i not in u or h[i][0]==-999: continue
        dt=h[i][0]-u[i][0]; db=h[i][1]-u[i][1]
        if abs(dt)>=2 or abs(db)>=2: flag[i].append((p,dt,db))
print(S,'glyphs whose hinted top/bottom differs from unhinted by >=2px at some size 10-24:',len(flag))
items=sorted(flag.items(),key=lambda kv:-len(kv[1]))
for i,v in items[:40]:
    n=go[i]; c=rev.get(n); print(f"  {n} {chr(c) if c else ''} n={len(v)} {v[:6]}")
