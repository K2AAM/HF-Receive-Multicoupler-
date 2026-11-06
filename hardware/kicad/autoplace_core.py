"""Simulated-annealing placement of the gain stage + diamond buffer (the parts that set node X, the base nodes,
the feedback loop and the output node). Everything else (input, LPF, ports, supply, holes) stays where place.py
puts it. Cost = weighted half-perimeter wire length per net (weights favour X, OUT, base and feedback nodes);
courtyard overlap is forbidden. Thermal pairs move as rigid units (flat faces 3.75 mm apart).
Writes place_core.json, which place.py merges over its defaults. Run with KiCad's python."""
import sys, json, math, random
sys.path.insert(0, ".")
import pcbnew, design, place
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
OX, OY = 150.0, 100.0
W = dict(X=12, OUT=6, BN=5, BP=5, N4=4, FB=4, EN=3, EP=3, D1=3, D2=3, E2A=3, E3A=3, EF=3, EG=3, VCF=2, LX=1.5,
         XO1=2, XO2=2, XO3=2, XO4=2, RM=0.4, RMP=0.4, VCC=0.6, GND=0.0)
CORE = ["Q1", "Q2", "PA", "PB", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "C2", "C3", "C8", "C9",
        "C14", "C15", "C24", "C25", "C26", "C16", "R12", "R13", "R14", "R15", "R16", "R17", "R18",
        "TP2", "TP3", "TP4", "TP5", "TP6", "C19"]
# local-bypass and bias-cap attractions: (cap, cap pad, device, device pad, weight per mm)
ATTR = [("C16", "1", "Q5", "3", 8), ("C26", "1", "Q4", "3", 8), ("C24", "1", "R3", "1", 5), ("C24", "1", "R11", "2", 3),
        ("C25", "1", "R12", "1", 6), ("C19", "1", "R16", "1", 4), ("C15", "2", "R9", "2", 2), ("C14", "1", "R6", "2", 2),
        # keep the X node a tight cluster: both collectors, both diamond bases, RF, CLX, bias feeds, test point
        ("Q1", "3", "Q2", "3", 10), ("Q3", "2", "Q1", "3", 10), ("Q4", "2", "Q2", "3", 10), ("Q3", "2", "Q4", "2", 6),
        ("R4", "1", "Q1", "3", 6), ("C9", "1", "Q2", "3", 4), ("R6", "1", "Q1", "3", 4), ("R9", "1", "Q2", "3", 4),
        ("TP2", "1", "Q1", "3", 3), ("R17", "1", "Q5", "1", 4), ("R18", "1", "Q6", "1", 4), ("R17", "2", "R18", "2", 6)]
PAIRS = {"PA": ("Q3", "Q5"), "PB": ("Q4", "Q6")}
REGION = (-51.5, 51.5, -38.5, 38.5)       # board edge less 0.5 mm; corner notches are added as fixed boxes
parts = {p["ref"]: p for p in design.P}
# ---- geometry per footprint & rotation (relative to origin): courtyard box + pad offsets
geo = {}
def load(fpid):
    lib, name = fpid.split(":")
    path = "hfmc.pretty" if lib == "hfmc" else f"/usr/share/kicad/footprints/{lib}.pretty"
    return pcbnew.FootprintLoad(path, name)
def rotp(x, y, rot):
    t = math.radians(rot); c, sn = round(math.cos(t)), round(math.sin(t))
    return x * c + y * sn, -x * sn + y * c
def g(ref, rot):
    k = (parts[ref]["fp"], rot)
    if k not in geo:
        if (parts[ref]["fp"], "base") not in geo:
            fp = load(parts[ref]["fp"]); c = fp.GetCourtyard(pcbnew.F_CrtYd)
            bb = c.BBox() if c.OutlineCount() else fp.GetBoundingBox(False, False)
            box = tuple(pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetRight(), bb.GetTop(), bb.GetBottom()))
            pads = [(pd.GetNumber(), pcbnew.ToMM(pd.GetPosition().x), pcbnew.ToMM(pd.GetPosition().y)) for pd in fp.Pads() if pd.GetNumber()]
            geo[(parts[ref]["fp"], "base")] = (box, pads)
        box, pads = geo[(parts[ref]["fp"], "base")]
        cs = [rotp(x, y, rot) for x in box[:2] for y in box[2:]]
        geo[k] = ((min(c[0] for c in cs), max(c[0] for c in cs), min(c[1] for c in cs), max(c[1] for c in cs)),
                  [(n, *rotp(x, y, rot)) for n, x, y in pads])
    return geo[k]
