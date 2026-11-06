"""Regression tests: the harness must never report success from a failed or stale simulation.
Run:  python3 test_harness.py      (exit status 0 = all tests passed)"""
import gen, numpy as np, os, sys, tempfile, glob

failures = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not cond: failures.append(name)

def expect_error(name, fn):
    try:
        fn()
    except gen.SimError as e:
        check(name, True, str(e)[:90]); return
    except Exception as e:
        check(name, False, f"wrong exception {type(e).__name__}: {e}"); return
    check(name, False, "no error raised")

P = gen.params("A")

# 1. A known-good run succeeds and is fresh.
f, V = gen._ac_files(P, 0, 1e4, 1e8, 10)
check("good AC run returns data", len(f) >= 40 and np.isfinite(V).all(), f"{len(f)} points")

# 2. Missing transistor model must fail (previously returned stale data).
expect_error("missing model -> SimError", lambda: gen._ac_files(gen.params("A", QN="NO_SUCH_MODEL"), 0, 1e4, 1e8, 10))

# 3. The same failing call right after a good run must not reuse the good run's output file.
before = set(glob.glob(os.path.join(tempfile.gettempdir(), "mcsim_*")))
expect_error("failing run after good run is not masked by stale file",
             lambda: gen._ac_files(gen.params("A", QN="NO_SUCH_MODEL"), 0, 1e4, 1e8, 10))
after = set(glob.glob(os.path.join(tempfile.gettempdir(), "mcsim_*")))
check("no run directories left behind", after <= before, f"{len(after - before)} new dirs")

# 4. Singular circuit (operating point fails) must fail.
expect_error("singular operating point -> SimError",
             lambda: gen.run(gen.netlist(P, "op\nprint v(out)", "VBAD1 OUT 0 1\nVBAD2 OUT 0 2\nRGIN IN 0 50\n" + gen.portloads(P))))

# 5. Partial transient (known abort: lossless lines, ideal open ends) must fail even though ngspice
#    continues the .control block and prints the completion marker.
kick = "\n".join([f"TL{k} P{k} 0 FAR{k} 0 Z0=50 TD=0.5n\nRF{k} FAR{k} 0 1e9" for k in range(1, 5)])
kick += "\nTLIN IN 0 FARIN 0 Z0=50 TD=0.5n\nRFIN FARIN 0 1e9\nIK 0 X PULSE(0 10m 1u 1n 1n 2n 1)"
expect_error("aborted transient -> SimError",
             lambda: gen.run(gen.netlist(P, "tran 0.2n 6u 0 0.2n\nwrdata k.txt v(out)", kick, extra=".options method=gear reltol=1e-4"),
                             {"k.txt": dict(xmin=0, xmax=6e-6, min_rows=100, ncols=2)}))

# 6. Requesting a vector that does not exist must fail.
expect_error("missing vector -> SimError",
             lambda: gen.run(gen.netlist(P, "op\nprint v(nonexistent_node)", "RGIN IN 0 50\n" + gen.portloads(P))))

# 7. Validator rejects truncated, empty, non-finite and wrong-shape tables.
t = np.c_[np.linspace(0, 5e-6, 200), np.zeros(200)]
expect_error("truncated transient table rejected", lambda: gen.validate_table(t, xmin=0, xmax=6e-6))
expect_error("empty table rejected", lambda: gen.validate_table(np.zeros((0, 2)), xmin=0, xmax=1))
bad = t.copy(); bad[5, 1] = np.nan
expect_error("NaN rejected", lambda: gen.validate_table(bad, xmin=0, xmax=5e-6))
expect_error("wrong column count rejected", lambda: gen.validate_table(t, ncols=3))
check("valid table accepted", gen.validate_table(t, xmin=0, xmax=5e-6, ncols=2) is not None)

# 8. Missing output file (analysis never wrote it) must fail.
expect_error("missing output file -> SimError",
             lambda: gen.run(gen.netlist(P, "op", "RGIN IN 0 50\n" + gen.portloads(P)), {"never_written.txt": {}}))

