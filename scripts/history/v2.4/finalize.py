import sys, time
from fontTools.ttLib import TTFont
from fontTools.misc.timeTools import timestampNow
STY={'Regular':'Regular','Bold':'Bold','Italic':'Italic','BoldItalic':'Bold Italic'}
def finalize(path, style, ver='2.400'):
    t=TTFont(path); n=t['name']; sn=STY[style]
    for r in list(n.names):
        if r.nameID in (16,17): n.names.remove(r)
    for pid,eid,lid in ((1,0,0),(3,1,0x409)):
        n.setName(sn,2,pid,eid,lid)
        n.setName(f'Arbor Mono {sn}' if sn!='Regular' else 'Arbor Mono Regular',4,pid,eid,lid)
        n.setName(f'{ver}; ArMo; ArborMono-{style}',3,pid,eid,lid)
        n.setName(f'Version {ver}; embedded TrueType instructions for 7–72 ppem',5,pid,eid,lid)
    t['head'].fontRevision=float(ver); t['head'].modified=timestampNow()
    t['OS/2'].achVendID='NONE'
    t.save(path)
if __name__=='__main__':
    for st in STY: finalize(f'{sys.argv[1]}/ArborMono-{st}.ttf',st)
