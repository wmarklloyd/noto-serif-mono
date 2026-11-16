# Noto Serif Mono 1.2: a Noto Serif monospaced family, audited glyph by glyph

## Scope and provenance

Noto Serif Mono is a distinct four-style derivative of the OFL-licensed **Noto
Serif 2.004** source distributed with Debian's `fonts-noto-core` package. It
is not the original Noto Serif, and is not derived from proprietary Georgia.
Noto Serif Mono and Noto Serif Mono Oldstyle use separate family and PostScript names.

The font is intended to retain Noto Serif's open, transitional serifs at small
text sizes while enforcing a fixed advance. Its advance is **563/1000 em**,
approximately **9.008 px at 16 ppem**, so a word of eight characters consumes
eight identical positions. It is close in proportion to Laurel Mono's
1152/2048 (0.5625), which was chosen after comparisons with Consolas,
Cascadia Code, and other monospaced families.

## Version 1.2: the figures were already tabular

Noto Serif's original lining digits `0`–`9` have the same **559-unit
advance** in every weight and posture. The previous Arbor pass needlessly
centered each numeral on its ink bounding box and sometimes squeezed it
horizontally. This was particularly damaging to italics: source Italic `7`
spans x=89…580, but Arbor 1.1 moved it **53 units to the left**, erasing
Noto's intentional italic sidebearing balance. Bold Italic digits were
sometimes compressed, changing their strokes and counters.

Noto also ships a **purpose-drawn, separately hinted `zero.slash` glyph**.
The old Arbor version added a makeshift diagonal on top of an ordinary zero.
Version 1.2 instead maps `0` to the authentic Noto alternate in the lining
family. All ten lining figures retain the **exact source outline geometry**,
merely translated +2 units into the new 563-unit cell. Their original
distinctive sidebearings are preserved. The oldstyle release uses Noto's
independently drawn tabular oldstyle figures (advances 579/585/588 units,
depending on style), keeping their relative sidebearings; its oldstyle
zero still requires an added slash, since Noto has no oldstyle slashed
equivalent. The oldstyle figures are not vertically scaled lining numerals.

### TrueType hinting, tested separately from geometry

A controlled comparison showed that **rehinting completely unchanged Noto
figure outlines** with the old Arbor settings visibly altered the pixels
at 12–24 ppem. Original Noto glyph instructions depend on Noto's own
`fpgm`, `prep`, and `cvt` tables. Pasting just its original numeral
instructions into an unrelated autohinted font produced corrupt glyphs;
using the entire Noto hint environment made many redesigned characters
unhinted. That was inconsistent with the aim of extensive hinting.

Noto Serif Mono 1.2 therefore continues to generate **native TrueType hint
programs for all 3,225 or 3,237 drawable glyphs**, with gentler, natural
stem modes in grayscale and ClearType, and no 16-unit forced x-height
enlargement. On the original, unmodified Noto control font these settings
usually reduced differences from Noto's native small-size raster compared
to the old configuration. This does not guarantee pixel-for-pixel Noto
equivalence: Noto's original globally coordinated hints are different.

### What the numerical lesson changed in other letters

* An authored italic letter's asymmetric source sidebearings are meaningful.
  For italic Latin, Greek and Cyrillic letters whose source placement fits
  within the fixed cell, we now preserve that relation rather than always
  recentering on the outline bounding box. Upright `S` and `a` retain their
  calibrated positions to avoid reintroducing the `Sa` collision.
* Character shapes are expanded or compressed only where monospacing truly
  requires it, preserving the core stem and minimum counter clearance.
* The `ij` gap came from centering `j` on its *whole hooked descender*, which
  leaves its upper shaft shifted right of `i`. The shaft and dot were
  recentered optically, the right entrance serif was modestly extended,
  and relevant accented, Cyrillic, and Greek forms were also corrected.
* A few Noto italic figures naturally extend past their nominal advance,
  even in Noto itself. The exhaustive audit marks these as intentional,
  source-matched overhangs instead of distorting the figures to satisfy a
  rectangular-boundary test.

Compare `NotoSerifMono-FigureRevision.png`, `NotoSerifMono-IJComparison.png`,
`NotoSerifMono-FigureGeometryAudit.md` and `NotoSerifMono-FullGlyphAudit.md` for
illustrated before/after tests and the exhaustive glyph census.

## Why `Saturday` is hard

The supplied four-word screenshot was rendered at approximately **16 ppem**.
In that environment a full character cell spans about nine pixels. An 8-pixel
ink width leaves only one pixel for the combined white margins. One cannot
give every adjacency the same amount of whitespace without changing outlines,
subpixel positioning, or the fixed cell itself.

Using identical 16-ppem grayscale rasterization, the *bounding-box* gaps
between the user's important pairs were:

| Pair | Laurel Mono Regular | Noto Serif Mono Regular |
| --- | ---: | ---: |
| `Sa` in Saturday | 2 px | 2 px |
| `at` in Saturday | 2 px | 2 px |
| `La` in Lantern | 1 px | 1 px |
| `an` in Lantern | 1 px | 1 px |
| `Ma` in Magic | 1 px | 1 px |
| `ag` in Magic | 2 px | 1 px |
| `la` in lavender | 4 px | 3 px |
| `av` in lavender | 1 px | 1 px |

The original image has some threshold-dependent differences, and minimum
same-row whitespace can be greater than these whole-glyph bounding-box gaps.
These numbers are useful comparative diagnostics, not an instruction to force
every pair into an identical raster pattern.

### What we changed from Laurel's experiments

