#!/usr/bin/env python3
"""Contact sheet: every glyph of a font in glyph order, in its 573-unit cell, with the
code point (or glyph name for unencoded glyphs) under it. Rendered unhinted by FreeType.

    python scripts/qa/contact_sheet.py fonts/ttf/NotoSerifMono-Regular.ttf out/contact/Regular.png

Each cell shows the advance as a light box and the baseline as a light line, so spacing
and side bearings can be compared across the whole font. Zero-width marks are drawn
centred on their origin.
"""
import sys, os
import freetype
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

PPEM = 40          # px per em for the glyphs
COLS = 48
LABEL = 11


def main(path, out):
    t = TTFont(path)
    order = t.getGlyphOrder()
    rev = {}
    for cp, n in t.getBestCmap().items():
        rev.setdefault(n, cp)
    upm = t['head'].unitsPerEm
    asc, desc = t['hhea'].ascent, t['hhea'].descent
    adv = max(w for w, _ in t['hmtx'].metrics.values())
    cw = round(adv * PPEM / upm) + 16
    gh = round((asc - desc) * PPEM / upm)
    ch = gh + LABEL + 8
    base = round(asc * PPEM / upm)
    rows = -(-len(order) // COLS)
    head = 34
    img = Image.new('L', (COLS * cw, head + rows * ch), 255)
    dr = ImageDraw.Draw(img)
    try:
        lab = ImageFont.truetype(path, LABEL)
        title = ImageFont.truetype(path, 20)
    except OSError:
        lab = title = ImageFont.load_default()
    name = t['name'].getDebugName(4)
    dr.text((8, 6), f'{name}: {len(order)} glyphs, advance {adv}/{upm}', font=title, fill=0)
    face = freetype.Face(path)
    face.set_char_size(0, PPEM * 64, 72, 72)
    for i, n in enumerate(order):
        r, c = divmod(i, COLS)
        x0, y0 = c * cw, head + r * ch
        w = t['hmtx'][n][0]
        aw = round(w * PPEM / upm)
        ox = x0 + (cw - aw) // 2 if w else x0 + cw // 2
        dr.rectangle([x0, y0, x0 + cw - 1, y0 + ch - 1], outline=235)
        if w:
            dr.rectangle([ox, y0 + 2, ox + aw, y0 + gh], outline=215)
        dr.line([x0 + 2, y0 + base, x0 + cw - 3, y0 + base], fill=215)
        face.load_glyph(i, freetype.FT_LOAD_NO_HINTING | freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_BITMAP)
        g = face.glyph; bm = g.bitmap
        if bm.width and bm.rows:
            m = Image.frombytes('L', (bm.width, bm.rows), bytes(bm.buffer)) if bm.pitch == bm.width else \
                Image.frombytes('L', (bm.width, bm.rows), bytes(b for row in range(bm.rows)
                                                                 for b in bm.buffer[row * bm.pitch: row * bm.pitch + bm.width]))
            img.paste(0, (ox + g.bitmap_left, y0 + base - g.bitmap_top), m)
        txt = f'{rev[n]:04X}' if n in rev else n
        while dr.textlength(txt, font=lab) > cw - 4 and len(txt) > 3:
            txt = txt[:-2] + '…'
        dr.text((x0 + (cw - dr.textlength(txt, font=lab)) / 2, y0 + gh + 4), txt, font=lab, fill=90)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out)
    print(out, img.size)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
