"""Power-supply verification, Rev B: J6 -> F1 PTC -> D5 -> C20 -> U1 LM317 (+D6, D7, C21, C23) -> L4 -> RDAMP -> C22 -> rail.
The LM317 is behavioural (see gen.supply_block): it has ideal line rejection, a fixed dropout
VDROP and a current limit. Conclusions that depend on those assumptions are labelled."""
import gen, numpy as np, json
R = {}
P = gen.params("A", SUPPLY="full")
loads = "RGIN IN 0 50\n" + gen.portloads(P)

def tran(P, S, tstop, step, probes, extra=""):
    an = f"tran {step} {tstop} 0 {step}\nlinearize {' '.join(probes)}\nwrdata s.txt {' '.join(probes)}"
    log, d = gen.run(gen.netlist(P, an, loads + "\n" + extra, extra=".options method=gear reltol=1e-4", supply_over=S),
                     {"s.txt": dict(xmin=0, xmax=tstop, min_rows=200, ncols=2 * len(probes))})
    a = d["s.txt"]; return a[:, 0], [a[:, 2 * i + 1] for i in range(len(probes))]

# 1. start-up: slow (1 ms) and hot-plug (1 us) ramps
for name, ramp in [("startup_1ms_ramp", 1e-3), ("hotplug_1us_ramp", 1e-6)]:
    t, (vcc, uout, iin) = tran(P, dict(RAMP=ramp), 400e-3, 2e-6, ["v(vcc)", "v(uout)", "i(vin)"])
    fin = vcc[-1]; assert abs(vcc[-1]-vcc[np.argmin(abs(t-0.3))])<2e-3, 'rail not settled by 0.3 s'; i99 = np.argmax(vcc > 0.99 * fin)
    R[name] = dict(final_rail_V=round(float(fin), 3), overshoot_mV=round(float((vcc.max() - fin) * 1e3), 1),
                   t_to_99pct_ms=round(float(t[i99] * 1e3), 2), peak_input_current_A=round(float(-iin.min()), 3),
                   final_input_current_mA=round(float(-iin[-1] * 1e3), 1))
    print(name, R[name], flush=True)

# 2. input-voltage sweep (DC)
an = "dc VIN 8 16 0.1\nwrdata d.txt v(vcc) v(uin) v(uout) i(vin)"
log, d = gen.run(gen.netlist(P, an, loads), {"d.txt": dict(xmin=8, xmax=16, min_rows=70, ncols=8)})
a = d["d.txt"]; vin = a[:, 0]; vcc = a[:, 1]; uin = a[:, 3]; uout = a[:, 5]
nom = vcc[-1]; head = uin - uout
def first(cond): i = np.argmax(cond); return round(float(vin[i]), 2) if cond.any() else None
R["input_sweep"] = dict(rail_at_13p8V=round(float(np.interp(13.8, vin, vcc)), 3),
    U1_headroom_at_13p8V=round(float(np.interp(13.8, vin, head)), 2),
    U1_headroom_at_12p0V=round(float(np.interp(12.0, vin, head)), 2),
    VIN_for_3V_headroom=first(head >= 3.0),
    VIN_where_rail_within_10mV_of_final_model=first(vcc >= nom - 0.01),
    note="Regulation below the 3 V datasheet test condition relies on typical dropout (model VDROP 1.7 V at ~0.1 A).")
print(R["input_sweep"], flush=True)

# 3. rail impedance at VCC node, full supply vs ideal-source+no-filter reference
def zrail(S):
    an = "ac dec 20 10 100e6\nwrdata z.txt v(vcc)"
    log, d = gen.run(gen.netlist(P, an, loads + "\nIZR 0 VCC dc 0 ac 1", supply_over=S),
                     {"z.txt": dict(xmin=10, xmax=100e6, min_rows=100, ncols=3)})
    a = d["z.txt"]; return a[:, 0], np.abs(a[:, 1] + 1j * a[:, 2])
f, z = zrail({})
R["rail_impedance_ohm"] = {f"{F:g}Hz": round(float(np.interp(F, f, z)), 4) for F in (100, 1e3, 10e3, 100e3, 1e6, 10e6, 30e6)}
R["rail_impedance_peak"] = dict(ohm=round(float(z.max()), 3), at_Hz=float(f[np.argmax(z)]))
print(R["rail_impedance_ohm"], R["rail_impedance_peak"], flush=True)

