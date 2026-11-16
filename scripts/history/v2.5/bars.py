import sys; sys.path.insert(0,'/home/claude/ft')
from ftr import render
from fontTools.ttLib import TTFont
import numpy as np
# (char, x-fraction of glyph cell column, y-units range to look for the bar)
BARS=[('H',0.5,(300,450),'H bar'),('E',0.62,(650,720),'E top'),('E',0.6,(330,420),'E mid'),('E',0.62,(0,60),'E base'),('T',0.72,(650,720),'T bar'),
      ('e',0.5,(230,330),'e bar'),('z',0.5,(480,540),'z top'),('z',0.5,(0,60),'z base'),('t',0.72,(440,536),'t bar'),('f',0.75,(440,536),'f bar'),('A',0.5,(160,300),'A bar'),('Z',0.5,(650,714),'Z top')]
def bar_profile(path,p,mode,iv,cm):
    out={}
    for ch,fx,(y0,y1),lab in BARS:
        n=cm[ord(ch)]; l,t,a=render(path,p,[n],mode,iv)[n]
        col=int(round(fx*0.563*p))-l
        if not (0<=col<a.shape[1]): out[lab]=None; continue
        rows=[(t-1-r) for r in range(a.shape[0])]  # pixel row index from baseline (row covering [y,y+1))
        vals=[(rows[r],int(a[r,col])) for r in range(a.shape[0]) if y0*p/1000-1.5<=rows[r]<=y1*p/1000+1]
        # bar = contiguous ink rows within window
        ink=[v for y,v in vals if v>40]
        out[lab]=(len([v for v in ink if v>128]),max(ink) if ink else 0, sum(ink)/255)
    return out
if __name__=='__main__':
    S=sys.argv[1]; path=f'/home/claude/out1/ArborMono-{S}.ttf' if len(sys.argv)<3 else sys.argv[2]
    cm=TTFont(path).getBestCmap()
    for p in range(9,25):
        h=bar_profile(path,p,1,40,cm); u=bar_profile(path,p,0,40,cm)
        print(f"{p:2d}px "+' '.join(f"{k}:{h[k][0]}/{h[k][1]}" for k in h if h[k]), '| unhinted peak', ' '.join(str(u[k][1]) for k in u if u[k]))
