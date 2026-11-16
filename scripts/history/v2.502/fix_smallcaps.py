"""Fill the small-cap gaps fontbakery's shape_languages check reports, and fix the
soft-dotted and Turkish small-cap shaping.

1. Soft-dotted: add the top marks that ccmp lookup L03 did not list, so i/j lose
   their dot before every top mark.
2. Small caps for letters that had none:
   - dotless i and long s map to the existing i.sc and s.sc;
   - letters with no decomposition are drawn from their capital, scaled to small-cap
     proportions (height x0.8 as in the existing small caps, width x0.87 so the
     stems match: capital stem 96 -> small-cap stem 83), unslanted first in italics;
   - accented letters reuse the designer's lowercase composite: its accent contours
     are moved from the lowercase base onto the small-cap base by the difference
     between their anchors (keeps the tuned Vietnamese stacking). When the base is
     not found intact in the composite (horn, ogonek welded on), the small cap is
     built from components and positioned through the mark anchors instead.
3. Turkish/Azeri/Crimean Tatar: declare the language systems, keep ccmp for them,
   and give smcp a dotted small-cap i.
"""
import math
import os
import re
import sys
import unicodedata as ud
import ufoLib2
from ufoLib2.objects import Anchor, Component

ROOT = r"C:\Users\Mark\arbor-mono\sources"
STYLES = ["Regular", "Bold", "Italic", "BoldItalic"]
SX, SY = 0.87, 0.8
dry = "--dry" in sys.argv

MISSING = ("0131 017F 0180 0183 0188 0192 0199 01A1 01A5 01AD 01B0 01B4 01B9 01CE 01D0 01D2 01D4 01D6 "
           "01D8 01DA 01DC 01DD 01E3 01E5 01E7 01E9 01EB 01EF 01F0 01F9 0201 0205 0209 020D 0213 0215 "
           "021F 0227 0229 0233 0242 0249 024D 0250 0251 0253 0254 0256 0257 0259 025B 0260 0263 0264 "
           "0265 0266 0268 0269 026A 026F 0272 0275 027D 0283 0288 0289 028A 028B 028C 0292 0298 029D "
           "1D7D 1E05 1E07 1E0B 1E0D 1E0F 1E13 1E15 1E1B 1E1F 1E23 1E25 1E2B 1E2D 1E2F 1E33 1E35 1E37 "
           "1E3D 1E3F 1E43 1E45 1E47 1E49 1E4B 1E4D 1E55 1E5B 1E61 1E63 1E6B 1E6D 1E6F 1E71 1E73 1E75 "
           "1E79 1E7D 1E7F 1E89 1E8B 1E91 1E93 1E96 1EA1 1EA3 1EA5 1EA7 1EA9 1EAB 1EAD 1EAF 1EB1 1EB3 "
           "1EB5 1EB7 1EB9 1EBB 1EBD 1EBF 1EC1 1EC3 1EC5 1EC7 1EC9 1ECB 1ECD 1ECF 1ED1 1ED3 1ED5 1ED7 "
           "1ED9 1EDB 1EDD 1EDF 1EE1 1EE3 1EE5 1EE7 1EE9 1EEB 1EED 1EEF 1EF1 1EF5 1EF7 1EF9 2C73 A78C "
           "A7B5 A7B7 A7C8").split()
ALIAS = {0x0131: "i.sc", 0x017F: "s.sc"}          # map to an existing small cap
CAPITAL = {0x0264: "uniA7CB", 0x0298: None}         # no Unicode uppercase mapping
DOTLESS = {"i": "dotlessi", "j": "uni0237"}
SOFT_DOTTED_TOP = ("uni1DC6 acutemacron uni0483 uni0484 uni0485 uni0486 uni0487 uni1AB0 uni1AB1 uni1AB2 "
                   "uni1AB3 uni1AB4 uni1ABB uni1ABC dottedgrave dottedacute suspensionmark uni1DC4 "
                   "gravemacron graveacutegrave acutegraveacute brevemacron").split()
TURKIC = ["TRK", "AZE", "CRT"]
SOFT_DOTTED_CHARS = set("iⅈᵢįịḭɨᶤjⅉʲⱼɉʝᶨϳіјᶖ")


def contour_key(c):
    return tuple((p.x, p.y, p.type) for p in c)


def same(a, b, tol=2, T=(0, 0)):
    return len(a) == len(b) and all(p[2] == q[2] and abs(p[0] + T[0] - q[0]) <= tol
                                    and abs(p[1] + T[1] - q[1]) <= tol for p, q in zip(a, b))


def found(c, keys, T=(0, 0)):
    k = contour_key(c)
    return any(same(k, o, T=T) for o in keys)


