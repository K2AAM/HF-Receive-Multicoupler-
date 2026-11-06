# Review 2 response (Rev B, second verification pass)

Date: 2026-11-05, frequency-sampling correction applied the same day (section 0). Simulator: ngspice 42. All results below are **simulation** unless marked otherwise. Nothing has been built or measured yet. Labels:

- **[sim]**: an ngspice run in this repo, regenerated from a clean run with the scripts named
- **[datasheet]**: a published manufacturer limit, not simulated
- **[unverified]**: not executed or not executable here; needs hardware
- **[hw]**: needs a bench measurement

The design stays **four ports, through-hole**. Nothing in the corrected verification required changing the signal-path topology. Three supply parts changed (F1, L4, new D6/D7/C23/RDAMP), and the LPF parts now carry tighter, stated tolerances plus an inductor-selection step.

---

## 0. Frequency-sampling correction (applied after the first issue of this document)

**The problem:** earlier AC metrics were read from a logarithmic sweep that did not contain the exact band edge or the named test frequencies.

- At 25 points per decade, the sweep points nearest 50 MHz are 47.35 MHz and 51.96 MHz.
- "Gain at 50 MHz" was therefore really gain at 51.96 MHz.
- The passband mask (≤ 50.01 MHz) stopped at 47.35 MHz, so extrema and flatness omitted the top 2.65 MHz, where the droop is steepest.
- The 88 MHz rejection was also read at the nearest grid point.

**The fix (`gen.ac_sweep`, `gen.at`, `gen.band_mask`, `gen.band_extrema`):**

- **Exact frequencies:** every AC analysis now runs a dense log sweep plus an exact single-frequency solve (`ac lin 1 F F`) at the sweep ends, at both band edges (10 kHz and 50 MHz) and at every reported frequency. The reported list is 10 k, 100 k, 1, 7, 10, 14, 28, 30, 50, 88, 100, 108 and 150 MHz. Each exact result is checked to have been solved at the requested frequency to 1e-7 relative.
- **Named values:** these are read only at exactly simulated frequencies. `gen.at()` raises an error if the frequency was not solved; it has no nearest-point fallback.
- **No interpolation:** none is used for any reported AC value. The supply analyses also solve their named frequencies exactly. One supply impedance value (30 MHz) had been interpolated and was wrong in the 4th decimal.
- **Passband extrema:** these use an inclusive mask that **raises an error** if 10 kHz or 50 MHz is missing, or if any step inside the band exceeds 1/20 decade.
- **Two-tone records:** these are now a whole number of periods of both tones. The FFT bin is the GCD of the tone frequencies, and every tone and product must fall exactly on a bin, or the run fails. Previously the 0.6/1.0 MHz record was 66.7 µs, which put 1.0 MHz a third of a bin off. That changed MW IIP2 by up to 0.5 dB.

**Density check** (`freq_density.py` → `results/freq_density.json`) [sim]:

- Method: passband S21 minimum and maximum, flatness, S11 and S22 maxima, and gain at 50 MHz, at 25, 50, 100, 200 and 400 points per decade, both edges included.
- Units checked: nominal build A and four units with unselected (±10 %) inductors, whose ripple is sharpest.
- Result: the largest change from the 400-point reference is 0.024 dB (S11 maximum at 25 points per decade). Every S21 extremum is unchanged to 0.001 dB. Monte Carlo and LPF runs use 25 points per decade; the nominal runs use 40.

**Regression tests added to `test_harness.py`** (all pass):

- 50 MHz is not on the raw 25-point grid (the test premise).
- Both band edges are present after merging.
- The named 50 MHz gain equals an independent single-point 50 MHz solve to 1e-6 dB.
- The old nearest-point method would have read 51.96 MHz (0.705 dB instead of 0.843 dB).
- The 50 MHz edge sets the passband minimum, and 10 kHz sits at the maximum.
- Asking for a non-simulated frequency raises an error.
- Extrema on a grid missing 50 MHz raise an error.
- Extrema on a too-sparse grid raise an error, even with both edges present.
- Extrema on a grid missing 10 kHz raise an error.
- The 0.6/1.0 MHz two-tone products land on exact FFT bins.

