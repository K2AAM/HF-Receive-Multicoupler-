# Prototype PCB, build A (first hardware prototype)

The prototype is a 2-layer through-hole board, 104 × 78 mm with notched corners, for a Hammond 1590BB. The KiCad project, fabrication files and check scripts are in [`hardware/kicad/`](../hardware/kicad/).

**Status:** the board is laid out and checked in software. It has not been built or measured. Every performance figure on this page comes from ngspice, as in the rest of the repository. The layout-parasitic figures go one step further: they also depend on an *estimated* trace capacitance, so treat them as estimates on top of estimates.

| Item | File |
| --- | --- |
| Schematic (native) / PDF | `hardware/kicad/hfmc.kicad_sch`, `hardware/kicad/hfmc_schematic.pdf` |
| PCB (native) | `hardware/kicad/hfmc.kicad_pcb` (project `hfmc.kicad_pro`, footprints `hfmc.pretty/`) |
| Gerbers + Excellon drill (zip for OSH Park) | `hardware/kicad/hfmc_gerbers.zip` (loose files and drill map in `fab/`) |
| BOM with exact MPNs and footprints | `hardware/kicad/BOM_prototype_A.csv` |
| Board images | `hardware/kicad/img/pcb_front.png`, `pcb_back.png`, `pcb_both_layers.png`, `pcb_assembly.png` |
| Enclosure fit (top, side section, two 3D block views) | `hardware/kicad/img/enclosure_*.png` |
| Check outputs | `drc.rpt`, `erc_check.txt`, `check_conn.txt`, `check_place.txt`, `layout_report.json`, `layout_parasitics.json`, `enclosure_report.txt` |

## 1. What is on the board

**Signal path (unchanged from the simulation):**

- J1 → GDT1 / C1 → RBL and the four 1N4148 clamps → 7-pole LPF (C4 L1 C5 L2 C6 L3 C7) → complementary gain stage.
- Gain stage: Q1N/Q1P, RE1 = RE2 = 56 Ω, RF = 220 Ω, RL = 220 Ω via CLX.
- Then the diamond buffer → OUT → four C + 51 Ω branches → J2–J5.
- Supply: J6 → F1 → D5 → LM317 (with D6/D7, R10/R11, C21, C23) → L4 + RDAMP → C22 → VCC.

**KiCad reference numbers.** KiCad needs numeric references, so the simulation and document names were renumbered. Each part keeps its old name in a `DocRef` field (visible on the schematic) and its simulation element in a `SimName` field. The renumbering:

| Group | Doc / sim name → KiCad ref |
| --- | --- |
| Transistors | Q1N → Q1, Q1P → Q2, Q2A → Q3, Q3A → Q4, Q2 → Q5, Q3 → Q6 |
| Input, gain stage, bias | RBL → R1, RE1 → R2, RE2 → R3, RF → R4, RL → R5, R1A → R6, R1B → R7, R2 → R8, R3A → R9, R3B → R10, R4 → R11 |
| Diamond buffer | RPU → R12, RPD → R13, RX1 → R14, RX2 → R15, RC → R16, RE3 → R17, RE4 → R18 |
| Ports | RS1–RS4 → R19–R22 |
| Supply | R10 → R23, R11 → R24, RDAMP → R25 |

Capacitors, inductors and diodes keep their names. Net names are the simulation node names.

**Test points (Keystone 5000/5001):**

| TP | Net | Use |
| --- | --- | --- |
| TP1 | VCC | Rail |
| TP2 | X | Gain-stage collector node |
| TP3 | OUT | Common output node |
| TP4 | EF | Top of RE3: I(Q5) = (V_TP4 − V_TP3) / 3.3 Ω |
| TP5 | EG | Bottom of RE4: I(Q6) = (V_TP3 − V_TP5) / 3.3 Ω |
| TP6 | EN | Top of RE1: I(Q1) = V_TP6 / 56 Ω |
| TP7, TP8 | GND | Ground |

All resistors use the same 7.62 mm-pitch axial footprint, so the build B/C values (RE1/RE2 56/47, RF 270/330) drop straight in.

## 2. Part selections and footprints

