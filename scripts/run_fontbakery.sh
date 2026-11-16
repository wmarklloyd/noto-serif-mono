#!/bin/sh
# Run FontBakery on your own machine (after `pip install fontbakery[googlefonts]`).
#   sh scripts/run_fontbakery.sh            # googlefonts profile (what Google Fonts uses)
#   sh scripts/run_fontbakery.sh universal  # vendor-neutral profile
set -e
PROFILE=${1:-googlefonts}
mkdir -p out/fontbakery
fontbakery check-$PROFILE -l WARN --full-lists --succinct \
  --html out/fontbakery/report-$PROFILE.html \
  --ghmarkdown out/fontbakery/report-$PROFILE.md \
  fonts/ttf/*.ttf
echo "Reports: out/fontbakery/report-$PROFILE.html and .md"
