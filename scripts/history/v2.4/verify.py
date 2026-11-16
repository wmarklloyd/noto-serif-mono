import sys, numpy as np, itertools, string
sys.path.insert(0,'/home/claude/tools')
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from measure import segs
A,B=sys.argv[1],sys.argv[2]
YS=list(range(-240,900,15))
def profile(t,g):
    L={};R={}
    for y in YS:
        sg=segs(t,g,y)
        if sg: L[y]=sg[0][0]; R[y]=sg[-1][1]
    return L,R
for S in ['Regular','Bold','Italic','BoldItalic']:
    a=TTFont(f'{A}/ArborMono-{S}.ttf'); b=TTFont(f'{B}/ArborMono-{S}.ttf')
    # structure
    assert a.getGlyphOrder()==b.getGlyphOrder()
    assert a.getBestCmap()==b.getBestCmap()
    adv=[g for g in a.getGlyphOrder() if a['hmtx'][g][0]!=b['hmtx'][g][0]]
    ptc=[g for g in a.getGlyphOrder() if not a['glyf'][g].isComposite() and a['glyf'][g].numberOfContours>0 and len(a['glyf'][g].coordinates)!=len(b['glyf'][g].coordinates)]
    changed=[g for g in a.getGlyphOrder() if a['glyf'][g].numberOfContours>0 and list(a['glyf'][g].coordinates)!=list(b['glyf'][g].coordinates)]
    ins=[g for g in a.getGlyphOrder() if hasattr(a['glyf'][g],'program') and a['glyf'][g].program.getBytecode()!=b['glyf'][g].program.getBytecode()]
    # outline integrity: signed area sign per contour should keep same sign; total area should not drop
    bad=[]
    gsa=a.getGlyphSet(); gsb=b.getGlyphSet()
    for g in changed:
        pa=AreaPen(gsa); gsa[g].draw(pa); pb=AreaPen(gsb); gsb[g].draw(pb)
        if np.sign(pa.value)!=np.sign(pb.value) or abs(pb.value)<abs(pa.value)*0.97: bad.append((g,round(pa.value),round(pb.value)))
        # contour orientation check
        from arborfix import contours
        for (s,e) in contours(b['glyf'][g]):
            P=np.array(b['glyf'][g].coordinates[s:e],float); Q=np.array(a['glyf'][g].coordinates[s:e],float)
            sa=np.sum(P[:,0]*np.roll(P[:,1],-1)-np.roll(P[:,0],-1)*P[:,1]); sq=np.sum(Q[:,0]*np.roll(Q[:,1],-1)-np.roll(Q[:,0],-1)*Q[:,1])
            if np.sign(sa)!=np.sign(sq): bad.append((g,'contour flipped'))
    print(f"== {S}: advances changed {len(adv)}, point counts changed {len(ptc)}, instructions changed {len(ins)}, outlines changed {len(changed)}, area drops >3% or flipped contours {len(bad)} {bad[:6]}")
    # pair clearance for printable ASCII
    cm=a.getBestCmap(); chars=[c for c in string.printable[:94]]
    pa={c:profile(a,cm[ord(c)]) for c in chars}; pb={c:profile(b,cm[ord(c)]) for c in chars}
    newov=[];worse=[]
    for l,r in itertools.product(chars,chars):
        def gap(p):
            Lr=p[l][1]; Rl=p[r][0]; ys=set(Lr)&set(Rl)
            return min((Rl[y]+563-Lr[y]) for y in ys) if ys else 999
        ga,gb=gap(pa),gap(pb)
        if gb<0 and ga>=0: newov.append(l+r)
        elif gb<0 and gb<ga-2: worse.append(f"{l}{r}:{ga}->{gb}")
        elif gb<ga-12 and gb<25: worse.append(f"{l}{r}:{ga}->{gb}")
    print(f"   ASCII pairs {len(chars)**2}: new overlaps {len(newov)} {newov[:20]}; notably tighter {len(worse)} {worse[:30]}")
