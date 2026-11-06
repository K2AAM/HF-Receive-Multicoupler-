"""HF receive multicoupler, Rev B: netlist generator and verified ngspice harness.

Every physical part has its own parameter key, so tolerance analyses can vary
parts independently. Builds A/B/C are defined explicitly in BUILDS.

Every simulation runs in its own fresh temporary directory. A run counts as
successful only if all of these pass:
  - the process exits with status 0
  - the deck reaches its completion marker
  - no simulator error or abort text appears in the log
  - every expected output file exists, is non-empty, was written during this
    run, parses as finite numbers, and covers the requested sweep or time span
Any failure raises SimError. Nothing silently falls back to old data.
"""
import subprocess, numpy as np, re, os, tempfile, shutil, time

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models_bjt.lib")

# ---------------------------------------------------------------- parts
# Nominal value of every physical part (recommended build A). Units: SI.
NOMINAL = dict(
    VCC=9.81,                      # ideal-rail value used when SUPPLY='ideal' (= full-supply model rail at 13.8 V in)
    CIN1=4.7e-6, RBL=10e3, CLAMP=1,
    # 7-pole LPF
    CF1=43e-12, LF1=220e-9, CF2=100e-12, LF2=270e-9, CF3=100e-12, LF3=220e-9, CF4=43e-12,
    QLF1=40, QLF2=40, QLF3=40,     # inductor Q (series R defined at 30 MHz)
    # gain stage
    CBN=2.2e-6, CBP=2.2e-6, RE1=56, RE2=56, RF=220, CFB=2.2e-6, CLX=2.2e-6, RLX=220,
    R1A=1.5e3, R1B=1.5e3, R2=3.3e3, R3A=1.5e3, R3B=1.5e3, R4=3.3e3, CRM=10e-6, CRMP=10e-6,
    # diamond buffer
    RPU=360, RPD=360, RX1=15, RX2=15, RCOL=4.7, REO1=3.3, REO2=3.3,
    # ports (per branch)
    CO1=4.7e-6, CO2=4.7e-6, CO3=4.7e-6, CO4=4.7e-6, CO5=4.7e-6,
    RS1=51, RS2=51, RS3=51, RS4=51, RS5=51,
    # devices
    QN='2N3904', QP='2N3906', QDP='2N3906', QDN='2N3904', QF='2N3904', QG='2N3906',
    NPORT=4, PAR=1, TEMP=27, SUPPLY='ideal',
)

# Builds differ only in the gain-setting parts. Every key is given explicitly.
BUILDS = {
    "A": dict(RE1=56, RE2=56, RF=220, RLX=220),   # recommended, about +1.7 dB
    "B": dict(RE1=56, RE2=56, RF=270, RLX=220),   # about +3.2 dB
    "C": dict(RE1=47, RE2=47, RF=330, RLX=220),   # about +5.5 dB
}
RECOMMENDED = "A"

def params(build=RECOMMENDED, **over):
    if build not in BUILDS:
        raise KeyError(build)
    P = dict(NOMINAL); P.update(BUILDS[build]); P.update(over); P['BUILD'] = build
    return P

# ---------------------------------------------------------------- supply
# 'full' supply: J6 13.8 V source with resistance -> PTC (as resistance) -> 1N5819 -> C20
# -> LM317 behavioural model -> C_out -> L4 (+DCR) -> C22 (+ESR) -> rail VCC.
SUPPLY_NOM = dict(VIN=13.8, RSRC=0.05,
                  RPTC=1.33,        # F1 Littelfuse RXEF030: Rmin 0.88, Rmax 1.33 ohm initial, R1max 2.1 ohm post-trip
                  VF5='D1N5819', C20=220e-6, C20ESR=0.15,
                  CU1OUT=10e-6, CU1ESR=0.5,         # C23, 10 uF at U1 output pin (TI recommends ~1 uF tantalum or 25 uF Al)
                  R10=240, R11=1.65e3, C21=10e-6,
                  ZU1_R=0.005, ZU1_L=30e-9,          # LM317 output impedance approximation (low-f R, HF rise)
                  L4=10e-6, L4DCR=0.048,             # Bourns RLB0914-100KL: 10 uH +/-10 %, DCR 48 mohm max, 2.7 A, SRF 20 MHz
                  RDAMP=1.0, C22=470e-6, C22ESR=0.10,
                  VREF=1.25, IADJ=50e-6, ILIM=1.5, VDROP=1.7, RAMP=1e-3, VRIP_AC=0)

