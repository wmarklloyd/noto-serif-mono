#!/usr/bin/env python3
"""Check that sources/*.ufo reproduce a reference TTF:
outlines, advance widths, cmap, glyph order, GDEF classes, GSUB behaviour
(features.fea compiled with feaLib) and mark/mkmk attachment offsets (anchors).

Outlines: the build removes overlaps with skia-pathops and rounds to integers, so a
source glyph is compared after the same steps (pathops simplify, TTGlyphPen rounding),
ignoring contour order, start point, direction and implied on-curve points, with 1 unit
of tolerance. Composites must keep the same components and offsets.

usage: python3 scripts/verify_sources.py REF.ttf SOURCE.ufo
"""
import sys, collections, io
import pathops, ufoLib2
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ufoLib import UFOReader
from fontTools.pens.recordingPen import RecordingPointPen
from fontTools.pens.pointPen import ReverseContourPointPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

ref, ufo = sys.argv[1], sys.argv[2]
t = TTFont(ref); r = UFOReader(ufo); gs = r.getGlyphSet(); lib = r.readLib()
fails = []
ufo_font = ufoLib2.Font.open(ufo)
class G: pass

def contours_of(glyph):
    """Contours as lists of (x, y, on), implied on-curve midpoints dropped."""
    if glyph.numberOfContours <= 0: return []
    c = glyph.coordinates; fl = glyph.flags; out = []; s = 0
    for e in glyph.endPtsOfContours:
        pts = [(int(c[i][0]), int(c[i][1]), fl[i] & 1) for i in range(s, e + 1)]; s = e + 1
        keep = []
        for k, p in enumerate(pts):
            a, b = pts[k - 1], pts[(k + 1) % len(pts)]
            if p[2] and not a[2] and not b[2] and abs(a[0] + b[0] - 2 * p[0]) <= 1 and abs(a[1] + b[1] - 2 * p[1]) <= 1:
                continue
            keep.append(p)
        out.append(keep)
    return out
def canon(ct):
    return min(tuple(seq[k:] + seq[:k]) for seq in (ct, ct[::-1]) for k in range(len(seq)))
def close(a, b, tol=1):
    return len(a) == len(b) and all(p[2] == q[2] and abs(p[0] - q[0]) <= tol and abs(p[1] - q[1]) <= tol for p, q in zip(a, b))
def contours_match(A, B):
    A = sorted(canon(c) for c in A); B = sorted(canon(c) for c in B)
    if A == B: return True
    if len(A) != len(B): return False
    left = list(B)
    for a in A:
        for i, b in enumerate(left):
            b = list(b)
            if any(close(list(a), seq[k:] + seq[:k]) for seq in (b, b[::-1]) for k in range(len(seq))):
                left.pop(i); break
        else: return False
    return True
def same_outline(tg, n):
    ug = ufo_font[n]
    if tg.isComposite():
        if ug.contours: return False
        tc = [(c.glyphName, c.x, c.y, getattr(c, 'transform', None) is not None) for c in tg.components]
        uc = [(c.baseGlyph, round(c.transformation[4]), round(c.transformation[5]),
               tuple(c.transformation[:4]) != (1, 0, 0, 1)) for c in ug.components]
        return tc == uc
    p = pathops.Path(); ug.draw(p.getPen(glyphSet=ufo_font)); p.simplify()
    pen = TTGlyphPen(None); p.draw(pen)
    return contours_match(contours_of(tg), contours_of(pen.glyph()))
# ---- glyphs
go = t.getGlyphOrder()
if lib['public.glyphOrder'] != go: fails.append('glyph order differs')
cm = collections.defaultdict(set)
for tb in t['cmap'].tables:
    if tb.isUnicode() and tb.format != 14:
        for c, g in tb.cmap.items(): cm[g].add(c)
glyf = t['glyf']; bad_o = []; bad_w = []; bad_u = []; ufog = {}
for n in go:
    g = G(); g.anchors = []
    p = RecordingPointPen(); gs.readGlyph(n, g, ReverseContourPointPen(p)); ufog[n] = g  # undo PS direction
    if not same_outline(glyf[n], n): bad_o.append(n)
    if getattr(g, 'width', 0) != t['hmtx'][n][0]: bad_w.append(n)
    if set(getattr(g, 'unicodes', []) or []) != cm.get(n, set()): bad_u.append(n)
print(f'outlines differ: {len(bad_o)}  widths differ: {len(bad_w)}  unicodes differ: {len(bad_u)}', bad_o[:5], bad_u[:5])
fails += ['outlines'] * bool(bad_o) + ['widths'] * bool(bad_w) + ['unicodes'] * bool(bad_u)
# ---- GDEF classes
cat = {'base': 1, 'ligature': 2, 'mark': 3, 'component': 4}
uc = {g: cat[c] for g, c in lib['public.openTypeCategories'].items()}
if uc != t['GDEF'].table.GlyphClassDef.classDefs: fails.append('GDEF classes'); print('GDEF classes differ')
# ---- GSUB: compile features.fea onto a copy and compare behaviour lookup-by-lookup
def lookup_sig(l):
    sig = []
    for st in l.SubTable:
        st = getattr(st, 'ExtSubTable', st); tp = st.LookupType
        if tp in (1, 2): sig.append((tp, tuple(sorted((a, tuple(b) if isinstance(b, list) else b) for a, b in st.mapping.items()))))
        elif tp == 3: sig.append((tp, tuple(sorted((a, tuple(b)) for a, b in st.alternates.items()))))
        elif tp == 4: sig.append((tp, tuple(sorted((a, tuple(x.Component), x.LigGlyph) for a, v in st.ligatures.items() for x in v))))
        else: sig.append((tp, 'ctx'))
    # merge subtables of simple types so subtable splitting does not matter
    merged = collections.defaultdict(set)
    for tp, s in sig: merged[tp] |= set(s) if s != 'ctx' else {'ctx'}
    return (l.LookupFlag, tuple(sorted((k, tuple(sorted(map(str, v)))) for k, v in merged.items())))
