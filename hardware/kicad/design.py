"""Single source of truth for the Rev B build A prototype PCB: parts, values, footprints, MPNs and nets.
Net names follow sim/scripts/gen.py node names so connectivity can be checked against the simulation."""
FP = dict(
    R="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
    CK="Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm",                       # KEMET C315: 3.81 x 2.54 body, 2.54 mm leads
    C320="hfmc:C_Radial_KEMET_C320_L5.08mm_T3.18mm_P2.54mm",              # KEMET C320: 5.08 x 3.18 body, 2.54 mm leads
    CU="hfmc:C_Disc_W3.2mm_P2.54mm_P5.08mm_Universal",
    F47="Capacitor_THT:C_Rect_L7.2mm_W7.2mm_P5.00mm_FKS2_FKP2_MKS2_MKP2",  # KEMET R82 4.7u (7.2x7.2x13) / 2.2u (7.2x6x11)
    F47C1="Capacitor_THT:C_Rect_L18.0mm_W11.0mm_P15.00mm_FKS3_FKP3",       # KEMET R60EI 18x11x19.1
    E5="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm", E8="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
    LAX="Inductor_THT:L_Axial_L7.0mm_D3.3mm_P10.16mm_Horizontal_Fastron_MICC",
    L4="Inductor_THT:L_Radial_D9.5mm_P5.00mm_Fastron_07HVP",
    D35="Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal", D41="Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
    Q="Package_TO_SOT_THT:TO-92_Inline", QP="hfmc:TO-92_Inline_ThermalPair",
    U1="Package_TO_SOT_THT:TO-220-3_Horizontal_TabDown",
    BNC="hfmc:BNC_Amphenol_031-5431-10RFX_Horizontal", GDT="hfmc:GDT_Bourns_2027_Axial_D8.0mm_L6.0mm_P12.70mm_Horizontal",
    PTC="hfmc:Fuse_Littelfuse_RXEF_7.4x3.0mm_P5.10mm", COAXPADS="hfmc:Pads_CoaxPigtail_RG316",
    PWRPADS="hfmc:Pads_PowerWire_1x02_P5.08mm", TP="TestPoint:TestPoint_Keystone_5000-5004_Miniature",
    MH="MountingHole:MountingHole_3.2mm_M3_Pad_Via")
RES = ("Device", "R"); CAP = ("Device", "C"); CPOL = ("Device", "C_Polarized"); IND = ("Device", "L")
DIO = ("Device", "D"); SCH = ("Device", "D_Schottky")
NPN = ("Transistor_BJT", "2N3904"); PNP = ("Transistor_BJT", "2N3906")

def mfr25(v): return f"Yageo MFR-25FBF52-{v}"
P = []   # (ref, (lib,sym), value, footprint, {pin: net}, mpn, note, gen_name)
def add(ref, sym, val, fp, pins, mpn, note="", gen=None): P.append(dict(ref=ref, sym=sym, value=val, fp=fp, pins=pins, mpn=mpn, note=note, gen=gen))

# ---- input
add("J1", ("Connector_Generic", "Conn_01x02"), "ANT IN (panel BNC pigtail)", FP["COAXPADS"], {"1": "IN", "2": "GND"},
    "Amphenol RF 031-221-RFX (panel BNC, wired with ~60 mm RG-316)", "Panel jack on the LEFT short wall (see docs/pcb-mechanical.md); RG-316 pigtail to these pads, braid to both GND pads")
