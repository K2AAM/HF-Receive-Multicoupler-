"""Does C4/C7 (43 pF) need +/-2 %, or is +/-5 % acceptable? Selected L (+/-3 %), C5/C6 +/-2 %,
C4/C7 at +/-2 % vs +/-5 %. Same seed for both, so the only difference is the end-cap tolerance."""
import gen, tolerance as T, numpy as np, json
from lpf_study import metrics
out = {}
for tol in (0.02, 0.05):
    rng = np.random.default_rng(2026); rows = []; fails = 0
    for i in range(100):
        P = T.sample(rng, "A", L="L_selected", C="C_C0G_G", devices=False)
        u = np.random.default_rng([7, i]).uniform(-1, 1, 2)
        P['CF1'] = gen.NOMINAL['CF1'] * (1 + tol * u[0]); P['CF4'] = gen.NOMINAL['CF4'] * (1 + tol * u[1])
        try: rows.append(metrics(P))
        except gen.SimError: fails += 1
    a = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    out[f"C4/C7 +/-{tol*100:g}%"] = dict(n=len(rows), failed=fails, S11_worst=round(float(a['S11max'].max()), 2),
        flat_worst=round(float(a['flat'].max()), 3), G50_min=round(float(a['G50'].min()), 3), rej88_min=round(float(a['rej88'].min()), 2))
    print(out)
json.dump(out, open('../results/lpf_endcap_tolerance.json', 'w'), indent=1)
