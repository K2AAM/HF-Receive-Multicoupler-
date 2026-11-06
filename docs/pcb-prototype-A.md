# Prototype PCB, build A (first hardware prototype)

The prototype is a 2-layer through-hole board, 104 × 78 mm with notched corners, for a **Hammond 1590C** (it was first laid out for a 1590BB; section 5 has the change). The KiCad project, fabrication files and check scripts are in [`hardware/kicad/`](../hardware/kicad/).

**Status:** the board is laid out and checked in software. It has not been built or measured. Every performance figure on this page comes from ngspice, as in the rest of the repository. The layout-parasitic figures go one step further: they also depend on an *estimated* trace capacitance, so treat them as estimates on top of estimates.

| Item | File |
| --- | --- |
| Schematic (native) / PDF | `hardware/kicad/hfmc.kicad_sch`, `hardware/kicad/hfmc_schematic.pdf` |
| PCB (native) | `hardware/kicad/hfmc.kicad_pcb` (project `hfmc.kicad_pro`, footprints `hfmc.pretty/`) |
| Gerbers + Excellon drill (zip for OSH Park) | `hardware/kicad/hfmc_gerbers.zip` (loose files and drill map in `fab/`) |
| BOM with exact MPNs and footprints | `hardware/kicad/BOM_prototype_A.csv` |
| Board images | `hardware/kicad/img/pcb_front.png`, `pcb_back.png`, `pcb_both_layers.png`, `pcb_assembly.png` |
| Enclosure fit (top, side section, insertion path, two 3D block views) | `hardware/kicad/img/enclosure_*.png` |
| Machining and drilling drawing (1590C) | `hardware/kicad/drill_drawing_1590C.pdf` (pages also as `img/drill_*.png`) |
| Check outputs | `drc.rpt`, `erc_native.rpt` (+ `erc_native.png`), `erc_check.txt`, `check_conn.txt`, `check_place.txt`, `layout_report.json`, `layout_parasitics.json`, `enclosure_report.txt` |

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
- **J1, Amphenol RF 031-221-RFX** front-mount panel BNC on the left end wall, wired to the board with about 60 mm of RG-316. *Layout-driven:* rear-mount PCB BNCs on two opposite walls cannot both be inserted.
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
| ERC, native KiCad | **0 errors, 0 warnings** (`erc_native.rpt`). KiCad 7.0.11 eeschema's own *Inspect → Electrical Rules Checker* was run, driven by `erc_native.sh` under a virtual display, because KiCad 7 has no command-line ERC. The only test in the Ignored list is KiCad's default "SPICE model issue" (simulation is done in ngspice). |
| ERC, scripted cross-check | **PASS** (`erc_check.py`): no single-pin nets, no unconnected pins, no duplicate references, every footprint and MPN assigned, power input driven, no conflicting drivers. This is a separate script, not KiCad's ERC. |
| PCB DRC (KiCad 7 engine, `drc.rpt`) | **0 violations, 0 unconnected pads, 0 footprint errors.** Rules: 0.2 mm clearance and track, 0.4 mm copper-to-edge, 0.25 mm hole clearance. Tracks are 0.4 mm for signal and 0.8 mm for power. |
| Courtyard overlap (`check_place.py`) | **0 issues.** Intentional exception: none needed now. The thermal-pair footprints end at the flat face, so the glued pairs do not overlap. |
| Enclosure fit, Hammond 1590C (`enclosure.py`) | **OK** under the stated sources and assumptions, including the insertion path (section 5). |
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
| μ min (input–port 1, port 1–port 2; each other port swept over 25 passive loads) | 1.066 | 1.033 (both > 1 in this model) |

**What this means:**

- This is a capacitance estimate in a simulation. It is not proof of hardware stability or performance; the bring-up oscillation checks still decide that.
- The extra capacitance mostly loads the LPF end nodes and the input side.
- S11 is the figure that moves. In the same estimate, trimming C4 and C7 from 43 pF to 39 pF brings S11 back to −21.0 dB, with 0.77 dB gain at 50 MHz and 37.3 dB rejection at 88 MHz.
- This is **not** adopted in the BOM, because it rests on an estimate. Measure S11 first (bring-up section P5). Order a few 39 pF C0G parts in the same KEMET series if you want the option; the universal footprint takes either lead spacing.
- An earlier, looser placement produced 12 pF on X and dropped 50 MHz gain to 0.26 dB in the same estimate. That result is why the core was re-placed.

## 5. Enclosure fit: Hammond 1590C

The enclosure is now the **Hammond 1590C**. The model, report and drawings come from `hardware/kicad/enclosure.py`. Outputs:

