#!/bin/bash
# Fabrication + documentation outputs from hfmc.kicad_pcb / hfmc.kicad_sch (run after run_all.sh and the checks)
set -e
cd "$(dirname "$0")"
rm -rf fab img; mkdir -p fab img
kicad-cli sch export pdf -o hfmc_schematic.pdf hfmc.kicad_sch >/dev/null
kicad-cli pcb export gerbers -o fab/ -l F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts --subtract-soldermask hfmc.kicad_pcb >/dev/null
kicad-cli pcb export drill -o fab/ --format excellon --excellon-units mm --generate-map --map-format pdf hfmc.kicad_pcb >/dev/null
(cd fab && rm -f ../hfmc_gerbers.zip && zip -q ../hfmc_gerbers.zip *.g* *.drl)
for spec in "front:F.Cu,F.SilkS,F.Mask,Edge.Cuts" "back:B.Cu,B.SilkS,Edge.Cuts" "assembly:F.Fab,F.CrtYd,Edge.Cuts,F.SilkS" "both_layers:F.Cu,B.Cu,F.SilkS,Edge.Cuts"; do
  n=${spec%%:*}; L=${spec#*:}; m=""; [ $n = back ] && m=--mirror
  kicad-cli pcb export svg --layers $L --page-size-mode 2 --exclude-drawing-sheet $m -o /tmp/$n.svg hfmc.kicad_pcb >/dev/null
  python3 -c "
import cairosvg; from PIL import Image, ImageOps
cairosvg.svg2png(url='/tmp/$n.svg', write_to='img/pcb_$n.png', output_width=2400, background_color='white')
im=Image.open('img/pcb_$n.png').convert('RGB'); bb=ImageOps.invert(im).getbbox(); im.crop((max(bb[0]-10,0),max(bb[1]-10,0),bb[2]+10,bb[3]+10)).save('img/pcb_$n.png')"
done
/usr/bin/python3 enclosure.py > /dev/null
mv enclosure_*.png img/
ls fab img