**What changed in the results** (build A, nominal):

| Quantity | Before | Corrected | Why |
| --- | --- | --- | --- |
| Gain range 10 kHz–50 MHz | 0.96–1.72 dB | 0.84–1.72 dB | 47–50 MHz now included |
| Flatness 10 kHz–50 MHz | 0.76–0.77 dB | **0.88 dB** | as above |
| Worst S22 | −23.7 dB | −23.3 dB | as above |
| Rejection 88 / 108 MHz | 35.9 / 49.4 dB | **34.8** / 50.7 dB | read at exactly 88 and 108 MHz instead of the nearest grid point |
| MC gain @50 MHz (min–max) | 0.55–0.97 dB | 0.69–1.04 dB | read at 50.0 MHz, not 51.96 MHz |
| MC flatness (max) | 0.79 dB | **0.91 dB** | |
| MC rejection @88 MHz (min) | 35.9 dB | **33.4 dB** | |
| LPF study, selected L: worst S11 / flatness | −20.0 / 0.80 dB | **−19.8 / 0.93 dB** | |
| IIP2 0.6+1.0 MHz (−10 / 0 dBm) | +82.5 / +79.3 dBm | +82.1 / +78.8 dBm | exact FFT bins |

**Do selected inductors still meet the targets?** Not the ones previously stated. Selection still does what it was chosen for: it keeps S11 near −20 dB instead of −11 dB. But the old "S11 ≤ −20 dB, flatness ≤ 0.8 dB, ≥ 36 dB at 88 MHz" claims are withdrawn. The supported specs with selected inductors are:

- **S11:** ≤ −19.4 dB (worst of 200 MC units)
- **Flatness, 10 kHz–50 MHz:** ≤ 0.93 dB
- **Rejection at 88 MHz:** ≥ 33.4 dB

Most of the 50 MHz droop comes from the amplifier, not the filter: the nominal unit already has 0.88 dB, and only 0.3 dB of droop occurs below 30 MHz. These numbers are still adequate for an HF receive splitter. If a hard ≤ 0.8 dB to 50 MHz or ≥ 36 dB at 88 MHz is required, it needs a design change (for example retuning the LPF cutoff upward, or a small 50 MHz peaking network). That change has not been simulated.

---

## 1. Simulation failure handling (`sim/scripts/gen.py`, `test_harness.py`)

What `gen.run()` now does for every simulation:

- **Fresh directory:** each run gets its own `tempfile.mkdtemp()` directory, which is removed afterwards. Set `MC_KEEP_FAILED=1` to keep failed runs for inspection.
- **Process checks:** a non-zero exit status fails the run, and so does a timeout (default 900 s, or `MC_SIM_TIMEOUT`).
- **Log scan:** any line matching a simulator error pattern fails the run. Patterns include `error`, `timestep too small`, `aborted`, `singular matrix`, `no such vector`, `checkvalid … is not available`, `unknown model/parameter/subckt`, `could not find`, `iteration limit`, `source stepping failed` and `not converge`.
- **Completion marker:** every deck ends with `echo @@SIM_COMPLETE@@`, and a run is rejected if the marker never appears.
- **Output files:** every expected file must exist, be non-empty, carry an mtime from this run and parse as finite numbers. It must also have the right column count, enough rows, and an x-axis covering the full requested sweep or time span. A partial transient fails here even when ngspice printed the marker.
- **Printed values:** the `.op` analyses require every requested value to be present.
- **No fallback:** nothing falls back to older data, and every caller records failures explicitly. The Monte Carlo and stability scripts count and list them instead of dropping them.

`python3 sim/scripts/test_harness.py` runs 26 regression checks (15 for failure handling, 11 for frequency sampling; see section 0). **All pass [sim].** They cover:

