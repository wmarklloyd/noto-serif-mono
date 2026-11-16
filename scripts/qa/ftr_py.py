"""Pure-Python stand-in for the compiled `ftr` renderer (same arguments, same output).

    python scripts/qa/ftr_py.py FONT PPEM MODE INTERP GID...

Uses the FreeType bundled with freetype-py, for machines without a C compiler.
MODE: 0 unhinted gray, 1 hinted gray, 2 hinted mono; +4 pedantic; +10 summary lines.
"""
import sys, ctypes
import freetype
import freetype.raw as raw


def run(path, ppem, mode, interp, gids, out):
    iv = ctypes.c_uint(interp)
    raw.FT_Property_Set(freetype.get_handle(), b"truetype", b"interpreter-version", ctypes.byref(iv))
    face = freetype.Face(path)
    face.set_char_size(0, int(ppem * 64 + 0.5), 72, 72)
    summary = mode >= 10
    if summary:
        mode -= 10
    ped = mode >= 4
    if ped:
        mode -= 4
    w = out.append
    for gid in gids:
        fl = freetype.FT_LOAD_NO_AUTOHINT | freetype.FT_LOAD_NO_BITMAP
        if mode == 0:
            fl |= freetype.FT_LOAD_NO_HINTING
        if mode == 2:
            fl |= freetype.FT_LOAD_TARGET_MONO
        if ped:
            fl |= freetype.FT_LOAD_PEDANTIC
        try:
            face.load_glyph(gid, fl)
        except freetype.FT_Exception as e:
            w(f"ERR {gid} {getattr(e, 'errcode', -1)}")
            continue
        g = face.glyph
        g.render(freetype.FT_RENDER_MODE_MONO if mode == 2 else freetype.FT_RENDER_MODE_NORMAL)
        b = g.bitmap
        buf = b.buffer; pitch = b.pitch; W = b.width; R = b.rows
        if mode == 2:
            px = [[((buf[r * pitch + c // 8] >> (7 - c % 8)) & 1) * 255 for c in range(W)] for r in range(R)]
        else:
            px = [buf[r * pitch:r * pitch + W] for r in range(R)]
        if summary:
            rows = [r for r in range(R) if any(v > 64 for v in px[r])]
            ink = sum(sum(row) for row in px)
            top = g.bitmap_top - rows[0] if rows else -999
            bot = g.bitmap_top - rows[-1] - 1 if rows else -999
            w(f"S {gid} {top} {bot} {ink} {g.advance.x}")
            continue
        w(f"G {gid} {g.bitmap_left} {g.bitmap_top} {W} {R} {g.advance.x}")
        for row in px:
            w("".join(f"{v:02x}" for v in row))
    return out


if __name__ == "__main__":
    a = sys.argv
    lines = run(a[1], float(a[2]), int(a[3]), int(a[4]), [int(x) for x in a[5:]], [])
    sys.stdout.write("\n".join(lines) + "\n")
