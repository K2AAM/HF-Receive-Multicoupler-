# Bring-up and bench test (Rev B)

Expected values come from simulation at the 9.9 V rail. Expect ±10 % on currents.

## 1. Power section alone (amplifier unpopulated)
1. Feed J6 from a bench supply at 13.8 V, current-limited to 150 mA.
2. Check the rail after L4: 9.85–10.0 V. Measured from J6, the drop across the diode and PTC should be under 0.6 V.

## 2. First power-up of the amplifier
1. Populate everything. Bond Q2 face-to-face to Q2A, and Q3 to Q3A, using thermal epoxy or a small clamp.
2. Power up through the supply's 150 mA current limit. Expected supply current: ~96 mA (Monte Carlo range 84–95 mA at the rail). Above 120 mA, switch off and check RX1/RX2 and the diamond wiring.
3. DC voltages, all ±0.3 V:

| Node | Expected |
| --- | --- |
| X | 4.9 V |
| OUT | 4.9 V |
| D1 | 5.8 V |
| D2 | 4.0 V |
| BN | 2.4 V |
| BP | 7.5 V |
| Q2 collector (after RC) | 9.7 V |

4. Output quiescent current: 125–130 mV across RE3 or RE4 (3.3 Ω) means 38–39 mA. Q1 current: 1.64 V across RE1 means 29 mA.
5. Let it run 15 minutes in the closed box and recheck RE3. A rise of up to ~20 % is expected. A steady climb means poor thermal bonding.
6. If OUT is more than 0.5 V off center: raise R2 to lower it, or raise R4 to raise it (in 10 % steps).

## 3. Small-signal checks (VNA, ports terminated)
- **Gain:** J1 → J2, with J3–J5 terminated in 50 Ω. Expect +1.7 dB ±0.5 dB from 100 kHz to 30 MHz and about +0.8 dB at 50 MHz. Repeat for each port. Port-to-port spread should be < 0.2 dB.
- **FM rejection:** S21 at 88/100 MHz should be about −36/−45 dB. Inductor tolerance moves the edge, so check that 50 MHz is still within 1 dB.
- **Match:** S11 and S22 better than −20 dB from 0.1–50 MHz.
- **Port-to-port isolation:** drive J2, measure J3, with J1, J4 and J5 terminated. Expect ≥ 33 dB at 1–10 MHz, ≥ 32 dB at 30 MHz, ≥ 29 dB at 50 MHz.
- **Output-to-input isolation:** drive J2, measure J1. Expect ≥ 60 dB at 30 MHz.
- **10 kHz–50 kHz:** below the VNA's lower limit. Use the R&S SMG or URM-26D into J1, with a scope or audio analyzer on J2 across 50 Ω. Expect +1.7 dB at 10 kHz.

## 4. Mismatch and oscillation checks
- Leave J2–J5 open, then shorted, then on 3 m of open-ended coax. Watch the TinySA (via a 20 dB pad on one port) from 100 kHz to 1 GHz with no input signal. Any discrete line that comes and goes as you touch cables or the box is an oscillation. Expected result: none.
- Repeat with J1 open and with J1 shorted.
- Look at OUT with a 10× probe on the 2465A at 500 MHz bandwidth. You should see no RF with no input.

## 5. Compression
- Single tone at 7 MHz into J1. Step from −10 to +14 dBm and watch J2 on the TinySA through a 20 dB pad.
- Expected output P1dB is about +12 dBm per port, with all four ports loaded.

## 6. Intermodulation
- Combine the SMG and URM-26D in a resistive or hybrid combiner, with 6–10 dB pads on each generator so they don't intermodulate each other.
- Two tones at 7.0 and 7.2 MHz, −10 dBm each at J1.
- Expected at J2: tones about −8.3 dBm, IM3 about −89 dBm (OIP3 ≈ +32 dBm).
- The TinySA's own IM3 is likely to dominate at this level. Check by adding 10 dB of attenuation in front of the analyzer: if the IM products drop by more than 10 dB, the analyzer is the limit.
- **IM2:** use 6.0 + 7.0 MHz and look at 13 MHz. Expected IIP2 is +61 to +86 dBm depending on transistor matching.

## Instrument limits
- A VNA cannot measure noise figure or intercept points.
- NF needs a calibrated noise source (Y-factor) or a dedicated noise-figure analyzer.
- Intercept measurements are only as good as the generator isolation and the analyzer's own IM. Always verify with the attenuator step test above.
