# Road to Google Fonts

A working checklist based on the
[Google Fonts Guide](https://googlefonts.github.io/gf-guide/onboarding.html).
Google Fonts is a curated catalog, so meeting every technical item makes a
family eligible but does not guarantee it will be accepted.

## 1. Before the first push

- [ ] Fill in your name and GitHub user:
      `python3 scripts/personalize.py --name "Your Name" --github your-user`.
      This replaces `Mark Lloyd` and `wmarklloyd` in the README, OFL,
      AUTHORS, sources and fonts.
- [ ] Create a **public** repository named `noto-serif-mono`. Google Fonts does
      not accept contributions from forks.
- [ ] Push. GitHub Actions builds the fonts and runs FontBakery. Download
      the `noto-serif-mono-qa` artifact for the report.

## 2. Ask Google Fonts early

- [ ] **Originality.** The guide lists originality as a requirement for new
      families. Noto Serif Mono is a derivative of Noto Serif, which is already
      in the catalog. Before investing in the remaining items, open an issue
      at [google/fonts](https://github.com/google/fonts/issues) titled
      "Add Noto Serif Mono". Describe the project and ask whether a monospaced
      adaptation of Noto Serif is in scope. Link the repository and specimen.
- [ ] **Name.** A quick search found no existing "Noto Serif Mono" (Arboria is a
      different, commercial family). Do a trademark search before
      committing to the name.
- [ ] **Contributor License Agreement.** Every copyright holder must sign
      Google's CLA. The Noto Serif copyright already belongs to Google LLC.

## 3. Technical requirements

| Requirement | Status |
| --- | --- |
| OFL 1.1, no Reserved Font Name | ✅ `OFL.txt` |
| Sources in the repo, built with open-source tools | ✅ UFO sources plus `sources/config.yaml`. ⚠️ Run `make build` once and check `make verify` |
| Repository layout (project template) | ✅ |
| Copyright string format | ⚠️ Google Fonts expects `Copyright YYYY The X Project Authors (URL)`. The Noto Serif notice must stay (OFL), so the string carries both notices. If FontBakery objects, ask the onboarding team which format they want for derivatives |
| License description and URL in the name table | ✅ |
| `fsType` 0 | ✅ |
| Monospace flags (`isFixedPitch`, PANOSE proportion 9, uniform advances) | ✅ |
| `USE_TYPO_METRICS`, typo = hhea, zero line gaps | ✅ |
| Hinting (ttfautohint for static TTFs) | ✅ `scripts/hint.py` reapplies the family alignment fix after autohinting |
| Win ascent/descent cover all glyphs | ❌ see below |
| Vendor ID | ⚠️ `NONE`. Register one with Microsoft or leave it as is |
| GF Latin Core glyph set | ⚠️ likely complete; confirm with FontBakery's glyph-coverage check |
| FontBakery googlefonts profile, no FAILs | ⚠️ run `make test` |
| Variable font | ⚠️ see below |

### Win descent (a FontBakery FAIL in the universal checks)

`usWinDescent` is 293 units, but 7 inherited glyphs reach lower:
ℊ (−389), U+A670–A672, U+0489, U+2E10 and U+2E11. Windows GDI clips
them. There are two options:

1. Raise `openTypeOS2WinDescent` to 389 in all four UFOs. This is the usual
   choice. Line spacing in older GDI applications grows by about 1.5 px at
   16 px. DirectWrite, macOS and browsers use the typo metrics, so they are
   unaffected.
2. Redraw or remove those glyphs so they fit within −293.

### Variable font

Google Fonts publishes many families as variable fonts and may ask for one. Regular and
Bold here are not point-compatible: about a third of the glyphs match, and
most letters do not. That is because each style was adapted separately
from Noto Serif's static fonts. A `wght` variable version would require
re-running the Arbor adaptation (`scripts/history/`) on Noto Serif's
variable *sources* (masters from
[notofonts/latin-greek-cyrillic](https://github.com/notofonts/latin-greek-cyrillic))
so that every master gets identical point structures. Raise this with the
onboarding team in the issue from step 2: they may accept the static
family first.

## 4. Submission

- [ ] Tag a release (`git tag v2.501 && git push --tags`). CI attaches the
      fonts to a GitHub release.
- [ ] Update the issue with the release link, the FontBakery report and the
      proofs (`make proof`). The Google Fonts team packages the family with
      `gftools packager`; you do not open a PR to google/fonts yourself
      unless they ask you to.
