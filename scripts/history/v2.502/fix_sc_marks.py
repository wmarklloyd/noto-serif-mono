"""Centre misplaced mark contours on upright small-cap precomposed glyphs."""
import sys, ufoLib2
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from sampler import Sampler
FIX = {"uni1E73.sc": ("u.sc", "bot"), "uni1E75.sc": ("u.sc", "bot"), "uni1EE5.sc": ("u.sc", "bot"),
       "uni1EA1.sc": ("a.sc", "bot"), "uni1EAD.sc": ("a.sc", "bot"), "uni1EB7.sc": ("a.sc", "bot"),
       "uni01E9.sc": ("k.sc", "top"), "uni021F.sc": ("h.sc", "top"), "uni1E23.sc": ("h.sc", "top"),
       }
def pts(f, obj):
    s = Sampler(f); obj.draw(s); return s.pts
for st in ["Regular", "Bold", "Italic", "BoldItalic"]:
    up = st in ("Regular", "Bold")
    f = ufoLib2.Font.open(f"C:/Users/Mark/arbor-mono/sources/ArborMono-{st}.ufo")
    for g, (b, zone) in (FIX.items() if up else []):
        bp = pts(f, f[b]); top = max(y for x, y in bp) + 8; bot = min(y for x, y in bp) - 8
        bc = (min(x for x, y in bp) + max(x for x, y in bp)) / 2
        sel = [c for c in f[g].contours if all((p.y > top) if zone == "top" else (p.y < bot) for p in c.points)]
        xs = [x for c in sel for x, y in pts(f, c)]
        dx = round(bc - (min(xs) + max(xs)) / 2)
        if abs(dx) < 10:
            print(st, g, "ok", dx); continue
        for c in sel:
            for p in c.points: p.x += dx
        print(st, g, zone, len(sel), "contours", f"{dx:+d}")
    # ḋ.sc: its dot sits inside the D at small-cap height; place it as ṅ.sc places its dot
    for g in ([f["uni1E0B.sc"]]):
        dot = [c for c in g.contours if len(c.points) == 12][0]
        nd = [c for c in f["uni1E45.sc"].contours if min(p.y for p in c.points) > 560][0]
        def bb(o):
            P = pts(f, o); return min(x for x,y in P), min(y for x,y in P), max(x for x,y in P), max(y for x,y in P)
        n0 = bb(f["n.sc"]); d0 = bb(f["d.sc"]); nb = bb(nd); db = bb(dot)
        tx = (d0[0]+d0[2])/2 + ((nb[0]+nb[2])/2 - (n0[0]+n0[2])/2)
        dx = round(tx - (db[0]+db[2])/2); dy = round(nb[1] - db[1])
        for p in dot.points: p.x += dx; p.y += dy
        print(st, g.name, "dot", dx, dy)
    f.save()