def ctx_expand(t2, l):
    """Expand contextual lookups into (input-sequence-start-glyph, nested lookup sigs) sets for comparison."""
    out = set(); L = t2['GSUB'].table.LookupList.Lookup
    for st in l.SubTable:
        st = getattr(st, 'ExtSubTable', st)
        if st.LookupType not in (5, 6): continue
        if st.Format == 3:
            cov = st.InputCoverage if st.LookupType == 6 else st.Coverage
            bt = tuple(tuple(c.glyphs) for c in st.BacktrackCoverage) if st.LookupType == 6 else ()
            la = tuple(tuple(c.glyphs) for c in st.LookAheadCoverage) if st.LookupType == 6 else ()
            out.add((bt, tuple(tuple(c.glyphs) for c in cov), la, tuple((r.SequenceIndex, lookup_sig(L[r.LookupListIndex])) for r in st.SubstLookupRecord)))
        else:
            out.add(('format', st.Format, st.LookupType))
    return out
def feature_map(t2):
    gs2 = t2['GSUB'].table; L = gs2.LookupList.Lookup; m = {}
    for sr in gs2.ScriptList.ScriptRecord:
        for lang, ls in [('dflt', sr.Script.DefaultLangSys)] + [(x.LangSysTag.strip(), x.LangSys) for x in sr.Script.LangSysRecord]:
            for fi in ls.FeatureIndex:
                fr = gs2.FeatureList.FeatureRecord[fi]
                if fr.FeatureTag == 'aalt': continue
                m.setdefault((sr.ScriptTag, lang, fr.FeatureTag), set()).update(fr.Feature.LookupListIndex)
    # lookups are applied once each, in LookupList order: compare the de-duplicated, ordered behaviour
    return {k: [(lookup_sig(L[i]), frozenset(ctx_expand(t2, L[i]))) for i in sorted(v)] for k, v in m.items()}
t2 = TTFont(ref); del t2['GSUB']
fea = r.readFeatures()
addOpenTypeFeaturesFromString(t2, fea, tables=['GSUB'])
a, b = feature_map(t), feature_map(t2)
diff = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
print(f'GSUB script/lang/feature entries: {len(a)} reference, {len(b)} from features.fea; differing: {len(diff)}', sorted(diff)[:6])
if diff: fails.append('GSUB')
# ---- anchors vs GPOS attachment offsets
A = {n: {x['name']: (x['x'], x['y']) for x in ufog[n].anchors} for n in go}
pairs = 0; badp = []
for l in t['GPOS'].table.LookupList.Lookup:
    for st in l.SubTable:
        st = getattr(st, 'ExtSubTable', st)
        if hasattr(st, 'BaseArray'):
            for m, mr in zip(st.MarkCoverage.glyphs, st.MarkArray.MarkRecord):
                for b_, br in zip(st.BaseCoverage.glyphs, st.BaseArray.BaseRecord):
                    a_ = br.BaseAnchor[mr.Class]
                    if a_ is None: continue
                    pairs += 1
                    want = (a_.XCoordinate - mr.MarkAnchor.XCoordinate, a_.YCoordinate - mr.MarkAnchor.YCoordinate)
                    nm = [k for k in A[m] if k.startswith('_')]
                    got = [(A[b_][k[1:]][0] - A[m][k][0], A[b_][k[1:]][1] - A[m][k][1]) for k in nm if k[1:] in A[b_]]
                    if want not in got: badp.append((b_, m))
        elif hasattr(st, 'Mark1Array'):
            for m, mr in zip(st.Mark1Coverage.glyphs, st.Mark1Array.MarkRecord):
                for m2, r2 in zip(st.Mark2Coverage.glyphs, st.Mark2Array.Mark2Record):
                    a_ = r2.Mark2Anchor[0]
                    if a_ is None: continue
                    pairs += 1
                    want = (a_.XCoordinate - mr.MarkAnchor.XCoordinate, a_.YCoordinate - mr.MarkAnchor.YCoordinate)
                    nm = [k for k in A[m] if k.startswith('_')]
                    got = [(A[m2][k[1:]][0] - A[m][k][0], A[m2][k[1:]][1] - A[m][k][1]) for k in nm if k[1:] in A[m2]]
                    if want not in got: badp.append((m2, m))
print(f'mark/mkmk attachment pairs checked: {pairs}; reproduced by anchors: {pairs - len(badp)}', badp[:5])
if badp: fails.append('anchors')
print('RESULT:', 'PASS' if not fails else 'FAIL ' + ', '.join(fails))
sys.exit(1 if fails else 0)
