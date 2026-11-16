import math
import ufoLib2
from ufoLib2.objects import Anchor

ROOT = r"C:\Users\Mark\arbor-mono\sources"
# glyph -> height its top anchor sits at (cap height or x-height), like I and omega
TARGETS = {"uniA7AE": 714, "uniA7B6": 714, "uniA7B7": 536}

for style in ["Regular", "Bold", "Italic", "BoldItalic"]:
    path = f"{ROOT}\\ArborMono-{style}.ufo"
    f = ufoLib2.Font.open(path)
    cats = f.lib["public.openTypeCategories"]
    t = math.tan(math.radians(-(f.info.italicAngle or 0)))
    log = []
    for n, h in TARGETS.items():
        g = f[n]
        cats[n] = "base"
        if g.anchors:
            continue
        b = g.getBounds(f)
        # horizontal center at mid-height, carried along the italic angle
        xmid = (b.xMin + b.xMax) / 2
        g.anchors.append(Anchor(x=round(xmid - (h / 2) * t), y=0, name="bottom"))
        g.anchors.append(Anchor(x=round(xmid + (h / 2) * t), y=h, name="top"))
        log.append(f"{n} {[(a.name, a.x, a.y) for a in g.anchors]}")
    f.save(path, overwrite=True)
    print(style, "; ".join(log))
