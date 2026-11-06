import schemdraw, schemdraw.elements as e
schemdraw.config(fontsize=10, lw=1.1, unit=2.4)
d=schemdraw.Drawing(show=False)
G=lambda: e.Ground()
def lbl(pt,text,loc='right',dx=0.15,dy=0):
    d.add(e.Label().at((pt[0]+dx,pt[1]+dy)).label(text,loc=loc))
# ---------------- INPUT + LPF -----------------
d.add(e.Coax(length=2).at((0,0)).right().label('J1 ANT IN\n(BNC)',loc='top'))
d.add(e.Line().right(0.6)); p=d.here; d.add(e.Dot())
d.add(e.Lamp().at(p).down().label('GDT1\n90 V',loc='bottom')); d.add(G())
d.add(e.Capacitor().at(p).right().label('C1 4.7µ\nfilm 63V',loc='top')); n1=d.here; d.add(e.Dot()); lbl(n1,'N1',loc='top',dx=-0.2,dy=0.4)
d.add(e.Resistor().at(n1).down().label('RBL\n10k',loc='bottom')); d.add(G())
d.add(e.Line().at(n1).right(1.3)); n1b=d.here; d.add(e.Dot())
d.add(e.Diode().at(n1b).down().label('D1–D4\n1N4148\n2 series\neach way',loc='bottom')); d.add(G())
d.add(e.Line().at(n1b).right(2.6)); c1=d.here; d.add(e.Dot())
d.add(e.Capacitor().at(c1).down().label('C4\n43p',loc='bottom')); d.add(G())
d.add(e.Inductor2(loops=3).at(c1).right().label('L1 220n',loc='top')); c2=d.here; d.add(e.Dot())
d.add(e.Capacitor().at(c2).down().label('C5\n100p',loc='bottom')); d.add(G())
d.add(e.Inductor2(loops=3).at(c2).right().label('L2 270n',loc='top')); c3=d.here; d.add(e.Dot())
d.add(e.Capacitor().at(c3).down().label('C6\n100p',loc='bottom')); d.add(G())
d.add(e.Inductor2(loops=3).at(c3).right().label('L3 220n',loc='top')); c4=d.here; d.add(e.Dot())
d.add(e.Capacitor().at(c4).down().label('C7\n43p',loc='bottom')); d.add(G())
d.add(e.Line().at(c4).right(1.4)); nf=d.here; d.add(e.Dot()); lbl(nf,'LPF',loc='bottom',dx=0.1,dy=-0.6)
# ---------------- GAIN STAGE -----------------
yP,yN=5.0,-5.0
d.add(e.Line().at(nf).up(yP)); d.add(e.Capacitor().right().label('C3 2.2µ film',loc='top')); bp=d.here; d.add(e.Dot()); lbl(bp,'BP',loc='top',dx=-0.3,dy=0.4)
d.add(e.Line().at(nf).down(-yN)); d.add(e.Capacitor().right().label('C2 2.2µ film',loc='bottom')); bn=d.here; d.add(e.Dot()); lbl(bn,'BN',loc='bottom',dx=-0.3,dy=-0.4)
d.add(e.Line().at(bp).right(0.5)); QP=d.add(e.BjtPnp(circle=True).anchor('base').label('Q1P\n2N3906',loc='right'))
d.add(e.Line().at(bn).right(0.5)); QN=d.add(e.BjtNpn(circle=True).anchor('base').label('Q1N\n2N3904',loc='right'))
d.add(e.Resistor().at(QP.emitter).up().label('RE2 56',loc='bottom')); d.add(e.Vdd().label('+9.8V'))
d.add(e.Resistor().at(QN.emitter).down().label('RE1 56',loc='bottom')); d.add(G())
d.add(e.Line().at(QP.collector).to((QP.collector[0],0))); X=(QP.collector[0],0)
d.add(e.Line().at(QN.collector).to(X)); d.add(e.Dot().at(X)); lbl(X,'X',loc='left',dx=-0.3,dy=0.3)
# ---------------- DIAMOND BUFFER -----------------
d.add(e.Line().at(X).right(4.5)); xr=d.here; d.add(e.Dot())
d.add(e.Line().at(xr).up(2.6)); d.add(e.Line().right(0.7)); xa=d.here
Q2A=d.add(e.BjtPnp(circle=True).anchor('base').at(xa).flip().reverse() if False else e.BjtPnp(circle=True).anchor('base').at(xa).label('Q2A\n2N3906',loc='right',ofst=(0.5,-0.6)))
d.add(e.Line().at(xr).down(2.6)); d.add(e.Line().right(0.7)); xb=d.here
Q3A=d.add(e.BjtNpn(circle=True).anchor('base').at(xb).label('Q3A\n2N3904',loc='right',ofst=(0.5,0.6)))
# Q2A: PNP emitter up, collector down -> collector to ground via label
d.add(e.Resistor().at(Q2A.emitter).up(1.6).label('RX1 15',loc='top')); D1=d.here; d.add(e.Dot()); lbl(D1,'D1',loc='left',dx=-0.4,dy=0.3)
d.add(e.Resistor().at(D1).up(1.8).label('RPU 360',loc='bottom')); d.add(e.Vdd().label('+9.8V'))
d.add(e.Line().at(Q2A.collector).down(0.4)); d.add(G())
d.add(e.Resistor().at(Q3A.emitter).down(1.6).label('RX2 15',loc='top')); D2=d.here; d.add(e.Dot()); lbl(D2,'D2',loc='left',dx=-0.4,dy=-0.3)
d.add(e.Resistor().at(D2).down(1.8).label('RPD 360',loc='bottom')); d.add(G())
d.add(e.Line().at(Q3A.collector).up(0.4)); d.add(e.Vdd().label('+9.8V'))
# outputs
d.add(e.Line().at(D1).right(3.4)); Q2=d.add(e.BjtNpn(circle=True).anchor('base').label('Q2\n2N3904',loc='right'))
d.add(e.Line().at(D2).right(3.4)); Q3=d.add(e.BjtPnp(circle=True).anchor('base').label('Q3\n2N3906',loc='right'))
d.add(e.Resistor().at(Q2.collector).up(1.4).label('RC 4.7',loc='bottom')); vcf=d.here
d.add(e.Vdd().at(vcf).label('+9.8V')); 
d.add(e.Line().at(Q3.collector).down(0.4)); d.add(G())
d.add(e.Resistor().at(Q2.emitter).to((Q2.emitter[0],0.9)).label('RE3 3.3',loc='bottom'))
d.add(e.Resistor().at(Q3.emitter).to((Q3.emitter[0],-0.9)).label('RE4 3.3',loc='bottom'))
d.add(e.Line().at((Q2.emitter[0],0.9)).to((Q3.emitter[0],-0.9))); OUT=(Q2.emitter[0],0); d.add(e.Dot().at(OUT)); lbl(OUT,'OUT',loc='left',dx=-0.2,dy=0.35)
d.add(e.Line().at(OUT).right(1.5)); bus=d.here
for k,dy in enumerate([4.2,1.4,-1.4,-4.2]):
    d.add(e.Line().at(bus).to((bus[0],bus[1]+dy))); d.add(e.Capacitor().right().label(f'C{10+k} 4.7µ film',loc='top')); d.add(e.Resistor().right().label(f'RS{k+1} 51',loc='top')); d.add(e.Coax(length=2).right().label(f'J{k+2} OUT{k+1}',loc='right'))
