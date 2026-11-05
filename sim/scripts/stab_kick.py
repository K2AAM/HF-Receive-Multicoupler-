import gen,numpy as np,itertools,json
P={}
res={}
# (1) one-port real part check at port 2 and at input, others terminated with combos
def zscan(loadkind, fmax=2e9):
    n=4
    def term(k):
        if loadkind=='50': return f"RL{k} P{k} 0 50"
        if loadkind=='open': return f"RL{k} P{k} 0 1e9"
        if loadkind=='short': return f"RL{k} P{k} 0 0.01"
        if loadkind=='C': return f"CLD{k} P{k} 0 100p\nRLD{k} P{k} 0 1e9"
        if loadkind=='L': return f"LLD{k} P{k} 0 1u"
    # port 2 driven by 1A AC current source -> V = Z
    loads="RGIN IN 0 50\n"+"\n".join(term(k) for k in (1,3,4))+"\nIZ 0 P2 dc 0 ac 1"
    gen.run(gen.netlist(P,f""".control
ac dec 30 1e4 {fmax}
wrdata /tmp/z.txt v(p2)
.endc""",loads))
    a=np.loadtxt('/tmp/z.txt'); f=a[:,0]; z=a[:,1]+1j*a[:,2]; return f,z
for lk in []:
    f,z=zscan(lk); i=np.argmin(z.real)
    res[f'port2 Re(Z) min, others {lk}']=(round(float(z.real[i]),2), float(f[i]))
# input impedance with ports at various loads
def zin(loadkind):
    def term(k):
        return {"50":f"RL{k} P{k} 0 50","open":f"RL{k} P{k} 0 1e9","short":f"RL{k} P{k} 0 0.01","C":f"CLD{k} P{k} 0 100p\nRLD{k} P{k} 0 1e9","L":f"LLD{k} P{k} 0 1u"}[lk2]
    lk2=loadkind
    loads="\n".join(term(k) for k in (1,2,3,4))+"\nIZ 0 IN dc 0 ac 1"
    gen.run(gen.netlist(P,""".control
ac dec 30 1e4 2e9
wrdata /tmp/z.txt v(in)
.endc""",loads))
    a=np.loadtxt('/tmp/z.txt'); f=a[:,0]; z=a[:,1]+1j*a[:,2]; i=np.argmin(z.real); return round(float(z.real[i]),2), float(f[i])
for lk in []:
    res[f'input Re(Z) min, ports {lk}']=zin(lk)
# (3) transient kick with cables open/short at far end
def kick(far, td):
    s=[]
    for k in (1,2,3,4):
        s.append(f"TL{k} P{k} 0 FAR{k} 0 Z0=50 TD={td}")
        s.append(f"RF{k} FAR{k} 0 {'10k' if far=='open' else '0.5'}")
    s.append(f"TLIN IN 0 FARIN 0 Z0=50 TD={td}\nRFIN FARIN 0 {'10k' if far=='open' else '0.5'}")
    s.append("IK 0 X PULSE(0 10m 1u 1n 1n 2n 1)")
    o=gen.run(gen.netlist(P,""".options method=gear reltol=1e-3 trtol=10
.control
tran 0.2n 6u 0 0.2n
wrdata /tmp/k.txt v(out)
.endc""","\n".join(s)))
    import os
    d=np.loadtxt('/tmp/k.txt'); t=d[:,0]
    if t.max()<5.9e-6: return None, o[-400:]
    v=d[:,1]-np.median(d[t>5e-6,1])
    early=np.abs(v[(t>1.0e-6)&(t<1.5e-6)]).max(); mid=np.abs(v[(t>3e-6)&(t<4e-6)]).max(); late=np.abs(v[t>5e-6]).max()
    return early,(mid,late)
    return early, late
for far,td in itertools.product(['open','short'],['0.5n','2n','5n','12n','25n']):
    open('/tmp/k.txt','w').write('0 0\n')
    e,l=kick(far,td)
    res[f'kick {far} cable TD={td}']=(f"peak {e*1e3:.1f} mV", f"3-4us {l[0]*1e6:.2f} uV", f">5us {l[1]*1e6:.2f} uV") if e is not None else ("FAILED",l[-200:])
for k,v in res.items(): print(k,v)
json.dump(res,open('stab_kick.json','w'),indent=1)
