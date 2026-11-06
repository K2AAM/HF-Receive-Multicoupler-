"""Layout metrics for the review notes: copper per layer, RF branch lengths, bypass distances, inductor geometry."""
import math, json, collections, pcbnew
b = pcbnew.LoadBoard("hfmc.kicad_pcb"); MM = pcbnew.ToMM
def pad(r, n):
    return [p for p in b.FindFootprintByReference(r).Pads() if p.GetNumber() == n][0].GetPosition()
def d(a, c): return round(MM(math.hypot(a.x - c.x, a.y - c.y)), 1)
rep = collections.OrderedDict()
L = collections.defaultdict(float); bnets = collections.defaultdict(float)
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA": continue
    L[t.GetLayerName()] += MM(t.GetLength())
    if t.GetLayerName() == "B.Cu": bnets[t.GetNetname()] += MM(t.GetLength())
rep["track_mm_per_layer"] = {k: round(v, 1) for k, v in L.items()}
rep["B.Cu_tracks_by_net_mm"] = {k: round(v, 1) for k, v in bnets.items()}
rep["gnd_stitching_vias"] = sum(1 for t in b.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == "GND")
net_len = collections.defaultdict(float)
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA": net_len[t.GetNetname()] += MM(t.GetLength())
rep["port_branches_mm (XOk, Pk)"] = {k: (round(net_len[f"XO{k}"], 1), round(net_len[f"P{k}"], 1)) for k in range(1, 5)}
rep["RS_to_BNC_centre_pin_mm"] = {rs: d(pad(rs, "2"), pad(j, "1")) for rs, j in (("R19", "J2"), ("R20", "J3"), ("R21", "J4"), ("R22", "J5"))}
rep["key_node_track_mm"] = {n: round(net_len[n], 1) for n in ("X", "OUT", "N4", "FB", "BN", "BP", "IN", "N1")}
# bypass: (cap, cap pad on rail, device, device pad)
BY = [("C16", "1", "Q5", "3", "VCF at Q5 (doc Q2) collector"), ("C26", "1", "Q4", "3", "VCC at Q4 (doc Q3A) collector"),
      ("C24", "1", "R3", "1", "VCC at RE2"), ("C24", "1", "R11", "2", "VCC at R4 (doc)"), ("C25", "1", "R12", "1", "VCC at RPU"),
      ("C19", "1", "R16", "1", "VCC at RC"), ("C15", "1", "R11", "2", "CRMP + at VCC"), ("C17", "1", "U1", "3", "U1 IN"),
      ("C23", "1", "U1", "2", "U1 OUT"), ("C21", "1", "U1", "1", "U1 ADJ")]
rep["bypass_pad_to_device_pad_mm"] = {f"{c}->{dev}.{dp} ({what})": d(pad(c, cp), pad(dev, dp)) for c, cp, dev, dp, what in BY}
ind = {}
for r in ("L1", "L2", "L3"):
    f = b.FindFootprintByReference(r); p = f.GetPosition()
    ind[r] = (MM(p.x) - 150, MM(p.y) - 100, f.GetOrientationDegrees())
def ctr(r):
    a, c = pad(r, "1"), pad(r, "2"); return ((MM(a.x) + MM(c.x)) / 2, (MM(a.y) + MM(c.y)) / 2)
rep["LPF_inductors"] = {r: dict(axis_deg=round(ind[r][2]) % 180, centre=tuple(round(v, 1) for v in ctr(r))) for r in ind}
rep["LPF_centre_spacing_mm"] = {f"{a}-{c}": round(math.dist(ctr(a), ctr(c)), 1) for a, c in (("L1", "L2"), ("L2", "L3"), ("L1", "L3"))}
rep["GDT_gnd_pad_to_J1_braid_pad_mm"] = d(pad("GDT1", "3"), pad("J1", "2"))
rep["GDT_gnd_pad_to_MH1_mm"] = d(pad("GDT1", "3"), pad("MH1", "1"))
json.dump(rep, open("layout_report.json", "w"), indent=1)
for k, v in rep.items(): print(k, v)
