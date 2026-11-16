# Noto Serif Mono 1.4 Italic and Bold Italic

The old row-dependent width compensation could distort stems and diagonals
as it squeezed slanted outlines into the fixed cell. The new fit retains
more of the source's slant and uses a smaller share of the optical
compensation. H uses a straight-sided fit with added weight at the inner
stem edges. G's bowl and horizontal bar were refitted together. H, I and J
were positioned as a group, with shorter italic I serifs and a J placement
that accounts for the hook below the baseline. The width fit reaches wide
letters, lowercase, and compressed accented Latin, Greek and Cyrillic
forms. Combining mark anchors follow the affine part of the revised fit.

Both character inventories have 2,840 codepoints. The outline comparison
identified changes at 1,415 in Italic and 1,651 in Bold Italic. All advances
and character mappings were preserved. Horizontal ink clearances were
sampled every five units from y=5 to y=710 for each of the 2,704 pairs of
ASCII letters per face, with no new or worsened intersections in those
samples. Lining figure outlines were identical, as were their FreeType
bitmaps at 12, 14, 16, 18, 24 and 32 px/em. Windows DirectWrite was untested.

For the slanted faces, first run make_font for Italic and BoldItalic with
oldstyle=False from SOURCE-v1.4/build_arbor_mono.py. Then run
space_capitals.py with the intermediate font directory and final output
directory as arguments. The upright TTFs in this release are the v1.3 files.