The footprints were drawn or chosen from manufacturer dimensions. The full list is in `BOM_prototype_A.csv`. These are the ones that needed care.

**Connectors and protection:**

- **J2–J5, Amphenol RF 031-5431-10RFX** (R/A rear-mount PCB bulkhead BNC). The custom footprint follows Amphenol drawing rev E:
  - fork posts Ø2.0 mm at ±5.08 mm
  - centre and post holes Ø0.89 mm, 2.54 mm apart
  - rows 5.08 mm apart
  - front face 7.37 mm ahead of the fork row
  - centreline 8.6 mm above the PCB
- **J1, Amphenol RF 031-221-RFX** front-mount panel BNC on the left short wall, wired to the board with about 60 mm of RG-316. *Layout-driven:* rear-mount PCB BNCs on two opposite walls cannot both be inserted.
- **J6, Switchcraft 722A** panel DC jack (2.0 mm pin; mates with common 2.1 mm plugs) on the back wall, wired to the board.
- **GDT1, Bourns 2027-09-BLF.** Axial, 8 mm × 6 mm body, laid flat on a 12.7 mm pitch.
- **F1, Littelfuse RXEF030.** 7.4 × 3.0 mm, seated height 12.7 mm, 5.1 mm pitch.
- **U1, LM317T,** mounted flat (TO-220 tab down, KiCad `TO-220-3_Horizontal_TabDown`). The tab is at VOUT, so a copper keep-out on F.Cu (no pour, tracks or vias) sits under the body and tab. The tab hole is non-plated: use a nylon screw or none. It dissipates about 0.3 W, so no heatsink is needed.
- **Q1–Q6, onsemi 2N3904BU / 2N3906BU,** pinout E-B-C (pad 1 = E). The four diamond devices use a custom footprint whose courtyard ends at the flat face. Each pair (Q3+Q5, Q4+Q6) sits flat face to flat face, 0.25 mm apart, ready for thermal epoxy.

**Film capacitors (sizes checked):**

- **C1:** KEMET R60EI4470AA30J, 4.7 µF 100 V, 18 × 11 × 19.1 mm, 15 mm pitch. It replaces the WIMA MKS4 in the old BOM, which is 26.5 × 10.5 × 19 mm on a 22.5 mm pitch and too big.
- **C10–C13:** KEMET R82CC4470DQ30K, 4.7 µF 50 V, 7.2 × 7.2 × 13 mm, 5 mm pitch.
- **C2, C3, C8, C9:** KEMET R82CC4220DQ70J, 2.2 µF 50 V, 7.2 × 6 × 11 mm. Same footprint as C10–C13.

**Ceramic capacitors (KEMET Goldmax):**

- **C5, C6 (C315):** 3.81 × 2.54 mm, seated height 4.66 mm.
- **C4, C7 (C325):** 5.08 × 3.18 mm, seated height 7.62 mm. The universal footprint has 2.54 mm and 5.08 mm lead holes, because distributor data disagree on the C325 lead spacing.
- **100 nF (C320):** 5.08 × 3.18 mm. *Corrected during layout:* the first footprint was the 3.8 × 2.6 mm disc and was too small.

**Other passives:**

- **Electrolytics, Panasonic:** ECA-1EM100 (5 × 11 mm), EEU-FR1E221 and EEU-FR1C471 (8 × 11.5 mm).
- **L4, Bourns RLB0914-100KL:** 8.7 mm diameter × 13 mm, 5 mm pitch.
- **L1–L3:** Bourns 78FR axial, VNA-selected as before.

**Hole sizes against lead diameters:** every component hole is at least 0.2 mm larger than the maximum lead diameter, except the BNC holes, which follow Amphenol's recommended sizes. For example, the 0.75 mm holes for TO-92, 0.8 mm for 0.5–0.6 mm leads, 1.2 mm for the C1 0.8 mm leads and 1.1 mm for the GDT 0.8 mm leads.

## 3. Layout

**Ground:**

