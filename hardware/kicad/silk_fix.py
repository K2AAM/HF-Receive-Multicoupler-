"""Iteratively move reference designators off pads / silk / each other, using KiCad's own DRC as the judge."""
import sys, re, pcbnew
f = sys.argv[1]
MM = pcbnew.FromMM
def cands(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    c = bb.Centre(); w, h = bb.GetWidth(), bb.GetHeight()
    vert = h > w * 1.3
    g = MM(0.7)
    out = [(c.x, c.y, 90 if vert else 0)]
    out += [(c.x, bb.GetTop() - g, 0), (c.x, bb.GetBottom() + g, 0),
            (bb.GetLeft() - g, c.y, 90), (bb.GetRight() + g, c.y, 90),
            (bb.GetLeft() - g, c.y, 0), (bb.GetRight() + g, c.y, 0)]
    q = [(bb.GetLeft() + w // 4, bb.GetTop() - g, 0), (bb.GetRight() - w // 4, bb.GetTop() - g, 0),
         (bb.GetLeft() + w // 4, bb.GetBottom() + g, 0), (bb.GetRight() - w // 4, bb.GetBottom() + g, 0)]
    sp = []
    for rr in (1.5, 2.5, 3.5, 4.5):
        for dx, dy in ((0,-1),(0,1),(-1,0),(1,0),(-1,-1),(1,-1),(-1,1),(1,1)):
            sp.append((c.x + dx * MM(rr), c.y + dy * MM(rr), 0))
    return out + q + sp
def apply(fp, k):
    x, y, a = cands(fp)[k]
    r = fp.Reference(); r.SetPosition(pcbnew.VECTOR2I(int(x), int(y)))
    r.SetTextAngle(pcbnew.EDA_ANGLE(a, pcbnew.DEGREES_T))
def offenders(rep):
    bad = set()
    for blk in open(rep).read().split("\n["):
        if not blk.startswith("silk"): continue
        bad |= set(re.findall(r"Reference '([^']+)'", blk))
    return bad
b = pcbnew.LoadBoard(f)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
for fp in fps.values():                       # stray library texts (diode 'K') duplicate the silk band
    for it in fp.GraphicalItems():
        if isinstance(it, pcbnew.FP_TEXT) and it.GetLayer() == pcbnew.F_SilkS: it.SetVisible(False)
state = {r: 0 for r in fps if not r.startswith("MH")}
for r in state: apply(fps[r], 0)
for it in range(40):
    b.Save(f); pcbnew.WriteDRCReport(b, "/tmp/silk.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
    bad = offenders("/tmp/silk.rpt") & set(state)
    print("iter", it, "offenders", len(bad), sorted(bad))
    if not bad: break
    for r in sorted(bad):
        state[r] += 1
        if state[r] >= len(cands(fps[r])):
            state[r] = 0; fps[r].Reference().SetVisible(False) if it > 38 else None
        apply(fps[r], state[r])
b.Save(f)
# stubborn ones: try a fine spiral of positions one by one, keep the first that clears the check
import math
left = offenders("/tmp/silk.rpt") & set(state)
b.Save(f); pcbnew.WriteDRCReport(b, "/tmp/silk.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
left = offenders("/tmp/silk.rpt") & set(state)
for r in sorted(left):
    fp = fps[r]; c = fp.GetCourtyard(pcbnew.F_CrtYd).BBox().Centre(); done = False
    for rr in [x * 0.5 for x in range(2, 16)]:
        for k in range(16):
            for ang in (0, 90):
                a = 2 * math.pi * k / 16
                ref = fp.Reference(); ref.SetVisible(True)
                ref.SetPosition(pcbnew.VECTOR2I(int(c.x + MM(rr) * math.cos(a)), int(c.y + MM(rr) * math.sin(a))))
                ref.SetTextAngle(pcbnew.EDA_ANGLE(ang, pcbnew.DEGREES_T))
                pcbnew.WriteDRCReport(b, "/tmp/silk.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
                if r not in offenders("/tmp/silk.rpt"): done = True; break
            if done: break
        if done: break
    print("placed" if done else "could not place", r)
b.Save(f)
