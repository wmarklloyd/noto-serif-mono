from pathlib import Path
from tempfile import TemporaryDirectory
import sys
from fontTools.ttLib import TTFont
from ttfautohint import StemWidthMode,ttfautohint

# Each group lists contour points along one edge of an existing stroke.
# Displacements taper into feet, shoulders or serif joins.
EDGES = {
    "Italic": {
        "M": [(35,[-7,-16,-19]), (40,[22,22,17,13,5])],
        "N": [(15,[-15,-13,-10,-6,-2]), (32,[14,15,11,8,3])],
        "U": [(29,[-4,-8,-12,-13,-9,-6,-2])],
        "W": [(28,[-5,-9,-10,-10,-7,-4,-2])],
        "m": [(3,[-6,-8,-8,-8,-8,-8,-6,-5]), (17,[8,8,8,8,8,8,8,8]),
              (41,[5,8,8,8])],
    },
    "BoldItalic": {
        "M": [(35,[-9,-18,-19]), (40,[33,33,27,21,14,6])],
        "N": [(15,[-19,-17,-14,-10,-6,-3]), (33,[20,20,18,12,8,3])],
        "W": [(29,[-4,-9,-11,-11,-8,-5,-3])],
        "m": [(3,[-7,-9,-9,-9,-9,-9,-8,-6,-5]), (17,[7,9,9,9,9,9,9]),
              (38,[5,8,9,9])],
    }
}

def build(src,dst,style):
    f=TTFont(src); cmap=f.getBestCmap(); glyf=f["glyf"]
    changes={}
    import unicodedata as ud
    related={"Μ":"M","М":"M","Ν":"N"}
    for cp,n in cmap.items():
        base=ud.normalize("NFD",chr(cp))[0]
        base=related.get(base,base)
        if base not in EDGES[style] or n in changes:
            continue
        g,ref=glyf[n],glyf[cmap[ord(base)]]
        if g.isComposite() or not g.numberOfContours:
            continue
        original=list(ref.coordinates) if n==cmap[ord(base)] else references[base]
        candidate=list(g.coordinates)
        # Accented forms qualify when the original contour is present in
        # the same point order. Its accent points are left intact.
        length=len(original)
        offsets=[k for k in (0,len(candidate)-length) if k>=0 and k+length<=len(candidate) and
                 all(abs(x-X)<=18 and y==Y for (x,y),(X,Y) in
                     zip(candidate[k:k+length],original))]
        if not offsets:
            continue
        start=offsets[0]
        for index,deltas in EDGES[style][base]:
            for k,delta in enumerate(deltas,start+index):
                x,y=g.coordinates[k];g.coordinates[k]=(x+delta,y)
        g.recalcBounds(glyf)
        f["hmtx"][n]=(f["hmtx"][n][0],g.xMin)
        changes[n]=base
    for n in f.getGlyphOrder():
        glyf[n].removeHinting()
    for tag in ("fpgm","prep","cvt ","gasp"):
        if tag in f:del f[tag]
    f["head"].fontRevision=2.3
    for n in f["name"].names:
        if n.nameID in (3,5):n.string=n.toUnicode().replace("2.200","2.300")
    with TemporaryDirectory() as tmp:
        p=Path(tmp)/src.name;f.save(p);mode=StemWidthMode.NATURAL
        ttfautohint(in_file=str(p),out_file=str(dst),hinting_range_min=7,hinting_range_max=72,
                    hinting_limit=220,increase_x_height=0,windows_compatibility=True,no_info=True,
                    gray_stem_width_mode=mode,gdi_cleartype_stem_width_mode=mode,dw_cleartype_stem_width_mode=mode)
    print(style,changes)

if __name__=="__main__":
    source,out=map(Path,sys.argv[1:])
    for style in EDGES:
        name=f"ArborMono-{style}.ttf"
        f=TTFont(source/name)
        references={c:list(f["glyf"][f.getBestCmap()[ord(c)]].coordinates) for c in EDGES[style]}
        build(source/name,out/name,style)
