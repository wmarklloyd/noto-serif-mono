# Noto Serif Mono 1.3 capital spacing

The alphabet screenshot exposed an imbalance at cap height. H was nearly
cell-wide, I was centered by its short serifs and J was centered by an outline
that included its descender. At the cap line, the left edge of J started
considerably farther right than that outline suggested.

In Regular, H's outside serifs each retreat 14 units. I's top and bottom
serifs each reach 52 units farther. J moves 28 units left and gains reach at
its top serif. The vertical stem widths and all vertical coordinates are
preserved. Bold uses less extension around I. The italic adjustments follow
the sloped stems and use smaller extensions to limit overhang.

At 100 px/em, Regular's cap-line clearances measured on a horizontal slice
at 70 px above the baseline were:

| Pair | 1.2 | 1.3 |
|---|---:|---:|
| GH | 13 px | 14 px |
| HI | 17 px | 12 px |
| IJ | 29 px | 17 px |
| JK | 13 px | 12 px |

The inventory covers all 2,840 mapped codepoints per style, recording both
sidebearings and advance before and after. The outline check also covers
unencoded glyphs. The revisions extend to Latin accents and corresponding
Greek and Cyrillic forms, including Eta, Iota, En, Ukrainian I and Yi, Je
and Palochka. Polytonic Greek side accents retain their location and shape.
The number of distinct changed outlines is 65 Regular, 64 Bold, 71 Italic
and 71 Bold Italic. Larger sidebearings on shapes such as Saltillo and the
vertical bar are consistent with their narrow silhouette. Zero-width marks,
control characters and spacing characters follow their own metrics.

Every advance and cmap entry was checked against 1.2. Printable ASCII still
uses 563 units per cell. FreeType grayscale tests produced identical glyph
bitmaps and offsets for ASCII lowercase and figures at 12, 14, 16, 18 and
24 px/em in all four styles. The included side-by-side proof uses hinted
rasterization at 14, 18, 24 and 34 px/em. Windows DirectWrite rendering was
not tested.
