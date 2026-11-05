"""Rev B multicoupler netlist generator + analysis harness (ngspice).
All values in one dict P; options toggle parasitics, port count, loads."""
import subprocess, numpy as np, re, os, tempfile, json
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=dict(
 VCC=9.9,
 # input
 CIN=4.7e-6, CBASE=2.2e-6, CFBK=2.2e-6, RBL=10e3, CLAMP=1,
 # LPF 7-pole Chebyshev ~57 MHz
 LC1=43e-12, LL=220e-9, LL2=270e-9, LC2=100e-12, LQ=40,
 # gain stage
 QN='2N3904', QP='2N3906', RE=56, RF=220, R1=1.5e3, R2=3.3e3, R3=1.5e3, R4=3.3e3, RL=220, RLREF=0,
 # Vbe multiplier spreader
 QDP='2N3906', QDN='2N3904', RPU=360, RPD=360, RX=15,
 # followers
 QF='2N3904', QG='2N3906', REO=3.3,
 # ports
 RS=51, NPORT=4, CPORT=4.7e-6,
 PAR=1,     # parasitics
 TEMP=27,
)
def netlist(P, analysis, loads=None, extra=""):
    P={**BASE,**P}; n=P['NPORT']
    par = P['PAR']
    Le = '5n' if par else '0.001n'
    L=[]
    L.append(f".include {HERE}/models_bjt.lib")
    L.append(P.get('MODELS',''))
    # ---------- input ----------
    # bipolar 10u input DC block with ESR/ESL + 100n film
    L.append(f"CIN1 IN XIN1 {P['CIN']}\nRIN1 XIN1 XIN2 0.02\nLIN1 XIN2 N1 {'8n' if par else '0.01n'}")
    L.append(f"RBL N1 0 {P['RBL']}")
    if P['CLAMP']:
        L.append("DA1 N1 DA D1N4148\nDA2 DA 0 D1N4148\nDB1 0 DB D1N4148\nDB2 DB N1 D1N4148")
    # LPF with inductor Q (series R at 30 MHz)
    rl = 2*np.pi*30e6*P['LL']/P['LQ']; rl2 = 2*np.pi*30e6*P['LL2']/P['LQ']
    L.append(f"CF1 N1 0 {P['LC1']}")
    L.append(f"LF1 N1 NL1 {P['LL']}\nRLF1 NL1 N2 {rl}")
    L.append(f"CF2 N2 0 {P['LC2']}")
    L.append(f"LF2 N2 NL2 {P['LL2']}\nRLF2 NL2 N3 {rl2}")
    L.append(f"CF3 N3 0 {P['LC2']}")
    L.append(f"LF3 N3 NL3 {P['LL']}\nRLF3 NL3 N4 {rl}")
    L.append(f"CF4 N4 0 {P['LC1']}")
    if par: L.append("CPN4 N4 0 1p")
    # ---------- complementary gain stage (collectors tied at X) ----------
    for nm,base in (('N','BN'),('P','BP')):
        L.append(f"CB{nm}1 N4 X{nm}B {P['CBASE']}\nRB{nm}E X{nm}B Y{nm}B 0.02\nLB{nm}E Y{nm}B {base} {'6n' if par else '0.01n'}")
    L.append(f"Q1N X BN EN1 {P['QN']}\nLEN EN1 EN {Le}\nRE1 EN 0 {P['RE']}")
    L.append(f"Q1P X BP EP1 {P['QP']}\nLEP EP1 EP {Le}\nRE2 VCC EP {P['RE']}")
    # collector-feedback DC bias (each half from X), AC-decoupled midpoints
    L.append(f"R1A X RM {P['R1']}\nR1B RM BN {P['R1']}\nCRM RM 0 10u\nR2 BN 0 {P['R2']}")
    L.append(f"R3A X RMP {P['R3']}\nR3B RMP BP {P['R3']}\nCRMP VCC RMP 10u\nR4 BP VCC {P['R4']}")
    # AC load at X
    L.append(f"CLX X LX {P['CBASE']}\nRLX LX {P['RLREF']} {P['RL']}")
    # shunt feedback X -> N4
    L.append(f"RF X FB {P['RF']}\nCFB1 FB FB2 {P['CFBK']}\nLFB FB2 N4 {'6n' if par else '0.01n'}")
    if par: L.append("CPX X 0 2p")
    # ---------- diamond buffer ----------
    # pre-drivers: PNP follower pulls up via RPU (to VCC) -> drives NPN output; NPN follower pulled down via RPD -> drives PNP output
    L.append(f"Q2A 0 X E2A {P['QDP']}{' temp='+str(P['TPRE']) if P.get('TPRE') is not None else ''}\nRX1 E2A D1 {P['RX']}\nRPU VCC D1 {P['RPU']}")
    L.append(f"Q3A VCC X E3A {P['QDN']}{' temp='+str(P['TPRE']) if P.get('TPRE') is not None else ''}\nRX2 D2 E3A {P['RX']}\nRPD D2 0 {P['RPD']}")
    L.append(f"RCOL VCC VCF 4.7\nCCOL VCF 0 100n")
    L.append(f"Q2 VCF D1 EF1 {P['QF']}{' temp='+str(P['TOUT']) if P.get('TOUT') is not None else ''}\nLEF EF1 EF {Le}\nREO1 EF OUT {P['REO']}")
    L.append(f"Q3 0 D2 EG1 {P['QG']}{' temp='+str(P['TOUT']) if P.get('TOUT') is not None else ''}\nLEG EG1 EG {Le}\nREO2 EG OUT {P['REO']}")
    if par: L.append("CPOUT OUT 0 3p\nCPD1 D1 0 1p\nCPD2 D2 0 1p")
    # ports
    for k in range(1,n+1):
        L.append(f"CO{k}A OUT XO{k} {P['CPORT']}\nRO{k}E XO{k} YO{k} 0.02\nLO{k}E YO{k} ZO{k} {'8n' if par else '0.01n'}")
        L.append(f"RS{k} ZO{k} SO{k} {P['RS']}")
        L.append(f"LS{k} SO{k} P{k} {'8n' if par else '0.01n'}" + (f"\nCPP{k} P{k} 0 2p" if par else ""))
    # supply (ideal regulated rail + local bypass)
    L.append(f"VCC VCC 0 {P['VCC']}")
    # loads / sources supplied by caller
    L.append(loads or "")
    L.append(extra)
    L.append(f".options temp={P['TEMP']} tnom=27")
    L.append(analysis)
    return "* rev B multicoupler\n"+"\n".join(L)+"\n.end\n"

