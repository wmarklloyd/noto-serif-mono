# Road to Noto / Google Fonts

A working checklist based on the
[Google Fonts Guide](https://googlefonts.github.io/gf-guide/onboarding.html).
Google Fonts is a curated catalog, so meeting every technical item makes a
family eligible but does not guarantee it will be accepted.

## 1. Repository

- [x] Name and GitHub user filled in (`scripts/personalize.py`).
- [x] Public repository `wmarklloyd/noto-serif-mono` (not a fork).
- [x] GitHub Actions builds the fonts and runs fontspector on every push. The
      `noto-serif-mono-qa` artifact has the report.
- [x] Release v2.502 published with the fonts as `NotoSerifMono.zip`, which the
      README links to.

## 2. Ask first

- [ ] **Submission route.** Propose the family to the Noto project first, in an
      issue at [notofonts/latin-greek-cyrillic](https://github.com/notofonts/latin-greek-cyrillic/issues)
      (the repository for Noto Serif and Noto Sans Mono). Noto is Google's
      trademark and its own project, so a family called "Noto Serif Mono" belongs
      there if they want it. If they take it on, the name, originality and
      variable-font questions below are theirs to settle. Link the repository,
      the specimen and the release, and say you are willing to rename it.
- [ ] **If Noto declines:** open an issue at
      [google/fonts](https://github.com/google/fonts/issues). The guide lists
      originality as a requirement for new families, and this is a derivative of
      Noto Serif, which is already in the catalog, so ask whether it is in scope.
      It would most likely need a name without "Noto".
- [ ] **Contributor License Agreement.** Every copyright holder must sign
      Google's CLA. The Noto Serif copyright already belongs to Google LLC.

## 3. Technical requirements

| Requirement | Status |
| --- | --- |
| OFL 1.1, no Reserved Font Name | ✅ `OFL.txt` |
| Sources in the repo, built with open-source tools | ✅ UFO sources plus `sources/config.yaml`; `make verify` passes in CI |
| Repository layout (project template) | ✅ |
| Copyright string format | ✅ fontspector accepts it. It carries both notices: the Noto Serif notice must stay (OFL). Ask which format they prefer for a derivative |
| License description and URL in the name table | ✅ |
| `fsType` 0 | ✅ |
| Monospace flags (`isFixedPitch`, PANOSE proportion 9, uniform advances) | ✅ |
| `USE_TYPO_METRICS`, typo = hhea, zero line gaps | ✅ |
| Hinting (ttfautohint for static TTFs) | ✅ `scripts/hint.py` reapplies the family alignment fix after autohinting |
| Win ascent/descent cover all glyphs | ✅ `usWinDescent` raised from 293 to 389, so ℊ and the inherited Cyrillic marks are no longer clipped under Windows GDI |
| Vendor ID | ⚠️ `ARBR`, left from the Arbor name; fontspector warns it is unregistered. Change or register it once the route in step 2 is settled (Noto fonts use `GOOG`) |
| GF Latin Core glyph set | ✅ fontspector's glyph-coverage check passes |
| fontspector googlefonts profile, no FAILs | ⚠️ 1 FAIL left: Khanty Tje U+1C89/U+1C8A not drawn (Noto Serif 2.015 has no Tje either); run `make test` |
| Variable font | ⚠️ see below |

### Variable font

Google Fonts publishes many families as variable fonts and may ask for one. Regular and
Bold here are not point-compatible: about a third of the glyphs match, and
most letters do not. That is because each style was adapted separately
from Noto Serif's static fonts. A `wght` variable version would require
re-running the adaptation (`scripts/history/`) on Noto Serif's
variable *sources* (masters from
[notofonts/latin-greek-cyrillic](https://github.com/notofonts/latin-greek-cyrillic))
so that every master gets identical point structures. Raise this in the
issue from step 2: they may accept the static family first, or prefer to
build the variable font in their own pipeline.

## 4. Submission

- [x] Tag a release (v2.502). CI attaches the fonts to the GitHub release as
      `NotoSerifMono.zip`.
- [ ] Update the issue with the release link, the fontspector report and the
      proofs (`make proof`). For Google Fonts, their team packages the family
      with `gftools packager`; you do not open a PR to google/fonts yourself
      unless they ask you to. Noto would bring it into its own repository.
