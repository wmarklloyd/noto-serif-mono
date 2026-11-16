from pathlib import Path
from PIL import ImageFont
from statistics import mean
import sys
groups=['FI IF LI IL LL IL','JA AJ JI IJ JO OJ UJ JU','WA AW AY AV VA WA VY','ri ir it ti tr rt ni in','AZ ZA ZZ ZE eJ ke ek']
i=int(sys.argv[1]); before,after=map(Path,sys.argv[2:])
for style in ('Italic','BoldItalic'):
    print(style,end=' ')
    for directory in (before,after):
        f=ImageFont.truetype(str(directory/f'ArborMono-{style}.ttf'),1000)
        chars=set(''.join(groups[i-1].split()))
        def profile(c):
            m,(x,t)=f.getmask2(c,anchor='ls');b=bytes(m);w,h=m.size
            return {y:(x+min(row),x+max(row)+1) for y in range(25,710,10)
                    if 0<=-y-t<h and (row:=[k for k,v in enumerate(b[(-y-t)*w:(1-y-t)*w]) if v>=128])}
        p={c:profile(c) for c in chars}
        pairs=[]
        for a,b in groups[i-1].split():
            rows=[563+p[b][y][0]-p[a][y][1] for y in p[a].keys()&p[b].keys()]
            pairs.append(f'{a+b}={mean(rows):.0f}/{min(rows)}')
        print(directory.name, ' '.join(pairs),end=' | ')
    print()