- a good run is accepted
- a missing model raises an error
- a failing run after a good run is not masked by a stale file
- no run directories are left behind
- a singular operating point raises an error
- an aborted transient raises an error even when the completion marker printed
- a missing vector raises an error
- the validator rejects truncated, empty, NaN and wrong-width tables
- a missing output file raises an error
- an unknown build name raises an error
- build B really has RF = 270

**Two real defects the new checks exposed and fixed:**

- **Name clash:** the supply inductor's DCR resistor was called `RL4`, the same name as the port-4 load. ngspice aborted with "device already exists". The old harness would have read stale data. The resistor is renamed `RL4DCR`.
- **Short transient grid:** the linearized two-tone record could end one step short of `tstop` when T/step was not an integer, so the validator flagged it as a partial run. The step is now chosen to divide the record exactly.

## 2. Build configurations

- `gen.BUILDS` defines A, B and C explicitly. Every gain-setting part (RE1, RE2, RF, RLX) is given for every build, and `gen.params(build)` raises an error for an unknown name.
- `run_all.py`, `mc.py`, `stability.py` and `export_netlists.py` all take their values from `gen.params()`. The result labels come from the same dictionary, and `summary.json` records each build's parts next to its numbers.
- The schematic shows build A and notes the B and C values. The BOM lists all three.
- The standalone decks in `sim/spice/` are regenerated from `gen.params('A')`, with a relative model include. All six run cleanly in ngspice with the completion marker and no errors **[sim]**.

| Build | RE1/RE2 | RF | RLX | Status |
| --- | --- | --- | --- | --- |
| **A (recommended)** | 56 | 220 | 220 | default |
| B | 56 | 270 | 220 | option |
| C | 47 | 330 | 220 | option, not for strong-signal sites (see section 6) |

**Rail value changed:** the nominal ideal-rail value is now **9.81 V**, the rail the full supply model gives at 13.8 V in. It was 9.9 V before, so every nominal number shifts slightly.

## 3. Tolerances, model provenance and the LPF

### Sources (`sim/scripts/tolerance.py`)

Every part varies independently. Paired emitter resistors, each LPF L and C, and each output branch get their own draws.

| Part group | Tolerance used | Source |
| --- | --- | --- |
| Resistors | ±1 % uniform | BOM spec |
| L1–L3 as purchased | **±10 %** | Bourns 78FR22K-RC / 78FR27K-RC "K" tolerance (DigiKey M10148-ND, 118-78FR27K-RC-ND) |
| L1–L3 after selection | ±3 % | VNA selection at 10 MHz (bring-up section 0) |
| LPF capacitors | ±2 % (recommended), ±5 % compared | KEMET C315 C0G "G" / "J" |
| Inductor Q | 40–60 | 78FR datasheet Q min 40 at 25 MHz |
| Film capacitors | ±10 % | WIMA MKS4 "K" |
| Electrolytics | ±20 % | |
| Rail | 9.81 V ±4.5 % | LM317 VREF 1.20–1.30 V [datasheet] with 1 % R10/R11 |
| Temperature | 0 / 27 / 50 °C | |

**Transistor model provenance:** the 2N3904/2N3906 models are simplified Gummel-Poon models (NXP-style) from the LTspice `standard.bjt` library, using the mirror at github.com/mpkopec/ltspice-lib. They lack low-current beta droop and current-dependent fT, and their junction capacitances are fixed.

- **Sampled:** BF log-uniform over the datasheet hFE range at 10 mA (100–300) and IS ×0.56–1.79 (about ±15 mV VBE), independent per device.
- **Not sampled:** TF, CJC and an all-device hFE shift are less certain, so they are run as **separate corners** instead.

### The LPF finding: reproduced, then fixed by part choice and selection

The reviewer was right. With the inductors at their real ±10 %, the input match degrades badly. Full-circuit AC Monte Carlo, 100 samples per option, build A, 10 kHz–50 MHz (`lpf_study.py` → `results/lpf_tolerance_study.json`) **[sim]**:

