import re, sys
s = open(sys.argv[1]).read()
POWER = ["VCC", "UIN", "UOUT", "J6A", "J6B", "L4B", "VCF"]
m = re.search(r'\(class kicad_default "" (.*?)\n      \(circuit', s, re.S)
nets = m.group(1).split()
sig = [n for n in nets if n not in POWER and n != "GND"]
def cls(name, ns, w, clr=250.1):
    return (f'    (class {name} {" ".join(ns)}\n      (circuit\n        (use_via Via[0-1]_800:400_um)\n      )\n'
            f'      (rule\n        (width {w})\n        (clearance {clr})\n      )\n    )\n')
start = s.rfind("    (class kicad_default", 0, m.end()); end = s.find("\n    )\n", m.end()) + 7
new = cls("kicad_default", sig, 400) + cls("power", POWER, 800) + cls("gnd", ["GND"], 800)
s = s[:start] + new + s[end:]
open(sys.argv[2], "w").write(s)
print("signal nets", len(sig))
