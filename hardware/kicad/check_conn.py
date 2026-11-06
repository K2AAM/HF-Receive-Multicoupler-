"""Connectivity / pin-mapping check: simulation netlist (sim/scripts/gen.py, build A)
   vs KiCad schematic netlist (hfmc.net) vs PCB pad nets (hfmc.kicad_pcb).
   Run with KiCad's python (/usr/bin/python3); REPO env var points at the repo root."""
import os, re, sys, subprocess, json
REPO = os.environ.get("REPO", os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
sys.path.insert(0, os.path.join(REPO, "sim", "scripts"))
import gen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design
fail = []
def bad(msg): fail.append(msg); print("FAIL", msg)

# ---------- 1. simulation netlist (build A, real supply, no parasitics)
P = gen.params("A"); P["PAR"] = False; P["SUPPLY"] = "real"
cir = gen.netlist(P, "op")
elems = {}
for ln in cir.splitlines():
    t = ln.split()
    if not t or t[0][0] in "*." or t[0].lower() in ("echo", "op", "run"): continue
    if t[0][0].upper() in "RCLDQVBI": elems[t[0]] = t[1:4] if t[0][0].upper() == "Q" else t[1:3]
WIRES = re.compile(r"^(RIN1|LIN1|RBNE|LBNE|RBPE|LBPE|LEN|LEP|LFB|LEF|LEG|RO\dE|LO\dE|LS\d|RLF\d|RL4DCR|R20E|R22E|RU1E|RSRC)$")
par = {}
def find(a):
    while par.get(a, a) != a: a = par[a]
    return a
def union(a, b):
    a, b = find(a), find(b)
    if a != b: par[max(a, b)] = min(a, b) if "0" not in (a, b) else "0"
for k, nodes in elems.items():
    if WIRES.match(k): union(*nodes[:2])
union("0", "0")
# behavioural LM317 internals: pass element from UIN to UPI, then RZU/LZU to UOUT (treat UPI..UOUT as U1 OUT)
for a, b in (("UPI", "UPJ"), ("UPJ", "UPK"), ("UPK", "UOUT")): union(a, b)
SN = lambda n: find(n)

# ---------- 2. sim element -> KiCad ref, and terminal order
SUPPLY = {"D5": "D5", "C20": "C20", "C20B": "C17", "D6": "D6", "D7": "D7", "R10": "R23", "R11": "R24",
          "C21": "C21", "CU1O": "C23", "L4": "L4", "RDMP": "R25", "C22": "C22", "C22B": "C18"}
bysim = {p["gen"]: p for p in design.P if p.get("gen")}
for s, r in SUPPLY.items():
    bysim[s] = next(p for p in design.P if p["ref"] == r)
def kpins(p, simname):
    pre = simname[0].upper()
    if pre == "Q": return ["3", "2", "1"]          # C, B, E  (onsemi TO-92: 1=E 2=B 3=C)
    if pre == "D": return ["2", "1"]               # anode, cathode (KiCad D: 1=K, 2=A)
    return ["1", "2"]

# ---------- 3. build node map sim->KiCad and check every mapped element
nmap = {SN("0"): "GND"}
checked = 0
for s, p in sorted(bysim.items()):
    if s not in elems: bad(f"{s}: in design.py but not in sim netlist"); continue
    snodes = [SN(n) for n in elems[s]]
    kp = kpins(p, s); knets = [p["pins"][k] for k in kp]
    pairs = list(zip(snodes, knets))
    if s[0].upper() in "RCL" and s not in ("C14", "C15", "C20", "C21", "C22", "CU1O", "CRM", "CRMP"):
        # unpolarised two-terminal: accept either orientation
        if not all(nmap.get(a, b) == b for a, b in pairs):
            pairs = list(zip(snodes, knets[::-1]))
    for a, b in pairs:
        if nmap.setdefault(a, b) != b: bad(f"{s}->{p['ref']}: sim node {a} maps to {nmap[a]} and {b}")
    checked += 1
inv = {}
for a, b in nmap.items():
    if inv.setdefault(b, a) != a: bad(f"KiCad net {b} corresponds to two sim nodes {inv[b]} and {a}")
print(f"sim elements checked against design: {checked}; node map size {len(nmap)}")

# U1 (behavioural model in sim): IN/OUT/ADJ by role
u1 = next(p for p in design.P if p["ref"] == "U1")
for pin, simnode in (("3", "UIN"), ("2", "UOUT"), ("1", "UADJ")):
    if nmap.get(SN(simnode)) != u1["pins"][pin]: bad(f"U1 pin {pin} net {u1['pins'][pin]} != sim {simnode}")

# ---------- 4. schematic netlist (kicad-cli export) vs design.py, incl. pin functions
txt = open("hfmc.net").read()
schnet = {}
pinfn = {}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)(.*?)\)\)\s*(?=\(net|\)\s*\)\s*$|$)', txt, re.S):
    name = m.group(1).lstrip("/")
    for r, pn, fn in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "([^"]*)"\))?', m.group(2)):
        schnet[(r, pn)] = name; pinfn[(r, pn)] = fn
for p in design.P:
    for pn, n in p["pins"].items():
        if schnet.get((p["ref"], pn)) != n: bad(f"schematic {p['ref']}.{pn}: {schnet.get((p['ref'], pn))} != design {n}")
EXP = {"Q": {"1": "E", "2": "B", "3": "C"}, "D": {"1": "K", "2": "A"}, "U": {"1": "ADJ", "2": "VO", "3": "VI"}}
for (r, pn), fn in pinfn.items():
    e = EXP.get(r[0], {}).get(pn)
    if r.startswith("GDT"): continue
    if e and fn != e: bad(f"schematic pin function {r}.{pn} = {fn!r}, expected {e}")
print(f"schematic pins checked: {len(schnet)}")

# ---------- 5. PCB pad nets vs schematic
import pcbnew
b = pcbnew.LoadBoard("hfmc.kicad_pcb")
npads = 0
for fp in b.GetFootprints():
    for pad in fp.Pads():
        if not pad.GetNumber(): continue
        npads += 1
        want = schnet.get((fp.GetReference(), pad.GetNumber()))
        if pad.GetNetname() != want: bad(f"PCB {fp.GetReference()}.{pad.GetNumber()}: {pad.GetNetname()} != schematic {want}")
print(f"PCB pads checked: {npads}")

# ---------- 6. what is deliberately not 1:1
unmapped_sim = sorted(k for k in elems if not WIRES.match(k) and k not in bysim)
extra_kicad = sorted(p["ref"] for p in design.P if not p.get("gen") and p["ref"] not in SUPPLY.values() and p["ref"] != "U1")
print("sim-only elements (sources, loads, behavioural regulator, ESR/loss models):", " ".join(unmapped_sim))
print("KiCad-only parts (connectors, protection, test points, holes, extra bypass):", " ".join(extra_kicad))
print("RESULT:", "PASS" if not fail else f"FAIL ({len(fail)})")
sys.exit(1 if fail else 0)
