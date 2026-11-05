import gen,numpy as np,re,json,sys
rng=np.random.default_rng(12345)
lib=open('models_bjt.lib').read()
def model_line(base,newname,bfk,isk):
    m=re.search(r"\.model "+base+r" (NPN|PNP)\((.*)\)",lib)
    typ,par=m.group(1),m.group(2)
    def scale(par,key,k):
        return re.sub(r"(?i)\b("+key+r")=([-\d.eEkKfFpPnNuUmM]+)", lambda mm: f"{mm.group(1)}={float(gen_val(mm.group(2)))*k:g}", par, count=1)
    par=scale(par,'BF',bfk); par=scale(par,'IS',isk)
    return f".model {newname} {typ}({par})"
def gen_val(s):
    s=s.lower(); mult={'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3}
    return float(s[:-1])*mult[s[-1]] if s[-1] in mult else float(s)
N=int(sys.argv[1]) if len(sys.argv)>1 else 60
B=gen.BASE; out=[]
for run in range(N):
    P={}; models=[]
    for inst,key,base in (('q1n','QN','2N3904'),('q1p','QP','2N3906'),('q2a','QDP','2N3906'),('q3a','QDN','2N3904'),('q2','QF','2N3904'),('q3','QG','2N3906')):
        bfk=np.exp(rng.uniform(np.log(0.5),np.log(1.5))); isk=np.exp(rng.uniform(np.log(0.6),np.log(1.7)))
        nm=f"M{inst}"; models.append(model_line(base,nm,bfk,isk)); P[key]=nm
    P['MODELS']="\n".join(models)
    for k in ('RE','RF','R1','R2','R3','R4','RL','RPU','RPD','RX','REO','RS','RBL'):
        P[k]=B[k]*(1+rng.normal(0,0.01/3))
    for k in ('LC1','LC2'): P[k]=B[k]*(1+rng.uniform(-0.05,0.05))
    for k in ('LL','LL2'): P[k]=B[k]*(1+rng.uniform(-0.05,0.05))
    for k in ('CIN','CBASE','CFBK','CPORT'): P[k]=B[k]*(1+rng.uniform(-0.1,0.1))
    P['LQ']=rng.uniform(40,80); P['TEMP']=float(rng.choice([0,27,50]))
    d,_=gen.op(P)
    r=gen.ac(P,1e4,60e6,10); f=r['f']; m=f<=50.1e6
    g=lambda F,a: float(a[np.argmin(abs(f-F))])
    row=dict(run=run,T=P['TEMP'],Iq1n=d['@q1n[ic]']*1e3,Iq1p=-d['@q1p[ic]']*1e3,Iq2=d['@q2[ic]']*1e3,Iq3=-d['@q3[ic]']*1e3,Itot=-d['i(vcc)']*1e3,Vout=d['v(out)'],
             G1=g(1e6,r['S21']),G30=g(3e7,r['S21']),G50=g(5e7,r['S21']),S11max=float(r['S11'][m].max()),iso30=g(3e7,r['iso']),iso50=g(5e7,r['iso']),rev30=g(3e7,r['rev']))
    if run<int(sys.argv[2] if len(sys.argv)>2 else 30):
        t=gen.twotone(P,7e6,7.2e6,-10); row['IIP3_7']=t['iip3']
        t=gen.twotone(P,6e6,7e6,-10); row['IIP2_67']=t['iip2']
        t=gen.twotone(P,0.6e6,1.0e6,-10,T=50e-6); row['IIP2_MW']=t['iip2']
    out.append(row); print(json.dumps({k:round(v,2) if isinstance(v,float) else v for k,v in row.items()}),flush=True)
json.dump(out,open('mc.json','w'),indent=1)
