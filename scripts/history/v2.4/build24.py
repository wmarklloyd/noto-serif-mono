import sys, os
sys.path.insert(0,'/home/claude/tools')
from fontTools.ttLib import TTFont
from refine24 import tune, straighten_H
from arborfix import embolden_x, contours, apply_with_propagation
from sync import sync
import math
SL=math.tan(math.radians(11))
PLAN={
 'Regular':[],
 'Bold':[('D',400,0,140)],
 'Italic':[('D',400,0,84),('E',200,0,84),('F',200,0,84),('H',420,0,84),('K',400,0,84),('U',400,0,84),('B',200,0,84),
           ('N',400,1,80,'bs'),('M',400,1,66,'bs'),('W',350,0,74,'bs'),('m',250,0,86),('w',300,0,78,'bs')],
 'BoldItalic':[('D',400,0,120),('E',200,0,120),('F',200,0,120),('H',420,0,120),('K',400,0,120),('U',400,0,120),('B',200,0,120),('P',200,0,120),('R',200,0,120),
           ('N',400,1,112,'bs'),('M',400,1,95,'bs'),('W',350,0,110,'bs'),('m',250,0,124),('w',300,0,112,'bs')],
}
def build(style,outdir,log):
    t=TTFont('/home/claude/src/ArborMono-%s.ttf'%style)
    sync(t,log)
    if style in ('Regular','Bold'): straighten_H(t,style,log)
    slant=SL if 'Italic' in style else 0.0
    cm=t.getBestCmap()
    for item in PLAN[style]:
        ch,y,which,target=item[:4]; mode=item[4] if len(item)>4 else 'all'
        g=cm[ord(ch)]
        s,ink0,gap0,ink,gaps,floor=tune(t,g,y,target,which,slant,mode=mode)
        cur=max(ink0) if which=='max' else ink0[which]
        if cur>=0.96*target or s<1.5:
            log.append(f"{style} {ch}: left as is ({ink0})"); continue
        G=t['glyf'][g]
        new=embolden_x(list(G.coordinates),G.flags,contours(G),s,slant,mode)
        touched=apply_with_propagation(t,g,new)
        log.append(f"{style} {ch}: +{s:.0f}u x-weight; strokes {ink0}->{ink}; counters {gap0}->{gaps}; {len(touched)-1} related forms")
    if 'Italic' in style:
        harmonize_caps(t,style,slant,log)
    return t

DONE=set('DEFHKUBPRNMWAVXYZ')
def harmonize_caps(t,style,slant,log,y=300):
    up=TTFont(OUT+'/ArborMono-%s.ttf'%('Regular' if style=='Italic' else 'Bold'))
    ucm=up.getBestCmap(); cm=t.getBestCmap()
    from measure import segs
    def first(tt,g):
        sg=segs(tt,g,y); return [b-a for a,b in sg]
    Hu=first(up,ucm[ord('H')])[0]; Hi=first(t,cm[ord('H')])[0]
    cands=list('КΓΠΦΨБГДЖИЙЛПЦЧШЩЪЫЬЮЯФЂЋЏЉЊ')
    done=[]
    for ch in cands:
        if ch in DONE or ord(ch) not in cm or ord(ch) not in ucm: continue
        if ch in 'АВЕНКМТОРСХІЈЅΑΒΕΖΗΙΚΜΝΟΡΤΥΧ': continue  # homoglyphs follow Latin
        g=cm[ord(ch)]
        ru=first(up,ucm[ord(ch)]); ri=first(t,g)
        if not ru or len(ru)!=len(ri) or ru[0]>200: continue
        target=ru[0]/Hu*Hi
        if ri[0]>=0.93*target: continue
        try: s,ink0,gap0,ink,gaps,floor=tune(t,g,y,target,0,slant)
        except IndexError: continue
        if s<3: continue
        G=t['glyf'][g]
        new=embolden_x(list(G.coordinates),G.flags,contours(G),s,slant)
        touched=apply_with_propagation(t,g,new)
        done.append(f"{ch} {ink0[0]}->{ink[0]} (target {target:.0f}, +{len(touched)-1})")
    log.append(f"{style} cap-stem harmonisation vs upright ratios: "+'; '.join(done))

if __name__=='__main__':
    out=sys.argv[1]; os.makedirs(out,exist_ok=True); OUT=out
    for st in ['Regular','Bold','Italic','BoldItalic']:
        log=[]; t=build(st,out,log)
        t.save(f'{out}/ArborMono-{st}.ttf')
        open(f'{out}/log-{st}.txt','w').write('\n'.join(log))
        print('\n'.join(l if len(l)<300 else l[:300]+'…' for l in log))
