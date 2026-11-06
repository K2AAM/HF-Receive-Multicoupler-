"""Enclosure fit for the Hammond 1590C (build A prototype).

Geometry source: Hammond drawing 1590C.pdf and the Hammond 1590C.dwg (geometry read with LibreDWG; the DWG
dimensions match the PDF). Every number below is tagged:
  MFR    - a dimension printed on the Hammond / connector drawing
  DWG    - measured from the Hammond DWG geometry (lines/arcs), not a printed dimension
  CALC   - calculated here from MFR/DWG values
  ASSUME - an assumption that must be checked on real parts
Box frame: origin at the box centre (centre of the cover-screw pattern), x along the length (+x = U1 / right side),
y along the width (+y = front wall with the four output BNCs), z up from the INSIDE floor. z_out = z + floor
thickness is height above the OUTSIDE bottom face. Run with KiCad's python (/usr/bin/python3).
Outputs: enclosure_report.txt, enclosure.json, img/enclosure_*.png, img/drill_*.png, drill_drawing.pdf."""
import sys, os, json, math
import numpy as np
import pcbnew
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
from matplotlib.backends.backend_pdf import PdfPages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import place
OX, OY = 150.0, 100.0
TM = pcbnew.ToMM
SRC = {}
def v(name, value, src, note=""):
    SRC[name] = (value, src, note); return value

# ---------------- Hammond 1590C ----------------
EXT_L = v("outside length (at rim)", 119.50, "MFR")
EXT_W = v("outside width (at rim)", 94.00, "MFR")
BODY_H = v("body height without lid", 52.50, "MFR")
LID_T = v("lid thickness", 4.00, "MFR")
OVERALL_H = v("overall height with lid", 56.50, "MFR")
FLOOR = v("floor thickness", 2.25, "MFR")
IN_H = v("inside height, floor to underside of lid", 52.25, "MFR", "lid pocket 2.00 deep (MFR)")
RIM_Z = v("inside floor to rim", BODY_H - FLOOR, "CALC")                                  # 50.25
LIP_Z = v("inside floor to bottom of lid lip", RIM_Z - 2.00, "DWG", "lid lip projects 2.0 below the rim, 0.57 mm inside the wall")
IN_L_RIM, IN_W_RIM = v("inside length at rim", 115.14, "MFR"), v("inside width at rim", 89.64, "MFR")
IN_L_FL, IN_W_FL = v("inside length near floor", 111.27, "MFR", "DWG: measured 0.96 mm above the floor, at the top of the R1.0 floor fillet"), v("inside width near floor", 85.77, "MFR")
Z_FL = v("height of the near-floor inside dimensions", 0.96, "DWG")
FILLET_IN = v("inside floor fillet radius", 1.0, "DWG")
WALL_T = v("wall thickness (horizontal)", 2.18, "DWG", "outer wall drafted parallel to inner; 2.18 at the rim")
K = v("wall draft tan", (IN_W_RIM - IN_W_FL) / 2 / (RIM_Z - Z_FL), "CALC")              # 2.25 deg
SCREW = v("cover-screw (6-32) pattern", (109.50, 84.00), "MFR", "screw centres (+-54.75, +-42.00): use as the drilling datum")
PILLAR_C = v("screw-pillar arc centre", (54.82, 42.07), "DWG")
PILLAR_R = v("screw-pillar radius, worst (near floor)", 5.94, "DWG", "arcs R4.94 and R5.94 about the pillar centre; 103.64 x 78.14 between pillar faces at the rim (MFR)")
def yin(z):   # inner face of the front/back wall (half width) at height z
    return IN_W_FL / 2 + K * (z - Z_FL)
def xin(z):
    return IN_L_FL / 2 + K * (z - Z_FL)

# ---------------- connectors (manufacturer drawings) ----------------
BNC = dict(cl=v("031-5431-10RFX centreline above PCB", 8.6, "MFR"),
           face_y=place.WALL_Y,                                   # board y of the BNC front (panel) face
           housing_w=v("031-5431-10RFX housing width", 14.5, "MFR"), housing_h=v("031-5431-10RFX housing height", 15.6, "MFR"),
           housing_d=13.8, thread=v("031-5431-10RFX 1/2-28 thread length", 8.9, "MFR"), thread_d=12.70,
           bayonet=v("031-5431-10RFX bayonet length beyond thread", 12.0, "MFR"),
           bayonet_d=v("BNC bayonet diameter over lugs", 11.5, "ASSUME", "BNC jack barrel ~9.6 + lugs; check with calipers"),
           hole_amph=v("031-5431-10RFX recommended panel hole", (12.83, 11.96), "MFR", "dia / D-flat"),
           panel_max=v("031-5431-10RFX max panel thickness", 5.0, "MFR"), hex=v("031-5431-10RFX hex nut", 15.88, "MFR"))
J1C = dict(hole=v("031-221-RFX panel hole (type U)", (11.1, 10.3), "MFR", "dia / D-flat, Amphenol BNC catalogue table"),
           panel_max=v("031-221-RFX max panel thickness", 3.2, "MFR"), hex=v("031-221-RFX hex nut", 12.7, "MFR"),
           behind=v("031-221-RFX length behind panel incl. nut and solder cup", 15.0, "ASSUME", "27.0 overall (MFR) less the front part"))
J6C = dict(hole=v("722A panel hole (5/16-32 bushing)", (8.00, 7.37), "MFR", "dia / flat from Switchcraft 5/16-32 jack drawings (L721A); confirm on the 722A sheet"),
           thread=v("722A bushing thread length", 5.46, "MFR"), panel_max=v("722A max panel thickness", 3.1, "MFR", "distributor listing"),
           behind=v("722A body + lugs behind panel", 16.0, "ASSUME", "20.8 overall less bushing; lugs turned horizontal"), half_w=8.0, half_h=6.0)

# ---------------- chosen build values ----------------
SPACER = v("M3 brass spacer height (Wurth 970060354)", 6.0, "MFR")
PCB_T = 1.6
ZB = SPACER + PCB_T                                   # PCB top above inside floor
ZC = ZB + BNC["cl"]                                   # BNC centreline
WASHER = (13.0, 0.0, 0.0)                             # no washer between housing face and wall (housing bears on the inside spot-face)
NUT_WASHER = v("outside flat washer under the BNC lock washer: DIN 433 M12", (13.0, 20.0, 2.0), "MFR", "ID 13 / OD 20 / t 2, bridges the slot")
SF_IN_D, SF_OUT_D = 22.0, 20.0                        # spot-face (milled flat strip) heights: inside covers the 14.5x15.6 housing faces, outside the washers
SF_IN_L, SF_OUT_L = 82.0, 80.0                        # strip lengths along the wall (x -41..+41 / -40..+40): one flat strip for all four BNCs
Y_SF = yin(ZC + SF_IN_D / 2)                          # inside spot-face plane = wall face at the top of the spot-face
Y_SF_OUT = yin(ZC - SF_OUT_D / 2) + WALL_T            # outside spot-face plane = outer face at the bottom of its spot-face
PANEL_BNC = Y_SF_OUT - Y_SF
DY = Y_SF - WASHER[2] - BNC["face_y"]                 # board-to-box offset (washer between housing face and wall): board y + DY = box y
SLOT_W, SLOT_H = 12.9, 15.5                           # front-wall opening per BNC: vertical slot (obround); height lets the thread pass at the tilt needed
HOLE_BNC = SLOT_H                                     # vertical extent used by the 2D insertion check
FLOOR_HOLE = 4.2                                      # clearance for M3: +-0.6 mm float so the BNC nuts set the board position
J1_POS = (-8.0, 24.0)                                 # left wall: (y, z)
J6_POS = (36.0, 26.0)                                 # back wall: (x, z)