| LPF parts | Worst S11 | 95th pct S11 | Worst flatness | Worst gain @50 MHz | Worst rejection @88 MHz |
| --- | --- | --- | --- | --- | --- |
| L ±10 %, C ±5 % (Rev B as documented) | **−11.0 dB** | −12.5 dB | 1.29 dB | +0.48 dB | 30.9 dB |
| L ±10 %, C ±2 % | −12.1 dB | −13.1 dB | 1.17 dB | +0.60 dB | 31.5 dB |
| **L selected to ±3 %, C ±2 % (adopted)** | **−19.8 dB** | −20.8 dB | 0.93 dB | +0.80 dB | 33.5 dB |

What this shows:

- **The inductors dominate.** Tighter capacitors alone barely help.
- **Tighter stocked inductors don't exist.** No stocked ±5 % through-hole 220/270 nH part with adequate Q was found. Gowanda 10M220JLF and API Delevan 1025R-04J are non-stocked or high-MOQ. The Delevan 9405-04 adjustable is about €50 with a 250-piece minimum.
- **Adopted fix:** buy 10 × 78FR22K-RC and 5 × 78FR27K-RC (about US$0.30 each), then measure them on the VNA and pick parts within ±3 % (bring-up section 0). For uniform ±10 % parts, about 30 % fall inside ±3 %.
- **Filter not redesigned:** a less sensitive filter would give up 88–108 MHz rejection, and selection reaches the same match without that cost.

**Achievable spec, stated honestly [sim]:**

- **Selected inductors:** S11 ≤ −19.4 dB, flatness ≤ 0.93 dB from 10 kHz to 50 MHz (≤ 0.89 dB at the 95th percentile), ≥ 33.4 dB rejection at 88 MHz.
- **Unselected inductors:** S11 can be as poor as about −11 dB, with up to ~1.3 dB of flatness.
- **Superseded targets:** the earlier "S11 ≤ −20 dB, flatness ≤ 0.8 dB, ≥ 36 dB at 88 MHz" was computed without the exact 50 MHz edge and is withdrawn (section 0).

### Full Monte Carlo, build A (`mc.py` → `results/mc_A.json`) [sim]

Conditions: 200 samples, selected L, ±2 % C, all other tolerances above, devices sampled, temperature 0/27/50 °C. **0 failed simulations.**

| Quantity | Nominal | Min | 5th pct | Median | 95th pct | Max |
| --- | --- | --- | --- | --- | --- | --- |
| Rail current (mA) | 89.8 | 78.5 | 81.2 | 87.7 | 94.3 | 96.6 |
| Q1 current (mA) | 28.9 | 22.8 | 25.0 | 27.6 | 30.3 | 30.8 |
| Output Iq (mA) | 38.0 | 30.6 | 33.8 | 36.9 | 40.9 | 43.2 |
| OUT DC (V) | 4.84 | 4.47 | 4.66 | 4.92 | 5.15 | 5.26 |
| Gain @1 MHz (dB) | 1.72 | 1.54 | 1.60 | 1.71 | 1.82 | 1.89 |
| Gain @50 MHz (dB) | 0.84 | 0.69 | 0.74 | 0.86 | 0.97 | 1.04 |
| Flatness 10 kHz–50 MHz (dB) | 0.88 | 0.79 | 0.81 | 0.85 | 0.89 | 0.91 |
| Worst S11 (dB) | −23.3 | — | — | −22.9 | −20.8 | **−19.4** |
| Worst S22 (dB) | −23.3 | — | — | −23.2 | −23.0 | −23.0 |
| Port isolation @30 MHz (dB) | 32.3 | 31.9 | | 32.2 | | 32.4 |
| Output-to-input isolation @30 MHz (dB) | 61.0 | 60.7 | | 60.9 | | 61.2 |
| Rejection @88 MHz (dB) | 34.8 | 33.4 | 34.2 | 34.8 | 35.5 | 35.8 |
| NF @10 MHz (dB) | 8.32 | 8.13 | 8.26 | 8.59 | 9.00 | 9.13 |
| IIP3 7.0/7.2 MHz (dBm) | +30.9 | +29.1 | +29.8 | +30.6 | +31.5 | +31.8 |
| IIP2 6+7 MHz (dBm) | +78.8 | **+60.0** | +62.1 | +69.8 | +81.3 | +88.0 |

