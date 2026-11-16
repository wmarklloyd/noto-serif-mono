import sys
from PIL import Image, ImageDraw, ImageFont
A,B,out=sys.argv[1],sys.argv[2],sys.argv[3]
size=int(sys.argv[4]) if len(sys.argv)>4 else 40
lines=sys.argv[5].split('|') if len(sys.argv)>5 else ["HNMKDU mw Iln","ÀÑÙĤĎ ñūķ НМИЙ","MINIMUM WAVE"]
lab=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',max(11,size//4))
cw=size*0.563; W=int(cw*max(map(len,lines))*2+90)
rows=4*len(lines); H=int(rows*size*1.35+4*size*0.5+20)
im=Image.new('L',(W,H),255); d=ImageDraw.Draw(im); y=6
for S in ['Regular','Bold','Italic','BoldItalic']:
    d.text((10,y),S+'   before  |  after',font=lab,fill=110); y+=size*0.45
    fa=ImageFont.truetype(f'{A}/ArborMono-{S}.ttf',size); fb=ImageFont.truetype(f'{B}/ArborMono-{S}.ttf',size)
    for l in lines:
        d.text((10,y),l,font=fa,fill=0); d.text((W//2+20,y),l,font=fb,fill=0); y+=size*1.35
d.line([(W//2+5,0),(W//2+5,H)],fill=170)
im.save(out)
