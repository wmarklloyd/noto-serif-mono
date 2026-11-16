import os
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ftr import render
from fontTools.ttLib import TTFont
import numpy as np, collections
def extents(entry,th=100):
    l,t,a=entry
    if a.size==0: return None
    rows=np.where((a>th).any(1))[0]
    if len(rows)==0: return None
    return t-rows[0], t-rows[-1]-1   # top above baseline (px), bottom
groups={'xflat':'xzvwyu','xround':'oecs','capflat':'HEFTZIL','capround':'OCGSQ','asc':'bdhkl','fig':'1457'}
def run(path,interp,mode,ppems):
    cm=TTFont(path).getBestCmap()
    out={}
    for p in ppems:
        names=sorted(set([cm[ord(c)] for g in groups.values() for c in g]+[cm[ord(c)] for c in 'HEFTxzvnmhil']))
        r=render(path,p,names,mode,interp)
        row={}
        for gname,chars in groups.items():
            tops=collections.Counter(extents(r[cm[ord(c)]])[0] for c in chars)
            row[gname]=dict(tops)
        bots=collections.Counter(extents(r[cm[ord(c)]])[1] for c in 'HEFTxzvnmhil')
        row['base']=dict(bots)
        out[p]=row
    return out
if __name__=='__main__':
    for S in sys.argv[1:]:
        path=f'fonts/ttf/NotoSerifMono-{S}.ttf'
        for interp,mode,lab in [(40,1,'v40 gray'),(35,1,'v35 gray'),(35,2,'v35 mono'),(40,0,'unhinted')]:
            res=run(path,interp,mode,range(9,25))
            print(f'== {S} {lab}')
            for p,row in res.items():
                flags=[k for k,v in row.items() if len(v)>1 and k in('xflat','capflat','asc','base','fig')]
                print(f"  {p:2d}px x:{row['xflat']} o:{row['xround']} H:{row['capflat']} O:{row['capround']} asc:{row['asc']} fig:{row['fig']} base:{row['base']}  {'<-- '+','.join(flags) if flags else ''}")
