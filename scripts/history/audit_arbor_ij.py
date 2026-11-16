#!/usr/bin/env python3
"""True-size and large optical comparison for Arbor j-centering revisions."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
INK='#132537';PAPER='#FBFAF7';RED='#A54B35';GRAY='#5F7083';GRID='#C9D5D7'


def ttf(style,version,size):
    suffix=f'ArborMono-{style}.ttf'
    location='ArborMono-v1.1-backup' if version=='Before' else 'ArborMono'
    return ImageFont.truetype(str(ROOT/location/suffix),size)


def proof():
    im=Image.new('RGB',(1580,1890),PAPER);d=ImageDraw.Draw(im)
    sans=lambda n:ImageFont.truetype(SANS,n)
    d.text((35,22),'Arbor Mono · i/j character positioning',font=sans(30),fill=INK)
    d.text((36,69),'v1.1 (left) versus shaft-centered draft (right)',font=sans(19),fill=GRAY)
    for si,style in enumerate(('Regular','Bold','Italic','BoldItalic')):
        top=120+si*435
        d.text((38,top),style,font=sans(23),fill=RED)
        for vi,version in enumerate(('Before','After')):
            x=35+vi*780
            d.text((x,top+39),version,font=sans(17),fill=GRAY)
            f=ttf(style,version,55)
            d.text((x,top+64),'h i j k l   hij jkl ijilj',font=f,fill=INK)
            ft=ttf(style,version,33)
            d.text((x,top+151),'abcdefghijklmnopqrstuvwxyz',font=ft,fill=INK)
            fsm=ttf(style,version,20)
            crop=Image.new('RGB',(175,44),'#FFFFFF')
            c=ImageDraw.Draw(crop)
            # Illustrate fixed cells without obscuring the hinting.
            cell=fsm.getlength('i')
            for k in range(9):
                xx=round(k*cell)
                c.line((xx,0,xx,43),fill=GRID,width=1)
            c.text((0,3),'ghijklmn',font=fsm,fill=INK)
            crop=crop.resize((700,176),Image.Resampling.NEAREST)
            im.paste(crop,(x,top+206))
            d.text((x,top+386),'Actual 20 px raster enlarged ×4',font=sans(15),fill=GRAY)
    target=ROOT/'ArborMono-IJComparison.png'
    im.save(target,optimize=True)
    return target


if __name__=='__main__':print(proof())
