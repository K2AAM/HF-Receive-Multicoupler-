import gen,json
rows=[]
for amb in (0,27,50):
    for dT_out,dT_pre in ((0,0),(30,30),(30,10),(30,0)):
        P=dict(TEMP=amb,TOUT=amb+dT_out,TPRE=amb+dT_pre)
        d,_=gen.op(P)
        rows.append(dict(amb=amb,dT_out=dT_out,dT_pre=dT_pre,Iq1=round(d['@q1n[ic]']*1e3,1),Iq2=round(d['@q2[ic]']*1e3,1),Itot=round(-d['i(vcc)']*1e3,1),Vout=round(d['v(out)'],2)))
        print(rows[-1],flush=True)
json.dump(rows,open('thermal.json','w'),indent=1)
