"""Minimal Specctra SES importer (freerouting output) for KiCad 7 python: adds tracks and vias."""
import re, pcbnew
from libsym import parse
def import_ses(board, path):
    t = parse(open(path).read())
    res = 10.0
    def find(node, key):
        out = []
        if isinstance(node, list):
            if node and node[0] == key: out.append(node)
            for c in node: out += find(c, key)
        return out
    r = find(t, "resolution")
    if r: res = float(r[0][2])          # units per um
    def mm(v): return float(v) / res / 1000.0
    nets = {n.GetNetname(): n for n in board.GetNetsByName().values()} if False else None
    ntrack = nvia = 0
    for net in find(t, "network_out")[0][1:]:
        if not (isinstance(net, list) and net[0] == "net"): continue
        name = net[1].strip('"'); ni = board.FindNet(name)
        for w in find(net, "wire"):
            p = find(w, "path")[0]
            layer = pcbnew.F_Cu if p[1] == "F.Cu" else pcbnew.B_Cu
            width = mm(p[2]); xy = [float(v) for v in p[3:] if not isinstance(v, list)]
            pts = [(xy[i], xy[i + 1]) for i in range(0, len(xy), 2)]
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                tr = pcbnew.PCB_TRACK(board)
                tr.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(mm(x1)), pcbnew.FromMM(-mm(y1))))
                tr.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(mm(x2)), pcbnew.FromMM(-mm(y2))))
                tr.SetWidth(pcbnew.FromMM(width)); tr.SetLayer(layer); tr.SetNet(ni); board.Add(tr); ntrack += 1
        for v in find(net, "via"):
            x, y = mm(v[2]), -mm(v[3])
            vi = pcbnew.PCB_VIA(board); vi.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)))
            vi.SetDrill(pcbnew.FromMM(0.4)); vi.SetWidth(pcbnew.FromMM(0.8)); vi.SetNet(ni)
            vi.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); board.Add(vi); nvia += 1
    return ntrack, nvia
