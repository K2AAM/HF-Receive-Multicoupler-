# HF Receive Multicoupler — Rev B

One antenna (an active receive loop such as the LZ1AQ AAA-1C or W6LVP) feeding four receivers: an RX888 or RSPdx plus vintage communications receivers. Through-hole, no hand-wound transformers, 13.8 V supply.

**Status:** design and simulation only. Nothing here has been built or measured yet. All performance numbers are from ngspice with approximate transistor models (see *Model limits*). Treat them as estimates until the hardware is measured.

![schematic](hardware/schematic_revB.png)

## What changed from Rev A

| Rev A problem | Rev B fix |
| --- | --- |
| 2N5160, 2N5109 and 2N3866 are discontinued (Central Semiconductor PDN01114, 2019); 2N5160 only from brokers at ~US$23–52 | Every transistor is a 2N3904 or 2N3906 (stocked jellybeans with published SPICE models) |
| A swap to 2N4401/2N4403 followers drooped 3 dB by 50 MHz and gave only 26 dB isolation at 30 MHz (simulated) | Output stage is a **diamond buffer** (complementary pre-drivers driving complementary outputs), which lowers the star-node impedance at HF |
| 5-pole LPF gave only 8.3 dB at 88 MHz | 7-pole LPF (43p–220n–100p–270n–100p–220n–43p): 36 dB at 88 MHz, 45 dB at 100 MHz |
| 11 V regulator then 10 Ω, so the rail was really ~10.1 V; doc numbers assumed 11 V | Rail is 9.9 V (LM317 at 9.93 V, then a 100 µH choke); all bias was recalculated at 9.9 V |
| Bias-T test (100 Ω at 13.4 V = 134 mA) exceeded its 100 mA PTC | Bias-T removed. Neither loop needs it (W6LVP has its own inserter; the AAA-1C controller powers the amplifier) |
| Electrolytic ‖ 100 nF in series signal paths formed a parallel tank (~5 MHz match dip) | Series coupling caps are single film capacitors |
| Trimmer-set output bias (a failed trimmer could cause runaway) | No trimmer; output current set by fixed RX1/RX2 |

## Simulated performance (recommended +1.7 dB build)

Conditions: 50 Ω source and four 50 Ω loads, measured at J2. Two tones of −10 dBm each, 200 kHz apart. Parasitic model on (lead and ESL inductances, pad capacitances, film-cap ESL). LPF inductor Q = 40.

| Parameter | 1 MHz | 7–10 MHz | 28–30 MHz | 50 MHz |
| --- | --- | --- | --- | --- |
| Gain (dB) | +1.73 | +1.69 | +1.43 | +0.84 |
| Port-to-port isolation (dB) | 34.2 | 34.0 | 32.3 | 29.4 |
| Output-to-input isolation (dB) | 107 | 80 | 61 | 52 |
| NF (dB, excludes receiver load noise) | 8.2 | 8.3 | 9.2 | 10.6 |
| IIP3 / OIP3 (dBm) | +30.7 / +32.4 | +30.1 / +31.9 (7 MHz) | +27.4 / +28.9 (28 MHz) | — |

- Gain at 10 kHz: +1.72 dB. S11 ≤ −23 dB and S22 ≤ −24 dB from 10 kHz to 50 MHz.
- FM rejection: −36 dB at 88 MHz, −45 dB at 100 MHz, −49 dB at 108 MHz.
- IIP2: +70 dBm (6 + 7 MHz), +69 dBm (0.6 + 1.0 MHz). The Monte Carlo spread is +61 to +86 dBm.
- Output P1dB: about +12 dBm per port at 7 MHz, with all four ports loaded.
- Supply: 91 mA at the 9.9 V rail, about 96 mA from 13.8 V.

Full numbers, including the +3 dB and +5.5 dB options, are in [`sim/results/summary.json`](sim/results/summary.json). The point-by-point review answers are in [`docs/review-response.md`](docs/review-response.md).

## Running the simulations

Requires ngspice 42 or later and Python 3 with numpy and matplotlib.

```
cd sim/spice && ngspice tb_ac_forward.cir          # interactive plot of S21/S11
cd sim/scripts && python3 run_all.py               # gain options A/B/C: AC, NF, IP3, IP2, P1dB -> results/summary.json
python3 mc.py 80 40                                # Monte Carlo (80 runs, 40 with two-tone)
python3 thermal.py; python3 stab_z.py              # thermal tracking; port/input real-part stability scan
```

`sim/scripts/gen.py` generates every netlist from one parameter dictionary (`BASE`). The `sim/spice/*.cir` files are standalone exports of the recommended values.

Netlist-to-schematic name map: CIN1 = C1, CBN1/CBP1 = C2/C3, CF1–CF4 = C4–C7, LF1–LF3 = L1–L3, CFB1 = C8, CLX = C9, REO1/REO2 = RE3/RE4, RCOL = RC, CO1A–CO4A = C10–C13.

## Model limits

- 2N3904/2N3906 models are the simplified NXP-style models in the LTspice library. Base resistance, junction capacitances and fT are approximate, and the models have no fT roll-off with current beyond IKF.
- Absolute IP3 can differ by several dB from hardware. IP2 depends on NPN/PNP matching, which the model cannot predict, so it is reported as a Monte Carlo range.
- Some cable-kick transient runs stopped on ngspice "timestep too small" errors (lossless T-lines). Every run that completed decayed. The frequency-domain check (Re Z > 0 at the input and every port, to 2 GHz, for open, short, 100 pF and 1 µH loads) is the primary stability evidence.
