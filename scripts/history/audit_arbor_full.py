#!/usr/bin/env python3
"""Comprehensive reproducible optical and structural inspection for Arbor 1.2."""
from collections import Counter
from pathlib import Path
import string
import unicodedata

from PIL import Image, ImageDraw, ImageFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

ROOT=Path(__file__).resolve().parent
STYLES=('Regular','Bold','Italic','BoldItalic')
FAMILIES=('ArborMono','ArborMonoOldstyle')
PAPER='#FBFAF7';INK='#152637';ACCENT='#AB513C';MUTED='#607185'
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def font(style,size,oldstyle=False):
    family='ArborMonoOldstyle' if oldstyle else 'ArborMono'
    return ImageFont.truetype(str(ROOT/family/f'{family}-{style}.ttf'),size)


def make_sheet():
    image=Image.new('RGB',(1780,1770),PAPER)
    draw=ImageDraw.Draw(image)
    sans=lambda n:ImageFont.truetype(SANS,n)
    draw.text((45,24),'Arbor Mono 1.2  |  Full character audit',font=sans(34),fill=INK)
    draw.text((46,74),'Noto-authored figures  ·  balanced serifs  ·  accents, Greek, Cyrillic, punctuation',
              font=sans(20),fill=MUTED)
    samples=[
        'illiterate little tilts  it li lt tl',
        'Saturday  Lantern  Magic  lavender',
        'minimum  mix  mW  WEAR  1Il|',
        'i í ï ı і   j ĵ ǰ ȷ ј   l ł ĺ',
        'café  façade  naïve  élève  piñata',
        'Crème brûlée; déjà vu?  Ångström',
        'Αθήνα  Ελληνικά  Ελληνική  123',
        'Москва  Привет  Рим  Киев  012',
        '0 O Ø 1 I l |  @#%&$ +*?!:;.,',
    ]
    for i,style in enumerate(STYLES):
        x=44+(i%2)*865
        y=145+(i//2)*790
        draw.text((x,y-10),style,font=sans(25),fill=ACCENT)
        for k,line in enumerate(samples):
            size=27 if k in (0,1,2) else 24
            draw.text((x,y+50+k*67),line,font=font(style,size),fill=INK)
        draw.text((x,y+675),'TRUE 12 px:  Saturday  lltt a mMW 0O1Il',
                  font=font(style,12),fill=MUTED)
        draw.text((x,y+704),'TRUE 16 px:  Saturday  lltt a mMW 0O1Il',
                  font=font(style,16),fill=MUTED)
    out=ROOT/'ArborMono-UnicodeAudit.png'
    image.save(out,optimize=True)
    return out


def scan():
    lines=['Arbor Mono 1.2 full-glyph structural QA','']
    for family in FAMILIES:
        for style in STYLES:
            path=ROOT/family/f'{family}-{style}.ttf'
            f=TTFont(path)
            cm=f.getBestCmap(); gs=f.getGlyphSet()
            src=TTFont(f'/usr/share/fonts/truetype/noto/NotoSerif-{style}.ttf')
            source_set=src.getGlyphSet()
            ink=0;outside=[];native_figure_overhang=[];wrong_advance=[];missing=[]
            for cp,name in cm.items():
                cat=unicodedata.category(chr(cp))
                if cat in ('Cc','Cf','Mn','Me'):continue
                if f['hmtx'].metrics[name][0]!=563:
                    wrong_advance.append(f'U+{cp:04X}')
                pen=BoundsPen(gs)
                gs[name].draw(pen)
                if pen.bounds is None:
                    if cat[0] in ('L','N'):missing.append(f'U+{cp:04X}')
                    continue
                ink+=1
                left,bottom,right,top=pen.bounds
                if left < -20 or right > 583:
                    native=BoundsPen(source_set)
                    source_set[name].draw(native)
                    srcadv=src['hmtx'][name][0]
                    offset=(563-srcadv)/2
                    native_figure=(48<=cp<=57 and native.bounds is not None
                       and abs((native.bounds[0]+offset)-left)<2
                       and abs((native.bounds[2]+offset)-right)<2)
                    record=(f'U+{cp:04X}',round(left),round(right))
                    (native_figure_overhang if native_figure else outside).append(record)
            for c in string.printable[:95]:
                # Every visible ASCII codepoint must have exactly the same advance.
                if ord(c) in cm:assert f['hmtx'].metrics[cm[ord(c)]][0]==563
            hints=sum(bool(getattr(f['glyf'][n],'program',None)) for n in f.getGlyphOrder())
            assert not outside,(path,outside[:12])
            assert not wrong_advance,(path,wrong_advance[:12])
            assert not missing,(path,missing[:12])
            assert hints>3200
            lines.append(f'{family} {style}: {len(cm)} Unicode mappings, '
                         f'{ink} drawable nonmark mappings, {hints} hinted glyphs; '
                         f'{len(outside)} unexpected overflows, '
                         f'{len(native_figure_overhang)} source figure overhangs, '
                         f'{len(wrong_advance)} non-monospaced mappings; '
                         f'{len(missing)} missing letter/number outlines')
    report=ROOT/'ArborMono-QA.txt'
    report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    print(make_sheet())
    print(scan())
