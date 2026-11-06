"""Build hfmc.kicad_pcb from design.py + place.py (run with KiCad's python: /usr/bin/python3)."""
import sys, pcbnew
sys.path.insert(0, ".")
import design, place
OX, OY = 150.0, 100.0
def V(x, y): return pcbnew.VECTOR2I(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
LIBROOT = "/usr/share/kicad/footprints"
def load(fpid):
    lib, name = fpid.split(":")
    path = "hfmc.pretty" if lib == "hfmc" else f"{LIBROOT}/{lib}.pretty"
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None: raise RuntimeError(fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp
def tidy_silk(fp):
    """Small reference centred on the part body (inside its silk outline), value on F.Fab only."""
    ref = fp.Reference()
    if fp.GetReference().startswith("MH"):
        ref.SetVisible(False); return
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False, False)
    c = bb.Centre()
    ref.SetPosition(c)
    sz = 0.8
    ref.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(sz), pcbnew.FromMM(sz)))
    ref.SetTextThickness(pcbnew.FromMM(0.12))
    w, h = bb.GetWidth(), bb.GetHeight()
    ref.SetTextAngle(pcbnew.EDA_ANGLE(90 if h > w * 1.3 else 0, pcbnew.DEGREES_T))
    fp.Value().SetLayer(pcbnew.F_Fab); fp.Value().SetVisible(True)
def design_pin(ref, num):
    return next(p for p in design.P if p["ref"] == ref)["pins"][num]
def build(outfile="hfmc.kicad_pcb", placement=None):
    PL = placement or place.PL
    b = pcbnew.BOARD()
    ds = b.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.2); ds.m_MinClearance = pcbnew.FromMM(0.2)
    ds.m_ViasMinSize = pcbnew.FromMM(0.6); ds.m_MinThroughDrill = pcbnew.FromMM(0.3)
    ds.m_HoleClearance = pcbnew.FromMM(0.25); ds.m_CopperEdgeClearance = pcbnew.FromMM(0.4)
    ds.SetBoardThickness(pcbnew.FromMM(1.6))
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(pcbnew.FromMM(0.2)); nc.SetTrackWidth(pcbnew.FromMM(0.4))
    nc.SetViaDiameter(pcbnew.FromMM(0.8)); nc.SetViaDrill(pcbnew.FromMM(0.4))
    nets = {}
    for p in design.P:
        for n in p["pins"].values():
            if n not in nets:
                ni = pcbnew.NETINFO_ITEM(b, n); b.Add(ni); nets[n] = ni
    for p in design.P:
        fp = load(p["fp"])
        fp.SetReference(p["ref"]); fp.SetValue(p["value"])
        x, y, r = PL[p["ref"]]
        fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(r)
        for k, v in (("MPN", p["mpn"]), ("DocRef", p["doc"]), ("SimName", p.get("gen") or "")):
            fp.SetProperty(k, v)
        b.Add(fp)
        tidy_silk(fp)
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num == "": continue
            if num not in p["pins"]:
                raise RuntimeError(f"{p['ref']} pad {num} has no net")
            pad.SetNet(nets[p["pins"][num]])
    # U1 lies tab-down; the tab is at VOUT, so keep F.Cu (pour, tracks, vias) out from under body + tab
    import math
    u1 = b.FindFootprintByReference("U1")
    th = math.radians(u1.GetOrientationDegrees()); P0 = u1.GetPosition()
    def xf(x, y):
        X = x * math.cos(th) + y * math.sin(th); Y = -x * math.sin(th) + y * math.cos(th)
        return pcbnew.VECTOR2I(P0.x + pcbnew.FromMM(X), P0.y + pcbnew.FromMM(Y))
    p3 = [p for p in u1.Pads() if p.GetNumber() == "3"][0].GetPosition(); chk = xf(5.08, 0)
    assert abs(p3.x - chk.x) < 1000 and abs(p3.y - chk.y) < 1000, "U1 transform"
    ka = pcbnew.ZONE(b); ka.SetIsRuleArea(True); ka.SetLayer(pcbnew.F_Cu)
    ka.SetDoNotAllowCopperPour(True); ka.SetDoNotAllowTracks(True); ka.SetDoNotAllowVias(True)
    ka.SetDoNotAllowPads(False); ka.SetDoNotAllowFootprints(False); ka.SetZoneName("U1_TAB_KEEPOUT")
    o = ka.Outline(); o.NewOutline()
    for x, y in ((-3.0, -20.0), (8.1, -20.0), (8.1, -3.3), (-3.0, -3.3)): o.Append(xf(x, y))
    b.Add(ka)
    # pre-routed, locked port branches (C1x -> RSk -> BNC centre pin): straight and mirror-symmetric, so the
    # autorouter cannot make one port's branch longer than the others
    def padpos(ref, num):
        return [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0].GetPosition()
    for c, r, j in (("C10", "R19", "J2"), ("C11", "R20", "J3"), ("C12", "R21", "J4"), ("C13", "R22", "J5")):
        for (ra, pa), (rb, pb) in (((c, "2"), (r, "1")), ((r, "2"), (j, "1"))):
            t = pcbnew.PCB_TRACK(b); t.SetStart(padpos(ra, pa)); t.SetEnd(padpos(rb, pb)); t.SetLayer(pcbnew.F_Cu)
            t.SetWidth(pcbnew.FromMM(0.5)); t.SetNet(nets[design_pin(ra, pa)]); t.SetLocked(True); b.Add(t)
    # board outline with corner notches for the enclosure bosses
    W, H, N = place.BOARD_W / 2, place.BOARD_H / 2, place.NOTCH
    pts = [(-W + N, -H), (W - N, -H), (W - N, -H + N), (W, -H + N), (W, H - N), (W - N, H - N), (W - N, H),
           (-W + N, H), (-W + N, H - N), (-W, H - N), (-W, -H + N), (-W + N, -H + N)]
    for i in range(len(pts)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(V(*pts[i])); s.SetEnd(V(*pts[(i + 1) % len(pts)])); s.SetWidth(pcbnew.FromMM(0.1)); b.Add(s)
    b.Save(outfile)
    return b
if __name__ == "__main__":
    build()
    print("ok")
