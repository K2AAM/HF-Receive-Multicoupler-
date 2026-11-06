#!/bin/bash
# Run KiCad's own (native) ERC on hfmc.kicad_sch by driving eeschema under a virtual X display.
# KiCad 7.0 has no command-line ERC. Needs Xvfb, xdotool, imagemagick (import). Writes erc_native.rpt
# and erc_native.png (screenshot of the ERC dialog). Screen coordinates match KiCad 7.0.11 at 1600x1000.
set -e
cd "$(dirname "$0")"
OUT=$(pwd)
export DISPLAY=:97 KICAD7_SYMBOL_DIR=/usr/share/kicad/symbols KICAD7_FOOTPRINT_DIR=/usr/share/kicad/footprints
Xvfb :97 -screen 0 1600x1000x24 >/dev/null 2>&1 & XPID=$!
sleep 2
eeschema "$OUT/hfmc.kicad_sch" >/dev/null 2>&1 & EPID=$!
sleep 25
rm -f "$OUT/erc_native.rpt"
xdotool mousemove 206 12 click 1; sleep 1.5          # Inspect menu
xdotool mousemove 282 37 click 1; sleep 3            # Electrical Rules Checker
xdotool mousemove 923 540 click 1; sleep 8           # Run ERC
import -window root "$OUT/erc_native.png"
xdotool mousemove 923 491 click 1; sleep 2           # Save...
xdotool key ctrl+a; xdotool type --delay 30 "$OUT/erc_native.rpt"; xdotool key Return; sleep 2
kill $EPID $XPID 2>/dev/null || true
rm -f "$OUT/~hfmc.kicad_sch.lck"
cat "$OUT/erc_native.rpt"
