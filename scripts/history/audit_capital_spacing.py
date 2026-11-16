"""Compare v1.2 and v1.3 outlines, metrics and rasterized spacing."""
from pathlib import Path
import csv
import sys
import unicodedata as ud

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

before, after = map(Path, sys.argv[1:3])
ui = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
proof = Image.new("RGB", (1240, 1130), "#fcfaf5")
draw = ImageDraw.Draw(proof)
draw.text((28, 20), "Arbor Mono  |  Capital spacing  |  1.2 → 1.3", "#181410",
          font=ImageFont.truetype(ui, 30))
label = ImageFont.truetype(ui, 15)
samples = ["abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ",
           "GH HI IJ JK  HILL  HIJACK  JIG  FIJI  HIGH",
           "Í Î Į Ĵ Ĥ  Η Ι Ί Ἰ Ϊ  Н І Ї Ј Ӏ  ijl"]
with (after/"Spacing-inventory.csv").open("w", newline="") as out:
    writer = csv.writer(out)
    writer.writerow(["style", "codepoint", "character", "name", "category",
                     "advance", "old_lsb", "old_rsb", "new_lsb", "new_rsb",
                     "outline_changed"])
    for row, path in enumerate(sorted(before.glob("*.ttf"),
                                     key=lambda p: ["Regular","Bold","Italic","BoldItalic"].index(p.stem.split("-")[1]))):
        a, b = TTFont(path), TTFont(after/path.name)
        style = path.stem.split("-")[1]
        cmap = a.getBestCmap()
        assert cmap == b.getBestCmap()
        assert a["hmtx"].metrics.keys() == b["hmtx"].metrics.keys()
        assert all(v[0] == b["hmtx"][n][0] for n,v in a["hmtx"].metrics.items())
        changed = set()
        for n in a.getGlyphOrder():
            g, h = a["glyf"][n], b["glyf"][n]
            if g.getCoordinates(a["glyf"])[0] != h.getCoordinates(b["glyf"])[0]:
                changed.add(n)
        assert not changed.intersection(cmap[ord(c)] for c in "0123456789iljt")
        for cp,n in sorted(cmap.items()):
            wa, la = a["hmtx"][n]
            wb, lb = b["hmtx"][n]
            g, h = a["glyf"][n], b["glyf"][n]
            ra = wa-la-(getattr(g,"xMax",0)-getattr(g,"xMin",0))
            rb = wb-lb-(getattr(h,"xMax",0)-getattr(h,"xMin",0))
            writer.writerow([style,f"U+{cp:04X}",chr(cp),ud.name(chr(cp),""),ud.category(chr(cp)),
                             wa,la,ra,lb,rb,n in changed])
        print(style, len(cmap), len(changed), [(c,
            a["hmtx"][c][1], a["glyf"][c].xMax, b["hmtx"][c][1], b["glyf"][c].xMax) for c in "HIJ"])
        y0 = 72+row*260
        draw.line((28,y0,1210,y0), fill="#cfcbc3")
        draw.text((28,y0+8),style,"#181410",font=label)
        for col, directory in enumerate([before,after]):
            x = 28+col*610
            draw.text((x+110,y0+8),["1.2","1.3"][col],"#6c5140",font=label)
            for idx,size in enumerate([14,18,24,34]):
                font = ImageFont.truetype(str(directory/path.name),size)
                y = y0+35+idx*32
                draw.text((x,y),str(size),"#6c5140",font=label)
                sample = samples[0] if size <= 18 else samples[1] if size==24 else "GH  HI  IJ  JK   HIJACK"
                draw.text((x+30,y-3),sample,"#181410",font=font)
            font = ImageFont.truetype(str(directory/path.name),25)
            draw.text((x+30,y0+178),samples[2],"#181410",font=font)
proof.save(after/"Capital-spacing-proof.png")
