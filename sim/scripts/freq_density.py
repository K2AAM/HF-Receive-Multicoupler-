"""Check that passband extrema (10 kHz-50 MHz, both edges included exactly) do not change materially
with sweep density. Cases: nominal A, and 4 sampled units with unselected (+/-10 %) inductors, whose
filter ripple is sharpest. Writes ../results/freq_density.json."""
import gen, tolerance as T, numpy as np, json
cases = {"A nominal": gen.params("A")}
for i in range(4):
    cases[f"A sample {i} (L +/-10 %)"] = T.sample(np.random.default_rng([99, i]), "A", L="L_78FR_K", C="C_C0G_G", devices=False)
out = {}
for name, P in cases.items():
    rows = {}
    for ppd in (25, 50, 100, 200, 400):
        r = gen.ac(P, 1e4, 120e6, ppd); f = r['f']; m = gen.band_mask(f)
        rows[ppd] = dict(S21_min=float(r['S21'][m].min()), S21_max=float(r['S21'][m].max()), flat=float(np.ptp(r['S21'][m])),
                         S11_max=float(r['S11'][m].max()), S22_max=float(r['S22'][m].max()), G50=float(gen.at(f, r['S21'], 50e6)))
    ref = rows[400]
    dev = {ppd: {k: round(v - ref[k], 4) for k, v in x.items()} for ppd, x in rows.items()}
    out[name] = dict(values_ppd400={k: round(v, 4) for k, v in ref.items()}, deviation_from_ppd400=dev)
    print(name, json.dumps(dev), flush=True)
json.dump(out, open("../results/freq_density.json", "w"), indent=1)
