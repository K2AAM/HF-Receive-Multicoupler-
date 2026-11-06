# Review 2 response (Rev B, second verification pass)

Date: 2026-11-05. Simulator: ngspice 42. All results below are **simulation** unless marked otherwise. Nothing has been built or measured yet. Labels:

- **[sim]**: an ngspice run in this repo, regenerated from a clean run with the scripts named
- **[datasheet]**: a published manufacturer limit, not simulated
- **[unverified]**: not executed or not executable here; needs hardware
- **[hw]**: needs a bench measurement

The design stays **four ports, through-hole**. Nothing in the corrected verification required changing the signal-path topology. Three supply parts changed (F1, L4, new D6/D7/C23/RDAMP), and the LPF parts now carry tighter, stated tolerances plus an inductor-selection step.

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

`python3 sim/scripts/test_harness.py` runs 15 regression checks. **All pass [sim].** They cover:

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
| L ±10 %, C ±5 % (Rev B as documented) | **−11.9 dB** | −14.3 dB | 1.04 dB | +0.07 dB | 33.4 dB |
| L ±10 %, C ±2 % | −12.1 dB | −14.7 dB | 1.03 dB | +0.29 dB | 34.0 dB |
| **L selected to ±3 %, C ±2 % (adopted)** | **−20.0 dB** | −20.9 dB | 0.80 dB | +0.63 dB | 36.0 dB |

What this shows:

- **The inductors dominate.** Tighter capacitors alone barely help.
- **Tighter stocked inductors don't exist.** No stocked ±5 % through-hole 220/270 nH part with adequate Q was found. Gowanda 10M220JLF and API Delevan 1025R-04J are non-stocked or high-MOQ. The Delevan 9405-04 adjustable is about €50 with a 250-piece minimum.
- **Adopted fix:** buy 10 × 78FR22K-RC and 5 × 78FR27K-RC (about US$0.30 each), then measure them on the VNA and pick parts within ±3 % (bring-up section 0). For uniform ±10 % parts, about 30 % fall inside ±3 %.
- **Filter not redesigned:** a less sensitive filter would give up 88–108 MHz rejection, and selection reaches the same match without that cost.

**Achievable spec, stated honestly [sim]:**

- **Selected inductors:** S11 ≤ −20 dB, flatness ≤ 0.8 dB from 10 kHz to 50 MHz, ≥ 36 dB rejection at 88 MHz.
- **Unselected inductors:** S11 can be as poor as about −12 dB, with up to ~1 dB of flatness error near 50 MHz.

### Full Monte Carlo, build A (`mc.py` → `results/mc_A.json`) [sim]

Conditions: 200 samples, selected L, ±2 % C, all other tolerances above, devices sampled, temperature 0/27/50 °C. **0 failed simulations.**

| Quantity | Nominal | Min | 5th pct | Median | 95th pct | Max |
| --- | --- | --- | --- | --- | --- | --- |
| Rail current (mA) | 89.8 | 78.5 | 81.2 | 87.7 | 94.3 | 96.6 |
| Q1 current (mA) | 28.9 | 22.8 | 25.0 | 27.6 | 30.3 | 30.8 |
| Output Iq (mA) | 38.0 | 30.6 | 33.8 | 36.9 | 40.9 | 43.2 |
| OUT DC (V) | 4.84 | 4.47 | 4.66 | 4.92 | 5.15 | 5.26 |
| Gain @1 MHz (dB) | 1.72 | 1.54 | 1.60 | 1.71 | 1.82 | 1.89 |
| Gain @50 MHz (dB) | 0.71 | 0.55 | 0.62 | 0.74 | 0.85 | 0.97 |
| Flatness 10 kHz–50 MHz (dB) | 0.77 | 0.70 | 0.71 | 0.74 | 0.77 | 0.79 |
| Worst S11 (dB) | −23.3 | — | — | −22.9 | −20.8 | **−19.4** |
| Worst S22 (dB) | −23.7 | — | — | −23.7 | −23.4 | −23.4 |
| Port isolation @30 MHz (dB) | 32.3 | 31.9 | | 32.2 | | 32.5 |
| Output-to-input isolation @30 MHz (dB) | 61.0 | 60.8 | | 61.0 | | 61.3 |
| Rejection @88 MHz (dB) | 37.2 | 35.9 | 36.6 | 37.2 | 38.0 | 38.2 |
| NF @10 MHz (dB) | 8.32 | 8.13 | 8.26 | 8.59 | 9.00 | 9.13 |
| IIP3 7.0/7.2 MHz (dBm) | +30.9 | +29.1 | +29.8 | +30.6 | +31.4 | +31.8 |
| IIP2 6+7 MHz (dBm) | +78.8 | **+60.0** | +62.1 | +69.8 | +81.3 | +88.0 |

Notes:

