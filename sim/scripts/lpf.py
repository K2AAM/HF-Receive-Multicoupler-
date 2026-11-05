import numpy as np
def resp(elems,f,Q=None):
    # ladder: list of ('C',val) shunt / ('L',val) series, between 50 ohm source/load; ABCD
    w=2*np.pi*f; out=[]
    for wi in w:
        M=np.eye(2,dtype=complex)
        for t,v in elems:
            if t=='C': Y=1j*wi*v; A=np.array([[1,0],[Y,1]])
            else:
                Z=1j*wi*v + ((wi*v/Q) if Q else 0); A=np.array([[1,Z],[0,1]])
            M=M@A
        A_,B_,C_,D_=M.ravel(); Z0=50
        s21=2/(A_+B_/Z0+C_*Z0+D_); s11=(A_+B_/Z0-C_*Z0-D_)/(A_+B_/Z0+C_*Z0+D_)
        out.append((20*np.log10(abs(s21)),20*np.log10(abs(s11))))
    return np.array(out)
old=[('C',27e-12),('L',180e-9),('C',82e-12),('L',180e-9),('C',27e-12)]
F=np.array([10e6,30e6,50e6,88e6,100e6,108e6,150e6])
r=resp(old,F)
print("OLD 5-pole (27p-180n-82p-180n-27p), ideal parts")
for f,(a,b) in zip(F,r): print(f"  {f/1e6:6.0f} MHz  S21 {a:7.2f} dB  S11 {b:6.1f} dB")
F=np.array([0.01e6,1e6,10e6,30e6,40e6,50e6,55e6,60e6,70e6,80e6,88e6,100e6,108e6,150e6])
def show(name,el,Q=None):
    r=resp(el,F,Q); print(name)
    print("  "+"  ".join(f"{f/1e6:g}:{a:.2f}/{b:.0f}" for f,(a,b) in zip(F,r)))
g=[1.1811,1.4228,2.0966,1.5733,2.0966,1.4228,1.1811]
for fc in [52e6,55e6,58e6]:
    el=[('C' if i%2==0 else 'L', gi/(2*np.pi*fc*50) if i%2==0 else gi*50/(2*np.pi*fc)) for i,gi in enumerate(g)]
    show(f"Cheb7 0.1dB fc={fc/1e6:.0f} ideal "+" ".join(f"{t}{v*1e12 if t=='C' else v*1e9:.0f}" for t,v in el),el)
E=[('C',68e-12),('L',220e-9),('C',120e-12),('L',220e-9),('C',120e-12),('L',220e-9),('C',68e-12)]
show("E12: 68p 220n 120p 220n 120p 220n 68p, Q=inf",E)
show("E12 same, inductor Q=40",E,40)
show("E12 same, inductor Q=25",E,25)
E2=[('C',56e-12),('L',220e-9),('C',100e-12),('L',220e-9),('C',100e-12),('L',220e-9),('C',56e-12)]
show("E12 alt: 56p 220n 100p 220n 100p 220n 56p Q=40",E2,40)
