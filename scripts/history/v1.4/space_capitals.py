"""Arbor Mono 1.3 capital spacing pass over the four version 1.2 TTFs."""
from pathlib import Path
import sys
import tempfile
import unicodedata as ud

from fontTools.ttLib import TTFont
from PIL import ImageFont
from ttfautohint import StemWidthMode, ttfautohint

FAMILIES = dict(zip("HIJΗΙНІЈƖӀꙆͿЇ", "HIJHIHIJIIIJI"))


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
    stems = {c: (stems_at(face, c, 200), stems_at(face, c, 510)) for c in "HIJ"}
    edited = {}
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
        shift = {"H": 9, "I": -12, "J": -45 if bold else -38}[family] if italic else (
            -28 if family == "J" else 0)
        for end in glyph.endPtsOfContours:
            points = glyph.coordinates[start:end+1]
            ys = [y for x, y in points]
            if min(ys) <= 10 and max(ys) == 714:
                for i in range(start, end+1):
                    x, y = glyph.coordinates[i]
                    t = (y-200)/310
                    edges = [(a+(c-a)*t, b+(d-b)*t)
                             for (a,b),(c,d) in zip(lower,upper)]
                    if family == "H":
                        left, right = edges[0][0], edges[-1][1]
                        dx = 14*min(1, max(0,(left-x)/65)) - 14*min(1,max(0,(x-right)/65))
                        if italic:
                            # Strengthen the two straight stems towards the counter.
                            first, second = edges[0][1], edges[-1][0]
                            weight = 13 if bold else 9
                            dx += shift + weight*max(0, 1-abs(x-first)/65)
                            dx -= weight*max(0, 1-abs(x-second)/65)
                    else:
                        left, right = edges[0]
                        if family == "I":
                            extension = (20 if bold else 24) if italic else (45 if bold else 52)
                            dx = shift + extension*(min(1,max(0,(x-right)/74)) -
                                            min(1,max(0,(left-x)/74)))
                        else:
                            extension = (22 if bold else 26) if italic else (32 if bold else 38)
                            dx = shift*min(1,max(0,(y+240)/240)) + max(0,min(1,(y-580)/90))*extension*(
                                min(1,max(0,(x-right)/73)) -
                                min(1,max(0,(left-x)/73)))
                    glyph.coordinates[i] = (round(x+dx), y)
            elif shift and min(ys) > 714:
                for i in range(start, end+1):
                    x, y = glyph.coordinates[i]
                    glyph.coordinates[i] = (x+shift,y)
            start = end+1
        glyph.recalcBounds(font["glyf"])
        font["hmtx"][name] = (font["hmtx"][name][0], glyph.xMin)
        edited[name] = shift

    # Translate the mark attachment points along with J's stem and accents.
    for lookup in font["GPOS"].table.LookupList.Lookup:
        for subtable in lookup.SubTable:
            subtable = getattr(subtable, "ExtSubTable", subtable)
            if not hasattr(subtable, "BaseCoverage"):
                continue
            for name, record in zip(subtable.BaseCoverage.glyphs, subtable.BaseArray.BaseRecord):
                if edited.get(name):
                    for anchor in record.BaseAnchor:
                        if anchor is not None:
                            anchor.XCoordinate += edited[name]
    for name in font.getGlyphOrder():
        glyph = font["glyf"][name]
        glyph.removeHinting()
    for tag in ("fpgm", "prep", "cvt ", "gasp"):
        if tag in font:
            del font[tag]
    font["head"].fontRevision = 1.4
    for record in font["name"].names:
        if record.nameID in (3, 5):
            record.string = record.toUnicode().replace("1.200", "1.400")
    with tempfile.TemporaryDirectory() as temp:
        intermediate = Path(temp)/source.name
        font.save(intermediate)
        ttfautohint(in_file=str(intermediate), out_file=str(output),
                    hinting_range_min=7, hinting_range_max=72, hinting_limit=220,
                    increase_x_height=0, windows_compatibility=True, no_info=True,
                    gray_stem_width_mode=StemWidthMode.NATURAL,
                    gdi_cleartype_stem_width_mode=StemWidthMode.NATURAL,
                    dw_cleartype_stem_width_mode=StemWidthMode.NATURAL)
    print(source.name, len(edited), stems)


if __name__ == "__main__":
    for source in sorted(Path(sys.argv[1]).glob("*.ttf")):
        revise(source, Path(sys.argv[2])/source.name)
