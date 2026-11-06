"""Enclosure fit check for the Hammond 1590BB: heights, wall connectors, standoffs; writes figures + a report.
   All enclosure numbers that are not from a manufacturer drawing are marked ASSUMED (see docs)."""
import sys, json, pcbnew
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
sys.path.insert(0, ".")
import place
OX, OY = 150.0, 100.0
TM = pcbnew.ToMM

# ---------------- enclosure (Hammond 1590BB) ----------------
EXT = (119.5, 94.0)           # external L x W (Hammond)
BODY_DEPTH = 30.0             # body depth less lid (1.18 in, Hammond/distributor listing)
LID = 4.0                     # lid 0.16 in
FLOOR = 2.5                   # ASSUMED floor thickness
LID_LIP = 1.5                 # ASSUMED allowance for any lid lip / gasket intruding into the cavity
IN_TOP = (112.66, 87.16)      # ASSUMED inside at rim
IN_FLOOR = (110.36, 84.86)    # ASSUMED inside at floor (draft)
BOSS = [(sx * 51.75, sy * 39.0) for sx in (-1, 1) for sy in (-1, 1)]   # ASSUMED lid-screw boss centres
BOSS_R = 4.0                  # ASSUMED boss radius
CAVITY = BODY_DEPTH - FLOOR   # floor to rim
USABLE = CAVITY - LID_LIP
STANDOFF = 4.0                # M3 x 4 mm spacers (selected so the 19.1 mm C1 clears the lid)
PCB_T = 1.6
ZB = STANDOFF + PCB_T         # PCB top above inside floor
def wall_half(z, i):          # inner half-size at height z (linear draft between floor and rim)
    return (IN_FLOOR[i] + (IN_TOP[i] - IN_FLOOR[i]) * z / CAVITY) / 2

# ---------------- seated part heights above PCB top (mm, max) ----------------
H = {
 "R_Axial_DIN0207": (3.0, "Yageo MFR-25 body dia 2.5 max, lying flat"),
 "D_DO-35": (2.5, "DO-35 dia 1.9 max"),
 "D_DO-41": (3.2, "DO-41 dia 2.7 max"),
 "L_Axial_L7.0mm_D3.3mm": (3.8, "Bourns 78FR axial, flat (footprint body dia 3.3)"),
 "C_Disc_D3.8mm": (4.7, "KEMET C315 seated H 4.66 max"),
 "C_Radial_KEMET_C320": (7.4, "KEMET C320 seated H 7.36 max"),
 "C_Disc_W3.2mm": (7.7, "KEMET C325 seated H 7.62 max"),
 "C_Rect_L7.2mm_W7.2mm": (13.0, "KEMET R82 4.7uF 13.0 / 2.2uF 11.0"),
 "C_Rect_L18.0mm": (19.1, "KEMET R60EI4470AA30J H 19.1"),
 "CP_Radial_D5.0mm": (12.5, "Panasonic ECA 5x11 + 1.5 sleeve/bulge"),
 "CP_Radial_D8.0mm": (13.0, "Panasonic FR 8x11.5 + 1.5"),
 "L_Radial_D9.5mm": (13.0, "Bourns RLB0914 seated H 13 max"),
 "TO-92": (7.0, "TO-92 body 5.2 + ~1.8 seating (assembly note)"),
 "TO-220-3_Horizontal": (5.0, "TO-220 lying flat, 4.7 incl. tab"),
 "GDT_Bourns": (8.5, "Bourns 2027 dia 8.0, lying flat"),
 "Fuse_Littelfuse_RXEF": (12.7, "RXEF030 seated H 12.7 max"),
 "TestPoint_Keystone": (8.0, "Keystone 5000 (estimate)"),
 "BNC_Amphenol": (16.4, "031-5431-10RFX CL 8.6 + housing 15.6/2"),
 "MountingHole": (2.4, "M3 pan head"),
 "Pads_": (3.0, "wire / coax pigtail solder joint"),
}
def height(fpname):
    for k, v in H.items():
        if k in fpname: return v
    raise KeyError(fpname)

