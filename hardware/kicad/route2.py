"""Two-pass routing support. pass1: make B.Cu a plane in the DSN (signals on F.Cu only).
   lock: import pass-1 SES into the placed board, lock it, export DSN for pass 2 (B.Cu allowed for leftovers only)."""
import sys
mode = sys.argv[1]
if mode == "planeB":
    s = open(sys.argv[2]).read()
    s2 = s.replace("(layer B.Cu\n      (type signal)", "(layer B.Cu\n      (type power)", 1)
    assert s2 != s; open(sys.argv[3], "w").write(s2)
elif mode == "lock":
    import pcbnew, ses_import
    b = pcbnew.LoadBoard(sys.argv[2]); ses_import.import_ses(b, sys.argv[3])
    for t in b.GetTracks(): t.SetLocked(True)
    b.Save(sys.argv[4]); assert pcbnew.ExportSpecctraDSN(b, sys.argv[5])
