"""Two-tone convergence study for the recommended build. Writes ../results/convergence.json.
Checks time step (steps per cycle of the highest product), reltol and integration method.
Gear is the default because trapezoidal integration was found to slow down by 20-200x on some
Monte Carlo samples (step-size rejection), while giving the same intercepts where it finished."""
import gen, json, time
P = gen.params(gen.RECOMMENDED)
rows = []
cases = [("IM3 7.0/7.2 MHz", 7.0e6, 7.2e6), ("IM2 6/7 MHz", 6.0e6, 7.0e6), ("IM2 0.6/1.0 MHz", 0.6e6, 1.0e6)]
for name, f1, f2 in cases:
    for pin in (-10, 0):
        for meth, spc, rel in (("gear", 20, 1e-5), ("gear", 40, 1e-6), ("gear", 80, 1e-6), ("gear", 160, 1e-6), ("trap", 80, 1e-6), ("trap", 160, 1e-6)):
            t = time.time()
            try:
                r = gen.twotone(P, f1, f2, pin, steps_per_cycle=spc, reltol=rel, method=meth)
                rows.append(dict(case=name, pin=pin, method=meth, steps_per_cycle=spc, reltol=rel, iip3=round(r['iip3'], 2), iip2=round(r['iip2'], 2),
                                 seconds=round(time.time() - t, 1), status="ok"))
            except gen.SimError as e:
                rows.append(dict(case=name, pin=pin, method=meth, steps_per_cycle=spc, reltol=rel, status="FAILED: " + str(e)[:120]))
            print(rows[-1], flush=True)
json.dump(rows, open('../results/convergence.json', 'w'), indent=1)
