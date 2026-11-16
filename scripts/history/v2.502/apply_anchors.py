"""Apply fitted anchor corrections (fit.json) to the four UFOs.
- base anchors: top/bottom x -= B (on the glyph that actually receives the mark)
- mark anchors: _top/_bottom x += M (cmap glyph and its suffixed variants)
- ogonek: every glyph with a 'bottom' anchor gets 'ogonek' at its pre-change bottom
  position; uni0328 (and variants) attach with '_ogonek'.
"""
import json, unicodedata as ud, sys
import ufoLib2, uharfbuzz as hb
from fontTools.ttLib import TTFont
SP = "C:/Users/Mark/arbor-mono/scripts/history/v2.502"
fit = json.load(open(f"{SP}/fit.json", encoding="utf8"))
MIN = 8
for st, F in fit.items():
    f = ufoLib2.Font.open(f"C:/Users/Mark/arbor-mono/sources/ArborMono-{st}.ufo")
    tt = TTFont(f"{SP}/decomp-{st}.ttf"); order = tt.getGlyphOrder()
    hf = hb.Font(hb.Face(hb.Blob.from_file_path(f"{SP}/decomp-{st}.ttf")))
    cmap = {u: g.name for g in f for u in g.unicodes}
    # 1. ogonek anchors at the current bottom positions
    n_og = 0
    for g in f:
        names = {a.name for a in g.anchors}
        b = [a for a in g.anchors if a.name == "bottom"]
        if b and "ogonek" not in names:
            g.appendAnchor({"name": "ogonek", "x": b[0].x, "y": b[0].y}); n_og += 1
    for g in f:
        if g.name == "uni0328" or g.name.startswith("uni0328."):
            for a in g.anchors:
                if a.name == "_bottom":
                    a.name = "_ogonek"
    # 2. base corrections
    log = []
    for key, v in F["B"].items():
        ch, zone = key.split("|")
        if abs(v) < MIN or not ud.category(ch).startswith("L"):
            continue
        buf = hb.Buffer(); buf.add_str(ch + ("\u0301" if zone == "top" else "\u0323"))
        buf.guess_segment_properties(); hb.shape(hf, buf, {})
        gname = order[buf.glyph_infos[0].codepoint]
        g = f[gname]
        a = [a for a in g.anchors if a.name == zone]
        if not a:
            log.append(f"{gname}:no-{zone}"); continue
        a[0].x = round(a[0].x - v); log.append(f"{gname}.{zone}{-v:+.0f}")
    # 3. mark corrections
    for ch, v in F["M"].items():
        if abs(v) < MIN or ord(ch) not in cmap:
            continue
        base = cmap[ord(ch)]
        for g in f:
            if g.name == base or g.name.startswith(base + "."):
                for a in g.anchors:
                    if a.name in ("_top", "_bottom"):
                        a.x = round(a.x + v); log.append(f"{g.name}{a.name}{v:+.0f}")
    f.save()
    print(st, "ogonek anchors", n_og, "|", " ".join(log))