# ---------------- board and parts ----------------
H = {
 "R_Axial_DIN0207": (3.0, "Yageo MFR-25 body dia 2.5 max, lying flat"), "D_DO-35": (2.5, "DO-35 dia 1.9 max"),
 "D_DO-41": (3.2, "DO-41 dia 2.7 max"), "L_Axial_L7.0mm_D3.3mm": (3.8, "Bourns 78FR axial, flat"),
 "C_Disc_D3.8mm": (4.7, "KEMET C315 seated H 4.66 max"), "C_Radial_KEMET_C320": (7.4, "KEMET C320 seated H 7.36 max"),
 "C_Disc_W3.2mm": (7.7, "KEMET C325 seated H 7.62 max"), "C_Rect_L7.2mm_W7.2mm": (13.0, "KEMET R82 4.7uF 13.0 / 2.2uF 11.0"),
 "C_Rect_L18.0mm": (19.1, "KEMET R60EI4470AA30J H 19.1"), "CP_Radial_D5.0mm": (12.5, "Panasonic ECA 5x11 + 1.5"),
 "CP_Radial_D8.0mm": (13.0, "Panasonic FR 8x11.5 + 1.5"), "L_Radial_D9.5mm": (13.0, "Bourns RLB0914 seated H 13 max"),
 "TO-92": (7.0, "TO-92 body 5.2 + ~1.8 seating (ASSUME)"), "TO-220-3_Horizontal": (5.0, "TO-220 lying flat, 4.7 incl. tab"),
 "GDT_Bourns": (8.5, "Bourns 2027 dia 8.0"), "Fuse_Littelfuse_RXEF": (12.7, "RXEF030 seated H 12.7 max"),
 "TestPoint_Keystone": (8.0, "Keystone 5000 (ASSUME)"), "BNC_Amphenol": (16.4, "031-5431-10RFX CL 8.6 + 15.6/2"),
 "MountingHole": (2.0, "M3 x 5 pan head + washer"), "Pads_": (3.0, "wire / coax pigtail solder joint"),
}
def height(fpname):
    for k, val in H.items():
        if k in fpname: return val
    raise KeyError(fpname)
b = pcbnew.LoadBoard("hfmc.kicad_pcb")
parts = []
for fp in b.GetFootprints():
    c = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = c.BBox() if c.OutlineCount() else fp.GetBoundingBox(False, False)
    name = str(fp.GetFPID().GetLibItemName()); h, src = height(name)
    if "R82CC4220" in fp.GetProperty("MPN"): h, src = 11.0, "KEMET R82 2.2uF H 11.0"
    x0, x1 = TM(bb.GetLeft()) - OX, TM(bb.GetRight()) - OX
    y0, y1 = TM(bb.GetTop()) - OY + DY, TM(bb.GetBottom()) - OY + DY
    if name.startswith("BNC"):                       # body only (the courtyard includes the thread through the wall)
        y0, y1 = BNC["face_y"] + DY - BNC["housing_d"], BNC["face_y"] + DY
    parts.append(dict(ref=fp.GetReference(), x0=x0, x1=x1, y0=y0, y1=y1, h=h, src=src, fp=name))
W2, H2, N = place.BOARD_W / 2, place.BOARD_H / 2, place.NOTCH
MH = {r: (place.PL[r][0], place.PL[r][1] + DY) for r in ("MH1", "MH2", "MH3", "MH4", "MH5")}

rep = []
def out(s=""): rep.append(s); print(s)
out("HAMMOND 1590C FIT - build A prototype (generated by enclosure.py)")
out("Box frame: origin = centre of the four cover-screw holes; +y = front (output) wall; +x = U1 side; z = above INSIDE floor;")
out(f"z_out = z + {FLOOR} = above the OUTSIDE bottom face.\n")
out("1. Enclosure data and sources")
for k, (val, s, note) in SRC.items():
    if any(w in k for w in ("031-", "722A", "spacer", "BNC")): continue
    out(f"   [{s:6s}] {k}: {val if not isinstance(val, float) else round(val, 4)}" + (f"  ({note})" if note else ""))
out(f"   [CALC  ] draft: {math.degrees(math.atan(K)):.2f} deg per side")
out("\n2. Stack-up (z above inside floor)")
out(f"   M3 x {SPACER:.0f} mm brass spacers -> PCB {SPACER:.1f}-{ZB:.1f}; BNC centreline {ZC:.1f}; lid lip bottom {LIP_Z:.2f}; rim {RIM_Z:.2f}; lid pocket {IN_H:.2f}")
tall = sorted(parts, key=lambda p: -p["h"])[:6]
for p in tall:
    out(f"   {p['ref']:5s} top {ZB + p['h']:5.1f}  -> {LIP_Z - ZB - p['h']:5.1f} mm below the lid lip, {IN_H - ZB - p['h']:5.1f} below the lid pocket ({p['src']})")
c1 = next(p for p in parts if p["ref"] == "C1")
out(f"   Solder side: {SPACER:.1f} mm from PCB bottom to inside floor (clipped leads <= 1.5 mm -> >= {SPACER - 1.5:.1f} mm clear)")

out("\n3. Board in the box")
out(f"   Board 104 x 78, corner notches {N} x {N}, outline unchanged. Board offset DY = {DY:+.2f} mm toward the front wall (set by the BNC faces).")
gx = xin(SPACER) - W2; gy_f = yin(SPACER) - (H2 + DY); gy_b = yin(SPACER) - (H2 - DY)
out(f"   Side clearance at PCB bottom: x {gx:.2f} each side; front edge {gy_f:.2f}; back edge {gy_b:.2f}")
def pillar_clear():
    res = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * PILLAR_C[0], sy * PILLAR_C[1]
            pts = []
            for t in np.linspace(0, 1, 200):          # board edge near this corner (notch)
                pts += [(sx * (W2 - N + N * t), sy * (H2 - N) + DY), (sx * (W2 - N), sy * (H2 - N + N * t) + DY),
                        (sx * W2, sy * (H2 - N) * t + DY), (sx * (W2 - N) * t, sy * H2 + DY)]
            d = min(math.hypot(px - cx, py - cy) for px, py in pts) - PILLAR_R
            res.append(((cx, cy), d))
    return res
