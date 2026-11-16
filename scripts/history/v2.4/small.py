import sys
from PIL import Image, ImageDraw, ImageFont
A,B,out=sys.argv[1:4]
txt="HNMKDU mw ÀÑÙ НИП minimum"
im=Image.new('L',(560,420),255); d=ImageDraw.Draw(im); y=4
for S in ['Regular','Bold','Italic','BoldItalic']:
    for sz in (12,16,20):
        d.text((4,y),txt,font=ImageFont.truetype(f'{A}/ArborMono-{S}.ttf',sz),fill=0)
        d.text((282,y),txt,font=ImageFont.truetype(f'{B}/ArborMono-{S}.ttf',sz),fill=0)
        y+=sz+6
    y+=4
im=im.crop((0,0,560,y)); im.resize((im.width*2,im.height*2),Image.NEAREST).save(out)
