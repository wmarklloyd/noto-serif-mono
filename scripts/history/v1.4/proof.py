from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
root=Path(__file__).parent
im=Image.new("RGB",(1300,900),"#faf8f2")
d=ImageDraw.Draw(im)
ui="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
title=ImageFont.truetype(ui,30)
label=ImageFont.truetype(ui,16)
d.text((28,20),"Arbor Mono  |  Italic spacing and shape",font=title,fill="#211915")
for k,style in enumerate(("Italic","BoldItalic")):
    path=f"ArborMono-{style}.ttf"
    fonts=[root/"before"/path,root/"final"/path]
    a,b=map(TTFont,fonts)
    cmap=a.getBestCmap()
    assert cmap==b.getBestCmap()
    assert all(b["hmtx"][n][0]==a["hmtx"][n][0] for n in a.getGlyphOrder())
    print(style,len(cmap))
    for c in "GHIJMWngmw0123456789":
        n=cmap[ord(c)]
        g,h=a["glyf"][n],b["glyf"][n]
        print(c,a["hmtx"][n],g.xMax,b["hmtx"][n],h.xMax,g.coordinates==h.coordinates)
    y0=80+405*k
    d.text((28,y0),style.replace("BoldItalic","Bold Italic"),font=label,fill="#211915")
    for col,p in enumerate(fonts):
        x=28+640*col
        d.text((x,y0+25),("1.3","1.4")[col],font=label,fill="#775342")
        for i,(size,sample) in enumerate([
            (36,"GHIJ  GH  HI  IJ  JIG  HIGH"),
            (20,"ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            (20,"abcdefghijklmnopqrstuvwxyz"),
            (15,"HIGHLIGHT  GH  HI  IJ  FIJI  minimum  0123456789"),
            (23,"Handwriting  minimum  WARM  Wing"),
            (22,"Ĥ Í Î Į Ĵ  Η Ι Ἰ Ί  Н І Ї Ј Ӏ  HÍJ"),
            (23,"ÀÁÂ Å  ÄÖÜ  ff fi fl  ст ШЩ  ΩΦΨ")]):
            f=ImageFont.truetype(str(p),size)
            d.text((x,y0+59+i*44),sample,font=f,fill="#211915")
im.save(root/"Italic-proof.png")
