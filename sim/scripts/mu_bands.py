import numpy as np, itertools, sys, json
b = sys.argv[1] if len(sys.argv) > 1 else "A"
a = np.load(f'../results/smatrix_{b}.npy'); f = a[:, 0, 0].real; S = a[:, 5:, :]
def reduce(S, keep, term, G):
    a=list(keep); bb=list(term)
    Saa=S[:,a][:,:,a]; Sab=S[:,a][:,:,bb]; Sba=S[:,bb][:,:,a]; Sbb=S[:,bb][:,:,bb]
    Gm=np.diag(G); M=np.linalg.inv(np.eye(len(bb))[None]-Sbb@Gm[None]); return Saa+Sab@Gm[None]@M@Sba
def mu(S2):
    s11,s12,s21,s22=S2[:,0,0],S2[:,0,1],S2[:,1,0],S2[:,1,1]; D=s11*s22-s12*s21
    return (1-abs(s11)**2)/(abs(s22-D*np.conj(s11))+abs(s12*s21))
ph=np.exp(1j*np.linspace(0,2*np.pi,12,endpoint=False)); g=[0]+list(ph)+list(.5*ph)
res = {}
for keep in [(0,1),(1,2)]:
    term=[k for k in range(5) if k not in keep]; m=np.full(len(f),np.inf)
    for G in itertools.product(g,repeat=3): m=np.minimum(m,mu(reduce(S,keep,term,np.array(G,complex))))
    for lo,hi in [(1e4,60e6),(60e6,500e6),(500e6,1e9),(1e9,2.01e9)]:
        bm=(f>=lo)&(f<hi); i=np.argmin(m[bm]); k=f"{keep} {lo/1e6:g}-{hi/1e6:g} MHz"
        res[k]=dict(mu_min=round(float(m[bm][i]),3), at_MHz=round(float(f[bm][i]/1e6),1)); print(k,res[k])
res["max|S_in,in|"]=float(abs(S[:,0,0]).max()); res["max|S_p1,p1|"]=float(abs(S[:,1,1]).max())
print(res); json.dump(res, open(f'../results/mu_bands_{b}.json','w'), indent=1)