# units: name -> list of (ref, dx, dy, rot_offset)
def members(u, rot):
    if u in PAIRS:
        a, b = PAIRS[u]
        return [(a, 0, 0, 0), (b, 2.54, 3.75, 180)] if rot == 0 else [(a, 0, 0, 180), (b, -2.54, -3.75, 0)]
    return [(u, 0, 0, 0)]
state = {}
for u in CORE:
    if u in PAIRS: x, y, r = place.PL[PAIRS[u][0]]; state[u] = [x, y, 0]
    else: state[u] = list(place.PL[u])
fixed = [r for r in place.PL if r not in CORE and r not in sum(PAIRS.values(), ())]
def boxes_pads(u, s):
    out = []
    for ref, dx, dy, ro in members(u, s[2]):
        box, pads = g(ref, (s[2] + ro) % 360 if u not in PAIRS else ro)
        x, y = s[0] + dx, s[1] + dy
        out.append((ref, (box[0] + x, box[1] + x, box[2] + y, box[3] + y), [(n, px + x, py + y) for n, px, py in pads]))
    return out
FB = []; FP = {}
for r in fixed:
    x, y, rot = place.PL[r]; box, pads = g(r, rot)
    FB.append((box[0] + x, box[1] + x, box[2] + y, box[3] + y))
    FP[r] = [(n, px + x, py + y) for n, px, py in pads]
for sx in (-1, 1):
    for sy in (-1, 1):
        FB.append((min(sx * 45.5, sx * 52.5), max(sx * 45.5, sx * 52.5), min(sy * 32.5, sy * 39.5), max(sy * 32.5, sy * 39.5)))
def ov(a, b): return a[0] < b[1] and b[0] < a[1] and a[2] < b[3] and b[2] < a[3]
netpads = {}
for r, pl in FP.items():
    for n, x, y in pl:
        net = parts[r]["pins"][n]
        if W.get(net, 1) > 0: netpads.setdefault(net, {}).setdefault(r, []).append((x, y))
cur = {u: boxes_pads(u, state[u]) for u in CORE}
def setnets(u):
    for ref, box, pads in cur[u]:
        for net in list(netpads):
            netpads[net].pop(ref, None)
        for n, x, y in pads:
            net = parts[ref]["pins"][n]
            if W.get(net, 1) > 0: netpads.setdefault(net, {}).setdefault(ref, []).append((x, y))
for u in CORE: setnets(u)
def hpwl(net):
    pts = [p for l in netpads[net].values() for p in l]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (max(xs) - min(xs) + max(ys) - min(ys)) * W.get(net, 1)
def legal(u):
    for ref, box, pads in cur[u]:
        if box[0] < REGION[0] or box[1] > REGION[1] or box[2] < REGION[2] or box[3] > REGION[3]: return False
        if any(ov(box, f) for f in FB): return False
        for v in CORE:
            if v == u: continue
            for _, b2, _ in cur[v]:
                if ov(box, b2): return False
    return True
nets_of = lambda u: {parts[ref]["pins"][n] for ref, _, pads in cur[u] for n, _, _ in pads if W.get(parts[ref]["pins"][n], 1) > 0}
def ovarea(a, b):
    w = min(a[1], b[1]) - max(a[0], b[0]); h = min(a[3], b[3]) - max(a[2], b[2])
    return w * h if w > 0 and h > 0 else 0.0
