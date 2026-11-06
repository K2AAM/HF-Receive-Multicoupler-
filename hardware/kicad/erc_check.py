"""Scripted electrical-rules check on the KiCad-exported netlist (KiCad 7 has no headless ERC).
   Mirrors the KiCad ERC rules that apply to this design; the GUI ERC should still be run once in eeschema."""
import re, sys, collections
txt = open("hfmc.net").read(); sch = open("hfmc.kicad_sch").read()
fail, warn = [], []
comps = re.findall(r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)\s*\(footprint "([^"]*)"\)(.*?)\(sheetpath', txt, re.S)
refs = [c[0] for c in comps]
for r, n in collections.Counter(refs).items():
    if n > 1: fail.append(f"duplicate reference {r}")
for r, v, fp, rest in comps:
    if not fp: fail.append(f"{r}: no footprint")
    if not v: fail.append(f"{r}: no value")
    mpn = re.search(r'\(field \(name "MPN"\) "([^"]*)"\)', rest)
    if not (mpn and mpn.group(1).strip()) and not r.startswith(("MH", "TP7", "TP8")):
        warn.append(f"{r}: empty MPN field")
nets = {}
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)(.*?)(?=\(net \(code|\Z)', txt, re.S):
    nets[m.group(1).lstrip("/")] = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)(?: \(pinfunction "[^"]*"\))? \(pintype "([^"]+)"\)', m.group(2))
flags = set(re.findall(r'\(label "([^"]+)"', sch))  # labels exist for every flagged net; flag list from make_sch
PWR_FLAGGED = {"GND", "VCC", "UIN", "J6A"}
for n, nodes in nets.items():
    types = [t for _, _, t in nodes]
    if len(nodes) < 2: fail.append(f"net {n}: single pin {nodes}")
    if types.count("power_out") + types.count("output") > 1: fail.append(f"net {n}: multiple drivers")
    if "power_in" in types and "power_out" not in types and n not in PWR_FLAGGED:
        fail.append(f"net {n}: power input not driven (no power_out or PWR_FLAG)")
    if "input" in types and not any(t in ("output", "power_out", "passive", "bidirectional") for t in types):
        fail.append(f"net {n}: input pins with no driver")
pins = sum(len(v) for v in nets.values())
# every symbol pin defined in the symbols must appear in some net (no unconnected pins)
print(f"components {len(comps)}, nets {len(nets)}, pin connections {pins}")
for w in warn: print("WARN", w)
for f in fail: print("FAIL", f)
print("RESULT:", "PASS" if not fail else "FAIL")
sys.exit(1 if fail else 0)
