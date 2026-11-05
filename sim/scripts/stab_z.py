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
for lk in ['50','open','short','C','L']:
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
for lk in ['50','open','short','C','L']:
    res[f'input Re(Z) min, ports {lk}']=zin(lk)

for k,v in res.items(): print(k,v)
json.dump(res,open('results/stab_final.json','w'),indent=1)
