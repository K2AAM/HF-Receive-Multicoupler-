# Bring-up and bench test (Rev B)

> **Prototype PCB:** the board-specific assembly steps and test-point readings are in the section *Prototype PCB (build A): assembly and test points* at the end of this file. The PCB uses numeric references (Q1–Q6, R1–R25); the table there maps them to the names used below.

Expected values come from simulation (9.81 V rail) and are not measurements. Monte Carlo (MC) ranges are given where they exist. They describe simulated tolerance spread, not guaranteed hardware limits. Measured values outside them call for investigation, not automatic rejection.

## 0. Select the LPF inductors (before assembly)
The Bourns 78FR inductors are ±10 %. In simulation, unselected parts can degrade S11 to about −11 dB. Parts selected to ±3 % hold S11 ≤ −19.4 dB (worst of 200 Monte Carlo units), or about −19.2 dB with ±5 % 43 pF end capacitors. Optional: buy 6 of the 43 pF capacitors and fit the two closest to 43 pF.

1. Buy 10 × 78FR22K-RC (L1, L3) and 5 × 78FR27K-RC (L2).
2. Calibrate the VNA (SOL) at the end of a short fixture: a BNC-to-clip or SMA edge pad with ≤ 5 mm leads.
3. Measure each inductor at 10 MHz and read L from the reactance (X = 2πfL). 220 nH is 13.8 Ω at 10 MHz, and 270 nH is 17.0 Ω.
4. Keep inductors within ±3 %: 213–227 nH (13.4–14.3 Ω) and 262–278 nH (16.5–17.5 Ω). Prefer an L1/L3 pair that also match each other.
5. If none fall in the window, use the closest parts and expect S11 between −11 and −19 dB.

The VNA fixture adds a few nH, so measure a short-circuited fixture first and subtract its reactance.

## 1. Power section alone (amplifier unpopulated)
The LM317's minimum load is up to 10 mA [datasheet], but its divider draws only 5.2 mA. **Do not judge the regulator without a load.**

1. Fit the dummy load **RDUMMY = 100 Ω, 3 W (TE ROX3SJ100R)** from the rail (C22 +) to ground. It draws about 98 mA and dissipates about 1 W, so keep it off the board surface.
2. Feed J6 from a bench supply at 13.8 V, current-limited to 200 mA.
3. Check these:
   - Input current about 103 mA.
   - Rail 9.6–10.2 V (9.80 V nominal [sim]; the spread comes from LM317 VREF 1.20–1.30 V [datasheet]).
   - U1 IN − OUT ≥ 3.0 V.
   - Drop from J6 to U1 IN (F1 + D5) under 0.6 V.
4. Lower the supply to 13.4 V. The rail should not move by more than 10 mV.
5. Check the diode orientation: D6 has its anode on U1 OUT and its cathode on U1 IN; D7 has its anode on ADJ and its cathode on OUT. Both should be reverse-biased, so no current flows in normal operation.
6. Remove RDUMMY before populating the amplifier.

## 2. First power-up of the amplifier
1. Populate everything. Bond Q2 face-to-face to Q2A, and Q3 to Q3A, using thermal epoxy or a small clamp.
2. Power up through a 150 mA current limit. Expected supply current from 13.8 V: about 95 mA. The Monte Carlo range for the rail current is 79–97 mA, plus 5 mA for the divider. Above 120 mA, switch off and check RX1/RX2 and the diamond wiring.
3. DC voltages, all ±0.3 V:

| Node | Expected |
| --- | --- |
| X | 4.8 V (MC 4.5–5.3) |
| OUT | 4.8 V |
| D1 | 5.7 V |
| D2 | 4.0 V |
| BN | 2.4 V |
| BP | 7.4 V |
| Q2 collector (after RC) | 9.6 V |

4. Output quiescent current: about 125 mV across RE3 or RE4 (3.3 Ω), which is 38 mA. The MC range is 31–43 mA (100–142 mV). Q1 current: about 1.62 V across RE1, which is 29 mA (MC 23–31 mA).
5. Let it run 15 minutes in the closed box and recheck RE3. A rise of up to ~20 % is expected. A steady climb means poor thermal bonding.
6. If OUT is more than 0.5 V off center: raise R2 to lower it, or raise R4 to raise it (in 10 % steps).

