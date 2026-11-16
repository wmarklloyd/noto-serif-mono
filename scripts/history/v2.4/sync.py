"""Re-sync base-letter contours inside precomposed glyphs to the plain letter."""
import sys, unicodedata, numpy as np
sys.path.insert(0,'/home/claude/tools')
from arborfix import contours
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
SKIP=set('ďľťĽŀĿΆΈΉΊΌΎΏ')
SKIP_RANGES=[(0x1F00,0x1FFF)]  # polytonic Greek: bases shifted for breathing marks  # apostrophe-caron / middle-dot forms legitimately reshape the base
HOMO={'А':'A','В':'B','Е':'E','Н':'H','К':'K','М':'M','Т':'T','О':'O','Р':'P','С':'C','Х':'X','І':'I','Ј':'J','Ѕ':'S',
 'Α':'A','Β':'B','Ε':'E','Ζ':'Z','Η':'H','Ι':'I','Κ':'K','Μ':'M','Ν':'N','Ο':'O','Ρ':'P','Τ':'T','Υ':'Y','Χ':'X',
 'а':'a','е':'e','о':'o','р':'p','с':'c','х':'x','у':'y','і':'i','ј':'j','ѕ':'s','ԁ':'d','ԛ':'q','ԝ':'w','ο':'o'}
def sync(t, log, maxdrift=30):
    glyf=t['glyf']; cm=t.getBestCmap(); n=0; detail=[]
    items=[(ord(k),cm.get(ord(k)),v) for k,v in HOMO.items() if ord(k) in cm]+[(cp,gn,None) for cp,gn in sorted(cm.items())]
    for cp,gn,hb in items:
        ch=chr(cp)
        if hb is None:
            if ch in SKIP or any(a<=cp<=b for a,b in SKIP_RANGES): continue
            d=unicodedata.normalize('NFD',ch)
            if len(d)<2 or not d[0].isalpha(): continue
        else: d=hb
        base=cm.get(ord(d[0]))
        if not base or base==gn: continue
        B=glyf[base]; G=glyf[gn]
        if B.numberOfContours<=0 or G.numberOfContours<=0: continue
        Bc=np.array(B.coordinates); Gc=np.array(G.coordinates)
        br=contours(B); gr=contours(G)
        # map each base contour to an equal-length contour in G with identical y's
        used=set(); pairs=[]
        for bi,(ba,bb) in enumerate(br):
            for gi,(ga,gb) in enumerate(gr):
                if gi in used or gb-ga!=bb-ba: continue
                if np.abs(Gc[ga:gb,1]-Bc[ba:bb,1]).max()<=1 and np.abs(Gc[ga:gb,0]-Bc[ba:bb,0]).max()<=maxdrift:
                    pairs.append((bi,gi)); used.add(gi); break
        if len(pairs)!=len(br): continue
        dmax=max(int(np.abs(Gc[gr[gi][0]:gr[gi][1]]-Bc[br[bi][0]:br[bi][1]]).max()) for bi,gi in pairs)
        if dmax<=1: continue
        # centre shift of the base for repositioning marks
        oldx=np.concatenate([Gc[gr[gi][0]:gr[gi][1],0] for _,gi in pairs]); newx=Bc[:,0]
        shift=((newx.min()+newx.max())-(oldx.min()+oldx.max()))/2
        new=Gc.copy()
        for bi,gi in pairs:
            new[gr[gi][0]:gr[gi][1]]=Bc[br[bi][0]:br[bi][1]]
        for gi,(ga,gb) in enumerate(gr):
            if gi not in used: new[ga:gb,0]=Gc[ga:gb,0]+round(shift)
        G.coordinates=GlyphCoordinates([tuple(map(int,p)) for p in new]); G.recalcBounds(glyf)
        t['hmtx'][gn]=(t['hmtx'][gn][0],G.xMin)
        n+=1; detail.append(f"{ch}:{dmax}")
    log.append(f"synced {n} precomposed glyphs to their base letter: "+' '.join(detail))
    return n
