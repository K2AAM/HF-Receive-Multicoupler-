# Review response — Rev A to Rev B

Dates: sourcing checked 2026-11-05. Labels used below:

- **[sim]** = ngspice run that is in this repo
- **[est]** = hand estimate
- **[hw]** = needs hardware measurement

## 1. Verification of the Rev A complementary amplifier

Checked against the Rev A netlist as simulated (`amp.inc`, not in this repo).

- **Separate NPN/PNP base coupling and bias:** correct in the netlist. Each base had its own coupling capacitor and its own collector-feedback divider. Feedback polarity was correct: RF went from the inverting collector node back to the input.
- **Electrolytic polarity:** all correct for the DC voltages in the sim.
- **Errors found:**
  - The rail was modelled as an ideal 11 V source. With the specified 10 Ω filter it would really have been ~10.1 V.
  - Every series coupling cap was an electrolytic ‖ 100 nF film. Once electrolytic ESL is included, that forms a parallel tank near 4–5 MHz **[sim]**.
- **Bias spreader / startup / failure:**
  - Iq depended on 1N4148 diodes that were not thermally coupled to the output devices.
  - Iq was steep against RV1 (about 1 mA per 2 Ω) **[sim]**.
  - Diode–Vbe mismatch plus self-heating could raise Iq by about 50 % **[est]**. Rev B removes the trimmer.
- **2N5109/2N5160 cancellation:** depends on device matching. Rev B reports IP2 as a Monte Carlo range for that reason (section 4).

## 2. Outstanding errors, resolved

