# Italic capitals in Noto Serif Mono 1.5

G's right edge was tucked in, H was widened across its counter and moved
slightly right, I's stem was lightened, and J's top serif was widened.
The placement changes were reviewed in GHIJ, JIG and HIGH at 12–68 px/em.
The same edits were applied to 79 mapped characters per italic face,
including related accented Latin, Greek and Cyrillic forms.

In a horizontal slice at y=685 in Bold Italic, the gaps in GH, HI and IJ
went from 196, 190 and 203 units to 221, 168 and 190. At y=300 the GH gap
grew from 143 to 168 units. All advances remain fixed, and the sampled
clearances of the 2,704 ASCII letter pairs showed no new or worse overlaps.

The revised outlines were rehinted and tested in Natural, Quantized and
Strong modes. At 10–24 px/em in FreeType grayscale, Natural kept the
difference in average normalized ink coverage between GHIJ and the
digits at 2.2 percentage points in Italic and 1.9 in Bold Italic. The
other modes ranged from 5.0 to 7.2 points. Natural was therefore retained
from 1.4. Figure bitmaps were identical to 1.4 at 12, 14, 16, 18, 24 and
32 px/em. Windows DirectWrite was untested.

Build using the v1.4 source builder to generate the two intermediate
italic faces. Pass their directory, the final directory, and NATURAL to
SOURCE-v1.5/refine.py. The upright TTFs are carried forward.
