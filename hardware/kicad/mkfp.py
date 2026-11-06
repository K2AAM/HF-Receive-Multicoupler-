"""Write the project-specific footprints (dimensions from manufacturer drawings; see notes in each descr)."""
import uuid, os
D = "hfmc.pretty"
def u(): return str(uuid.uuid4())
def line(x1,y1,x2,y2,layer,w):
    return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}") (tstamp {u()}))\n'
def rect(x1,y1,x2,y2,layer,w):
    return line(x1,y1,x2,y1,layer,w)+line(x2,y1,x2,y2,layer,w)+line(x2,y2,x1,y2,layer,w)+line(x1,y2,x1,y1,layer,w)
def circ(cx,cy,r,layer,w):
    return f'  (fp_circle (center {cx} {cy}) (end {cx+r} {cy}) (stroke (width {w}) (type solid)) (fill none) (layer "{layer}") (tstamp {u()}))\n'
def pad(num,x,y,shape,sx,sy,drill,extra=""):
    return f'  (pad "{num}" thru_hole {shape} (at {x} {y}) (size {sx} {sy}) (drill {drill}) (layers "*.Cu" "*.Mask"){extra} (tstamp {u()}))\n'
def text(kind,val,x,y,layer,hide=False):
    return f'  (fp_text {kind} "{val}" (at {x} {y}) (layer "{layer}"){" hide" if hide else ""}\n    (effects (font (size 1 1) (thickness 0.15)))\n    (tstamp {u()})\n  )\n'
def fp(name, descr, body, ref_xy=(0,-3), val_xy=(0,3)):
    s = f'(footprint "{name}" (version 20221018) (generator pcbnew)\n  (layer "F.Cu")\n  (descr "{descr}")\n  (attr through_hole)\n'
    s += text("reference","REF**",ref_xy[0],ref_xy[1],"F.SilkS") + text("value",name,val_xy[0],val_xy[1],"F.Fab")
    s += text("user","${REFERENCE}",0,0,"F.Fab")
    s += body + ")\n"
    open(os.path.join(D, name + ".kicad_mod"), "w").write(s)

# 1. Amphenol 031-5431-10RFX right-angle bulkhead BNC (customer drawing 31-5431-10RFX rev E).
#    Origin = centre contact. Panel (front) toward -Y. Fork pins (shell, dia 2.0 holes) at (+/-5.08, -5.08);
#    centre contact (0,0) and ground post (-2.54, 0) dia 0.89 holes. Housing 14.5 W x 15.6 H; front face
#    7.37 mm ahead of the fork-pin row; thread 8.9 + bayonet 12 beyond the front face; CL 8.6 above PCB.
ff = -5.08 - 7.37   # front face y
b = ""
b += pad(1, 0, 0, "circle", 1.7, 1.7, 0.9)
b += pad(2, -2.54, 0, "circle", 1.7, 1.7, 0.9)
b += pad(2, -5.08, -5.08, "circle", 3.2, 3.2, 2.0)
b += pad(2, 5.08, -5.08, "circle", 3.2, 3.2, 2.0)
b += rect(-7.25, ff, 7.25, ff + 13.8, "F.Fab", 0.1)                 # housing behind panel
b += rect(-6.35, ff - 20.9, 6.35, ff, "F.Fab", 0.1)                 # 1/2-28 thread + bayonet (through wall)
# silk only on the part of the housing that sits over the board (board edge is 3.5 mm behind the wall)
b += rect(-7.25, ff + 3.8, 7.25, ff + 13.8, "F.SilkS", 0.12)
b += rect(-7.5, ff, 7.5, ff + 14.05, "F.CrtYd", 0.05)
b += line(-9, ff, 9, ff, "Dwgs.User", 0.1)                          # panel inner face reference
fp("BNC_Amphenol_031-5431-10RFX_Horizontal",
   "Amphenol RF 031-5431-10RFX BNC R/A PCB bulkhead jack, rear mount. Hole pattern from Amphenol customer drawing 31-5431-10RFX rev E (2016): forks dia 2.0 at 10.16 c/c, 0.89 holes 2.54 c/c, rows 5.08 apart; front face 7.37 ahead of fork row; CL 8.6 above PCB",
   b, (0, ff + 15.5), (0, 3))

# 2. TO-92 inline, courtyard trimmed at the flat face so two devices can be glued face-to-face.
b = ""
b += pad(1, 0, 0, "rect", 1.05, 1.5, 0.75) + pad(2, 1.27, 0, "oval", 1.05, 1.5, 0.75) + pad(3, 2.54, 0, "oval", 1.05, 1.5, 0.75)
b += line(-0.5, 1.75, 3.04, 1.75, "F.Fab", 0.1)
b += f'  (fp_arc (start -0.483625 1.753625) (mid 1.27 -2.48) (end 3.023625 1.753625) (stroke (width 0.1) (type solid)) (layer "F.Fab") (tstamp {u()}))\n'
# silk: rounded back only (flat face is glued to the partner, so no silk there)
b += f'  (fp_arc (start -0.982 1.3) (mid 1.27 -2.6) (end 3.522 1.3) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (tstamp {u()}))\n'
b += rect(-1.46, -2.73, 4.0, 1.86, "F.CrtYd", 0.05)
fp("TO-92_Inline_ThermalPair",
   "TO-92 inline (E-B-C, onsemi), pads as KiCad TO-92_Inline; courtyard ends at the flat face (y=+1.86) so a mating device rotated 180 deg can sit 3.7 mm away, faces glued for thermal coupling",
   b, (1.27, -3.6), (1.27, 3.2))

