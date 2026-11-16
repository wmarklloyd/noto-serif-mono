"""Arbor Mono 2.5.1: FontBakery-style metadata cleanups (no outline/metric/hint changes)."""
import sys
from fontTools.ttLib import TTFont
def drop_empty_features(t, tag):
    tbl=t[tag].table; fl=tbl.FeatureList.FeatureRecord
    keep=[i for i,fr in enumerate(fl) if fr.Feature.LookupListIndex]
    if len(keep)==len(fl): return []
    removed=[fl[i].FeatureTag for i in range(len(fl)) if i not in keep]
    remap={old:new for new,old in enumerate(keep)}
    tbl.FeatureList.FeatureRecord=[fl[i] for i in keep]; tbl.FeatureList.FeatureCount=len(keep)
    for sr in tbl.ScriptList.ScriptRecord:
        lss=[sr.Script.DefaultLangSys]+[l.LangSys for l in sr.Script.LangSysRecord]
        for ls in lss:
            if ls is None: continue
            ls.FeatureIndex=[remap[i] for i in ls.FeatureIndex if i in remap]; ls.FeatureCount=len(ls.FeatureIndex)
            if ls.ReqFeatureIndex!=0xFFFF: ls.ReqFeatureIndex=remap.get(ls.ReqFeatureIndex,0xFFFF)
    return removed
SRC,OUT=sys.argv[1],sys.argv[2]
for S in ['Regular','Bold','Italic','BoldItalic']:
    t=TTFont(f'{SRC}/ArborMono-{S}.ttf'); log=[]
    o=t['OS/2']
    assert (o.sTypoAscender,o.sTypoDescender,o.sTypoLineGap)==(t['hhea'].ascent,t['hhea'].descent,t['hhea'].lineGap)
    o.fsSelection|=1<<7; log.append('USE_TYPO_METRICS on (typo == hhea, so line spacing is unchanged)')
    n=t['name']; n.names=[r for r in n.names if r.platformID!=1]; log.append('Mac name records removed')
    n.setName('https://openfontlicense.org',14,3,1,0x409); log.append('license URL')
    for tag in ('GSUB','GPOS'):
        r=drop_empty_features(t,tag)
        if r: log.append(f'{tag} empty features removed: {r}')
    t.save(f'{OUT}/ArborMono-{S}.ttf'); print(S,'; '.join(log))
