import os
"""Approximation of key FontBakery (opentype + universal profile) checks using fontTools."""
import sys, glob, re, unicodedata, collections
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
R=[]
def rep(status,check,font,msg=''): R.append((status,check,font,msg))
fonts={p.split('/')[-1]:TTFont(p) for p in sorted(glob.glob(sys.argv[1]+'/NotoSerifMono-*.ttf'))}
STY={'Regular':(400,0b1000000,0,0),'Bold':(700,0b100000,1,0),'Italic':(400,1,2,1),'BoldItalic':(700,0b100001,3,1)}
for fn,t in fonts.items():
    sty=fn[len('NotoSerifMono-'):-4]; n=t['name']; os2=t['OS/2']; head=t['head']; hhea=t['hhea']; post=t['post']
    cm=t.getBestCmap(); hm=t['hmtx'].metrics; go=t.getGlyphOrder(); glyf=t['glyf']
    gn=lambda i:(n.getName(i,3,1,0x409) or n.getName(i,1,0,0)); s=lambda i:str(gn(i)) if gn(i) else None
    # required tables
    req={'cmap','head','hhea','hmtx','maxp','name','OS/2','post','glyf','loca'}
    miss=req-set(t.keys()); rep('FAIL' if miss else 'PASS','opentype/required_tables',fn,str(miss) if miss else '')
    for tag in ('DSIG','hdmx','VDMX','LTSH','prop','TTFA'):
        if tag in t: rep('WARN','universal/unwanted_tables',fn,tag)
    # naming
    w,fs,mac,it=STY[sty]
    rep('PASS' if os2.usWeightClass==w else 'FAIL','opentype/weight_class',fn,str(os2.usWeightClass))
    sel=os2.fsSelection&0b1100001
    rep('PASS' if sel==fs else 'FAIL','opentype/fsselection',fn,bin(os2.fsSelection))
    rep('PASS' if head.macStyle&3==mac else 'FAIL','opentype/mac_style',fn,str(head.macStyle))
    rep('PASS' if os2.fsSelection&(1<<7) else 'INFO','opentype/use_typo_metrics',fn,'USE_TYPO_METRICS '+('set' if os2.fsSelection&(1<<7) else 'clear'))
    exp2={'Regular':'Regular','Bold':'Bold','Italic':'Italic','BoldItalic':'Bold Italic'}[sty]
    rep('PASS' if s(2)==exp2 else 'FAIL','opentype/name/match_familyname_fullfont + style',fn,f'nameID2={s(2)!r}')
    rep('PASS' if s(4)==f'Noto Serif Mono {exp2}' else 'FAIL','opentype/family_naming_recommendations (full name)',fn,repr(s(4)))
    rep('PASS' if s(6)==f'NotoSerifMono-{sty}' else 'FAIL','opentype/postscript_name',fn,repr(s(6)))
    if 16 in {r.nameID for r in n.names}: rep('WARN','opentype/name/no_typographic_names_in_RIBBI',fn,'ID16/17 present')
    bad=[(r.nameID,r.platformID) for r in n.names if r.toUnicode()!=r.toUnicode().strip()]
    rep('FAIL' if bad else 'PASS','universal/name/trailing_spaces',fn,str(bad) if bad else '')
    macn=[r for r in n.names if r.platformID==1]
    if macn: rep('WARN','googlefonts/name/no_mac_entries',fn,f'{len(macn)} Mac (platform 1) name records')
    v5=s(5) or ''; m=re.match(r'Version (\d+\.\d+)',v5)
    rep('PASS' if m and abs(float(m.group(1))-head.fontRevision)<0.001 else 'FAIL','opentype/font_version',fn,f'name5 {v5[:13]!r} head {head.fontRevision:.3f}')
    rep('PASS' if s(13) and 'Open Font License' in s(13) else 'FAIL','googlefonts/name/license',fn,repr((s(13) or '')[:40]))
    rep('PASS' if s(14)=='https://openfontlicense.org' else 'WARN','googlefonts/name/license_url',fn,repr(s(14)))
    rep('PASS' if s(0) and re.match(r'Copyright \d{4} The .* Project Authors \(.*\)',s(0)) else 'WARN','googlefonts/metadata/valid_copyright (GF format)',fn,repr(s(0)))
    rep('PASS' if os2.fsType==0 else 'FAIL','universal/fstype',fn,str(os2.fsType))
    rep('PASS' if os2.achVendID not in ('GOOG',) else 'WARN','googlefonts/vendor_id',fn,repr(os2.achVendID))
    # italic
    if it:
        rep('PASS' if -30<post.italicAngle<0 else 'FAIL','opentype/italic_angle',fn,str(post.italicAngle))
        import math
        slope=math.degrees(math.atan2(hhea.caretSlopeRun,hhea.caretSlopeRise))
        rep('PASS' if abs(slope+post.italicAngle)<0.5 else 'WARN','opentype/caret_slope',fn,f'{slope:.2f}° vs {-post.italicAngle}')
    else:
        rep('PASS' if post.italicAngle==0 and hhea.caretSlopeRun==0 else 'FAIL','opentype/italic_angle',fn,str(post.italicAngle))
    # monospace
    mapped=set(cm.values()); widths=collections.Counter(hm[g][0] for g in mapped)
    nonmono=[g for g in mapped if hm[g][0] not in (0,563)]
    rep('PASS' if post.isFixedPitch and os2.panose.bProportion==9 and hhea.advanceWidthMax==563 and not nonmono else 'FAIL','googlefonts/monospace',fn,
        f'isFixedPitch={post.isFixedPitch} panose.prop={os2.panose.bProportion} advanceWidthMax={hhea.advanceWidthMax} non-mono mapped={len(nonmono)}')
    allw=collections.Counter(hm[g][0] for g in go)
    rep('PASS' if set(allw)<= {0,563} else 'WARN','googlefonts/monospace (all glyphs)',fn,str(dict(allw)))
    zero_nonmark=[g for g in mapped if hm[g][0]==0 and glyf[g].numberOfContours!=0 and not any(unicodedata.category(chr(c)).startswith('M') for c,gg in cm.items() if gg==g)]
    rep('WARN' if zero_nonmark else 'PASS','universal/zero-width non-mark glyphs',fn,str(zero_nonmark[:10]))
    xavg=round(sum(hm[g][0] for g in go if hm[g][0])/len([g for g in go if hm[g][0]]))
    rep('PASS' if abs(os2.xAvgCharWidth-xavg)<=1 else 'WARN','opentype/xavgcharwidth',fn,f'{os2.xAvgCharWidth} vs computed {xavg}')
    # whitespace
    for cp,name in ((0x20,'space'),(0xA0,'nbsp')):
        g=cm.get(cp); rep('PASS' if g and hm[g][0]==563 and glyf[g].numberOfContours==0 else 'FAIL',f'universal/whitespace_glyphs ({name})',fn,str(g))
    rep('PASS' if go[0]=='.notdef' and glyf['.notdef'].numberOfContours!=0 else 'WARN','universal/mandatory_glyphs (.notdef)',fn,go[0])
    ws=[cp for cp,g in cm.items() if unicodedata.category(chr(cp)) in ('Zs',) and glyf[g].numberOfContours!=0]
    rep('FAIL' if ws else 'PASS','universal/whitespace_ink',fn,str([hex(c) for c in ws]))
    # metrics
    ymax=max((glyf[g].yMax for g in mapped if glyf[g].numberOfContours), default=0)
    ymin=min((glyf[g].yMin for g in mapped if glyf[g].numberOfContours), default=0)
    rep('PASS' if os2.usWinAscent>=ymax and os2.usWinDescent>=-ymin else 'FAIL','universal/family/win_ascent_and_descent',fn,f'win {os2.usWinAscent}/{os2.usWinDescent}; glyph yMax {ymax} yMin {ymin}')
    rep('PASS' if hhea.lineGap==0 and os2.sTypoLineGap==0 else 'WARN','googlefonts/vertical_metrics (line gaps)',fn,f'{hhea.lineGap},{os2.sTypoLineGap}')
    rep('PASS' if (hhea.ascent,hhea.descent)==(os2.sTypoAscender,os2.sTypoDescender) else 'WARN','universal/linegaps & hhea==typo',fn,'')
    rep('PASS' if head.unitsPerEm in (1000,2048) or 16<=head.unitsPerEm<=16384 else 'FAIL','opentype/unitsperem',fn,str(head.unitsPerEm))
    # hinting
    if 'fpgm' in t: rep('PASS' if head.flags&8 else 'FAIL','googlefonts/integer_ppem_if_hinted',fn,bin(head.flags))
    rep('PASS' if 'gasp' in t else 'WARN','googlefonts/gasp',fn,str(t['gasp'].gaspRange if 'gasp' in t else None))
    if 'gasp' in t and t['gasp'].gaspRange.get(0xFFFF)!=15: rep('WARN','googlefonts/gasp (65535 should be 15)',fn,'')
    # glyph names / cmap
    names=go; dup=[k for k,v in collections.Counter(names).items() if v>1]
    rep('FAIL' if dup else 'PASS','universal/unique_glyphnames',fn,str(dup[:5]))
    badn=[g for g in names if not re.match(r'^[A-Za-z_.][A-Za-z0-9_.]*$',g) or len(g)>63]
    rep('WARN' if badn else 'PASS','universal/valid_glyphnames',fn,str(badn[:5]))
    rep('PASS' if post.formatType==2 else 'INFO','opentype/post_table_version',fn,str(post.formatType))
    # unreachable glyphs
    reach=set(mapped)|{'.notdef'}
    for tag in ('GSUB',):
        if tag in t:
            for lk in t[tag].table.LookupList.Lookup:
                for st in lk.SubTable:
                    st=getattr(st,'ExtSubTable',st)
                    if hasattr(st,'mapping'): reach|=set(st.mapping.values())
                    if hasattr(st,'alternates'): [reach.update(v) for v in st.alternates.values()]
                    if hasattr(st,'ligatures'): [reach.update(l.LigGlyph for l in ls) for ls in st.ligatures.values()]
                    if hasattr(st,'Coverage') and hasattr(st,'Sequence'): [reach.update(sq.Substitute) for sq in st.Sequence]
    unreach=[g for g in go if g not in reach and glyf[g].numberOfContours!=0]
    rep('WARN' if unreach else 'PASS','universal/unreachable_glyphs',fn,f'{len(unreach)} e.g. {unreach[:8]}')
    # GDEF marks
    gdef=t['GDEF'].table.GlyphClassDef.classDefs if 'GDEF' in t and t['GDEF'].table.GlyphClassDef else {}
    marks=[g for cp,g in cm.items() if unicodedata.category(chr(cp))=='Mn']
    notmark=[g for g in marks if gdef.get(g)!=3]
    rep('WARN' if notmark else 'PASS','opentype/gdef_mark_chars',fn,f'{len(notmark)} {notmark[:6]}')
    nonmarks_as_mark=[g for cp,g in cm.items() if gdef.get(g)==3 and not unicodedata.category(chr(cp)).startswith('M')]
    rep('WARN' if nonmarks_as_mark else 'PASS','opentype/gdef_non_mark_chars',fn,str(nonmarks_as_mark[:6]))
    wide_marks=[g for g in marks if hm[g][0]!=0]
    rep('WARN' if wide_marks else 'PASS','universal/mark_chars_zero_width',fn,str(wide_marks[:6]))
    # empty features
    for tag in ('GSUB','GPOS'):
        if tag in t:
            empty=sorted({fr.FeatureTag for fr in t[tag].table.FeatureList.FeatureRecord if not fr.Feature.LookupListIndex})
            if empty: rep('WARN',f'opentype/{tag.lower()} empty features',fn,str(empty))
            lk=t[tag].table.LookupList.Lookup
            emptyl=[i for i,l in enumerate(lk) if not l.SubTable]
            if emptyl: rep('WARN',f'opentype/{tag.lower()} empty lookups',fn,str(emptyl))
    if 'GPOS' in t and 'kern' not in {fr.FeatureTag for fr in t['GPOS'].table.FeatureList.FeatureRecord}: rep('INFO','opentype/kern_table','fn','no kern')
    # OS/2 ranges sanity
    rep('PASS' if os2.ulCodePageRange1 or os2.ulCodePageRange2 else 'FAIL','opentype/code_pages',fn,hex(os2.ulCodePageRange1))
    rep('PASS' if os2.usFirstCharIndex==min(cm) and os2.usLastCharIndex==min(max(cm),0xFFFF) else 'WARN','opentype/OS2 first/last char',fn,f'{os2.usFirstCharIndex:#x}-{os2.usLastCharIndex:#x} vs {min(cm):#x}-{max(cm):#x}')
    # outline sanity
    short=0; openc=0
    for g in go:
        G=glyf[g]
        if G.numberOfContours>0:
            c=G.coordinates; ends=G.endPtsOfContours; s0=0
            for e in ends:
                if e-s0<2: openc+=1
                s0=e+1
    rep('WARN' if openc else 'PASS','universal/outline: degenerate contours (<3 pts)',fn,str(openc))
