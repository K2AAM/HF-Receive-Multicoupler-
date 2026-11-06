"""Independent per-part tolerance sampling for the Rev B multicoupler.

Every physical part is varied independently: no two parts share a random draw.
Tolerances come from the selected parts' published specifications (see TOL_SOURCES).
Transistor parameter ranges are model-uncertainty estimates, not datasheet limits;
see MODEL_PROVENANCE.
"""
import numpy as np, re, gen

# Published tolerance of each selected part type (fractional, +/-), with the reason.
TOL_SOURCES = {
    "res_1pct": (0.01, "1 % metal-film resistors (BOM spec)"),
    "L_78FR_K": (0.10, "Bourns 78FR22K-RC / 78FR27K-RC: +/-10 % (DigiKey M10148-ND, 118-78FR27K-RC-ND)"),
    "L_selected": (0.03, "78FR inductors measured on the VNA and binned to +/-3 % (procedure in bring-up doc)"),
    "C_C0G_J": (0.05, "C0G radial +/-5 % (J)"),
    "C_C0G_G": (0.02, "KEMET C315 C0G radial +/-2 % (G), e.g. C315C101G1G5TA"),
    "C_film_K": (0.10, "WIMA MKS4 film +/-10 % (K)"),
    "C_elec": (0.20, "aluminium electrolytic +/-20 %"),
    "rail": (0.045, "LM317 VREF 1.20-1.30 V (TI datasheet min/max) with 1 % R10/R11: rail 9.81 V +/-4.5 %"),
}

MODEL_PROVENANCE = (
    "2N3904/2N3906: simplified Gummel-Poon models (mfg=NXP) from the LTspice standard.bjt library, "
    "mirror github.com/mpkopec/ltspice-lib cmp/standard.bjt. They have no ISE/NE low-current beta "
    "droop, no fT-versus-current roll-off beyond IKF, and fixed junction capacitances. "
    "Sampling: BF spans the datasheet hFE range at 10 mA (100-300 for both types), and IS is "
    "log-uniform x0.56-1.79 (about +/-15 mV Vbe, lot-to-lot). TF and CJC are not sampled; they are "
    "tested as deliberate corners (x0.7 and x1.4) because the models' dynamic parameters are the "
    "least certain.")

RESISTORS = ["RBL", "RE1", "RE2", "RF", "RLX", "R1A", "R1B", "R2", "R3A", "R3B", "R4",
             "RPU", "RPD", "RX1", "RX2", "RCOL", "REO1", "REO2", "RS1", "RS2", "RS3", "RS4", "RS5"]
FILM = ["CIN1", "CBN", "CBP", "CFB", "CLX", "CO1", "CO2", "CO3", "CO4", "CO5"]
ELEC = ["CRM", "CRMP"]
LPF_L = ["LF1", "LF2", "LF3"]
LPF_C = ["CF1", "CF2", "CF3", "CF4"]
DEVICES = [("QN", "2N3904"), ("QP", "2N3906"), ("QDP", "2N3906"), ("QDN", "2N3904"), ("QF", "2N3904"), ("QG", "2N3906")]
MODEL_BF = {"2N3904": 300.0, "2N3906": 200.0}
HFE_RANGE = (100.0, 300.0)

LIB = open(gen.MODELS).read()

def _num(s):
    s = s.strip().lower(); m = {'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3}
    return float(s[:-1]) * m[s[-1]] if s[-1] in m else float(s)

def model_line(base, newname, scale):
    m = re.search(r"\.model " + base + r" (NPN|PNP)\((.*)\)", LIB, re.IGNORECASE)
    typ, par = m.group(1), m.group(2)
    for key, k in scale.items():
        pat = re.compile(r"\b(" + key + r")=([-\d.eE]+[a-zA-Z]?)", re.IGNORECASE)
        if not pat.search(par):
            raise ValueError(f"{key} not in model {base}")
        par = pat.sub(lambda mm: f"{mm.group(1)}={_num(mm.group(2))*k:g}", par, count=1)
    return f".model {newname} {typ}({par})"

def sample(rng, build="A", L="L_78FR_K", C="C_C0G_J", temps=(0, 27, 50), devices=True, extra=None):
    """One Monte Carlo draw. Uniform within +/-tol for passives (independent per part)."""
    P = gen.params(build)
    def u(t): return 1 + rng.uniform(-t, t)
    for k in RESISTORS: P[k] *= u(TOL_SOURCES["res_1pct"][0])
    for k in FILM: P[k] *= u(TOL_SOURCES["C_film_K"][0])
    for k in ELEC: P[k] *= u(TOL_SOURCES["C_elec"][0])
    for k in LPF_L: P[k] *= u(TOL_SOURCES[L][0])
    for k in LPF_C: P[k] *= u(TOL_SOURCES[C][0])
    for q in ("QLF1", "QLF2", "QLF3"): P[q] = rng.uniform(40, 60)   # datasheet Q min 40 @ 25 MHz
    P['VCC'] *= u(TOL_SOURCES['rail'][0])
    P['TEMP'] = float(rng.choice(temps))
    if devices:
        lines = []
        for key, base in DEVICES:
            hfe = np.exp(rng.uniform(*np.log(HFE_RANGE)))
            isk = np.exp(rng.uniform(np.log(0.56), np.log(1.79)))
            name = f"M_{key}"
            lines.append(model_line(base, name, {"BF": hfe / MODEL_BF[base], "IS": isk}))
            P[key] = name
        P['MODELS'] = "\n".join(lines)
    if extra: P.update(extra)
    return P

def corner_models(tf=1.0, cjc=1.0, bf=1.0):
    """All six devices shifted together: a deliberate corner, not a random sample."""
    lines = []; over = {}
    for key, base in DEVICES:
        name = f"C_{key}"
        lines.append(model_line(base, name, {"TF": tf, "CJC": cjc, "BF": bf}))
        over[key] = name
    over['MODELS'] = "\n".join(lines)
    return over
