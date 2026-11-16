"""Add U+24B6 CIRCLED LATIN CAPITAL LETTER A and U+24D0 CIRCLED LATIN SMALL LETTER A.

Ring: the outer two contours of the font's own copyright sign (an upright oval in
every style). Letter: the style's A or a, scaled by the ratio the copyright sign
uses for its C (456 units of a 714 cap height = 0.64), centred in the ring, and
reduced where needed so the whole letter keeps MARGIN units clear of the inner oval
(the letter may move up to SHIFT units vertically to find a larger fit). In the
italics the letter keeps its slant and is centred along the slant axis through the
ring's centre.
"""
import math
import ufoLib2
from ufoLib2.objects import Glyph, Contour, Point
from fontTools.pens.basePen import BasePen

ROOT = "C:/Users/Mark/arbor-mono/sources"
SCALE = 456 / 714
MARGIN = 40
SHIFT = 30
NEW = {"uni24B6": ("A", 0x24B6), "uni24D0": ("a", 0x24D0)}


class Sampler(BasePen):
    def __init__(self, gs):
        super().__init__(gs); self.pts = []; self.cur = None
    def _moveTo(self, p): self.cur = p; self.pts.append(p)
    def _lineTo(self, p): self.cur = p; self.pts.append(p)
    def _curveToOne(self, a, b, c):
        p0 = self.cur
        for i in range(1, 17):
            t = i / 16; u = 1 - t
            self.pts.append((u**3*p0[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0],
                             u**3*p0[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
        self.cur = c
    def _qCurveToOne(self, a, b):
        p0 = self.cur
        for i in range(1, 17):
            t = i / 16; u = 1 - t
            self.pts.append((u*u*p0[0] + 2*u*t*a[0] + t*t*b[0], u*u*p0[1] + 2*u*t*a[1] + t*t*b[1]))
        self.cur = b


for style in ["Regular", "Bold", "Italic", "BoldItalic"]:
    path = f"{ROOT}/ArborMono-{style}.ufo"
    f = ufoLib2.Font.open(path)
    t = math.tan(math.radians(-(f.info.italicAngle or 0)))
    ring = f["copyright"].contours[:2]
    rb = [p for c in ring for p in c.points]
    cx = (min(p.x for p in rb) + max(p.x for p in rb)) / 2
    cy = (min(p.y for p in rb) + max(p.y for p in rb)) / 2
    inner = [p for p in ring[1].points]
    ea = (max(p.x for p in inner) - min(p.x for p in inner)) / 2 - MARGIN
    eb = (max(p.y for p in inner) - min(p.y for p in inner)) / 2 - MARGIN
    order = f.lib["public.glyphOrder"]
    cats = f.lib["public.openTypeCategories"]
    for name, (src, cp) in NEW.items():
        s = Sampler(f); f[src].draw(s)
        ys = [y for x, y in s.pts]
        us = [x - y * t for x, y in s.pts]
        yc = (min(ys) + max(ys)) / 2
        uc = (min(us) + max(us)) / 2
        def place(k, off=0):
            dy = cy - k * yc + off
            dx = cx - cy * t - k * uc + dy * t
            return dx, dy
        def fits(k, off):
            dx, dy = place(k, off)
            return all(((k*x + dx - cx) / ea) ** 2 + ((k*y + dy - cy) / eb) ** 2 <= 1 for x, y in s.pts)
        best = (0, 0)
        for off in range(-SHIFT, SHIFT + 1, 5):
            k = SCALE
            while k > best[0] and not fits(k, off):
                k -= 0.005
            if k > best[0] or (k == best[0] and abs(off) < abs(best[1])):
                best = (k, off)
        k, off = best
        dx, dy = place(k, off)
        g = Glyph(name, width=f["copyright"].width, unicodes=[cp])
        for c in ring:
            g.contours.append(Contour([Point(p.x, p.y, p.type, p.smooth) for p in c.points]))
        for c in f[src].contours:
            g.contours.append(Contour([Point(round(p.x * k + dx), round(p.y * k + dy), p.type, p.smooth)
                                       for p in c.points]))
        if name in f:
            del f[name]
        f.addGlyph(g)
        if name not in order:
            order.append(name)
        cats.pop(name, None)
        print(style, name, 'scale', round(k, 3), 'shift', off)
    f.save(path, overwrite=True)
