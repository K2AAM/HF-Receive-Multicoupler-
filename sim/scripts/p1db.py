import gen,numpy as np
def p1db(P={},f=7e6):
    rows=[]
    for pin in range(-10,22,2):
        a=np.sqrt(2*50*10**(pin/10)/1000)*2
        loads=f"V1 G 0 SIN(0 {a} {f})\nRGIN G IN 50\n"+gen.portloads(P)
        gen.run(gen.netlist(P,f""".options reltol=1e-5 method=gear
.control
tran {1/(f*40)} {25e-6} {5e-6} {1/(f*40)}
linearize v(p1)
wrdata /tmp/p1.txt v(p1)
.endc""",loads))
        d=np.loadtxt('/tmp/p1.txt'); v=d[:,1]-d[:,1].mean(); w=np.blackman(len(v)); S=np.fft.rfft(v*w)/w.sum()*2; fr=np.fft.rfftfreq(len(v),d[1,0]-d[0,0])
        i=np.argmin(abs(fr-f)); po=10*np.log10(max(abs(S[i-2:i+3]))**2/2/50*1000)
        rows.append((pin,po,po-pin))
    g0=rows[0][2]
    for pin,po,g in rows:
        if g<g0-1: return rows,pin,po
    return rows,None,None
if __name__=="__main__":
    rows,pin,po=p1db()
    for r in rows: print("Pin %d  Pout %.2f  G %.2f"%r)
    print("P1dB: input",pin,"output",po)