* **No pair-specific `Sa` advance changes.** Laurel's 44-unit `Sa` positioning
  correction becomes only 0.34 pixel at 16 ppem; some hinted rasterizers show
  essentially identical pixels with it on or off. Arbor balances underlying
  glyph outlines and side bearings first. No enabled feature should change
  cursor advance widths.
* **Stem-protected serif extension** for `t`, `r`, `i`, and `l` avoids leaving
  narrow letters isolated in the 9-pixel cell **without fattening their main
  stems**. The center stem is measured at two heights in the source font;
  those two boundaries are protected while end serifs or shoulders outside
  them are carefully extended. For italics the protected zone follows the
  slope of the stem.
* **Nonlinear stroke-preserving condensation** for wide letters restores a
  substantial portion of the black strokes lost to a naïve horizontal squash.
  The transformation uses seven vertical slices, bounded counter compression
  and monotone interpolation. It applies to alphabetic characters throughout
  the Noto Serif-supported Unicode inventory, including accented Latin,
  Greek and Cyrillic. `m`, `M`, `W` and `w` get separate safety caps to avoid
  destroying their unusually narrow interior spaces. The designed minimum
  white widths are 42% of the original (47% for `W`), subject to the detected
  spans and sample positions.
* **A clear slash in zero**, distinct from the letter O. The lining family
  now maps Noto's purpose-drawn `zero.slash`. The two numeral families use Noto's
  *purpose-drawn* figure shapes, not vertical scaling of ordinary figures.
* **TrueType rehinting** is performed after all outline edits: generated glyph
  instructions plus `fpgm`, `prep`, and `cvt` are present for every style,
  targeting 7–72 ppem with natural grayscale and ClearType stem tuning.

## Version 1.1: what was wrong with lowercase `l` and `t`?

The initial 1.0 conversion expanded `l` and `t` with a uniform horizontal
stretch: it made their vertical strokes **too heavy** next to neighboring
letters. At the same time, letters that needed squeezing, particularly `n`,
`h` and `m`, had their stems thinned. The resulting text alternated between
excessively black and pale letters even though all character cells were equal.

The comparison below measures representative vertical stem widths in font
design units, using a 1000-ppem render at the middle of each letter. The
first number is the initial 1.0 glyph; the second is the 1.1 glyph.

| Letter | Regular 1.0 → 1.1 | Bold 1.0 → 1.1 | Correction |
| --- | --- | --- | --- |
| `i` | 107 → **94** | 167 → **152** | Preserve main shaft; extend only serifs |
| `l` | 107 → **94** | 167 → **152** | Preserve main shaft; extend only serifs |
| `t` | 117 → **94** | 175 → **152** | Extend crossbar without inflating vertical shaft |
| `r` | 101 → **94** | 152 → **152** | Keep shaft weight; use shoulder extension |
| `n` | 84 → **93–96** | 128–129 → **151–152** | Restore thinned stems |
| `m` | 75–76 → **90–92** | 103–104 → **116–119** | Restore stems subject to counter safety |

Unchanged original Noto Serif vertical stems typically measure about 94
units in Regular and 152 in Bold at that sample height. The 1.1 figures are
an optical consistency target, not a requirement that every letter have the
same visual black area. With three tightly packed stems, `m` must still use
lighter strokes to keep its counters open. The terminal serifs also cannot
erase every perceived gap around `l` or `t` in a true monospaced design.

### Whole-font checks

The audit includes every printable ASCII character and sample texts covering
accents, Greek, Cyrillic, numberforms, punctuation, and the deliberately
distinct `0`, `O`, `1`, `I`, `l`, and `|`. At 12 and 16 pixels the actual
hinted rasters are shown, rather than an enlarged vector approximation.

For **each of the eight finished font files**, a full scan found:

* **2,840 Unicode cmap entries** and **2,529 drawable nonmark mappings**.
* **Zero unexpected horizontal outline overflows** outside the inspected cell
  tolerance of −20 to 583 units (the actual advance is 0 to 563). Noto's
  intentional numeral overhangs are documented separately.
* **Zero non-monospaced drawable characters** and no missing outlines for
  mapped letters or numbers.
* **3,225 or 3,237 embedded hinted glyph programs**, depending on style.

The included `NotoSerifMono-QA.txt` is the machine-generated result, and
`NotoSerifMono-ASCIIAudit.png` and `NotoSerifMono-UnicodeAudit.png` show the visual
inspection. These tests establish outline integrity and fixed-pitch metrics,
not universal perfection on every display rasterizer.

## The two numeral families

* **Noto Serif Mono** maps `0`–`9` to Noto Serif's lining/tabular numerals.
* **Noto Serif Mono Oldstyle** maps `0`–`9` to the independent `.tosf` glyphs.

The font names differ, so both families can be installed simultaneously.

## Remaining tradeoff

Optical texture depends on adjacent shapes and the renderer. A serifed
monospaced font can improve the average rhythm, but cannot achieve the pair
spacing of proportional Noto Serif while retaining exact alignment. At tiny
sizes, one pixel is about one ninth of the entire character cell; renderer
hinting, fractional positioning, and subpixel color treatment matter at least
as much as design-unit changes. Test final choices at the intended size and
in the intended application.

## Source and license

Noto Serif font data: Copyright 2015 Google LLC; SIL Open Font License 1.1.
The archive includes the applicable `OFL.txt`, Noto source copyright notices,
and the reproducible font-building scripts. Original source information:
https://github.com/notofonts/latin-greek-cyrillic