b = pcbnew.LoadBoard("hfmc.kicad_pcb")
parts = []
for fp in b.GetFootprints():
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox() if fp.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else fp.GetBoundingBox(False, False)
    name = str(fp.GetFPID().GetLibItemName())
    h, src = height(name)
    if fp.GetReference().startswith("C") and "R82CC4220" in fp.GetProperty("MPN"): h, src = 11.0, "KEMET R82 2.2uF H 11.0"
    parts.append(dict(ref=fp.GetReference(), x0=TM(bb.GetLeft()) - OX, x1=TM(bb.GetRight()) - OX,
                      y0=TM(bb.GetTop()) - OY, y1=TM(bb.GetBottom()) - OY, h=h, src=src, fp=name))

rep = []
def out(s): rep.append(s); print(s)
out(f"Stack: floor 0, standoff {STANDOFF}, PCB {ZB - PCB_T:.1f}-{ZB:.1f}, cavity to rim {CAVITY:.1f} (ASSUMED floor {FLOOR}), usable {USABLE:.1f}")
tall = sorted(parts, key=lambda p: -p["h"])[:6]
for p in tall:
    out(f"  {p['ref']:5s} top {ZB + p['h']:5.1f} mm above floor -> margin to usable top {USABLE - ZB - p['h']:4.1f} mm ({p['src']})")
worst = max(ZB + p["h"] for p in parts)
ok_height = worst <= USABLE

# ---------------- wall connectors ----------------
# box volumes inside the cavity: (name, wall, centre along wall, centre z, half-width along wall, half-height, depth from inner wall)
BNC_Z = ZB + 8.6
CONN = [
 ("J1 031-221-RFX (input, left wall)", "left", -8.0, 16.5, 7.4, 7.4, 15.0),
 ("J6 722A DC jack (back wall)", "back", 36.0, 19.5, 8.0, 5.0, 16.0),
]
def conn_box(c):
    name, wall, a, z, hw, hh, d = c
    if wall == "left":
        xw = -wall_half(z, 0); return (xw, xw + d, a - hw, a + hw, z - hh, z + hh)
    if wall == "right":
        xw = wall_half(z, 0); return (xw - d, xw, a - hw, a + hw, z - hh, z + hh)
    if wall == "back":
        yw = -wall_half(z, 1); return (a - hw, a + hw, yw, yw + d, z - hh, z + hh)
conn_ok = True
for c in CONN:
    x0, x1, y0, y1, z0, z1 = conn_box(c)
    under = [p for p in parts if p["x1"] > x0 and p["x0"] < x1 and p["y1"] > y0 and p["y0"] < y1]
    top_under = max([ZB + p["h"] for p in under] + [ZB])
    bosses = [bx for bx in BOSS if (x0 - BOSS_R < bx[0] < x1 + BOSS_R) and (y0 - BOSS_R < bx[1] < y1 + BOSS_R)]
    m_lo = z0 - top_under; m_hi = USABLE - z1
    good = m_lo >= 0.5 and m_hi >= 0.5 and not bosses
    conn_ok &= good
    out(f"{c[0]}: centre z {c[3]:.1f} above inside floor; under it: {', '.join(p['ref'] for p in under) or 'nothing'}; "
        f"clearance below {m_lo:.1f} mm, to usable top {m_hi:.1f} mm, boss conflict {bool(bosses)} -> {'OK' if good else 'CHECK'}")
# PCB BNCs vs wall
for ref in ("J2", "J3", "J4", "J5"):
    fp = b.FindFootprintByReference(ref)
gap = wall_half(BNC_Z, 1) - place.WALL_Y
out(f"PCB BNC front face y = {place.WALL_Y:.2f}; drafted inner wall at BNC height y = {wall_half(BNC_Z, 1):.2f} -> gap {gap:.2f} mm (ASSUMED wall data)")
# board vs walls / bosses
W, Hh, N = place.BOARD_W / 2, place.BOARD_H / 2, place.NOTCH
out(f"Board {place.BOARD_W} x {place.BOARD_H}: side clearance at PCB height x {wall_half(ZB, 0) - W:.2f}, y {wall_half(ZB, 1) - Hh:.2f} mm")
for bx, by in BOSS:
    # nearest board point to boss centre (board notched corners)
    cx = min(max(bx, -W), W); cy = min(max(by, -Hh), Hh)
    if abs(cx) > W - N and abs(cy) > Hh - N:   # inside notch: nearest is notch edges
        cands = [(W - N if bx > 0 else -(W - N), by if abs(by) <= Hh else (Hh if by > 0 else -Hh)),
                 (bx if abs(bx) <= W else (W if bx > 0 else -W), Hh - N if by > 0 else -(Hh - N))]
        cands = [(min(max(px, -W), W), min(max(py, -Hh), Hh)) for px, py in cands]
        d = min(((bx - px) ** 2 + (by - py) ** 2) ** .5 for px, py in cands)
    else:
        d = ((bx - cx) ** 2 + (by - cy) ** 2) ** .5
    out(f"  boss at ({bx:+.2f},{by:+.2f}): clearance to board edge {d - BOSS_R:.2f} mm")
