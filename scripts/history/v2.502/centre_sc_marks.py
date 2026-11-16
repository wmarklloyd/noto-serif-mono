"""Centre the ink of acutecomb.sc / gravecomb.sc / uni030B.sc on their _top anchor
(unslanted about the anchor height in italics), as the precomposed small caps do."""
import math, sys, ufoLib2
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from sampler import Sampler
styles = sys.argv[1:] or ["Regular", "Bold", "Italic", "BoldItalic"]
for st in styles:
    f = ufoLib2.Font.open(f"C:/Users/Mark/arbor-mono/sources/ArborMono-{st}.ufo")
    t = math.tan(math.radians(-(f.info.italicAngle or 0)))
    for n in ["acutecomb.sc", "gravecomb.sc", "uni030B.sc"]:
        g = f[n]; s = Sampler(f); g.draw(s)
        a = [x for x in g.anchors if x.name == "_top"][0]
        us = [x - (y - a.y) * t for x, y in s.pts]
        cx = (min(us) + max(us)) / 2
        d = round(cx - a.x)
        for x in g.anchors: x.x += d
        print(st, n, f"{d:+d}")
    f.save()
