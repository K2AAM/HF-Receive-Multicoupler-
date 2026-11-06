#!/bin/sh
# render.sh board.kicad_pcb out.png [layers]
L=${3:-F.Cu,B.Cu,F.SilkS,F.CrtYd,Edge.Cuts}
kicad-cli pcb export svg --layers $L --page-size-mode 2 --exclude-drawing-sheet --black-and-white -o /tmp/r.svg $1 >/dev/null 2>&1 || kicad-cli pcb export svg --layers $L --page-size-mode 2 --exclude-drawing-sheet -o /tmp/r.svg $1 >/dev/null
python3 -c "import cairosvg; cairosvg.svg2png(url='/tmp/r.svg', write_to='$2', output_width=${4:-1700}, background_color='white')"
