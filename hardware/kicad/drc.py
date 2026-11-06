"""Fill zones, save, and write a DRC report (KiCad 7 python)."""
import sys, pcbnew
f = sys.argv[1]
b = pcbnew.LoadBoard(f)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(f)
rep = sys.argv[2]
pcbnew.WriteDRCReport(b, rep, pcbnew.EDA_UNITS_MILLIMETRES, True)
txt = open(rep).read()
import re
for line in txt.splitlines():
    if line.startswith("**") or "Found" in line: print(line)
