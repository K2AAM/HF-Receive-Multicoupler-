"""Rev B final verification suite. Writes results/*.json and plots."""
import gen,numpy as np,json,os,p1db
os.makedirs('results',exist_ok=True)
OPT={"A_+1.5dB":dict(RE=56,RF=220,RL=220),"B_+3dB_recommended":dict(),"C_+5.5dB":dict(RE=47,RF=330,RL=220)}
summary={}
for name,P in OPT.items():
    d,_=gen.op(P)
    r=gen.ac(P,1e3,200e6,40); f=r['f']; band=(f>=1e4)&(f<=50.1e6)
    at=lambda a,F: float(a[np.argmin(abs(f-F))])
    nfr=gen.nf_breakdown(P,(1e6,10e6,30e6,50e6))
    s=dict(op={k:float(v) for k,v in d.items()},
      gain={f"{F/1e6:g}MHz":round(at(r['S21'],F),2) for F in (1e4,1e6,10e6,30e6,50e6)},
      flatness_10k_50M=[round(float(r['S21'][band].min()),2),round(float(r['S21'][band].max()),2)],
      S11_max_10k_50M=round(float(r['S11'][band].max()),1),
      S22_max_10k_50M=round(float(r['S22'][band].max()),1),
      iso={f"{F/1e6:g}MHz":round(at(r['iso'],F),1) for F in (1e6,10e6,30e6,50e6)},
      rev_iso={f"{F/1e6:g}MHz":round(at(r['rev'],F),1) for F in (1e6,10e6,30e6,50e6)},
      rej={f"{F/1e6:g}MHz":round(at(r['S21'],F),1) for F in (88e6,100e6,108e6)},
      NF={f"{F/1e6:g}MHz":round(float(x['NF']),2) for F,x in nfr.items()},
      NF_top10MHz=[(k,round(p,1)) for k,p in nfr[10e6]['top'][:8]],
      IM={})
    for F in (1e6,7e6,14e6,28e6):
        t=gen.twotone(P,F,F+0.2e6,-10); s['IM'][f"IP3_{F/1e6:g}MHz"]=dict(OIP3=round(t['oip3'],1),IIP3=round(t['iip3'],1))
    t=gen.twotone(P,6e6,7e6,-10); s['IM']['IP2_6+7MHz']=dict(OIP2=round(t['oip2'],1),IIP2=round(t['iip2'],1))
    t=gen.twotone(P,0.6e6,1.0e6,-10,T=50e-6); s['IM']['IP2_0.6+1.0MHz']=dict(OIP2=round(t['oip2'],1),IIP2=round(t['iip2'],1))
    rows,pin,po=p1db.p1db(P,7e6); s['P1dB_7MHz']=dict(input=pin,output=round(po,1) if po else None)
    summary[name]=s; print(name,json.dumps(s)[:1500],flush=True)
    if name.startswith('B'): np.save('results/ac_B.npy',np.array([f,r['S21'],r['S11'],r['S22'],r['iso'],r['rev']]))
json.dump(summary,open('results/summary.json','w'),indent=1)
