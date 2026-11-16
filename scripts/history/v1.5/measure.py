from pathlib import Path
from statistics import mean
from PIL import ImageFont
root=Path(__file__).parent
letters="GHIJ"
figures="0123456789"
for style in ("Italic","BoldItalic"):
 for option in ("baseline","natural","quantized","strong"):
    folder = root/option if option!="baseline" else root.parent/"final"
    p=folder/f"ArborMono-{style}.ttf"
    f=ImageFont.truetype(str(p),1000)
    def coverage(face,c):
        return sum(bytes(face.getmask(c)))
    ideal={c:coverage(f,c)/1e6 for c in letters+figures}
    errors=[]; differences=[]
    for size in range(10,25):
        face=ImageFont.truetype(str(p),size)
        ratios={c:coverage(face,c)/(size**2*ideal[c]) for c in ideal}
        errors.extend(abs(v-1) for v in ratios.values())
        differences.append(abs(mean(ratios[c] for c in letters)-mean(ratios[c] for c in figures)))
    print(style,option,round(mean(errors)*100,2),round(mean(differences)*100,2))
