"""Arbor Mono 1.3 capital spacing pass over the four version 1.2 TTFs."""
from pathlib import Path
import sys
import tempfile
import unicodedata as ud

from fontTools.ttLib import TTFont
from PIL import ImageFont
from ttfautohint import StemWidthMode, ttfautohint

FAMILIES = {"G":"G", **dict(zip("HIJΗΙНІЈƖӀꙆͿЇ", "HIJHIHIJIIIJI"))}


def stems_at(face, character, y):
    mask, (x, top) = face.getmask2(character, anchor="ls")
    row = bytes(mask)[(-y-top)*mask.size[0]:(1-y-top)*mask.size[0]]
    runs = []
    for i, value in enumerate(row):
        if value >= 128:
            if i == 0 or row[i-1] < 128:
                runs.append([x+i, x+i+1])
            else:
                runs[-1][1] = x+i+1
    return runs


def revise(source, output):
    font = TTFont(source)
    cmap = font.getBestCmap()
    face = ImageFont.truetype(str(source), 1000)
    italic = "Italic" in source.stem
    bold = "Bold" in source.stem
    stems = {c: (stems_at(face, c, 200), stems_at(face, c, 510)) for c in "GHIJ"}
    edited = {}
    j_forms = set()
    for cp, name in cmap.items():
        character = chr(cp)
        family = FAMILIES.get(ud.normalize("NFD", character)[0])
        if not family or name in edited:
            continue
        glyph = font["glyf"][name]
        if glyph.isComposite():
            raise ValueError(name)
        lower, upper = stems[family]
        # Detached accents sit beside or above the capitals in polytonic Greek.
        # Adjust only the letter contour, preserving each accent's own geometry.
        start = 0
        shift = {"G": 0, "H": 19, "I": -37, "J": -16 if bold else -9}[family] if italic else (
            -28 if family == "J" else 0)
        for end in glyph.endPtsOfContours:
            points = glyph.coordinates[start:end+1]
            ys = [y for x, y in points]
            if min(ys) <= 10 and (max(ys) == 714 or family == "G" and max(ys) == 724):
                for i in range(start, end+1):
                    x, y = glyph.coordinates[i]
                    t = (y-200)/310
                    edges = [(a+(c-a)*t, b+(d-b)*t)
                             for (a,b),(c,d) in zip(lower,upper)]
                    if family == "G":
                        # Tuck the bowl's right edge and spur away from the next stem.
                        dx = -22*min(1,max(0,(x-315)/180))
                    elif family == "H":
                        left, right = edges[0][0], edges[-1][1]
                        dx = 14*min(1, max(0,(left-x)/65)) - 14*min(1,max(0,(x-right)/65))
                        if italic:
                            # Strengthen the two straight stems towards the counter.
                            first, second = edges[0][1], edges[-1][0]
                            weight = 13 if bold else 9
                            center = (edges[0][1]+edges[-1][0])/2
                            dx += 11*max(-1,min(1,(x-center)/95))
                            dx += shift + weight*max(0, 1-abs(x-first)/65)
                            dx -= weight*max(0, 1-abs(x-second)/65)
                    else:
                        left, right = edges[0]
                        if family == "I":
                            # I's unusually heavy shaft dominates HIGH at text size.
                            # Reduce shaft weight and fade the correction into the serifs.
                            center = (left+right)/2
                            strength = 19 if bold else 9
                            taper = min(1, max(0, min(y,714-y)/120))
                            trim = -taper*strength*max(-1,min(1,(x-center)/((right-left)/2)))

                            extension = (20 if bold else 24) if italic else (45 if bold else 52)
                            dx = shift + trim + extension*(min(1,max(0,(x-right)/74)) -
                                            min(1,max(0,(left-x)/74)))
                        else:
                            extension = (39 if bold else 40) if italic else (32 if bold else 38)
                            dx = shift*min(1,max(0,(y+240)/240)) + max(0,min(1,(y-580)/90))*extension*(
                                (.70 if italic else 1)*min(1,max(0,(x-right)/73)) -
                                (2.40 if italic else 1)*min(1,max(0,(left-x)/73)))
                    glyph.coordinates[i] = (round(x+dx), y)
            elif shift and min(ys) > 714:
                for i in range(start, end+1):
                    x, y = glyph.coordinates[i]
                    glyph.coordinates[i] = (x+shift,y)
            start = end+1
        glyph.recalcBounds(font["glyf"])
        font["hmtx"][name] = (font["hmtx"][name][0], glyph.xMin)
        edited[name] = shift
        if family == "J":
            j_forms.add(name)

    if italic:
        for name in edited:
            if name not in j_forms:
                continue
            g = font["glyf"][name]
            for index,(x,y) in enumerate(g.coordinates):
                # Shorten the hook and bring its outer end toward the shaft.
                # Above baseline, retain the established angle.
                hook = min(1,max(0,-y/240))
                terminal = min(1,max(0,(y-620)/94))
                right_tip = min(1,max(0,(x-445)/105))
                g.coordinates[index] = (round(x-8+hook*16-terminal*right_tip*17),
                                        round(y*.89) if y<0 else y)
            g.recalcBounds(font["glyf"])
            font["hmtx"][name] = (font["hmtx"][name][0],g.xMin)
            edited[name] -= 8

        # The angled sides of AW leave very little air where the A foot
        # approaches W's left downstroke. Move that stroke inward low down.
        w_forms = {name for cp,name in cmap.items()
                   if ud.normalize("NFD",chr(cp))[0] == "W"}
        for name in w_forms:
            g = font["glyf"][name]
            for index,(x,y) in enumerate(g.coordinates):
                height = min(1,max(0,(680-y)/650))
                left = min(1,max(0,(235-x)/130))
                g.coordinates[index] = (round(x+37*height*left),y)
            g.recalcBounds(font["glyf"])
            font["hmtx"][name] = (font["hmtx"][name][0],g.xMin)

    if italic:
        # Balance opposite sides of A in both words. W and Z were left-heavy
        # in their cells. Center them by their ink distribution across height.
        placement = {"A": -29, "W": 26, "Y": 13, "Z": 20,
                     "Α": -29, "А": -29, "Υ": 13, "Ζ": 20}
        for cp,name in cmap.items():
            offset = placement.get(ud.normalize("NFD",chr(cp))[0])
            if offset is None or name in edited:
                continue
            g = font["glyf"][name]
            if g.isComposite() or not g.numberOfContours:
                continue
            g.coordinates.translate((offset,0))
            g.recalcBounds(font["glyf"])
            font["hmtx"][name] = (font["hmtx"][name][0],g.xMin)
            edited[name] = offset

    if italic:
        fitted = set()
        for cp,name in cmap.items():
            base = ud.normalize("NFD",chr(cp))[0]
            if base not in "AWΑА" or name in fitted:
                continue
            g = font["glyf"][name]
            if g.isComposite() or not g.numberOfContours:
                continue
            for index,(x,y) in enumerate(g.coordinates):
                if base == "W":
                    # Carry the right downstroke into the WA gap. The top
                    # serif already reaches the next cell, so taper below it.
                    band = min(1,max(0,(680-y)/180))
                    leg = min(1,max(0,(x-(210+.22*y))/69))
                    dx = 39*band*leg
                else:
                    # Give the left diagonal a little more reach through
                    # the body, with the foot and apex held in place.
                    band = min(1,max(0,(y-42)/103),max(0,(690-y)/150))
                    leg = min(1,max(0,((188+.47*y)-x)/64))
                    dx = -14*band*leg
                g.coordinates[index] = (round(x+dx),y)
            g.recalcBounds(font["glyf"])
            font["hmtx"][name] = (font["hmtx"][name][0],g.xMin)
            fitted.add(name)

    shear_by_name = {}
    if italic:
        # Use F/J as the reference for the straight-stem capitals. Measured
        # centerline slopes in v1.5 varied from 0.16 to 0.21 units per unit.
        shear_by_family = {"H": .025, "I": -.017, "K": .024,
                           "L": -.008, "M": .032, "N": .025}
        related = {"Κ": "K", "К": "K", "Μ": "M", "М": "M", "Ν": "N"}
        for cp, name in cmap.items():
            base = ud.normalize("NFD", chr(cp))[0]
            family = FAMILIES.get(base, related.get(base, base))
            shear = shear_by_family.get(family)
            if shear is None or name in shear_by_name:
                continue
            g = font["glyf"][name]
            if g.isComposite() or not g.numberOfContours:
                continue
            # Shift complete contours, including the accent, about mid-cap.
            for index, (x, y) in enumerate(g.coordinates):
                g.coordinates[index] = (round(x+shear*(y-357)), y)
            g.recalcBounds(font["glyf"])
            font["hmtx"][name] = (font["hmtx"][name][0],g.xMin)
            shear_by_name[name] = shear

    # Translate the mark attachment points along with J's stem and accents.
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            subtable = getattr(subtable, "ExtSubTable", subtable)
            if not hasattr(subtable, "BaseCoverage"):
                continue
            for name, record in zip(subtable.BaseCoverage.glyphs, subtable.BaseArray.BaseRecord):
                if edited.get(name) or shear_by_name.get(name):
                    for anchor in record.BaseAnchor:
                        if anchor is not None:
                            anchor.XCoordinate += edited.get(name,0) + round(
                                shear_by_name.get(name,0)*(anchor.YCoordinate-357))
    for name in font.getGlyphOrder():
        glyph = font["glyf"][name]
        glyph.removeHinting()
    for tag in ("fpgm", "prep", "cvt ", "gasp"):
        if tag in font:
            del font[tag]
    font["head"].fontRevision = 2.0
    for record in font["name"].names:
        if record.nameID in (3, 5):
            record.string = record.toUnicode().replace("1.200", "2.000")
    with tempfile.TemporaryDirectory() as temp:
        intermediate = Path(temp)/source.name
        font.save(intermediate)
        ttfautohint(in_file=str(intermediate), out_file=str(output),
                    hinting_range_min=7, hinting_range_max=72, hinting_limit=220,
                    increase_x_height=0, windows_compatibility=True, no_info=True,
                    gray_stem_width_mode=StemWidthMode[sys.argv[3]],
                    gdi_cleartype_stem_width_mode=StemWidthMode[sys.argv[3]],
                    dw_cleartype_stem_width_mode=StemWidthMode[sys.argv[3]])
    print(source.name, len(edited), stems)


if __name__ == "__main__":
    for source in sorted(Path(sys.argv[1]).glob("*.ttf")):
        revise(source, Path(sys.argv[2])/source.name)
