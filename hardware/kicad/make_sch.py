"""Generate the KiCad 7 schematic from design.py (label-connected functional blocks)."""
import uuid, math
from libsym import flatten, pins, parse
import design
def U(): return str(uuid.uuid4())
G = 2.54
def snap(v): return round(v / 1.27) * 1.27
ROOT = U()
SECTIONS = [
  ("INPUT PROTECTION & DC BLOCK", ["J1", "GDT1", "C1", "RBL", "D1", "D2", "D3", "D4"]),
  ("7-POLE LOW-PASS FILTER (L1-L3 VNA-selected to +/-3 %)", ["C4", "L1", "C5", "L2", "C6", "L3", "C7"]),
  ("COMPLEMENTARY GAIN STAGE - BUILD A (RE1/RE2 56, RF 220, RL 220)", ["C2", "C3", "Q1N", "Q1P", "RE1", "RE2", "R1A", "R1B", "C14", "R2", "R3A", "R3B", "C15", "R4", "RF", "C8", "C9", "RL"]),
  ("DIAMOND BUFFER (thermal pairs Q3+Q5 and Q4+Q6, flat faces glued)", ["Q2A", "RX1", "RPU", "Q3A", "RX2", "RPD", "RC", "C16", "Q2", "RE3", "Q3", "RE4"]),
  ("OUTPUT PORTS", ["C10", "RS1", "J2", "C11", "RS2", "J3", "C12", "RS3", "J4", "C13", "RS4", "J5"]),
  ("POWER SUPPLY 13.8 V -> +9.8 V (VCC)", ["J6", "F1", "D5", "C20", "C17", "U1", "D6", "D7", "R10", "R11", "C21", "C23", "L4", "RDAMP", "C22", "C18", "C19", "C24", "C25", "C26"]),
  ("TEST POINTS & MOUNTING", ["TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "TP8", "MH1", "MH2", "MH3", "MH4", "MH5"]),
]
parts = {p["doc"]: p for p in design.P}
assert sorted(sum((s[1] for s in SECTIONS), [])) == sorted(parts), set(parts) ^ set(sum((s[1] for s in SECTIONS), []))
libs = {}
for p in design.P:
    libs[p["sym"]] = flatten(*p["sym"])
libs[("power", "GND")] = flatten("power", "GND"); libs[("power", "PWR_FLAG")] = flatten("power", "PWR_FLAG")
def ser(x):
    if isinstance(x, list): return "(" + " ".join(ser(e) for e in x) + ")"
    return x
out = []
def eff(hide=False, just=None):
    j = f" (justify {just})" if just else ""
    return f"(effects (font (size 1.27 1.27)){j}{' hide' if hide else ''})"
items = []
def label(net, x, y, ang):
    rot = {0: 0, 180: 180, 90: 90, 270: 270}[ang]
    just = "left" if rot in (0, 90) else "right"
    items.append(f'(label "{net}" (at {x:.2f} {y:.2f} {rot}) (fields_autoplaced) {eff(just=just)} (uuid {U()}))')
def wire(x1, y1, x2, y2):
    items.append(f'(wire (pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f})) (stroke (width 0) (type default)) (uuid {U()}))')
pwr_n = [0]
def power(kind, x, y, rot):
    pwr_n[0] += 1
    ref = f"#PWR{pwr_n[0]:03d}" if kind == "GND" else f"#FLG{pwr_n[0]:03d}"
    items.append(f'(symbol (lib_id "power:{kind}") (at {x:.2f} {y:.2f} {rot}) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {U()})'
                 f' (property "Reference" "{ref}" (at {x:.2f} {y+6:.2f} 0) {eff(hide=True)})'
                 f' (property "Value" "{kind}" (at {x:.2f} {y+3.8:.2f} 0) {eff(hide=kind!="GND")})'
                 f' (property "Footprint" "" (at {x:.2f} {y:.2f} 0) {eff(hide=True)}) (property "Datasheet" "" (at {x:.2f} {y:.2f} 0) {eff(hide=True)})'
                 f' (pin "1" (uuid {U()})) (instances (project "hfmc" (path "/{ROOT}" (reference "{ref}") (unit 1)))))')
def body_extent(sym):
    """x/y extent of the symbol graphics + pins (symbol coords, y up)."""
    xs, ys = [0.0], [0.0]
    def walk(e):
        if not isinstance(e, list) or not e: return
        if e[0] in ("property",): return
        if e[0] in ("xy", "start", "end", "at") and len(e) >= 3:
            try: xs.append(float(e[1])); ys.append(float(e[2]))
            except ValueError: pass
        if e[0] == "circle":
            c = [x for x in e if isinstance(x, list) and x[0] == "center"]; r = [x for x in e if isinstance(x, list) and x[0] == "radius"]
            if c and r:
                cx, cy, rr = float(c[0][1]), float(c[0][2]), float(r[0][1]); xs.extend([cx - rr, cx + rr]); ys.extend([cy - rr, cy + rr])
        for x in e[1:]: walk(x)
    walk(sym)
    return min(xs), max(xs), min(ys), max(ys)
def place(p, X, Y):
    sym = libs[p["sym"]]; lid = f'{p["sym"][0]}:{p["sym"][1]}'
    ps = pins(sym)
    x0, x1, y0, y1 = body_extent(sym)
    angs = {int(q[4]) for q in ps}
    horiz = (0 in angs and 180 in angs) or not (angs & {90, 270})
    if horiz:      # pins left/right: fields stacked above the body, clear of the labels
        fx_ = X + x0 + 1.0
        pos = [(fx_, Y - y1 - 7.0), (fx_, Y - y1 - 4.6), (fx_, Y - y1 - 2.2)]
    else:          # pins up/down (or mixed): fields to the right of the body
        fx_ = X + x1 + 1.5
        pos = [(fx_, Y - 2.6), (fx_, Y), (fx_, Y + 2.6)]
    props = [("Reference", p["ref"], *pos[0], False), ("Value", p["value"], *pos[1], False), ("DocRef", p["doc"] if p["doc"] != p["ref"] else "", *pos[2], p["doc"] == p["ref"]),
             ("Footprint", p["fp"], X, Y, True), ("Datasheet", "", X, Y, True), ("MPN", p["mpn"], X, Y, True)]
    if p.get("gen"): props.append(("SimName", p["gen"], X, Y, True))
    if p.get("note"): props.append(("Note", p["note"], X, Y, True))
    s = f'(symbol (lib_id "{lid}") (at {X:.2f} {Y:.2f} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {U()})'
    for k, v, x, y, h in props:
        s += f' (property "{k}" "{v}" (at {x:.2f} {y:.2f} 0) {eff(hide=h, just="left")})'
    for num, *_ in ps:
        s += f' (pin "{num}" (uuid {U()}))'
    s += f' (instances (project "hfmc" (path "/{ROOT}" (reference "{p["ref"]}") (unit 1)))))'
    items.append(s)
    for num, name, px, py, ang, ln, et in ps:
        ex, ey = X + px, Y - py                      # pin endpoint in sheet coords (y down)
        d = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[int(ang)]   # outward direction
        sx, sy = ex + d[0] * G, ey + d[1] * G
        wire(ex, ey, sx, sy)
        net = p["pins"][num]
        if net == "GND":
            rot = {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[d]
            power("GND", sx, sy, rot)
        else:
            lang = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[d]
            label(net, sx, sy, lang)
# page layout: A2 landscape 594 x 420
texts = []
x0, y0 = 20.32, 30.48
col_w, row_h = 27.94, 33.02
cursor_y = y0
title_x = x0
sec_pos = [(20.32, 25.4, 9), (20.32, 106.68, 9), (20.32, 182.88, 10), (330.2, 25.4, 6), (330.2, 106.68, 6), (330.2, 182.88, 7), (20.32, 330.2, 13)]
for (title, refs), (sx, sy, ncol) in zip(SECTIONS, sec_pos):
    texts.append(f'(text "{title}" (at {sx:.2f} {sy:.2f} 0) (effects (font (size 2.54 2.54) bold) (justify left)) (uuid {U()}))')
    for i, r in enumerate(refs):
        cx = snap(sx + 10.16 + (i % ncol) * col_w); cy = snap(sy + 17.78 + (i // ncol) * row_h)
        place(parts[r], cx, cy)
# PWR_FLAGs: GND, VCC, UIN, J6A
fx, fy = 520.7, 330.2
for i, net in enumerate(["GND", "VCC", "UIN", "J6A"]):
    x = snap(fx + i * 12.7); y = fy
    power("PWR_FLAG", x, y, 0)
    if net == "GND":
        wire(x, y, x, y + G); power("GND", x, y + G, 0)
    else:
        wire(x, y, x, y + G); label(net, x, y + G, 270)
texts.append(f'(text "PWR_FLAG markers (ERC)" (at {fx:.2f} {fy-8:.2f} 0) {eff(just="left")} (uuid {U()}))')
notes = ("Rev B build A prototype. Net names = sim/scripts/gen.py node names (SimName field = simulation element).\\n"
         "Electrical simulation status: see docs/review2-response.md (simulated, not measured).\\n"
         "Layout additions vs simulation: C19, C24, C25, C26 extra 100 nF bypass on VCC (ideal rail in simulation);\\n"
         "J1 panel BNC wired by RG-316 pigtail; J6 panel DC jack wired; MH1 bonds GDT1 ground to the chassis.")
texts.append(f'(text "{notes}" (at 160.02 330.2 0) {eff(just="left")} (uuid {U()}))')
hdr = f'(kicad_sch (version 20230121) (generator eeschema)\n  (uuid {ROOT})\n  (paper "A2")\n'
hdr += '  (title_block (title "HF Receive Multicoupler Rev B - Build A prototype") (date "2026-11-05") (rev "B-proto1") (company "K2AAM") (comment 1 "4-port, through-hole, 2-layer, Hammond 1590BB") (comment 2 "Simulated design; hardware unmeasured"))\n'
hdr += "  (lib_symbols\n" + "\n".join("    " + ser(v) for v in libs.values()) + "\n  )\n"
body = "\n".join("  " + t for t in items + texts)
foot = f'\n  (sheet_instances (path "/" (page "1")))\n)\n'
open("hfmc.kicad_sch", "w").write(hdr + body + foot)
print("parts", len(design.P), "items", len(items))