# family-wide consistency
vals=lambda f:{k:f(t) for k,t in fonts.items()}
for lab,f in [('vertical metrics',lambda t:(t['hhea'].ascent,t['hhea'].descent,t['OS/2'].usWinAscent,t['OS/2'].usWinDescent,t['OS/2'].sTypoAscender,t['OS/2'].sTypoDescender)),
              ('version',lambda t:round(t['head'].fontRevision,3)),('family name',lambda t:str(t['name'].getName(1,3,1,0x409))),
              ('vendor',lambda t:t['OS/2'].achVendID),('unitsPerEm',lambda t:t['head'].unitsPerEm),('underline',lambda t:(t['post'].underlinePosition,t['post'].underlineThickness)),
              ('panose family',lambda t:t['OS/2'].panose.bFamilyType),('cmap coverage',lambda t:len(t.getBestCmap()))]:
    v=vals(f); rep('PASS' if len(set(v.values()))==1 else 'FAIL',f'universal/family consistency: {lab}','family',str(set(v.values())))
order={'FAIL':0,'WARN':1,'INFO':2,'PASS':3}
cnt=collections.Counter(s for s,*_ in R)
print('SUMMARY',dict(cnt))
for st in ('FAIL','WARN','INFO'):
    agg=collections.defaultdict(list)
    for s,c,f,m in R:
        if s==st: agg[c].append((f,m))
    for c,v in agg.items():
        print(f"{st:4s} {c}: "+'; '.join(f"{f.replace('NotoSerifMono-','').replace('.ttf','')}: {m}" for f,m in v)[:400])
