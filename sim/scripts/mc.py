"""Monte Carlo and corner analysis, Rev B build A. Usage: python3 mc.py [N_full] [N_unbinned]
Every part varies independently with its published tolerance (tolerance.TOL_SOURCES).
Failed simulations are counted and listed; they are never silently dropped."""
import gen, tolerance as T, numpy as np, json, sys, multiprocessing as mp
NF = int(sys.argv[1]) if len(sys.argv) > 1 else 200
NU = int(sys.argv[2]) if len(sys.argv) > 2 else 200

def rf_metrics(P):
    d = gen.op(P)
    r = gen.ac(P, 1e4, 120e6, 25); f = r['f']; b = gen.band_mask(f)   # includes exactly 10 kHz and 50 MHz
    g = lambda a, F: float(gen.at(f, a, F))                            # exact simulated frequency only
    return dict(T=P['TEMP'], VCC=round(P['VCC'], 3), Itot_mA=-d['i(vcc)'] * 1e3, Iq1n_mA=d['@q1n[ic]'] * 1e3, Iq1p_mA=-d['@q1p[ic]'] * 1e3,
                Iout_mA=d['@q2[ic]'] * 1e3, Vout=d['v(out)'], G1=g(r['S21'], 1e6), G10=g(r['S21'], 10e6), G30=g(r['S21'], 30e6),
                G50=g(r['S21'], 50e6), flat=float(r['S21'][b].max() - r['S21'][b].min()), S11max=float(r['S11'][b].max()),
                S22max=float(r['S22'][b].max()), iso30=g(r['iso'], 30e6), rev30=g(r['rev'], 30e6), rej88=-g(r['S21'], 88e6))

def full_metrics(P):
    m = rf_metrics(P)
    m['NF10'] = gen.nf_breakdown(P, (10e6,))[10e6]['NF']
    m['IIP3_7'] = gen.twotone(P, 7e6, 7.2e6, -10)['iip3']
    m['IIP2_67'] = gen.twotone(P, 6e6, 7e6, -10)['iip2']
    return m

def job(args):
    kind, i, seed, opts = args
    rng = np.random.default_rng([seed, i])
    P = T.sample(rng, "A", **opts)
    try:
        return dict(run=i, status="ok", **(full_metrics(P) if kind == "full" else rf_metrics(P)))
    except gen.SimError as e:
        return dict(run=i, status="FAILED", error=str(e)[:300])

LOWER_BAD = {"G1", "G10", "G30", "G50", "rej88", "IIP3_7", "IIP2_67"}   # smaller is worse
def stats(rows):
    ok = [r for r in rows if r['status'] == 'ok']
    keys = [k for k in ok[0] if k not in ('run', 'status')]
    s = {}
    for k in keys:
        v = np.array([r[k] for r in ok], float)
        s[k] = dict(min=round(float(v.min()), 3), p5=round(float(np.percentile(v, 5)), 3), median=round(float(np.median(v)), 3),
                    p95=round(float(np.percentile(v, 95)), 3), max=round(float(v.max()), 3))
    return dict(n=len(rows), ok=len(ok), failed=[r for r in rows if r['status'] != 'ok'], stats=s)

def corners():
    out = {}
    base = gen.params("A")
    cases = {"nominal": {}, "T=0C": dict(TEMP=0), "T=50C": dict(TEMP=50),
             "rail -4.5%": dict(VCC=base['VCC'] * 0.955), "rail +4.5%": dict(VCC=base['VCC'] * 1.045),
             "all hFE=100": T.corner_models(bf=100 / 300) | {}, "TF x0.7": T.corner_models(tf=0.7), "TF x1.4": T.corner_models(tf=1.4),
             "CJC x0.7": T.corner_models(cjc=0.7), "CJC x1.4": T.corner_models(cjc=1.4)}
    # hFE=100 corner: scale each device's BF to 100 (PNP model BF=200, NPN 300)
    lines = []; over = {}
    for key, b in T.DEVICES:
        nm = f"H_{key}"; lines.append(T.model_line(b, nm, {"BF": 100 / T.MODEL_BF[b]})); over[key] = nm
    over['MODELS'] = "\n".join(lines); cases["all hFE=100"] = over
    lines = []; over = {}
    for key, b in T.DEVICES:
        nm = f"K_{key}"; lines.append(T.model_line(b, nm, {"BF": 300 / T.MODEL_BF[b]})); over[key] = nm
    over['MODELS'] = "\n".join(lines); cases["all hFE=300"] = over
    for name, ov in cases.items():
        try: out[name] = dict(status="ok", **full_metrics(gen.params("A", **ov)))
        except gen.SimError as e: out[name] = dict(status="FAILED", error=str(e)[:300])
        print("corner", name, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in out[name].items()}, flush=True)
    return out

if __name__ == "__main__":
    res = dict(sources={k: v[1] for k, v in T.TOL_SOURCES.items()}, model_provenance=T.MODEL_PROVENANCE)
    res["corners"] = corners()
    with mp.Pool(max(1, mp.cpu_count())) as pool:
        rows = pool.map(job, [("full", i, 2026, dict(L="L_selected", C="C_C0G_G")) for i in range(NF)])
        res["mc_recommended_binnedL_2pctC"] = stats(rows); res["mc_recommended_rows"] = rows
        print("recommended", json.dumps(res["mc_recommended_binnedL_2pctC"]["stats"]), "failed", len(res["mc_recommended_binnedL_2pctC"]["failed"]), flush=True)
        rows = pool.map(job, [("rf", i, 4242, dict(L="L_78FR_K", C="C_C0G_G")) for i in range(NU)])
        res["mc_unbinnedL_2pctC"] = stats(rows)
        print("unbinned", json.dumps(res["mc_unbinnedL_2pctC"]["stats"]), "failed", len(res["mc_unbinnedL_2pctC"]["failed"]), flush=True)
    json.dump(res, open("../results/mc_A.json", "w"), indent=1)