def placement(B, L, shift):
    """Translation T at which every contour of base B appears in composite L, or None.
    shift=False only accepts T=(0, 0); otherwise T comes from the first contour's match
    and must hold for every other contour."""
    lk = [contour_key(d) for d in L.contours]
    if not B.contours:
        return None
    if all(found(c, lk) for c in B.contours):
        return (0, 0)
    if not shift:
        return None
    k0 = contour_key(B.contours[0])
    for d in lk:
        if len(d) != len(k0):
            continue
        T = (d[0][0] - k0[0][0], d[0][1] - k0[0][1])
        if all(found(c, lk, T) for c in B.contours):
            return T
    return None


def anchors(g):
    return {a.name: (a.x, a.y) for a in g.anchors}


def copy_contour(pen, c, fn):
    pen.beginPath()
    for p in c:
        x, y = fn(p.x, p.y)
        pen.addPoint((x, y), segmentType=p.type, smooth=p.smooth)
    pen.endPath()


def process(style):
    path = f"{ROOT}\\ArborMono-{style}.ufo"
    f = ufoLib2.Font.open(path)
    t = math.tan(math.radians(-(f.info.italicAngle or 0)))
    cats = f.lib["public.openTypeCategories"]
    order = f.lib["public.glyphOrder"]
    cmap = {u: g.name for g in f for u in g.unicodes}
    if "--redo-components" in sys.argv:
        # rebuild the small caps an earlier run assembled from components
        targets = {cmap[int(h, 16)] + ".sc" for h in MISSING}
        for n in [n for n in targets if n in f and (f[n].components or os.environ.get("REDO") == "*" or n in os.environ.get("REDO", "").split(","))]:
            del f[n]
    log = {"design": [], "contours": [], "components": [], "alias": []}
    smcp, c2sc = {}, {}

    def scname(ch):
        if ord(ch) in ALIAS:
            return ALIAS[ord(ch)]
        n = cmap.get(ord(ch))
        return n and n + ".sc"

    def add_glyph(name, after):
        g = f.newGlyph(name)
        g.width = f[after].width if after in f else 563
        cats[name] = "base"
        if name not in order:
            order.append(name)
        return g

    def capital_of(ch):
        if ord(ch) in CAPITAL:
            return CAPITAL[ord(ch)]
        up = ch.upper()
        return cmap.get(ord(up)) if len(up) == 1 and up != ch else None

    chars = sorted((chr(int(h, 16)) for h in MISSING), key=lambda c: len(ud.normalize("NFD", c)))
    for ch in chars:
        lc = cmap[ord(ch)]
        cap = capital_of(ch)
        if ord(ch) in ALIAS:
            smcp[lc] = ALIAS[ord(ch)]
            log["alias"].append(lc)
            continue
        name = lc + ".sc"
        if name in f:
            smcp[lc] = name
            if cap and cap in f:
                c2sc[cap] = name
            continue
        nfd = ud.normalize("NFD", ch)
        if len(nfd) == 1:
            # ---- drawn from the capital (or, without one, from the letter itself)
            src = f[cap] if cap else f[lc]
            b = src.getBounds(f)
            sy = SY if cap else 571 / b.yMax
            g = add_glyph(name, src.name)
            # centre of the ink in unslanted space
            us = [(p.x - p.y * t) for c in src.contours for p in c]
            cx = (min(us) + max(us)) / 2
            mid = g.width / 2

            def tf(x, y):
                y2 = y * sy
                return round(mid + (x - y * t - cx) * SX + (y2 - 285.5) * t), round(y2)
            pen = g.getPointPen()
            for c in src.contours:
                copy_contour(pen, c, tf)
            for a in src.anchors:
                x, y = tf(a.x, a.y)
                g.anchors.append(Anchor(x=x, y=y, name=a.name))
            if not any(a.name == "top" for a in g.anchors):
                g.anchors.append(Anchor(x=round(mid + 285.5 * t), y=571, name="top"))
            if not any(a.name == "bottom" for a in g.anchors):
                g.anchors.append(Anchor(x=round(mid - 285.5 * t), y=0, name="bottom"))
            log["design"].append(f"{name}<-{src.name}")
        else:
            # candidate (composite, its base, small-cap base): the lowercase composite with
            # its longest decomposed prefix first; then the capital composite, whose flatter
            # accent arrangement keeps tall stacks inside the vertical metrics
            cands = []
            for k in range(len(nfd) - 1, 0, -1):
                pre = ud.normalize("NFC", nfd[:k])
                if len(pre) == 1 and ord(pre) in cmap:
                    cands.append((lc, cmap[ord(pre)], scname(pre)))
            base0 = cmap.get(ord(nfd[0]))
            if base0 in DOTLESS:
                cands.append((lc, DOTLESS[base0], base0 + ".sc"))
            if cap:
                for k in range(len(nfd) - 1, 0, -1):
                    pre = ud.normalize("NFC", nfd[:k])
                    upre = ud.normalize("NFC", nfd[:k].upper())
                    if len(pre) == 1 and len(upre) == 1 and ord(upre) in cmap:
                        cands.append((cap, cmap[ord(upre)], scname(pre)))
            chosen = None
            # exact placement first; a base the composite moved sideways only as a fallback
            for shift in (False, True):
                for ln, bn, sn in cands:
                    if bn in f and sn in f:
                        T = placement(f[bn], f[ln], shift)
                        if T is not None:
                            chosen = (ln, bn, sn, T)
                            break
                if chosen:
                    break
            if not chosen:
                # last resort: the composite redrew its base (italic stacks narrow it), so
                # split L by height and line the base groups up on their unslanted centres
                for ln, bn, sn in cands:
                    if bn in f and sn in f and f[bn].contours and "top" in anchors(f[bn]):
                        top = anchors(f[bn])["top"][1]
                        L = f[ln]
                        grp = [c for c in L.contours
                               if min(p.y for p in c) >= -40 and max(p.y for p in c) <= top + 40]
                        if sorted(map(len, grp)) != sorted(map(len, f[bn].contours)):
                            continue
                        def ucentre(cs):
                            us = [p.x - p.y * t for c in cs for p in c]
                            return (min(us) + max(us)) / 2
                        T = (round(ucentre(grp) - ucentre(f[bn].contours)), 0)
                        chosen = (ln, bn, sn, T, [c for c in L.contours if c not in grp])
                        break
            if chosen:
                ln, bn, sn, T = chosen[:4]
                L = f[ln]
                B, S = f[bn], f[sn]
                ba, sa = anchors(B), anchors(S)
                bkeys = [contour_key(c) for c in B.contours]
                extra = chosen[4] if len(chosen) > 4 else [c for c in L.contours if not found(c, bkeys, (-T[0], -T[1]))]
                # bring the accents back into the base's own frame
                ba = {k: (v[0] + T[0], v[1] + T[1]) for k, v in ba.items()}
                g = add_glyph(name, sn)
                pen = g.getPointPen()
                for c in S.contours:
                    copy_contour(pen, c, lambda x, y: (x, y))
                for comp in S.components:
                    g.components.append(Component(comp.baseGlyph, transformation=comp.transformation))
                split = ba.get("top", (0, 536))[1] / 2
                for c in extra:
                    ys = [p.y for p in c]
                    which = "top" if (min(ys) + max(ys)) / 2 > split else "bottom"
                    if which not in ba or which not in sa:
                        raise SystemExit(f"{style} {name}: no {which} anchor on {bn}/{sn}")
                    dx = sa[which][0] - ba[which][0]
                    dy = sa[which][1] - ba[which][1]
                    copy_contour(pen, c, lambda x, y: (x + dx, y + dy))
                la = anchors(L)
                for an, (x, y) in sa.items():
                    if an in la and an in ba:
                        x, y = x + la[an][0] - ba[an][0], y + la[an][1] - ba[an][1]
                    g.anchors.append(Anchor(x=round(x), y=round(y), name=an))
                log["contours"].append(f"{name}({sn}+{len(extra)}{' from ' + ln if ln == cap else ''}"
                                       f"{' moved ' + str(T) if T != (0, 0) else ''}{' loose' if len(chosen) > 4 else ''})")
            else:
                sn = scname(nfd[0])
                if sn not in f:
                    raise SystemExit(f"{style} {name}: base {sn} missing")
                g = add_glyph(name, sn)
                g.components.append(Component(sn))
                acc = dict(anchors(f[sn]))
                for m in nfd[1:]:
                    mn = cmap[ord(m)]
                    ma = anchors(f[mn])
                    att = next((k[1:] for k in ma if k.startswith("_") and k[1:] in acc), None)
                    if att is None:
                        raise SystemExit(f"{style} {name}: cannot attach {mn}")
                    dx = acc[att][0] - ma["_" + att][0]
                    dy = acc[att][1] - ma["_" + att][1]
                    g.components.append(Component(mn, transformation=(1, 0, 0, 1, dx, dy)))
                    if att in ma:
                        acc[att] = (ma[att][0] + dx, ma[att][1] + dy)
                for an, (x, y) in acc.items():
                    g.anchors.append(Anchor(x=round(x), y=round(y), name=an))
                log["components"].append(name)
        smcp[lc] = name
        if cap and cap in f:
            c2sc[cap] = name

    # ---- features
    fea = f.features.text
    # lookup numbers differ between the upright and italic sources: find them by feature
    lsm = re.search(r"feature smcp \{\s*lookup (\w+);", fea).group(1)
    lc2 = re.search(r"feature c2sc \{\s*lookup (\w+);", fea).group(1)

    def block(n):
        return fea.split(f"lookup {n} {{")[1].split(f"}} {n};")[0]
    have_sm = set(re.findall(r"^\s*sub (\S+) by", block(lsm), re.M))
    have_c2 = set(re.findall(r"^\s*sub (\S+) by", block(lc2), re.M))
    add37 = "".join(f"  sub {k} by {v};\n" for k, v in smcp.items() if k not in have_sm)
    add36 = "".join(f"  sub {k} by {v};\n" for k, v in c2sc.items() if k not in have_c2)
    fea = fea.replace(f"}} {lsm};", add37 + f"}} {lsm};", 1).replace(f"}} {lc2};", add36 + f"}} {lc2};", 1)

    # soft-dotted: complete the three classes of both L03 rules with the sets fontbakery's
    # soft_dotted check shapes: soft-dotted letter, optional non-above mark, above mark
    ucm = sorted((g.unicodes[0], g.name) for g in f if g.unicodes)
    blk = lambda u, rs: any(lo <= u <= hi for lo, hi in rs)
    DIACR = [(0x0300, 0x036F), (0x1AB0, 0x1AFF), (0x1DC0, 0x1DFF), (0x20D0, 0x20FF)]
    CYR = [(0x0400, 0x052F), (0x1C80, 0x1C8F), (0x2DE0, 0x2DFF), (0xA640, 0xA69F)]
    soft = [n for u, n in ucm if chr(u) in SOFT_DOTTED_CHARS]
    above = [m for m in SOFT_DOTTED_TOP if m in f] + [
        n for u, n in ucm if ud.combining(chr(u)) == 230 and blk(u, DIACR + CYR)]
    nonabove = [n for u, n in ucm if ud.combining(chr(u)) < 230 and blk(u, DIACR)]
    head, body = fea.split("lookup L03 {", 1)
    body, tail = body.split("} L03;", 1)
    lines = body.split(chr(10))
    for i, line in enumerate(lines):
        if line.strip().startswith("sub [") and line.rstrip().endswith("];"):
            parts = re.split(r"(\[[^\]]*\])", line)
            cls = [j for j, x in enumerate(parts) if x.startswith("[")]
            want = [soft] + ([nonabove] if len(cls) == 3 else []) + [above]
            for j, extra in zip(cls, want):
                have = parts[j][1:-1].split()
                parts[j] = "[" + " ".join(have + [n for n in dict.fromkeys(extra) if n not in have]) + "]"
            lines[i] = "".join(parts)
    fea = head + "lookup L03 {" + chr(10).join(lines) + "} L03;" + tail

    # Turkic languages (each step idempotent)
    if "languagesystem latn TRK;" not in fea:
        fea = fea.replace("languagesystem latn ROM;\n", "languagesystem latn ROM;\n" +
                          "".join(f"languagesystem latn {l};\n" for l in TURKIC), 1)
    ccmp = fea.split("feature ccmp {")[1].split("} ccmp;")[0]
    if "language TRK;" not in ccmp:
        fea = fea.replace("} ccmp;", "  script latn;\n" + "".join(f"  language {l};\n" for l in TURKIC) + "} ccmp;", 1)
    if "lookup smcpTRK {" not in fea:
        fea = fea.replace(f"}} {lsm};", f"}} {lsm};\n\nlookup smcpTRK {{\n  lookupflag 0;\n  sub i.sc by i.loclTRK.sc;\n}} smcpTRK;", 1)
    head = f"feature smcp {{\n  lookup {lsm};\n"
    if head + "  script latn;" not in fea:
        assert head in fea, "smcp feature layout"
        fea = fea.replace(head, head + "  script latn;\n" +
                          "".join(f"  language {l};\n    lookup smcpTRK;\n" for l in TURKIC), 1)
    f.features.text = fea

    if not dry:
        f.save(path, overwrite=True)
    print(f"{style}: designed {len(log['design'])}, from contours {len(log['contours'])}, "
          f"components {len(log['components'])} {log['components']}, aliases {log['alias']}, "
          f"smcp +{add37.count(chr(10))}, c2sc +{add36.count(chr(10))}")
    if True:
        print("  ", " ".join(log["design"]))
        print("  ", " ".join(log["contours"]))


for s in STYLES:
    process(s)
