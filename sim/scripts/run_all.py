"""Nominal verification of builds A, B, C (all defined in gen.BUILDS). Writes ../results/summary.json.
Each two-tone result is computed at 80 and 160 steps per cycle of the highest product; the
difference is reported so convergence is visible for every number, not assumed."""
import gen, numpy as np, json, sys
builds = sys.argv[1:] or list(gen.BUILDS)
summary = {}
def r2(x): return round(float(x), 2)
for b in builds:
    P = gen.params(b); s = dict(build=b, parts={k: P[k] for k in gen.BUILDS[b]}, status={})
    def step(name, fn):
        try: fn(); s['status'][name] = "ok"
        except gen.SimError as e: s['status'][name] = "FAILED: " + str(e)[:300]
        print(b, name, s['status'][name], flush=True)
    def do_op():
        d = gen.op(P); s['op'] = {k: r2(v * (1e3 if '[ic]' in k else 1)) for k, v in d.items() if k != 'i(vcc)'}
        dd = gen.op(gen.params(b, SUPPLY='full')); s['op_full_supply'] = dict(rail_V=r2(dd['v(vcc)']), input_mA=r2(dd['Irail_mA']))
    def do_ac():
        r = gen.ac(P, 1e3, 200e6, 40); f = r['f']; band = (f >= 1e4) & (f <= 50.1e6)
        at = lambda a, F: r2(a[np.argmin(abs(f - F))])
        s['gain_dB'] = {f"{F/1e6:g}MHz": at(r['S21'], F) for F in (1e4, 1e5, 1e6, 10e6, 30e6, 50e6)}
        s['gain_range_10k_50M_dB'] = [r2(r['S21'][band].min()), r2(r['S21'][band].max())]
        s['S11_max_10k_50M_dB'] = r2(r['S11'][band].max()); s['S22_max_10k_50M_dB'] = r2(r['S22'][band].max())
        s['port_isolation_dB'] = {f"{F/1e6:g}MHz": at(r['iso'], F) for F in (1e6, 10e6, 30e6, 50e6)}
        s['reverse_isolation_dB'] = {f"{F/1e6:g}MHz": at(r['rev'], F) for F in (1e6, 10e6, 30e6, 50e6)}
        s['rejection_dB'] = {f"{F/1e6:g}MHz": -at(r['S21'], F) for F in (88e6, 100e6, 108e6, 150e6)}
        np.savetxt(f"../results/ac_{b}.csv", np.column_stack([f, r['S21'], r['S11'], r['S22'], r['iso'], r['rev']]), delimiter=",",
                   header="f_Hz,S21_dB,S11_dB,S22_dB,port2_to_port3_dB,port2_to_input_dB", comments="")
    def do_nf():
        n = gen.nf_breakdown(P); s['NF_dB'] = {f"{F/1e6:g}MHz": r2(x['NF']) for F, x in n.items()}
        s['NF_contributors_10MHz_pct'] = [(k, round(p, 1)) for k, p in n[10e6]['top'][:8]]
    def do_im():
        s['IM'] = {}
        for lab, f1, f2, kind in [("IP3 1.0/1.2 MHz", 1e6, 1.2e6, 3), ("IP3 7.0/7.2 MHz", 7e6, 7.2e6, 3), ("IP3 14.0/14.2 MHz", 14e6, 14.2e6, 3),
                                  ("IP3 28.0/28.2 MHz", 28e6, 28.2e6, 3), ("IP2 6+7 MHz", 6e6, 7e6, 2), ("IP2 0.6+1.0 MHz", 0.6e6, 1.0e6, 2)]:
            for pin in (-10, 0):
                a = gen.twotone(P, f1, f2, pin, steps_per_cycle=80); c = gen.twotone(P, f1, f2, pin, steps_per_cycle=160)
                key = 'iip3' if kind == 3 else 'iip2'
                s['IM'][f"{lab} @{pin} dBm/tone"] = dict(IIP=r2(c[key]), OIP=r2(c['o' + key[1:]]), IIP_80steps=r2(a[key]),
                                                       conv_delta_dB=r2(abs(a[key] - c[key])))
    def do_p1():
        rows, pin, po = gen.p1db(P, 7e6); s['P1dB_7MHz'] = dict(input_dBm=r2(pin) if pin else None, output_dBm=r2(po) if po else None)
    for name, fn in [("op", do_op), ("ac", do_ac), ("noise", do_nf), ("two-tone", do_im), ("p1db", do_p1)]: step(name, fn)
    summary[b] = s
json.dump(summary, open("../results/summary.json", "w"), indent=1)
