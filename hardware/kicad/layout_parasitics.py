"""Layout-parasitic re-check (SIMULATED, estimate): extract each signal net's routed copper from hfmc.kicad_pcb,
convert it to a shunt capacitance to ground, add it to the build-A simulation (on top of the existing PAR=1
package/wiring parasitics) and compare AC metrics and the mu stability factor against the unmodified model.
Capacitance model (estimate, not a field solve): 0.10 pF/mm of 0.4 mm track (grounded coplanar on 1.6 mm FR-4,
~0.08 pF/mm calculated, rounded up) + 0.30 pF per through-hole pad. Run with KiCad's python (/usr/bin/python3)."""
import os, sys, json, itertools, collections
import numpy as np, pcbnew
REPO = os.environ.get("REPO", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.join(REPO, "sim", "scripts"))
os.chdir(os.path.join(REPO, "sim", "scripts"))
import gen
HERE = os.path.dirname(os.path.abspath(__file__))
C_PER_MM, C_PAD = 0.10e-12, 0.30e-12
SKIP = {"GND", "VCC", "UIN", "UOUT", "UADJ", "L4B", "J6A", "J6B"}
b = pcbnew.LoadBoard(os.path.join(HERE, "hfmc.kicad_pcb"))
length = collections.defaultdict(float); pads = collections.Counter()
for t in b.GetTracks():
    if t.GetClass() != "PCB_VIA": length[t.GetNetname()] += pcbnew.ToMM(t.GetLength())
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNumber(): pads[p.GetNetname()] += 1
caps = {n: length[n] * C_PER_MM + pads[n] * C_PAD for n in set(length) | set(pads) if n not in SKIP and n}
extra = "\n".join(f"CLAY_{n} {n} 0 {c:.4g}" for n, c in sorted(caps.items()))

def metrics(P):
    r = gen.ac(P, 1e3, 200e6, 40); f = r["f"]
    at = lambda a, F: round(float(gen.at(f, a, F)), 2)
    return dict(gain_1MHz=at(r["S21"], 1e6), gain_50MHz=at(r["S21"], 50e6),
                flatness_10k_50M=round(float(np.ptp(r["S21"][gen.band_mask(f)])), 2),
                S11_max=round(float(gen.band_extrema(f, r["S11"])[1]), 2), S22_max=round(float(gen.band_extrema(f, r["S22"])[1]), 2),
                iso_50MHz=at(r["iso"], 50e6), rej_88MHz=round(-float(gen.at(f, r["S21"], 88e6)), 2))
def mu_min(P):
    f, S = gen.smatrix(P, 1e4, 2e9, 30)
    def reduce(S, keep, term, G):
        a, bb = list(keep), list(term)
        Saa = S[:, a][:, :, a]; Sab = S[:, a][:, :, bb]; Sba = S[:, bb][:, :, a]; Sbb = S[:, bb][:, :, bb]
        return Saa + Sab @ np.diag(G)[None] @ np.linalg.inv(np.eye(len(bb))[None] - Sbb @ np.diag(G)[None]) @ Sba
    def mu(S2):
        s11, s12, s21, s22 = S2[:, 0, 0], S2[:, 0, 1], S2[:, 1, 0], S2[:, 1, 1]; D = s11 * s22 - s12 * s21
        return (1 - abs(s11) ** 2) / (abs(s22 - D * np.conj(s11)) + abs(s12 * s21))
    ph = np.exp(1j * np.linspace(0, 2 * np.pi, 12, endpoint=False)); gam = [0.0] + list(ph) + list(0.5 * ph)
    res = {}
    for keep in [(0, 1), (1, 2)]:
        term = [k for k in range(5) if k not in keep]; w = (np.inf, 0)
        for G in itertools.product(gam, repeat=3):
            m = mu(reduce(S, keep, term, np.array(G, complex))); i = int(np.argmin(m))
            if m[i] < w[0]: w = (float(m[i]), float(f[i]))
        res[{(0, 1): "input-port1", (1, 2): "port1-port2"}[keep]] = dict(mu_min=round(w[0], 3), at_MHz=round(w[1] / 1e6, 1))
    return res
base = gen.params("A"); lay = gen.params("A"); lay["MODELS"] = (lay.get("MODELS", "") + "\n" + extra).strip()
out = dict(note="SIMULATED with an ESTIMATED layout capacitance; not a measurement and not a field solve",
           C_model=dict(pF_per_mm=C_PER_MM * 1e12, pF_per_pad=C_PAD * 1e12),
           added_pF={n: round(c * 1e12, 2) for n, c in sorted(caps.items(), key=lambda x: -x[1])},
           track_mm={n: round(length[n], 1) for n in sorted(caps, key=lambda n: -length[n])},
           baseline_PAR1=metrics(base), with_layout_C=metrics(lay))
print(json.dumps({k: out[k] for k in ("baseline_PAR1", "with_layout_C")}, indent=1), flush=True)
out["mu_baseline"] = mu_min(base); out["mu_with_layout_C"] = mu_min(lay)
print(out["mu_baseline"], out["mu_with_layout_C"])
json.dump(out, open(os.path.join(HERE, "layout_parasitics.json"), "w"), indent=1)