Notes:

- **Gain spread:** unit-to-unit gain spread across all 200 samples is 0.36 dB at 1 MHz and 0.36 dB at 50 MHz (min to max). That compares with the reviewer's 1.38 dB, which came from unselected inductors with ±5 % capacitors.
- **Unselected-inductor MC:** with otherwise identical tolerances, S11 reaches −11.6 dB, gain at 50 MHz drops to +0.53 dB, flatness reaches 1.14 dB and 88 MHz rejection falls to 31.6 dB.
- **IIP2 spread:** the wide spread comes from NPN/PNP mismatch in the sampled models. The true spread in hardware is **[unverified]**.

### Corners (all devices shifted together, nominal passives) [sim]

| Corner | Rail I (mA) | Gain 1 / 50 MHz | Flatness | S11 | NF10 | IIP3 7 MHz | IIP2 6+7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nominal 27 °C | 89.8 | 1.72 / 0.84 | 0.88 | −23.3 | 8.32 | +30.9 | +78.8 |
| 0 °C / 50 °C | 88.6 / 90.9 | 1.73 / 0.86, 1.72 / 0.83 | 0.87–0.89 | −23.3 | 8.32 | +31.1 / +30.7 | +79.9 / +78.1 |
| rail −4.5 % / +4.5 % | 84.5 / 95.2 | 1.71 / 0.81, 1.74 / 0.87 | 0.87–0.90 | −23.3 | 8.26 / 8.38 | +30.2 / +31.4 | +77.8 / +79.9 |
| all hFE 100 | 84.0 | 1.53 / 0.66 | 0.87 | −23.4 | 9.28 | +30.6 | +72.5 |
| all hFE 300 | 90.8 | 1.75 / 0.87 | 0.88 | −23.3 | 8.14 | +31.0 | +71.0 |
| TF ×0.7 / ×1.4 | 89.8 | 1.72 / 0.89, 1.72 / 0.74 | 0.83 / 0.99 | −23.6 / −23.1 | 8.27 / 8.42 | +31.0 / +30.8 | +78.8 / +79.7 |
| CJC ×0.7 / ×1.4 | 89.8 | 1.72 / 1.16, 1.72 / **0.33** | 0.56 / **1.39** | −23.7 / −22.8 | 8.33 | +31.4 / +30.3 | +81.0 / +77.8 |

The model's collector capacitance is the main uncertainty for the 50 MHz end. If the real CJC is 40 % higher, gain at 50 MHz drops to about +0.3 dB and flatness grows to 1.4 dB. Below 30 MHz the effect is ≤ 0.2 dB.

## 4. Stability (`stability.py`, `mu_bands.py` → `results/stability_*.json`, `mu_bands_*.json`)

Old evidence: one-port Re(Z) scans. That showed only that **one** port at a time could not see negative resistance. It did not cover mixed terminations, source mismatch or cables. Two new analyses replace it, run for builds A, B and C **[sim]**.

### 1. Multiport μ test

**Method:**

- Extract the full 5-port S-matrix (input + 4 outputs) from 10 kHz to 2 GHz with the modelled lead, ESL and pad parasitics.
- For a pair of ports, terminate the other three in every combination of |Γ| = 0, |Γ| = 0.5 and |Γ| = 1 at 12 phases (25³ = 15,625 combinations).
- Compute the Edwards-Sinsky μ of the reduced 2-port at each frequency.
- μ > 1 means that 2-port is unconditionally stable for **any** passive load on its own two ports, given those other-port loads.
- Pairs tested: input–port 1 (this covers source mismatch at J1) and port 1–port 2. Ports 1–4 are identical by symmetry.

