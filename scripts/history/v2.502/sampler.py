from fontTools.pens.basePen import BasePen
class Sampler(BasePen):
    def __init__(self, gs):
        super().__init__(gs); self.pts = []; self.cur = None
    def _moveTo(self, p): self.cur = p; self.pts.append(p)
    def _lineTo(self, p): self.cur = p; self.pts.append(p)
    def _curveToOne(self, a, b, c):
        p0 = self.cur
        for i in range(1, 13):
            t = i / 12; u = 1 - t
            self.pts.append((u**3*p0[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0],
                             u**3*p0[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
        self.cur = c
    def _qCurveToOne(self, a, b):
        p0 = self.cur
        for i in range(1, 9):
            t = i / 8; u = 1 - t
            self.pts.append((u*u*p0[0] + 2*u*t*a[0] + t*t*b[0], u*u*p0[1] + 2*u*t*a[1] + t*t*b[1]))
        self.cur = b

