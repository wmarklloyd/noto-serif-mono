"""Undo fix_smallcaps.py's first-run feature edits in the italics, where it assumed the
upright lookup numbers (there c2sc is L37 and smcp is L38, L36 is onum)."""
import re
import ufoLib2

ROOT = r"C:\Users\Mark\arbor-mono\sources"
BACKUP = r"C:\Users\Mark\arbor-mono-backup\sources-2.501"
for style in ["Italic", "BoldItalic"]:
    f = ufoLib2.Font.open(f"{ROOT}/ArborMono-{style}.ufo")
    old = ufoLib2.Font.open(f"{BACKUP}/ArborMono-{style}.ufo")
    new = {g.name for g in f if g.name.endswith(".sc") and g.name not in old}
    oldlines = set(old.features.text.split("\n"))
    out, dropped = [], 0
    for line in f.features.text.split("\n"):
        m = re.match(r"\s*sub (\S+) by (\S+);$", line)
        if m and line not in oldlines and (m.group(2) in new or m.group(1) in ("dotlessi", "longs")):
            dropped += 1
            continue
        out.append(line)
    fea = "\n".join(out)
    fea = re.sub(r"\n\nlookup smcpTRK \{.*?\} smcpTRK;", "", fea, flags=re.S)
    f.features.text = fea
    f.save(f"{ROOT}/ArborMono-{style}.ufo", overwrite=True)
    print(style, "dropped", dropped, "smcpTRK left:", "smcpTRK" in fea)
