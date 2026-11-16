import os
import sys, numpy as np, collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ftr import render
from fontTools.ttLib import TTFont
try:
    from skimage.measure import label
except ImportError:  # small pure-Python fallback: label(binary, connectivity=1|2).max() is all we use
    class _L(int):
        def max(self): return int(self)
    def label(b, connectivity=1):
        b = np.asarray(b, bool); seen = np.zeros_like(b); n = 0
        nb = [(1,0),(-1,0),(0,1),(0,-1)] + ([(1,1),(1,-1),(-1,1),(-1,-1)] if connectivity == 2 else [])
        H, W = b.shape
        for y in range(H):
            for x in range(W):
                if b[y, x] and not seen[y, x]:
                    n += 1; st = [(y, x)]; seen[y, x] = True
                    while st:
                        cy, cx = st.pop()
                        for dy, dx in nb:
                            yy, xx = cy + dy, cx + dx
                            if 0 <= yy < H and 0 <= xx < W and b[yy, xx] and not seen[yy, xx]:
                                seen[yy, xx] = True; st.append((yy, xx))
        return _L(n)
def holes(b):
    if b.size==0: return 0
    p=np.pad(b,1); lab=label(~p,connectivity=1); return lab.max()-1
def comps(b):
    if b.size==0: return 0
    return label(b,connectivity=2).max()
def analyse(path, ppems, chars, interp=40, th=128):
    cm=TTFont(path).getBestCmap()
    names=[cm[ord(c)] for c in chars]
    rep=collections.defaultdict(list)
    for p in ppems:
        H=render(path,p,names,1,interp); U=render(path,p,names,0,interp); M=render(path,p,names,2,interp)
        for c,n in zip(chars,names):
            hl,ht,ha=H[n]; ul,ut,ua=U[n]; ml,mt,ma=M[n]
            hb=ha>th; ub=ua>th; mb=ma>127
            hu=holes(ub); hh=holes(hb); hm=holes(mb)
            cu=comps(ub); ch_=comps(hb); cmn=comps(mb)
            inkh=ha.sum(); inku=ua.sum()
            if hh<hu: rep[c].append((p,'gray counter closed',hu,hh))
            if hm<hu: rep[c].append((p,'mono counter closed',hu,hm))
            if cmn<cu: rep[c].append((p,'mono part lost',cu,cmn))
            if ch_<cu: rep[c].append((p,'gray part lost',cu,ch_))
            if inku and not (0.75<inkh/inku<1.45): rep[c].append((p,'ink',round(inkh/inku,2)))
    return rep
if __name__=='__main__':
    import string
    chars=string.ascii_letters+string.digits+string.punctuation+'ÀÉÎÕÜàéîõüßæøåçñ'
    for S in sys.argv[1:]:
        rep=analyse(f'fonts/ttf/NotoSerifMono-{S}.ttf',range(9,21),chars)
        kinds=collections.Counter(k[1] for v in rep.values() for k in v)
        print('==',S,dict(kinds))
        for c,v in rep.items(): print('  ',c,v[:8])