def supply_block(S):
    """Behavioural LM317 (pass current drawn from U1 input, so input current is real).
    Target voltage = ADJ + VREF, limited by VIN - VDROP; pass current limited to ILIM.
    Regulator line rejection is ideal in this model; use the VRIP_AC injection at U1's output
    for a conservative no-rejection bound. Includes TI-recommended protection diodes
    D6 (OUT->IN) and D7 (ADJ->OUT)."""
    S = {**SUPPLY_NOM, **S}
    return f"""* ---- supply ----
VIN J6 0 dc {S['VIN']} PWL(0 0 {S['RAMP']} {S['VIN']})
RSRC J6 J6A {S['RSRC']}
RPTC J6A J6B {S['RPTC']}
D5 J6B UIN {S['VF5']}
C20 UIN C20E {S['C20']}
R20E C20E 0 {S['C20ESR']}
C20B UIN 0 100n
BUT UTGT 0 V = min(v(UADJ)+{S['VREF']}, v(UIN)-{S['VDROP']})
BPASS UIN UPI I = min({S['ILIM']}, max(0, (v(UTGT)-v(UPI))*50))
VRIP UPI UPJ dc 0 ac {S['VRIP_AC']}
RZU UPJ UPK {S['ZU1_R']}
LZU UPK UOUT {S['ZU1_L']}
CPI UPI 0 1n
IADJ UOUT UADJ {S['IADJ']}
D6 UOUT UIN D1N4002
D7 UADJ UOUT D1N4002
R10 UOUT UADJ {S['R10']}
R11 UADJ 0 {S['R11']}
C21 UADJ 0 {S['C21']}
CU1O UOUT CU1E {S['CU1OUT']}
RU1E CU1E 0 {S['CU1ESR']}
L4 UOUT L4A {S['L4']}
RL4DCR L4A L4B {S['L4DCR']}
RDMP L4B VCC {S['RDAMP']}
C22 VCC C22E {S['C22']}
R22E C22E 0 {S['C22ESR']}
C22B VCC 0 100n
.model D1N5819 D(IS=31.7u RS=0.051 N=1.373 CJO=110p M=0.35 BV=40)
.model D1N4002 D(IS=14.1n RS=33.9m N=1.984 CJO=51.2p M=0.3 BV=100)
"""

