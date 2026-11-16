import sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
def set_stem_mode(t, gray=None, gdi=None, dw=None):
    """ttfautohint prep writes cvt[3] (stem width mode: -100 natural, 0 quantized, 100 strong):
    first unconditional write = grayscale, then GDI ClearType branch, then DirectWrite ClearType branch."""
    asm=[x.split('\t')[0].strip() for x in t['prep'].program.getAssembly()]
    idx=[i for i in range(len(asm)-3) if asm[i]=='PUSHW[ ]' and asm[i+1]=='3' and asm[i+3]=='WCVTP[ ]']
    assert len(idx)==4, idx
    # order: grayscale default, GDI ClearType, DirectWrite ClearType (two branches)
    for i,v in zip(idx,(gray,gdi,dw,dw)):
        if v is not None: asm[i+2]=str(v)
    p=ttProgram.Program(); p.fromAssembly(asm); t['prep'].program=p
if __name__=='__main__':
    t=TTFont(sys.argv[1]); v=int(sys.argv[3]); set_stem_mode(t,v,v,v); t.save(sys.argv[2])
