#!/usr/bin/env python3
"""Fill in the author name and GitHub user everywhere they appear.

    python3 scripts/personalize.py --name "Jane Doe" --github janedoe

Replaces AUTHOR_NAME and GITHUB_USER in text files (README, OFL,
AUTHORS, the UFO fontinfo.plist files, ...) and in the copyright /
designer / URL name records of fonts/ttf/*.ttf. Run it once, before
the first commit.
"""
import argparse, os, pathlib
from fontTools.ttLib import TTFont

ap = argparse.ArgumentParser()
ap.add_argument('--name', required=True)
ap.add_argument('--github', required=True)
a = ap.parse_args()
root = pathlib.Path(__file__).resolve().parent.parent
subs = {'AUTHOR_NAME': a.name, 'GITHUB_USER': a.github}
skip = {'.git', 'venv', 'history'}
n = 0
for p in root.rglob('*'):
    if any(part in skip for part in p.parts) or not p.is_file() or p.suffix in ('.ttf', '.woff2', '.png', '.glif'):
        continue
    if p.name == 'personalize.py':
        continue
    try:
        s = p.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        continue
    new = s
    for k, v in subs.items():
        new = new.replace(k, v)
    if new != s:
        p.write_text(new, encoding='utf-8'); n += 1; print('updated', p.relative_to(root))
for f in sorted((root / 'fonts' / 'ttf').glob('*.ttf')):
    t = TTFont(f); name = t['name']; changed = False
    for r in name.names:
        s = r.toUnicode(); new = s
        for k, v in subs.items():
            new = new.replace(k, v)
        if new != s:
            r.string = new; changed = True
    if changed:
        t.save(f); n += 1; print('updated', f.relative_to(root))
print(f'{n} files updated')
