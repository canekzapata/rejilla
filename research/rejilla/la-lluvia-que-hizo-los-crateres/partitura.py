"""La lluvia que hizo los cráteres — partitura. Taiko × footwork de Chicago (160 bpm) × Pléiades de Xenakis, sobre el campo de impactos
18 de Traspuesta (41 cráteres) y dos poemas de Canek: «Planeta 9» (sólo lo conocemos por los objetos de roca y hielo que se reúnen
alrededor de un vacío) y el de la sonda (una triste roca de agua congelada golpeará la superficie… nuestra última esperanza).
Diseño en DISENO.md.

CADA CRÁTER ES UN TAMBOR (motor/crater.js): una membrana de Bessel con f₀₁ = K / D. La tónica de la canción es el cráter más grande
(1.8 km → 45 Hz). La lista de cráteres se reproduce exacta con la semilla del motor (terreno/terreno-18.json) y sus posiciones se
ajustan al encuadre de la lámina con una afín por los tres cráteres que el motor sí nombra. La posición en x es el paneo; la edad
(el orden de llegada) es el filo.
FORMA: I la lluvia (los 41 caen en su orden, cada vez más seguido) · II footwork · III taiko (sólo los dos complejos, con ma) ·
IV footwork y el gran impacto (un cráter nuevo borra los tambores que caen en su tazón) · V la aguja (los que quedan, lento).
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np

SEMILLA = 18
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__))
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-18.json'), encoding='utf-8'))
m_de = lambda f: 69 + 12 * math.log2(f / 440)
CR = TER['crateres']; n = len(CR); DMAX = max(c['D'] for c in CR); K = 45 * DMAX       # el más grande da 45 Hz
TON = m_de(45)
# ── las posiciones al encuadre de la lámina: afín por los tres cráteres que el motor nombra (los tres más grandes) ──
grandes = sorted(CR, key=lambda c: -c['D'])[:3]; esp = [e for e in TER['especiales'] if 'CRÁTER' in e['term']][:3]
A = np.array([[c['x'], c['y'], 1] for c in grandes]); Bx = np.array([e['u'] for e in esp]); By = np.array([e['v'] for e in esp])
ax, ay = np.linalg.solve(A, Bx), np.linalg.solve(A, By)
TAMBORES = {}
for c in CR:
    u, v = float(np.dot([c['x'], c['y'], 1], ax)), float(np.dot([c['x'], c['y'], 1], ay))
    fam = 'complejo' if c['complejo'] else 'mediano' if c['D'] > 600 else 'chico' if c['D'] > 350 else 'diminuto'
    TAMBORES[str(c['k'])] = dict(D=c['D'], complejo=c['complejo'], edad=round(1 - c['k'] / (n - 1), 3), u=round(u, 4), v=round(v, 4), f=round(K / c['D'], 2), familia=fam, pan=round(np.clip(2 * u - 1, -.9, .9), 3))
FAM = {f: sorted([k for k, t in TAMBORES.items() if t['familia'] == f], key=lambda k: -TAMBORES[k]['D']) for f in ('complejo', 'mediano', 'chico', 'diminuto')}

BPM = 160; Q = 60 / BPM; BAR = 4 * Q; S16 = Q / 4
SEC = {}; t0 = 0.0
for nom, dur in (('I', 40.0), ('II', 32 * BAR), ('III', 30.0), ('IV', 24 * BAR), ('V', 34.0)): SEC[nom] = (round(t0, 3), round(t0 + dur, 3)); t0 += dur
DUR = t0 + 4
golpes = {f: [] for f in FAM}; golpes['grande'] = []
def golpe(k, t, v, r=.4, choque=0):
    tb = TAMBORES[k]; golpes[tb['familia']].append(dict(t=round(t, 4), id=k, v=round(v, 3), r=round(r, 3), pan=tb['pan'], choque=choque))

# ═════════ I · la lluvia: los 41 caen en su orden, cada vez más seguido (Poisson que se acelera) ═════════
a, b = SEC['I']; gaps = [R.expovariate(1) * (1 - k / n) ** 1.4 for k in range(n)]; esc = (b - a - 4) / sum(gaps); t = a + 1.5
caida = {}
for c in CR:
    k = str(c['k']); t += gaps[c['k']] * esc; caida[k] = t
    golpe(k, t, .55 + .45 * math.log(c['D'] / 200) / math.log(DMAX / 200), 0.0, choque=round(min(1, c['D'] / DMAX), 2) if c['D'] > 700 else 0)
polvo = [[a, 0], [a + 2, .2], [b - 6, 1], [b, .4], [SEC['II'][1], .15], [SEC['III'][1], .3], [SEC['IV'][0] + 16 * BAR, 1], [SEC['V'][0], .5], [DUR, .15]]

# ═════════ II y IV · footwork ═════════
ev = {k: [] for k in ['bateria', 'bateria-frito']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr808', stem='bateria'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)
PENTA = [0, 3, 5, 7, 10]
def pm(g, o=0): k, r = divmod(g, 5); return TON + 12 * (o + k) + PENTA[r]
sub, chops, coro, susurro, viva, coros = [], [], [], [], [], {v: [] for v in 'SAT'}
KICKS = [[0, 3, 6, 10, 13], [0, 3, 8, 11, 14]]
def footwork(b, vivos, denso=False):
    t = lambda s: SEC_B0 + b * BAR + s * S16
    for s in KICKS[b % 2]:
        golpe(FAM['complejo'][0 if s in (0, 6, 10) else 1], t(s), .95 if s == 0 else .8, .15)   # los dos complejos de bombo
        sub.append(dict(t=round(t(s), 4), dur=round(2.5 * S16, 4), midi=round(pm([0, 0, 2, 0, 3][s % 5], 1), 3), vel=.9))
    for s in (4, 12): web('bateria-frito', t(s), 'bateria-frito', 60, .85, .2, 0, pieza='clap')
    dim = [k for k in FAM['diminuto'] if k in vivos]
    for s in range(16):                                                        # los diminutos de hats, rotando por el campo
        if s % 2 == 0 or R.random() < (.6 if denso else .35): golpe(dim[(s + 3 * b) % len(dim)], t(s), .35 + .25 * (s % 4 == 2), .8)
    if b % 2 == 1:                                                             # la ráfaga
        for q in range(6 if not denso else 10): golpe(dim[q % len(dim)], t(12 + q * (4 / (6 if not denso else 10))), .3 + .05 * q, .85)
    med = [k for k in FAM['mediano'] if k in vivos] or [k for k in FAM['chico'] if k in vivos]; chi = [k for k in FAM['chico'] if k in vivos] or dim
    for j, s in enumerate((2, 7, 9, 15)): golpe(med[(j + b) % len(med)], t(s), .65, .5)
    for s in (1, 5, 11): golpe(chi[(s + b) % len(chi)], t(s), .4, .6)
    if b % 4 == 3:                                                             # tom roll que baja por los medianos
        for q, k in enumerate(sorted(med, key=lambda k: TAMBORES[k]['D'])[:6]): golpe(k, t(10 + q), .7 + .05 * q, .5)
    if denso:
        for s in range(0, 16, 1): bat(t(s + .5), 'hat', .18 + .1 * (s % 4 == 0), -.3)
        if b % 2 == 0: web('bateria-frito', t(14), 'bateria-frito', 60, .7, .2, .3, pieza='spray')
CHOP = [('gol', 0), ('gol', 1), ('gol', 2), ('pe', 3), ('a', 6), ('rá', 8), ('gol', 10), ('gol', 11), ('pe', 12), ('a', 13), ('rá', 14)]
def chop_bar(b, transp=0):
    for i, (sy, s) in enumerate(CHOP): chops.append(dict(t=round(SEC_B0 + b * BAR + s * S16, 4), dur=round(S16 * .8, 4), texto=sy, nota=round(pm([4, 4, 4, 3, 2, 3, 4, 4, 3, 2, 0][i], 3) + transp, 3)))
def coro_frase(texto, b, alturas, ritmo):
    t = SEC_B0 + b * BAR
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; sop = alturas[i % len(alturas)]
        for v, x in zip('SAT', (0, -5, -10)): coros[v].append(dict(t=round(t, 4), dur=round(d * .9, 4), texto=sy, nota=round(sop + x, 3)))
        coro.append(dict(t=round(t, 4), dur=round(d * .9, 4), texto=sy, nota=round(sop, 3))); t += d
TODOS = set(TAMBORES)
SEC_B0 = SEC['II'][0]
for b in range(32):
    footwork(b, TODOS, denso=b >= 24)
    if 8 <= b < 16 or b >= 28: chop_bar(b)
coro_frase('só lo lo co no ce mos', 16, [pm(4, 3), pm(4, 3), pm(3, 3), pm(2, 3), pm(3, 3), pm(2, 3), pm(0, 3)], [2, 2, 2, 2, 2, 2, 12])
coro_frase('por los ob je tos', 18, [pm(2, 3), pm(3, 3), pm(4, 3), pm(5, 3), pm(4, 3)], [2, 2, 2, 2, 8])
coro_frase('de ro ca y hie lo', 20, [pm(5, 3), pm(4, 3), pm(3, 3), pm(2, 3), pm(3, 3), pm(0, 3)], [2, 2, 2, 2, 4, 12])
coro_frase('que se re ú nen al re de dor de un va cí o', 22, [pm(x, 3) for x in (0, 2, 3, 4, 5, 4, 3, 2, 3, 2, 0, -1, 0)], [1, 1, 2, 2, 2, 1, 1, 2, 2, 1, 1, 4, 12])
# ═════════ III · taiko: los dos complejos, con ma; el kiai; el viento ═════════
a, b = SEC['III']; t = a + .8; garganta = []; lado = 0
GOLPES_T = [(0, 1), (1.2, .7), (3.5, 1), (4.1, .6), (4.6, .6), (7.5, 1), (9.8, .9), (10.4, .5), (13.6, 1), (15.2, .8), (15.8, .8), (16.4, .8), (19.5, 1), (22.8, .9), (23.3, .7), (26.5, 1)]
for dt, v in GOLPES_T:
    k = FAM['complejo'][lado % 2]; golpe(k, a + dt, v, R.choice([.05, .3, .6]), choque=.6 if v == 1 else 0); lado += 1
    if v == 1: garganta.append(dict(t=round(a + dt - .25, 3), dur=.35, nota=round(TON + 24 + 5, 3), fonemas=['x', 'a'] if lado % 2 else ['y', 'o'], v=.95, aprende=.8, ronco=.9))
VIENTO = dict(vel=[[0, 0], [a - .1, 0], [a, 7], [a + 15, 12], [b, 5], [SEC['V'][0], 4], [DUR, 2]], estria=[[0, 1], [DUR, 1]], escala=PENTA, periodo=12, base=round(TON + 36, 3))
# ═════════ IV · footwork y el gran impacto ═════════
SEC_B0 = SEC['IV'][0]; GRAN_B = 16; t_gran = SEC_B0 + GRAN_B * BAR
med_uv = np.mean([[TAMBORES[k]['u'], TAMBORES[k]['v']] for k in FAM['mediano']], axis=0)
GRAN = dict(D=int(DMAX * 1.35), u=round(float(med_uv[0]), 4), v=round(float(med_uv[1]), 4)); radio = GRAN['D'] / 2 / (TER['anchoKm'] * 1000)
BORRADOS = sorted([k for k, tb in TAMBORES.items() if math.hypot(tb['u'] - GRAN['u'], tb['v'] - GRAN['v']) < radio * 1.1 and tb['familia'] != 'complejo'])
TAMBORES['grande'] = dict(D=GRAN['D'], complejo=True, edad=0, u=GRAN['u'], v=GRAN['v'], f=round(K / GRAN['D'], 2), familia='grande', pan=round(2 * GRAN['u'] - 1, 3))
VIVOS = TODOS - set(BORRADOS)
for b in range(24):
    if b == GRAN_B: continue                                                    # un compás de silencio después del golpe
    footwork(b, TODOS if b < GRAN_B else VIVOS, denso=b < GRAN_B)
    if b < GRAN_B and b % 2 == 0: chop_bar(b, 0 if b < 8 else 3)
golpes['grande'].append(dict(t=round(t_gran, 4), id='grande', v=1.0, r=0.0, pan=TAMBORES['grande']['pan'], choque=1.0))
coro_frase('u na tris te ro ca', 4, [pm(x, 3) for x in (4, 4, 3, 2, 0, 2)], [2, 2, 4, 2, 2, 12])
coro_frase('com pues ta de a gua con ge la da', 8, [pm(x, 3) for x in (2, 3, 4, 3, 2, 3, 4, 5, 4, 2)], [2, 2, 2, 1, 1, 2, 2, 2, 2, 12])
coro_frase('gol pe a rá la su per fi cie', 12, [pm(x, 3) for x in (5, 5, 4, 3, 2, 3, 2, 0, -1, 0)], [1, 1, 1, 3, 2, 2, 2, 2, 2, 12])
# ═════════ V · la aguja: los que quedan, cada uno a su periodo (del tamaño), y se apagan ═════════
a, b = SEC['V']
for k in sorted(VIVOS, key=lambda k: -TAMBORES[k]['D']):
    tb = TAMBORES[k]; per = .35 + 1.6 * tb['D'] / DMAX; t = a + R.uniform(0, per)
    while t < b - 1: golpe(k, t, .5 * (1 - (t - a) / (b - a)) ** 1.5 + .05, .5); t += per
sonda = [dict(t=round(a + 2 + 3.1 * i, 3), midi=round(pm([7, 9, 8, 10, 7, 12, 9, 7, 10, 8][i % 10], 2), 3), dur=2.5, vel=.5 - .03 * i, pan=round(.6 * math.sin(i), 3)) for i in range(10)]
for txt, tt, alt, rit in (('nues tra úl ti ma', a + 8, [pm(x, 2) for x in (4, 3, 4, 2, 0)], [.45, .45, .9, .45, 1.6]), ('es pe ran za', a + 14, [pm(x, 2) for x in (2, 3, 2, 0)], [.5, .5, .9, 3.0])):
    for sy, m, d in zip(txt.split(), alt, rit): viva.append(dict(t=round(tt, 3), dur=round(d * .95, 3), texto=sy, nota=round(m, 3))); tt += d
# ═════════ el susurro (I): Planeta 9 ═════════
for txt, tt in (('el pla ne ta nue ve no se pue de ver', 12.0), ('ha bi ta en tre un cú mu lo de hie los', 26.0)):
    for i, sy in enumerate(txt.split()): susurro.append(dict(t=round(tt + i * .28, 3), dur=.26, texto=sy, nota=round(pm(2 if i < len(txt.split()) - 1 else 0, 2), 3)))

partitura = dict(titulo='La lluvia que hizo los cráteres', semilla=SEMILLA, terreno=f"traspuesta 18 «{TER['nombre']}», {TER['anchoKm']} km, {n} cráteres", K=K, tonica=round(TON, 3), bpm=BPM,
                 compas=BAR, dieciseisavo=S16, secciones=[dict(num=k, t=v[0], t1=v[1]) for k, v in SEC.items()], duracion=round(DUR, 3), tambores=TAMBORES, familias=FAM, golpes=golpes,
                 caida={k: round(v, 3) for k, v in caida.items()}, gran=dict(GRAN, t=round(t_gran, 3), radio=round(radio, 4), borrados=BORRADOS), polvo=polvo, web=ev, sub=sub, garganta=garganta,
                 viento=VIENTO, sonda=sonda, sabina=[dict(eventos=susurro, nivel=.8, pan=0, capa='susurro'), dict(eventos=chops, nivel=.9, pan=0, capa='chops'),
                 dict(eventos=coro, nivel=.85, pan=0, capa='coro'), dict(eventos=viva, nivel=.85, pan=0, capa='viva')], coros=coros,
                 instrumentos='instrumentos-36bae82e7154', tres_tiempos_codigo='tres-tiempos-6b17c3ba5aa8')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', round(DUR, 1), 's · tónica', round(TON, 2), '(45 Hz) · K', K, '· secciones', SEC)
    print('familias', {f: len(v) for f, v in FAM.items()}, '· golpes', {f: len(v) for f, v in golpes.items()}, '· borrados por el gran impacto', len(BORRADOS), BORRADOS)
    print('gran impacto', GRAN, '→', TAMBORES['grande']['f'], 'Hz · chops', len(chops), '· coro', len(coro))
