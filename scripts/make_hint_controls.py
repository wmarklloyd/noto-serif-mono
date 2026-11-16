#!/usr/bin/env python3
"""Generate the ttfautohint control files in sources/hinting/.

    python scripts/make_hint_controls.py fonts/ttf/NotoSerifMono-*.ttf

Run on the unhinted (or hinted: ttfautohint ignores existing hints) TTFs from
`gftools builder`, then run scripts/hint.py, which applies the control files.
Re-run whenever outlines change: the control files address glyph points by index.

The control file for each style contains:

1. `n` (no-direction) segments for every point of the glyphs in NODIR. ttfautohint
   snapped the descender of U+210A SCRIPT SMALL G onto the baseline zone, lifting the
   whole glyph by 0.37 em at every size, and moved U+25CC DOTTED CIRCLE by 2 px at
   10 ppem. With no segments these glyphs are scaled without being distorted.

2. Delta hints (`touch ... yshift`, applied after IUP so FreeType v40 honours them in full;
   `point` deltas moved the accent only 0.2-0.4 px there) that keep accents clear of their letters. For every
   precomposed letter drawn as one glyph, with accents above (or below) the letter's
   body, the script compares the hinted outline with the unhinted one at 8-36 ppem in
   FreeType's v40 and v35 interpreters. Where the outline has a gap of at least
   GAP_MIN px between body and accent and hinting closes it to less than half a pixel,
   the accent's points are moved 1 px away from the body at that size, unless that would
   take the accent past usWinAscent/usWinDescent, where Windows GDI clips it. The typical
   cases are Cyrillic and Greek letters (ttfautohint's Cyrillic and Greek styles have
   no ascender zone, so a dot or diaeresis top at 744 units is not held up the way the
   Latin style holds it) and accented letters at 11 ppem.

Each style is measured with Regular's x-height CVT values copied in, as hint.py does.
The script then hints with the new control file and checks every delta's result,
reporting any letter that is still closed.
"""
import sys, os, re, math, ctypes, collections, unicodedata as ud, tempfile
import freetype
import freetype.raw as raw
from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hint

NODIR = ['scriptg', 'uni25CC']
PPEMS = range(8, 37)
INTERPRETERS = (40, 35)
GAP_MIN = 0.75     # px of white the outline itself has between body and accent
CLOSED = 0.5       # hinted gap below this (px) counts as touching
SOFT_DOTTED = set('ijіјɨʝɉϳ')
REGULAR = re.compile(r'-(Bold|Italic|BoldItalic)\.ttf$')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def control_path(font_path):
    base = os.path.splitext(os.path.basename(font_path))[0]
    return os.path.join(ROOT, 'sources', 'hinting', base + '.ttfa.txt')


def candidates(font):
    """(glyph, side, accent contour indices) for one-glyph letters with marks above/below."""
    cmap = font.getBestCmap(); glyf = font['glyf']
    out = []
    for cp, name in sorted(cmap.items()):
        nfd = ud.normalize('NFD', chr(cp))
        if len(nfd) < 2 or not ud.category(nfd[0]).startswith('L') or ord(nfd[0]) not in cmap:
            continue
        g = glyf[name]
        if g.isComposite() or g.numberOfContours < 2:
            continue
        base = glyf[cmap[ord(nfd[0])]]
        ccc = {ud.combining(c) for c in nfd[1:]}
        coords = g.getCoordinates(glyf)[0]
        ends = list(g.endPtsOfContours)
        starts = [0] + [e + 1 for e in ends[:-1]]
        ys = [[coords[i][1] for i in range(s, e + 1)] for s, e in zip(starts, ends)]
        if ccc & {230, 232, 234}:
            top = 560 if nfd[0] in SOFT_DOTTED else base.yMax
            acc = [k for k, y in enumerate(ys) if min(y) > top + 5]
            if acc and len(acc) < len(ys):
                out.append((name, 'top', acc, starts, ends))
        if ccc & {220, 202, 233}:
            acc = [k for k, y in enumerate(ys) if max(y) < base.yMin - 5]
            if acc and len(acc) < len(ys):
                out.append((name, 'bottom', acc, starts, ends))
    return out


def set_interpreter(iv):
    v = ctypes.c_uint(iv)
    raw.FT_Property_Set(freetype.get_handle(), b'truetype', b'interpreter-version', ctypes.byref(v))


