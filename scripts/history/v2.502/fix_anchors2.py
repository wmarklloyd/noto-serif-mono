"""Second pass over the heuristic anchors from fix_anchors.py, to match the hand-placed convention:
- bottom anchors on short tails (-150 < y < 100) go to the baseline, like Ц and Д
- anchors with no ascender/descender to sit over are centred on the letter body,
  following the italic slant through the body's mid-height (like Ъ, Ѣ, Q)
Only glyphs that had no anchors in the original sources are touched.
"""
import math, sys, unicodedata as ud
import ufoLib2
SRC = "C:/Users/Mark/arbor-mono/sources"
BAK = sys.argv[1]
dry = "--dry" in sys.argv
for style in ["Regular", "Bold", "Italic", "BoldItalic"]:
    path = f"{SRC}/ArborMono-{style}.ufo"
    f = ufoLib2.Font.open(path)
    b = ufoLib2.Font.open(f"{BAK}/ArborMono-{style}.ufo")
    t = math.tan(math.radians(-(f.info.italicAngle or 0)))
    moved = 0
    for n in f.keys():
        if n in b and b[n].anchors:
            continue
        g = f[n]
        if not g.unicodes or not g.anchors:
            continue
        H = 714 if ud.category(chr(g.unicodes[0])) in ("Lu", "Lt") else 536
        for a in g.anchors:
            if a.name not in ("top", "bottom"):
                continue
            old = (a.x, a.y)
            if a.name == "bottom" and -150 < a.y < 100:
                a.y = 0
            justified = (a.name == "top" and a.y > H + 30) or (a.name == "bottom" and a.y < -150)
            if not justified:
                a.x = round(g.width / 2 + (a.y - H / 2) * t)
            if (a.x, a.y) != old:
                moved += 1
    if not dry:
        f.save(path, overwrite=True)
    print(f"{style}: {moved} anchors moved")
