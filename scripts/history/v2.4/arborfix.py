"""Arbor Mono 2.4 refinement helpers: stem straightening, x-only stem
emboldening with bbox preservation, and contour-matched propagation."""
import math, numpy as np
from fontTools.ttLib import TTFont

def contours(g):
    ends=g.endPtsOfContours; s=0; out=[]
    for e in ends: out.append((s,e+1)); s=e+1
    return out

def embolden_x(coords, flags, ranges, s, slant=0.0, mode='all'):
    """Shift every point horizontally away from ink by up to s/2 (x only).
    Returns new coords list. Ink-on-right (TrueType) convention."""
    pts=np.array(coords,float); new=pts.copy()
    for a,b in ranges:
        P=pts[a:b]; n=len(P)
        if n<3: continue
        def edge_h(i,j):
            d=P[j]-P[i]; L=math.hypot(*d)
            if L<1e-6: return None
            nx=-d[1]/L  # left normal x component (outward from ink)
            w=1.0
            if mode=='bs':  # only backslash-oriented strokes (broad-nib thick strokes)
                dy=d[1]; dxu=d[0]-dy*slant
                if abs(dy)<1e-6: w=0.0
                else:
                    r=dxu/dy  # <0 for '\'
                    w=max(0.0,min(1.0,(-r-0.10)/0.08))
            return w*s/2*max(-1,min(1,nx*1.6))
        H=[]
        for i in range(n):
            j=(i+1)%n; h=edge_h(i,j)
            k=1
            while h is None and k<n: h=edge_h(i,(i+1+k)%n); k+=1
            H.append(h or 0.0)
        def inter(p,d1,q,d2):
            den=d1[0]*d2[1]-d1[1]*d2[0]
            if abs(den)<1e-3*math.hypot(*d1)*math.hypot(*d2): return None
            t=((q[0]-p[0])*d2[1]-(q[1]-p[1])*d2[0])/den
            return p+t*d1
        for i in range(n):
            hin=H[i-1]; hout=H[i]
            if mode=='bs' and (abs(hin)<1e-6) != (abs(hout)<1e-6):
                din=P[i]-P[i-1]; dout=P[(i+1)%n]-P[i]
                if abs(hin)<1e-6:   # previous edge fixed, next edge shifted
                    q=inter(P[i],din,P[i]+np.array([hout,0.0]),dout)
                else:
                    q=inter(P[i],dout,P[i]+np.array([hin,0.0]),din)
                if q is not None and math.hypot(*(q-P[i]))<=3*s+1:
                    new[a+i]=q; continue
            if hin*hout>=0: h=hin if abs(hin)>abs(hout) else hout
            else: h=(hin+hout)/2
            new[a+i,0]=P[i,0]+h
    # bbox-preserving rescale along the slant axis
    if s>0 and mode=='bs':
        u=pts[:,0]-pts[:,1]*slant; un=new[:,0]-new[:,1]*slant
        un=np.clip(un,u.min(),u.max()); new[:,0]=un+new[:,1]*slant
    elif s>0:
        u=pts[:,0]-pts[:,1]*slant; un=new[:,0]-new[:,1]*slant
        lo,hi=u.min(),u.max(); nlo,nhi=un.min(),un.max()
        k=(hi-lo)/(nhi-nlo)
        un=lo+(un-nlo)*k
        new[:,0]=un+new[:,1]*slant
    return [(int(round(x)),int(round(y))) for x,y in new]

def find_matches(font, base, tol=1):
    """Yield (glyphname, base_contour_index, (start,end)) of contours elsewhere
    in the font that equal a contour of `base` up to translation."""
    glyf=font['glyf']; B=glyf[base]; Bc=np.array(B.coordinates)
    bcs=[(i,r) for i,r in enumerate(contours(B))]
    for gn in font.getGlyphOrder():
        if gn==base: continue
        G=glyf[gn]
        if G.isComposite() or G.numberOfContours<=0: continue
        Gc=np.array(G.coordinates)
        for (a,b) in contours(G):
            for bi,(ba,bb) in bcs:
                if bb-ba!=b-a: continue
                off=Gc[a]-Bc[ba]
                if np.abs(Gc[a:b]-Bc[ba:bb]-off).max()<=tol:
                    yield gn,bi,(a,b); break

def apply_with_propagation(font, base, newcoords, log=None):
    glyf=font['glyf']; B=glyf[base]
    old=np.array(B.coordinates); new=np.array(newcoords)
    delta=new-old; br=contours(B)
    matches=list(find_matches(font,base))
    from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
    B.coordinates=GlyphCoordinates([tuple(map(int,p)) for p in new])
    touched={base}
    for gn,bi,(a,b) in matches:
        G=glyf[gn]; c=np.array(G.coordinates)
        ba,bb=br[bi]; c[a:b]+=delta[ba:bb]
        G.coordinates=GlyphCoordinates([tuple(map(int,p)) for p in c]); touched.add(gn)
    for gn in touched:
        glyf[gn].recalcBounds(glyf)
        lsb=glyf[gn].xMin if glyf[gn].numberOfContours else 0
        adv=font['hmtx'][gn][0]; font['hmtx'][gn]=(adv,lsb)
    return touched