out(f"RESULT height {'OK' if ok_height else 'FAIL'}, wall connectors {'OK' if conn_ok else 'CHECK'}")
open("enclosure_report.txt", "w").write("\n".join(rep) + "\n")
json.dump(dict(STANDOFF=STANDOFF, ZB=ZB, BNC_Z=BNC_Z, CONN=CONN, USABLE=USABLE, CAVITY=CAVITY), open("enclosure.json", "w"), indent=1)

# ---------------- figures ----------------
fig, ax = plt.subplots(figsize=(11, 8.6))
ax.add_patch(Rectangle((-EXT[0] / 2, -EXT[1] / 2), *EXT, fill=False, lw=1.5, ec="k"))
ax.add_patch(Rectangle((-IN_TOP[0] / 2, -IN_TOP[1] / 2), *IN_TOP, fill=False, lw=0.8, ec="0.4", ls="--"))
ax.add_patch(Rectangle((-IN_FLOOR[0] / 2, -IN_FLOOR[1] / 2), *IN_FLOOR, fill=False, lw=0.8, ec="0.4"))
for bx, by in BOSS: ax.add_patch(Circle((bx, by), BOSS_R, fc="0.8", ec="0.3"))
pts = [(-W + N, -Hh), (W - N, -Hh), (W - N, -Hh + N), (W, -Hh + N), (W, Hh - N), (W - N, Hh - N), (W - N, Hh),
       (-W + N, Hh), (-W + N, Hh - N), (-W, Hh - N), (-W, -Hh + N), (-W + N, -Hh + N)]
ax.add_patch(Polygon(pts, closed=True, fc="#2e7d32", alpha=0.25, ec="#1b5e20"))
import matplotlib.cm as cm
for p in parts:
    col = cm.viridis(min(p["h"] / 20, 1))
    ax.add_patch(Rectangle((p["x0"], p["y0"]), p["x1"] - p["x0"], p["y1"] - p["y0"], fc=col, alpha=0.55, ec="k", lw=0.3))
    if p["h"] >= 11 or p["ref"].startswith(("J", "U", "MH")):
        ax.text((p["x0"] + p["x1"]) / 2, (p["y0"] + p["y1"]) / 2, f"{p['ref']}\n{p['h']:.0f}", ha="center", va="center", fontsize=6)
for c in CONN:
    x0, x1, y0, y1, z0, z1 = conn_box(c)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="red", lw=1.2, ls="--"))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, c[0].split(" ")[0] + f"\nz {c[3]:.0f}", color="red", ha="center", va="center", fontsize=7)
for x in (-30, -10, 10, 30):   # BNC bodies through the front wall
    ax.add_patch(Rectangle((x - 6.35, place.WALL_Y), 12.7, 20.9 - 7.37 + 7.37, fill=False, ec="blue", lw=0.8))
ax.set_xlim(-64, 64); ax.set_ylim(70, -52); ax.set_aspect("equal")
ax.set_title(f"1590BB top view (lid removed), PCB on {STANDOFF:.0f} mm standoffs; part heights in mm above PCB; red = panel-connector keep-outs\n"
             "front wall (outputs) at bottom, back wall top; ASSUMED inside dims/bosses: verify on the actual box", fontsize=9)
ax.set_xlabel("mm (board centre = box centre)"); fig.tight_layout(); fig.savefig("enclosure_top.png", dpi=150)

