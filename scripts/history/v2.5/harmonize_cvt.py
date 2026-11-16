from fontTools.ttLib import TTFont
# x-height alignment references used by ttfautohint's bci_align_x_height (indices from the prep LOOPCALL)
XALIGN=[47,67,141,161,181]
def harmonize(t, ref, idx=XALIGN):
    cv=t['cvt '].values; changed={}
    for i in idx:
        if cv[i]!=ref[i]: changed[i]=(int(cv[i]),int(ref[i])); cv[i]=ref[i]
    return changed
