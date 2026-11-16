#!/usr/bin/env python3
"""Build Laurel Mono, a hinted monospaced derivative of OFL Gelasio.

The outlines come from Eben Sorkin's Gelasio, an independently drawn,
Georgia-metric-compatible design, not from Microsoft's Georgia font.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
import sys
import unicodedata
import zipfile

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables
from fontTools.ttLib.tables.otBase import ValueRecord
from fontTools.varLib.instancer import instantiateVariableFont

BASE = Path(__file__).resolve().parent
OUT = BASE / "LaurelMono"
CELL = 1152  # 56.25% of the em, between Consolas and Cascadia Code
SIDE_INSET = 56
FAMILY = "Laurel Mono"

sys.path.insert(0, str(BASE / ".fontbuild"))
from ttfautohint import StemWidthMode, ttfautohint  # noqa: E402


def set_name(font: TTFont, name_id: int, value: str) -> None:
    # fontTools creates both Macintosh and Windows Unicode name records.
    font["name"].setName(value, name_id, 3, 1, 0x409)
    font["name"].setName(value, name_id, 1, 0, 0)


def retain_non_kern_layout(font: TTFont) -> None:
    # Every keystroke must advance one cell.  Preserve mark/locl features but
    # disable ligatures and pair-positioning that would disturb the grid.
    for table_tag, disabled in (
        ("GPOS", {"kern", "dist", "palt", "halt", "chws"}),
        ("GSUB", {"liga", "dlig", "clig", "hlig", "calt", "rclt"}),
    ):
        if table_tag not in font:
            continue
        feat_list = font[table_tag].table.FeatureList
        if feat_list is None:
            continue
        for record in feat_list.FeatureRecord:
            if record.FeatureTag in disabled:
                record.Feature.LookupListIndex = []
                record.Feature.LookupCount = 0


def add_optical_sa_pair(font: TTFont, cmap: dict[int, str], *,
                        italic: bool, weight: int) -> int:
    """Open the `Sa` pair without changing either character's cell advance.

    A fixed-pitch font must not change cursor positions for a pair: traditional
    kerning using XAdvance would break alignment. Use an isolated GPOS PairPos
    lookup that changes only the second glyph's XPlacement. This moves the
    small a *inside its own cell* when following S, and leaves all other a
    occurrences untouched. The at gap gets narrower by exactly the same
    amount, balancing `Saturday` without affecting line length or columns.
    """
    assert "GPOS" in font
    positioning = font["GPOS"].table
    records = positioning.FeatureList.FeatureRecord
    kern_index = next(i for i, rec in enumerate(records) if rec.FeatureTag == "kern")
    kern_feature = records[kern_index].Feature
    assert kern_feature.LookupListIndex == [], "Unexpected inherited kerning"

    offset = {(False, 400): 44, (False, 700): 48,
              (True, 400): 60, (True, 700): 48}[(italic, weight)]

    pair_record = otTables.PairValueRecord()
    pair_record.SecondGlyph = cmap[ord("a")]
    pair_record.Value1 = None
    pair_record.Value2 = ValueRecord()
    pair_record.Value2.XPlacement = offset  # no XAdvance on either glyph

    pair_set = otTables.PairSet()
    pair_set.PairValueRecord = [pair_record]
    pair_set.PairValueCount = 1

    coverage = otTables.Coverage()
    coverage.glyphs = [cmap[ord("S")]]
    pair_positioning = otTables.PairPos()
    pair_positioning.Format = 1
    pair_positioning.Coverage = coverage
    pair_positioning.ValueFormat1 = 0
    pair_positioning.ValueFormat2 = 0x0001  # XPlacement, not XAdvance
    pair_positioning.PairSet = [pair_set]
    pair_positioning.PairSetCount = 1

    lookup = otTables.Lookup()
    lookup.LookupType = 2  # pair positioning
    lookup.LookupFlag = 0
    lookup.SubTable = [pair_positioning]
    lookup.SubTableCount = 1
    lookup_index = len(positioning.LookupList.Lookup)
    positioning.LookupList.Lookup.append(lookup)
    positioning.LookupList.LookupCount = lookup_index + 1
    kern_feature.LookupListIndex = [lookup_index]
    kern_feature.LookupCount = 1

    # Latin script already advertises `kern`. Also enable the position-only
    # pair in the default script, when it exists, for broad renderer support.
    for script_record in positioning.ScriptList.ScriptRecord:
        script = script_record.Script
        langs = ([script.DefaultLangSys] if script.DefaultLangSys else []) + [
            rec.LangSys for rec in script.LangSysRecord
        ]
        for lang in langs:
            if kern_index not in lang.FeatureIndex:
                lang.FeatureIndex.insert(0, kern_index)
                lang.FeatureCount = len(lang.FeatureIndex)
    return offset


def move_anchor(anchor, xform: tuple[float, ...]) -> None:
    if anchor is not None:
        scale, shift, *shear = xform
        anchor.XCoordinate = round(anchor.XCoordinate * scale + shift +
                                   anchor.YCoordinate * (shear[0] if shear else 0))


def adjust_mark_anchors(font: TTFont, xforms: dict) -> None:
    """Keep combining-diacritic anchors aligned with adjusted glyph outlines."""
    if "GPOS" not in font:
        return

    def fix_lookup(typ, sub):
        if typ == 9:  # extension positioning
            fix_lookup(sub.ExtensionLookupType, sub.ExtSubTable)
        elif typ == 4:  # mark-to-base
            for g, rec in zip(sub.MarkCoverage.glyphs, sub.MarkArray.MarkRecord):
                move_anchor(rec.MarkAnchor, xforms[g])
            for g, rec in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
                for a in rec.BaseAnchor:
                    move_anchor(a, xforms[g])
        elif typ == 5:  # mark-to-ligature
            for g, rec in zip(sub.MarkCoverage.glyphs, sub.MarkArray.MarkRecord):
                move_anchor(rec.MarkAnchor, xforms[g])
            for g, rec in zip(sub.LigatureCoverage.glyphs, sub.LigatureArray.LigatureAttach):
                for component in rec.ComponentRecord:
                    for a in component.LigatureAnchor:
                        move_anchor(a, xforms[g])
        elif typ == 6:  # mark-to-mark
            for g, rec in zip(sub.Mark1Coverage.glyphs, sub.Mark1Array.MarkRecord):
                move_anchor(rec.MarkAnchor, xforms[g])
            for g, rec in zip(sub.Mark2Coverage.glyphs, sub.Mark2Array.Mark2Record):
                for a in rec.Mark2Anchor:
                    move_anchor(a, xforms[g])

    for lookup in font["GPOS"].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            fix_lookup(lookup.LookupType, sub)


def append_slash(pen, box: tuple[float, float, float, float], weight: int):
    """Draw a high-contrast / across the counter of zero, joining its bowl."""
    l, b, r, t = box
    width, height = r - l, t - b
    # Enough overlap at both ends to avoid a floating dash at text sizes.
    lo = (l + width * 0.21, b + height * 0.11)
    hi = (l + width * 0.79, t - height * 0.11)
    dx, dy = hi[0] - lo[0], hi[1] - lo[1]
    length = math.hypot(dx, dy)
    half_stroke = (155 if weight == 400 else 200) / 2
    normal = (-dy * half_stroke / length, dx * half_stroke / length)
    pt = lambda p, sign: (round(p[0] + sign * normal[0]), round(p[1] + sign * normal[1]))
    # Clockwise contour, matching Gelasio's clockwise outer zero contour.
    pen.moveTo(pt(lo, 1))
    pen.lineTo(pt(hi, 1))
    pen.lineTo(pt(hi, -1))
    pen.lineTo(pt(lo, -1))
    pen.closePath()


def mono_m_warp(u: float, italic: bool, weight: int) -> float:
    """Compress the *counters* of m while retaining the width of its stems.

    Uniformly condensing Georgia/Gelasio's very broad m makes three vertical
    stems roughly 40% too thin compared with n and h.  These measured regions
    correspond to the three stems at mid-x-height.  Allocate more width to
    those regions and less to the two counters, with fixed endpoints.
    """
    # Based on black-pixel scans at mid-x-height of original Gelasio m.
    stem_edges = {
        (False, 400): (0.09, 0.215, 0.44, 0.56, 0.785, 0.91),
        (False, 700): (0.08, 0.24, 0.425, 0.585, 0.76, 0.925),
        (True, 400): (0.05, 0.18, 0.42, 0.55, 0.78, 0.915),
        (True, 700): (0.045, 0.215, 0.415, 0.585, 0.77, 0.945),
    }
    knots = (0.0, *stem_edges[(italic, weight)], 1.0)
    stem_total = sum(knots[i + 1] - knots[i] for i in (1, 3, 5))
    # M remains slightly lighter than n to keep its two counters open at 10px.
    stem_factor = 1.35
    counter_factor = (1.0 - stem_factor * stem_total) / (1.0 - stem_total)
    slopes = (counter_factor, stem_factor, counter_factor, stem_factor,
              counter_factor, stem_factor, counter_factor)
    if u < 0:
        return u * slopes[0]
    acc = 0.0
    for i, slope in enumerate(slopes):
        lo, hi = knots[i : i + 2]
        if u <= hi:
            return acc + (u - lo) * slope
        acc += (hi - lo) * slope
    return 1.0 + (u - 1.0) * slopes[-1]


def draw_optical_m(shape, out_pen, bounds, scale: float, shift: float,
                   italic: bool, weight: int):
    """Warp m in x, leaving its bowl shape, baseline and vertical hints intact."""
    affine = RecordingPen()
    shape.replay(TransformPen(affine, (scale, 0, 0, 1, shift, 0)))
    left = bounds[0] * scale + shift
    width = (bounds[2] - bounds[0]) * scale

    def warp(pt):
        if pt is None:
            return None
        x, y = pt
        return (left + width * mono_m_warp((x - left) / width, italic, weight), y)

    for operation, args in affine.value:
        if operation in ("moveTo", "lineTo", "qCurveTo", "curveTo"):
            args = tuple(warp(point) for point in args)
        getattr(out_pen, operation)(*args)


def draw_optical_capital(shape, out_pen, bounds, scale: float, shift: float,
                         source_path: Path, weight: int, character: str):
    """Rebalance M or W dark-to-light rhythm within its fixed-width cell.

    A uniform x-scale attenuates Gelasio's dramatically contrasted wide strokes.
    Measure actual dark spans at several cap-height slices and use monotone
    piecewise maps to redistribute width *within* each slice. This thickens
    the thin outer upright and the major diagonals without expanding the cell.
    Interpolating between slices follows the slope of italic capitals. For W,
    retain more white in the two descending notches so they don't close at 10px.
    """
    from PIL import ImageFont

    image_size = 1024
    sample_font = ImageFont.truetype(str(source_path), image_size)
    sample_font.set_variation_by_axes([weight])
    bitmap = sample_font.getmask(character)
    bitmap_w, bitmap_h = bitmap.size
    pixel_to_units = 2048 / image_size
    sample_fractions = (0.065, 0.18, 0.32, 0.48, 0.64, 0.80, 0.94)
    maps = []

    def prepare_map(frac):
        scan_y = round(frac * (bitmap_h - 1))
        runs = []
        start = None
        for px in range(bitmap_w):
            dark = bitmap.getpixel((px, scan_y)) > 160
            if dark and start is None:
                start = px
            elif not dark and start is not None:
                if px - start >= 2:
                    runs.append((start * pixel_to_units, px * pixel_to_units))
                start = None
        if start is not None and bitmap_w - start >= 2:
            runs.append((start * pixel_to_units, bitmap_w * pixel_to_units))
        if len(runs) < 2:
            return lambda x: x

        left, right = runs[0][0], runs[-1][1]
        dark_len = sum(b - a for a, b in runs)
        white_len = right - left - dark_len
        if white_len <= 0:
            return lambda x: x

        # Preserve counter openings, especially where W's diagonals converge.
        target = 1.35 if character == "M" else 1.44 - 0.28 * frac
        min_white = 0.4 if character == "M" else 0.46
        dark_factor = min(target, (right - left - white_len * min_white) / dark_len)
        white_factor = (right - left - dark_factor * dark_len) / white_len
        parts = []
        cursor = left
        for a, b in runs:
            if a > cursor:
                parts.append((cursor, a, white_factor))
            parts.append((a, b, dark_factor))
            cursor = b

        def warp(x):
            if x <= left or x >= right:
                return x
            after = left
            for a, b, factor in parts:
                if x <= b:
                    return after + (x - a) * factor
                after += (b - a) * factor
            return x

        return warp

    for fraction in sample_fractions:
        maps.append(prepare_map(fraction))

    _, bottom, _, top = bounds

    def warp_point(pt):
        if pt is None:
            return None
        x, y = pt
        fraction = (top - y) / (top - bottom)
        if fraction <= sample_fractions[0]:
            adjusted = maps[0](x)
        elif fraction >= sample_fractions[-1]:
            adjusted = maps[-1](x)
        else:
            adjusted = x
            for i in range(len(sample_fractions) - 1):
                lo, hi = sample_fractions[i : i + 2]
                if lo <= fraction <= hi:
                    blend = (fraction - lo) / (hi - lo)
                    adjusted = maps[i](x) * (1 - blend) + maps[i + 1](x) * blend
                    break
        return (adjusted * scale + shift, y)

    for operation, args in shape.value:
        if operation in ("moveTo", "lineTo", "qCurveTo", "curveTo"):
            args = tuple(warp_point(pt) for pt in args)
        getattr(out_pen, operation)(*args)


def make_font(style: str, italic: bool, weight: int, *, lining: bool = False) -> Path:
    src = BASE / ("gelasio-italic-variable.ttf" if italic else "gelasio-upright-variable.ttf")
    vf = TTFont(src)
    font = instantiateVariableFont(vf, {"wght": weight}, inplace=False)

    if lining:
        # Gelasio includes separately DRAWN cap-height tabular lining figures.
        # Map their glyphs directly to Unicode digits in this distinct family.
        # The slashed-zero form is built by Gelasio itself from zero.tf and
        # zeroSlash_part.; our custom zero bar must not be added on top.
        digit_glyphs = (
            "zero.tf.zero", "one.tf", "two.tf", "three.tf", "four.tf",
            "five.tf", "six.tf", "seven.tf", "eight.tf", "nine.tf",
        )
        for subtable in font["cmap"].tables:
            if subtable.isUnicode():
                for digit, glyph in enumerate(digit_glyphs):
                    subtable.cmap[ord("0") + digit] = glyph

    cmap = font.getBestCmap()
    zero_name = cmap[ord("0")]
    unicode_for_glyph: dict[str, list[int]] = {}
    for cp, name in cmap.items():
        unicode_for_glyph.setdefault(name, []).append(cp)

    original_set = font.getGlyphSet()
    outlines = {}
    metrics = {}
    xforms = {}

    for glyph_name in font.getGlyphOrder():
        shape = DecomposingRecordingPen(original_set)
        original_set[glyph_name].draw(shape)
        bounds_pen = BoundsPen(original_set)
        shape.replay(bounds_pen)
        bounds = bounds_pen.bounds

        cps = unicode_for_glyph.get(glyph_name, [])
        is_mark = bool(cps) and all(
            unicodedata.category(chr(cp)) in ("Mn", "Me") for cp in cps
        )
        nonprinting = glyph_name in {".null", "nonmarkingreturn", "NULL", "CR"}
        cell = 0 if is_mark or nonprinting else CELL
        if bounds is None:
            scale, shift = 1.0, 0.0
        elif is_mark:
            # Keep zero-width, off-origin marks near their original positioning.
            scale, shift = 1.0, 0.0
        else:
            ink_width = bounds[2] - bounds[0]
            # W needs additional shoulder room; its four diagonals otherwise
            # become conspicuously weaker than those in M and V.
            inset = 32 if glyph_name == cmap[ord("W")] else SIDE_INSET
            scale = min(1.0, (CELL - 2 * inset) / max(ink_width, 1))
            # Widen the naturally narrow t and light r in running text.
            # Keep the independently designed heavy r essentially unchanged.
            if glyph_name == cmap[ord("t")]:
                target = (790 if italic else 805) if weight == 400 else (845 if italic else 850)
                scale = max(scale, min(target / max(ink_width, 1), (CELL - 2 * SIDE_INSET) / max(ink_width, 1)))
            elif glyph_name == cmap[ord("r")] and weight == 400:
                target = 900 if italic else 845
                scale = max(scale, min(target / max(ink_width, 1), (CELL - 2 * SIDE_INSET) / max(ink_width, 1)))
            shift = (CELL - ink_width * scale) / 2 - bounds[0] * scale

        xforms[glyph_name] = (scale, shift)
        out_pen = TTGlyphPen(None)
        if glyph_name == cmap[ord("M")] and bounds is not None:
            draw_optical_capital(shape, out_pen, bounds, scale, shift, src, weight, "M")
        elif glyph_name == cmap[ord("W")] and bounds is not None:
            draw_optical_capital(shape, out_pen, bounds, scale, shift, src, weight, "W")
        elif glyph_name == cmap[ord("m")] and bounds is not None:
            draw_optical_m(shape, out_pen, bounds, scale, shift, italic, weight)
        else:
            transformed_pen = TransformPen(out_pen, (scale, 0, 0, 1, shift, 0))
            shape.replay(transformed_pen)

        if glyph_name == zero_name and bounds is not None and not lining:
            l, b, r, t = bounds
            append_slash(out_pen, (l * scale + shift, b, r * scale + shift, t), weight)

        glyph = out_pen.glyph()
        outlines[glyph_name] = glyph
        metrics[glyph_name] = (cell, round(bounds[0] * scale + shift) if bounds else 0)

    font["glyf"].glyphs = outlines
    font["hmtx"].metrics = metrics
    retain_non_kern_layout(font)
    add_optical_sa_pair(font, cmap, italic=italic, weight=weight)
    adjust_mark_anchors(font, xforms)

    # Bytecode from variable source must not survive changed coordinates.
    for tag in ("fpgm", "prep", "cvt ", "hdmx", "LTSH", "VDMX"):
        if tag in font:
            del font[tag]

    font["post"].isFixedPitch = 1
    font["hhea"].advanceWidthMax = CELL
    font["OS/2"].xAvgCharWidth = CELL
    font["OS/2"].panose.bProportion = 9  # monospaced
    font["OS/2"].usWeightClass = weight
    font["OS/2"].fsSelection &= ~(0x01 | 0x20 | 0x40)
    if italic:
        font["OS/2"].fsSelection |= 0x01
    if weight == 700:
        font["OS/2"].fsSelection |= 0x20
    if weight == 400 and not italic:
        font["OS/2"].fsSelection |= 0x40
    font["head"].macStyle = (1 if weight == 700 else 0) | (2 if italic else 0)
    font["head"].fontRevision = 1.2 if lining else 1.5

    family = "Laurel Mono Lining" if lining else FAMILY
    ps = ("LaurelMonoLining-" if lining else "LaurelMono-") + style.replace(" ", "")
    version = "1.200" if lining else "1.500"
    names = {
        0: "Copyright 2022 The Gelasio Project Authors; Laurel Mono adaptation 2026.",
        1: family,
        2: style,
        3: f"{version}; LaMo; {ps}",
        4: f"{family} {style}",
        5: f"Version {version}; TrueType autohinted for 7-72 ppem",
        6: ps,
        8: "Gelasio Project Authors; Laurel Mono derivative",
        9: "Gelasio Project Authors; adapted into a fixed-width face",
        11: "https://github.com/SorkinType/Gelasio",
        13: "SIL Open Font License, Version 1.1",
        14: "https://openfontlicense.org/open-font-license-official-text/",
        16: family,
        17: style,
    }
    for name_id, content in names.items():
        set_name(font, name_id, content)

    destination = BASE / "LaurelMonoLining" if lining else OUT
    destination.mkdir(parents=True, exist_ok=True)
    unhinted = destination / (ps + "-unhinted.ttf")
    finished = destination / (ps + ".ttf")
    font.save(unhinted)
    # Write substantial actual per-glyph TrueType instructions for major
    # renderers; use stem quantization and x-height alignment at small sizes.
    ttfautohint(
        in_file=str(unhinted),
        out_file=str(finished),
        hinting_range_min=7,
        hinting_range_max=72,
        hinting_limit=220,
        increase_x_height=16,
        windows_compatibility=True,
        gray_stem_width_mode=StemWidthMode.QUANTIZED,
        gdi_cleartype_stem_width_mode=StemWidthMode.STRONG,
        dw_cleartype_stem_width_mode=StemWidthMode.STRONG,
        no_info=True,
    )
    unhinted.unlink()
    return finished


def validate(paths: list[Path]) -> None:
    from PIL import ImageFont

    for path in paths:
        font = TTFont(path)
        cmap = font.getBestCmap()
        advances = {font["hmtx"].metrics[cmap[ord(c)]][0] for c in (
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "!@#$%^&*()-_=+[]{};:'\",.<>/?\\|`~ "
        )}
        assert advances == {CELL}, (path, advances)
        assert font["post"].isFixedPitch == 1
        assert all(k in font for k in ("fpgm", "prep", "cvt "))
        positioning = font["GPOS"].table
        kern = next(f.Feature for f in positioning.FeatureList.FeatureRecord
                    if f.FeatureTag == "kern")
        assert len(kern.LookupListIndex) == 1
        pair = positioning.LookupList.Lookup[kern.LookupListIndex[0]].SubTable[0]
        assert pair.ValueFormat1 == 0 and pair.ValueFormat2 == 1
        assert pair.Coverage.glyphs == [cmap[ord("S")]]
        record = pair.PairSet[0].PairValueRecord[0]
        assert record.SecondGlyph == cmap[ord("a")]
        assert record.Value1 is None and not hasattr(record.Value2, "XAdvance")
        # Real shaping, including the pair adjustment, must preserve the grid.
        pillow = ImageFont.truetype(str(path), 150)
        assert pillow.getlength("Saturday") == 8 * pillow.getlength("S")
        assert pillow.getlength("Saturday", features=["-kern"]) == 8 * pillow.getlength("S")
        hint_count = sum(
            bool(getattr(font["glyf"][g], "program", None))
            for g in font.getGlyphOrder()
        )
        zero_glyph = font["glyf"][cmap[ord("0")]]
        assert zero_glyph.numberOfContours >= 3
        print(f"{path.name}: {len(font.getGlyphOrder())} glyphs, "
              f"{hint_count} outlined glyphs with hint programs, "
              f"zero contours={zero_glyph.numberOfContours}, "
              f"size={path.stat().st_size:,} B")


def bundle(paths: list[Path]) -> Path:
    readme = OUT / "README.txt"
    readme.write_text(
        "LAUREL MONO — VERSION 1.5 (OPTICAL 'Sa' PAIR)\n\n"
        "A true fixed-width, Georgia-inspired transitional serif, constructed\n"
        "from Gelasio, the open-licensed Georgia-metric-compatible typeface\n"
        "by the Gelasio Project authors. No Georgia font files were used.\n\n"
        "Included styles: Regular, Bold, Italic, Bold Italic.\n"
        f"All printable ASCII characters have a {CELL}/2048-em advance.\n"
        "The zero has a diagonal slash; uppercase O does not.\n"
        "The Sa pair has a position-only correction (no advance change).\n"
        "Every style contains embedded TrueType autohint instructions\n"
        "optimized for 7–72 pixel-per-em text and tuned x-height alignment.\n\n"
        "Install (Windows): select all four .ttf files, right-click, Install.\n"
        "Install (Mac): double-click each .ttf and select Install Font.\n"
        "Use font family 'Laurel Mono' in a text editor or document.\n\n"
        "The fonts are distributed under the SIL Open Font License 1.1;\n"
        "see OFL.txt for license and required attribution.\n"
        "Original design: https://github.com/SorkinType/Gelasio\n",
        encoding="utf-8",
    )
    zip_path = BASE / "LaurelMono-FontFamily.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in paths:
            z.write(path, path.name)
        z.write(readme, readme.name)
        z.write(BASE / "OFL-Gelasio.txt", "OFL.txt")
        z.write(BASE / "build_laurel_mono.py", "SOURCE-build_laurel_mono.py")
        z.write(BASE / "make_laurel_preview.py", "SOURCE-make_laurel_preview.py")
        z.write(BASE / "SPACING_NOTES.md", "SPACING_NOTES.md")
        for image_name in ("LaurelMono-Specimen.png", "LaurelMono-HintingProof.png",
                           "LaurelMono-SpacingProof.png", "LaurelMono-SaComparison.png"):
            if (BASE / image_name).exists():
                z.write(BASE / image_name, image_name)
        z.write(BASE / "review_laurel_spacing.py", "SOURCE-review_laurel_spacing.py")
    return zip_path


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [
        make_font("Regular", False, 400),
        make_font("Bold", False, 700),
        make_font("Italic", True, 400),
        make_font("Bold Italic", True, 700),
    ]
    validate(paths)
    from make_laurel_preview import make_hint_proof, make_specimen

    make_specimen()
    make_hint_proof()
    from review_laurel_spacing import make as make_spacing_proof, make_sa_comparison
    make_spacing_proof()
    make_sa_comparison()
    print("BUNDLE", bundle(paths))


if __name__ == "__main__":
    main()
