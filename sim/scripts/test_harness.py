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

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
