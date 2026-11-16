#!/usr/bin/env python3
"""Optical QA of the Noto-derived full ASCII set and its narrow glyphs."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent
SOURCE='/usr/share/fonts/truetype/noto/NotoSerif-{}.ttf'
BUILT=str(ROOT/'ArborMono/ArborMono-{}.ttf')
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
PAPER='#FBFAF7';INK='#152637';ACCENT='#AD5B40';GRID='#CAD3D9'


def text_font(size):return ImageFont.truetype(SANS,size)


def target_grid():
    im=Image.new('RGB',(1600,1450),PAPER);d=ImageDraw.Draw(im)
    d.text((32,15),'Arbor Mono · Regular versus Bold · every printable ASCII glyph',
           font=text_font(26),fill=INK)
    rows=[
        'ABCDEFGHIJKLMNOP',
        'QRSTUVWXYZ',
        'abcdefghijklmnop',
        'qrstuvwxyz',
        '0123456789',
        '!@#$%^&*()-_=+[]',
        '{};:\'",.<>/?\\|`~',
    ]
    for col,style in enumerate(('Regular','Bold')):
        ft=ImageFont.truetype(BUILT.format(style),72)
        advance=ft.getlength('A')
        x=35+col*790
        d.text((x,71),style,font=text_font(22),fill=ACCENT)
        for i,word in enumerate(rows):
            y=129+i*176
            d.text((x,y-30),f'Group {i+1} — {len(word)} glyphs',font=text_font(16),fill=ACCENT)
            for j in range(len(word)):
                left=x+round(j*advance);right=x+round((j+1)*advance)
                d.rectangle((left,y,right,y+110),outline=GRID,width=1)
            d.text((x,y),word,font=ft,fill=INK)
    file=ROOT/'ArborMono-ASCIIAudit.png'
    im.save(file,optimize=True)
    print(file)


def narrow_glyphs():
    im=Image.new('RGB',(1570,1190),PAPER);d=ImageDraw.Draw(im)
    d.text((34,21),'Source Noto Serif vs initial Arbor Mono: narrow/wide optical shapes',
           font=text_font(24),fill=INK)
    selections='iltfrnhmMWw1'
    # Each character is shown at one em size, not artificially resized.
    for panel,style in enumerate(('Regular','Bold')):
        top=86+panel*543
        d.text((36,top-21),style,font=text_font(21),fill=ACCENT)
        fsrc=ImageFont.truetype(SOURCE.format(style),130)
        fdst=ImageFont.truetype(BUILT.format(style),130)
        for i,char in enumerate(selections):
            row=i//6; col=i%6
            x=35+col*253;y=top+31+row*249
            d.text((x,y),f'"{char}"',font=text_font(16),fill=ACCENT)
            d.text((x+15,y+20),char,font=fsrc,fill=INK)
            d.text((x+125,y+20),char,font=fdst,fill=INK)
            d.text((x+16,y+165),'Noto',font=text_font(13),fill=ACCENT)
            d.text((x+129,y+165),'Arbor',font=text_font(13),fill=ACCENT)
    file=ROOT/'ArborMono-NarrowGlyphAudit.png'
    im.save(file,optimize=True)
    print(file)


if __name__=='__main__':
    target_grid()
    narrow_glyphs()
