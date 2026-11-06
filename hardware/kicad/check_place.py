"""Courtyard overlap / board-edge check for the current placement (fast loop before routing)."""
import sys, pcbnew
sys.path.insert(0, ".")
import importlib, place, make_pcb
importlib.reload(place)
b = make_pcb.build("tmp_place.kicad_pcb", place.PL)
b = pcbnew.LoadBoard("tmp_place.kicad_pcb")
fps = list(b.GetFootprints())
polys = {}
for fp in fps:
    fp.BuildCourtyardCaches()
    c = fp.GetCourtyard(pcbnew.F_CrtYd)
    if c.OutlineCount() == 0:
        bb = fp.GetBoundingBox(False, False)
        c = pcbnew.SHAPE_POLY_SET(); c.NewOutline()
        for x, y in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())):
            c.Append(x, y)
    polys[fp.GetReference()] = c
refs = list(polys)
bad = 0
allowed = {frozenset(("Q3", "Q5")), frozenset(("Q4", "Q6"))}
for i in range(len(refs)):
    for j in range(i + 1, len(refs)):
        a = pcbnew.SHAPE_POLY_SET(polys[refs[i]]); a.BooleanIntersection(polys[refs[j]], pcbnew.SHAPE_POLY_SET.PM_FAST)
        if a.OutlineCount() and a.Area() > pcbnew.FromMM(0.01) * pcbnew.FromMM(0.01) * 100:
            if frozenset((refs[i], refs[j])) in allowed: continue
            print("OVERLAP", refs[i], refs[j], round(a.Area() / 1e12, 2), "mm2"); bad += 1
# pads outside board
W, H, N = place.BOARD_W / 2, place.BOARD_H / 2, place.NOTCH
def inside(x, y, m):
    x -= make_pcb.OX; y -= make_pcb.OY
    if abs(x) > W - m or abs(y) > H - m: return False
    if abs(x) > W - N - 0 and abs(y) > H - N: 
        return abs(x) <= W - N - m or abs(y) <= H - N - m
    return True
for fp in fps:
    for p in fp.Pads():
        pos = p.GetPosition(); r = pcbnew.ToMM(max(p.GetSize().x, p.GetSize().y)) / 2
        if not inside(pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y), r + 0.4):
            print("EDGE", fp.GetReference(), p.GetNumber(), round(pcbnew.ToMM(pos.x) - make_pcb.OX, 2), round(pcbnew.ToMM(pos.y) - make_pcb.OY, 2)); bad += 1
print("issues:", bad)