for (c, d) in pillar_clear():
    out(f"   screw pillar at ({c[0]:+.2f},{c[1]:+.2f}) R{PILLAR_R}: clearance to notched board edge {d:.2f} mm")
out("   Without the notches the board corner would be inside the pillars -> keep the notched outline.")

out("\n4. Output BNCs (031-5431-10RFX, rear mount) on the drafted front wall")
out(f"   The wall leans out {math.degrees(math.atan(K)):.2f} deg; across the 15.6 mm housing face that is {K * BNC['housing_h']:.2f} mm, so the face cannot seat flat on the as-cast wall.")
out(f"   Inside: mill one flat strip {SF_IN_L:.0f} long x {SF_IN_D:.0f} high centred on the BNC row, plane perpendicular to the floor at y = {Y_SF:.3f}")
out(f"   (cut 0 at its top edge, {Y_SF - yin(ZC - SF_IN_D / 2):.2f} at its bottom edge). Separate dia 22 spot-faces would overlap at the 20 mm pitch.")
out(f"   Outside: parallel strip {SF_OUT_L:.0f} x {SF_OUT_D:.0f} at y = {Y_SF_OUT:.3f} (cut {yin(ZC + SF_OUT_D / 2) + WALL_T - Y_SF_OUT:.2f} at its top edge, 0 at its bottom).")
out(f"   Finished wall at each BNC: {PANEL_BNC:.2f} mm (connector limit {BNC['panel_max']} max).")
out(f"   BNC front face lands on the inside spot-face at board offset DY = {DY:+.3f}: zero gap by construction; floor holes dia {FLOOR_HOLE}")
out("   give +-0.6 mm float so the BNC nuts, not the spacers, position the board (tighten spacer screws last).")

# ---------------- insertion path (2D, y-z section through a BNC) ----------------
def board_shapes():
    """Rigid board assembly in board frame (y_b, z_b), z_b = 0 at PCB top. Spacers are attached during insertion."""
    rects = [(-H2, H2, -PCB_T, 0.0)]
    for r in MH: rects.append((place.PL[r][1] - 2.9, place.PL[r][1] + 2.9, -PCB_T - SPACER, -PCB_T))
    for p in parts:
        if p["fp"].startswith("BNC") or p["fp"].startswith("MountingHole"): continue
        rects.append((p["y0"] - DY, p["y1"] - DY, 0.0, p["h"]))
    f = BNC["face_y"]
    rects.append((f - BNC["housing_d"], f, BNC["cl"] - BNC["housing_h"] / 2, BNC["cl"] + BNC["housing_h"] / 2))
    pts = []
    for y0, y1, z0, z1 in rects:
        for t in np.linspace(0, 1, 9):
            pts += [(y0 + (y1 - y0) * t, z0), (y0 + (y1 - y0) * t, z1), (y0, z0 + (z1 - z0) * t), (y1, z0 + (z1 - z0) * t)]
    return np.array(pts)
PTS = board_shapes()
FB = np.array([BNC["face_y"], BNC["cl"]])
def pose(theta, u, P=PTS):
    c, s = math.cos(theta), math.sin(theta)
    d = np.array([c, s]); F = np.array([Y_SF - WASHER[2], ZC]) - u * d
    R = np.array([[c, -s], [s, c]])
    return (P - FB) @ R.T + F, F, d
def feasible(theta, u, Rh):
    q, F, d = pose(theta, u)
    y, z = q[:, 0], q[:, 1]
    if (z < -1e-6).any(): return False
    below = z <= RIM_Z                                                            # the box is open above the rim (lid off)
    if (below & (y < -yin(z) - 1e-6)).any(): return False                         # back wall
    inspot = np.abs(z - ZC) <= SF_IN_D / 2
    front = np.where(inspot, Y_SF, yin(z))
    if (below & (y > front + 1e-6)).any(): return False                           # front wall (solid apart from the hole)
    nrm = np.array([-d[1], d[0]])
    for a0, a1, dia in ((WASHER[2], BNC["thread"], BNC["thread_d"]), (BNC["thread"], BNC["thread"] + BNC["bayonet"], BNC["bayonet_d"])):
        r = dia / 2
        for sgn in (1, -1):                       # top and bottom generator lines of the barrel in this section
            P0 = F + sgn * r * nrm
            for yp in (Y_SF, Y_SF + PANEL_BNC):   # inside and outside face of the wall at the hole
                if abs(d[0]) < 1e-9: return False
                a = (yp - P0[0]) / d[0]
                if a0 - 1e-9 <= a <= a1 + 1e-9:
                    if abs(P0[1] + a * d[1] - ZC) > Rh / 2 + 1e-9: return False
        for a in (a0, a1):                        # barrel end faces inside the wall slab
            A = F + a * d
            for sgn in (1, -1):
                Q = A + sgn * r * nrm
                if Y_SF <= Q[0] <= Y_SF + PANEL_BNC and abs(Q[1] - ZC) > Rh / 2: return False
    return True
def insertion(Rh, thetas=np.radians(np.arange(-60, 60.01, 0.5)), us=np.arange(0, 32.01, 0.25)):
    """Breadth-first search over (tilt, withdrawal along the BNC axis) from the seated pose. Returns the reachable set,
    the withdrawn poses reached and one path (list of (theta_deg, u)) to the least-tilted withdrawn pose."""
    from collections import deque
    ok = np.array([[feasible(t, u, Rh) for u in us] for t in thetas])
    i0 = int(np.argmin(abs(thetas))); free_u = BNC["thread"] + BNC["bayonet"] + PANEL_BNC + 1.0
    seen = np.zeros_like(ok); parent = {}
    q = deque([(i0, 0)] if ok[i0, 0] else [])
    if q: seen[i0, 0] = True
    while q:
        i, j = q.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, c = i + di, j + dj
            if 0 <= a < len(thetas) and 0 <= c < len(us) and ok[a, c] and not seen[a, c]:
                seen[a, c] = True; parent[(a, c)] = (i, j); q.append((a, c))
    cells = [(i, j) for i, j in zip(*np.nonzero(seen)) if us[j] >= free_u]
    reach = [(math.degrees(thetas[i]), us[j]) for i, j in cells]
    path = []
    if cells:
        k = min(cells, key=lambda ij: (abs(thetas[ij[0]]), us[ij[1]]))
        while k in parent or k == (i0, 0):
            path.append((math.degrees(thetas[k[0]]), us[k[1]]))
            if k == (i0, 0): break
            k = parent[k]
        path = path[::-1]
    return ok, seen, reach, thetas, us, path
