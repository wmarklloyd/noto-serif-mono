from pathlib import Path
from PIL import ImageFont,ImageDraw,Image
from fontTools.ttLib import TTFont
import unicodedata as ud
import csv,sys,statistics
before,after=map(Path,sys.argv[1:3])
outfile=Path(sys.argv[3])
styles=("Regular","Bold","Italic","BoldItalic")
with outfile.open("w",newline="") as stream:
    writer=csv.writer(stream)
    writer.writerow(["style","codepoint","character","unicode_category","advance","before_ink",
        "after_ink","Noto_ink","before_ink_per_bbox","after_ink_per_bbox","ink_retention_vs_Noto"])
    for style in styles:
        name=f"ArborMono-{style}.ttf"
        a=TTFont(before/name); b=TTFont(after/name)
        cmap=a.getBestCmap();assert cmap==b.getBestCmap()
        assert all(a["hmtx"][n][0]==b["hmtx"][n][0] for n in a.getGlyphOrder())
        origin=Path(f"/usr/share/fonts/truetype/noto/NotoSerif-{style}.ttf")
        src_cmap=TTFont(origin).getBestCmap()
        fa,fb,fs=[ImageFont.truetype(str(p),96,layout_engine=ImageFont.Layout.BASIC) for p in (before/name,after/name,origin)]
        def measure(face,c):
            mask=face.getmask(c)
            area=sum(bytes(mask))/255
            w,h=mask.size
            return area,area/(w*h) if w*h else 0
        stats={}
        for cp,n in sorted(cmap.items()):
            c=chr(cp)
            p,pdensity=measure(fa,c);q,qdensity=measure(fb,c)
            r=measure(fs,c)[0] if cp in src_cmap else 0
            ratio=p/r if r else None
            writer.writerow([style,f"U+{cp:04X}",c,ud.category(c),a["hmtx"][n][0],
                            round(p,2),round(q,2),round(r,2),round(pdensity,3),
                            round(qdensity,3),round(ratio,4) if ratio is not None else ""])
            if ratio is not None and "A"<=c<="z" and c.isalpha():
                stats[c]=round(ratio,2)
        print(style,len(cmap),sorted(stats.items(),key=lambda x:x[1])[:13])