add("GDT1", ("Device", "GDT_2Pin"), "90V", FP["GDT"], {"1": "IN", "3": "GND"}, "Bourns 2027-09-BLF", "Ground pad bonded to MH1 (chassis) by a short wide pour")
add("C1", CAP, "4.7u 100V film", FP["F47C1"], {"1": "IN", "2": "N1"}, "KEMET R60EI4470AA30J", "18x11x19.1 mm, 15 mm pitch", gen="CIN1")
add("RBL", RES, "10k", FP["R"], {"1": "N1", "2": "GND"}, mfr25("10K"), gen="RBL")
add("D1", DIO, "1N4148", FP["D35"], {"2": "N1", "1": "DA"}, "onsemi 1N4148", gen="DA1")
add("D2", DIO, "1N4148", FP["D35"], {"2": "DA", "1": "GND"}, "onsemi 1N4148", gen="DA2")
add("D3", DIO, "1N4148", FP["D35"], {"2": "GND", "1": "DB"}, "onsemi 1N4148", gen="DB1")
add("D4", DIO, "1N4148", FP["D35"], {"2": "DB", "1": "N1"}, "onsemi 1N4148", gen="DB2")
# ---- 7-pole LPF
add("C4", CAP, "43p C0G 5%", FP["CU"], {"1": "N1", "2": "GND"}, "KEMET C325C430JAG5TA", gen="CF1")
add("L1", IND, "220n", FP["LAX"], {"1": "N1", "2": "N2"}, "Bourns 78FR22K-RC (VNA-selected +/-3%)", gen="LF1")
add("C5", CAP, "100p C0G 2%", FP["CK"], {"1": "N2", "2": "GND"}, "KEMET C315C101G1G5TA", gen="CF2")
add("L2", IND, "270n", FP["LAX"], {"1": "N2", "2": "N3"}, "Bourns 78FR27K-RC (VNA-selected +/-3%)", gen="LF2")
add("C6", CAP, "100p C0G 2%", FP["CK"], {"1": "N3", "2": "GND"}, "KEMET C315C101G1G5TA", gen="CF3")
add("L3", IND, "220n", FP["LAX"], {"1": "N3", "2": "N4"}, "Bourns 78FR22K-RC (VNA-selected +/-3%)", gen="LF3")
add("C7", CAP, "43p C0G 5%", FP["CU"], {"1": "N4", "2": "GND"}, "KEMET C325C430JAG5TA", gen="CF4")
# ---- gain stage (build A)
add("C2", CAP, "2.2u film", FP["F47"], {"1": "N4", "2": "BN"}, "KEMET R82CC4220DQ70J", gen="CBN")
add("C3", CAP, "2.2u film", FP["F47"], {"1": "N4", "2": "BP"}, "KEMET R82CC4220DQ70J", gen="CBP")
add("Q1N", NPN, "2N3904", FP["Q"], {"3": "X", "2": "BN", "1": "EN"}, "onsemi 2N3904BU", gen="Q1N")
add("Q1P", PNP, "2N3906", FP["Q"], {"3": "X", "2": "BP", "1": "EP"}, "onsemi 2N3906BU", gen="Q1P")
add("RE1", RES, "56", FP["R"], {"1": "EN", "2": "GND"}, mfr25("56R"), "Build A 56 (B 56, C 47)", gen="RE1")
add("RE2", RES, "56", FP["R"], {"1": "VCC", "2": "EP"}, mfr25("56R"), "Build A 56 (B 56, C 47)", gen="RE2")
add("R1A", RES, "1.5k", FP["R"], {"1": "X", "2": "RM"}, mfr25("1K5"), gen="R1A")
add("R1B", RES, "1.5k", FP["R"], {"1": "RM", "2": "BN"}, mfr25("1K5"), gen="R1B")
add("C14", CPOL, "10u 25V", FP["E5"], {"1": "RM", "2": "GND"}, "Panasonic ECA-1EM100", "+ to RM", gen="CRM")
add("R2", RES, "3.3k", FP["R"], {"1": "BN", "2": "GND"}, mfr25("3K3"), gen="R2")
add("R3A", RES, "1.5k", FP["R"], {"1": "X", "2": "RMP"}, mfr25("1K5"), gen="R3A")
add("R3B", RES, "1.5k", FP["R"], {"1": "RMP", "2": "BP"}, mfr25("1K5"), gen="R3B")
add("C15", CPOL, "10u 25V", FP["E5"], {"1": "VCC", "2": "RMP"}, "Panasonic ECA-1EM100", "+ to VCC", gen="CRMP")
add("R4", RES, "3.3k", FP["R"], {"1": "BP", "2": "VCC"}, mfr25("3K3"), gen="R4")
add("C9", CAP, "2.2u film", FP["F47"], {"1": "X", "2": "LX"}, "KEMET R82CC4220DQ70J", gen="CLX")
add("RL", RES, "220", FP["R"], {"1": "LX", "2": "GND"}, mfr25("220R"), "RLX, all builds", gen="RLX")
add("RF", RES, "220", FP["R"], {"1": "X", "2": "FB"}, mfr25("220R"), "Build A 220 (B 270, C 330)", gen="RF")
add("C8", CAP, "2.2u film", FP["F47"], {"1": "FB", "2": "N4"}, "KEMET R82CC4220DQ70J", gen="CFB")
# ---- diamond buffer
add("Q2A", PNP, "2N3906", FP["QP"], {"3": "GND", "2": "X", "1": "E2A"}, "onsemi 2N3906BU", "Thermal pair: glue flat face to Q5 (doc Q2)", gen="Q2A")
add("RX1", RES, "15", FP["R"], {"1": "E2A", "2": "D1"}, mfr25("15R"), gen="RX1")
add("RPU", RES, "360", FP["R"], {"1": "VCC", "2": "D1"}, mfr25("360R"), gen="RPU")
add("Q3A", NPN, "2N3904", FP["QP"], {"3": "VCC", "2": "X", "1": "E3A"}, "onsemi 2N3904BU", "Thermal pair: glue flat face to Q6 (doc Q3)", gen="Q3A")
add("RX2", RES, "15", FP["R"], {"1": "D2", "2": "E3A"}, mfr25("15R"), gen="RX2")
add("RPD", RES, "360", FP["R"], {"1": "D2", "2": "GND"}, mfr25("360R"), gen="RPD")
add("RC", RES, "4.7", FP["R"], {"1": "VCC", "2": "VCF"}, mfr25("4R7"), gen="RCOL")
add("C16", CAP, "100n", FP["C320"], {"1": "VCF", "2": "GND"}, "KEMET C320C104K5R5TA", gen="CCOL")
add("Q2", NPN, "2N3904", FP["QP"], {"3": "VCF", "2": "D1", "1": "EF"}, "onsemi 2N3904BU", "Thermal pair: glue flat face to Q3 (doc Q2A)", gen="Q2")
add("RE3", RES, "3.3", FP["R"], {"1": "EF", "2": "OUT"}, mfr25("3R3"), gen="REO1")
add("Q3", PNP, "2N3906", FP["QP"], {"3": "GND", "2": "D2", "1": "EG"}, "onsemi 2N3906BU", "Thermal pair: glue flat face to Q4 (doc Q3A)", gen="Q3")
add("RE4", RES, "3.3", FP["R"], {"1": "EG", "2": "OUT"}, mfr25("3R3"), gen="REO2")
# ---- ports
for k in range(1, 5):
    add(f"C{9+k}", CAP, "4.7u film", FP["F47"], {"1": "OUT", "2": f"XO{k}"}, "KEMET R82CC4470DQ30K", gen=f"CO{k}")
    add(f"RS{k}", RES, "51", FP["R"], {"1": f"XO{k}", "2": f"P{k}"}, mfr25("51R"), gen=f"RS{k}")
    add(f"J{k+1}", ("Connector", "Conn_Coaxial"), f"OUT{k}", FP["BNC"], {"1": f"P{k}", "2": "GND"}, "Amphenol RF 031-5431-10RFX")
