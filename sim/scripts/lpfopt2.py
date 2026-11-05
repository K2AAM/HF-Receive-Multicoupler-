import numpy as np, itertools
exec(open('lpf.py').read().split("old=")[0])
E24=[33,36,39,43,47,51,56,62,68,75,82,91,100,110,120,130,150]
Ls=[180e-9,220e-9,270e-9]
fpass=np.linspace(0.1e6,52e6,150); res=[]
for c1,c2,c3 in itertools.product(E24,E24,E24):
  for L1,L2 in itertools.product(Ls,Ls):
    el=[('C',c1*1e-12),('L',L1),('C',c2*1e-12),('L',L2),('C',c3*1e-12),('L',L1),('C',c1*1e-12)]
    # symmetric 7-pole requires c3==c2 for symmetry; allow general middle
    el=[('C',c1*1e-12),('L',L1),('C',c2*1e-12),('L',L2),('C',c2*1e-12),('L',L1),('C',c1*1e-12)] if c3!=c2 else el
    r=resp(el,fpass,60); s11=r[:,1].max(); il=-r[:,0].min()
    if s11>-20: continue
    rej=-resp(el,np.array([88e6]),60)[0,0]
    res.append((rej,s11,il,c1,c2,L1,L2))
res=sorted(set(res),reverse=True)
for x in res[:8]: print("rej88 %.1f S11max %.1f ILmax %.2f  C1=%dp C2=%dp L1=%dn L2=%dn"%(x[0],x[1],x[2],x[3],x[4],x[5]*1e9,x[6]*1e9))
