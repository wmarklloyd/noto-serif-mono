#!/bin/sh
# Run fontspector on your own machine (`cargo install --locked fontspector`;
# set FONTSPECTOR to use a release binary instead).
#   sh scripts/run_fontspector.sh            # googlefonts profile (what Google Fonts uses)
#   sh scripts/run_fontspector.sh universal  # vendor-neutral profile
set -e
PROFILE=${1:-googlefonts}
FONTSPECTOR=${FONTSPECTOR:-fontspector}
# Check a copy in out/fontspector/notoserifmono/: google/fonts keeps the family in
# ofl/notoserifmono, and dirname_matches_nameid_1 expects that directory name.
rm -rf out/fontspector/notoserifmono && mkdir -p out/fontspector/notoserifmono
cp fonts/ttf/*.ttf out/fontspector/notoserifmono/
"$FONTSPECTOR" -p $PROFILE -l warn --full-lists --succinct \
  --html out/fontspector/report-$PROFILE.html \
  --ghmarkdown out/fontspector/report-$PROFILE.md \
  out/fontspector/notoserifmono/*.ttf || status=$?
echo "Reports: out/fontspector/report-$PROFILE.html and .md"
exit ${status:-0}
