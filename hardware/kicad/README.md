# KiCad project: prototype PCB, build A

The design description, the check results and the open items are in [`docs/pcb-prototype-A.md`](../../docs/pcb-prototype-A.md).

**Native files:**

| File | What it is |
| --- | --- |
| `hfmc.kicad_pro` | Project |
| `hfmc.kicad_sch` | Schematic |
| `hfmc.kicad_pcb` | PCB |
| `fp-lib-table` + `hfmc.pretty/` | Project footprint library (BNC, thermal-pair TO-92, GDT, KEMET C320, universal C32x, RXEF, pigtail and wire pads) |

The files were made with KiCad 7.0.11 and open in KiCad 7 or later.

**Outputs:**

| File | Contents |
| --- | --- |
| `hfmc_schematic.pdf` | Schematic |
| `hfmc_gerbers.zip` | Gerbers + Excellon drill, the upload for OSH Park |
| `fab/` | The same files loose, plus a drill map |
| `img/` | Board and enclosure-fit views |
| `BOM_prototype_A.csv` | Bill of materials |

## How the files are produced

`design.py` is the single source of truth: parts, values, MPNs, footprints, and pin-to-net maps whose net names are the `sim/scripts/gen.py` node names. Everything else is generated from it.

| Step | Command | Notes |
| --- | --- | --- |
| Footprints | `python3 mkfp.py` | Writes `hfmc.pretty/` |
| Schematic | `python3 make_sch.py` | Then `kicad-cli sch export netlist -o hfmc.net hfmc.kicad_sch` |
| Placement | `place.py` | Hand placement, merged with `place_core.json`, which comes from `autoplace_core.py` (core annealer: `/usr/bin/python3 autoplace_core.py <seed> place_core.json 200000 <T0>`) |
| Board, routing, pours, DRC | `./run_all.sh` | Needs KiCad's python (`/usr/bin/python3` with `pcbnew`), Java, `xvfb-run` and `freerouting.jar` (Freerouting 1.9.0 from GitHub releases; not committed) |
| Fab outputs, images, enclosure views | `./make_outputs.sh` | Then `python3 make_bom.py` for the BOM |

**What `run_all.sh` does:**

1. Builds the board.
2. Routes in two Freerouting passes:
   - Pass 1 declares B.Cu a plane, so signals go on F.Cu.
   - Pass 2 lets B.Cu finish only what is left.
3. Imports the routing (`ses_import.py`).
4. Adds GND pours on both layers and makes starved GND pads solid.
5. Adds stitching vias and places the silkscreen references.
6. Runs DRC.

**Freerouting is not deterministic.** Each run gives a different routing. The committed `hfmc.kicad_pcb` is the routing that all the checks below were run on. If you re-run `run_all.sh`, run the checks again.

## Checks

| Command | Checks | Report |
| --- | --- | --- |
| `/usr/bin/python3 check_conn.py` | Simulation netlist ↔ schematic ↔ PCB pads, plus pin functions | `check_conn.txt` |
| `python3 erc_check.py` | Scripted ERC on the exported netlist | `erc_check.txt` |
| `/usr/bin/python3 drc.py hfmc.kicad_pcb drc.rpt` | KiCad DRC | `drc.rpt` |
| `python3 check_place.py` | Courtyard overlaps | `check_place.txt` |
| `/usr/bin/python3 layout_report.py` | Branch lengths, bypass distances, LPF geometry | `layout_report.json` |
| `/usr/bin/python3 enclosure.py` | 1590BB fit; contains the ASSUMED enclosure numbers | `enclosure_report.txt` |
| `/usr/bin/python3 layout_parasitics.py` | Estimated trace capacitance added to the build-A simulation (needs ngspice) | `layout_parasitics.json` |

To run headless, set `KICAD7_FOOTPRINT_DIR=/usr/share/kicad/footprints`.