# ---------------------------------------------------------------- netlist
def netlist(P, analysis, loads="", extra="", supply_over=None):
    """P: full parameter dict from params(). analysis: .control body (without .control/.endc)."""
    n = P['NPORT']; par = P['PAR']
    Le = '5n' if par else '0.001n'
    tiny = '0.01n'
    L = [f".include {MODELS}", P.get('MODELS', '')]
    L.append(f"CIN1 IN XIN1 {P['CIN1']}\nRIN1 XIN1 XIN2 0.02\nLIN1 XIN2 N1 {'8n' if par else tiny}")
    L.append(f"RBL N1 0 {P['RBL']}")
    if P['CLAMP']:
        L.append("DA1 N1 DA D1N4148\nDA2 DA 0 D1N4148\nDB1 0 DB D1N4148\nDB2 DB N1 D1N4148")
    w30 = 2 * np.pi * 30e6
    L.append(f"CF1 N1 0 {P['CF1']}")
    L.append(f"LF1 N1 NL1 {P['LF1']}\nRLF1 NL1 N2 {w30*P['LF1']/P['QLF1']}")
    L.append(f"CF2 N2 0 {P['CF2']}")
    L.append(f"LF2 N2 NL2 {P['LF2']}\nRLF2 NL2 N3 {w30*P['LF2']/P['QLF2']}")
    L.append(f"CF3 N3 0 {P['CF3']}")
    L.append(f"LF3 N3 NL3 {P['LF3']}\nRLF3 NL3 N4 {w30*P['LF3']/P['QLF3']}")
    L.append(f"CF4 N4 0 {P['CF4']}")
    if par: L.append("CPN4 N4 0 1p")
    L.append(f"CBN N4 XNB {P['CBN']}\nRBNE XNB YNB 0.02\nLBNE YNB BN {'6n' if par else tiny}")
    L.append(f"CBP N4 XPB {P['CBP']}\nRBPE XPB YPB 0.02\nLBPE YPB BP {'6n' if par else tiny}")
    L.append(f"Q1N X BN EN1 {P['QN']}\nLEN EN1 EN {Le}\nRE1 EN 0 {P['RE1']}")
    L.append(f"Q1P X BP EP1 {P['QP']}\nLEP EP1 EP {Le}\nRE2 VCC EP {P['RE2']}")
    L.append(f"R1A X RM {P['R1A']}\nR1B RM BN {P['R1B']}\nCRM RM 0 {P['CRM']}\nR2 BN 0 {P['R2']}")
    L.append(f"R3A X RMP {P['R3A']}\nR3B RMP BP {P['R3B']}\nCRMP VCC RMP {P['CRMP']}\nR4 BP VCC {P['R4']}")
    L.append(f"CLX X LX {P['CLX']}\nRLX LX 0 {P['RLX']}")
    L.append(f"RF X FB {P['RF']}\nCFB FB FB2 {P['CFB']}\nLFB FB2 N4 {'6n' if par else tiny}")
    if par: L.append("CPX X 0 2p")
    tp = f" temp={P['TPRE']}" if P.get('TPRE') is not None else ""
    to = f" temp={P['TOUT']}" if P.get('TOUT') is not None else ""
    L.append(f"Q2A 0 X E2A {P['QDP']}{tp}\nRX1 E2A D1 {P['RX1']}\nRPU VCC D1 {P['RPU']}")
    L.append(f"Q3A VCC X E3A {P['QDN']}{tp}\nRX2 D2 E3A {P['RX2']}\nRPD D2 0 {P['RPD']}")
    L.append(f"RCOL VCC VCF {P['RCOL']}\nCCOL VCF 0 100n")
    L.append(f"Q2 VCF D1 EF1 {P['QF']}{to}\nLEF EF1 EF {Le}\nREO1 EF OUT {P['REO1']}")
    L.append(f"Q3 0 D2 EG1 {P['QG']}{to}\nLEG EG1 EG {Le}\nREO2 EG OUT {P['REO2']}")
    if par: L.append("CPOUT OUT 0 3p\nCPD1 D1 0 1p\nCPD2 D2 0 1p")
    for k in range(1, n + 1):
        L.append(f"CO{k} OUT XO{k} {P[f'CO{k}']}\nRO{k}E XO{k} YO{k} 0.02\nLO{k}E YO{k} ZO{k} {'8n' if par else tiny}")
        L.append(f"RS{k} ZO{k} SO{k} {P[f'RS{k}']}")
        L.append(f"LS{k} SO{k} P{k} {'8n' if par else tiny}" + (f"\nCPP{k} P{k} 0 2p" if par else ""))
    if P['SUPPLY'] == 'ideal':
        L.append(f"VCC VCC 0 {P['VCC']}")
    else:
        L.append(supply_block(supply_over or {}))
    L.append(loads); L.append(extra)
    L.append(f".options temp={P['TEMP']} tnom=27")
    L.append(".control\n" + analysis.strip() + "\necho @@SIM_COMPLETE@@\n.endc")
    return "* HF multicoupler rev B\n" + "\n".join(L) + "\n.end\n"

# ---------------------------------------------------------------- runner
class SimError(RuntimeError):
    pass

ERROR_PATTERNS = [
    r"\berror\b", r"could not find", r"can't find", r"timestep too small",
    r"aborted", r"singular matrix", r"no such vector", r"no such device",
    r"unknown (model|parameter|subckt)", r"source stepping failed",
    r"iteration limit reached", r"fatal", r"not converge", r"checkvalid", r"is not available", r"can.t interpolate", r"lengths too small",
]
ERR_RE = re.compile("|".join(ERROR_PATTERNS), re.IGNORECASE)
KEEP_FAILED = os.environ.get("MC_KEEP_FAILED") == "1"

