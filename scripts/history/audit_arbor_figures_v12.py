#!/usr/bin/env python3
"""Noto vs Arbor 1.1/1.2: source geometry and real hinted raster proof."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

ROOT=Path(__file__).resolve().parent
SRC=Path('/usr/share/fonts/truetype/noto')
SANS='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
PAPER='#FBFAF7';INK='#142434';GRAY='#657587';ACCENT='#A95339'
STYLES=('Regular','Bold','Italic','BoldItalic')


def source_metrics(style):
    font=TTFont(SRC/f'NotoSerif-{style}.ttf')
    cmap=font.getBestCmap()
    hmtx=font['hmtx'].metrics
    return tuple(hmtx[cmap[ord(ch)]][0] for ch in '0123456789')


def make_proof():
    im=Image.new('RGB',(1720,1770),PAPER)
    d=ImageDraw.Draw(im)
    sans=lambda n:ImageFont.truetype(SANS,n)
    d.text((35,20),'Arbor Mono 1.2: Noto figure preservation and hinting',
           font=sans(29),fill=INK)
    d.text((38,64),'The source figures already share a 559-unit advance; Arbor uses 563 units.',
           font=sans(17),fill=GRAY)
    d.text((38,88),'1.2 keeps Noto’s individual outlines and sidebearings and uses its zero.slash alternate.',
           font=sans(17),fill=GRAY)
    for idx,style in enumerate(STYLES):
        top=139+idx*403
        d.text((36,top),style,font=sans(23),fill=ACCENT)
        d.text((38,top+35),'Noto native · 0 is unslashed',font=sans(16),fill=GRAY)
        d.text((589,top+35),'Arbor 1.1 · edited & rehinted',font=sans(16),fill=GRAY)
        d.text((1140,top+35),'Arbor 1.2 · source shapes',font=sans(16),fill=GRAY)
        sources=(SRC/f'NotoSerif-{style}.ttf',
                 ROOT/'ArborMono-v1.1-backup'/f'ArborMono-{style}.ttf',
                 ROOT/'ArborMono'/f'ArborMono-{style}.ttf')
        for col,path in enumerate(sources):
            x=38+col*550
            for row,px in enumerate((16,24,50)):
                y=top+75+row*100
                f=ImageFont.truetype(str(path),px)
                if px==50:
                    d.text((x,y),'0123456789',font=f,fill=INK)
                    continue
                patch=Image.new('RGB',(179,29),'white')
                ImageDraw.Draw(patch).text((2,1),'0123456789',font=f,fill=INK)
                patch=patch.resize((537,87),Image.Resampling.NEAREST)
                im.paste(patch,(x,y))
                d.text((x+410,y-15),f'{px} px ×3',font=sans(12),fill=GRAY)
        d.line((38,top+385,1674,top+385),fill='#D7D4D0',width=2)
    p=ROOT/'ArborMono-FigureRevision.png'
    im.save(p,optimize=True)
    print(p)


def audit_geometry():
    out=['# Figure geometry provenance','',
         'Unchanged digit widths and source optical sidebearings are the goal.',
         'This compares actual outlines, not merely advance metadata.','',
         '| Style | Source figure advances | Exact outline point matches (0–9) | Source sidebearing preservation |',
         '|---|---|---:|---:|']
    for style in STYLES:
        source=TTFont(SRC/f'NotoSerif-{style}.ttf')
        dest=TTFont(ROOT/'ArborMono'/f'ArborMono-{style}.ttf')
        source_gs=source.getGlyphSet();dest_gs=dest.getGlyphSet()
        widths=[];shift_errors=[];all_points=[]
        src_cmap=source.getBestCmap();dst_cmap=dest.getBestCmap()
        for c in '0123456789':
            original='zero.slash' if c=='0' else src_cmap[ord(c)]
            updated=dst_cmap[ord(c)]
            xy,ends,_=source['glyf'][original].getCoordinates(source['glyf'])
            xy2,ends2,_=dest['glyf'][updated].getCoordinates(dest['glyf'])
            point_match=(ends==ends2 and len(xy)==len(xy2) and
                         all(x2-x==2 and y2==y
                             for (x,y),(x2,y2) in zip(xy,xy2)))
            all_points.append(point_match)
            src=BoundsPen(source_gs);source_gs[original].draw(src)
            dst=BoundsPen(dest_gs);dest_gs[dst_cmap[ord(c)]].draw(dst)
            widths.append(abs((src.bounds[2]-src.bounds[0])-
                              (dst.bounds[2]-dst.bounds[0]))<.1)
            shift=(563-source['hmtx'][src_cmap[ord(c)]][0])/2
            shift_errors.append(abs((dst.bounds[0]-src.bounds[0])-shift)<.1)
        assert all(widths) and all(shift_errors) and all(all_points),style
        units=','.join(map(str,sorted(set(source_metrics(style)))))
        out.append(f'| {style} | {units} units | {sum(all_points)}/10 | {sum(shift_errors)}/10 |')
    out.extend(['','The 1.2 lining zero uses source `zero.slash`, not a newly',
       'overlaid stroke. Every one of the ten digit outlines matches its',
       'corresponding Noto source outline, up to **exactly two design units**',
       'of horizontal translation. This is checked point-by-point for all',
       'ten numeral glyphs and all four styles (40 of 40 pass).',
       '1.2 still applies a new all-glyph TrueType hint pass because many',
       'nonfigure glyph outlines change and need coherent global hint programs.',
       'Thus it does not claim bit-for-bit equivalence with Noto’s original',
       'hand-tuned hint programs. Compare 12–24 px across renderers.',''])
    p=ROOT/'ArborMono-FigureGeometryAudit.md'
    p.write_text('\n'.join(out),encoding='utf-8')
    print(p)


if __name__=='__main__':
    make_proof()
    audit_geometry()
