import sys; sys.path.insert(0,'/home/claude/ft')
from ftr import render
from fontTools.ttLib import TTFont
import numpy as np
from PIL import Image
def text_image(path,ppem,lines,mode=1,iv=40):
    t=TTFont(path); cm=t.getBestCmap()
    names=sorted({cm[ord(c)] for l in lines for c in l if ord(c) in cm})
    R=render(path,ppem,names,mode,iv)
    adv=0.563*ppem; lh=int(round(1.362*ppem)); asc=int(round(1.069*ppem))
    W=int(adv*max(map(len,lines)))+4; H=lh*len(lines)+2
    img=np.zeros((H,W),float)
    for li,l in enumerate(lines):
        for ci,c in enumerate(l):
            if ord(c) not in cm or c==' ': continue
            left,top,a=R[cm[ord(c)]]
            x0=int(round(ci*adv))+left+2; y0=li*lh+asc-top
            for r in range(a.shape[0]):
                for cc in range(a.shape[1]):
                    y=y0+r; x=x0+cc
                    if 0<=y<H and 0<=x<W: img[y,x]=min(255,img[y,x]+a[r,cc])
    return Image.fromarray((255-img).astype('uint8'))
def sheet(paths_labels,sizes,lines,out,scale=3):
    from PIL import ImageDraw, ImageFont
    lab=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',13)
    blocks=[]
    for p in sizes:
        row=[text_image(path,p,lines) for path,_ in paths_labels]
        blocks.append((p,row))
    colw=max(im.width for _,row in blocks for im in row)*scale+20
    H=sum(max(im.height for im in row)*scale+24 for _,row in blocks)+30
    sheet=Image.new('L',(colw*len(paths_labels),H),255); d=ImageDraw.Draw(sheet)
    for i,(_,l) in enumerate(paths_labels): d.text((i*colw+6,6),l,font=lab,fill=90)
    y=28
    for p,row in blocks:
        for i,im in enumerate(row):
            d.text((i*colw+6,y),f'{p} px',font=lab,fill=130)
            sheet.paste(im.resize((im.width*scale,im.height*scale),Image.NEAREST),(i*colw+6,y+16))
        y+=max(im.height for im in row)*scale+24
    sheet.save(out)