def run(cir, outputs=None, timeout=None):
    """Run one deck in a fresh directory.
    outputs: {filename: dict(xmin=, xmax=, min_rows=, ncols=)}; filenames are relative to the run dir.
    Returns (log, {filename: ndarray}). Raises SimError on any failure."""
    outputs = outputs or {}
    if timeout is None: timeout = float(os.environ.get("MC_SIM_TIMEOUT", 900))
    d = tempfile.mkdtemp(prefix="mcsim_")
    ok = False
    try:
        deck = os.path.join(d, "deck.cir")
        with open(deck, "w") as fh:
            fh.write(cir)
        t0 = time.time()
        try:
            p = subprocess.run(["ngspice", "-b", "deck.cir"], cwd=d, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise SimError(f"timeout after {timeout} s")
        log = p.stdout + "\n" + p.stderr
        if p.returncode != 0:
            raise SimError(f"ngspice exit status {p.returncode}: " + _tail(log))
        bad = [ln for ln in log.splitlines() if ERR_RE.search(ln)]
        if bad:
            raise SimError("simulator reported: " + " | ".join(bad[:5]))
        if "@@SIM_COMPLETE@@" not in log:
            raise SimError("deck did not reach completion marker: " + _tail(log))
        data = {}
        for fn, spec in outputs.items():
            path = os.path.join(d, fn)
            if not os.path.exists(path):
                raise SimError(f"missing output {fn}")
            st = os.stat(path)
            if st.st_size == 0:
                raise SimError(f"empty output {fn}")
            if st.st_mtime < t0 - 1:
                raise SimError(f"stale output {fn}")
            a = validate_table(np.loadtxt(path, ndmin=2), **spec)
            data[fn] = a
        ok = True
        return log, data
    finally:
        if ok or not KEEP_FAILED:
            shutil.rmtree(d, ignore_errors=True)

def validate_table(a, xmin=None, xmax=None, min_rows=2, ncols=None, rtol=1e-6):
    """Check a wrdata table: finite, enough rows, expected columns, x covers [xmin, xmax]."""
    if a.size == 0 or a.shape[0] < min_rows:
        raise SimError(f"too few rows ({a.shape[0]} < {min_rows})")
    if ncols is not None and a.shape[1] != ncols:
        raise SimError(f"expected {ncols} columns, got {a.shape[1]}")
    if not np.all(np.isfinite(a)):
        raise SimError("non-finite values in output")
    x = a[:, 0]
    if xmin is not None and x[0] > xmin * (1 + rtol) + 1e-30:
        raise SimError(f"sweep starts at {x[0]:.4g}, expected {xmin:.4g}")
    if xmax is not None and x[-1] < xmax * (1 - rtol):
        raise SimError(f"sweep/transient ended at {x[-1]:.6g}, expected {xmax:.6g} (partial run)")
    return a

def _tail(log, n=600):
    return log[-n:].replace("\n", " | ")

def parse_prints(log, names):
    vals = {}
    for ln in log.splitlines():
        m = re.match(r"\s*(\S+)\s*=\s*([-+\d.eE]+)\s*$", ln)
        if m: vals[m.group(1)] = float(m.group(2))
    missing = [n for n in names if n not in vals]
    if missing:
        raise SimError(f"missing printed values {missing}")
    return vals

# ---------------------------------------------------------------- terminations
def src50(P, node="IN", emf=2.0):
    return f"VGIN GIN 0 dc 0 ac {emf}\nRGIN GIN {node} 50"

def portloads(P, drive=None, z='50', zmap=None):
    """Port terminations. zmap: {k: spice text} overrides for port k (must reference node Pk)."""
    s = []
    for k in range(1, P['NPORT'] + 1):
        if zmap and k in zmap:
            s.append(zmap[k])
        elif drive == k:
            s.append(f"VG{k} G{k} 0 dc 0 ac 2\nRG{k} G{k} P{k} 50")
        else:
            s.append(f"RL{k} P{k} 0 {z}")
    return "\n".join(s)

OP_NAMES = ["v(x)", "v(out)", "v(d1)", "v(d2)", "v(bn)", "v(bp)", "v(vcf)", "v(vcc)",
            "@q1n[ic]", "@q1p[ic]", "@q2a[ic]", "@q3a[ic]", "@q2[ic]", "@q3[ic]"]

def op(P):
    loads = "RGIN IN 0 50\n" + portloads(P)
    curr = "i(vcc)" if P['SUPPLY'] == 'ideal' else "i(vin)"
    log, _ = run(netlist(P, f"op\nprint {' '.join(OP_NAMES)} {curr}", loads))
    v = parse_prints(log, OP_NAMES + [curr])
    v['Irail_mA'] = -v[curr] * 1e3
    return v

def _ac_files(P, drive_port, fstart, fstop, ppd, extra_loads=""):
    ndec = np.log10(fstop / fstart)
    spec = dict(xmin=fstart, xmax=fstop, min_rows=int(ppd * ndec * 0.95))
    nodes = ["in"] + [f"p{k}" for k in range(1, P['NPORT'] + 1)]
    if drive_port == 0:
        loads = src50(P) + "\n" + portloads(P)
    else:
        loads = "RGIN IN 0 50\n" + portloads(P, drive=drive_port)
    an = f"ac dec {ppd} {fstart} {fstop}\nwrdata ac.txt " + " ".join(f"v({n})" for n in nodes)
    log, data = run(netlist(P, an, loads + "\n" + extra_loads), {"ac.txt": dict(spec, ncols=3 * len(nodes))})
    a = data["ac.txt"]
    f = a[:, 0]
    V = np.array([a[:, 3 * i + 1] + 1j * a[:, 3 * i + 2] for i in range(len(nodes))])
    return f, V

def smatrix(P, fstart=1e4, fstop=2e9, ppd=30):
    """Full (NPORT+1)-port S-matrix, port 0 = antenna input, ports 1..N = outputs, 50-ohm reference."""
    N = P['NPORT'] + 1
    S = None
    for j in range(N):
        f, V = _ac_files(P, j, fstart, fstop, ppd)
        if S is None: S = np.zeros((len(f), N, N), complex)
        for i in range(N):
            S[:, i, j] = V[i] - (1.0 if i == j else 0.0)
    return f, S

def ac(P, fstart=1e3, fstop=200e6, ppd=40):
    f, Vf = _ac_files(P, 0, fstart, fstop, ppd)
    f2, Vr = _ac_files(P, 2, fstart, fstop, ppd)
    db = lambda x: 20 * np.log10(np.abs(x))
    return dict(f=f, S21=db(Vf[1]), S11=db(Vf[0] - 1), iso=db(Vr[3]), rev=db(Vr[0]), S22=db(Vr[2] - 1),
                zin=50 * Vf[0] / (2 - Vf[0]), zout=50 * Vr[2] / (2 - Vr[2]))

def nf_breakdown(P, freqs=(1e6, 10e6, 30e6, 50e6)):
    """NF at port 1, excluding the noise of port 1's own 50-ohm load (the receiver).
    Per-element percentages of the remaining output noise power."""
    loads = src50(P) + "\n" + portloads(P)
    PP = dict(P); PP['TEMP'] = 16.85
    res = {}
    for f0 in freqs:
        log, _ = run(netlist(PP, f"noise v(p1) vgin dec 1 {f0} {f0} 1\nsetplot noise1\nprint all", loads))
        v = {}
        for ln in log.splitlines():
            m = re.match(r"\s*onoise_(\S+?)\s*=\s*([-\d.eE+]+)", ln)
            if m: v[m.group(1)] = float(m.group(2)) ** 2
        if 'spectrum' not in v or 'rgin' not in v:
            raise SimError("noise analysis produced no spectrum")
        tot = v.pop('spectrum'); v = {k: x for k, x in v.items() if '_' not in k}
        own = v.get('rl1', 0.0); src = v['rgin']
        top = sorted(((k, 100 * x / (tot - own)) for k, x in v.items() if k != 'rl1'), key=lambda t: -t[1])
        res[f0] = dict(NF=float(10 * np.log10((tot - own) / src)), top=top[:14])
    return res

def twotone(P, f1=7.0e6, f2=7.2e6, pin=-10, T=None, step=None, settle=20e-6, reltol=1e-6, steps_per_cycle=80, method="gear"):
    """Two equal tones (pin dBm available each). Settings converged per sim/results/convergence.json:
    step = 1/(80 x highest product frequency), reltol 1e-6. Coarser steps left IM2 unconverged by up to 20 dB."""
    a = np.sqrt(2 * 50 * 10 ** (pin / 10) / 1000) * 2
    df = abs(f2 - f1)
    if T is None: T = max(10 / df, 40 / min(f1, f2))
    fmax = max(2 * f2 + f1, f1 + f2)
    if step is None: step = 1 / (fmax * steps_per_cycle)
    step = T / np.ceil(T / step)          # integer number of steps in the record, so the linearized grid ends exactly at tstop
    loads = f"V1 G 0 SIN(0 {a} {f1})\nV2 G GG SIN(0 {a} {f2})\nRGIN GG IN 50\n" + portloads(P)
    an = (f"tran {step} {settle+T} {settle} {step}\nlinearize v(p1)\nwrdata tt.txt v(p1)")
    cir = netlist(P, an, loads, extra=f".options reltol={reltol} abstol=1e-14 vntol=1e-9 method={method}")
    log, data = run(cir, {"tt.txt": dict(xmin=settle, xmax=settle + T, min_rows=1000, ncols=2)})
    d = data["tt.txt"]; t = d[:, 0]; v = d[:, 1] - d[:, 1].mean()
    w = np.blackman(len(v)); S = np.fft.rfft(v * w) / np.sum(w) * 2; fr = np.fft.rfftfreq(len(v), t[1] - t[0])
    def pw(F):
        i = np.argmin(abs(fr - F)); m = max(abs(S[max(i - 2, 0):i + 3])); return 10 * np.log10(m ** 2 / 2 / 50 * 1000)
    r = dict(f1=pw(f1), f2=pw(f2), im3l=pw(2 * f1 - f2), im3h=pw(2 * f2 - f1), im2s=pw(f1 + f2))
    r['gain'] = r['f1'] - pin
    r['oip3'] = r['f1'] + (r['f1'] - max(r['im3l'], r['im3h'])) / 2; r['iip3'] = r['oip3'] - r['gain']
    r['oip2'] = 2 * r['f1'] - r['im2s']; r['iip2'] = r['oip2'] - r['gain']
    return r

def single_tone_pout(P, f=7e6, pin=0, T=25e-6, settle=5e-6):
    a = np.sqrt(2 * 50 * 10 ** (pin / 10) / 1000) * 2
    loads = f"V1 G 0 SIN(0 {a} {f})\nRGIN G IN 50\n" + portloads(P)
    step = T / np.ceil(T * f * 40)
    an = f"tran {step} {settle+T} {settle} {step}\nlinearize v(p1)\nwrdata p.txt v(p1)"
    log, data = run(netlist(P, an, loads, extra=".options reltol=1e-5 method=gear"),
                    {"p.txt": dict(xmin=settle, xmax=settle + T, min_rows=500, ncols=2)})
    d = data["p.txt"]; v = d[:, 1] - d[:, 1].mean(); w = np.blackman(len(v))
    S = np.fft.rfft(v * w) / w.sum() * 2; fr = np.fft.rfftfreq(len(v), d[1, 0] - d[0, 0])
    i = np.argmin(abs(fr - f)); return 10 * np.log10(max(abs(S[i - 2:i + 3])) ** 2 / 2 / 50 * 1000)

def p1db(P, f=7e6, pins=range(-10, 22, 1)):
    rows = []
    for pin in pins:
        po = single_tone_pout(P, f, pin); rows.append((pin, po, po - pin))
    g0 = rows[0][2]
    for (p0, o0, g0_), (p1, o1, g1) in zip(rows, rows[1:]):
        if g1 < g0 - 1:
            # interpolate input where gain = g0 - 1
            fr = (g0 - 1 - g0_) / (g1 - g0_) if g1 != g0_ else 0
            pin_c = p0 + fr * (p1 - p0); return rows, pin_c, pin_c + g0 - 1
    return rows, None, None