# ---- supply
add("J6", ("Connector_Generic", "Conn_01x02"), "13.8V IN (panel jack)", FP["PWRPADS"], {"1": "J6A", "2": "GND"},
    "Switchcraft 722A (2.1 mm panel jack, centre +)", "Wired to the back-wall jack")
add("F1", ("Device", "Polyfuse"), "RXEF030", FP["PTC"], {"1": "J6A", "2": "J6B"}, "Littelfuse RXEF030")
add("D5", SCH, "1N5819", FP["D41"], {"2": "J6B", "1": "UIN"}, "onsemi 1N5819")
add("C20", CPOL, "220u 25V", FP["E8"], {"1": "UIN", "2": "GND"}, "Panasonic EEU-FR1E221")
add("C17", CAP, "100n", FP["C320"], {"1": "UIN", "2": "GND"}, "KEMET C320C104K5R5TA", "C20B")
add("U1", ("Regulator_Linear", "LM317_TO-220"), "LM317T", FP["U1"], {"3": "UIN", "2": "UOUT", "1": "UADJ"}, "TI LM317T/NOPB", "Lies flat, tab down on solder mask over a copper keep-out (tab = VOUT); optional M3 nylon screw, no heatsink")
add("D6", DIO, "1N4002", FP["D41"], {"2": "UOUT", "1": "UIN"}, "onsemi 1N4002")
add("D7", DIO, "1N4002", FP["D41"], {"2": "UADJ", "1": "UOUT"}, "onsemi 1N4002")
add("R10", RES, "240", FP["R"], {"1": "UOUT", "2": "UADJ"}, mfr25("240R"))
add("R11", RES, "1.65k", FP["R"], {"1": "UADJ", "2": "GND"}, mfr25("1K65"))
add("C21", CPOL, "10u 25V", FP["E5"], {"1": "UADJ", "2": "GND"}, "Panasonic ECA-1EM100")
add("C23", CPOL, "10u 25V", FP["E5"], {"1": "UOUT", "2": "GND"}, "Panasonic ECA-1EM100", "U1 output cap (CU1O)")
add("L4", IND, "10u", FP["L4"], {"1": "UOUT", "2": "L4B"}, "Bourns RLB0914-100KL")
add("RDAMP", RES, "1.0", FP["R"], {"1": "L4B", "2": "VCC"}, mfr25("1R"))
add("C22", CPOL, "470u 16V", FP["E8"], {"1": "VCC", "2": "GND"}, "Panasonic EEU-FR1C471")
add("C18", CAP, "100n", FP["C320"], {"1": "VCC", "2": "GND"}, "KEMET C320C104K5R5TA", "C22B")
# ---- extra local bypass on the amplifier rail (layout addition; ideal rail in simulation)
for ref, note in [("C19", "rail entry to amplifier"), ("C24", "at RE2/R4/C15"), ("C25", "at RPU"), ("C26", "at Q3A collector")]:
    add(ref, CAP, "100n", FP["C320"], {"1": "VCC", "2": "GND"}, "KEMET C320C104K5R5TA", "Local bypass " + note)