## 3. Small-signal checks (VNA, ports terminated)
- **Gain:** J1 → J2, with J3–J5 terminated in 50 Ω. Simulated nominal: +1.72 dB at 1 MHz, +1.42 dB at 30 MHz and +0.84 dB at 50 MHz. Monte Carlo ranges (sim): 1.54–1.89 dB at 1 MHz and 0.69–1.04 dB at 50 MHz; flatness 10 kHz–50 MHz 0.79–0.91 dB. If 50 MHz measures near +0.3 dB, the transistors' CJC is higher than modelled. Repeat for each port. Port-to-port spread should be < 0.2 dB.
- **FM rejection:** simulated S21 at 88/100/108 MHz is about −34.8/−44.8/−50.7 dB nominal. With selected inductors the Monte Carlo range at 88 MHz is −33.4 to −35.8 dB. Inductor tolerance moves the edge, so check that gain at 50 MHz is within about 0.9 dB of gain at 1 MHz.
- **Match:** simulated S22 is −23.3 dB nominal (MC worst −23.0 dB). S11 is −23.3 dB nominal and, with selected inductors, no worse than −19.4 dB (MC). Measure from 0.1–50 MHz, and include 50 MHz itself.
- **Port-to-port isolation:** drive J2, measure J3, with J1, J4 and J5 terminated. Expect ≥ 33 dB at 1–10 MHz, ≥ 32 dB at 30 MHz, ≥ 29 dB at 50 MHz.
- **Output-to-input isolation:** drive J2, measure J1. Expect ≥ 60 dB at 30 MHz.
- **10 kHz–50 kHz:** below the VNA's lower limit. Use the R&S SMG or URM-26D into J1, with a scope or audio analyzer on J2 across 50 Ω. Expect +1.7 dB at 10 kHz.

## 4. Mismatch and oscillation checks
- Leave J2–J5 open, then shorted, then on 3–5 m of open-ended coax, then a mix (simulation covered 33 such cases, all stable). Watch the TinySA (via a 20 dB pad on one port) from 100 kHz to at least 1 GHz with no input signal. Any discrete line that comes and goes as you touch cables or the box is an oscillation. Expected result: none.
- Repeat with J1 open and with J1 shorted.
- Look at OUT with a 10× probe on the 2465A at 500 MHz bandwidth. You should see no RF with no input.

## 5. Compression
- Single tone at 7 MHz into J1. Step from −10 to +14 dBm and watch J2 on the TinySA through a 20 dB pad.
- Expected output P1dB is about +11.7 dBm per port (input +11 dBm), with all four ports loaded.

## 6. Intermodulation
- Combine the SMG and URM-26D in a resistive or hybrid combiner, with 6–10 dB pads on each generator so they don't intermodulate each other.
- Two tones at 7.0 and 7.2 MHz, −10 dBm each at J1.
- Expected at J2: tones about −8.3 dBm, IM3 about −90 dBm (OIP3 ≈ +32.5 dBm).
- The TinySA's own IM3 is likely to dominate at this level. Check by adding 10 dB of attenuation in front of the analyzer: if the IM products drop by more than 10 dB, the analyzer is the limit.
- **IM2:** use 6.0 + 7.0 MHz and look at 13 MHz. Expected IIP2 is about +79 dBm nominal, +60 to +88 dBm across the Monte Carlo (it depends on transistor matching). At −10 dBm tones the IM2 product is near −100 dBm, so use 0 dBm tones (expect about −80 dBm at 13 MHz).

## Instrument limits
- A VNA cannot measure noise figure or intercept points.
- NF needs a calibrated noise source (Y-factor) or a dedicated noise-figure analyzer.
- Intercept measurements are only as good as the generator isolation and the analyzer's own IM. Always verify with the attenuator step test above.

## Prototype PCB (build A): assembly and test points