- `enclosure_report.txt`
- `img/enclosure_top.png`, `img/enclosure_side.png`, `img/enclosure_insertion.png`, `img/enclosure_3d_a.png`, `img/enclosure_3d_b.png`
- `drill_drawing_1590C.pdf` (pages also saved as `img/drill_*.png`)

None of the earlier 1590BB interior assumptions are used.

### 5.1 Sources

Hammond supplied three files:

- **`1590C.pdf`** (drawing).
- **`1590C.dwg`.** LibreDWG read its geometry, and its 24 dimensions match the PDF.
- **`1590C.x_t`.** This is a Parasolid assembly, not STEP. No open-source reader here could load it, so the model uses the drawing and the DWG geometry.

Each number in `enclosure.py` is tagged with its source:

- **MFR:** printed by the manufacturer.
- **DWG:** measured from the DWG geometry.
- **CALC:** calculated from MFR or DWG values.
- **ASSUME:** must be measured.

| Item | Value | Source |
| --- | --- | --- |
| Outside, at the rim | 119.50 × 94.00 mm; body 52.50 high, lid 4.00, overall 56.50 | MFR |
| Floor thickness | 2.25 mm | MFR |
| Inside height, floor to underside of the lid | 52.25 mm (lid pocket 2.00 deep) | MFR |
| Inside floor to rim | 50.25 mm | CALC |
| Lid lip below the rim | 2.0 mm, 0.57 mm inside the wall, so it reaches down to z 48.25 | DWG |
| Inside at the rim | 115.14 × 89.64 mm | MFR |
| Inside near the floor (0.96 mm up, top of the R1.0 fillet) | 111.27 × 85.77 mm | MFR / DWG |
| Wall draft | 2.25° per side, both faces | CALC / DWG |
| Wall thickness | 2.18 mm (horizontal) | DWG |
| Cover screws | 4 × 6-32, centres 109.50 × 84.00 | MFR |
| Screw pillars | about (±54.82, ±42.07) with arcs R4.94 and R5.94; 103.64 × 78.14 between pillar faces at the rim | DWG / MFR |

The pillar check uses R5.94 at all heights, which is the conservative case.

### 5.2 Stack-up and clearances

All heights are above the **inside** floor. Add 2.25 mm for heights above the outside bottom face.

**Stack-up:**

| Item | Height |
| --- | --- |
| Spacers: Würth 970060354, M3 × 6 mm brass hex, female-female | 0–6.0 mm |
| PCB | 6.0–7.6 mm |
| BNC centreline | 16.2 mm |

**Clearance to the lid** (worst case is the lid lip at z 48.25; the lid pocket at z 52.25 is higher still):

| Part | Top | Below the lid lip | Below the lid pocket |
| --- | --- | --- | --- |
| C1 (tallest) | 26.7 | **21.5 mm** | 25.5 mm |
| J2–J5 housings | 24.0 | 24.2 mm | 28.2 mm |
| C22 | 20.6 | 27.6 mm | 31.6 mm |

**Under the board:** 6.0 mm from the PCB bottom to the floor. With leads clipped to 1.5 mm or less, that leaves at least 4.5 mm.

**Board in the box:**

- **Outline unchanged.** 104 × 78 mm with 7 × 7 corner notches.
- **Offset.** The board sits 1.42 mm toward the output wall, set by the BNC faces (5.3).
- **Wall clearances at board level:**
  - sides: 3.83 mm each
  - front edge: 2.67 mm
  - back edge: 5.50 mm
- **Pillar clearance to the notched edges:** 3.2 mm at the two output-wall corners and 4.9 mm at the two back corners. Without the notches the board corners would sit inside the pillars, so the notches stay.

**U1 (LM317T lying tab-down).** The tab is at VOUT, about 9.8 V.

- **Box clearances:** its far end is 4.7 mm from the grounded right wall, and its top (z 12.6) is 35.6 mm below the lid lip.
- **Under the tab:** there is no F.Cu copper under the body or tab (PCB keep-out). The tab rests on solder mask over bare laminate.
- **Fixing:** use a nylon M3 screw, or none. Never a metal screw.
- **Lid:** do not let anything conductive bridge the tab to the lid.

### 5.3 Output BNCs (J2–J5) on the drafted wall

**Why the as-cast wall won't do:**

- The wall leans out 2.25°. Across the 15.6 mm housing face that is a 0.61 mm wedge, so tightening a nut against the as-cast wall would tilt each connector and load the PCB and its solder joints.
- The old instruction to let the nuts pull the connectors across a gap is withdrawn.