**Results:**

| Band | μ min, input–port 1 | μ min, port 1–port 2 |
| --- | --- | --- |
| 10 kHz–60 MHz | 11.3 | 11.3 |
| 60–500 MHz | 2.52 | 2.52 |
| 0.5–1 GHz | 1.56 | 1.56 |
| 1–2 GHz | **1.07** (at 2 GHz, the sweep edge) | 1.07 |

Builds B and C give the same μ to within 0.15 below 60 MHz and identical values above.

### 2. Time-domain kicks with cables

**Method:**

- A 2 ns, 10 mA current pulse is injected at node X.
- All five ports connect through lumped-ladder RG-58-like coax (0.1–5 m). The far ends are open, short, 50 Ω, 100 pF or 1 µH.
- Cases: 4 uniform-length sets per far-end type, plus 16 random mixed sets (different cable and far end on every port, including the input).
- The record runs 8 µs, and decay is checked after 7 µs.

**Results:**

- **Builds A, B and C: 33 of 33 cases decay. 0 simulator failures, 0 aborted runs.**
- **Negative control:** a series RLC with −5 Ω on OUT is flagged as non-decaying (it grows to 5 V), which shows the test can fail.

### What is supported, and what is not

The blanket "no passive load can cause oscillation" is withdrawn. The supported conclusion is:

> Within the transistor models and the modelled parasitics, the circuit is unconditionally stable between any two ports for every sampled set of passive (including fully reactive) loads on the other three ports, from 10 kHz to 2 GHz. Every simulated mixed cable/termination case decays.

Limits:

- **Phase sampling:** the μ test samples other-port phases at 30° steps. It is not a proof for every possible termination.
- **2 GHz margin:** μ falls toward 1 at the 2 GHz sweep limit.
- **Model validity:** the transistor models are not trustworthy above ~500 MHz.
- **Layout:** layout parasitics beyond the lumped estimates are not modelled.
- **Hardware:** an oscillation check with open, shorted and long-cable ports to at least 1 GHz remains a bring-up requirement **[hw]**.

## 5. Power supply (`supply.py` → `results/supply.json`)

### Parts

| Ref | Part | Verified data |
| --- | --- | --- |
| L4 | **Bourns RLB0914-100KL**, 10 µH | ±10 %, 2.7 A, Isat 6.7 A typ, DCR 48 mΩ max, SRF 20 MHz, Q 50 at 2.52 MHz, 8.7–9.2 mm dia × 12–13 mm, 5 mm pitch, in production (RS 811-8799). Replaces the unspecified 100 µH. |
| RDAMP | 1.0 Ω in series with L4 | Damps L4 with C22 (Z0 = 0.15 Ω, so the filter is overdamped); dissipates 9 mW |
| F1 | **Littelfuse RXEF030** (0.3 A hold, 0.6 A trip) | Rmin 0.88 Ω, Rmax 1.33 Ω, R1max 2.1 Ω. Replaces the RXEF020, which has 1.83 Ω min, to recover headroom. |
| D6, D7 | 1N4002 | TI-recommended protection: D6 OUT→IN, D7 ADJ→OUT (needed because C21 sits on ADJ) |
| C23 | 10 µF at the U1 output pin | |
| RDUMMY | **TE ROX3SJ100R**, 100 Ω 5 % 3 W | Test fixture for power-only bring-up: ~98 mA, ~1 W |

### Modelling

- **Regulator:** LM317 is behavioural. The pass current comes from the input (so input current is real), there is a fixed dropout (1.7 V, the typical value at ~0.1 A), a 1.5 A current limit and an approximate output impedance.
- **Line rejection:** the model's line rejection is ideal, so ripple is bounded conservatively by injecting at the regulator output with **no** rejection.
- **Protection parts:** the PTC is modelled at its maximum initial resistance and D5 as a 1N5819.

### Results [sim] (13.8 V in, build A)