The full board description is in [`pcb-prototype-A.md`](pcb-prototype-A.md). All "expected" values below are simulated.

**Reference map:**

| Group | Name in this document → PCB reference |
| --- | --- |
| Transistors | Q1N = Q1, Q1P = Q2, Q2A = Q3, Q3A = Q4, Q2 = Q5, Q3 = Q6 |
| Gain stage and bias | RBL = R1, RE1 = R2, RE2 = R3, RF = R4, RL = R5, R1A = R6, R1B = R7, R2 = R8, R3A = R9, R3B = R10, R4 = R11 |
| Diamond buffer | RPU = R12, RPD = R13, RX1 = R14, RX2 = R15, RC = R16, RE3 = R17, RE4 = R18 |
| Ports | RS1–RS4 = R19–R22 |
| Supply | R10 = R23, R11 = R24, RDAMP = R25 |

### P1. Before soldering
- Select L1–L3 (step 0). Write the measured values on the silkscreen next to each part.
- Check the 1590BB against the assumptions in `pcb-prototype-A.md` section 5: floor thickness, depth, bosses. Then drill:
  - the floor holes for M3 × 4 mm brass spacers, using the bare PCB as a template;
  - the front-wall BNC holes: 4 × at x = −30, −10, +10, +30 mm from the box centre, centre 14.2 mm above the inside floor;
  - the left-wall input BNC hole: 8 mm toward the back wall, centre 16.5 mm up;
  - the back-wall DC jack hole: x = +36 mm, centre 19.5 mm up.
- Check the panel cut-outs on the connector drawings before drilling.

### P2. Assembly order
The order is the same as `layout-guidance.md`: supply first, then output stage and ports, then gain stage, then input and LPF.

1. **Supply:**
   - Fit F1, D5, C17, C20, U1, D6, D7, R23, R24, C21, C23, L4, R25, C22, C18, C19, C24, C25 and C26.
   - Lay U1 flat. Use a nylon screw or none: the tab is VOUT.
   - Wire J6 (pad 1 = +13.8 V, centre of the 722A; pad 2 = GND).
   - Run bring-up step 1 with RDUMMY clipped between TP1 and TP7.
2. **Diamond buffer, ports and BNCs:**
   - Glue each thermal pair flat face to flat face *before* soldering: Q3 (2N3906) to Q5 (2N3904), and Q4 (2N3904) to Q6 (2N3906). Seat the bodies about 2 mm above the board.
   - Fit J2–J5 last in this group, after a trial fit in the box.
3. **Gain stage:** Q1, Q2 and their resistors and capacitors, plus TP2.
4. **Input and LPF:**
   - Fit GDT1, C1, R1, D1–D4, C4–C7 and L1–L3.
   - Fit J1 as about 60 mm of RG-316: centre to J1 pad 1, braid to both J1 pads 2.
5. **Into the box:**
   - Fit spacers and screws at MH1–MH5.
   - Tighten the BNC nuts before the spacer screws.

### P3. DC readings at the test points (amplifier powered, bring-up step 2)
| Reading | Expected (sim) |
| --- | --- |
| TP1 (VCC) | 9.8 V (9.6–10.2 V) |
| TP2 (X) | 4.8 V |
| TP3 (OUT) | 4.8 V |
| TP6 (EN) | 1.62 V → Q1 current 29 mA |
| V(TP4) − V(TP3) | 125 mV → Q5 (doc Q2) current 38 mA |
| V(TP3) − V(TP5) | 125 mV → Q6 (doc Q3) current 38 mA |

TP7 and TP8 are ground.

### P4. Thermal check
Re-read V(TP4) − V(TP3) after 15 minutes in the closed box (step 2.5).

### P5. Match
Measure S11 at J1 before anything else in step 3.

- The layout-parasitic estimate predicts about −18 dB worst case, against −23 dB for the schematic alone.
- If S11 is worse than about −18 dB near 30–50 MHz, change C4 and C7 to 39 pF C0G (estimated −21 dB) and measure again.
- Keep the change only if it measures better.
