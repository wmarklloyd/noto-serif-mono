from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

root=Path(__file__).parent
im=Image.new("RGB",(1380,880),"#faf8f2")
d=ImageDraw.Draw(im)
sans="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
d.text((28,20),"Arbor Mono  |  AWAY and JAZZ in Arbor Mono",fill="#221a16",
       font=ImageFont.truetype(sans,30))
label=ImageFont.truetype(sans,17)
for i,style in enumerate(("Italic","BoldItalic")):
    name=f"ArborMono-{style}.ttf"
    fonts=[root.parent/"v18"/"natural"/name,root/"natural"/name]
    a,b=map(TTFont,fonts)
    assert a.getBestCmap()==b.getBestCmap()
    assert all(a["hmtx"][n][0] == b["hmtx"][n][0] for n in a.getGlyphOrder())
    for n in (a.getBestCmap()[cp] for cp in range(48,58)):
        assert a["glyf"][n].coordinates == b["glyf"][n].coordinates
    y=76+i*390
    for j,p in enumerate(fonts):
        x=28+678*j
        d.text((x,y),f'{style.replace("BoldItalic","Bold Italic")}  ·  1.{8+j}',
               fill="#644936",font=label)
        for k,(size,sample,offset) in enumerate([
            (68,"AWAY  JAZZ  JIG",29),
            (43,"AW WA AY JA AZ ZZ",111),
            (25,"JAZZ  JILT  JOE  FIJI  AWAY  JAW",174),
            (18,"Jump  eJect  eJ  jJ  Jj  (J)  J-1  AJW",217),
            (14,"AW  WA   AV  VA   EW  WE   OW  WO   WW",247),
            (12,"HIGH  GHIJ  JIG  0123456789",272),
            (21,"Á G Ĥ Í Î Ĵ  Η Ι  Н І Ї Ј  1I  0G",305)]):
            d.text((x,y+offset+7),str(size),fill="#644936",font=label)
            d.text((x+38,y+offset),sample,fill="#221a16",
                   font=ImageFont.truetype(str(p),size))
im.save(root/"ArborMono-AWAY-JAZZ.png")
