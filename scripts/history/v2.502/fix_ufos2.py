import math
import ufoLib2
from ufoLib2.objects import Anchor

ROOT = r"C:\Users\Mark\arbor-mono\sources"
STYLES = ["Regular", "Bold", "Italic", "BoldItalic"]
CAP, XH = 714, 536
# 1-unit nudges where base and mark anchors line up so exactly that the mark
# offset is (0, 0) and shaperglot cannot tell the mark was attached.
NUDGE = {"Bold": [("eng", "top", 317)], "BoldItalic": [("uni026F", "top", 321)]}

for style in STYLES:
    path = f"{ROOT}\\ArborMono-{style}.ufo"
    f = ufoLib2.Font.open(path)
    log = []
    cats = f.lib.setdefault("public.openTypeCategories", {})
    order = f.lib.setdefault("public.glyphOrder", [])
    t = math.tan(math.radians(-(f.info.italicAngle or 0)))

    # dotted circle: center anchor so the _center overlay marks (U+0334-0338) attach
    dc = f["uni25CC"]
    if not any(a.name == "center" for a in dc.anchors):
        b = dc.getBounds(f)
        dc.anchors.append(Anchor(x=round((b.xMin + b.xMax) / 2), y=round((b.yMin + b.yMax) / 2), name="center"))
        log.append("uni25CC center anchor")

    # uniA78D had an anchor but no category, so ufo2ft left it out of the mark feature
    for n in ("uniA78D", "uni2212", "uni2183"):
        if n in f and n not in cats:
            cats[n] = "base"

    for gname, aname, x in NUDGE.get(style, []):
        for a in f[gname].anchors:
            if a.name == aname:
                a.x = x
        log.append(f"{gname} {aname} x->{x}")

    # U+A7CB LATIN CAPITAL LETTER RAMS HORN, from uni0264: the loop is kept,
    # everything above the neck is stretched from x-height to cap height.
    if "uniA7CB" not in f:
        src = f["uni0264"]
        counter_top = min(max(p.y for p in c) for c in src.contours)  # the inner counter is the shorter contour
        yc = counter_top + 15
        k = (CAP - yc) / (XH - yc)

        def tf(x, y):
            x0 = x - y * t  # unslant
            y2 = y if y <= yc else yc + (y - yc) * k
            return round(x0 + y2 * t), round(y2)

        g = f.newGlyph("uniA7CB")
        g.width = src.width
        g.unicodes = [0xA7CB]
        pen = g.getPointPen()
        for c in src.contours:
            pen.beginPath()
            for p in c:
                pen.addPoint(tf(p.x, p.y), segmentType=p.type, smooth=p.smooth)
            pen.endPath()
        for a in src.anchors:
            x, y = tf(a.x, a.y)
            g.anchors.append(Anchor(x=x, y=y, name=a.name))
        cats["uniA7CB"] = "base"
        if "uniA7CB" not in order:
            order.insert(order.index("uni0264") + 1 if "uni0264" in order else len(order), "uniA7CB")
        log.append(f"uniA7CB added (stretch above y={yc}, k={k:.3f}, anchors {[(a.name, a.x, a.y) for a in g.anchors]})")

    f.save(path, overwrite=True)
    print(style, "; ".join(log))
