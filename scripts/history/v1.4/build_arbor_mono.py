#!/usr/bin/env python3
"""Build Arbor Mono, a fixed-pitch, Noto Serif-derived TrueType family.

The freely licensed Noto Serif outlines are redrawn onto a compact cell,
with local stroke rebalancing and new native TrueType hint programs. This is
an independent derivative and does not modify or replace installed Noto fonts.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
import unicodedata
import zipfile

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from build_laurel_mono import (
    StemWidthMode, adjust_mark_anchors, retain_non_kern_layout,
    set_name, ttfautohint,
)

ROOT = Path(__file__).resolve().parent
SYSTEM_NOTO = Path('/usr/share/fonts/truetype/noto')
CELL = 563  # 0.563 em; 9.0 px at 16 ppem, very close to Laurel's 0.5625
SIDE_INSET = 19
SUFFIXES = ('Regular','Bold','Italic','BoldItalic')
SOURCES = {s: SYSTEM_NOTO / f'NotoSerif-{s}.ttf' for s in SUFFIXES}


@lru_cache(maxsize=8)
def source_raster(font_path: str):
    from PIL import ImageFont
    return ImageFont.truetype(font_path,1000)


def weight_for(style: str) -> int:
    return 700 if 'Bold' in style else 400


def append_slash(pen, bbox, bold: bool) -> None:
    """An integral diagonal stroke that connects to the zero counter."""
    left, bottom, right, top = bbox
    width, height = right-left, top-bottom
    lo = (left + width * .21, bottom + height * .10)
    hi = (left + width * .79, top - height * .10)
    vx, vy = hi[0]-lo[0], hi[1]-lo[1]
    norm = math.hypot(vx, vy)
    # Match the slash's optical stroke to the 16-ppem body strokes. A 38-unit
    # thin slash disappeared at small pixel sizes; the high-contrast slash
    # should remain unambiguous in 0/O comparisons down to 10-12 ppem.
    radius = (98 if bold else 76) / 2
    n = (-vy*radius/norm, vx*radius/norm)
    def offset(p, sign):
        return (round(p[0]+sign*n[0]), round(p[1]+sign*n[1]))
    pen.moveTo(offset(lo, 1))
    pen.lineTo(offset(hi, 1))
    pen.lineTo(offset(hi, -1))
    pen.lineTo(offset(lo, -1))
    pen.closePath()


def optical_dark_warp(shape, pen, bbox, scale, shift, src: Path,
                      character: str) -> None:
    """Preserve source stroke weights when fitting wide glyphs to the grid.

    Per-row source black spans are widened nonuniformly and white counters
    proportionally narrowed. Interpolation across the cap/x-height follows
    diagonals in upright and italic designs; end points and y stay unchanged.
    Unlike blanket horizontal scaling, this operation can keep a 94-unit
    stem in `n` and a 94-unit stem in `l` optically comparable. The warp
    remains monotone and preserves a minimum width in all visible counters.
    """
    px_size = 1000
    source = source_raster(str(src))
    mask = source.getmask(character)
    bw, bh = mask.size
    factor = px_size / 1000
    sample_fractions = (.07, .18, .31, .46, .61, .78, .93)
    # Source stem restoration ideally uses 1/scale. Very broad shapes need
    # a cap so W's small white valleys and the m arches do not close.
    base=unicodedata.normalize('NFD',character)[0]
    limit = {'m': 1.76, 'M': 1.55, 'W': 1.48, 'w': 1.48}.get(base, 1.30)
    target_base = min(1.0/max(scale,.01),limit)

    def prepare(frac):
        y = round(frac*(bh-1))
        runs=[]; start=None
        for x in range(bw):
            black = mask.getpixel((x,y)) > 150
            if black and start is None: start=x
            if not black and start is not None:
                if x-start>=2:runs.append((start/factor,x/factor))
                start=None
        if start is not None and bw-start>=2:runs.append((start/factor,bw/factor))
        if len(runs)<2:
            return lambda x:x
        left,right=runs[0][0],runs[-1][1]
        dark=sum(b-a for a,b in runs)
        white=right-left-dark
        if white<=0:return lambda x:x
        # At lower W valleys the counters get smaller and need more air.
        target = target_base * (1-.10*frac if base=='W' else 1)
        min_white = .47 if base=='W' else .42
        black_factor=min(target,(right-left-white*min_white)/dark)
        white_factor=(right-left-black_factor*dark)/white
        pieces=[];cursor=left
        for a,b in runs:
            if a>cursor:pieces.append((cursor,a,white_factor))
            pieces.append((a,b,black_factor))
            cursor=b
        def warp(x):
            if x<=left or x>=right:return x
            after=left
            for a,b,slope in pieces:
                if x<=b:return after+(x-a)*slope
                after+=(b-a)*slope
            return x
        return warp

    maps=[prepare(f) for f in sample_fractions]
    bottom,top=bbox[1],bbox[3]
    def warp_point(pt):
        if pt is None:return None
        x,y=pt
        frac=(top-y)/(top-bottom)
        if frac<=sample_fractions[0]:new_x=maps[0](x)
        elif frac>=sample_fractions[-1]:new_x=maps[-1](x)
        else:
            for i in range(len(maps)-1):
                a,b=sample_fractions[i:i+2]
                if a<=frac<=b:
                    t=(frac-a)/(b-a)
                    new_x=maps[i](x)*(1-t)+maps[i+1](x)*t
                    break
        return (new_x*scale+shift,y)

    for op,args in shape.value:
        if op in ('moveTo','lineTo','qCurveTo','curveTo'):
            args=tuple(warp_point(pt) for pt in args)
        getattr(pen,op)(*args)


def fit_italic(shape, drawing, box, scale, shift, src, character, inset):
    """Fit in unslanted coordinates, with restrained stroke compensation."""
    slant = .123
    adjusted = RecordingPen()
    shape.replay(TransformPen(adjusted, (scale, 0, slant*(1-scale), 1, shift, 0)))
    optical = RecordingPen()
    optical_dark_warp(shape, optical, box, scale, shift, src, character)
    # The affine version preserves straight shafts. Keep a modest share of
    # the optical compensation on other forms so counters stay open.
    blend = 0 if unicodedata.normalize("NFD", character)[0] in "HΗН" else .23
    fitted = RecordingPen()
    for (op, affine), (_, warped) in zip(adjusted.value, optical.value):
        points = tuple(None if a is None else (a[0]+blend*(b[0]+slant*(1-scale)*a[1]-a[0]), a[1])
                       for a, b in zip(affine, warped))
        getattr(fitted, op)(*points)
    bounds = BoundsPen(None)
    fitted.replay(bounds)
    x0, _, x1, _ = bounds.bounds
    # Retain the slant within a small, consistent outer inset.
    limit = CELL - 2*min(inset, 13)
    compression = min(1, limit/(x1-x0))
    translation = (CELL-compression*(x0+x1))/2
    fitted.replay(TransformPen(drawing, (compression, 0, 0, 1, translation, 0)))
    return compression*scale, compression*shift+translation, compression*slant*(1-scale)


def narrow_serif_warp(shape, pen, bbox, shift, character: str,
                      desired_width: float, source_font: Path,
                      source_character: str | None = None) -> None:
    """Broaden terminal details while preserving the full original stem.

    This deliberately does *not* scale the whole outline, even in a narrow
    vertical band. FreeType raster probes locate the central stem at two
    heights. Its two sides (plus eight units) become protected boundaries;
    only points outside them are displaced towards the edges of the cell.
    For italic styles the protected boundaries follow the source stem's
    slant, so the horizontal serif treatment never thickens its core.
    """
    left,bottom,right,top=bbox
    extra=(desired_width-(right-left))/2
    source=source_raster(str(source_font))
    mask,(mask_x_offset,_)=source.getmask2(source_character or character,
                                           anchor='ls')
    sample_heights=(.47,.67)

    def stem_edges(frac):
        y=min(mask.size[1]-1,round(frac*(mask.size[1]-1)))
        runs=[];start=None
        for x in range(mask.size[0]):
            black=mask.getpixel((x,y))>150
            if black and start is None:start=x
            if not black and start is not None:
                if x-start>=50:runs.append((start+mask_x_offset,x+mask_x_offset))
                start=None
        if not runs:
            raise ValueError(f'Missing stem for {character} at sample {frac}')
        return runs[0]

    edges=[stem_edges(frac) for frac in sample_heights]

    def smoothstep(t):
        t=max(0.0,min(1.0,t))
        return t*t*(3-2*t)

    def warp_point(pt):
        if pt is None:return None
        x,y=pt
        frac=(top-y)/(top-bottom)
        t=(frac-sample_heights[0])/(sample_heights[1]-sample_heights[0])
        # Extrapolate the italic stem position above/below the two probes.
        core_left=edges[0][0]+(edges[1][0]-edges[0][0])*t-8
        core_right=edges[0][1]+(edges[1][1]-edges[0][1])*t+8
        if character=='t':
            # Crossbar is in the top third; leave the lower curved hook alone.
            emphasis=1-smoothstep((frac-.28)/.32)
        elif character=='r':
            emphasis=max(1-smoothstep((frac-.22)/.51),
                         .24*smoothstep((frac-.80)/.15))
        else:
            emphasis=1.0
        if x<core_left:
            x-=extra*emphasis*(core_left-x)/max(core_left-left,1)
        elif x>core_right:
            x+=extra*emphasis*(x-core_right)/max(right-core_right,1)
        return (x+shift,y)

    for op,args in shape.value:
        if op in ('moveTo','lineTo','qCurveTo','curveTo'):
            args=tuple(warp_point(pt) for pt in args)
        getattr(pen,op)(*args)


def j_optical_recenter(shape, pen, shift: float, style: str) -> None:
    """Center j's *shaft*, not its left-sweeping descender.

    Noto's original j has a 220-unit union bounding box, but its upright
    vertical stem and dot sit 57 units right of i. The outline-wide bbox
    centering used in 1.1 preserved that offset in every monospaced cell.
    Italic j has a much more pronounced leftward descender and its upper
    stem sits 104 units to the right. Keep the bottom hook in the cell while
    moving its upper stem, and preserve the stroke widths exactly.
    """
    core={'Regular':-57,'Bold':-57,'Italic':-104,'BoldItalic':-104}[style]
    hook={'Regular':-57,'Bold':-57,'Italic':-74,'BoldItalic':-62}[style]

    def pos(pt):
        if pt is None:return None
        x,y=pt
        if y>=0:extra=core
        elif y<=-240:extra=hook
        else:
            u=-y/240
            extra=core+(hook-core)*u*u*(3-2*u)
        return (x+shift+extra,y)

    for op,args in shape.value:
        if op in ('moveTo','lineTo','qCurveTo','curveTo'):
            args=tuple(pos(pt) for pt in args)
        getattr(pen,op)(*args)


def j_extend_entrance_serif(shape, style: str):
    """Give j a short right-hand top serif to balance j-k and i-j gaps.

    Its Noto source entrance serif extends only to the left of its stem.
    The j outline is surgically adjusted at the horizontal top bar, rather
    than stretching its already-correct vertical shaft or round dot. The
    italic top bar follows the existing italic stem slope.
    """
    top=536
    thickness=53 if 'Bold' in style else 42
    extension=55
    cmds=shape.value
    result=RecordingPen()
    modified=False
    for i,(op,args) in enumerate(cmds):
        if (not modified and op=='lineTo' and len(args)==1 and args[0][1]==top
                and i+1<len(cmds) and cmds[i+1][0]=='lineTo'
                and len(cmds[i+1][1])==1 and cmds[i+1][1][0][1]<0):
            px,py=args[0]
            below_x,below_y=cmds[i+1][1][0]
            low_y=top-thickness
            x_at_low=px+(below_x-px)*(thickness/(top-below_y))
            result.lineTo((px+extension,py))
            result.lineTo((x_at_low+extension,low_y))
            result.lineTo((x_at_low,low_y))
            modified=True
        else:
            getattr(result,op)(*args)
    if not modified:
        raise ValueError(f'Unable to extend j top serif in {style}')
    return result


def glyph_width_target(ch: str, style: str) -> float | None:
    """Optical widths for shapes that otherwise look stranded in wide cells."""
    if ch=='t': return 385 if style=='Regular' else 420 if style=='Bold' else 363 if style=='Italic' else 420
    if ch=='r': return 452 if style=='Regular' else 470 if style=='Italic' else None
    if ch=='i': return 385 if style=='Regular' else 395 if style=='Bold' else 340 if style=='Italic' else 370
    if ch=='l': return 355 if style=='Regular' else 380 if style=='Bold' else 315 if style=='Italic' else 345
    return None


def make_font(style: str, *, oldstyle: bool) -> Path:
    src=SOURCES[style]
    assert src.is_file(), f'Missing installed OFL source: {src}'
    font=TTFont(src)
    assert font['head'].unitsPerEm == 1000
    if oldstyle:
        # Purpose-drawn TABULAR oldstyle glyphs, not vertically scaled figures.
        names=('zero','one','two','three','four','five','six','seven','eight','nine')
        for table in font['cmap'].tables:
            if table.isUnicode():
                for digit,name in enumerate(names):
                    table.cmap[48+digit]=name+'.tosf'
    else:
        # Noto already designs all ten figures on the SAME 559-unit advance.
        # It also ships a bespoke slashed-zero alternate. The earlier build
        # needlessly redrew its zero and centered/compressed the others.
        for table in font['cmap'].tables:
            if table.isUnicode():
                table.cmap[48]='zero.slash'
    cmap=font.getBestCmap()
    zero_name=cmap[48]
    unicodes={}
    for cp,name in cmap.items():unicodes.setdefault(name,[]).append(cp)
    glyph_set=font.getGlyphSet()
    outlines={};metrics={};xforms={}
    special={cmap[ord(c)]:c for c in 'mMWw'}
    small={cmap[ord(c)]:c for c in 'tril'}
    printable={cmap[ord(c)]:c for c in
               'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@#%&$'}
    j_variants={cmap[ord(c)] for c in 'jĵǰȷјϳ' if ord(c) in cmap}
    digit_roots={'zero','one','two','three','four','five','six','seven',
                 'eight','nine'}
    preserve_figures={n for n in font.getGlyphOrder()
                      if n in digit_roots or n in {'zero.slash'} or
                      any(n==root+'.tosf' for root in digit_roots)}

    for name in font.getGlyphOrder():
        shape=DecomposingRecordingPen(glyph_set)
        glyph_set[name].draw(shape)
        bounds=BoundsPen(glyph_set)
        shape.replay(bounds)
        box=bounds.bounds
        cps=unicodes.get(name,[])
        mapped_letter=next((chr(cp) for cp in cps
                            if unicodedata.category(chr(cp)).startswith('L')),None)
        # Precomposed Latin accents need the same stem-protected serif treatment
        # as the unaccented form. Dotless i, l-stroke and Cyrillic i are shape
        # siblings without Unicode canonical decomposition.
        base=(unicodedata.normalize('NFD',mapped_letter)[0]
              if mapped_letter else None)
        base={'ı':'i','ł':'l','і':'i'}.get(base,base)
        narrow=small.get(name) or (base if base is not None and base in 'iltr'
                                   else None)
        target=glyph_width_target(narrow,style) if narrow else None
        mark=bool(cps) and all(unicodedata.category(chr(cp)) in ('Mn','Me') for cp in cps)
        nonprinting=name in ('.null','nonmarkingreturn','NULL','CR')
        advance=0 if mark or nonprinting else CELL
        native_advance=font['hmtx'][name][0]
        if box is None or mark:
            scale,shift=1.0,0.0
        elif name in preserve_figures:
            # Keep the complete authored figure geometry, even the deliberate
            # optical overhang of italic 7. Preserve the DIFFERENCE between
            # left and right sidebearings. Noto's tabular figures are already
            # professionally arranged relative to their original advance;
            # only translate the original advance center to our new cell.
            scale=1.0
            shift=(CELL-native_advance)/2
        else:
            width=box[2]-box[0]
            special_char=special.get(name)
            inset=(13 if special_char=='W' else 24 if special_char=='M' else
                   21 if special_char in ('m','w') else SIDE_INSET)
            scale=min(1.0,(CELL-2*inset)/max(width,1))
            if target is not None:
                # Only the foot, crossbar or shoulder is broadened later.
                # Never enlarge the narrow character's vertical stem.
                scale=min(1.0,scale)
            shift=(CELL-width*scale)/2-box[0]*scale
            # The originals' italic overhang is often deliberate. Recenter
            # only if the source's optical position would exceed a sensible
            # cell. This mirrors the treatment of native tabular figures
            # without perturbing upright S/a and other established pairs.
            if ('Italic' in style and mapped_letter is not None and
                    name not in j_variants and narrow is None and
                    abs(box[0]-(native_advance-box[2]))>=24):
                native_shift=(CELL-native_advance*scale)/2
                if (box[0]*scale+native_shift>=-20 and
                        box[2]*scale+native_shift<=CELL+20):
                    shift=native_shift
        xforms[name]=(scale,shift + (
            {'Regular':-57,'Bold':-57,'Italic':-104,'BoldItalic':-104}[style]
            if name in j_variants else 0))
        drawing=RecordingPen()
        if name in j_variants and box is not None:
            widened=j_extend_entrance_serif(shape,style)
            j_optical_recenter(widened,drawing,shift,style)
        elif narrow is not None and box is not None and target is not None and target>(box[2]-box[0]):
            narrow_serif_warp(shape,drawing,box,shift,narrow,target,src,
                              source_character=mapped_letter or narrow)
        elif box is not None and scale<.999 and (
                name in printable or any(unicodedata.category(chr(cp)).startswith('L')
                                         for cp in cps)):
            # Extend the stroke-weight correction through the complete
            # Latin, Greek, and Cyrillic inventory, including accented letters.
            # Otherwise 'é' alongside 'e' retains the old thinned stem.
            character=printable.get(name) or next(chr(cp) for cp in cps
                            if unicodedata.category(chr(cp)).startswith('L'))
            if 'Italic' in style:
                xforms[name] = fit_italic(shape,drawing,box,scale,shift,src,character,inset)
            else:
                optical_dark_warp(shape,drawing,box,scale,shift,src,character)
        else:
            shape.replay(TransformPen(drawing,(scale,0,0,1,shift,0)))
        if oldstyle and name==zero_name and box is not None:
            left,bottom,right,top=box
            append_slash(drawing,(left*scale+shift,bottom,right*scale+shift,top),
                         bold=weight_for(style)==700)
        # Derive LSB from actual new outlines, not the pre-warp bounding box.
        # This is particularly important for expanded end serifs and italics.
        actual_bounds=BoundsPen(None)
        drawing.replay(actual_bounds)
        # Some italic j diacritics (notably caron) extend well left of the
        # ordinary descender. Recenter only the exceptional completed outline
        # if its union exceeds its cell; the base j keeps its optical shift.
        if (name in j_variants and actual_bounds.bounds is not None
                and actual_bounds.bounds[0]<0):
            left_edge,right_edge=actual_bounds.bounds[0],actual_bounds.bounds[2]
            correction=max(-left_edge,min(2-left_edge,563-right_edge))
            if correction>0:
                adjusted=RecordingPen()
                drawing.replay(TransformPen(adjusted,(1,0,0,1,correction,0)))
                drawing=adjusted
                xscale,xshift,*shear=xforms[name]
                xforms[name]=(xscale,xshift+correction,*shear)
                actual_bounds=BoundsPen(None)
                drawing.replay(actual_bounds)
        pen=TTGlyphPen(None)
        drawing.replay(pen)
        outlines[name]=pen.glyph()
        metrics[name]=(advance,round(actual_bounds.bounds[0]) if actual_bounds.bounds else 0)

    font['glyf'].glyphs=outlines
    font['hmtx'].metrics=metrics
    retain_non_kern_layout(font)
    adjust_mark_anchors(font,xforms)
    for tag in ('fpgm','prep','cvt ','hdmx','LTSH','VDMX','DSIG'):
        if tag in font:del font[tag]
    font['post'].isFixedPitch=1
    font['hhea'].advanceWidthMax=CELL
    font['OS/2'].xAvgCharWidth=CELL
    font['OS/2'].panose.bProportion=9
    font['OS/2'].usWeightClass=weight_for(style)
    font['OS/2'].fsSelection &= ~(0x01|0x20|0x40)
    if 'Italic' in style:font['OS/2'].fsSelection|=0x01
    if 'Bold' in style:font['OS/2'].fsSelection|=0x20
    if style=='Regular':font['OS/2'].fsSelection|=0x40
    font['head'].macStyle=(1 if 'Bold' in style else 0)|(2 if 'Italic' in style else 0)
    font['head'].fontRevision=1.2
    family='Arbor Mono Oldstyle' if oldstyle else 'Arbor Mono'
    ps=('ArborMonoOldstyle-' if oldstyle else 'ArborMono-')+style
    for id,value in {
        0:'Copyright 2015 Google LLC. Noto Serif outlines adapted into Arbor Mono, 2026.',
        1:family,2:style,3:f'1.200; ArMo; {ps}',4:f'{family} {style}',
        5:'Version 1.200; embedded TrueType instructions for 7–72 ppem',6:ps,
        8:'Noto Serif authors; Arbor Mono adaptation',
        9:'Noto Serif authors; adapted from an OFL-licensed design',
        11:'https://github.com/notofonts/latin-greek-cyrillic',
        13:'SIL Open Font License, Version 1.1',
        14:'https://openfontlicense.org/open-font-license-official-text/',
        16:family,17:style,
    }.items():set_name(font,id,value)

    destination=ROOT/('ArborMonoOldstyle' if oldstyle else 'ArborMono')
    destination.mkdir(exist_ok=True)
    unhinted=destination/f'{ps}-unhinted.ttf'
    finished=destination/f'{ps}.ttf'
    font.save(unhinted)
    ttfautohint(in_file=str(unhinted),out_file=str(finished),
        hinting_range_min=7,hinting_range_max=72,hinting_limit=220,
        increase_x_height=0,windows_compatibility=True,
        gray_stem_width_mode=StemWidthMode.NATURAL,
        gdi_cleartype_stem_width_mode=StemWidthMode.NATURAL,
        dw_cleartype_stem_width_mode=StemWidthMode.NATURAL,
        no_info=True)
    unhinted.unlink()
    return finished


def validate(paths: list[Path], *, oldstyle: bool) -> None:
    from PIL import ImageFont
    for file in paths:
        f=TTFont(file)
        cmap=f.getBestCmap()
        alphabet='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        punctuation='!@#$%^&*()-_=+[]{};:\'",.<>/?\\|`~ '
        advances={f['hmtx'].metrics[cmap[ord(c)]][0] for c in alphabet+punctuation}
        assert advances=={CELL},(file,advances)
        assert f['post'].isFixedPitch == 1
        assert all(k in f for k in ('fpgm','prep','cvt '))
        assert f['glyf'][cmap[48]].numberOfContours>=3
        if oldstyle:
            assert all(cmap[48+i].endswith('.tosf') for i in range(10))
        else:
            assert all(not cmap[48+i].endswith('.tosf') for i in range(10))
        count=sum(bool(getattr(f['glyf'][g],'program',None)) for g in f.getGlyphOrder())
        assert count>=2900,(file,count)
        r=ImageFont.truetype(str(file),16)
        assert abs(r.getlength('Saturday')-8*r.getlength('a'))<.01
        print(file.name,'hinted glyphs',count,'zero contours',f['glyf'][cmap[48]].numberOfContours)


def bundle(paths: list[Path], *, oldstyle: bool) -> Path:
    fam='ArborMonoOldstyle' if oldstyle else 'ArborMono'
    folder=ROOT/fam
    readme=folder/'README.txt'
    readme.write_text(
        f"ARBOR MONO {'OLDSTYLE' if oldstyle else 'LINING'} — 1.2\n\n"
        "A compact monospaced, optically balanced derivative of Noto Serif.\n"
        "The four styles are Regular, Bold, Italic and Bold Italic.\n"
        f"All printable ASCII glyphs use {CELL}/1000-em advance width.\n"
        "Latin, Greek and Cyrillic letters use stroke-aware condensation where needed.\n"
        "The narrow t, r, i and l extend their serifs, not vertical stems.\n"
        "Zero is diagonally slashed; O is not. Lining uses Noto's zero.slash.\n"
        "Numbers are tabular and " + ("oldstyle.\n" if oldstyle else "cap-height lining.\n")+
        "Embedded TrueType auto-hint programs cover 7–72 ppem.\n"
        "No pair kerning changes character advances or column alignment.\n\n"
        "Install all four TTFs by selecting them in Windows and choosing Install.\n"
        "The distinct Arbor Mono and Arbor Mono Oldstyle families can coexist.\n"
        "Source: Google Noto Serif 2.004, installed OFL-licensed release.\n"
        "Noto Serif copyright 2015 Google LLC; see OFL.txt and SOURCE_COPYRIGHT.txt.\n",
        encoding='utf-8')
    archive=ROOT/f'{fam}-FontFamily.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for file in paths:z.write(file,file.name)
        z.write(readme,'README.txt')
        z.write(ROOT/'OFL-Noto.txt','OFL.txt')
        z.write('/usr/share/doc/fonts-noto-core/copyright','SOURCE_COPYRIGHT.txt')
        z.write(ROOT/'build_arbor_mono.py','SOURCE-build_arbor_mono.py')
        z.write(ROOT/'build_laurel_mono.py','SOURCE-build_laurel_mono.py')
        z.write(ROOT/'make_arbor_preview.py','SOURCE-make_arbor_preview.py')
        z.write(ROOT/'audit_arbor_full.py','SOURCE-audit_arbor_full.py')
        z.write(ROOT/'audit_arbor_glyphs.py','SOURCE-audit_arbor_glyphs.py')
        z.write(ROOT/'audit_arbor_ij.py','SOURCE-audit_arbor_ij.py')
        z.write(ROOT/'audit_arbor_inventory.py','SOURCE-audit_arbor_inventory.py')
        z.write(ROOT/'audit_arbor_figures_v12.py','SOURCE-audit_arbor_figures_v12.py')
        z.write(ROOT/'ARBOR_DESIGN_NOTES.md','DESIGN_NOTES.md')
        for name in ('ArborMono-QA.txt','ArborMono-ASCIIAudit.png',
                     'ArborMono-UnicodeAudit.png','ArborMono-RevisionAudit.png',
                     'ArborMono-FigureRevision.png','ArborMono-IJComparison.png',
                     'ArborMono-FullGlyphAudit.md','ArborMono-FigureGeometryAudit.md'):
            file=ROOT/name
            if file.exists():z.write(file,name)
        specimen=ROOT/f'{fam}-Specimen.png'
        if specimen.exists():z.write(specimen,specimen.name)
        comparison=ROOT/'ArborMono-Comparison.png'
        if comparison.exists():z.write(comparison,comparison.name)
    print('ARCHIVE',archive)
    return archive


def main():
    for src in SOURCES.values():assert src.is_file(),src
    # The license and provenance document is prepared separately below.
    assert (ROOT/'OFL-Noto.txt').is_file()
    for oldstyle in (False,True):
        paths=[make_font(style,oldstyle=oldstyle) for style in SUFFIXES]
        validate(paths,oldstyle=oldstyle)
    from make_arbor_preview import render_all
    render_all()
    from audit_arbor_full import make_sheet,scan
    from audit_arbor_glyphs import target_grid
    make_sheet()
    scan()
    target_grid()
    for oldstyle in (False,True):
        fam='ArborMonoOldstyle' if oldstyle else 'ArborMono'
        bundle([ROOT/fam/f'{fam}-{style}.ttf' for style in SUFFIXES],oldstyle=oldstyle)


if __name__=='__main__':main()
