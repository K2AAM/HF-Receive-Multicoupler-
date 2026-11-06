"""Full-circuit AC Monte Carlo of the input filter options (independent part tolerances)."""
import gen, tolerance as T, numpy as np, json, sys
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
def metrics(P):
    r = gen.ac(P, 1e4, 120e6, 25); f = r['f']; b = gen.band_mask(f)   # includes exactly 10 kHz and 50 MHz
    g = lambda F: float(gen.at(f, r['S21'], F))                        # exact simulated frequency only
    return dict(S11max=float(r['S11'][b].max()), flat=float(r['S21'][b].max() - r['S21'][b].min()),
                G1=g(1e6), G50=g(50e6), rej88=-g(88e6))
out = {}
options = {"78FR +/-10% L, C0G +/-5% C": dict(L="L_78FR_K", C="C_C0G_J"),
           "78FR +/-10% L, C0G +/-2% C": dict(L="L_78FR_K", C="C_C0G_G"),
           "L binned +/-3%, C0G +/-2% C": dict(L="L_selected", C="C_C0G_G")}
if __name__ == "__main__":
  for name, o in options.items():
      rng = np.random.default_rng(2026)   # same seed for every option
      rows, fails = [], 0
      for i in range(N):
          try: rows.append(metrics(T.sample(rng, "A", devices=False, **o)))
          except gen.SimError as e: fails += 1
      a = {k: np.array([x[k] for x in rows]) for k in rows[0]}
      out[name] = dict(n=len(rows), failed=fails, **{k: dict(worst=float(v.max() if k in ('S11max','flat') else v.min()),
                       p95=float(np.percentile(v, 95 if k in ('S11max','flat') else 5)), median=float(np.median(v))) for k, v in a.items()})
      print(name, json.dumps(out[name]), flush=True)
  json.dump(out, open('../results/lpf_tolerance_study.json', 'w'), indent=1)