- **Gain spread:** unit-to-unit gain spread across all 200 samples is 0.36 dB at 1 MHz and 0.42 dB at 50 MHz (min to max). That compares with the reviewer's 1.38 dB, which came from unselected inductors with ±5 % capacitors.
- **Unselected-inductor MC:** with otherwise identical tolerances, S11 reaches −11.6 dB, gain at 50 MHz drops to +0.22 dB and flatness reaches 1.06 dB.
- **IIP2 spread:** the wide spread comes from NPN/PNP mismatch in the sampled models. The true spread in hardware is **[unverified]**.

### Corners (all devices shifted together, nominal passives) [sim]

| Corner | Rail I (mA) | Gain 1 / 50 MHz | Flatness | S11 | NF10 | IIP3 7 MHz | IIP2 6+7 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| nominal 27 °C | 89.8 | 1.72 / 0.71 | 0.77 | −23.3 | 8.32 | +30.9 | +78.8 |
| 0 °C / 50 °C | 88.6 / 90.9 | 1.73 / 0.72, 1.72 / 0.69 | 0.76–0.77 | −23.3 | 8.32 | +31.0 / +30.6 | +79.9 / +78.1 |
| rail −4.5 % / +4.5 % | 84.5 / 95.2 | 1.71 / 0.67, 1.74 / 0.73 | 0.75–0.78 | −23.3 | 8.26 / 8.38 | +30.2 / +31.4 | +77.8 / +79.9 |
| all hFE 100 | 84.0 | 1.53 / 0.52 | 0.76 | −23.4 | 9.28 | +30.5 | +72.5 |
| all hFE 300 | 90.8 | 1.75 / 0.73 | 0.77 | −23.3 | 8.14 | +30.9 | +71.0 |
| TF ×0.7 / ×1.4 | 89.8 | 1.72 / 0.76, 1.72 / 0.58 | 0.73 / 0.85 | −23.6 / −23.1 | 8.27 / 8.42 | +30.9 / +30.8 | +78.8 / +79.7 |
| CJC ×0.7 / ×1.4 | 89.8 | 1.72 / 1.04, 1.72 / **0.16** | 0.48 / **1.23** | −23.7 / −22.8 | 8.33 | +31.3 / +30.3 | +81.0 / +77.8 |

The model's collector capacitance is the main uncertainty for the 50 MHz end. If the real CJC is 40 % higher, gain at 50 MHz drops to about +0.2 dB. Below 30 MHz the effect is ≤ 0.2 dB.

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
| Gain 10 kHz / 1 / 10 / 30 / 50 MHz (dB) | 1.72 / 1.72 / 1.69 / 1.42 / 0.83 | 3.15 / 3.16 / 3.11 / 2.74 / 2.00 | 5.51 / 5.52 / 5.45 / 4.95 / 4.01 |
| Worst S11 / S22, 10 kHz–50 MHz (dB) | −23.3 / −23.7 | −20.8 / −23.6 | −20.4 / −23.6 |
| Port isolation 1 / 30 / 50 MHz (dB) | 34.2 / 32.3 / 29.4 | 34.2 / 32.3 / 29.3 | 34.2 / 32.3 / 29.2 |
| Output-to-input isolation 30 MHz (dB) | 61.0 | 61.6 | 62.8 |
| Rejection 88 / 100 / 108 MHz (dB) | 35.9 / 44.9 / 49.4 | 35.3 / 44.5 / 49.0 | 34.0 / 43.1 / 47.6 |
| NF 1 / 10 / 30 / 50 MHz (dB) | 8.2 / 8.3 / 9.2 / 10.6 | 7.6 / 7.8 / 8.7 / 10.2 | 6.8 / 6.9 / 7.9 / 9.5 |
| IIP3 1 / 7 / 14 / 28 MHz, −10 dBm tones (dBm) | +31.9 / +30.8 / +29.3 / +27.1 | +30.6 / +29.4 / +27.8 / +25.6 | +28.4 / +27.1 / +25.5 / +23.5 |
| IIP3 7 MHz, 0 dBm tones | +29.7 | +27.8 | **+20.8** |
| IIP2 6+7 MHz, −10 / 0 dBm tones | +79.7 / +78.5 | +77.7 / +75.7 | +76.7 / **+43.7** |
| IIP2 0.6+1.0 MHz, −10 / 0 dBm tones | +82.5 / +79.3 | +80.8 / +76.0 | +77.4 / **+43.7** |
| Input / output P1dB at 7 MHz (dBm) | +11.0 / +11.7 | +9.8 / +11.9 | +8.1 / +12.6 |
| Rail current, ideal rail (mA) | 89.8 | 89.8 | 94.5 |
| Input current from 13.8 V, full supply (mA) | 95.1 | 95.1 | 99.8 |
| Largest two-tone difference, 80 vs 160 steps (dB) | 0.94 (IIP2) | 0.45 | 0.43 |

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
