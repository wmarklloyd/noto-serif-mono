#!/usr/bin/env python3
"""Convert Noto Serif Mono TTF binaries into UFO3 sources.

This is how the initial sources in sources/ were created from the
2.501 binaries (which were themselves produced by the scripted Noto
Serif -> Noto Serif Mono pipeline, see scripts/history/). Outlines stay
quadratic (TrueType) so a fontmake TTF build reproduces them exactly.

  * glyph outlines, advance widths, unicodes, glyph order
  * fontinfo (names, vertical metrics, OS/2 values, version)
  * GDEF glyph classes  -> lib public.openTypeCategories
  * GPOS mark/mkmk/mark-to-ligature -> glyph anchors
    (top/bottom/topright/center, _top..., top_1...) so ufo2ft regenerates
    the mark and mkmk features at build time
  * GSUB                -> features.fea (lookup-by-lookup decompilation)

usage: python3 scripts/ttf2ufo.py FONT.ttf OUT.ufo
"""
import sys, os, shutil, collections
from fontTools.ttLib import TTFont
from fontTools.ufoLib import UFOWriter
from fontTools.ufoLib.glifLib import GlyphSet
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.pointPen import ReverseContourPointPen

ANCHOR_NAMES = ['bottom', 'top', 'topright', 'center']  # GPOS mark classes 0..3

class Obj: pass

# Project metadata written into the sources. Placeholders are replaced by scripts/personalize.py.
PROJECT = {
    'copyright': 'Copyright 2015 Google LLC. Copyright 2026 The Noto Serif Mono Project Authors (https://github.com/wmarklloyd/noto-serif-mono)',
    'designer': 'Monotype Design Team (Noto Serif); Noto Serif Mono by Mark Lloyd',
    'manufacturer': 'The Noto Serif Mono Project Authors',
    'url': 'https://github.com/wmarklloyd/noto-serif-mono',
    'description': 'Noto Serif Mono is a monospaced adaptation of Noto Serif for code and text.',
}

