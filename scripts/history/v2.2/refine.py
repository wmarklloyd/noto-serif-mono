from pathlib import Path
from tempfile import TemporaryDirectory
import sys,unicodedata as ud
from fontTools.ttLib import TTFont
from ttfautohint import StemWidthMode,ttfautohint

def clip(x):
    return max(0,min(1,x))

def adjust(c,x,y,stage):
    if stage==1:
        if c == "I":
            return -12*clip((abs(y-357)-245)/95)*clip((287+.195*(y-357)-x)/122)
        if c == "L":
            return 14*clip((x-365)/160)*clip((185-y)/145)
        if c == "F":
            return 11*clip((x-355)/140)*clip((y-455)/210)
    if stage==2:
        if c == "L":
            return -9*clip((x-365)/160)*clip((185-y)/145)
        if c == "J":
            return -6*clip((y+215)/215) + 13*clip((x-405)/130)*clip((y-580)/130)
        if c == "j":
            return 8*clip((x-230)/120)*clip((y-390)/140)
    if stage==3:
        if c == "J":
            return 4*clip((y+215)/215)*clip((670-y)/110)
        if c == "V":
            return 12*clip((x-290)/140)*clip((625-y)/200)
        if c == "W":
            return 10*clip((x-290)/145)*clip((635-y)/185)
    if stage==4:
        if c == "A":
            return -8*clip(1-abs(y-420)/240)*clip((255+.4*y-x)/100)
        if c == "r":
            return 11*clip((x-245)/160)*clip((y-365)/140)
        if c == "t":
            return -10*clip((235-x)/125)*clip(1-abs(y-510)/120)
        if c == "i":
            return -9*clip((258-x)/135)*clip((120-y)/100)
    if stage==5:
        if c == "t":
            return 5*clip((235-x)/125)*clip(1-abs(y-510)/120)
        if c == "Z":
            return -8*clip((y-470)/210)*clip((320-x)/175)
        if c == "e":
            return 7*clip((x-285)/170)*clip(1-abs(y-190)/210)
        if c == "k":
            return -7*clip((250-x)/150)*clip((630-y)/140)
    return 0

def build(source, target, stage):
    f=TTFont(source)
    done=set()
    families={}
    for cp,n in f.getBestCmap().items():
        if n in done: continue
        c=ud.normalize('NFD',chr(cp))[0]
        c={'Ι':'I','І':'I','Ї':'I','Ј':'J','Α':'A','А':'A','Ε':'E','Е':'E'}.get(c,c)
        families[n]=c
        g=f['glyf'][n]
        if g.isComposite() or not g.numberOfContours: continue
        xy=[(round(x+adjust(c,x,y,stage)),y) for x,y in g.coordinates]
        if xy!=list(g.coordinates):
            for i,p in enumerate(xy):g.coordinates[i]=p
            g.recalcBounds(f['glyf'])
            f['hmtx'][n]=(f['hmtx'][n][0],g.xMin)
        done.add(n)
    for lookup in f["GPOS"].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            sub=getattr(sub,"ExtSubTable",sub)
            if not hasattr(sub,"BaseCoverage"):
                continue
            for n,rec in zip(sub.BaseCoverage.glyphs,sub.BaseArray.BaseRecord):
                for a in rec.BaseAnchor:
                    if a is not None and n in families:
                        a.XCoordinate=round(a.XCoordinate+adjust(
                            families[n],a.XCoordinate,a.YCoordinate,stage))
    for n in f.getGlyphOrder(): f['glyf'][n].removeHinting()
    for tag in ('fpgm','prep','cvt ','gasp'):
        if tag in f: del f[tag]
    f['head'].fontRevision=2.2
    for n in f['name'].names:
        if n.nameID in (3,5):n.string=n.toUnicode().replace('2.100','2.200')
    mode=StemWidthMode.NATURAL
    with TemporaryDirectory() as tmp:
        raw=Path(tmp)/source.name
        f.save(raw)
        ttfautohint(in_file=str(raw),out_file=str(target),hinting_range_min=7,hinting_range_max=72,
                    hinting_limit=220,increase_x_height=0,windows_compatibility=True,no_info=True,
                    gray_stem_width_mode=mode,gdi_cleartype_stem_width_mode=mode,dw_cleartype_stem_width_mode=mode)

if __name__=='__main__':
    src,dst,stage=sys.argv[1:]
    for f in Path(src).glob('*.ttf'):
        build(f,Path(dst)/f.name,int(stage))
