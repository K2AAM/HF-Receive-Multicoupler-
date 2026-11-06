"""Write net classes into the KiCad 7 project file (KiCad keeps them there, not in the board)."""
import json, sys
f = sys.argv[1]
d = json.load(open(f))
ns = d["net_settings"]
base = dict(ns["classes"][0])
base.update(clearance=0.2, track_width=0.4, via_diameter=0.8, via_drill=0.4)
pw = dict(base); pw.update(name="Power", clearance=0.2, track_width=0.8)
ns["classes"] = [base, pw]
ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in
                           ["VCC", "UIN", "UOUT", "J6A", "J6B", "L4B", "VCF"]]
json.dump(d, open(f, "w"), indent=2)
print("net classes:", [c["name"] for c in ns["classes"]])
