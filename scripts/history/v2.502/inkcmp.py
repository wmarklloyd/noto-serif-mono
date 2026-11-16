"""Precomposed vs decomposed (anchor-positioned) mark placement, by ink.

For each encoded char whose NFD has >= 2 encoded chars: shape the precomposed char in
the real font and the NFD in a copy whose cmap lacks every precomposed char (so
HarfBuzz cannot recompose). Take the base letter's own ink extent (shaping the base
alone); ink above its top (+8) is the top-mark zone, ink below its bottom (-8) the
bottom-mark zone. Report each zone's centre x (unslanted about y=268 in the italics)
in both renderings and their difference.  Optional env FEAT=smcp.
TSV: style, char, cp, zone, pre_cx, dec_cx, diff, pre_w, dec_w
"""
import sys, os, math, unicodedata as ud
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen

FEAT = os.environ.get("FEAT", "")
SP = os.path.dirname(os.path.abspath(__file__))


class Sampler(BasePen):
    def __init__(self, gs, dx=0, dy=0):
        super().__init__(gs); self.pts = []; self.cur = None; self.d = (dx, dy)
    def add(self, p): self.pts.append((p[0] + self.d[0], p[1] + self.d[1]))
    def _moveTo(self, p): self.cur = p; self.add(p)
    def _lineTo(self, p): self.cur = p; self.add(p)
    def _curveToOne(self, a, b, c):
        p0 = self.cur
        for i in range(1, 13):
            t = i/12; u = 1-t
            self.add((u**3*p0[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*c[0], u**3*p0[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*c[1]))
        self.cur = c
    def _qCurveToOne(self, a, b):
        p0 = self.cur
        for i in range(1, 9):
            t = i/8; u = 1-t
            self.add((u*u*p0[0]+2*u*t*a[0]+t*t*b[0], u*u*p0[1]+2*u*t*a[1]+t*t*b[1]))
        self.cur = b


def shape(font, tt, txt):
    buf = hb.Buffer(); buf.add_str(txt); buf.guess_segment_properties()
    hb.shape(font, buf, {FEAT: True} if FEAT else {})
    gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
    pts = []; x = 0; names = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        n = order[info.codepoint]; names.append(n)
        s = Sampler(gs, x + pos.x_offset, pos.y_offset); gs[n].draw(s); pts += s.pts
        x += pos.x_advance
    return pts, names


out = open(sys.argv[1], "w", encoding="utf8")
out.write("style\tchar\tcp\tglyph\tzone\tpre_cx\tdec_cx\tdiff\tpre_w\tdec_w\n")
for style in ["Regular", "Bold", "Italic", "BoldItalic"]:
    path = f"fonts/ttf/ArborMono-{style}.ttf"
    tt = TTFont(path); cmap = tt.getBestCmap()
    t = math.tan(math.radians(-tt["post"].italicAngle))
    pre_cps = [cp for cp in cmap if len(ud.normalize("NFD", chr(cp))) >= 2
               and all(ord(c) in cmap for c in ud.normalize("NFD", chr(cp)))]
    dpath = os.path.join(SP, f"decomp-{style}.ttf")
    dt = TTFont(path)
    for sub in dt["cmap"].tables:
        for cp in pre_cps:
            sub.cmap.pop(cp, None)
    dt.save(dpath)
    dt = TTFont(dpath)
    F = hb.Font(hb.Face(hb.Blob.from_file_path(path)))
    D = hb.Font(hb.Face(hb.Blob.from_file_path(dpath)))
    for cp in sorted(pre_cps):
        nfd = ud.normalize("NFD", chr(cp))
        bpts, _ = shape(D, dt, nfd[0])
        if not bpts:
            continue
        top = max(y for x, y in bpts) + 8; bot = min(y for x, y in bpts) - 8
        ppts, pn = shape(F, tt, chr(cp))
        dpts, dn = shape(D, dt, nfd)
        if len(dn) < 2:
            continue
        for zone, sel in (("top", lambda y: y > top), ("bottom", lambda y: y < bot)):
            a = [x - (y - 268) * t for x, y in ppts if sel(y)]
            b = [x - (y - 268) * t for x, y in dpts if sel(y)]
            if not a and not b:
                continue
            if not a or not b:
                out.write(f"{style}\t{chr(cp)}\t{cp:04X}\t{pn[0]}\t{zone}\t{'' if not a else round((min(a)+max(a))/2)}\t{'' if not b else round((min(b)+max(b))/2)}\tmissing\t\t\n")
                continue
            ca = (min(a) + max(a)) / 2; cb = (min(b) + max(b)) / 2
            out.write(f"{style}\t{chr(cp)}\t{cp:04X}\t{pn[0]}\t{zone}\t{ca:.0f}\t{cb:.0f}\t{cb-ca:.0f}\t{max(a)-min(a):.0f}\t{max(b)-min(b):.0f}\n")
out.close()
