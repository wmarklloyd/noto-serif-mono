import sys
import ufoLib2
from ufoLib2.objects import Component, Anchor

ROOT = r"C:\Users\Mark\arbor-mono\sources"
STYLES = {"Regular": 75, "Italic": 75, "Bold": 105, "BoldItalic": 105}
MARKS = ["uni0488", "uni0489", "uni1ABE", "uniA670", "uniA671", "uniA672"]

for style, thick in STYLES.items():
    path = f"{ROOT}\\ArborMono-{style}.ufo"
    f = ufoLib2.Font.open(path)
    log = []

    f.info.openTypeOS2WinDescent = max(f.info.openTypeOS2WinDescent or 0, 389)
    f.info.openTypeOS2VendorID = "ARBR"

    # U+2212 MINUS SIGN: same width as plus, centered on plus's vertical center
    if "uni2212" not in f:
        g = f.newGlyph("uni2212")
        g.width = 563
        g.unicodes = [0x2212]
        y0 = 357.5 - thick / 2
        y1 = 357.5 + thick / 2
        pen = g.getPen()
        pen.moveTo((67, y0)); pen.lineTo((67, y1)); pen.lineTo((496, y1)); pen.lineTo((496, y0)); pen.closePath()
        log.append("uni2212 added")

    # U+2183 ROMAN NUMERAL REVERSED ONE HUNDRED: mirror of U+2184
    if "uni2183" not in f and "uni2184" in f:
        g = f.newGlyph("uni2183")
        g.width = 563
        g.unicodes = [0x2183]
        g.components.append(Component("uni2184", transformation=(-1, 0, 0, 1, 563, 0)))
        log.append("uni2183 added")

    order = list(f.lib.get("public.glyphOrder", []))
    for n in ("uni2212", "uni2183"):
        if n in f and n not in order:
            order.append(n)

    cats = f.lib.setdefault("public.openTypeCategories", {})
    for m in MARKS:
        if m in f:
            cats[m] = "mark"
    log.append("mark categories set")

    if "uniA78D" in f:
        g = f["uniA78D"]
        if not any(a.name == "top" for a in g.anchors):
            b = g.getBounds(f)
            x = round((b.xMin + b.xMax) / 2)
            g.anchors.append(Anchor(x=x, y=714, name="top"))
            log.append(f"uniA78D top anchor at {x},714")

    if "uni00AD" in f:
        del f["uni00AD"]
        log.append("uni00AD removed")
    order = [n for n in order if n != "uni00AD"]
    cats.pop("uni00AD", None)
    for k in [k for k in f.kerning if "uni00AD" in k]:
        del f.kerning[k]
    for gname, members in f.groups.items():
        if "uni00AD" in members:
            f.groups[gname] = [m for m in members if m != "uni00AD"]
    f.lib["public.glyphOrder"] = order

    f.save(path, overwrite=True)
    print(style, "; ".join(log))
