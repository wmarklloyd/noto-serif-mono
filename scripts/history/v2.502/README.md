# 2.502 FontBakery fix pass

One-off scripts that edited the UFO sources in place, run in this order. They are kept for
provenance and are not part of the build. They use hard-coded `C:\Users\Mark\arbor-mono` paths.

| Script | What it changed |
| --- | --- |
| `fix_ufos.py` | WinDescent 389, vendor ID `ARBR`; added U+2212 MINUS and U+2183; mark category for six enclosing/combining marks; top anchor on U+A78D; removed U+00AD |
| `fix_ufos2.py` | `center` anchor on U+25CC; base category for U+A78D, U+2212, U+2183; 1-unit anchor nudges (Bold `eng`, Bold Italic U+026F); added U+A7CB from U+0264 |
| `fix_ufos3.py` | top/bottom anchors on U+A7AE, U+A7B6, U+A7B7 |
| `fix_anchors.py` | top/bottom anchors on every Latin/Greek/Cyrillic letter that had none (199 per upright, 235 per italic), placed over the ink at each edge |
| `fix_anchors2.py` | moved those anchors onto the hand-placed convention: centred on the letter body along the italic slant, except over ascenders and descenders; short tails anchor at the baseline. Takes the path of the pre-2.502 sources |
| `audit_anchors.py` | reports anchors added by this pass that are off-centre without an ascender or descender to justify it. Takes the path of the pre-2.502 sources |
| `fix_smallcaps.py` | small caps (`smcp`/`c2sc`) for the 165 lowercase letters that had none: 49 drawn from the capital at 0.87 x 0.8, the accented ones assembled from the composite's accents over the `.sc` base (Vietnamese stacks kept below WinAscent), component builds only for horn letters. Also completes the soft-dotted `ccmp` classes from FontBakery's sets and adds Turkish, Azerbaijani and Crimean Tatar dotted-i small caps. Run with `--redo-components`; `REDO='*'` rebuilds every glyph it generated |
| `repair_italic_fea.py` | removes feature lines an early `fix_smallcaps.py` run wrote into the wrong lookups of the italic sources (their lookup numbering differs from the uprights) |
| `add_circled.py` | adds U+24B6 Ⓐ and U+24D0 ⓐ: the copyright sign's oval with the style's A or a scaled into it (at most the copyright C's 0.64 ratio, shrunk until it keeps 40 units clear of the inner oval, lifted up to 30 units where the oval is wider). Re-running replaces both glyphs |
| `inkcmp.py` | audit, no edits: for every precomposed letter, compares the accent's ink centre with what the base plus a separate combining mark produces through GPOS. Run `inkcmp.py out.tsv` from the repository root on the built TTFs; `FEAT=smcp` for small caps. Uses `sampler.py` |
| `fit.py` | fits `difference = base correction + mark correction` (iterative medians) to `ink.tsv` and writes `fit.json` |
| `apply_anchors.py` | applies `fit.json`: moves base `top`/`bottom` anchors and mark `_top`/`_bottom` anchors (grave and double grave about +40, double acute about -32, comma below +9 to +23); gives the ogonek its own `ogonek`/`_ogonek` anchor at the old bottom position so it does not move with the other below-marks |
| `fix_sc_marks.py` | small-cap letters with misplaced accents: centres the below-marks of ṳ ṵ ụ ạ ậ ặ and the above-marks of ǩ ȟ ḣ (Regular, Bold); lifts the ḋ dot out of the D (all styles) |
| `fix_sc_markglyphs.py` | the small-cap combining marks (`acutecomb.sc` and 11 others) were 563-unit spacing glyphs; makes them zero-width marks aligned with the plain marks and copies their anchors. Reads the pre-anchor-fit sources, kept in `C:\Users\Mark\arbor-mono-backup\sources-pre-anchor-fit` |
| `centre_sc_marks.py` | centres `acutecomb.sc`, `gravecomb.sc` and `uni030B.sc` on their `_top` anchor. Run as `centre_sc_marks.py Regular Bold` (the italics measured worse) |

The pre-2.502 sources were kept outside the repository, in `C:\Users\Mark\arbor-mono-backup\sources-2.501`.
