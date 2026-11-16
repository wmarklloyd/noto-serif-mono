"""Add top/bottom anchors to letters that have none, following Arbor Mono's conventions.

top y   : x-height 536 / cap height 714 / ascender 760 when the glyph top is near one,
          otherwise the glyph's own top (superscripts etc.)
bottom y: baseline 0, or the glyph bottom when it descends or floats (superscripts)
x       : centre of the ink in a band at that edge (so 'b'-like shapes get the
          anchor over the stem, and italics follow the slant automatically)
"""
import sys
import unicodedata as ud
import ufoLib2
from ufoLib2.objects import Anchor
from fontTools.pens.basePen import BasePen

ROOT = r"C:\Users\Mark\arbor-mono\sources"
HEIGHTS = [536, 714, 760]
BAND = 0.15
dry = "--dry" in sys.argv


class Sampler(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.pts = []
        self.cur = None

    def _moveTo(self, p):
        self.cur = p; self.pts.append(p)

    def _lineTo(self, p):
        a = self.cur
        for i in range(1, 9):
            t = i / 8
            self.pts.append((a[0] + (p[0] - a[0]) * t, a[1] + (p[1] - a[1]) * t))
        self.cur = p

    def _curveToOne(self, b, c, d):
        a = self.cur
        for i in range(1, 13):
            t = i / 12; u = 1 - t
            self.pts.append((u**3*a[0] + 3*u*u*t*b[0] + 3*u*t*t*c[0] + t**3*d[0],
                             u**3*a[1] + 3*u*u*t*b[1] + 3*u*t*t*c[1] + t**3*d[1]))
        self.cur = d

    def _qCurveToOne(self, b, c):
        a = self.cur
        for i in range(1, 9):
            t = i / 8; u = 1 - t
            self.pts.append((u*u*a[0] + 2*u*t*b[0] + t*t*c[0], u*u*a[1] + 2*u*t*b[1] + t*t*c[1]))
        self.cur = c


def band_center(pts, lo, hi):
    xs = [x for x, y in pts if lo <= y <= hi]
    return round((min(xs) + max(xs)) / 2)


def wants_anchors(g, cats):
    if not g.unicodes or g.anchors or cats.get(g.name) == "mark":
        return False
    ch = chr(g.unicodes[0])
    return (ud.category(ch) in ("Lu", "Ll", "Lt", "Lo")
            and ud.name(ch, "").startswith(("LATIN", "GREEK", "CYRILLIC")))


for style in ["Regular", "Bold", "Italic", "BoldItalic"]:
    path = f"{ROOT}\\ArborMono-{style}.ufo"
    f = ufoLib2.Font.open(path)
    cats = f.lib["public.openTypeCategories"]
    done, skipped = [], []
    for g in f:
        if not wants_anchors(g, cats):
            continue
        b = g.getBounds(f)
        if b is None:
            skipped.append(g.name); continue
        s = Sampler(f); g.draw(s)
        h = b.yMax - b.yMin
        top_y = next((y for y in HEIGHTS if abs(b.yMax - y) <= 30), round(b.yMax))
        bot_y = 0 if abs(b.yMin) <= 20 else round(b.yMin)
        top_x = band_center(s.pts, b.yMax - BAND * h, b.yMax)
        bot_x = band_center(s.pts, b.yMin, b.yMin + BAND * h)
        g.anchors.append(Anchor(x=bot_x, y=bot_y, name="bottom"))
        g.anchors.append(Anchor(x=top_x, y=top_y, name="top"))
        cats[g.name] = "base"
        done.append((g.name, bot_x, bot_y, top_x, top_y))
    if not dry:
        f.save(path, overwrite=True)
    print(f"{style}: {len(done)} glyphs anchored, skipped {skipped}")
    for row in done[:6] + [d for d in done if d[0] in ("uniA7AE", "uniA72C", "uniAB53", "uni047C", "uniA640")]:
        print("   ", row)