**What to do instead:**

- **Inside:** mill one flat strip, 82 mm long × 22 mm high, centred on the BNC row and perpendicular to the floor. It cuts 0 at its top edge and 0.86 mm at its bottom edge. Separate Ø22 spot-faces would overlap at the 20 mm pitch.
- **Outside:** mill a parallel strip, 80 × 20 mm, cutting 0.79 mm at its top edge and 0 at its bottom.
- **Result:** the finished wall between the strips is **1.36 mm** (the connector allows 5 mm). Each housing face then seats fully on a vertical flat.
- **By hand:** a careful file and a square against the floor will do the same job.

**Board position:**

- With the faces on the inside strip, the board offset is +1.42 mm.
- The floor holes are Ø4.2 for M3, which gives ±0.6 mm of float. The BNC nuts locate the board; the spacer screws are tightened last.
- Nothing pulls the board across a gap.

**Insertion path.** A 2D search over board tilt and travel along the BNC axis (`enclosure.py` section 5; `img/enclosure_insertion.png`) modelled:

- the board, the attached spacers and every part's height envelope
- the drafted walls, floor and rim
- the 8.9 mm × Ø12.70 thread and the 12 mm × Ø11.5 bayonet (the bayonet diameter is assumed)

**Findings:**

- **The board cannot slide in level.** There is only 5.5 mm behind the back edge, and the thread is 8.9 mm long.
- **It has to go in at about 30°,** BNC end down and back end up above the rim (lid off). It is then levelled while the thread passes through the wall.
- **The opening size decides it:**
  - With Amphenol's recommended Ø12.83 D-hole, **no path exists**.
  - The threshold is a 14.4 mm vertical opening.
  - Removing tall parts does not help; the bare board plus spacers is the limit.
  - The same applies to the old 1590BB plan, which had the same flaw.
- **Opening chosen:** a vertical slot (obround) **12.9 wide × 15.5 high**, giving 1.1 mm margin over the threshold. The width keeps 0.8 mm strips plus the corners of each 14.5 × 15.6 housing face bearing on the inside strip (about 62 mm²). There is no D-flat; the soldered board stops the connectors turning.
- **Outside hardware:**
  - a DIN 433 M12 steel washer (ID 13, OD 20, t 2) bridges the slot under the supplied lock washer and nut
  - stack before the nut: 4.4 mm of the 8.9 mm thread
- **Ground path:** the BNC shells clamp to bare metal on both strips.

### 5.4 Panel jacks

These are wired, so the draft only tilts the jack and puts no load on the PCB. Fit them **after** the board, because the tilting board sweeps through their volume.

**J1, Amphenol 031-221-RFX** (input; front-mount, nut inside), on the left end wall:

| Item | Value |
| --- | --- |
| Position | y = −8.0 mm (toward the back wall); centre z 24.0 (outside z 26.25) |
| Hole | D-hole Ø11.1 with 10.3 across the flat (Amphenol panel type U, from the catalogue table); **confirm on the drawing** |
| Wall vs limit | 2.18 mm wall, 3.2 mm limit |
| Keep-out | 15 mm deep × ±7.4 mm: 7.0 mm above MH1's screw head, 16.9 mm below the lid lip |

**J6, Switchcraft 722A** (body inside, nut outside), on the back wall:

| Item | Value |
| --- | --- |
| Position | x = +36.0 mm (U1 end); centre z 26.0 (outside z 28.25) |
| Hole | D-hole Ø8.00 with 7.37 across the flat (Switchcraft 5/16-32 jack drawings); **confirm on the 722A sheet** |
| Wall vs limit | 2.18 mm wall, about 3.1 mm limit |
| Keep-out | 16 × ±8 × ±6 mm, lugs horizontal: 5.0 mm above C17, 16.2 mm below the lid lip |

### 5.5 Screws and ground

- **Top:** M3 × 5 pan head plus washer through each mounting hole into the spacer (2.9 mm of thread engaged).
- **Bottom:** M3 × 5 pan head plus washer from below through the Ø4.2 floor hole (2.25 mm engaged). The two screws together take 5.15 mm of the 6 mm spacer thread.
- **Access:** all screws are reachable. The top ones go in before the board goes into the box; the bottom ones from outside.
- **Ground bond:**
  - the spacer end faces bear on bare floor metal
  - the BNC shells bear on the milled strips
  - the J1 shell bonds through its own nut
  - MH1 is 6.7 mm from the GDT ground pad
- **1590CBK (textured black):** remove the coating at the spacer seats, the BNC strips and the J1 nut.

### 5.6 Drilling and machining (`drill_drawing_1590C.pdf`)