- **B.Cu is the ground plane.** Signals were routed on F.Cu only (the router was told B.Cu is a plane). Three short pad-to-pad links went on B.Cu where F.Cu could not finish: X 3.7 mm, RMP 6.2 mm and D1 7.3 mm, 17 mm in total.
- **F.Cu carries a second ground pour.** 137 stitching vias on a 4 mm grid tie it to the plane, keeping clear of every courtyard.
- **Mounting holes M1–M5 are plated and on GND.** Brass M3 spacers bond the board to the box at each one.
- **MH1 is 6.7 mm from the GDT ground pad.** That is the chassis discharge path. The coax braid at J1 is the other path, back to the panel connector.

**Placement:**

- **Input and outputs are separated.** Input, protection and LPF sit along the back wall on the left. The four outputs are on the front wall, and the supply is on the right.
- **Gain stage and diamond buffer were placed by an annealer.** `autoplace_core.py` placed them by weighted wire length, with the heaviest weights on X, OUT, the base nodes and the feedback loop. It also pulls each local bypass capacitor to its device pin. The placement passes the courtyard check.
- **Local bypass distances (pad to device pad):**
  - C16 to Q5 collector: 4.8 mm
  - C26 to Q4 collector: 5.0 mm
  - C24 to RE2 / R4: 3.2 / 4.4 mm
  - C25 to RPU: 3.0 mm
  - C19 to RC: 3.0 mm
  - C21 to U1 ADJ: 4.2 mm
  - C23 to U1 OUT: 6.5 mm
- **Port branches** (C1x → RSk → BNC) are pre-routed straight and mirror-symmetric:
  - C → RS: 4.9 / 6.6 / 6.6 / 4.9 mm
  - RS → BNC pin: 4.9 / 4.6 / 4.6 / 4.9 mm
- **LPF inductors:**
  - L1 ⟂ L2 and L2 ⟂ L3.
  - L1 and L3 are parallel but 21 mm apart.
  - Centre spacings are 9.6, 12.8 and 21.2 mm.

**Routed track lengths:**

- X 33 mm
- OUT 52 mm
- N4 41 mm
- BN 33 mm
- BP 13 mm
- FB 6 mm

**Deviations from `docs/layout-guidance.md`:**

1. J1 and J6 are on different walls (left short wall and back wall), not one end wall. The panel jacks need clear volume above low parts (section 5). J1 is still the farthest connector from the outputs.
2. No dedicated via fence between L1 and L3. The stitching grid runs between them, and L1/L3 are 21 mm apart.
3. GDT ground goes through the pours to MH1 and to the J1 braid pads (6.7 mm and 17.6 mm), not through a single dedicated strap.

## 4. Verification done

| Check | Result |
| --- | --- |
| Schematic vs simulation netlist (`check_conn.py`) | **PASS.** 64 simulation elements mapped by `SimName` and checked terminal by terminal against `sim/scripts/gen.py` (build A). Transistors are checked as C-B-E, diodes as A-K, polar capacitors by +. The node mapping is one-to-one (39 nodes). U1 is checked by IN/OUT/ADJ role. All 174 schematic pins match `design.py`, and all 225 PCB pads match the schematic netlist. Schematic pin functions are confirmed (Q 1/2/3 = E/B/C, D 1/2 = K/A, LM317 1/2/3 = ADJ/VO/VI). |
| ERC | **Scripted equivalent PASS** (`erc_check.py`): no single-pin nets, no unconnected pins, no duplicate references, every footprint and MPN assigned, power input driven, no conflicting drivers. **KiCad's own ERC was not run.** KiCad 7.0 has no command-line ERC, so run *Inspect → ERC* once in eeschema. |
| PCB DRC (KiCad 7 engine, `drc.rpt`) | **0 violations, 0 unconnected pads, 0 footprint errors.** Rules: 0.2 mm clearance and track, 0.4 mm copper-to-edge, 0.25 mm hole clearance. Tracks are 0.4 mm for signal and 0.8 mm for power. |
| Courtyard overlap (`check_place.py`) | **0 issues.** Intentional exception: none needed now. The thermal-pair footprints end at the flat face, so the glued pairs do not overlap. |
| Enclosure fit (`enclosure.py`) | **Heights OK, wall connectors OK** under the stated assumptions (section 5). |
| Layout parasitics in simulation (`layout_parasitics.py`) | See below. |

