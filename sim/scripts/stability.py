"""Stability analysis, Rev B (build given on the command line, default A).

1. Full 5-port S-matrix (antenna input + 4 outputs), 10 kHz - 2 GHz, with the modelled package
   and wiring parasitics (PAR=1).
2. Each 2-port obtained by terminating the other three ports in sampled passive loads
   (|G| = 0 and |G| = 1 at 12 phases each, i.e. all-reactive worst cases, plus |G| = 0.5)
   is tested with the Edwards-Sinsky mu factor. mu > 1 means that 2-port is unconditionally
   stable for ANY passive load on its own two ports, given those other-port loads.
   Pairs tested: (input, port 1) and (port 1, port 2). Ports 1-4 are identical by symmetry.
3. Time-domain kicks with all 5 ports on lumped-ladder coax (0.1-5 m; far end open, short,
   50 ohm, 100 pF, 1 uH), mixed per port. Any simulator failure is recorded as FAILED, not skipped.
Limits: the frequency-domain test assumes the 50-ohm-terminated circuit is itself stable (checked
by the 50-ohm kick case). The transistor models are not trustworthy far above ~500 MHz, and PCB
parasitics beyond the lumped estimates are not modelled.
"""
import gen, numpy as np, itertools, json, sys
build = sys.argv[1] if len(sys.argv) > 1 else "A"
P = gen.params(build)
out = {"build": build}

f, S = gen.smatrix(P, 1e4, 2e9, 30)
np.save(f"../results/smatrix_{build}.npy", np.concatenate([f[:, None, None] * np.ones((1, 5, 5)), S], 1))

def reduce(S, keep, term, G):
    a = list(keep); b = list(term)
    Saa = S[:, a][:, :, a]; Sab = S[:, a][:, :, b]; Sba = S[:, b][:, :, a]; Sbb = S[:, b][:, :, b]
    Gm = np.diag(G)
    M = np.linalg.inv(np.eye(len(b))[None] - Sbb @ Gm[None])
    return Saa + Sab @ Gm[None] @ M @ Sba

def mu(S2):
    s11, s12, s21, s22 = S2[:, 0, 0], S2[:, 0, 1], S2[:, 1, 0], S2[:, 1, 1]
    D = s11 * s22 - s12 * s21
    return (1 - abs(s11) ** 2) / (abs(s22 - D * np.conj(s11)) + abs(s12 * s21))

phases = np.exp(1j * np.linspace(0, 2 * np.pi, 12, endpoint=False))
gammas = [0.0] + list(phases) + list(0.5 * phases)
for keep in [(0, 1), (1, 2)]:
    term = [k for k in range(5) if k not in keep]
    worst = (np.inf, None, None)
    nloads = 0
    for G in itertools.product(gammas, repeat=3):
        m = mu(reduce(S, keep, term, np.array(G, complex)))
        i = int(np.argmin(m)); nloads += 1
        if m[i] < worst[0]:
            worst = (float(m[i]), float(f[i]), [complex(g) for g in G])
    name = {(0, 1): "input-port1", (1, 2): "port1-port2"}[keep]
    out[f"mu_min_{name}"] = dict(mu=round(worst[0], 3), at_Hz=worst[1],
                                 other_port_gammas=[f"{abs(g):.2f}<{np.degrees(np.angle(g)):.0f}" for g in worst[2]],
                                 combos=nloads, verdict="mu>1 (unconditionally stable for these other-port loads)" if worst[0] > 1 else "mu<=1: potentially unstable")
    print(name, out[f"mu_min_{name}"], flush=True)
# S-parameter magnitudes summary: max |Sii| at each port (>1 would be negative resistance into a 50-ohm reference)
out["max_abs_S00"] = float(abs(S[:, 0, 0]).max()); out["max_abs_S11"] = float(abs(S[:, 1, 1]).max())
out["max_abs_gain_any_path_dB"] = float(20 * np.log10(abs(S).max()))

