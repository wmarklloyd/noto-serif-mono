from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys
old,new=map(Path,sys.argv[1:3])
im=Image.new("RGB",(1240,900),"#faf8f2")
d=ImageDraw.Draw(im); sans="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
label=ImageFont.truetype(sans,19)
d.text((25,18),"Arbor Mono | Italic stroke weight",font=ImageFont.truetype(sans,29),fill="black")
for row,s in enumerate(("Italic","BoldItalic")):
  for i,p in enumerate((old,new)):
    x=26+615*i;y=76+405*row
    d.text((x,y),f"{s} · v2.{i+2}",font=label,fill="#72553b")
    for size,sample,offset in [
        (58,"HMNMUWMm",25),(38,"MOMENT MINIMUM WARM",96),
        (28,"HUMMING NUMBING MUNICH",149),
        (25,"H M N U W    m n u w    Ḿ Ñ Ü Ŵ",192),
        (19,"ABCDEFGHIJKLMNOPQRSTUVWXYZ",229),
        (19,"abcdefghijklmnopqrstuvwxyz  0123456789",263),
        (16,"Handwriting  minimum  momentum  WARM  AWAY",299),
        (13,"Handwriting  minimum  momentum  WARM  AWAY",328)]:
        d.text((x,y+offset),sample,
               font=ImageFont.truetype(str(p/f"ArborMono-{s}.ttf"),size),fill="#211810")
im.save(sys.argv[3])
