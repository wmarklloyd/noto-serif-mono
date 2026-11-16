from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys
root=Path(__file__).parent
words=list(dict.fromkeys((root/'words.txt').read_text().split()))
sizes=(16,26)
before,after=map(Path,sys.argv[1:])
ui=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def render(label,face,size):
    f=ImageFont.truetype(str(face),size)
    lines=[]; current=''
    for word in words:
        trial=(current+'  '+word).strip()
        if f.getlength(trial)>570:
            lines.append(current);current=word
        else:
            current=trial
    if current:lines.append(current)
    return f,lines
for s in ('Italic','BoldItalic'):
    name=f'ArborMono-{s}.ttf'
    im=Image.new('RGB',(1230,2300),'#faf8f2')
    d=ImageDraw.Draw(im); y=20
    for size in sizes:
        h=0
        for j,directory in enumerate((before,after)):
            x=20+610*j
            f,lines=render(s,directory/name,size)
            d.text((x,y),f'{s} · {"v2.1" if directory.parent.name=="v21" else "v2.2" if directory.name=="step5" else directory.name} · {size} px/em',font=ui,fill='black')
            for i,line in enumerate(lines):
                d.text((x,y+34+i*(size+8)),line,font=f,fill='#211915')
            h=max(h,34+len(lines)*(size+8))
        y+=h+25
    im.crop((0,0,1230,y)).save(after/f'{s}-review.png')
print(len(words),'unique samples')