# ---------------------------------------------------------------- fontinfo
def fontinfo(t):
    n = t['name']; os2 = t['OS/2']; hh = t['hhea']; post = t['post']; head = t['head']
    g = lambda i: (str(n.getName(i, 3, 1, 0x409)) if n.getName(i, 3, 1, 0x409) else None)
    i = Obj()
    fam = g(1); sub = g(2)
    i.familyName = fam
    i.styleName = sub
    i.styleMapFamilyName = fam
    i.styleMapStyleName = sub.lower()
    ver = round(head.fontRevision, 3)
    i.versionMajor = int(ver); i.versionMinor = int(round((ver - int(ver)) * 1000))
    i.copyright = PROJECT['copyright']
    i.unitsPerEm = head.unitsPerEm
    i.ascender = hh.ascent; i.descender = hh.descent
    i.xHeight = os2.sxHeight; i.capHeight = os2.sCapHeight
    i.italicAngle = post.italicAngle
    i.openTypeHeadFlags = [b for b in range(16) if head.flags & (1 << b) and b not in (0, 1, 3, 4)]  # builder sets the rest
    i.openTypeHheaAscender = hh.ascent; i.openTypeHheaDescender = hh.descent; i.openTypeHheaLineGap = hh.lineGap
    i.openTypeHheaCaretSlopeRise = hh.caretSlopeRise; i.openTypeHheaCaretSlopeRun = hh.caretSlopeRun
    i.openTypeNameDesigner = PROJECT['designer']; i.openTypeNameDesignerURL = PROJECT['url']
    i.openTypeNameManufacturer = PROJECT['manufacturer']; i.openTypeNameManufacturerURL = PROJECT['url']
    i.openTypeNameLicense = ('This Font Software is licensed under the SIL Open Font License, Version 1.1. '
                             'This license is available with a FAQ at: https://openfontlicense.org')
    i.openTypeNameLicenseURL = 'https://openfontlicense.org'
    i.openTypeNameDescription = PROJECT['description']
    i.openTypeOS2WeightClass = os2.usWeightClass; i.openTypeOS2WidthClass = os2.usWidthClass
    i.openTypeOS2Selection = [b for b in (7, 8, 9) if os2.fsSelection & (1 << b)]
    i.openTypeOS2VendorID = os2.achVendID
    i.openTypeOS2Type = [b for b in range(16) if os2.fsType & (1 << b)]
    p = os2.panose
    i.openTypeOS2Panose = [p.bFamilyType, p.bSerifStyle, p.bWeight, p.bProportion, p.bContrast,
                           p.bStrokeVariation, p.bArmStyle, p.bLetterForm, p.bMidline, p.bXHeight]
    i.openTypeOS2TypoAscender = os2.sTypoAscender; i.openTypeOS2TypoDescender = os2.sTypoDescender
    i.openTypeOS2TypoLineGap = os2.sTypoLineGap
    i.openTypeOS2WinAscent = os2.usWinAscent; i.openTypeOS2WinDescent = os2.usWinDescent
    for k in ('ySubscriptXSize ySubscriptYSize ySubscriptXOffset ySubscriptYOffset ySuperscriptXSize '
              'ySuperscriptYSize ySuperscriptXOffset ySuperscriptYOffset yStrikeoutSize yStrikeoutPosition').split():
        setattr(i, 'openTypeOS2' + k[0].upper() + k[1:].replace('Xsize', 'XSize'), getattr(os2, k))
    i.postscriptFontName = g(6)
    i.postscriptFullName = g(4)
    i.postscriptUnderlinePosition = post.underlinePosition
    i.postscriptUnderlineThickness = post.underlineThickness
    i.postscriptIsFixedPitch = bool(post.isFixedPitch)
    i.openTypeOS2UnicodeRanges = [b for b in range(128) if (os2.ulUnicodeRange1, os2.ulUnicodeRange2, os2.ulUnicodeRange3, os2.ulUnicodeRange4)[b // 32] & (1 << (b % 32))]
    i.openTypeOS2CodePageRanges = [b for b in range(64) if (os2.ulCodePageRange1, os2.ulCodePageRange2)[b // 32] & (1 << (b % 32))]
    i.openTypeGaspRangeRecords = [{'rangeMaxPPEM': k, 'rangeGaspBehavior': [b for b in range(4) if v & (1 << b)]}
                                  for k, v in sorted(t['gasp'].gaspRange.items())] if 'gasp' in t else None
    # fix attribute names produced above for OS/2 sub/superscript fields
    fixed = {}
    for k, v in list(vars(i).items()):
        if k.startswith('openTypeOS2Y'):
            nk = 'openTypeOS2' + k[len('openTypeOS2'):].replace('Xsize', 'XSize').replace('Ysize', 'YSize')
            fixed[nk] = v; delattr(i, k)
    for k, v in fixed.items(): setattr(i, k, v)
    for k, v in list(vars(i).items()):
        if v is None: delattr(i, k)
    return i

# ---------------------------------------------------------------- anchors
def anchors(t):
    """Return ({glyph: {name: (x, y)}}, report)."""
    A = collections.defaultdict(dict); clash = []
    def put(g, name, x, y):
        old = A[g].get(name)
        if old and old != (x, y): clash.append((g, name, old, (x, y)))
        if not old: A[g][name] = (x, y)
    L = t['GPOS'].table.LookupList.Lookup
    for l in L:                      # mark-to-base and mark-to-ligature first: they define "_x"
        for st in l.SubTable:
            st = getattr(st, 'ExtSubTable', st)
            if hasattr(st, 'BaseArray'):
                for g, r in zip(st.MarkCoverage.glyphs, st.MarkArray.MarkRecord):
                    put(g, '_' + ANCHOR_NAMES[r.Class], r.MarkAnchor.XCoordinate, r.MarkAnchor.YCoordinate)
                for g, br in zip(st.BaseCoverage.glyphs, st.BaseArray.BaseRecord):
                    for c, a in enumerate(br.BaseAnchor):
                        if a is not None: put(g, ANCHOR_NAMES[c], a.XCoordinate, a.YCoordinate)
            elif hasattr(st, 'LigatureArray'):
                for g, la in zip(st.LigatureCoverage.glyphs, st.LigatureArray.LigatureAttach):
                    for k, cr in enumerate(la.ComponentRecord):
                        for c, a in enumerate(cr.LigatureAnchor):
                            if a is not None: put(g, f'{ANCHOR_NAMES[c]}_{k+1}', a.XCoordinate, a.YCoordinate)
    for l in L:                      # mark-to-mark: mark1 "_x" (already set), mark2 "x"
        for st in l.SubTable:
            st = getattr(st, 'ExtSubTable', st)
            if hasattr(st, 'Mark1Array'):
                # mark-to-mark lookups here have one class each; map it via the mark's existing "_x" anchor
                names = set()
                for g, r in zip(st.Mark1Coverage.glyphs, st.Mark1Array.MarkRecord):
                    cand = [k for k in A.get(g, {}) if k.startswith('_')]
                    if len(cand) == 1: names.add(cand[0][1:])
                assert len(names) == 1, names
                nm = names.pop()
                for g, r in zip(st.Mark1Coverage.glyphs, st.Mark1Array.MarkRecord):
                    put(g, '_' + nm, r.MarkAnchor.XCoordinate, r.MarkAnchor.YCoordinate)
                for g, m2 in zip(st.Mark2Coverage.glyphs, st.Mark2Array.Mark2Record):
                    a = m2.Mark2Anchor[0]
                    if a is not None: put(g, nm, a.XCoordinate, a.YCoordinate)
    return A, clash

# ---------------------------------------------------------------- GSUB -> fea
def gsub_fea(t):
    gs = t['GSUB'].table; L = gs.LookupList.Lookup
    gdef = t['GDEF'].table
    out = ['# GSUB decompiled from the 2.501 binary by scripts/ttf2ufo.py.',
           '# Mark and mark-to-mark positioning is generated by ufo2ft from glyph anchors.', '']
    marksets = []
    if getattr(gdef, 'MarkGlyphSetsDef', None):
        for k, cov in enumerate(gdef.MarkGlyphSetsDef.Coverage):
            out.append(f'@MarkSet{k} = [{" ".join(cov.glyphs)}];'); marksets.append(f'@MarkSet{k}')
        out.append('')
    # language systems
    ls = []
    for sr in gs.ScriptList.ScriptRecord:
        ls.append((sr.ScriptTag, 'dflt'))
        ls += [(sr.ScriptTag, l.LangSysTag.strip()) for l in sr.Script.LangSysRecord]
    for s, l in ls: out.append(f'languagesystem {s} {l};')
    out.append('')
    def cls(gl): return gl[0] if len(gl) == 1 else '[' + ' '.join(gl) + ']'
    def flagstr(l):
        f = l.LookupFlag; parts = []
        if f & 2: parts.append('IgnoreBaseGlyphs')
        if f & 4: parts.append('IgnoreLigatures')
        if f & 8: parts.append('IgnoreMarks')
        if f & 1: parts.append('RightToLeft')
        if f & 0x10: parts.append(f'UseMarkFilteringSet {marksets[l.MarkFilteringSet]}')
        if f & 0xFF00: parts.append(f'MarkAttachmentType {f >> 8}')
        return 'lookupflag ' + (' '.join(parts) if parts else '0') + ';'
    def coverage_classes(st, attr):
        cd = getattr(st, attr).classDefs if getattr(st, attr) else {}
        return cd
    body = {}
    for li, l in enumerate(L):
        lines = []
        for st in l.SubTable:
            st = getattr(st, 'ExtSubTable', st)
            tp = st.LookupType
            if tp == 1:
                for a, b in sorted(st.mapping.items()): lines.append(f'sub {a} by {b};')
            elif tp == 2:
                for a, b in sorted(st.mapping.items()): lines.append(f'sub {a} by {" ".join(b)};')
            elif tp == 3:
                for a, b in sorted(st.alternates.items()): lines.append(f'sub {a} from [{" ".join(b)}];')
            elif tp == 4:
                for first, ligs in st.ligatures.items():
                    for lg in ligs: lines.append(f'sub {" ".join([first] + list(lg.Component))} by {lg.LigGlyph};')
            elif tp in (5, 6):
                lines += chain_rules(st, tp, cls)
            else:
                raise NotImplementedError(f'GSUB type {tp} in lookup {li}')
            lines.append('subtable;')
        if lines and lines[-1] == 'subtable;': lines.pop()
        body[li] = (flagstr(l), lines)
    import re
    deps = {li: sorted({int(m) for x in lines for m in re.findall(r'lookup L(\d+)', x)}) for li, (flag, lines) in body.items()}
    order, seen = [], set()
    def visit(li):
        if li in seen: return
        seen.add(li)
        for d in deps[li]: visit(d)
        order.append(li)
    for li in body: visit(li)
    for li in order:
        flag, lines = body[li]
        out.append(f'lookup L{li:02d} {{'); out.append('  ' + flag)
        out += ['  ' + x for x in lines]
        out.append(f'}} L{li:02d};'); out.append('')
    # features, per script/language
    feats = collections.OrderedDict()
    for fi, fr in enumerate(gs.FeatureList.FeatureRecord):
        feats.setdefault(fr.FeatureTag, {})
    for sr in gs.ScriptList.ScriptRecord:
        for lang, lsys in [('dflt', sr.Script.DefaultLangSys)] + [(l.LangSysTag.strip(), l.LangSys) for l in sr.Script.LangSysRecord]:
            if lsys is None: continue
            for fi in lsys.FeatureIndex:
                fr = gs.FeatureList.FeatureRecord[fi]
                feats[fr.FeatureTag].setdefault((sr.ScriptTag, lang), []).extend(fr.Feature.LookupListIndex)
    for tag, per in feats.items():
        if tag == 'aalt': continue   # rebuilt below from the features it collects
        out.append(f'feature {tag} {{')
        if tag.startswith('ss') and len(tag) == 4:
            out.append('  featureNames { name "Stylistic Set ' + str(int(tag[2:])) + '"; };')
        bysig = collections.OrderedDict()
        for (s, l), lks in per.items(): bysig.setdefault(tuple(lks), []).append((s, l))
        common = per.get(('DFLT', 'dflt'))
        if common is not None and all(tuple(v) == tuple(common) for v in per.values()) and len(per) == len(ls):
            for x in common: out.append(f'  lookup L{x:02d};')
        else:
            for s, l in ls:
                lks = per.get((s, l))
                out.append(f'  script {s};' if l == 'dflt' else f'  script {s}; language {l} exclude_dflt;')
                for x in (lks or []): out.append(f'    lookup L{x:02d};')
        out.append(f'}} {tag};'); out.append('')
    if 'aalt' in feats:
        src = [tg for tg, per in feats.items() if tg != 'aalt' and any(L[x].LookupType in (1, 3) or (L[x].LookupType == 7 and L[x].SubTable[0].ExtensionLookupType in (1, 3)) for v in per.values() for x in v)]
        out.insert(out.index('') + 1, 'feature aalt {\n' + ''.join(f'  feature {s};\n' for s in src) + '} aalt;\n')
    return '\n'.join(out) + '\n'

def chain_rules(st, tp, cls):
    rules = []
    def emit(bt, inp, la, recs):
        marked = []
        lk = collections.defaultdict(list)
        for r in recs: lk[r.SequenceIndex].append(r.LookupListIndex)
        for k, gl in enumerate(inp):
            s = cls(gl) + "'"
            for x in lk.get(k, []): s += f' lookup L{x:02d}'
            marked.append(s)
        seq = ' '.join([cls(g) for g in bt] + marked + [cls(g) for g in la])
        rules.append(('ignore sub ' if not recs else 'sub ') + seq + ';')
    f = st.Format
    if f == 3:
        if tp == 6:
            bt = [c.glyphs for c in reversed(st.BacktrackCoverage)]; inp = [c.glyphs for c in st.InputCoverage]
            la = [c.glyphs for c in st.LookAheadCoverage]; recs = st.SubstLookupRecord
        else:
            bt = []; inp = [c.glyphs for c in st.Coverage]; la = []; recs = st.SubstLookupRecord
        emit(bt, inp, la, recs)
    elif f == 1:
        cov = st.Coverage.glyphs
        sets = st.ChainSubRuleSet if tp == 6 else st.SubRuleSet
        for first, rs in zip(cov, sets):
            if rs is None: continue
            for r in (rs.ChainSubRule if tp == 6 else rs.SubRule):
                bt = [[g] for g in reversed(r.Backtrack)] if tp == 6 else []
                inp = [[first]] + [[g] for g in r.Input]
                la = [[g] for g in r.LookAhead] if tp == 6 else []
                emit(bt, inp, la, r.SubstLookupRecord)
    elif f == 2:
        def members(cd, glyphset):
            m = collections.defaultdict(list)
            for g, c in cd.classDefs.items(): m[c].append(g)
            return m
        if tp == 6:
            bc = members(st.BacktrackClassDef, None); ic = members(st.InputClassDef, None); lc = members(st.LookAheadClassDef, None)
        else:
            ic = members(st.ClassDef, None); bc = lc = {}
        cov = set(st.Coverage.glyphs)
        sets = st.ChainSubClassSet if tp == 6 else st.SubClassSet
        for c0, rs in enumerate(sets):
            if rs is None: continue
            first = [g for g in (ic.get(c0, []) if c0 else [g for g in cov if g not in st.InputClassDef.classDefs]) if g in cov]
            for r in (rs.ChainSubClassRule if tp == 6 else rs.SubClassRule):
                for c in list(r.Input) + (list(r.Backtrack) + list(r.LookAhead) if tp == 6 else []):
                    if c == 0: raise NotImplementedError('class 0 in context')
                bt = [sorted(bc[c]) for c in reversed(r.Backtrack)] if tp == 6 else []
                inp = [sorted(first)] + [sorted(ic[c]) for c in r.Input]
                la = [sorted(lc[c]) for c in r.LookAhead] if tp == 6 else []
                emit(bt, inp, la, r.SubstLookupRecord)
    return rules

# ---------------------------------------------------------------- main
def convert(ttf, ufo):
    t = TTFont(ttf)
    if os.path.exists(ufo): shutil.rmtree(ufo)
    w = UFOWriter(ufo, formatVersion=3)
    w.writeInfo(fontinfo(t))
    gdef = t['GDEF'].table.GlyphClassDef.classDefs
    cat = {1: 'base', 2: 'ligature', 3: 'mark', 4: 'component'}
    w.writeLib({
        'public.glyphOrder': t.getGlyphOrder(),
        'public.openTypeCategories': {g: cat[c] for g, c in gdef.items() if c in cat},
    })
    w.writeFeatures(gsub_fea(t))
    A, clash = anchors(t)
    gs = w.getGlyphSet()
    cmap = collections.defaultdict(list)
    for cp, g in t.getBestCmap().items(): cmap[g].append(cp)
    for tb in t['cmap'].tables:   # keep secondary mappings (e.g. format 14 is ignored)
        if tb.isUnicode():
            for cp, g in tb.cmap.items():
                if cp not in cmap[g]: cmap[g].append(cp)
    glyf = t['glyf']; hm = t['hmtx']
    for name in t.getGlyphOrder():
        o = Obj(); o.width = hm[name][0]; o.unicodes = sorted(cmap.get(name, []))
        o.anchors = [{'name': k, 'x': x, 'y': y} for k, (x, y) in sorted(A.get(name, {}).items())]
        g = glyf[name]
        # UFO sources use PostScript (counter-clockwise) direction; fontmake reverses back for TTF.
        gs.writeGlyph(name, o, lambda pen, g=g: g.drawPoints(ReverseContourPointPen(pen), glyf))
    gs.writeContents(); w.writeLayerContents(); w.close()
    return clash

if __name__ == '__main__':
    clash = convert(sys.argv[1], sys.argv[2])
    print(f'{sys.argv[2]}: done; {len(clash)} anchor conflicts kept at first value')
    for c in clash[:10]: print('  ', c)