**Decisions made during these checks:**

- The netclass clearance was set to 0.2 mm. The TO-92 pads at 1.27 mm pitch leave 0.22 mm, which is within OSH Park's 6 mil rule.
- GND pads that could only get one thermal spoke on F.Cu were made solid. The list is found by DRC and printed by `finish_pcb.py`; for this board it is C14, C23 and Q6 pin 3.

**Layout-parasitic estimate (simulated, not measured).**

- **Method:** each signal net's routed copper and pads were turned into a shunt capacitance: 0.10 pF/mm of track plus 0.30 pF per through-hole pad. This is a hand estimate for grounded coplanar track on 1.6 mm FR-4, not a field solve. It was added to the build-A model, on top of the package and wiring parasitics already in it.
- **Largest additions:** OUT 7.3 pF, X 6.0 pF, E2A 5.8 pF, N4 5.6 pF, BN 4.5 pF, N1 4.1 pF.

| Simulated | Model (PAR = 1) | Model + layout C estimate |
| --- | --- | --- |
| Gain 1 / 50 MHz | 1.72 / 0.84 dB | 1.72 / 0.78 dB |
| Flatness 10 kHz–50 MHz | 0.88 dB | 0.94 dB |
| Worst S11 / S22, 10 kHz–50 MHz | −23.3 / −23.3 dB | **−17.9** / −24.0 dB |
| Port isolation at 50 MHz | 29.4 dB | 29.0 dB |
| Rejection at 88 MHz | 34.8 dB | 38.4 dB |
| μ min (input–port 1, port 1–port 2; each other port swept over 25 passive loads) | 1.066 | 1.033 (both > 1) |

**What this means:**

- The extra capacitance mostly loads the LPF end nodes and the input side.
- S11 is the figure that moves. In the same estimate, trimming C4 and C7 from 43 pF to 39 pF brings S11 back to −21.0 dB, with 0.77 dB gain at 50 MHz and 37.3 dB rejection at 88 MHz.
- This is **not** adopted in the BOM, because it rests on an estimate. Measure S11 first (bring-up section P5). Order a few 39 pF C0G parts in the same KEMET series if you want the option; the universal footprint takes either lead spacing.
- An earlier, looser placement produced 12 pF on X and dropped 50 MHz gain to 0.26 dB in the same estimate. That result is why the core was re-placed.

## 5. Enclosure fit

**Data sources:**

- **Hammond (distributor listings):** external 119.5 × 94 mm; body depth 30 mm (1.18 in) without the lid; lid 4 mm (0.16 in).
- **Interpreted from drawings, not verified (marked ASSUMED in `enclosure.py`):** inside 112.66 × 87.16 mm at the rim and about 110.36 × 84.86 mm at the floor (draft); floor 2.5 mm; four lid-screw bosses at 103.5 × 78 mm centres, radius 4 mm.
- **Allowance:** 1.5 mm for any lid lip or gasket.

**Stack-up:**

- Floor (inside) = 0.
- M3 × 4 mm brass spacers.
- PCB from 4.0 to 5.6 mm.
- Usable height to the lid, as assumed: 26.0 mm.
- The spacer height was chosen so the 19.1 mm C1 clears the lid.

**Margins against the usable height:**

| Part | Top above inside floor | Margin |
| --- | --- | --- |
| C1 | 24.7 mm | 1.3 mm (tallest part) |
| J2–J5 housings | 22.0 mm | 4.0 mm |
| C22 | 18.6 mm | 7.4 mm |

**Side and boss clearances:**

- Board to wall at PCB height: 3.4 mm (x) and 3.7 mm (y).
- Board-edge notches to bosses: 2.75 mm each.

**Panel holes** (box coordinates: origin at the box centre; +y toward the output wall; heights above the *inside* floor, so add the measured floor thickness for the outside):

