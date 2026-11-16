"""Fit diff = B[base,zone] + M[mark] from single-mark rows of ink.tsv (per style).
Prints base corrections and mark corrections; writes fit.json."""
import csv, json, sys, statistics as S, unicodedata as ud
SP = "C:/Users/Mark/arbor-mono/scripts/history/v2.502"
rows = list(csv.DictReader(open(f"{SP}/ink.tsv", encoding="utf8"), delimiter="\t", quoting=csv.QUOTE_NONE))
EXCL = set("ďľĽťḋḃḟḣḱḳ")  # deliberate side forms checked visually later
res = {}
for st in ["Regular", "Bold", "Italic", "BoldItalic"]:
    obs = []
    for r in rows:
        if r["style"] != st or r["diff"] in ("", "missing"):
            continue
        n = ud.normalize("NFD", r["char"])
        if len(n) != 2 or r["char"] in EXCL:
            continue
        base, mark = n
        if 0x370 <= ord(base) <= 0x3FF and base.isupper():
            continue  # Greek capitals put accents to the left by design
        cls = "top" if ud.combining(mark) == 230 else "bottom" if ud.combining(mark) == 220 else None
        if cls != r["zone"]:
            continue
        obs.append((base, mark, cls, float(r["diff"])))
    B = {}; M = {}
    for it in range(20):
        for k in {(b, z) for b, m, z, d in obs}:
            B[k] = S.median([d - M.get(m, 0) for b, m, z, d in obs if (b, z) == k])
        for m in {m for b, m, z, d in obs}:
            M[m] = S.median([d - B[(b, z)] for b, mm, z, d in obs if mm == m])
        c = S.median(M.values())
        M = {k: v - c for k, v in M.items()}
    resid = [(b, m, d - B[(b, z)] - M[m]) for b, m, z, d in obs]
    res[st] = {"B": {f"{b}|{z}": v for (b, z), v in B.items()}, "M": M}
    print(st, len(obs), "obs; big resid:", " ".join(f"{b}{m}{r:+.0f}" for b, m, r in resid if abs(r) > 20))
    print("  marks:", " ".join(f"{ud.name(m,'?').replace('COMBINING ','')[:14]}{v:+.0f}" for m, v in sorted(M.items(), key=lambda x: -abs(x[1])) if abs(v) >= 6))
    print("  bases:", " ".join(f"{b}{z[0]}{v:+.0f}" for (b, z), v in sorted(B.items(), key=lambda x: -abs(x[1])) if abs(v) >= 10))
json.dump(res, open(f"{SP}/fit.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