# 9. Unknown build name must fail loudly.
try:
    gen.params("Z"); check("unknown build rejected", False)
except KeyError:
    check("unknown build rejected", True)

# 10. Builds are explicit and distinct.
check("build B has RF=270", gen.params("B")["RF"] == 270 and gen.params("A")["RF"] == 220)

# 11. Frequency sampling: 50 MHz is not on the 25-point/decade grid from 10 kHz.
fd, Vd = gen._ac_files(P, 0, 1e4, 120e6, 25, exact=())
dense_only = gen.run(gen.netlist(P, "ac dec 25 1e4 120e6\nwrdata d.txt v(p1)", gen.src50(P) + "\n" + gen.portloads(P)),
                     {"d.txt": dict(xmin=1e4, xmax=120e6, min_rows=90, ncols=3)})[1]["d.txt"]
check("50 MHz is NOT on the raw dense grid (test premise)", not gen.has_freq(dense_only[:, 0], 50e6),
      f"nearest {dense_only[np.argmin(abs(dense_only[:, 0] - 50e6)), 0]:.6g} Hz")
check("band edges are always added exactly", gen.has_freq(fd, 1e4) and gen.has_freq(fd, 50e6))
r = gen.ac(P, 1e4, 120e6, 25)
single = gen.run(gen.netlist(P, "ac lin 1 50e6 50e6\nwrdata s.txt v(p1)", gen.src50(P) + "\n" + gen.portloads(P)),
                 {"s.txt": dict(min_rows=1, ncols=3)})[1]["s.txt"]
g_single = 20 * np.log10(abs(single[0, 1] + 1j * single[0, 2]))
g_named = gen.at(r['f'], r['S21'], 50e6)
check("named 50 MHz value equals an independent single-point 50 MHz solve", abs(g_named - g_single) < 1e-6,
      f"{g_named:.6f} vs {g_single:.6f} dB")
io = np.argmin(abs(dense_only[:, 0] - 50e6)); nearest_old = 20 * np.log10(abs(dense_only[io, 1] + 1j * dense_only[io, 2]))
check("old nearest-grid-point method would have differed (shows the bug)", abs(nearest_old - g_single) > 0.01,
      f"nearest point {dense_only[io, 0]/1e6:.2f} MHz: {nearest_old:.3f} dB vs exact {g_single:.3f} dB")
lo, hi = gen.band_extrema(r['f'], r['S21'])
check("upper band edge contributes to passband minimum (S21 droops to 50 MHz)", abs(lo - g_single) < 1e-6, f"min {lo:.4f} dB")
check("lower band edge contributes to passband extrema", abs(gen.at(r['f'], r['S21'], 1e4) - hi) < 0.02,
      f"max {hi:.4f}, at 10 kHz {gen.at(r['f'], r['S21'], 1e4):.4f}")
expect_error("named value at a non-simulated frequency -> SimError", lambda: gen.at(r['f'], r['S21'], 49e6))
expect_error("passband extrema on a grid missing 50 MHz -> SimError",
             lambda: gen.band_extrema(dense_only[:, 0], dense_only[:, 1]))
f_sparse = np.array([1e4, 1e5, 1e6, 1e7, 5e7])
expect_error("passband extrema on a too-sparse grid (edges present) -> SimError",
             lambda: gen.band_extrema(f_sparse, np.zeros(5)))
expect_error("exact list that would push below the band is still checked",
             lambda: gen.band_extrema(np.array([2e4, 5e7]), np.zeros(2)))
# two-tone products land on exact FFT bins, including the non-commensurate-looking 0.6/1.0 MHz case
t = gen.twotone(P, 0.6e6, 1.0e6, -10)
check("0.6/1.0 MHz two-tone products on exact FFT bins", np.isfinite(t['iip2']), f"IIP2 {t['iip2']:.2f} dBm")

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