| Connector | Wall | Position | Centre height | Hole |
| --- | --- | --- | --- | --- |
| J2, J3, J4, J5 | front (long) | x = −30, −10, +10, +30 mm | 14.2 mm | per the Amphenol 31-5431-10RFX panel cut-out (1/2-28 thread), **verify on the drawing** |
| J1 031-221-RFX | left (short) | y = −8 mm (8 mm toward the back wall) | 16.5 mm | per the Amphenol panel cut-out (3/8-32 thread; max panel 3.2 mm), **verify** |
| J6 722A | back (long) | x = +36 mm (on the U1 side) | 19.5 mm; turn the lugs horizontal | per the Switchcraft drawing, **verify** |

**Clearance at each panel jack** (each keep-out is modelled as a box):

- **J1:** 15 mm deep × 14.8 mm square. It clears MH1's screw head by 1.1 mm and the usable top by 2.1 mm.
- **J6:** 16 mm deep, ±8 mm wide, ±5 mm high. It clears C17 by 1.5 mm and the top by 1.5 mm.

**Floor holes for the spacers (M3):**

| Hole | Position (mm) |
| --- | --- |
| MH1 | (−38.5, −12.0) |
| MH2 | (−46.5, +25.0) |
| MH3 | (+46.5, +25.0) |
| MH4 | (+47.5, −27.8) |
| MH5 | (−34.0, +10.0) |

Drill the floor from these coordinates, or better, from the bare PCB used as a template.

**Assembly access:**

- The four PCB BNCs go in through the front-wall holes with the board tilted, then the board drops onto the spacers.
- Tighten the BNC nuts **before** the spacer screws. The model puts the BNC front faces 0.5 mm short of the drafted wall; the nut pulls them to the wall.

**Unverified mechanical assumptions (check on the real box before drilling):**

- Floor thickness, inside depth, and any lid lip.
- Boss positions and diameter, and the draft angle. These set the 2.75 mm boss clearance and the 0.5 mm BNC face gap.
- The panel cut-outs for all three connector types.
- The rear depth of the 031-221-RFX (taken as 15 mm) and the 722A (taken as 16 mm with lugs).
- The seated heights marked "estimate" in `enclosure.py`: TO-92 about 7 mm and Keystone 5000 about 8 mm.
- No STEP models were used. The 3D views are a block model (courtyard × seated height).

## 6. Layout-driven circuit and BOM changes

These change the hardware relative to the simulated netlist. None of them alters the signal-path topology.

1. **J1 is now a front-mount panel BNC (031-221-RFX)** on an RG-316 pigtail, not a PCB jack. A ~60 mm 50 Ω coax adds delay, not mismatch, below 50 MHz. It is not in the simulation.
2. **J6 is a panel jack (722A),** wired.
3. **Four more 100 nF local bypass capacitors** on VCC (C19, C24, C25, C26), plus C16/C17/C18 placed at their devices. The AC simulation uses an ideal rail, so these are not modelled. They can only help.
4. **C1 is KEMET R60, 100 V** (same 4.7 µF). C2/C3/C8/C9/C10–C13 are KEMET R82 (same values; 50 V instead of 63 V, still well above the 9.8 V rail).
5. **100 nF capacitors use a corrected C320 footprint** (5.08 × 3.18 mm).
6. **U1 lies flat** over a copper keep-out (tab = VOUT).
7. **Board ground is bonded to the box** at all five spacers (brass, 4 mm).
8. **Optional C4/C7 = 39 pF** if S11 measures poor (section 4). Not fitted by default.

## 7. Remaining blockers before ordering

1. Measure the actual 1590BB (section 5 list). Confirm the 4 mm spacer height and the panel-hole heights.
2. Open the project in KiCad 7 or later:
   - Run eeschema ERC.
   - Look over the autorouted tracks. The router is not deterministic, and the committed board is the one that was checked; re-running `run_all.sh` produces a different routing that must be re-checked.
   - Check the silkscreen.
3. Load `hfmc_gerbers.zip` into a Gerber viewer or the OSH Park preview. Check the drill file (plated and non-plated holes are in one file; the U1 tab hole is non-plated).
4. Confirm the panel cut-out dimensions on the three connector drawings.
5. Choose the M3 × 4 mm brass spacer part (`BOM_prototype_A.csv` gives the requirement, not an MPN).

Nothing in the signal-path design is blocking.
