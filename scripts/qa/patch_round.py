import os
import sys
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import ttProgram
def patch_xheight_round(t, const=32):
    prog=t['fpgm'].program; asm=[x.split('\t')[0].strip() for x in prog.getAssembly()]
    # locate function 0 body: first 'DUP[ ] PUSHB[ ] 0 NEQ[ ] IF[ ] RCVT[ ] EIF[ ] DUP[ ] DUP[ ] PUSHB[ ] 40 ADD[ ] FLOOR[ ]'
    pat=['DUP[ ]','PUSHB[ ]','0','NEQ[ ]','IF[ ]','RCVT[ ]','EIF[ ]','DUP[ ]','DUP[ ]','PUSHB[ ]','40','ADD[ ]','FLOOR[ ]']
    for i in range(len(asm)-len(pat)):
        if asm[i:i+len(pat)]==pat:
            asm[i+10]=str(const); break
    else: raise RuntimeError('pattern not found')
    p=ttProgram.Program(); p.fromAssembly(asm); t['fpgm'].program=p
    return i
if __name__=='__main__':
    t=TTFont(sys.argv[1]); patch_xheight_round(t,int(sys.argv[3])); t.save(sys.argv[2])
