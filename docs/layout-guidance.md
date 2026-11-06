# Layout guidance (Rev B, through-hole, Hammond 1590BB)

The schematic and calculations are settled. These were the guidelines for the KiCad layout. The prototype layout now exists: see [`pcb-prototype-A.md`](pcb-prototype-A.md) for how it follows them and where it deviates (J1 and J6 on different walls; no separate via fence between L1 and L3; GDT ground through the pours).

## Board and enclosure
- 2-layer, 1.6 mm FR-4. The bottom layer is an unbroken ground plane, and top-side ground pour is stitched to it with vias every ~5 mm along RF traces.
- The 1590BB inside is about 112 × 87 mm. Plan a ~100 × 75 mm board with corner mounting holes tied to ground.
- Put J1 (input) and J6 (DC) on one end wall, and J2–J5 on the opposite wall at ≥ 18 mm spacing, so the input and outputs are physically separated.
- Bond the board ground to the box at the connector wall: the BNC bulkhead nuts and lock washers do this. Add one more screw near J1 for the GDT ground path.

## Signal path
- Lay the signal path out in a straight line: J1 → GDT1/C1 → clamps → LPF → gain stage → diamond → star → ports. Don't fold it back on itself.
- Mount the GDT1 ground lead directly to the J1 shell pad with a short, wide trace to the chassis screw. Surge current must not flow through the amplifier ground.
- **LPF:** keep the inductors at right angles to each other, ≥ 8 mm apart, with each shunt capacitor's ground pad its own via into the plane. A small grounded fence (a row of vias plus a 5 mm copper strip) between L1 and L3 helps preserve rejection at 88–108 MHz.
- 50 Ω microstrip on 1.6 mm FR-4 is ~3 mm wide. Runs are short enough (< 30 mm) that exact impedance matters little below 50 MHz. Keep them as short as layout allows.
- **Star node OUT:** make it a small copper island. Fan the four C10–C13 / RS1–RS4 branches out symmetrically, with equal lengths within ~5 mm, so port-to-port gain and isolation match.
- Mount RS1–RS4 within 10 mm of their BNC pins.

## Transistors
- Put Q2+Q2A and Q3+Q3A side by side, flat faces together, glued.
- Keep the emitter resistors (RE3, RE4, RX1, RX2) and RC right at the transistor leads. Lead inductance in the output path directly raises the star impedance at 50 MHz.
- Q1N/Q1P: RE1/RE2 at the emitters. Keep RF and C8 tight between node X and the LPF output node; that loop sets the input match.

## Supply and decoupling
- **Each supply-side resistor** (RE2, R4, R3 midpoint cap, RPU, RC, Q3A collector): a 100 nF X7R to the plane within 5 mm.
- **Electrolytic polarity:** the R3-midpoint 10 µF goes + to the +9.8 V side. The R1-midpoint 10 µF goes + to the midpoint.
- Run the +9.8 V rail as a trace star from C22, not as a daisy chain.
- Keep U1, L4 and C20–C23 at the J6 end, away from the LPF.
- **Supply footprints:**
  - L4 (RLB0914-100KL): radial, 9.2 mm diameter keep-out, 5 mm pitch, 0.65 mm leads.
  - F1 (RXEF030): radial, 7.4 × 3 mm, 5.1 mm pitch.
  - RDAMP: 1/4 W axial.
- **D6 and D7:** mount them at U1's pins.
- **C23:** within 10 mm of U1 OUT.
- **Hot-plug inrush:** the J6 → F1 → D5 → C20 path carries up to ~11 A for under 1 ms when hot-plugged. Use a ≥ 1 mm trace.
- **LPF inductors:** footprints sized for the 78FR body (2.8 × 7.1 mm) with 10 mm lead pitch. Mark the selected values on the silkscreen.

## Assembly order
1. Power section, then test it (bring-up step 1).
2. Diamond buffer and port network.
3. Gain stage.
4. Input protection and LPF last.

This lets you bias-check the output stage before any RF signal can reach it.
