"""Make the smcp/c2sc substitutes of combining marks (acutecomb.sc ...) real zero-width
marks: move outlines to the plain mark's x position, copy its anchors (top anchor y
follows the .sc ink), mark them 'mark' in public.openTypeCategories."""
import re, ufoLib2
for st in ["Regular", "Bold", "Italic", "BoldItalic"]:
    f = ufoLib2.Font.open(f"C:/Users/Mark/arbor-mono/sources/ArborMono-{st}.ufo")
    bk = ufoLib2.Font.open(f"C:/Users/Mark/arbor-mono-backup/sources-pre-anchor-fit/ArborMono-{st}.ufo")
    cats = f.lib.setdefault("public.openTypeCategories", {})
    pairs = sorted(set((a, b) for a, b in re.findall(r"sub (\S+) by (\S+\.sc);", f.features.text) if cats.get(a) == "mark"))
    for a, b in pairs:
        A, B = f[a], f[b]
        B.clearContours()
        for c in bk[b].contours: B.appendContour(c.copy() if hasattr(c, "copy") else c)
        B.width = bk[b].width
        ka = [len(c.points) for c in A.contours]; kb = [len(c.points) for c in B.contours]
        if ka != kb:
            print(st, b, "shape differs", ka, kb); continue
        ba = A.getBounds(f); bb = bk[b].getBounds(bk)
        dx = round(((ba[0] + ba[2]) - (bb[0] + bb[2])) / 2); dy = ba[3] - bb[3]
        same_x = abs((ba[2] - ba[0]) - (bb[2] - bb[0])) < 2
        for c in B.contours:
            for p in c.points: p.x += dx
        B.width = 0
        B.clearAnchors()
        for an in A.anchors:
            y = an.y if an.name.startswith("_") else an.y - dy
            B.appendAnchor({"name": an.name, "x": an.x, "y": y})
        cats[b] = "mark"
        print(st, b, f"dx={dx:+.0f} dy={-dy:+.0f}", "" if same_x else "(x-shape differs)")
    f.save()