# ---------------- time-domain kicks with mixed cable terminations
CAB = dict(L=250e-9, C=100e-12, R=0.1)   # per metre, RG-58-like, R includes skin loss at ~30 MHz
def cable(tag, node, length, far):
    n = max(4, int(round(length / 0.1)))
    n = min(n, 40)
    dl = length / n; s = []; prev = node
    for k in range(n):
        nx = f"{tag}_{k}"
        s.append(f"L{tag}{k} {prev} {nx}m {CAB['L']*dl:g}\nR{tag}{k} {nx}m {nx} {CAB['R']*dl:g}\nC{tag}{k} {nx} 0 {CAB['C']*dl:g}")
        prev = nx
    s.append({"open": f"R{tag}F {prev} 0 1e7", "short": f"R{tag}F {prev} 0 0.05", "50": f"R{tag}F {prev} 0 50",
              "C": f"C{tag}F {prev} 0 100p\nR{tag}FB {prev} 0 1e7", "L": f"L{tag}F {prev} {tag}FL 1u\nR{tag}FL {tag}FL 0 0.1"}[far])
    return "\n".join(s)

def kick(cfg, extra_net=""):
    """cfg: list of 5 (length_m or None for direct 50 ohm, far) for IN, P1..P4."""
    s = []
    for idx, (node, (ln, far)) in enumerate(zip(["IN", "P1", "P2", "P3", "P4"], cfg)):
        s.append(f"RT{idx} {node} 0 50" if ln is None else cable(f"K{idx}", node, ln, far))
    s.append("IK 0 X PULSE(0 10m 1u 1n 1n 2n 1)")
    if extra_net: s.append(extra_net)
    an = "tran 0.5n 8u 0 0.5n\nlinearize v(out)\nwrdata k.txt v(out)"
    log, d = gen.run(gen.netlist(P, an, "\n".join(s), extra=".options method=gear reltol=1e-4"),
                     {"k.txt": dict(xmin=0, xmax=8e-6, min_rows=10000, ncols=2)})
    a = d["k.txt"]; t = a[:, 0]; v = a[:, 1] - np.median(a[t > 7e-6, 1])
    pk = np.abs(v[(t > 1e-6) & (t < 1.5e-6)]).max()
    w1 = np.abs(v[(t > 3e-6) & (t < 4e-6)]).max(); w2 = np.abs(v[t > 7e-6]).max()
    return dict(peak_mV=round(pk * 1e3, 2), late_3to4us_uV=round(w1 * 1e6, 3), late_gt7us_uV=round(w2 * 1e6, 3),
                decays=bool(w2 < 0.01 * pk and (w2 <= w1 * 1.5 or w2 < 0.1e-6)))   # 0.1 uV = numerical floor of the 0.5 ns-step record

cases = {"all direct 50 ohm": [(None, "50")] * 5}
rng = np.random.default_rng(7)
for far in ["open", "short", "C", "L"]:
    for ln in [0.1, 0.5, 2.0, 5.0]:
        cases[f"all ports {ln} m coax, far end {far}"] = [(ln, far)] * 5
for i in range(16):
    cfg = [(float(rng.choice([0.1, 0.3, 1.0, 2.0, 5.0])), str(rng.choice(["open", "short", "50", "C", "L"]))) for _ in range(5)]
    cases["mixed %02d: " % i + ", ".join(f"{l}m/{fa}" for l, fa in cfg)] = cfg
kres = {}; nfail = 0; nbad = 0
for name, cfg in cases.items():
    try:
        r = kick(cfg)
        if not r["decays"]: nbad += 1
    except gen.SimError as e:
        r = dict(status="FAILED", error=str(e)[:300]); nfail += 1
    kres[name] = r; print(name, r, flush=True)
# negative control: a series RLC with negative resistance on OUT must be flagged (proves the test can fail)
try:
    nc = kick([(None, "50")] * 5, "LNEG OUT NT1 1u\nCNEG NT1 NT2 100p\nRNEG NT2 0 -5")
    nc_ok = not nc["decays"]
except gen.SimError as e:
    nc = dict(status="sim failed (counts as detected)", error=str(e)[:200]); nc_ok = True
out["negative_control"] = dict(result=nc, detected=nc_ok)
print("negative control", out["negative_control"], flush=True)
out["kicks"] = kres
out["kick_summary"] = dict(cases=len(cases), sim_failures=nfail, non_decaying=nbad)
json.dump(out, open(f"../results/stability_{build}.json", "w"), indent=1)
print(out["kick_summary"])