**Datums:**

- X/Y: the centre of the four 6-32 cover-screw holes. Hammond advises against using the moulded part-number text as a reference.
- Z_out: height above the **outside** bottom face. The inside floor is at Z_out 2.25.
- Drill and mill wall features with the axis parallel to the floor (2.25° off the wall normal).

| Feature | Wall | Position (box frame) | Height Z_out | Size |
| --- | --- | --- | --- | --- |
| J2–J5 | front (output) | x = −30, −10, +10, +30 | 18.45 | slot 12.9 × 15.5, plus inside strip 82 × 22 and outside strip 80 × 20 |
| J1 | left end | y = −8.0 (toward the back wall; seen from outside it is right of centre) | 26.25 | D 11.1 / 10.3 |
| J6 | back | x = +36.0 (toward U1; seen from outside it is right of centre) | 28.25 | D 8.00 / 7.37 |
| MH1 | floor | (−38.50, −10.58) | — | Ø4.2 |
| MH2 | floor | (−46.50, +26.42) | — | Ø4.2 |
| MH3 | floor | (+46.50, +26.42) | — | Ø4.2 |
| MH4 | floor | (+47.50, −26.38) | — | Ø4.2 |
| MH5 | floor | (−34.00, +11.42) | — | Ø4.2 |

**Making the floor holes:** the floor coordinates are given seen from inside. The surest method is to seat the board on the BNC strips first (spacers fitted, nuts snug), then spot the floor through the spacers. Bottom-up marking flips the sign of x.

### 5.7 Still to measure on a real 1590C before cutting

1. Floor thickness, inside depth, and the lid-lip depth and position.
2. Inside widths at a few heights (this confirms the 2.25° draft).
3. Pillar radius near the floor.
4. Wall thickness at the BNC row, to confirm 1.36 mm remains after the strips are milled.
5. On the BNCs:
   - the 031-5431-10RFX housing-face size and flatness
   - the bayonet diameter over the lugs (the 11.5 mm assumed in the insertion check)
   - the thread length
6. Panel cut-outs and behind-panel lengths of the 031-221-RFX and the 722A.
7. Seated heights marked ASSUME in `enclosure.py` (TO-92 about 7 mm, Keystone 5000 about 8 mm).
8. A dry run of the tilted insertion with the bare PCB and spacers before any parts are soldered.

## 6. Layout-driven circuit and BOM changes

These change the hardware relative to the simulated netlist. None of them alters the signal-path topology.

1. **J1 is now a front-mount panel BNC (031-221-RFX)** on an RG-316 pigtail, not a PCB jack. A ~60 mm 50 Ω coax adds delay, not mismatch, below 50 MHz. It is not in the simulation.
2. **J6 is a panel jack (722A),** wired.
3. **Four more 100 nF local bypass capacitors** on VCC (C19, C24, C25, C26), plus C16/C17/C18 placed at their devices. The AC simulation uses an ideal rail, so these are not modelled. They can only help.
4. **C1 is KEMET R60, 100 V** (same 4.7 µF). C2/C3/C8/C9/C10–C13 are KEMET R82 (same values; 50 V instead of 63 V, still well above the 9.8 V rail).
5. **100 nF capacitors use a corrected C320 footprint** (5.08 × 3.18 mm).
6. **U1 lies flat** over a copper keep-out (tab = VOUT).
7. **Board ground is bonded to the box** at all five spacers (Würth 970060354, M3 × 6 mm brass).
8. **Enclosure is the Hammond 1590C**, with milled BNC strips, 12.9 × 15.5 slots and outside M12 washers (section 5). Mechanical only; no copper change.
9. **Optional C4/C7 = 39 pF** if S11 measures poor (section 4). Not fitted by default; C4/C7 stay 43 pF.

## 7. Remaining blockers before ordering

1. Measure a real 1590C and the three connector types (section 5.7). Dry-run the tilted insertion with the bare PCB and spacers.
2. Open the project in KiCad 7 or later:
   - Look over the autorouted tracks. The router is not deterministic; the committed board is the one that was checked.
   - Check the silkscreen. (Native ERC has been run: 0 errors, 0 warnings.)
3. Load `hfmc_gerbers.zip` into a Gerber viewer or the OSH Park preview. Check the drill file (plated and non-plated holes are in one file; the U1 tab hole is non-plated).
   - The 1590C change did not touch copper. The only PCB edit was the spacer MPN text in five mounting-hole footprints.
   - Gerbers and drill regenerated from the current board match the committed ZIP line for line, apart from creation timestamps.

Nothing in the signal-path design is blocking.