# ---- test points and mounting
for ref, net, note in [("TP1", "VCC", "+9.8 V rail"), ("TP2", "X", "gain-stage collector node X"), ("TP3", "OUT", "common output node"),
                       ("TP4", "EF", "RE3 top: I(Q2) = V(TP4-TP3)/3.3"), ("TP5", "EG", "RE4 bottom: I(Q3) = V(TP3-TP5)/3.3"),
                       ("TP6", "EN", "RE1 top: I(Q1N) = V(TP6)/56"), ("TP7", "GND", "ground"), ("TP8", "GND", "ground")]:
    add(ref, ("Connector", "TestPoint"), net, FP["TP"], {"1": net}, "Keystone 5001" if net == "GND" else "Keystone 5000", note)
for k in range(1, 6):
    add(f"MH{k}", ("Mechanical", "MountingHole_Pad"), "M3", FP["MH"], {"1": "GND"}, "M3 x 4 mm spacer (brass, chassis bond) + M3 screws",
        "Chassis bond next to GDT1" if k == 1 else "Board mounting / chassis bond")

# ---- KiCad references must be prefix + number. Map documentation names (README, docs, sim) to KiCad refs.
DOC2REF = {"Q1N": "Q1", "Q1P": "Q2", "Q2A": "Q3", "Q3A": "Q4", "Q2": "Q5", "Q3": "Q6",
           "RBL": "R1", "RE1": "R2", "RE2": "R3", "RF": "R4", "RL": "R5", "R1A": "R6", "R1B": "R7", "R2": "R8",
           "R3A": "R9", "R3B": "R10", "R4": "R11", "RPU": "R12", "RPD": "R13", "RX1": "R14", "RX2": "R15", "RC": "R16",
           "RE3": "R17", "RE4": "R18", "RS1": "R19", "RS2": "R20", "RS3": "R21", "RS4": "R22", "R10": "R23", "R11": "R24",
           "RDAMP": "R25"}
for p in P:
    p["doc"] = p["ref"]
    p["ref"] = DOC2REF.get(p["ref"], p["ref"])
REF2DOC = {p["ref"]: p["doc"] for p in P}
assert len(set(p["ref"] for p in P)) == len(P)