# ---------------- NET-LABEL BLOCKS -----------------
def block(x,y,items,title=None):
    d.add(e.Label().at((x,y)).label(items[0],loc='left'))
    d.add(e.Line().at((x,y)).right(0.4))
    for kind,lab in items[1:]:
        if kind=='R': d.add(e.Resistor().right().label(lab,loc='top'))
        elif kind=='C': d.add(e.Capacitor().right().label(lab,loc='top'))
        elif kind=='N': d.add(e.Line().right(0.3)); d.add(e.Label().label(lab,loc='right'))
        elif kind=='G': d.add(G())
        elif kind=='V': d.add(e.Vdd().label(lab))
        elif kind=='T':
            d.add(e.Dot()); d.push(); d.add(e.Capacitor().down(1.6).label(lab[0],loc='bottom'))
            d.add(G() if lab[1]=='G' else e.Vdd().flip().label('+9.8V',loc='bottom')); d.pop()
yb=-15
d.add(e.Label().at((0,yb+4.2)).label('LPF: L1-L3 Bourns 78FR (±10%), VNA-selected to ±3% of nominal; C4-C7 C0G ±2%. Build A shown (RE 56, RF 220, RL 220).',loc='right'))
d.add(e.Label().at((0,yb+2.4)).label('Bias, feedback and AC load (join by net name). Electrolytics: 25 V.',loc='right'))
block(1,yb,['X',('R','R1A 1.5k'),('T',('10µ','G')),('R','R1B 1.5k'),('N','BN')])
block(1,yb-5,['BN',('R','R2 3.3k'),('G',None)])
block(15,yb,['X',('R','R3A 1.5k'),('T',('10µ','V')),('R','R3B 1.5k'),('N','BP')])
block(15,yb-5,['BP',('R','R4 3.3k'),('V','+9.8V')])
block(30,yb,['X',('R','RF 220'),('C','C8 2.2µ film'),('N','LPF')])
block(30,yb-5,['X',('C','C9 2.2µ film'),('R','RL 220'),('G',None)])
# ---------------- POWER -----------------
yp=-30
d.add(e.Label().at((0,yp+3.4)).label('Power: 13.8 V in (regulates down to ~12.1 V typ; 13.4 V for the 3 V datasheet headroom), +9.8 V rail',loc='right'))
d.add(e.Line().at((1,yp)).right(0.1)); d.add(e.Label().at((1,yp)).label('J6 +13.8V',loc='left'))
d.add(e.Resistor().at((1.1,yp)).right().label('F1 PTC RXEF030\n0.3 A hold',loc='top'))
d.add(e.Diode().right().label('D5 1N5819',loc='top')); a=d.here; d.add(e.Dot())
d.add(e.Capacitor().at(a).down().label('C20 220µ\n‖100n',loc='bottom')); d.add(G())
d.add(e.Line().at(a).right(0.8)); U=d.add(e.Ic(pins=[e.IcPin(name='IN',side='left'),e.IcPin(name='OUT',side='right'),e.IcPin(name='ADJ',side='bottom')],edgepadW=1.2,edgepadH=0.6).anchor('IN').label('U1 LM317T',loc='top'))
d.add(e.Line().at(U.OUT).right(0.6)); o=d.here; d.add(e.Dot())
# D6: OUT -> IN protection (anode OUT, cathode IN)
d.add(e.Line().at(o).up(2.2)); d.add(e.Line().to((a[0]+0.4,o[1]+2.2)))
d.add(e.Line().at((a[0]+0.4,o[1]+2.2)).right(0.01))
d.add(e.Diode().at((o[0],o[1]+2.2)).left(o[0]-a[0]-0.4 if o[0]-a[0]-0.4>1 else 2).label('D6 1N4002',loc='top'))
d.add(e.Line().to((a[0],o[1]+2.2))); d.add(e.Line().to(a))
d.add(e.Resistor().at(o).down().label('R10 240',loc='bottom')); adjn=d.here; d.add(e.Dot())
d.add(e.Line().at(U.ADJ).to((U.ADJ[0],adjn[1]))); d.add(e.Line().to(adjn))
d.add(e.Resistor().at(adjn).down().label('R11 1.65k',loc='bottom')); d.add(G())
d.add(e.Capacitor().at((U.ADJ[0],adjn[1])).down().label('C21 10µ',loc='bottom')); d.add(G())
d.add(e.Line().at(o).right(3.4)); o2=d.here; d.add(e.Dot())
# D7: ADJ -> OUT protection (anode ADJ, cathode OUT)
d.add(e.Line().at(adjn).right(2.0)); d.add(e.Diode().up(o[1]-adjn[1]).label('D7\n1N4002',loc='bottom')); d.add(e.Dot())
d.add(e.Capacitor().at(o2).down().label('C23 10µ',loc='bottom')); d.add(G())
d.add(e.Inductor2(loops=4).at(o2).right().label('L4 10µH\nRLB0914-100KL',loc='top'))
d.add(e.Resistor().right().label('RDAMP 1.0',loc='top')); r=d.here; d.add(e.Dot())
d.add(e.Capacitor().at(r).down().label('C22 470µ\n‖100n',loc='bottom')); d.add(G())
d.add(e.Line().at(r).right(0.8)); d.add(e.Vdd().label('+9.8V rail'))
d.add(e.Label().at((r[0]+3,yp-1.2)).label('Each transistor: 100 nF X7R to ground at its supply-side resistor.\nRC (4.7 Ω) is Q2 collector decoupling with its own 100 nF.\nPower-only bring-up: fit RDUMMY 100 Ω 3 W (ROX3SJ100R) rail to ground.',loc='right'))
d.save('schematic_revB.png',dpi=140); d.save('schematic_revB.svg')
