"""Flag heuristic anchors that are off-centre without an ascender/descender to justify it."""
import math, sys, unicodedata as ud
import ufoLib2
SRC = "C:/Users/Mark/arbor-mono/sources"
BAK = sys.argv[1]
LIMIT = 50

def body(g, a, ch):
    """Height of the letter body the centre line runs through."""
    return 714 if ud.category(ch) in ("Lu", "Lt") else 536

def centre(g, y, H, t):
    return g.width / 2 + (y - H / 2) * t

def classify(f, b, t):
    rows = []
    for n in f.keys():
        if n in b and b[n].anchors: continue
        g = f[n]
        if not g.unicodes or not g.anchors: continue
        ch = chr(g.unicodes[0])
        H = body(g, None, ch)
        for a in g.anchors:
            if a.name not in ("top", "bottom"): continue
            justified = (a.name == "top" and a.y > H + 30) or (a.name == "bottom" and a.y < -150)
            d = a.x - centre(g, a.y, H, t)
            if abs(d) > LIMIT and not justified:
                rows.append((n, a.name, a.x, a.y, round(d), ud.name(ch, "")))
    return rows

if __name__ == "__main__":
    for style in ["Regular", "Bold", "Italic", "BoldItalic"]:
        f = ufoLib2.Font.open(f"{SRC}/ArborMono-{style}.ufo")
        b = ufoLib2.Font.open(f"{BAK}/ArborMono-{style}.ufo")
        t = math.tan(math.radians(-(f.info.italicAngle or 0)))
        rows = classify(f, b, t)
        print(f"{style}: {len(rows)} unjustified off-centre anchors")
        for r in rows: print("   ", r)