# side section through the front wall (looking from +x)
fig, ax = plt.subplots(figsize=(11, 4.2))
ax.add_patch(Rectangle((-EXT[1] / 2, -FLOOR), EXT[1], FLOOR, fc="0.7"))
ax.plot([-wall_half(0, 1), -wall_half(CAVITY, 1)], [0, CAVITY], "k"); ax.plot([wall_half(0, 1), wall_half(CAVITY, 1)], [0, CAVITY], "k")
ax.axhline(CAVITY, color="k", lw=0.8, ls=":"); ax.axhline(USABLE, color="r", lw=0.8, ls="--")
ax.text(-45, USABLE + 0.3, f"usable top {USABLE:.1f} (rim {CAVITY:.1f} minus {LID_LIP} lid allowance)", fontsize=7, color="r")
ax.add_patch(Rectangle((-Hh, ZB - PCB_T), 2 * Hh, PCB_T, fc="#2e7d32"))
for p in parts:
    ax.add_patch(Rectangle((p["y0"], ZB), p["y1"] - p["y0"], p["h"], fc=cm.viridis(min(p["h"] / 20, 1)), alpha=0.35, ec="k", lw=0.2))
    if p["h"] >= 13: ax.text((p["y0"] + p["y1"]) / 2, ZB + p["h"] + 0.3, p["ref"], ha="center", fontsize=6)
ax.add_patch(Circle((place.WALL_Y, BNC_Z), 0.4, color="b")); ax.text(place.WALL_Y - 9, BNC_Z, f"BNC CL {BNC_Z:.1f}", fontsize=7, color="b")
for s in (-1, 1):
    ax.add_patch(Rectangle((s * 46.5 - 2.75, 0), 5.5, STANDOFF, fc="0.5"))
ax.set_xlim(-50, 50); ax.set_ylim(-4, 31); ax.set_aspect("equal")
ax.set_xlabel("y (mm): back wall left, front (output) wall right"); ax.set_ylabel("z above inside floor (mm)")
ax.set_title("Side section, all parts projected: heights vs usable cavity (ASSUMED floor/lid data)", fontsize=9)
fig.tight_layout(); fig.savefig("enclosure_side.png", dpi=150)

# isometric 3D view (boxes = courtyard x seated height)
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def cuboid(x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 3, 7, 4)]
    return [[v[i] for i in q] for q in f]
for elev, azim, fn in ((28, -60, "enclosure_3d_a.png"), (35, 120, "enclosure_3d_b.png")):
    fig = plt.figure(figsize=(10, 7.5)); ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(cuboid(-W, W, -Hh, Hh, ZB - PCB_T, ZB), fc="#2e7d32", alpha=0.5))
    for p in parts:
        if p["ref"].startswith("MH"): continue
        col = "#c0c0c0" if p["ref"].startswith("J") else cm.viridis(min(p["h"] / 20, 1))
        ax.add_collection3d(Poly3DCollection(cuboid(p["x0"], p["x1"], p["y0"], p["y1"], ZB, ZB + p["h"]), fc=col, ec="k", lw=0.1, alpha=0.85))
    for c in CONN:
        ax.add_collection3d(Poly3DCollection(cuboid(*conn_box(c)), fc="red", alpha=0.25, ec="r", lw=0.3))
    # enclosure walls (inner, wireframe) and floor
    for z in (0, CAVITY):
        hx, hy = wall_half(z, 0), wall_half(z, 1)
        ax.plot([-hx, hx, hx, -hx, -hx], [-hy, -hy, hy, hy, -hy], [z] * 5, color="0.4", lw=0.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            ax.plot([sx * wall_half(0, 0), sx * wall_half(CAVITY, 0)], [sy * wall_half(0, 1), sy * wall_half(CAVITY, 1)], [0, CAVITY], color="0.4", lw=0.8)
    for bx, by in BOSS:
        ax.add_collection3d(Poly3DCollection(cuboid(bx - BOSS_R, bx + BOSS_R, by - BOSS_R, by + BOSS_R, 0, CAVITY), fc="0.6", alpha=0.3))
    ax.set_xlim(-60, 60); ax.set_ylim(-48, 48); ax.set_zlim(0, 40); ax.set_box_aspect((120, 96, 40))
    ax.view_init(elev, azim); ax.set_xlabel("x"); ax.set_ylabel("y (outputs +y)"); ax.set_zlabel("z")
    ax.set_title("1590BB fit (block model, ASSUMED enclosure interior); red = panel-jack keep-outs", fontsize=9)
    fig.tight_layout(); fig.savefig(fn, dpi=140); plt.close(fig)