def pen(u):
    p = 0.0
    for ref, box, pads in cur[u]:
        p += max(0, REGION[0] - box[0]) * 10 + max(0, box[1] - REGION[1]) * 10 + max(0, REGION[2] - box[2]) * 10 + max(0, box[3] - REGION[3]) * 10
        p += sum(ovarea(box, f) for f in FB)
        for v in CORE:
            if v == u: continue
            p += sum(ovarea(box, b2) for _, b2, _ in cur[v])
    return p
def totpen(): return sum(pen(u) for u in CORE) / 2
def padpos(ref, num):
    for u in CORE:
        for r, _, pads in cur[u]:
            if r == ref:
                for n, x, y in pads:
                    if n == num: return x, y
    for n, x, y in FP[ref]:
        if n == num: return x, y
def attr():
    return sum(w * math.dist(padpos(a, pa), padpos(c, pc)) for a, pa, c, pc, w in ATTR)
wl = lambda: sum(hpwl(n) for n in netpads) + attr()
print("start wl", round(wl(), 1), "pen", round(totpen(), 2), {n: round(hpwl(n) / max(W.get(n, 1), 1e-9), 1) for n in ("X", "OUT", "BN", "BP", "N4", "FB")})
T0, T1, N = (float(sys.argv[4]) if len(sys.argv) > 4 else 40.0), 0.02, int(sys.argv[3]) if len(sys.argv) > 3 else 150000
for it in range(N):
    fr = it / N
    T = T0 * (T1 / T0) ** fr; lam = 2.0 + 400.0 * fr ** 2
    u = random.choice(CORE); old = list(state[u]); oldcur = cur[u]
    s2 = list(old)
    r = random.random()
    if r < 0.12 and u not in PAIRS: s2[2] = random.choice([0, 90, 180, 270])
    elif r < 0.15 and u in PAIRS: s2[2] = 180 - s2[2]
    else:
        step = max(0.5, min(15, 4 * T0 ** 0.5) * (1 - fr) ** 2)
        s2[0] = round((s2[0] + random.gauss(0, step)) * 2) / 2; s2[1] = round((s2[1] + random.gauss(0, step)) * 2) / 2
    ns = nets_of(u); b_wl = sum(hpwl(n) for n in ns) + attr(); b_p = pen(u)
    state[u] = s2; cur[u] = boxes_pads(u, s2); setnets(u)
    ns2 = ns | nets_of(u); a_wl = sum(hpwl(n) for n in ns2) + attr(); a_p = pen(u)
    b_wl2 = b_wl + sum(0 for n in ns2 - ns)
    d = (a_wl - b_wl) + lam * (a_p - b_p)
    if not (d <= 0 or random.random() < math.exp(-d / T)):
        state[u] = old; cur[u] = oldcur; setnets(u)
    if it % 25000 == 0: print(it, round(T, 2), round(wl(), 1), round(totpen(), 2), flush=True)
# final legalisation: greedy nudges for any remaining overlap
for rep in range(4000):
    bad = [u for u in CORE if pen(u) > 0]
    if not bad: break
    u = random.choice(bad); old = list(state[u]); oldcur = cur[u]; bp = pen(u)
    s2 = list(old); s2[0] = round((s2[0] + random.uniform(-1.5, 1.5)) * 2) / 2; s2[1] = round((s2[1] + random.uniform(-1.5, 1.5)) * 2) / 2
    state[u] = s2; cur[u] = boxes_pads(u, s2); setnets(u)
    if pen(u) >= bp: state[u] = old; cur[u] = oldcur; setnets(u)
final = wl(); fp_ = totpen()
print("final wl", round(final, 1), "pen", round(fp_, 3), {n: round(hpwl(n) / max(W.get(n, 1), 1e-9), 1) for n in ("X", "OUT", "BN", "BP", "N4", "FB", "D1", "D2", "E3A", "E2A")})
out = {}
for u in CORE:
    for ref, dx, dy, ro in members(u, state[u][2]):
        out[ref] = [state[u][0] + dx, state[u][1] + dy, (ro if u in PAIRS else state[u][2])]
json.dump(dict(wl=final, pen=fp_, PL=out), open(sys.argv[2] if len(sys.argv) > 2 else "place_core.json", "w"), indent=0)