out("\n5. Insertion path of the board with its four BNCs (2D search over tilt and travel along the BNC axis)")
out(f"   Back edge to back wall when level: {yin(SPACER) - (H2 - DY):.2f} mm, but the 1/2-28 thread is {BNC['thread']} mm long,")
out("   so the board cannot be slid in level: it has to go in tilted, which needs a front hole larger than the thread.")
INS = {}
for Rh in (12.83, 14.0, 14.4, SLOT_H):
    ok, seen, reach, th, us, pth = insertion(Rh)
    INS[Rh] = (ok, seen, reach, th, us, pth)
    if reach:
        tmin = min(abs(t) for t, u in reach)
        out(f"   opening {Rh:5.2f} high: PATH FOUND (barrels fully withdrawn at a tilt of {tmin:.1f} deg, BNC end down)")
    else:
        out(f"   opening {Rh:5.2f} high: no path - the board cannot be fitted")
assert INS[HOLE_BNC][2], "chosen BNC hole does not allow insertion"
pth = INS[HOLE_BNC][5]
maxtilt = min(t for t, u in pth); thr = [t for t, u in pth if u <= BNC["thread"] + PANEL_BNC]
out(f"   Path found: back the board off level about {max(u for t, u in pth if abs(t) < 0.3):.1f} mm, then tilt the BNC end down while withdrawing;")
out(f"   up to {abs(min(thr)):.1f} deg while the thread is still in the slot, {abs(maxtilt):.1f} deg once only the bayonet is (back end above the rim).")
out("   Assembly is the same path in reverse (lid off).")
slot_area = math.pi * (SLOT_W / 2) ** 2 + SLOT_W * (SLOT_H - SLOT_W)
bear = BNC["housing_w"] * BNC["housing_h"] - slot_area
out(f"   Chosen: vertical slot {SLOT_W} wide x {SLOT_H} high (obround, no D-flat; the soldered board stops the connectors turning).")
out(f"   Amphenol's dia 12.83 D-hole is too tight for the tilt: with it the board cannot be fitted at all.")
out(f"   Housing-face bearing on the inside spot-face: {bear:.0f} mm2 ({(BNC['housing_w'] - SLOT_W) / 2:.2f} mm strips at the sides + corners).")
out(f"   Outside: DIN 433 M12 flat washer (OD 20) + the supplied lock washer + nut; stack {PANEL_BNC + 2.0 + 1.0:.1f} mm of the {BNC['thread']} mm thread before the nut.")
out("   Fit J1 and J6 (wired panel jacks) after the board: the tilting board sweeps through their volume.")

out("\n6. Panel jacks")
def under(box):
    x0, x1, y0, y1 = box
    return [p for p in parts if p["x1"] > x0 and p["x0"] < x1 and p["y1"] > y0 and p["y0"] < y1]
yJ1, zJ1 = J1_POS; xw = -xin(zJ1)
j1box = (xw, xw + J1C["behind"], yJ1 - 7.4, yJ1 + 7.4)
u1 = under(j1box); top1 = max([ZB + p["h"] for p in u1] + [ZB])
out(f"   J1 031-221-RFX, left wall: y = {yJ1:+.1f}, z = {zJ1:.1f} (z_out {zJ1 + FLOOR:.2f}). Nut/body keep-out {J1C['behind']:.0f} deep, +-7.4:")
out(f"      parts below: {', '.join(p['ref'] for p in u1) or 'none'}; clearance below {zJ1 - 7.4 - top1:.1f} mm, to lid lip {LIP_Z - zJ1 - 7.4:.1f} mm; wall {WALL_T} <= {J1C['panel_max']} max")
xJ6, zJ6 = J6_POS; yw = -yin(zJ6)
j6box = (xJ6 - J6C["half_w"], xJ6 + J6C["half_w"], yw, yw + J6C["behind"])
u6 = under(j6box); top6 = max([ZB + p["h"] for p in u6] + [ZB])
out(f"   J6 Switchcraft 722A, back wall: x = {xJ6:+.1f}, z = {zJ6:.1f} (z_out {zJ6 + FLOOR:.2f}). Body keep-out {J6C['behind']:.0f} deep, +-{J6C['half_w']:.0f} x +-{J6C['half_h']:.0f}:")
out(f"      parts below: {', '.join(p['ref'] for p in u6) or 'none'}; clearance below {zJ6 - J6C['half_h'] - top6:.1f} mm, to lid lip {LIP_Z - zJ6 - J6C['half_h']:.1f} mm; wall {WALL_T} <= {J6C['panel_max']} max")
out("   Both are wired jacks, so the 2.25 deg wall draft only tilts the jack; no PCB load. Spot-face if a flat nut seat is wanted.")

out("\n7. U1 (LM317T lying tab-down, tab = VOUT ~9.8 V)")
u1p = next(p for p in parts if p["ref"] == "U1")
out(f"   Tab/body x {u1p['x0']:.1f}..{u1p['x1']:.1f}: {xin(ZB) - u1p['x1']:.2f} mm from the grounded right wall; top at z {ZB + u1p['h']:.1f}, {LIP_Z - ZB - u1p['h']:.1f} mm below the lid lip.")
out("   No F.Cu copper under body/tab (keep-out on the PCB); tab rests on solder mask over bare laminate. Use a nylon M3 screw or none.")

out("\n8. Screws and ground bond")
out(f"   Spacers: Wurth 970060354, M3 x 6 brass female-female, 5 mm hex. Top: M3 x 5 pan + washer (2.9 mm engagement).")
out(f"   Bottom: M3 x 5 pan + washer through dia {FLOOR_HOLE} floor holes (2.25 mm engagement); 5.15 mm total < 6 mm spacer thread.")
out("   Ground: spacer end faces bear on bare die-cast floor (natural 1590C; remove paint on a 1590CBK); BNC shells clamp to the")
out("   bare spot-faces. MH1 sits 6.7 mm from the GDT ground pad.")
mh_s = "; ".join(f"{r} ({x:+.2f}, {y:+.2f})" for r, (x, y) in MH.items())
out(f"\n9. Floor holes (box frame, from the cover-screw centre), dia {FLOOR_HOLE}: {mh_s}")
out(f"   Front-wall BNC slots: x = -30, -10, +10, +30; centre z = {ZC:.2f} (z_out {ZC + FLOOR:.2f}); {SLOT_W} wide x {SLOT_H} high, axis parallel to the floor.")
out(f"   Left-wall J1: y = {yJ1:+.1f}, z_out {zJ1 + FLOOR:.2f}; back-wall J6: x = {xJ6:+.1f}, z_out {zJ6 + FLOOR:.2f}.")
OK = all([LIP_Z - ZB - c1["h"] > 5, zJ1 - 7.4 - top1 >= 2, zJ6 - J6C["half_h"] - top6 >= 2, min(d for _, d in pillar_clear()) > 2,
          PANEL_BNC <= BNC["panel_max"], WALL_T <= J1C["panel_max"], WALL_T <= J6C["panel_max"], bool(INS[HOLE_BNC][2])])