# 3. Bourns 2027-09-BLF GDT, axial: body 8.0 dia x 6.0 L, leads 0.8 dia.
b = pad(1, 0, 0, "circle", 2.4, 2.4, 1.1) + pad(3, 12.7, 0, "circle", 2.4, 2.4, 1.1)
b += rect(3.35, -4.0, 9.35, 4.0, "F.Fab", 0.1) + rect(3.25, -4.1, 9.45, 4.1, "F.SilkS", 0.12)
b += line(1.55, 0, 3.25, 0, "F.SilkS", 0.12) + line(9.45, 0, 11.15, 0, "F.SilkS", 0.12)
b += rect(-1.45, -4.35, 14.15, 4.35, "F.CrtYd", 0.05)
fp("GDT_Bourns_2027_Axial_D8.0mm_L6.0mm_P12.70mm_Horizontal",
   "Bourns 2027 series 2-electrode GDT, axial leaded (2027-xx-BLF): body 8 dia x 6 mm, lead 0.8 mm", b, (6.35, -5.4), (6.35, 5.4))

# 4. Radial ceramic, universal 2.54 / 5.08 lead spacing (pad 2 duplicated).
b = pad(1, 0, 0, "circle", 1.6, 1.6, 0.8) + pad(2, 2.54, 0, "circle", 1.6, 1.6, 0.8) + pad(2, 5.08, 0, "circle", 1.6, 1.6, 0.8)
# body outline covers a 5.08 x 3.18 (KEMET C32x) body in either lead position
b += rect(-1.27, -1.59, 6.35, 1.59, "F.Fab", 0.1) + rect(-1.55, -1.85, 6.63, 1.85, "F.CrtYd", 0.05)
b += line(-1.4, -1.72, 6.48, -1.72, "F.SilkS", 0.12) + line(-1.4, 1.72, 6.48, 1.72, "F.SilkS", 0.12)
fp("C_Disc_W3.2mm_P2.54mm_P5.08mm_Universal",
   "Radial ceramic (KEMET C32x Goldmax, 5.08 x 3.18 body), accepts 2.54 mm or 5.08 mm lead spacing (pad 2 duplicated)", b, (2.54, -2.9), (2.54, 2.9))

# 4b. KEMET Goldmax C320 (100 nF X7R): body L 5.08 max, T 3.18 max, H 7.36 seated max, leads 2.54.
b = pad(1, 0, 0, "rect", 1.6, 1.6, 0.8) + pad(2, 2.54, 0, "circle", 1.6, 1.6, 0.8)
b += rect(-1.27, -1.59, 3.81, 1.59, "F.Fab", 0.1) + rect(-1.55, -1.85, 4.09, 1.85, "F.CrtYd", 0.05)
b += line(-1.4, -1.72, 3.94, -1.72, "F.SilkS", 0.12) + line(-1.4, 1.72, 3.94, 1.72, "F.SilkS", 0.12)
fp("C_Radial_KEMET_C320_L5.08mm_T3.18mm_P2.54mm",
   "KEMET Goldmax 300 C320 radial MLCC: L 5.08 x T 3.18 max, seated H 7.36 max, 2.54 mm lead spacing", b, (1.27, -2.9), (1.27, 2.9))

# 5. Littelfuse RXEF030 PPTC radial: 7.4 x 3.0 body, lead spacing 5.1, lead 0.51.
b = pad(1, 0, 0, "circle", 1.8, 1.8, 0.9) + pad(2, 5.1, 0, "circle", 1.8, 1.8, 0.9)
b += rect(-1.15, -1.5, 6.25, 1.5, "F.Fab", 0.1) + rect(-1.25, -1.6, 6.35, 1.6, "F.SilkS", 0.12) + rect(-1.4, -1.75, 6.5, 1.75, "F.CrtYd", 0.05)
fp("Fuse_Littelfuse_RXEF_7.4x3.0mm_P5.10mm", "Littelfuse PolySwitch RXEF radial (RXEF030): 7.4 x 3.0 mm body, 5.1 mm lead spacing", b, (2.55, -2.7), (2.55, 2.7))

# 6. Coax pigtail pads for the panel-mount input BNC: centre (1), braid (2) twice.
b = pad(1, 0, 0, "circle", 2.2, 2.2, 1.1) + pad(2, 3.81, 0, "circle", 3.2, 3.2, 1.8) + pad(2, -3.81, 0, "circle", 3.2, 3.2, 1.8)
b += rect(-5.65, -1.85, 5.65, 1.85, "F.CrtYd", 0.05)
fp("Pads_CoaxPigtail_RG316", "Solder pads for a short RG-316 pigtail from a panel-mount BNC: pad 1 centre conductor, pads 2 shield/braid", b, (0, -2.8), (0, 2.8))

# 7. Power wire pads (J6): 2 x 1.3 mm holes, 5.08 pitch.
b = pad(1, 0, 0, "rect", 2.6, 2.6, 1.3) + pad(2, 5.08, 0, "circle", 2.6, 2.6, 1.3)
b += rect(-1.55, -1.55, 6.63, 1.55, "F.CrtYd", 0.05)
fp("Pads_PowerWire_1x02_P5.08mm", "Solder pads for the panel-mount DC jack leads (pad 1 = +13.8 V, pad 2 = GND), 0.5 mm^2 wire", b, (2.54, -2.6), (2.54, 2.6))
print(sorted(os.listdir(D)))
