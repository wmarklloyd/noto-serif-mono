# QA tools

These scripts render the fonts through FreeType directly. They check
the hinting and the outlines in ways fontspector does not. Run them from
the repository root. First compile the renderer once (it needs the
FreeType development headers):

    gcc -O2 -o scripts/qa/ftr scripts/qa/ftr.c $(pkg-config --cflags --libs freetype2)

Without a C compiler the scripts fall back to `ftr_py.py`, the same renderer written
against freetype-py (slower, same output). `defects.py` uses scikit-image when it is
installed and a pure-Python flood fill otherwise.

| Script | What it checks |
| --- | --- |
| `pedantic.sh FONT` | Runs every glyph's hint program at 7–72 ppem (v35, v40 and mono) in FreeType's pedantic mode, then lists the bytecode errors. The output should be empty |
| `align.py STYLE…` | Hinted x-height, cap height, ascender, figure height and baseline per size: are they consistent within the face? |
| `stale.py STYLE` | Glyphs whose hinted top or bottom moves 2 px or more from the outline (signs of stale hints) |
| `defects.py STYLE…` | Counters that close and parts that disappear under hinting, gray and mono |
| `clip.py FONT` | Glyphs that Windows GDI clips at usWinAscent/usWinDescent |
| `bars.py STYLE [FONT]` | Thickness and crispness of horizontal strokes per size |
| `textimg.py` | Renders hinted text sheets for visual comparison |
| `patch_mode.py IN OUT MODE` | Experiment: switch ttfautohint's stem-width mode (-100 natural, 0 quantized, 100 strong) |
| `patch_round.py IN OUT CONST` | Experiment: change ttfautohint's x-height rounding threshold (default 40/64) |
| `ftr_py.py FONT PPEM MODE INTERP GID…` | Pure-Python stand-in for the compiled `ftr` renderer |
| `../make_hint_controls.py FONT…` | Not a check: regenerates the ttfautohint control files in `sources/hinting/` and reports any accent still touching its letter after hinting. Rerun it whenever outlines change, before `scripts/hint.py` |
| `check_family.py DIR` | About 45 FontBakery/fontspector-style metadata checks in pure fontTools, for use when fontspector is unavailable |
| `contact_sheet.py FONT OUT.png` | Not a check: every glyph in its cell, with code point or name, for reviewing spacing across the whole font |
| `specimen.py [DIR] [OUT.png]` | Not a check: redraws `documentation/specimen.png`, the README image, from the built fonts. Rerun it after a rename or a change to the cell |

`STYLE` is one of Regular, Bold, Italic or BoldItalic, and refers to `fonts/ttf/NotoSerifMono-STYLE.ttf`.
