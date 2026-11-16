import sys, numpy as np, collections
sys.path.insert(0,'/home/claude/ft')
from ftr import render
from fontTools.ttLib import TTFont
from skimage.measure import label
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
        rep=analyse(f'/home/claude/out1/ArborMono-{S}.ttf',range(9,21),chars)
        kinds=collections.Counter(k[1] for v in rep.values() for k in v)
        print('==',S,dict(kinds))
        for c,v in rep.items(): print('  ',c,v[:8])