out(f"\nRESULT {'OK' if OK else 'CHECK'} (assumptions in section 1 and the ASSUME items in docs/pcb-prototype-A.md still need measuring)")
open("enclosure_report.txt", "w").write("\n".join(rep) + "\n")
json.dump(dict(spacer=SPACER, pcb_top=ZB, bnc_cl=ZC, board_dy=DY, y_spotface_in=Y_SF, y_spotface_out=Y_SF_OUT, panel_at_bnc=PANEL_BNC,
               hole_bnc=HOLE_BNC, floor_hole=FLOOR_HOLE, lip_z=LIP_Z, rim_z=RIM_Z, floor=FLOOR, J1=J1_POS, J6=J6_POS,
               mounting_holes=MH, c1_below_lip=LIP_Z - ZB - c1["h"], sources={k: [str(a), b_, c] for k, (a, b_, c) in SRC.items()}),
          open("enclosure.json", "w"), indent=1)

# =============================== figures ===============================
os.makedirs("img", exist_ok=True)
import matplotlib.cm as cm
def board_outline():
    return [(-W2 + N, -H2), (W2 - N, -H2), (W2 - N, -H2 + N), (W2, -H2 + N), (W2, H2 - N), (W2 - N, H2 - N), (W2 - N, H2),
            (-W2 + N, H2), (-W2 + N, H2 - N), (-W2, H2 - N), (-W2, -H2 + N), (-W2 + N, -H2 + N)]
# --- top view
fig, ax = plt.subplots(figsize=(11, 9))
ax.add_patch(Rectangle((-EXT_L / 2, -EXT_W / 2), EXT_L, EXT_W, fill=False, lw=1.5, ec="k"))
ax.add_patch(Rectangle((-IN_L_RIM / 2, -IN_W_RIM / 2), IN_L_RIM, IN_W_RIM, fill=False, lw=0.8, ec="0.4", ls="--"))
ax.add_patch(Rectangle((-xin(ZB), -yin(ZB)), 2 * xin(ZB), 2 * yin(ZB), fill=False, lw=0.8, ec="0.2"))
for sx in (-1, 1):
    for sy in (-1, 1):
        ax.add_patch(Circle((sx * PILLAR_C[0], sy * PILLAR_C[1]), PILLAR_R, fc="0.8", ec="0.3"))
        ax.add_patch(Circle((sx * SCREW[0] / 2, sy * SCREW[1] / 2), 1.32, fc="w", ec="k"))
ax.add_patch(Polygon([(x, y + DY) for x, y in board_outline()], closed=True, fc="#2e7d32", alpha=0.25, ec="#1b5e20"))
for p in parts:
    ax.add_patch(Rectangle((p["x0"], p["y0"]), p["x1"] - p["x0"], p["y1"] - p["y0"], fc=cm.viridis(min(p["h"] / 20, 1)), alpha=0.55, ec="k", lw=0.3))
    if p["h"] >= 11 or p["ref"].startswith(("J", "U", "MH")):
        ax.text((p["x0"] + p["x1"]) / 2, (p["y0"] + p["y1"]) / 2, f"{p['ref']}\n{p['h']:.0f}", ha="center", va="center", fontsize=6)
for (x0, x1, y0, y1), lab in ((j1box, f"J1\nz {zJ1:.0f}"), (j6box, f"J6\nz {zJ6:.0f}")):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="red", lw=1.2, ls="--"))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, lab, color="red", ha="center", va="center", fontsize=7)
for x in (-30, -10, 10, 30):
    ax.add_patch(Rectangle((x - BNC["thread_d"] / 2, Y_SF), BNC["thread_d"], BNC["thread"] + BNC["bayonet"], fill=False, ec="blue", lw=0.8))
ax.set_xlim(-64, 64); ax.set_ylim(-52, 70); ax.set_aspect("equal")
ax.set_title(f"Hammond 1590C, top view (lid off). PCB on M3 x {SPACER:.0f} spacers, offset {DY:+.2f} mm toward the BNC wall.\n"
             "Part heights in mm above PCB; grey = screw pillars (R5.94 worst case); red = panel-jack keep-outs; outputs at the top", fontsize=9)
ax.set_xlabel("x (mm), origin = cover-screw pattern centre"); ax.set_ylabel("y (mm), + = output wall")
fig.tight_layout(); fig.savefig("img/enclosure_top.png", dpi=150); plt.close(fig)

# --- side section through a BNC (x = +10), with lid
def wall_poly(sign):
    zs = np.linspace(0, RIM_Z, 50)
    inner = [(sign * yin(z), z) for z in zs]
    outer = [(sign * (yin(z) + WALL_T), z) for z in zs[::-1]]
    return inner + outer
fig, ax = plt.subplots(figsize=(12, 6.2))
ax.add_patch(Polygon(wall_poly(1), closed=True, fc="0.75", ec="k", lw=0.6))
ax.add_patch(Polygon(wall_poly(-1), closed=True, fc="0.75", ec="k", lw=0.6))
ax.add_patch(Rectangle((-yin(0) - WALL_T, -FLOOR), 2 * (yin(0) + WALL_T), FLOOR, fc="0.75", ec="k", lw=0.6))
ax.add_patch(Rectangle((-EXT_W / 2, BODY_H - FLOOR), EXT_W, LID_T, fc="0.85", ec="k", lw=0.6))
ax.add_patch(Rectangle((-IN_W_RIM / 2 + 0.57, LIP_Z), 1.75, 2.0, fc="0.85", ec="k", lw=0.4))
ax.add_patch(Rectangle((IN_W_RIM / 2 - 0.57 - 1.75, LIP_Z), 1.75, 2.0, fc="0.85", ec="k", lw=0.4))
# spot-faces and hole
ax.add_patch(Polygon([(yin(ZC - SF_IN_D / 2), ZC - SF_IN_D / 2), (Y_SF, ZC - SF_IN_D / 2), (Y_SF, ZC + SF_IN_D / 2)], closed=True, fc="w", ec="r", lw=0.6))
ax.add_patch(Polygon([(Y_SF_OUT, ZC - SF_OUT_D / 2), (Y_SF_OUT, ZC + SF_OUT_D / 2), (yin(ZC + SF_OUT_D / 2) + WALL_T, ZC + SF_OUT_D / 2)], closed=True, fc="w", ec="r", lw=0.6))
ax.add_patch(Rectangle((Y_SF - 0.01, ZC - HOLE_BNC / 2), PANEL_BNC + 0.02, HOLE_BNC, fc="w", ec="none"))
ax.add_patch(Rectangle((-H2 + DY, ZB - PCB_T), 2 * H2, PCB_T, fc="#2e7d32"))
for my in [y for _, y in MH.values()]:
    ax.add_patch(Rectangle((my - 2.5, 0), 5.0, SPACER, fc="#b8860b", ec="k", lw=0.3))
for p in parts:
    if p["fp"].startswith(("BNC", "MountingHole")): continue
    ax.add_patch(Rectangle((p["y0"], ZB), p["y1"] - p["y0"], p["h"], fc=cm.viridis(min(p["h"] / 20, 1)), alpha=0.3, ec="k", lw=0.2))
    if p["h"] >= 13: ax.text((p["y0"] + p["y1"]) / 2, ZB + p["h"] + 0.4, p["ref"], ha="center", fontsize=6)
