#!/usr/bin/env python3
"""Render inspectable large and small specimens for Arbor Mono."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
CREAM='#FAF8F5'; NAVY='#162536'; RED='#A75340'; SLATE='#506176'; RULE='#DEDDD8'


def sans(px):return ImageFont.truetype(SANS,px)


def face(folder,style,px):
    return ImageFont.truetype(str(ROOT/folder/f'{folder}-{style}.ttf'),px)


def render_one(folder, oldstyle):
    label='Arbor Mono Oldstyle' if oldstyle else 'Arbor Mono'
    f=lambda style,px:face(folder,style,px)
    im=Image.new('RGB',(1640,1350),CREAM);d=ImageDraw.Draw(im)
    d.rectangle((0,0,1640,14),fill=RED)
    d.text((88,48),'NOTO SERIF DERIVATIVE · MONOSPACED · SLASHED ZERO',font=sans(23),fill=RED)
    d.text((78,101),label,font=f('Bold',95),fill=NAVY)
    d.text((90,245),'Compact fixed-width transitional serif, balanced at small sizes.',font=sans(25),fill=SLATE)
    d.line((90,312,1550,312),fill=RULE,width=2)
    d.text((92,339),'REGULAR · WORD SPACING',font=sans(20),fill=RED)
    d.text((85,386),'Saturday Lantern Magic lavender',font=f('Regular',65),fill=NAVY)
    d.text((92,501),'BOLD',font=sans(20),fill=RED)
    d.text((86,544),'Saturday Lantern Magic lavender',font=f('Bold',55),fill=NAVY)
    d.text((92,653),'ITALIC',font=sans(20),fill=RED)
    d.text((86,693),'Saturday Lantern Magic lavender',font=f('Italic',54),fill=NAVY)
    d.text((92,796),'BOLD ITALIC',font=sans(20),fill=RED)
    d.text((86,841),'Saturday Lantern Magic lavender',font=f('BoldItalic',53),fill=NAVY)
    d.line((90,952,1550,952),fill=RULE,width=2)
    d.text((92,976),'FIXED-WIDTH LINING / OLDSTYLE FIGURES',font=sans(20),fill=RED)
    d.text((86,1016),'H W M 0123456789 O 0',font=f('Regular',65),fill=NAVY)
    d.rectangle((80,1124,1560,1270),fill='#F0EFEB')
    d.text((105,1137),'HINTED AT REAL PIXEL SIZES',font=sans(18),fill=RED)
    for i,px in enumerate((12,14,16,18,20,24)):
        x=108+(i//3)*720;y=1179+(i%3)*27
        d.text((x,y),f'{px}px',font=sans(15),fill=SLATE)
        d.text((x+57,y-3),'Sa La Ma la  0 O  il1 W M',font=f('Regular',px),fill=NAVY)
    d.text((95,1305),'4 hinted styles  ·  563/1000-em cell  ·  separate numeral families',font=sans(18),fill=SLATE)
    path=ROOT/f'{folder}-Specimen.png'
    im.save(path,optimize=True)
    print(path)


def render_comparison():
    im=Image.new('RGB',(1720,1340),CREAM);d=ImageDraw.Draw(im)
    d.text((45,28),'How compact serif monospace designs handle adjacent a',font=sans(29),fill=NAVY)
    samples=[
        ('Noto Serif — proportional source','/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf'),
        ('Laurel Mono — Gelasio derivative',str(ROOT/'LaurelMono/LaurelMono-Regular.ttf')),
        ('Arbor Mono — Noto Serif derivative',str(ROOT/'ArborMono/ArborMono-Regular.ttf')),
    ]
    for row,(title,path) in enumerate(samples):
        y=104+row*396
        d.text((49,y),title,font=sans(25),fill=RED)
        for col,px in enumerate((16,24,44)):
            x=49+col*562
            d.text((x,y+53),f'{px} ppem',font=sans(18),fill=SLATE)
            ft=ImageFont.truetype(path,px)
            for j,line in enumerate(('Saturday','Lantern','Magic','lavender')):
                d.text((x,y+102+j*61),line,font=ft,fill=NAVY)
        d.line((40,y+355,1670,y+355),fill=RULE,width=2)
    output=ROOT/'ArborMono-Comparison.png'
    im.save(output,optimize=True)
    print(output)


def render_all():
    render_one('ArborMono',False)
    render_one('ArborMonoOldstyle',True)
    render_comparison()


if __name__=='__main__':render_all()
