import io, numpy as np
from PIL import Image, ImageDraw, ImageFont
def font_bytes(tt):
    b=io.BytesIO(); tt.save(b); return b.getvalue()
def runs_glyph(tt, gname, y, SZ=1000):
    """Render one glyph outline directly (no cmap) via a temp font: use pen raster."""
    from fontTools.pens.basePen import BasePen
    gs=tt.getGlyphSet(); 
    from fontTools.pens.recordingPen import RecordingPen
    # analytic horizontal scanline intersection with flattened outline
    pts=[]
    class P(BasePen):
        def __init__(s):super().__init__(gs);s.c=[];s.all=[]
        def _moveTo(s,p):s.c=[p]
        def _lineTo(s,p):s.c.append(p)
        def _qCurveToOne(s,a,b):
            p0=s.c[-1]
            for i in range(1,17):
                t=i/16;s.c.append(tuple((1-t)**2*p0[k]+2*(1-t)*t*a[k]+t*t*b[k] for k in (0,1)))
        def _curveToOne(s,a,b,c):
            p0=s.c[-1]
            for i in range(1,17):
                t=i/16;s.c.append(tuple((1-t)**3*p0[k]+3*(1-t)**2*t*a[k]+3*(1-t)*t*t*b[k]+t**3*c[k] for k in (0,1)))
        def _closePath(s):s.all.append(s.c);s.c=[]
    p=P(); gs[gname].draw(p)
    xs=[]
    yy=y+0.5
    for poly in p.all:
        for (x0,y0),(x1,y1) in zip(poly,poly[1:]+poly[:1]):
            if (y0<=yy<y1) or (y1<=yy<y0):
                xs.append((x0+(yy-y0)*(x1-x0)/(y1-y0), 1 if y1>y0 else -1))
    xs.sort(); w=0; out=[]; start=None
    for x,d in xs:
        nw=w+d
        if w==0 and nw!=0: start=x
        if w!=0 and nw==0: out.append(round(x-start))
        w=nw
    return out

def segs(tt, gname, y, SZ=1000):
    """Render one glyph outline directly (no cmap) via a temp font: use pen raster."""
    from fontTools.pens.basePen import BasePen
    gs=tt.getGlyphSet(); 
    from fontTools.pens.recordingPen import RecordingPen
    # analytic horizontal scanline intersection with flattened outline
    pts=[]
    class P(BasePen):
        def __init__(s):super().__init__(gs);s.c=[];s.all=[]
        def _moveTo(s,p):s.c=[p]
        def _lineTo(s,p):s.c.append(p)
        def _qCurveToOne(s,a,b):
            p0=s.c[-1]
            for i in range(1,17):
                t=i/16;s.c.append(tuple((1-t)**2*p0[k]+2*(1-t)*t*a[k]+t*t*b[k] for k in (0,1)))
        def _curveToOne(s,a,b,c):
            p0=s.c[-1]
            for i in range(1,17):
                t=i/16;s.c.append(tuple((1-t)**3*p0[k]+3*(1-t)**2*t*a[k]+3*(1-t)*t*t*b[k]+t**3*c[k] for k in (0,1)))
        def _closePath(s):s.all.append(s.c);s.c=[]
    p=P(); gs[gname].draw(p)
    xs=[]
    yy=y+0.5
    for poly in p.all:
        for (x0,y0),(x1,y1) in zip(poly,poly[1:]+poly[:1]):
            if (y0<=yy<y1) or (y1<=yy<y0):
                xs.append((x0+(yy-y0)*(x1-x0)/(y1-y0), 1 if y1>y0 else -1))
    xs.sort(); w=0; out=[]; start=None
    for x,d in xs:
        nw=w+d
        if w==0 and nw!=0: start=x
        if w!=0 and nw==0: out.append((round(start),round(x)))
        w=nw
    return out