fy = BNC["face_y"] + DY
ax.add_patch(Rectangle((fy - BNC["housing_d"], ZC - BNC["housing_h"] / 2), BNC["housing_d"], BNC["housing_h"], fc="#c0c0c0", ec="k", lw=0.5))
ax.add_patch(Rectangle((fy, ZC - BNC["thread_d"] / 2), BNC["thread"], BNC["thread_d"], fc="#d8d8d8", ec="k", lw=0.5))
ax.add_patch(Rectangle((fy + BNC["thread"], ZC - BNC["bayonet_d"] / 2), BNC["bayonet"], BNC["bayonet_d"], fc="#e8e8e8", ec="k", lw=0.5))
ax.add_patch(Rectangle((Y_SF_OUT, ZC - BNC["hex"] * 0.577), 3.0, BNC["hex"] * 1.155, fc="#a0a0a0", ec="k", lw=0.5))
ax.axhline(LIP_Z, color="r", lw=0.6, ls="--"); ax.text(-40, LIP_Z + 0.4, f"lid lip z {LIP_Z:.2f}", color="r", fontsize=7)
ax.text(-40, ZB + c1["h"] + 0.5, f"C1 top z {ZB + c1['h']:.1f} ({LIP_Z - ZB - c1['h']:.1f} below lip)", fontsize=7)
ax.annotate(f"BNC CL z {ZC:.1f}\n(z_out {ZC + FLOOR:.2f})", (fy + 2, ZC), (fy - 32, ZC + 14), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.5))
ax.annotate(f"spot-faces (red): wall {PANEL_BNC:.2f} thick at hole", (Y_SF + 0.7, ZC + 9), (fy - 38, ZC + 22), fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.5))
ax.set_xlim(-52, 72); ax.set_ylim(-4, 58); ax.set_aspect("equal")
ax.set_xlabel("y (mm): back wall left, output wall right"); ax.set_ylabel("z above inside floor (mm)")
ax.set_title("Hammond 1590C section through an output BNC (all parts projected). Drafted walls from the Hammond DWG.", fontsize=9)
fig.tight_layout(); fig.savefig("img/enclosure_side.png", dpi=150); plt.close(fig)

# --- insertion path figure
ok, seen, reach, th, us, pth = INS[HOLE_BNC]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.6), gridspec_kw=dict(width_ratios=[1, 1.6]))
for Rh, col in ((12.83, "0.55"), (HOLE_BNC, "#1f77b4")):
    s_ = INS[Rh][1]
    if s_.any(): a1.contourf(np.degrees(INS[Rh][3]), INS[Rh][4], s_.T.astype(float), levels=[0.5, 1.5], colors=[col], alpha=0.5)
a1.plot([t for t, u in pth], [u for t, u in pth], "k-", lw=1)
a1.axhline(BNC["thread"] + BNC["bayonet"] + PANEL_BNC + 1, color="k", lw=0.6, ls=":")
a1.axhline(BNC["thread"] + PANEL_BNC, color="r", lw=0.6, ls=":")
a1.set_xlabel("board tilt (deg; negative = BNC end down, back end up)"); a1.set_ylabel("withdrawal of the BNC face along its axis (mm)")
a1.set_title(f"Reachable poses from the seated position: blue = {SLOT_W} x {SLOT_H} slot,\ngrey = dia 12.83 Amphenol hole; red dotted = thread clear, black dotted = fully withdrawn; line = path", fontsize=8)
a2.add_patch(Polygon(wall_poly(1), closed=True, fc="0.8", ec="k", lw=0.5)); a2.add_patch(Polygon(wall_poly(-1), closed=True, fc="0.8", ec="k", lw=0.5))
a2.add_patch(Rectangle((Y_SF - 0.01, ZC - HOLE_BNC / 2), PANEL_BNC + 0.02, HOLE_BNC, fc="w", ec="none"))
a2.add_patch(Rectangle((-yin(0) - WALL_T, -FLOOR), 2 * (yin(0) + WALL_T), FLOOR, fc="0.8", ec="k", lw=0.5))
snap = [pth[int(round(k))] for k in np.linspace(0, len(pth) - 1, 7)]
for i, (t, u) in enumerate(snap):
    col = cm.plasma(i / (len(snap) - 1))
    qq, F, d = pose(math.radians(t), u)
    a2.plot(qq[:, 0], qq[:, 1], ".", ms=0.5, color=col)
    for a0, a1_, dia in ((0, BNC["thread"], BNC["thread_d"]), (BNC["thread"], BNC["thread"] + BNC["bayonet"], BNC["bayonet_d"])):
        A0, A1 = F + a0 * d, F + a1_ * d; nrm = np.array([-d[1], d[0]]) * dia / 2
        a2.add_patch(Polygon([A0 + nrm, A1 + nrm, A1 - nrm, A0 - nrm], closed=True, fill=False, ec=col, lw=0.6))
    a2.text(qq[:, 0].min() - 1, qq[:, 1].max() + 0.5, f"{t:+.0f} deg / {u:.1f}", fontsize=6, color=col)
a2.axhline(RIM_Z, color="k", lw=0.4, ls="--"); a2.text(-50, RIM_Z + 0.5, "rim (lid off)", fontsize=6)
a2.set_xlim(-52, 72); a2.set_ylim(-3, 80); a2.set_aspect("equal")
a2.set_title("Board + spacers + parts envelope along the path (section through a BNC). Assembly runs it in reverse:\n"
             "BNC end down, feed the bayonets into the slots, slide in while levelling, seat the housing faces.", fontsize=8)
a2.set_xlabel("y (mm)"); a2.set_ylabel("z above inside floor (mm)")
fig.tight_layout(); fig.savefig("img/enclosure_insertion.png", dpi=150); plt.close(fig)

# --- 3D block views
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def cuboid(x0, x1, y0, y1, z0, z1):
    vv = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 3, 7, 4)]
    return [[vv[i] for i in q] for q in f]
