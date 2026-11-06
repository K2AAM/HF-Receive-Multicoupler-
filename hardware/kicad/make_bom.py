"""Prototype BOM (build A) from design.py: grouped by MPN + value + footprint, plus off-board items."""
import csv, collections
import design
H = {"R60EI": "18 x 11 x 19.1 mm, 15 mm pitch", "R82CC4470": "7.2 x 7.2 x 13 mm, 5 mm pitch", "R82CC4220": "7.2 x 6 x 11 mm, 5 mm pitch",
     "C320C": "5.08 x 3.18, H 7.36 max, 2.54 mm", "C315C": "3.81 x 2.54, H 4.66 max, 2.54 mm", "C325C": "5.08 x 3.18, H 7.62 max, 2.54 or 5.08 mm",
     "RLB0914": "8.7 dia x 13 mm max, 5 mm pitch", "RXEF030": "7.4 x 3.0, H 12.7 max, 5.1 mm", "EEU-FR": "8 x 11.5, 3.5 mm pitch",
     "ECA-1EM100": "5 x 11, 2 mm pitch", "2027-09": "8 dia x 6 axial", "031-5431": "R/A PCB bulkhead, rear mount"}
groups = collections.OrderedDict()
for p in design.P:
    if p["ref"].startswith("MH"): continue
    k = (p["mpn"], p["value"], p["fp"])
    groups.setdefault(k, []).append(p)
def refkey(r):
    import re
    m = re.match(r"([A-Z]+)(\d+)", r); return (m.group(1), int(m.group(2)))
rows = []
for (mpn, val, fp), ps in groups.items():
    refs = sorted((p["ref"] for p in ps), key=refkey)
    docs = [p["doc"] for p in sorted(ps, key=lambda p: refkey(p["ref"]))]
    size = next((v for k, v in H.items() if k in mpn), "")
    notes = "; ".join(sorted({p["note"] for p in ps if p.get("note") and not p["note"].startswith(("C20B", "C22B"))}))
    rows.append([" ".join(refs), " ".join(d for d, r in zip(docs, refs) if d != r), len(ps), val, mpn, fp, size, notes])
rows.sort(key=lambda r: refkey(r[0].split()[0]))
EXTRA = [
 ["(J1 panel)", "", 1, "BNC jack, front-mount bulkhead", "Amphenol RF 031-221-RFX", "panel, left end wall", "27.0 mm long, 12.7 hex nut, max panel 3.2", "Input connector; RG-316 pigtail to J1 pads. D-hole 11.1 / 10.3 flat (Amphenol type U, confirm on drawing). Fit after the PCB"],
 ["(J1 cable)", "", 1, "RG-316 coax, ~60 mm", "any RG-316 (e.g. Belden 83284)", "", "", "Centre to J1 pad 1, braid to J1 pads 2"],
 ["(J6 panel)", "", 1, "DC power jack 2.1 mm (2.0 mm pin)", "Switchcraft 722A", "panel, back wall", "20.8 mm long, 5/16-32 bushing, solder lugs", "Centre positive. Wire to J6 pads (1 = +13.8 V, 2 = GND). D-hole 8.00 / 7.37 flat (confirm on drawing). Fit after the PCB"],
 ["MH1-MH5", "", 5, "M3 x 6 mm hex spacer, brass, female-female, 5 mm hex", "Wurth 970060354", "MountingHole_3.2mm_M3_Pad_Via", "", "Bonds board GND to the box floor at every hole"],
 ["MH1-MH5", "", 10, "M3 x 5 pan-head screw, stainless", "any ISO 7045 M3 x 5", "", "", "5 on top through the PCB, 5 from below through the dia 4.2 floor holes"],
 ["MH1-MH5", "", 10, "M3 flat washer (DIN 125 3.2)", "any", "", "", "Under each screw head; the floor ones bridge the oversize holes"],
 ["J2-J5", "", 4, "M12 flat washer, steel, ID 13 / OD 20 / t 2 (DIN 433)", "any DIN 433 M12 zinc-plated", "", "", "Outside, under the supplied lock washer and nut: bridges the 12.9 x 15.5 wall slot"],
 ["Q3/Q5, Q4/Q6", "Q2A/Q2, Q3A/Q3", 1, "thermally conductive epoxy or cyanoacrylate + heat-shrink", "e.g. Arctic Silver thermal adhesive", "", "", "Glue the flat faces of each pair together"],
 ["U1", "", 1, "M3 x 8 nylon screw + nut (optional)", "any nylon M3", "", "", "Tab is VOUT; do not use a metal screw"],
 ["Enclosure", "", 1, "Hammond 1590C die-cast aluminium, natural", "Hammond 1590C", "", "119.5 x 94 x 56.5 mm with lid (inside 52.25 high)", "Machine and drill per hardware/kicad/drill_drawing_1590C.pdf; 1590CBK (black) needs the coating removed at spacer seats and BNC strips"],
]
with open("BOM_prototype_A.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["KiCad refs", "Doc/sim refs (if different)", "Qty", "Value", "Manufacturer part", "KiCad footprint", "Body / pitch (from datasheet)", "Notes"])
    w.writerows(rows); w.writerows(EXTRA)
print(len(rows), "PCB lines,", sum(r[2] for r in rows), "PCB parts")
