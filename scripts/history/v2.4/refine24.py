import sys, json, math, copy
sys.path.insert(0,'/home/claude/tools')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
from arborfix import embolden_x, contours, apply_with_propagation
from measure import segs

def stroke_and_gaps(t,g,y):
    sg=segs(t,g,y); ink=[b-a for a,b in sg if b-a<220]
    gaps=[sg[i+1][0]-sg[i][1] for i in range(len(sg)-1)]
    return ink,gaps

def tune(t,g,y,target,which,slant,gapfrac=0.72,mingap=22,smax=70,mode='all'):
    G=t['glyf'][g]; orig=list(G.coordinates); fl=G.flags; rng=contours(G)
    ink0,gap0=stroke_and_gaps(t,g,y)
    floor=max(mingap, min(gap0)*gapfrac) if gap0 else mingap
    def trial(s):
        G.coordinates=GlyphCoordinates(embolden_x(orig,fl,rng,s,slant,mode))
        ink,gaps=stroke_and_gaps(t,g,y)
        G.coordinates=GlyphCoordinates(orig)
        v=max(ink) if which=='max' else ink[which]
        return v,(min(gaps) if gaps else 999),ink,gaps
    lo,hi=0.0,smax
    for _ in range(14):
        mid=(lo+hi)/2; v,mg,_,gaps=trial(mid)
        if v<target and mg>=floor and len(gaps)==len(gap0): lo=mid
        else: hi=mid
    s=lo; v,mg,ink,gaps=trial(s)
    return s,ink0,gap0,ink,gaps,floor

def run(style, plan, slant, out, log):
    t=TTFont('/home/claude/src/ArborMono-%s.ttf'%style)
    for g,y,which,target in plan:
        s,ink0,gap0,ink,gaps,floor=tune(t,g,y,target,which,slant)
        if s<1.5:
            log.append(f"{style} {g}: unchanged (s={s:.1f}) ink {ink0} gaps {gap0}"); continue
        G=t['glyf'][g]
        new=embolden_x(list(G.coordinates),G.flags,contours(G),s,slant)
        touched=apply_with_propagation(t,g,new)
        log.append(f"{style} {g}: s={s:.1f} ink {ink0}->{ink} gaps {gap0}->{gaps} (+{len(touched)-1} matched forms)")
    return t

def straighten_H(t, style, log):
    G=t['glyf']['H']; c=[list(p) for p in G.coordinates]
    if style=='Regular':
        for i in (17,18,45,46): c[i][0]=187
        for i in (19,20,43,44): c[i][0]=376
    else: # Bold
        for i in (16,17,18,45,46,47): c[i][0]=219
        for i in (19,20,21,42,43,44): c[i][0]=344
    touched=apply_with_propagation(t,'H',[tuple(p) for p in c])
    log.append(f"{style} H: inner stem edges made vertical; +{len(touched)-1} matched forms")