for elev, azim, fn in ((28, -60, "img/enclosure_3d_a.png"), (35, 120, "img/enclosure_3d_b.png")):
    fig = plt.figure(figsize=(10, 8)); ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(cuboid(-W2, W2, -H2 + DY, H2 + DY, ZB - PCB_T, ZB), fc="#2e7d32", alpha=0.5))
    for p in parts:
        if p["fp"].startswith("MountingHole"): continue
        z1 = ZB + p["h"]
        if p["fp"].startswith("BNC"):
            ax.add_collection3d(Poly3DCollection(cuboid(p["x0"], p["x1"], p["y0"], p["y1"], ZC - 7.8, ZC + 7.8), fc="#c0c0c0", ec="k", lw=0.1, alpha=0.9))
            continue
        ax.add_collection3d(Poly3DCollection(cuboid(p["x0"], p["x1"], p["y0"], p["y1"], ZB, z1), fc=cm.viridis(min(p["h"] / 20, 1)), ec="k", lw=0.1, alpha=0.85))
    for (x0, x1, y0, y1), zc, hh in ((j1box, zJ1, 7.4), (j6box, zJ6, J6C["half_h"])):
        ax.add_collection3d(Poly3DCollection(cuboid(x0, x1, y0, y1, zc - hh, zc + hh), fc="red", alpha=0.25, ec="r", lw=0.3))
    for (x, y) in MH.values():
        ax.add_collection3d(Poly3DCollection(cuboid(x - 2.5, x + 2.5, y - 2.5, y + 2.5, 0, SPACER), fc="#b8860b", alpha=0.9))
    for z in (0, RIM_Z):
        hx, hy = xin(z), yin(z)
        ax.plot([-hx, hx, hx, -hx, -hx], [-hy, -hy, hy, hy, -hy], [z] * 5, color="0.4", lw=0.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ax.plot([sx * xin(0), sx * xin(RIM_Z)], [sy * yin(0), sy * yin(RIM_Z)], [0, RIM_Z], color="0.4", lw=0.8)
            cx, cy = sx * PILLAR_C[0], sy * PILLAR_C[1]
            ax.add_collection3d(Poly3DCollection(cuboid(cx - 3, cx + 3, cy - 3, cy + 3, 0, RIM_Z), fc="0.6", alpha=0.25))
    ax.set_xlim(-60, 60); ax.set_ylim(-48, 48); ax.set_zlim(0, 56); ax.set_box_aspect((120, 96, 56)); ax.view_init(elev, azim)
    ax.set_xlabel("x"); ax.set_ylabel("y (outputs +y)"); ax.set_zlabel("z")
    ax.set_title("Hammond 1590C fit, block model (walls/pillars from the Hammond DWG); red = panel-jack keep-outs", fontsize=9)
    fig.tight_layout(); fig.savefig(fn, dpi=140); plt.close(fig)

# =============================== drilling drawings ===============================
def dim(ax, p0, p1, off, text, horiz=True, fs=7):
    (x0, y0), (x1, y1) = p0, p1
    if horiz:
        yy = y0 + off
        ax.annotate("", (x0, yy), (x1, yy), arrowprops=dict(arrowstyle="<->", lw=0.6))
        ax.plot([x0, x0], [y0, yy], "k-", lw=0.3); ax.plot([x1, x1], [y1, yy], "k-", lw=0.3)
        ax.text((x0 + x1) / 2, yy + 0.8, text, ha="center", va="bottom", fontsize=fs)
    else:
        xx = x0 + off
        ax.annotate("", (xx, y0), (xx, y1), arrowprops=dict(arrowstyle="<->", lw=0.6))
        ax.plot([x0, xx], [y0, y0], "k-", lw=0.3); ax.plot([x1, xx], [y1, y1], "k-", lw=0.3)
        ax.text(xx + 0.8, (y0 + y1) / 2, text, ha="left", va="center", fontsize=fs, rotation=90)
NOTE = ("DATUMS: X/Y = centre of the four 6-32 cover-screw holes (109.50 x 84.00 pattern, Hammond). Z_out = height above the\n"
        f"OUTSIDE bottom face; the inside floor is at Z_out {FLOOR:.2f} (Hammond floor 2.25). Drill wall holes parallel to the floor\n"
        "(2.25 deg off the drafted wall normal). Dimensions in mm. Verify on the actual box before drilling.")
pages = []
# front wall
fig, ax = plt.subplots(figsize=(11.7, 8.3))
L = EXT_L
ax.add_patch(Rectangle((-L / 2, 0), L, BODY_H, fill=False, lw=1.2))
ax.plot([-L / 2, L / 2], [FLOOR, FLOOR], "k--", lw=0.4); ax.text(L / 2 + 1, FLOOR, "inside floor", fontsize=6, va="center")
for x in (-30, -10, 10, 30):
    zz = ZC + FLOOR; rr = SLOT_W / 2; hh = (SLOT_H - SLOT_W) / 2
    tt = np.linspace(0, math.pi, 30)
    ob = [(x + rr * math.cos(a), zz + hh + rr * math.sin(a)) for a in tt] + [(x - rr * math.cos(a), zz - hh - rr * math.sin(a)) for a in tt]
    ax.add_patch(Polygon(ob, closed=True, fill=False, lw=1))
    ax.plot([x - 2, x + 2], [ZC + FLOOR] * 2, "k-", lw=0.3); ax.plot([x, x], [ZC + FLOOR - 2, ZC + FLOOR + 2], "k-", lw=0.3)
ax.add_patch(Rectangle((-SF_OUT_L / 2, ZC + FLOOR - SF_OUT_D / 2), SF_OUT_L, SF_OUT_D, fill=False, lw=0.6, ls="--", ec="r"))
ax.add_patch(Rectangle((-SF_IN_L / 2, ZC + FLOOR - SF_IN_D / 2), SF_IN_L, SF_IN_D, fill=False, lw=0.6, ls=":", ec="b"))
dim(ax, (-30, ZC + FLOOR), (-10, ZC + FLOOR), 22, "20.00"); dim(ax, (-10, ZC + FLOOR), (10, ZC + FLOOR), 22, "20.00")
dim(ax, (10, ZC + FLOOR), (30, ZC + FLOOR), 22, "20.00"); dim(ax, (0, 0), (30, ZC + FLOOR), -13, "30.00 from centre")
dim(ax, (30, 0), (30, ZC + FLOOR), 21, f"Z_out {ZC + FLOOR:.2f}", horiz=False)
ax.axvline(0, color="k", lw=0.3, ls="-.")
ax.text(-L / 2, BODY_H + 9, f"FRONT (OUTPUT) WALL - viewed from outside. 4 x SLOT {SLOT_W} wide x {SLOT_H} high (J2-J5, 031-5431-10RFX).", fontsize=10, weight="bold")
dim(ax, (-30 - SLOT_W / 2, ZC + FLOOR - SLOT_H / 2), (-30 - SLOT_W / 2, ZC + FLOOR + SLOT_H / 2), -16, f"{SLOT_H}", horiz=False)
dim(ax, (-30 - SLOT_W / 2, ZC + FLOOR - SLOT_H / 2), (-30 + SLOT_W / 2, ZC + FLOOR - SLOT_H / 2), -6, f"{SLOT_W}")
ax.text(-L / 2, BODY_H + 3, f"Mill flat, perpendicular to the slot axis: INSIDE strip {SF_IN_L:.0f} x {SF_IN_D:.0f} (blue dotted; cut 0 at its top edge -> "
        f"{Y_SF - yin(ZC - SF_IN_D / 2):.2f} at its bottom) and OUTSIDE strip {SF_OUT_L:.0f} x {SF_OUT_D:.0f} (red dashed;\n0 at its bottom -> "
        f"{yin(ZC + SF_OUT_D / 2) + WALL_T - Y_SF_OUT:.2f} at its top). Finished wall between the strips {PANEL_BNC:.2f} +-0.1. Slots: drill dia 12.9 at +-1.3 mm above/below centre and file to the obround.", fontsize=7)
ax.text(-L / 2, -16, NOTE, fontsize=6.5)
ax.set_xlim(-L / 2 - 6, L / 2 + 14); ax.set_ylim(-22, BODY_H + 14); ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout(); fig.savefig("img/drill_front_wall.png", dpi=160); pages.append(fig)
# left wall (J1) - viewed from outside: +y (front wall) appears on the LEFT
fig, ax = plt.subplots(figsize=(11.7, 8.3)); Wd = EXT_W
ax.add_patch(Rectangle((-Wd / 2, 0), Wd, BODY_H, fill=False, lw=1.2)); ax.plot([-Wd / 2, Wd / 2], [FLOOR, FLOOR], "k--", lw=0.4)
hx = -yJ1                                             # drawing x = -y (viewed from outside the left wall)
ax.add_patch(Circle((hx, zJ1 + FLOOR), J1C["hole"][0] / 2, fill=False, lw=1)); ax.plot([hx - 2, hx + 2], [zJ1 + FLOOR] * 2, "k-", lw=0.3)
ax.plot([hx - J1C["hole"][0] / 2 + (J1C["hole"][0] - J1C["hole"][1]), hx - J1C["hole"][0] / 2 + (J1C["hole"][0] - J1C["hole"][1])], [zJ1 + FLOOR - 3, zJ1 + FLOOR + 3], "k-", lw=0.6)
ax.axvline(0, color="k", lw=0.3, ls="-.")
dim(ax, (0, zJ1 + FLOOR), (hx, zJ1 + FLOOR), 12, f"{abs(yJ1):.2f} toward the back wall")
dim(ax, (hx, 0), (hx, zJ1 + FLOOR), 10, f"Z_out {zJ1 + FLOOR:.2f}", horiz=False)
ax.text(-Wd / 2, BODY_H + 9, f"LEFT END WALL (input) - viewed from outside; front/output wall to the LEFT. J1 Amphenol 031-221-RFX.", fontsize=10, weight="bold")
ax.text(-Wd / 2, BODY_H + 3, f"D-hole dia {J1C['hole'][0]} with flat {J1C['hole'][1]} across (Amphenol panel type U) - confirm on the 031-221-RFX drawing.\n"
        "Connector inserted from outside; nut + lock washer inside.", fontsize=7)
ax.text(-Wd / 2, -16, NOTE, fontsize=6.5)
ax.set_xlim(-Wd / 2 - 6, Wd / 2 + 14); ax.set_ylim(-22, BODY_H + 14); ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout(); fig.savefig("img/drill_left_wall.png", dpi=160); pages.append(fig)
# back wall (J6) - viewed from outside: +x appears on the RIGHT
fig, ax = plt.subplots(figsize=(11.7, 8.3))
ax.add_patch(Rectangle((-L / 2, 0), L, BODY_H, fill=False, lw=1.2)); ax.plot([-L / 2, L / 2], [FLOOR, FLOOR], "k--", lw=0.4)
ax.add_patch(Circle((xJ6, zJ6 + FLOOR), J6C["hole"][0] / 2, fill=False, lw=1)); ax.axvline(0, color="k", lw=0.3, ls="-.")
dim(ax, (0, zJ6 + FLOOR), (xJ6, zJ6 + FLOOR), 12, f"{xJ6:.2f} toward the U1 / right end")
dim(ax, (xJ6, 0), (xJ6, zJ6 + FLOOR), 10, f"Z_out {zJ6 + FLOOR:.2f}", horiz=False)
ax.text(-L / 2, BODY_H + 9, "BACK WALL (DC input) - viewed from outside; the U1 end is on the RIGHT. J6 Switchcraft 722A.", fontsize=10, weight="bold")
ax.text(-L / 2, BODY_H + 3, f"D-hole dia {J6C['hole'][0]:.2f} with flat {J6C['hole'][1]:.2f} across (Switchcraft 5/16-32 bushing) - confirm on the 722A drawing.\n"
        "Jack body inside, washer + nut outside; turn the solder lugs horizontal.", fontsize=7)
ax.text(-L / 2, -16, NOTE, fontsize=6.5)
ax.set_xlim(-L / 2 - 6, L / 2 + 14); ax.set_ylim(-22, BODY_H + 14); ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout(); fig.savefig("img/drill_back_wall.png", dpi=160); pages.append(fig)
# floor, viewed from INSIDE (as the PCB sits) and the mirrored outside view note
fig, ax = plt.subplots(figsize=(11.7, 8.3))
ax.add_patch(Rectangle((-EXT_L / 2, -EXT_W / 2), EXT_L, EXT_W, fill=False, lw=1.2))
for sx in (-1, 1):
    for sy in (-1, 1): ax.add_patch(Circle((sx * SCREW[0] / 2, sy * SCREW[1] / 2), 1.3, fc="k"))
ax.add_patch(Polygon([(x, y + DY) for x, y in board_outline()], closed=True, fill=False, ec="#2e7d32", lw=0.6, ls="--"))
for r, (x, y) in MH.items():
    ax.add_patch(Circle((x, y), FLOOR_HOLE / 2, fill=False, lw=1)); ax.plot([x - 2.5, x + 2.5], [y, y], "k-", lw=0.3); ax.plot([x, x], [y - 2.5, y + 2.5], "k-", lw=0.3)
    ax.text(x + 2.6, y + 1.2, f"{r}\n({x:+.2f}, {y:+.2f})", fontsize=7)
ax.axvline(0, color="k", lw=0.3, ls="-.", ymax=0.9); ax.axhline(0, color="k", lw=0.3, ls="-.")
ax.text(-EXT_L / 2, EXT_W / 2 + 11, f"FLOOR - viewed from INSIDE (output wall at the top). 5 x dia {FLOOR_HOLE} for M3 spacer screws.", fontsize=10, weight="bold")
ax.text(-EXT_L / 2, EXT_W / 2 + 3, "Coordinates (x, y) from the centre of the cover-screw pattern; + y toward the output wall, + x toward the U1 end.\n"
        "When marking from the OUTSIDE (box upside down) the x values change sign. Dashed green = PCB outline.", fontsize=7)
ax.text(-EXT_L / 2, -EXT_W / 2 - 14, NOTE, fontsize=6.5)
ax.set_xlim(-EXT_L / 2 - 6, EXT_L / 2 + 6); ax.set_ylim(-EXT_W / 2 - 18, EXT_W / 2 + 18); ax.set_aspect("equal"); ax.axis("off")
fig.tight_layout(); fig.savefig("img/drill_floor.png", dpi=160); pages.append(fig)
with PdfPages("drill_drawing_1590C.pdf") as pdf:
    for f in pages: pdf.savefig(f)
for f in pages: plt.close(f)
