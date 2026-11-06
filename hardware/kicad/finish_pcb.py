"""Import the freerouting session, add ground pours on both layers + stitching vias, fill, DRC report."""
import sys, pcbnew
sys.path.insert(0, ".")
import make_pcb, place
IN, SES, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
b = pcbnew.LoadBoard(IN)
import ses_import
ok = ses_import.import_ses(b, SES)
print("ses import", ok)
gnd = b.FindNet("GND")
def V(x, y): return make_pcb.V(x, y)
W, H, N = place.BOARD_W / 2, place.BOARD_H / 2, place.NOTCH
pts = [(-W + N, -H), (W - N, -H), (W - N, -H + N), (W, -H + N), (W, H - N), (W - N, H - N), (W - N, H),
       (-W + N, H), (-W + N, H - N), (-W, H - N), (-W, -H + N), (-W + N, -H + N)]
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd)
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(V(x, y))
    z.SetLocalClearance(pcbnew.FromMM(0.3)); z.SetMinThickness(pcbnew.FromMM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(pcbnew.FromMM(0.4)); z.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.6))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetZoneName("GND_" + ("F" if layer == pcbnew.F_Cu else "B"))
    b.Add(z)
b.Save(OUT)
# GND pads where routing leaves room for only one thermal spoke on a pour: connect those pads solid to the pours
# (found with KiCad's own DRC, so the list follows the routing)
import re
b = pcbnew.LoadBoard(OUT)
for t in b.GetTracks(): t.SetLocked(False)
for rep in range(3):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.WriteDRCReport(b, "/tmp/starved.rpt", pcbnew.EDA_UNITS_MILLIMETRES, True)
    hits = re.findall(r"PTH pad (\S+) \[GND\] of (\S+)", "\n".join(blk for blk in open("/tmp/starved.rpt").read().split("\n[") if blk.startswith("starved")))
    if not hits: break
    for num, ref in hits:
        for pad in b.FindFootprintByReference(ref).Pads():
            if pad.GetNumber() == num: pad.SetZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    print("solid GND pads:", sorted(set(f"{r}.{n}" for n, r in hits)))
b.Save(OUT)
