"""Inventory both slanted faces and compare horizontal ink clearance."""
import csv
from pathlib import Path
from PIL import ImageFont
from fontTools.ttLib import TTFont
from refine import stems_at

root = Path(__file__).parent
latin = "".join(map(chr,range(33,127)))
sizes = (12, 14, 16, 18, 24, 32)
with (root/"Italic-inventory.csv").open("w", newline="") as out, (
        root/"Italic-pair-clearance.csv").open("w", newline="") as pairs:
    writer, pair_writer = csv.writer(out), csv.writer(pairs)
    writer.writerow(["style","codepoint","character","advance","old_left","old_right",
                     "new_left","new_right","outline_changed"])
    pair_writer.writerow(["style","pair","old_min_clearance","new_min_clearance"])
    for style in ("Italic","BoldItalic"):
        path = f"ArborMono-{style}.ttf"
        paths = [folder/path for folder in (root.parent/"v17"/"natural",root/"natural")]
        a,b = map(TTFont,paths)
        cmap = a.getBestCmap()
        assert cmap == b.getBestCmap()
        assert a.getGlyphOrder() == b.getGlyphOrder()
        assert all(a["hmtx"][n][0] == b["hmtx"][n][0] for n in a.getGlyphOrder())
        changed = 0
        for cp,n in sorted(cmap.items()):
            g,h = a["glyf"][n], b["glyf"][n]
            width,l0 = a["hmtx"][n]
            _,l1 = b["hmtx"][n]
            r0,r1 = (width-left-(getattr(glyph,"xMax",0)-getattr(glyph,"xMin",0))
                     for glyph,left in ((g,l0),(h,l1)))
            differs = g.getCoordinates(a["glyf"])[0] != h.getCoordinates(b["glyf"])[0]
            writer.writerow([style,f"U+{cp:04X}",chr(cp),width,l0,r0,l1,r1,differs])
            changed += differs
        assert all(a["glyf"][cmap[cp]].coordinates == b["glyf"][cmap[cp]].coordinates
                   for cp in range(48,58))
        raster = [ImageFont.truetype(str(p),1000) for p in paths]
        ys = tuple(range(-240,925,5))
        def edge_profiles(face, c):
            mask,(x,top) = face.getmask2(c,anchor="ls")
            payload, width = bytes(mask), mask.size[0]
            sides = {}
            for y in ys:
                pos = -y-top
                if 0 <= pos < mask.size[1]:
                    ink = [x+i for i,value in enumerate(payload[pos*width:(pos+1)*width]) if value>=128]
                    if ink:
                        sides[y]=(ink[0],ink[-1]+1)
            return sides
        profiles = [{c:edge_profiles(face,c) for c in latin} for face in raster]
        def clearance(profile, left, right):
            l,r = profile[left],profile[right]
            return min((563+r[y][0]-l[y][1] for y in l.keys() & r.keys()), default=None)
        overlaps = []
        for left in latin:
            for right in latin:
                old,new = (clearance(profile,left,right) for profile in profiles)
                pair_writer.writerow([style,left+right,old,new])
                if new is not None and new < 0 and (old is None or new < min(0,old)):
                    overlaps.append((left+right,old,new))
        digit_changes = []
        for size in sizes:
            f0,f1 = [ImageFont.truetype(str(p),size) for p in paths]
            for char in "0123456789":
                m0,xy0=f0.getmask2(char)
                m1,xy1=f1.getmask2(char)
                if (bytes(m0),xy0)!=(bytes(m1),xy1):
                    digit_changes.append((size,char))
        print(style, "changed codepoints",changed, "new/worsened intersections",overlaps,
              "figure bitmap changes",digit_changes)
        for y in (30,300,685):
            print(y, [[563+stems_at(face,r,y)[0][0]-stems_at(face,l,y)[-1][1]
                       for l,r in ("GH","HI","IJ")] for face in raster])