def run(cir, tag="t"):
    fd,fn=tempfile.mkstemp(suffix='.cir',dir='/tmp'); os.write(fd,cir.encode()); os.close(fd)
    r=subprocess.run(['ngspice','-b',fn],capture_output=True,text=True,cwd='/tmp')
    os.remove(fn); return r.stdout+r.stderr

def portloads(P, drive=None, z='50'):
    n={**BASE,**P}['NPORT']; s=[]
    for k in range(1,n+1):
        if drive==k: s.append(f"VG{k} G{k} 0 dc 0 ac 2\nRG{k} G{k} P{k} 50")
        else: s.append(f"RL{k} P{k} 0 {z}")
    return "\n".join(s)

def op(P={}):
    loads="VGIN GIN 0 0\nRGIN GIN IN 50\n"+portloads(P)
    out=run(netlist(P,""".control
op
print v(n4) v(bn) v(bp) v(x) v(d1) v(d2) v(out) v(vcf)
print @q1n[ic] @q1p[ic] @q2a[ic] @q3a[ic] @q2[ic] @q3[ic] i(vcc)
.endc""",loads))
    d={}
    for l in out.splitlines():
        m=re.match(r"\s*(\S+)\s*=\s*([-\d.eE+]+)",l)
        if m: d[m.group(1)]=float(m.group(2))
    return d,out

def ac(P={}, fstart=1e3, fstop=500e6, ppd=40):
    """returns dict of arrays: f, S21 (port1), S11, iso(P2->P3), rev(P2->IN), S22(P2)"""
    k=1.38e-23
    # forward
    loads="VGIN GIN 0 dc 0 ac 2\nRGIN GIN IN 50\n"+portloads(P)
    fn='/tmp/acf.txt'
    run(netlist(P,f""".control
ac dec {ppd} {fstart} {fstop}
wrdata {fn} v(p1) v(in) v(p2)
.endc""",loads))
    a=np.loadtxt(fn); f=a[:,0]
    vp1=a[:,1]+1j*a[:,2]; vin=a[:,4]+1j*a[:,5]
    S21=20*np.log10(abs(vp1)); S11=20*np.log10(abs(vin-1))
    # reverse/isolation: drive P2
    loads="RGIN IN 0 50\n"+portloads(P,drive=2)
    run(netlist(P,f""".control
ac dec {ppd} {fstart} {fstop}
wrdata {fn} v(p3) v(in) v(p2)
.endc""",loads))
    b=np.loadtxt(fn)
    vp3=b[:,1]+1j*b[:,2]; vin2=b[:,4]+1j*b[:,5]; vp2=b[:,7]+1j*b[:,8]
    return dict(f=f,S21=S21,S11=S11,iso=20*np.log10(abs(vp3)),rev=20*np.log10(abs(vin2)),S22=20*np.log10(abs(vp2-1)),
                zin=50*(vin/(2-vin)), zout=50*(vp2/(2-vp2)))