- **Rail:** 9.81 V. Input current 95.1 mA. U1 headroom 3.47 V.
- **Datasheet headroom:** U1 has ≥ 3 V headroom (the LM317 datasheet regulation test condition) for **VIN ≥ 13.4 V** [sim + datasheet]. With typical dropout the model regulates down to about **12.1 V** in. Below 13.4 V, regulation depends on typical, not guaranteed, behaviour.
- **Start-up:**
  - No rail overshoot for 1 ms or 1 µs (hot-plug) ramps. The rail reaches 99 % in 75 ms, set by the bias-network time constants.
  - Hot-plug inrush into C20 peaks at 8.4 A for well under 1 ms. With the PTC at its 0.88 Ω minimum this rises to about 11 A, still within the 1N5819's 25 A IFSM.
- **Rail impedance at the amplifier:**
  - 0.99 Ω at 100 Hz (RDAMP + DCR outside the regulation loop), 0.31 Ω at 1 kHz, 0.10 Ω from 10 kHz to 1 MHz, 0.05 Ω at 30 MHz. No LC peak: the maximum is 1.14 Ω at 10 Hz.
  - The amplifier is class A with near-constant current, so this costs nothing in signal terms.
- **Regulator-output noise to port 1, worst case with no regulator rejection:** −14 dB at 100 Hz, −43 dB at 100 kHz, −64 dB at 1 MHz, −96 dB at 10 MHz. The real LM317's rejection adds to this, typically ~65–80 dB at 120 Hz [datasheet]. Rail noise is therefore not expected to be visible in the HF band.
- **Fault with U1's input shorted:**
  - With D6, U1 OUT−IN peaks at 1.97 V during the discharge. Without D6 it reaches 7.0 V (6.6 V still on the rail 5 ms later).
  - With D7, OUT−ADJ stays ≤ −0.07 V. Without D7 it reaches +1.2 V.
- **Dissipation:** U1 0.33 W, so no heatsink is needed: a TO-220 at about 50–65 °C/W junction-to-air rises about 15–20 °C [est].
- **Minimum load:**
  - The divider alone draws 5.2 mA. That is below the LM317's 10 mA maximum minimum-load spec [datasheet], so an unloaded power-only test is not a valid check of the regulator.
  - The behavioural model cannot show the unloaded rise, so that case is **[unverified]**.
  - With the 100 Ω dummy the model gives 9.80 V at 103 mA. In circuit, the amplifier's ~90 mA meets the spec.

## 6. Nominal performance, all builds (`run_all.py` → `results/summary.json`) [sim]

Conditions: 50 Ω source, four 50 Ω loads, measured at J2. Ideal 9.81 V rail. Every two-tone figure is computed at 80 and 160 steps per cycle, and the 160-step value is reported. The largest 80-vs-160 difference is shown in the last row.

