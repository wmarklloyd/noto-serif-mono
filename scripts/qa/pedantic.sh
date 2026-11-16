f=$1; n=$(python3 -c "from fontTools.ttLib import TTFont;print(len(TTFont('$f').getGlyphOrder()))")
ids=$(seq 0 $((n-1)) | tr '\n' ' ')
for iv in 35 40; do for p in $(seq 7 72); do
  "$(dirname "$0")"/ftr $f $p 15 $iv $ids | grep ERR | sed "s/^/$iv $p /"
  "$(dirname "$0")"/ftr $f $p 16 $iv $ids | grep ERR | sed "s/^/mono$iv $p /"
done; done
