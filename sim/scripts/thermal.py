"""Bias versus ambient and device self-heating (output and pre-driver transistors warmer than ambient)."""
import gen, json
rows = []
for amb in (0, 27, 50):
    for dT_out, dT_pre in ((0, 0), (30, 30), (30, 10), (30, 0)):
        P = gen.params("A", TEMP=amb, TOUT=amb + dT_out, TPRE=amb + dT_pre)
        try:
            d = gen.op(P)
            rows.append(dict(ambient_C=amb, dT_output=dT_out, dT_predriver=dT_pre, Iq1n_mA=round(d['@q1n[ic]'] * 1e3, 1),
                             Iout_mA=round(d['@q2[ic]'] * 1e3, 1), Itot_mA=round(d['Irail_mA'], 1), Vout=round(d['v(out)'], 2), status="ok"))
        except gen.SimError as e:
            rows.append(dict(ambient_C=amb, dT_output=dT_out, dT_predriver=dT_pre, status="FAILED: " + str(e)[:200]))
        print(rows[-1], flush=True)
json.dump(rows, open("../results/thermal.json", "w"), indent=1)