def gap(face, name, side, acc, starts, ends, ppem, hinted):
    face.set_char_size(0, ppem * 64, 72, 72)
    fl = freetype.FT_LOAD_NO_BITMAP | freetype.FT_LOAD_NO_AUTOHINT
    if not hinted:
        fl |= freetype.FT_LOAD_NO_HINTING
    face.load_glyph(face.get_name_index(name.encode()), fl)
    pts = face.glyph.outline.points
    accset = set(acc)
    a, b = [], []
    for k, (s, e) in enumerate(zip(starts, ends)):
        (a if k in accset else b).extend(pts[i][1] / 64 for i in range(s, e + 1))
    g = (min(a) - max(b)) if side == 'top' else (min(b) - max(a))
    return g, (max(a) if side == 'top' else -min(a))   # gap, accent extent (px) beyond the origin


def measure(path, cands, room=False):
    """{(glyph, side): {ppem: (unhinted gap, hinted gap)}} for gaps hinting closes.
    room=True keeps only sizes where moving the accent 1 px out stays inside
    usWinAscent/usWinDescent, which Windows GDI clips at."""
    os2 = TTFont(path)['OS/2']; upm = TTFont(path)['head'].unitsPerEm
    res = collections.defaultdict(dict)
    for iv in INTERPRETERS:
        set_interpreter(iv)
        face = freetype.Face(path)
        for name, side, acc, starts, ends in cands:
            for p in PPEMS:
                u, _ = gap(face, name, side, acc, starts, ends, p, False)
                h, ext = gap(face, name, side, acc, starts, ends, p, True)
                limit = math.ceil((os2.usWinAscent if side == 'top' else os2.usWinDescent) * p / upm)
                if u >= GAP_MIN and h < CLOSED and not (room and math.ceil(ext - 1e-6) + 1 > limit):
                    res[(name, side)][p] = (round(u, 2), round(h, 2))
    return res


def ranges(idx):
    idx = sorted(idx); out = []; s = p = idx[0]
    for i in idx[1:]:
        if i != p + 1:
            out.append(f'{s}-{p}' if p > s else str(s)); s = i
        p = i
    out.append(f'{s}-{p}' if p > s else str(s))
    return ', '.join(out)


def make(path):
    font = TTFont(path)
    glyf = font['glyf']
    lines = ['# Generated by scripts/make_hint_controls.py; do not edit by hand.',
             '# Glyphs scaled without segments (see the script for why):']
    for n in NODIR:
        if n in glyf.glyphs and glyf[n].numberOfContours > 0:
            lines.append(f'{n} n 0-{len(glyf[n].coordinates) - 1}')
    base_ctrl = '\n'.join(lines) + '\n'
    cands = candidates(font)
    tmp = tempfile.NamedTemporaryFile(suffix='.ttf', delete=False).name
    regular = os.path.join(os.path.dirname(path), REGULAR.sub('-Regular.ttf', os.path.basename(path)))
    ref = None
    if os.path.abspath(regular) != os.path.abspath(path) and os.path.exists(regular):
        # hint.py copies Regular's x-height CVT values into the other styles; measure with them
        hint.autohint(regular, out=tmp, control='')
        ref = TTFont(tmp, lazy=False); ref['cvt '].values

    def hinted(ctrl):
        hint.autohint(path, out=tmp, control=ctrl)
        if ref is not None:
            t = TTFont(tmp, lazy=False); hint.align_xheight_cvt(t, ref, path); t.save(tmp)

    hinted(base_ctrl)
    closed = measure(tmp, cands, room=True)
    lines.append('# Accents kept 1 px clear of the letter where hinting closed the gap:')
    by = {(c[0], c[1]): c for c in cands}
    for (name, side), sizes in sorted(closed.items()):
        _, _, acc, starts, ends = by[(name, side)]
        pts = [i for k in acc for i in range(starts[k], ends[k] + 1)]
        lines.append(f'{name} touch {ranges(pts)} yshift {1 if side == "top" else -1} @ '
                     + ', '.join(str(p) for p in sorted(sizes)))
    ctrl = '\n'.join(lines) + '\n'
    hinted(ctrl)
    still = measure(tmp, [c for c in cands if (c[0], c[1]) in closed])
    os.unlink(tmp)
    os.makedirs(os.path.dirname(control_path(path)), exist_ok=True)
    with open(control_path(path), 'w', encoding='utf-8', newline='\n') as f:
        f.write(ctrl)
    n = sum(len(v) for v in closed.values())
    print(f'{os.path.basename(path)}: {len(cands)} accented letters, {len(closed)} with a gap closed by '
          f'hinting at {n} sizes; after deltas still closed: {dict(still) or "none"}')


if __name__ == '__main__':
    for p in sys.argv[1:]:
        make(p)