| Item | Resolution |
| --- | --- |
| 11 V → 10 Ω → ~10.1 V rail | Rail is now **9.9 V**. U1 (LM317) is set to 9.93 V (R10 240 Ω, R11 1.65 kΩ, including 50 µA ADJ current), followed by L4 100 µH (DCR drop ~0.03 V). All bias was simulated at 9.9 V. |
| LM317 dropout margin | The datasheet line/load regulation specs apply for 3 V ≤ VIN − VOUT ([onsemi table](https://www.scribd.com/doc/6617290/LM317T)). At 13.8 V in: −0.33 V (1N5819 at 0.1 A) −~0.2 V (PTC) → 13.25 V at U1, giving **3.3 V headroom**. Below ~13.2 V supply it falls under the guaranteed-regulation condition but typically still regulates. Minimum load (10 mA max spec) is met by the 96 mA load. U1 dissipation ≈ 0.32 W. |
| Total supply current | **91 mA** at the 9.9 V rail **[sim]**, plus ~5 mA for the LM317 divider: ≈ **96 mA** from 13.8 V. Monte Carlo range for the rail current: 84–95 mA. |
| LPF actually 8.3 dB at 88 MHz | Confirmed: the old network gives 0.03 / 8.3 / 13.5 dB at 50 / 88 / 100 MHz between 50 Ω. The new 7-pole filter (43p–220n–100p–270n–100p–220n–43p) was optimised for S11 ≤ −20 dB to 52 MHz. In circuit, overall S21 is **−36 / −45 / −49 dB at 88 / 100 / 108 MHz** **[sim]**. It costs ~0.6 dB at 40–50 MHz with Q = 40 inductors. |
| Bias-T test current | The bias-T is removed. The W6LVP draws ~70 mA at 12 V through its own inserter ([IRCA](https://www.hard-core-dx.com/archive/irca/msg103913.html)); the commercial AAA-1C powers its amplifier over CAT cable from its own controller ([fallows.ca](https://play.fallows.ca/wp/radio/shortwave-radio/commercial-lz1aq-antenna-amplifier)). C1 is a 63–100 V film cap, so DC on the coax is blocked either way. |
| Fifth-output penalty | **[sim]** 4 → 5 ports: gain −0.17 dB (1.73 → 1.56), isolation unchanged (32.4 → 32.5 dB at 30 MHz), IIP3 −1.1 dB (30.1 → 29.0 dBm at 7 MHz), NF unchanged. The earlier "0.5 dB / 2 dB" figures were guesses and were wrong. |
| Clamp distortion and surge | **Distortion [sim]:** IM3 and IM2 with and without D1–D4 differ by ≤ 0.2 dB and ≤ 1 dB at −10 and 0 dBm per tone; the clamps start conducting near +10 dBm. **What the protection can actually do:** GDT1 (90 V DC sparkover, 10 kA 8/20 µs rating) handles induced surges and static on the coax. Between its ~500 V impulse sparkover and conduction, C1 passes the surge edge into the 1N4148 clamps, which have only modest pulse current. This is static and induced-transient protection, not lightning protection. Use an external grounded arrestor and disconnect the antenna in storms. |

## 3. Sourcing (checked 2026-11-05)

| Part | Status | Notes / link |
| --- | --- | --- |
| 2N5160 (Rev A Q1P/Q3) | Discontinued (Central PDN01114, "stock only"); DigiKey die listings obsolete; brokers US$23–52 | [Central notice](https://www.mouser.com/datasheet/2/68/cm5160-596764.pdf), [Findchips](https://www.findchips.com/search/2N5160) |
| 2N5109 (Rev A Q1N) | Mouser lists Obsolete / End of Life; broker stock only | [Mouser](https://www.mouser.com/ProductDetail/Central-Semiconductor/2N5109?qs=Ypxpq5eNvNXHBK9WNBb9CQ%3D%3D) |
| 2N3866 (Rev A Q2) | DigiKey: Obsolete | [DigiKey](https://www.digikey.com/en/products/detail/central-semiconductor-corp/2N3866-PBFREE/4806874) |
| MPSH81 (TO-92 RF PNP) | Obsolete at DigiKey (onsemi and Central) | [DigiKey](https://www.digikey.de/en/products/detail/onsemi/MPSH81/1048853) |
| **2N3904 / 2N3906** (recommended) | Active, multiple makers, large stock; LTspice library models | [DigiKey 2N3906 (Diotec)](https://www.digikey.com/en/products/detail/diotec-semiconductor/2N3906/22191309) |
| 2N4401 / 2N4403 | Active (onsemi, Diotec 2N4403: 15k+ at DigiKey, US$0.17) | Tried as followers: too slow here (Cjc 11/15 pF in model) **[sim]** |
| ZTX951 (PNP) | Active (DigiKey 7,748 in stock, US$1.70), but fT 120 MHz | Rejected: too slow for a 50 MHz low-Z driver |
| Mini-Circuits TT1-6-X65+ | Active, through-hole 6-DIP, 1:1 with center taps, **4 kHz–300 MHz**, 30 mA DC max, ~US$11–16, low distributor stock | [DigiKey](https://www.digikey.ca/en/products/detail/mini-circuits/TT1-6-X65/21727905) — shows that prewound transformers can reach 10 kHz |
| AD811ANZ (current-feedback op amp, PDIP-8) | Active, 100 mA output, ~US$5.82 @1k | [ADI](https://www.analog.com/ad811/documentation?lsrc=doc) |
| BFR92P / BFT92 (SMT RF) | BFR92P not recommended for new designs (last-time-buy 2027-05); BFT92 obsolete | No SMT variant recommended |

## Approaches compared

1. **Keep Rev A with substitutes.** There is no stocked through-hole RF PNP left. The 2N4401/2N4403 drop-in was simulated: 3 dB droop at 50 MHz and 26 dB isolation at 30 MHz. Rejected.
2. **Revised discrete, all 2N3904/2N3906 (recommended).** The gain stage keeps the complementary common-emitter pair, now with collectors tied at one node X. The driver is a diamond buffer. Six TO-92 transistors, no trimmers, no transformers.
3. **NPN-only push-pull with Mini-Circuits TT1-6-X65+.** Feasible down to 10 kHz, but needs 2–3 transformers (~US$11–16 each, low stock) with a 30 mA DC limit per winding. No vendor SPICE model was used here, so it was not simulated. Kept as the fallback if 2N3906 matching proves poor.
4. **IC buffers (e.g., one AD811 per port).** Port isolation would be excellent. But the current-feedback input noise (20 pA/√Hz at the inverting input, times RF) needs ≳15 dB of front-end gain, which costs IIP3. Not simulated (no vendor model run); not pursued.

## 4. Meaningful performance comparison

### Gain options (same bias, all [sim])

| Build | RE1/RE2, RF, RL | Gain @1 MHz | NF @10 MHz | IIP3 @7 / 28 MHz | IIP2 6+7 / 0.6+1.0 MHz | max S11 |
| --- | --- | --- | --- | --- | --- | --- |
| **A (recommended)** | 56, 220, 220 | +1.73 dB | 8.3 dB | +30.1 / +27.4 dBm | +70.0 / +69.2 dBm | −23.3 dB |
| B | 56, 270, 220 | +3.16 dB | 7.8 dB | +28.3 / +25.9 dBm | +79.9 / +71.3 dBm | −20.8 dB |
| C | 47, 330, 220 | +5.52 dB | 6.9 dB | +27.3 / +23.6 dBm | +71.4 / +70.8 dBm | −20.4 dB |

**Why A.** Behind an active loop, the coupler's noise figure barely matters. If the loop amplifier delivers noise ≥ 20 dB above kTB, NF 8.3 dB costs 10·log(1 + 5.8/100) ≈ 0.25 dB of S/N, and NF 6.9 dB costs ≈ 0.17 dB **[est]**. The IIP3 difference, by contrast, is 2.8 dB at 7 MHz and 3.8 dB at 28 MHz. Lower gain also gives the RX888/RSPdx less overload risk. Build C only makes sense for a passive antenna on quiet upper-HF bands.

### Rev A vs Rev B, compared on input-referred figures

Rev A (+5.5 dB, TO-39 models) implied IIP3 ≈ +28.5 dBm at 10 MHz. Rev B A-build is +30.1 dBm at 7 MHz and +29.3 at 14 MHz: about **1 dB better input-referred IP3** at 3.8 dB less gain. That improvement is within model uncertainty, so it is not a claim of better linearity. The real gains are:

- isolation at 50 MHz: 29.4 dB vs ~27 dB
- output-to-input isolation: 52–107 dB vs 38–53 dB
- FM rejection: 36 dB vs 8 dB
- parts you can buy

### Convergence and tolerance

- **Two-tone convergence [sim]:** halving the timestep, reltol 1e-6 and a doubled record moved OIP3 by ≤ 0.2 dB and OIP2 by ≤ 1 dB. IM3 slope is 3:1 and IM2 slope is 2:1 from −20 to 0 dBm per tone. The numerical floor is about −115 dBm, so products were measured at −10 dBm per tone, 25+ dB above the floor.
- **Monte Carlo, 80 runs [sim]:**
  - Variations: transistor BF ×0.5–1.5 and IS ×0.6–1.7, independent per device; resistors 1 %; LPF L and C ±5 %; film caps ±10 %; inductor Q 40–80; 0, 27 and 50 °C.
  - Results: Q1 current 25–31 mA, output Iq 34–42 mA, output DC 4.6–5.1 V, gain at 1 MHz 1.63–1.91 dB, worst S11 −17 dB, isolation at 30 MHz 32.1–32.5 dB, IIP3 at 7 MHz +29.5 to +32.6 dBm (40 runs), IIP2 (6+7) +61 to +86 dBm.
- **Thermal [sim]:**
  - Ambient 0 → 50 °C changes output Iq by < 1 mA.
  - Outputs 30 °C hotter than their pre-drivers: Iq 39 → 50 mA, self-limiting, no runaway.
  - Outputs 30 °C hotter but the pair bonded together (pre-drivers +10 °C): 46 mA.
  - Glue each output face-to-face with its matching pre-driver: Q2 with Q2A, Q3 with Q3A.
- **Stability [sim]:** real part of impedance > 0 to 2 GHz:
  - input ≥ 0.83 Ω, with every port open, shorted, 100 pF or 1 µH
  - every port ≥ 2.9 Ω, with the other ports open, shorted, 100 pF or 1 µH

  So no passive load at any single port can cause oscillation. Cable-kick transients that completed all decayed; the rest stopped on solver errors (see README).
- **Noise breakdown at 10 MHz (A build) [sim]:** Q1P 17 %, source 15 %, Q1N 13 %, RF 13 %, RE1+RE2 20 %, port resistor 10 %. Getting below ~5 dB does **not** require transformers. It requires either more gain ahead of the port resistors (C gets to 6.9 dB) or replacing the resistive feedback and degeneration (RF, RE) with lossless feedback, for example transformer-coupled or a lower-noise first stage ahead of this one. Each option trades IIP3 or complexity, which the loop application does not need.

## 5. What needs hardware measurement [hw]

- **Absolute IP3/IP2:** two-tone with a hybrid combiner and a spectrum analyzer.
- **NF:** a noise source and an analyzer with noise-figure capability, or the Y-factor method with the TinySA and a calibrated noise source.
- **Gain flatness against real inductor Q.**
- **Thermal Iq drift.**
- **Low-frequency response down to 10 kHz:** the SV4401A VNA's lower limit is above 10 kHz, so use the signal generator and a scope or audio analyzer there.

A VNA alone cannot establish NF or intercept points.
