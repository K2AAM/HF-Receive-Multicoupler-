"""Add GND stitching vias (both pours) on a grid, outside every courtyard; drop any that DRC flags."""
import sys, re, pcbnew
sys.path.insert(0, ".")
import place
f = sys.argv[1]; MM = pcbnew.FromMM
b = pcbnew.LoadBoard(f); gnd = b.FindNet("GND")
OX, OY = 150.0, 100.0
W, H, N = place.BOARD_W / 2, place.BOARD_H / 2, place.NOTCH
cy = []
for fp in b.GetFootprints():
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False, False)
    bb.Inflate(MM(0.6)); cy.append(bb)
def inside(x, y):
    m = 1.5
    if abs(x) > W - m or abs(y) > H - m: return False
    if abs(x) > W - N - m and abs(y) > H - N - m: return False
    return True
vias = []
step = 4.0
y = -H
while y <= H:
    x = -W
    while x <= W:
        if inside(x, y):
            p = pcbnew.VECTOR2I(MM(OX + x), MM(OY + y))
            if not any(bb.Contains(p) for bb in cy):
                v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetWidth(MM(0.8)); v.SetDrill(MM(0.4))
                v.SetNet(gnd); b.Add(v); vias.append(v)
        x += step
    y += step
print("candidate vias", len(vias))
for it in range(6):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.WriteDRCReport(b, "/tmp/st.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open("/tmp/st.rpt").read()
    bad = set()
    for blk in txt.split("\n["):
        if blk.startswith("silk") or blk.startswith("lib_"): continue
        for xs, ys in re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): Via", blk):
            bad.add((round(float(xs), 3), round(float(ys), 3)))
        # dangling vias (connected to only one layer's pour fragment) are reported as via_dangling / unconnected
    keep = []
    for v in vias:
        p = v.GetPosition(); k = (round(pcbnew.ToMM(p.x), 3), round(pcbnew.ToMM(p.y), 3))
        if k in bad: b.Remove(v)
        else: keep.append(v)
    print("iter", it, "removed", len(vias) - len(keep)); 
    if len(keep) == len(vias): break
    vias = keep
print("stitching vias kept", len(vias))
b.Save(f)