| | A (recommended) | B | C |
| --- | --- | --- | --- |
| Gain 10 kHz / 1 / 10 / 30 / 50 MHz (dB) | 1.72 / 1.72 / 1.69 / 1.42 / 0.84 | 3.15 / 3.16 / 3.11 / 2.74 / 2.01 | 5.51 / 5.52 / 5.45 / 4.95 / 4.02 |
| Flatness 10 kHz–50 MHz (dB) | 0.88 | 1.14 | 1.50 |
| Worst S11 / S22, 10 kHz–50 MHz (dB) | −23.3 / −23.3 | −20.8 / −23.2 | −20.4 / −23.2 |
| Port isolation 1 / 30 / 50 MHz (dB) | 34.2 / 32.3 / 29.4 | 34.2 / 32.3 / 29.3 | 34.2 / 32.3 / 29.2 |
| Output-to-input isolation 30 MHz (dB) | 61.0 | 61.6 | 62.8 |
| Rejection 88 / 100 / 108 MHz (dB) | 34.8 / 44.8 / 50.7 | 34.1 / 44.3 / 50.4 | 32.8 / 43.0 / 49.0 |
| NF 1 / 10 / 30 / 50 MHz (dB) | 8.2 / 8.3 / 9.2 / 10.6 | 7.6 / 7.8 / 8.7 / 10.2 | 6.8 / 6.9 / 7.9 / 9.5 |
| IIP3 1 / 7 / 14 / 28 MHz, −10 dBm tones (dBm) | +32.0 / +30.9 / +29.3 / +27.1 | +30.6 / +29.4 / +27.8 / +25.6 | +28.4 / +27.1 / +25.5 / +23.5 |
| IIP3 7 MHz, 0 dBm tones | +29.7 | +27.8 | **+20.8** |
| IIP2 6+7 MHz, −10 / 0 dBm tones | +79.7 / +78.5 | +77.7 / +75.7 | +76.7 / **+43.7** |
| IIP2 0.6+1.0 MHz, −10 / 0 dBm tones | +82.1 / +78.8 | +80.1 / +75.6 | +76.9 / **+43.2** |
| Input / output P1dB at 7 MHz (dBm) | +11.0 / +11.7 | +9.8 / +11.9 | +8.1 / +12.6 |
| Rail current, ideal rail (mA) | 89.8 | 89.8 | 94.5 |
| Input current from 13.8 V, full supply (mA) | 95.1 | 95.1 | 99.8 |
| Largest two-tone difference, 80 vs 160 steps (dB) | 0.83 (IIP2) | 0.51 | 0.41 |

**Build C:** with 0 dBm tones it is approaching compression, and IIP2 and IIP3 collapse. Use it only where the antenna delivers well under −10 dBm per signal.

**Correction to review 1:** the earlier "IIP2 +70 dBm", in my results and in the reviewer's, was unconverged. At 20 steps per cycle, reltol 1e-5, IIP2 moved by up to 20 dB. The earlier "≤ 1 dB convergence" statement was wrong.

**Convergence study** (`convergence.py`):

- IIP3 agrees within 0.3 dB at ≥ 80 steps per cycle with gear or trap integration.
- IIP2 agrees within 0.3 dB at 0 dBm tones and within about 1 dB at −10 dBm tones, where the IM2 product is near −100 dBm.
- Gear integration is now the default. Trapezoidal integration ran 20–200× slower on some Monte Carlo samples (step rejection) while giving the same intercepts where it finished. This was found when 2 of the first MC samples took more than 6 minutes each.

**Thermal** (`thermal.py`) [sim]:

- Output Iq changes < 0.2 mA from 0 to 50 °C ambient.
- Outputs 30 °C hotter than their pre-drivers: Iq rises to 48.5 mA, self-limiting.
- Outputs bonded to their pre-drivers (+30 / +10 °C): 45 mA.

## 7. Status

**Supported by simulation:**

- Gain, match, isolation, FM rejection and NF figures, with the tolerance spreads above. S11 ≤ −19.4 dB relies on selected inductors.
- IIP3 to ±0.3 dB numerical accuracy.
- Bias spread and thermal behaviour.
- Multiport stability to 2 GHz within the models.
- Supply start-up, impedance, fault clamping and headroom.

**Not established; needs hardware [hw]:**

- Absolute IP3/IP2: the models' nonlinearity and the NPN/PNP matching are approximate.
- NF.
- 50 MHz gain: depends on the real CJC.
- Oscillation-free behaviour with real layout parasitics.
- Unloaded LM317 behaviour.
- Thermal drift in the real enclosure.

**PCB layout readiness:** ready to start layout. No simulation blocker remains. Open items that do not block layout but must be closed before ordering parts:

- Confirm current distributor stock of KEMET C315C430G3G5TA (43 pF ±2 %). An equivalent ±2 % C0G radial on a 2.54 mm pitch fits the same footprint.
- Confirm 78FR27K-RC stock.
- Note the footprints: L4 needs a radial 9.2 mm dia / 5 mm pitch footprint, and F1 a 7.4 × 3 mm radial.
