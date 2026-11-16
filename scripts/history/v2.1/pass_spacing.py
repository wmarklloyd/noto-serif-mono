from pathlib import Path
from tempfile import TemporaryDirectory
import sys,unicodedata as ud
from fontTools.ttLib import TTFont
from ttfautohint import StemWidthMode,ttfautohint

def clip(x):
    return max(0,min(1,x))

def adjust(c,x,y,stage):
    if stage==1:
        if c=='I':
            return 7+15*clip((abs(y-357)-215)/105)*max(-1,min(1,(x-(287+.195*(y-357)))/165))
        if c=='J':
            return 8*clip((y+240)/240)-15*clip((y-620)/94)*clip((285-x)/100)
        if c=='L':
            return 16*clip((x-345)/180)*clip((220-y)/190)
        if c=='F':
            return 13*clip((x-350)/170)*clip((y-490)/180)
    if stage==2:
        if c=="I":
            return -11*clip((abs(y-357)-220)/100)*clip((260+.195*(y-357)-x)/100)
        if c=='i':
            return -7+20*clip((100-y)/70)*max(-1,min(1,(x-240)/135))
        if c=='t':
            return 9*clip((x-260)/110)*clip((y-365)/125)
        if c=='r':
            return 24*clip((x-260)/160)*clip((y-350)/140)
    if stage==3:
        if c=='J':
            return -10*clip((y-570)/110)*clip((275-x)/115)
        if c=='W':
            return 13*clip((x-310)/120)*clip((675-y)/125)
        if c=='E':
            return -10
        if c=='A':
            return -7*clip((640-y)/130)*clip((330+.2*y-x)/145)
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
    if stage==3:
        # Earlier trial files keep the original anchors. Apply the three
        # horizontal outline transforms to base anchors when finalizing.
        for lookup in f["GPOS"].table.LookupList.Lookup:
            for sub in lookup.SubTable:
                sub=getattr(sub,"ExtSubTable",sub)
                if not hasattr(sub,"BaseCoverage"):
                    continue
                for n,rec in zip(sub.BaseCoverage.glyphs,sub.BaseArray.BaseRecord):
                    for a in rec.BaseAnchor:
                        if a is not None and n in families:
                            for pass_number in (1,2,3):
                                a.XCoordinate=round(a.XCoordinate+adjust(
                                    families[n],a.XCoordinate,a.YCoordinate,pass_number))
    for n in f.getGlyphOrder(): f['glyf'][n].removeHinting()
    for tag in ('fpgm','prep','cvt ','gasp'):
        if tag in f: del f[tag]
    f['head'].fontRevision=2.1
    for n in f['name'].names:
        if n.nameID in (3,5):n.string=n.toUnicode().replace('2.000','2.100')
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