def nf(P={}, fstart=10e3, fstop=60e6):
    k=1.38e-23; T=290
    loads="VGIN GIN 0 dc 0 ac 2\nRGIN GIN IN 50\n"+portloads(P)
    fn='/tmp/nz.txt'
    PP={**P,'TEMP':16.85}
    run(netlist(PP,f""".control
noise v(p1) vgin dec 10 {fstart} {fstop}
setplot noise1
wrdata {fn} inoise_spectrum
.endc""",loads))
    a=np.loadtxt(fn)
    return a[:,0], 10*np.log10(a[:,1]**2/(4*k*T*50))

def noise_contrib(P={}, f0=10e6):
    """per-element output noise contribution at f0 (ngspice noise with ptsperdecade 1 over tiny span)"""
    loads="VGIN GIN 0 dc 0 ac 2\nRGIN GIN IN 50\n"+portloads(P)
    out=run(netlist({**P,'TEMP':16.85},f""".control
noise v(p1) vgin lin 1 {f0} {f0} 1
print all
.endc""",loads))
    return out

def twotone(P={}, f1=7.0e6, f2=7.1e6, pin=-10, T=None, step=None, settle=20e-6, reltol=1e-5, extra=""):
    """two equal tones, pin dBm each available power into 50 ohm. Returns dict of output powers (dBm) at port1."""
    a=np.sqrt(2*50*10**(pin/10)/1000)*2   # EMF peak per tone
    df=abs(f2-f1); 
    if T is None: T=max(10/df, 40/min(f1,f2))   # >=10 beat periods
    fmax=max(2*f2+f1, f1+f2)*1.0
    if step is None: step=1/(fmax*20)
    loads=f"V1 G 0 SIN(0 {a} {f1})\nV2 G GG SIN(0 {a} {f2})\nRGIN GG IN 50\n"+portloads(P)
    fn='/tmp/tt.txt'
    run(netlist(P,f""".options reltol={reltol} abstol=1e-14 vntol=1e-9 method=gear maxord=2
.control
tran {step} {settle+T} {settle} {step}
linearize v(p1)
wrdata {fn} v(p1)
.endc""",loads,extra))
    d=np.loadtxt(fn); t=d[:,0]; v=d[:,1]-d[:,1].mean()
    w=np.blackman(len(v)); S=np.fft.rfft(v*w)/np.sum(w)*2; fr=np.fft.rfftfreq(len(v),t[1]-t[0])
    def p(F):
        i=np.argmin(abs(fr-F)); m=max(abs(S[max(i-2,0):i+3])); return 10*np.log10(m**2/2/50*1000)
    res=dict(f1=p(f1),f2=p(f2),im3l=p(2*f1-f2),im3h=p(2*f2-f1),im2s=p(f1+f2),im2d=p(abs(f2-f1)),h2=p(2*f1))
    res['oip3']=res['f1']+(res['f1']-max(res['im3l'],res['im3h']))/2
    res['gain']=res['f1']-pin
    res['iip3']=res['oip3']-res['gain']
    res['oip2']=2*res['f1']-res['im2s']; res['iip2']=res['oip2']-res['gain']
    return res

def nf_breakdown(P={}, freqs=(1e6,10e6,30e6,50e6)):
    """NF excluding the port-1 load's own noise; per-element % of the remaining output noise power."""
    loads="VGIN GIN 0 dc 0 ac 2\nRGIN GIN IN 50\n"+portloads(P)
    res={}
    for f0 in freqs:
        vec="onoise_spectrum"
        o=run(netlist({**P,'TEMP':16.85},f""".control
noise v(p1) vgin dec 1 {f0} {f0} 1
setplot noise1
print all
.endc""",loads))
        v={}
        for l in o.splitlines():
            m=re.match(r"\s*onoise_(\S+?)\s*=\s*([-\d.eE+]+)",l)
            if m: v[m.group(1)]=float(m.group(2))**2
        tot=v.pop('spectrum'); v={k:x for k,x in v.items() if '_' not in k}
        own=v.get('rl1',0); src=v['rgin']
        F=(tot-own)/src
        grp={}
        for k,x in v.items():
            if k in('rl1',): continue
            grp[k]=x
        top=sorted(((k,100*x/(tot-own)) for k,x in grp.items()),key=lambda t:-t[1])
        res[f0]=dict(NF=10*np.log10(F),top=top[:14])
    return res
