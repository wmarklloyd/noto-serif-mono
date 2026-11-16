"""Arbor Mono 2.5 hinting fixes applied to the 2.4 TTFs."""
import sys
sys.path.insert(0,'/home/claude/ft'); sys.path.insert(0,'/home/claude/tools')
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
from harmonize_cvt import harmonize
from finalize import finalize
SRC, OUT = sys.argv[1], sys.argv[2]
BROKEN=['uni1ABF','uni1AC0']   # glyph programs raise FT Invalid_Reference (0x86) at 7-32 ppem
ref=list(TTFont(f'{SRC}/ArborMono-Regular.ttf')['cvt '].values)
for S in ['Regular','Bold','Italic','BoldItalic']:
    t=TTFont(f'{SRC}/ArborMono-{S}.ttf'); log=[]
    t['head'].flags |= 1<<3; log.append('head.flags bit 3 (integer ppem) set')
    for n in BROKEN:
        if n in t['glyf'].glyphs:
            p=ttProgram.Program(); p.fromBytecode(b''); t['glyf'][n].program=p
    log.append('instructions removed from '+', '.join(BROKEN))
    ch=harmonize(t,ref)
    if ch: log.append(f'x-height alignment CVT entries set to Regular values: {ch}')
    t.save(f'{OUT}/ArborMono-{S}.ttf'); finalize(f'{OUT}/ArborMono-{S}.ttf',S,'2.500')
    print(S,'; '.join(log))
