#!/bin/bash
# Full board pipeline: placement -> DSN -> freerouting -> SES import + GND pours -> DRC
set -e
cd "$(dirname "$0")"
export KICAD7_FOOTPRINT_DIR=/usr/share/kicad/footprints KICAD7_SYMBOL_DIR=/usr/share/kicad/symbols
/usr/bin/python3 -c "import sys;sys.path.insert(0,'.');import make_pcb;make_pcb.build('hfmc_placed.kicad_pcb')"
/usr/bin/python3 -c "import pcbnew;b=pcbnew.LoadBoard('hfmc_placed.kicad_pcb');assert pcbnew.ExportSpecctraDSN(b,'hfmc.dsn')"
python3 fix_dsn.py hfmc.dsn hfmc_r.dsn
# pass 1: B.Cu declared a plane, so every signal is routed on F.Cu and the bottom ground plane stays whole
python3 route2.py planeB hfmc_r.dsn hfmc_p1.dsn
rm -f hfmc_p1.ses hfmc.ses
xvfb-run -a java -jar ${FREEROUTING:-freerouting.jar} -de hfmc_p1.dsn -do hfmc_p1.ses -mp 30 -inc gnd > fr.log 2>&1 || true
test -f hfmc_p1.ses
# pass 2: pass-1 wiring locked; B.Cu allowed only for what F.Cu could not complete (short pad-to-pad links)
/usr/bin/python3 route2.py lock hfmc_placed.kicad_pcb hfmc_p1.ses hfmc_p1.kicad_pcb hfmc_p2.dsn
python3 fix_dsn.py hfmc_p2.dsn hfmc_p2r.dsn
xvfb-run -a java -jar ${FREEROUTING:-freerouting.jar} -de hfmc_p2r.dsn -do hfmc.ses -mp 10 -inc gnd >> fr.log 2>&1 || true
test -f hfmc.ses
/usr/bin/python3 finish_pcb.py hfmc_p1.kicad_pcb hfmc.ses hfmc.kicad_pcb
python3 fix_pro.py hfmc.kicad_pro
/usr/bin/python3 stitch.py hfmc.kicad_pcb | tail -2
/usr/bin/python3 silk_fix.py hfmc.kicad_pcb | tail -2
/usr/bin/python3 drc.py hfmc.kicad_pcb drc.rpt
grep "^\[" drc.rpt | sed 's/(.*//' | sort | uniq -c
