import subprocess, numpy as np
from fontTools.ttLib import TTFont
_go={}
def gids(path,names):
    if path not in _go: _go[path]={n:i for i,n in enumerate(TTFont(path).getGlyphOrder())}
    return [_go[path][n] for n in names]
def render(path,ppem,names,mode=1,interp=40):
    ids=gids(path,names)
    out=subprocess.run(['/home/claude/ft/ftr',path,str(ppem),str(mode),str(interp)]+[str(i) for i in ids],capture_output=True,text=True).stdout.split('\n')
    res={};i=0;k=0
    while i<len(out):
        l=out[i]
        if l.startswith('G '):
            _,gid,left,top,w,r,adv=l.split(); w,r=int(w),int(r)
            rows=[bytes.fromhex(out[i+1+j]) for j in range(r)]
            a=np.array([list(x) for x in rows],np.uint8) if r and w else np.zeros((0,0),np.uint8)
            res[names[k]]=(int(left),int(top),a); k+=1; i+=1+r
        else: i+=1
    return res