# 4. regulator-output noise to port 1 (conservative: no regulator rejection assumed)
an = "ac dec 20 10 100e6\nwrdata r.txt v(p1) v(vcc)"
log, d = gen.run(gen.netlist(P, an, loads, supply_over=dict(VRIP_AC=1)), {"r.txt": dict(xmin=10, xmax=100e6, min_rows=100, ncols=6)})
a = d["r.txt"]; f = a[:, 0]; tp1 = 20 * np.log10(np.abs(a[:, 1] + 1j * a[:, 2])); tvcc = 20 * np.log10(np.abs(a[:, 4] + 1j * a[:, 5]))  # wrdata repeats the scale column per vector
R["U1_output_to_port1_dB"] = {f"{F:g}Hz": round(float(np.interp(F, f, tp1)), 1) for F in (100, 1e3, 10e3, 100e3, 1e6, 10e6, 30e6)}
R["U1_output_to_rail_dB"] = {f"{F:g}Hz": round(float(np.interp(F, f, tvcc)), 1) for F in (100, 1e3, 10e3, 100e3, 1e6, 10e6, 30e6)}
print(R["U1_output_to_port1_dB"], R["U1_output_to_rail_dB"], flush=True)

# 5. supply-only bring-up deck (amplifier not fitted): with and without the dummy load
def bare(rload):
    cir = ("* supply only\n" + gen.supply_block({}) + (f"RDUMMY VCC 0 {rload}\n" if rload else "") +
           ".control\nop\nprint v(vcc) v(uout) v(uin) i(vin)\necho @@SIM_COMPLETE@@\n.endc\n.end\n")
    log, _ = gen.run(cir); v = gen.parse_prints(log, ["v(vcc)", "v(uout)", "v(uin)", "i(vin)"])
    return dict(rail_V=round(v["v(vcc)"], 3), input_mA=round(-v["i(vin)"] * 1e3, 1),
                U1_load_mA=round((-v["i(vin)"]) * 1e3, 1),
                dummy_W=round(v["v(vcc)"] ** 2 / rload, 2) if rload else 0)
R["bringup_no_load"] = dict(bare(None), note="U1 load = divider only (~5.2 mA): below the LM317 10 mA maximum minimum-load spec; the model cannot show the resulting rise, so do not judge the regulator this way.")
R["bringup_dummy_100ohm"] = dict(bare(100), note="100 ohm 3 W dummy (~98 mA, ~1 W) stands in for the amplifier's ~91 mA.")
print(R["bringup_no_load"], R["bringup_dummy_100ohm"], flush=True)

# 6. fault: U1 input node shorted at 20 ms (e.g. C20 failure). Check D6/D7 clamp U1 reverse bias.
ex = "VSW SWC 0 PULSE(0 5 20m 1u 1u 1 2)\nSFLT UIN 0 SWC 0 SWMOD\n.model SWMOD SW(VT=2.5 VH=0.1 RON=0.01 ROFF=1e9)"
def fault(nod6):
  an = "tran 1u 25m 0 1u\nlinearize v(uout) v(uin) v(uadj) v(vcc)\nwrdata f.txt v(uout) v(uin) v(uadj) v(vcc)"
  cir = gen.netlist(P, an, loads, extra=".options method=gear reltol=1e-4\n" + ex)
  if nod6: cir = cir.replace("D6 UOUT UIN D1N4002", "* D6 omitted")
  log, d = gen.run(cir, {"f.txt": dict(xmin=0, xmax=25e-3, min_rows=1000, ncols=8)})
  a = d["f.txt"]; t = a[:, 0]; uo, ui, ua, vc = a[:, 1], a[:, 3], a[:, 5], a[:, 7]
  m = t > 20e-3
  return dict(max_out_minus_in_V=round(float((uo - ui)[m].max()), 2), max_out_minus_adj_V=round(float((uo - ua)[m].max()), 2),
    rail_after_5ms_V=round(float(vc[-1]), 3))
R["fault_input_short_with_D6"] = fault(False)
R["fault_input_short_without_D6"] = fault(True)
R["fault_note"] = "U1 input node shorted at 20 ms (worst case, e.g. C20 failure; D5 blocks a J6-side short). The behavioural U1 has no internal reverse path, so without D6 the reverse bias shown is what the real part's internal junctions would have to absorb."
print(R["fault_input_short_with_D6"], R["fault_input_short_without_D6"], flush=True)

# 7. dissipation
hd = R["input_sweep"]["U1_headroom_at_13p8V"]; I = R["startup_1ms_ramp"]["final_input_current_mA"] / 1e3
R["dissipation_W"] = dict(U1=round(hd * I, 2), RDAMP=round(I ** 2 * 1.0, 3), F1_max=round(I ** 2 * 1.33, 3),
    note="TO-220 at ~0.3 W: about 15-20 C rise with no heatsink (R_thetaJA ~50-65 C/W).")
json.dump(R, open("../results/supply.json", "w"), indent=1)
print(json.dumps(R["dissipation_W"]))
