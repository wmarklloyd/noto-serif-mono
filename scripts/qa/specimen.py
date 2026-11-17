#!/usr/bin/env python3
"""Render documentation/specimen.png (the README image) from the built fonts.

    python scripts/qa/specimen.py [fonts/ttf] [documentation/specimen.png]

The family name is read from the Regular font's name table, so the image follows the font.
"""
import sys, os
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

FONTS = sys.argv[1] if len(sys.argv) > 1 else 'fonts/ttf'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'documentation/specimen.png'

W, H = 1600, 780
BG, INK, GREY, GREEN = (249, 248, 244), (28, 30, 33), (128, 128, 128), (45, 95, 75)
X = 84


def font(style, size):
    return ImageFont.truetype(os.path.join(FONTS, f'NotoSerifMono-{style}.ttf'), size)


family = TTFont(os.path.join(FONTS, 'NotoSerifMono-Regular.ttf'))['name'].getDebugName(1)
img = Image.new('RGB', (W, H), BG)
dr = ImageDraw.Draw(img)


def runs(y, parts, size):
    """Draw [(text, style, colour), ...] left to right from X on baseline-ish y."""
    x = X
    for text, style, colour in parts:
        f = font(style, size)
        dr.text((x, y), text, font=f, fill=colour)
        x += dr.textlength(text, font=f)


dr.text((X, 72), family, font=font('Bold', 96), fill=INK)
dr.text((X, 180), 'A monospaced serif adapted from Noto Serif', font=font('Italic', 34), fill=GREY)

code = 34
runs(275, [('def', 'Bold', GREEN), (' fib(n: int) -> int:', 'Regular', INK)], code)
runs(325, [('    ', 'Regular', INK), ('return', 'Bold', GREEN), (' n ', 'Regular', INK), ('if', 'Bold', GREEN),
           (' n < 2 ', 'Regular', INK), ('else', 'Bold', GREEN), (' fib(n-1) + fib(n-2)', 'Regular', INK)], code)
runs(375, [('    # 0O 1lI| {}[]() <= != => ~-_', 'Italic', GREY)], code)

big = 40
dr.text((X, 465), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', font=font('Regular', big), fill=INK)
dr.text((X, 522), 'abcdefghijklmnopqrstuvwxyz 0123456789', font=font('Regular', big), fill=INK)
dr.text((X, 579), 'ÀÉÎÕÜ ąčęłńšž ΑΒΓΔΩ αβγδω АБВГД абвгд', font=font('Italic', big), fill=INK)

for i, (label, style) in enumerate([('Regular', 'Regular'), ('Italic', 'Italic'),
                                    ('Bold', 'Bold'), ('Bold Italic', 'BoldItalic')]):
    dr.text((X + i * 370, 657), label, font=font(style, big), fill=INK)

img.save(OUT)
print(OUT, img.size, family)
