"""El coral que no se deja hundir — partitura. Exotica oscura (Martin Denny y sus pájaros) × hyperpop × los pájaros de Messiaen,
sobre el atolón 2 de Traspuesta, «El Banco de las Fragatas». Diseño en DISENO.md.

DOS MOVIMIENTOS CONTRARIOS (Darwin): el volcán se hunde (su altura baja de verdad, una octava cada 100 s) y el coral sube a la luz
(la copa del arrecife sube a la misma velocidad, al revés). Se cruzan a media canción en la misma nota: el batido llega a cero.
EL NIVEL DEL MAR ES LA LUZ: lo que está bajo el agua suena apagado. El volcán se apaga al hundirse; el coral se enciende al salir.
EL ANILLO ES UN COLLAR RÍTMICO: los islotes (motus) del anillo, leídos en ángulo, son los golpes de un ciclo de 32 dieciseisavos
(dos compases); la Boca Grande (el paso) es el silencio y el güiro que la raspa.
LA TÓNICA es el seiche de la laguna (la ola estacionaria de la laguna: c = √(g·h), f = c / 2D), subido por octavas.
TEMA V (el volcán, baja): 12, 10, 7, 5, 3, 0.  TEMA C (el coral, sube): su inversión, 0, 2, 5, 7, 9, 12.
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np

SEMILLA = 2
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__)); G = 360
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-2.json'), encoding='utf-8'))
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-2.f32'), dtype=np.float32).reshape(G, G).astype(float)
HF = np.fromfile(os.path.join(AQUI, 'terreno', 'fondo-2.f32'), dtype=np.float32).reshape(G, G).astype(float)
m_de = lambda f: 69 + 12 * math.log2(f / 440)
fT = lambda m: 440 * 2 ** ((m - 69) / 12)

# ── la lámina: los islotes en ángulo, la laguna, el seiche ──
tierra = H > TER['umbralMar']; ys, xs = np.nonzero(tierra); cy, cx = ys.mean(), xs.mean()
km = TER['anchoKm'] * 1000 / (G - 1)
ang = (np.degrees(np.arctan2(ys - cy, xs - cx)) + 360) % 360; rad = np.hypot(ys - cy, xs - cx) * km
B = 720; arco = np.zeros(B, bool); arco[(ang / 360 * B).astype(int) % B] = True
ISLOTES = []                                                                    # (centro en grados, ancho en grados)
k = 0
while k < B:
    if arco[k] and not arco[k - 1]:
        j = k
        while arco[(j + 1) % B]: j += 1
        a, z = k * 360 / B, (j + 1) * 360 / B; ISLOTES.append(((a + z) / 2 % 360, z - a)); k = j + 1
    else: k += 1
ISLOTES.sort()
huecos = sorted(((ISLOTES[(i + 1) % len(ISLOTES)][0] - ISLOTES[i][0]) % 360, i) for i in range(len(ISLOTES)))
BOCA = ((ISLOTES[huecos[-1][1]][0] + huecos[-1][0] / 2) % 360, huecos[-1][0])  # el hueco más grande: la Boca Grande
R_ANILLO = float(np.median(rad))
dentro = np.hypot(*np.mgrid[0:G, 0:G] - np.array([[[cy]], [[cx]]])) * km < R_ANILLO * .85
prof_laguna = float(np.mean(np.clip(TER['umbralMarFondo'] - HF[dentro], 0, None)) * TER['relieveFondo'])
c_onda = math.sqrt(9.81 * max(prof_laguna, 1)); f_seiche = c_onda / (2 * 2 * R_ANILLO)
octavas = 0; f = f_seiche
while f < 55: f *= 2; octavas += 1
TON = m_de(f)                                                                   # la tónica (seiche subido por octavas)

TEMA_V = [12, 10, 7, 5, 3, 0]; TEMA_C = [0, 2, 5, 7, 9, 12]
FRIGIO = [0, 1, 3, 5, 7, 8, 10]
def tv(i, o=0): k, r = divmod(i, 6); return TON + 12 * (o - k) + TEMA_V[r]
def tc_(i, o=0): k, r = divmod(i, 6); return TON + 12 * (o + k) + TEMA_C[r]
def gr(g, o=0): k, r = divmod(g, 7); return TON + 12 * (o + k) + FRIGIO[r]
MODO3 = [0, 2, 3, 4, 6, 7, 8, 10, 11]
def m3(g, o=0): k, r = divmod(g, 9); return TON + 12 * (o + k) + MODO3[r]

BPM = 100; Q = 60 / BPM; BAR = 4 * Q; S16 = Q / 4
SEC = {}; t0 = 0.0
for nom, nb in (('I', 16), ('II', 20), ('III', 12), ('IV', 24), ('V', 18)): SEC[nom] = (round(t0, 3), round(t0 + nb * BAR, 3)); t0 += nb * BAR
DUR = round(t0 + 8, 3)
def ts(sec, b, s=0.0): return SEC[sec][0] + b * BAR + s * S16
TC = (SEC['III'][0] + SEC['III'][1]) / 2                                        # el cruce
T8 = 100.0                                                                      # segundos por octava
F_X = fT(TON + 12)                                                              # la nota del cruce (la tónica, una octava arriba)
fv = lambda t: F_X * 2 ** ((TC - t) / T8)                                       # el volcán baja
fc = lambda t: F_X * 2 ** ((t - TC) / T8)                                       # el coral sube

# ═════════ el volcán: su altura, su profundidad bajo el mar, su vocal, su borrado ═════════
VOLCAN = dict(f=[[round(t, 2), round(fv(t), 4)] for t in np.linspace(0, DUR, 200)],
              prof=[[0, -40], [SEC['II'][0] + 24, 0], [SEC['III'][1], 90], [DUR, 220]],                # metros bajo el agua
              vocal=[[0, 0], [SEC['II'][1], 1], [SEC['IV'][1], 2], [DUR, 2]],
              theta=[[0, 0], [SEC['V'][0] + 6, 0], [SEC['V'][0] + 26, 2 * math.pi], [DUR, 2 * math.pi]])  # la vuelta que borra

# ═════════ el coral: crece por agregación; la copa sube con fc ═════════
CORAL = dict(W=120, H=64, n=1500, semilla=SEMILLA, inicio=6.0,
             base=[int(4 + 8 * math.exp(-((x - 60) / 26) ** 2)) for x in range(120)])      # el flanco del volcán viejo

# ═════════ el collar rítmico (32 dieciseisavos = 2 compases) ═════════
COLLAR = []
for a, w in ISLOTES:
    s = int(round(((a - BOCA[0] + 180) % 360) / 360 * 32)) % 32                # el ciclo empieza enfrente de la boca
    COLLAR.append(dict(paso=s, peso=round(min(1.0, w / max(x[1] for x in ISLOTES)), 3)))
paso_boca = 16
ev = {k: [] for k in ['congas', 'guiro', 'shaker', 'vibrafono', 'marimba', 'steelpan', 'teponaztli', 'bateria808', 'bateria-frito']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def collar(t_ini, ciclos, fuerza=1.0, doble=False):
    for c in range(ciclos):
        for e in COLLAR:
            tt = t_ini + c * 2 * BAR + e['paso'] * S16 + R.gauss(0, .004)
            grave = e['peso'] > .6
            web('congas', tt, 'meleeviewer-13-conga', 60 if grave else 67, (.5 + .45 * e['peso']) * fuerza, .2, -.25 if grave else .3)
            if doble and R.random() < .5: web('congas', tt + S16 / 2, 'meleeviewer-13-conga', 72, .35 * fuerza, .1, .4)
        g0 = t_ini + c * 2 * BAR + paso_boca * S16
        web('guiro', g0, 'meleeviewer-13-guiro', 60, .55 * fuerza, BOCA[1] / 360 * 32 * S16, .15)           # la boca: el güiro la raspa
PROG = [[0, 3, 7, 10], [0, 3, 7, 10], [1, 5, 8, 12], [1, 5, 8, 12], [5, 8, 12, 15], [8, 12, 15, 19], [7, 10, 13, 17], [1, 5, 8, 12]]   # i, i, bII, bII, iv, bVI, v°, bII
def acorde(b): return PROG[b % 8]
def exotica(sec, b0, b1, vib=True, mar=True, steel=False):
    for b in range(b0, b1):
        t = ts(sec, b); ac = acorde(b)
        if vib:                                                                 # vibráfono grave en los «y» del 2 y del 4 (beguine)
            for s in (6, 14):
                for i, x in enumerate(ac): web('vibrafono', t + s * S16 + i * .012, 'vibrafono', TON + 12 + x, .45, 1.6, -.2 + .13 * i)
        if mar:                                                                 # la marimba grave: el bajo del beguine (1, 2y, 3)
            for s, x in ((0, ac[0]), (6, ac[2] - 12), (8, ac[0])): web('marimba', t + s * S16, 'marimba', TON + x, .7, .5, 0)
        if steel and b % 2 == 0:
            for i in range(6): web('steelpan', t + i * 2 * S16, 'steelpan', tc_(i, 1), .4, .3, .3)
def teponaztli(sec, b0, b1):
    for b in range(b0, b1, 2):
        for e in COLLAR:
            if e['peso'] > .8: web('teponaztli', ts(sec, b) + e['paso'] * S16, 'teponaztli', TON + 12 + (7 if e['paso'] > 16 else 0), .5, .4, -.4)
def shaker(sec, b0, b1, div=2, v=.25):
    for b in range(b0, b1):
        for s in range(0, 16, div): web('shaker', ts(sec, b, s) + R.gauss(0, .003), 'meleeviewer-2-shaker', 60, v * (1.3 if s % 4 == 2 else 1), .1, .35)

# I · la isla alta: collar suave, exotica entra a la mitad
collar(ts('I', 4), 6, .7); exotica('I', 8, 16, vib=True, mar=False); shaker('I', 8, 16, 4, .2)
# II · el hundimiento: beguine completo
collar(ts('II', 0), 10, .9); exotica('II', 0, 20); shaker('II', 0, 20, 2, .22); teponaztli('II', 4, 20)
# III · el cruce: el collar sigue (y el tapete de Talbot lo transforma en la mezcla), la exotica se adelgaza
collar(ts('III', 0), 6, .9); exotica('III', 0, 12, vib=True, mar=False)
# IV · el arrecife: hyperpop a doble tiempo
collar(ts('IV', 0), 12, 1.0, doble=True); exotica('IV', 0, 24, vib=True, mar=True, steel=True); shaker('IV', 0, 24, 1, .18); teponaztli('IV', 0, 24)
sub = []
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr808', stem='bateria808'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)
for b in range(24):
    t = ts('IV', b)
    for s in (0, 3, 6, 10, 11, 14): bat(t + s * S16, 'kick', .95 if s in (0, 6) else .75)
    for s in (4, 12): bat(t + s * S16, 'snare', .85, .05); web('bateria-frito', t + s * S16 + .008, 'bateria-frito', 60, .5, .2, -.1, pieza='clap')
    for s in range(16): bat(t + s * S16, 'hat', .3 + .2 * (s % 2 == 0), .3)
    if b % 4 == 3:                                                              # el redoble hyperpop que acelera (32avos → 64avos)
        k, tt = 0, t + 12 * S16
        while tt < t + BAR - .01: bat(tt, 'snare', .4 + .5 * k / 20, .05); tt += S16 / 2 * (.97 ** k); k += 1
    ac = acorde(b)
    for s, d, x in ((0, 3, ac[0]), (6, 2, ac[0]), (10, 4, ac[2] - 12)): sub.append(dict(t=round(t + s * S16, 4), dur=round(d * S16, 4), midi=round(TON - 12 + x, 3), vel=.9))
for b in range(0, 20, 2):                                                       # en II el 808 empieza a bajar con el volcán (sólo el 1)
    t = ts('II', b); sub.append(dict(t=round(t, 4), dur=round(6 * S16, 4), midi=round(m_de(fv(t)) - 24, 3), vel=.7))
for b in range(4, 18, 2): sub.append(dict(t=round(ts('V', b), 4), dur=round(10 * S16, 4), midi=round(TON - 12, 3), vel=.55))
# el tapete de Talbot sobre el collar en III (se aplica en la mezcla: τ = 1/2, 1/3, 1/4, exacto)
TALBOT = dict(loop_desde=round(ts('II', 8), 4), ciclo=round(2 * BAR, 4), tramos=[[SEC['III'][0], '1/2'], [ts('III', 4), '1/3'], [ts('III', 8), '1/4'], [SEC['III'][1], '0']])

# ═════════ las olas: cada una se parte en n solitones en el arrecife ═════════
OLAS = []
for sec, cada, nmin, nmax in (('I', 4, 1, 2), ('II', 2, 2, 3), ('III', 2, 3, 3), ('IV', 1, 3, 5), ('V', 4, 1, 2)):
    a, z = SEC[sec]; b = 0
    while a + b * BAR < z - BAR:
        OLAS.append(dict(t=round(a + b * BAR + R.uniform(0, .3), 3), n=R.randint(nmin, nmax), dur=round(BAR * (1.6 if sec != 'IV' else 1.0), 3))); b += cada

# ═════════ los pájaros ═════════
aves = []                                                                       # las fragatas a lo Messiaen (pajaro.js, modo 3)
def canto(t, o, n, v=.5, voz=0):
    notas = []; dt = 0
    for i in range(n):
        d = R.choice([.05, .07, .09, .12, .2]); notas.append([round(dt, 3), round(m3(R.randint(4, 14), o), 3), d]); dt += d
    aves.append(dict(t=round(t, 3), tipo='canto', notas=notas, dur=round(dt + .1, 3), m=notas[0][1], v=v, voz=voz))
for sec, cuantos, o in (('I', 4, 4), ('II', 8, 4), ('IV', 26, 4), ('V', 5, 5)):
    for _ in range(cuantos):
        t = R.uniform(SEC[sec][0] + 2, SEC[sec][1] - 2); canto(t, o, R.randint(5, 14), R.uniform(.35, .6), R.randint(0, 1))
        if R.random() < .4: aves.append(dict(t=round(t + R.uniform(.5, 2), 3), tipo='trino', m=round(m3(R.randint(8, 12), 4), 3), m2=round(m3(R.randint(5, 9), 4), 3), dur=.6, rate=R.choice([14, 18, 22]), v=.4, voz=1))
boca = []                                                                       # los pájaros de boca (Denny): I, II, y contra Messiaen en IV
for sec, cuantos in (('I', 10), ('II', 14), ('IV', 12), ('V', 4)):
    for _ in range(cuantos):
        t = R.uniform(SEC[sec][0] + 1, SEC[sec][1] - 2); tipo = R.choice(['silbido', 'silbido', 'trino', 'chasquido', 'buho'])
        if tipo == 'silbido': boca.append(dict(t=round(t, 3), tipo=tipo, m=round(gr(R.randint(14, 18)), 3), m2=round(gr(R.randint(16, 21)), 3), dur=round(R.uniform(.25, .6), 3), v=.6, pan=round(R.uniform(-.7, .7), 2)))
        elif tipo == 'trino': boca.append(dict(t=round(t, 3), tipo=tipo, m=round(gr(R.randint(17, 20)), 3), dur=round(R.uniform(.4, .9), 3), rate=R.choice([20, 24, 28]), v=.5, pan=round(R.uniform(-.7, .7), 2)))
        elif tipo == 'chasquido': boca.append(dict(t=round(t, 3), tipo=tipo, n=R.randint(2, 6), cada=round(R.uniform(.06, .12), 3), dur=.8, v=.6, pan=round(R.uniform(-.7, .7), 2)))
        else: boca.append(dict(t=round(t, 3), tipo=tipo, m=round(TON + 24 + R.choice([0, 3]), 3), dur=.55, v=.55, pan=round(R.uniform(-.5, .5), 2)))

# ═════════ las burbujas (cueva.js): el volcán desgasifica al hundirse; la laguna ═════════
CAMARAS = {'laguna': dict(fh=round(fT(TON + 12), 2), fb=round(fT(TON + 31), 2), q=18, pan=0, eco=.7),
           'flanco': dict(fh=round(fT(TON + 19), 2), fb=round(fT(TON + 36), 2), q=12, pan=-.4, eco=.5)}
gotas = []; t = SEC['II'][0] + 10
while t < SEC['IV'][0]:
    u = (t - SEC['II'][0]) / (SEC['IV'][0] - SEC['II'][0])
    gotas.append(dict(t=round(t, 4), id=R.choice(['flanco', 'flanco', 'laguna']), r=round(R.uniform(2, 6) * (1 + u), 3), v=round(R.uniform(.3, .8), 3))); t += R.expovariate(1.2 + 5 * u)
for _ in range(60):
    t = R.uniform(SEC['V'][0], DUR - 3); gotas.append(dict(t=round(t, 4), id='laguna', r=round(R.uniform(1.5, 3), 3), v=round(R.uniform(.2, .5), 3)))
gotas.sort(key=lambda g: g['t'])

LAGUNA = dict(f=round(fT(TON), 4), curva=[[0, 0], [SEC['III'][0], 0], [TC, .6], [SEC['IV'][0], .4], [SEC['V'][0], .7], [DUR - 3, .7], [DUR, 0]])
LUCIERNAGAS = dict(t0=SEC['V'][0] + 4, t1=DUR - 2, f_pulso=BPM / 60 / 2, K=[[SEC['V'][0], .3], [SEC['V'][0] + 20, 1.8], [DUR, 2.4]],
                   notas=[round(m3(g, 3), 3) for g in range(0, 18)])

# ═════════ las voces (Sabina) ═════════
lead, coro, chops, coros = [], [], [], {v: [] for v in 'SATB'}
def frase(dest, texto, t, alturas, ritmo, legato=.92, **kw):
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; dest.append(dict(t=round(t, 4), dur=round(d * legato, 4), texto=sy, nota=round(alturas[i % len(alturas)], 3), **kw)); t += d
    return t
V1 = [('la is la se hun de un de do ca da si glo', [tv(0, 1), tv(0, 1), tv(1, 1), tv(1, 1), tv(2, 1), tv(2, 1), tv(3, 1), tv(2, 1), tv(3, 1), tv(4, 1), tv(4, 1), tv(5, 1), tv(5, 1)], [2, 2, 3, 2, 4, 2, 2, 3, 2, 2, 3, 2, 9]),
      ('na die la em pu ja na die la de tie ne', [tv(2, 1), tv(2, 1), tv(3, 1), tv(3, 1), tv(4, 1), tv(3, 1), tv(2, 1), tv(2, 1), tv(3, 1), tv(4, 1), tv(4, 1), tv(5, 1), tv(5, 1)], [2, 2, 2, 3, 3, 4, 2, 2, 2, 3, 3, 2, 10])]
V2 = [('a ba jo el co ral no pe le a con el a gua', [tc_(0, 1), tc_(0, 1), tc_(1, 1), tc_(1, 1), tc_(2, 1), tc_(2, 1), tc_(1, 1), tc_(2, 1), tc_(3, 1), tc_(2, 1), tc_(3, 1), tc_(3, 1), tc_(4, 1), tc_(3, 1)], [2, 2, 3, 2, 2, 5, 2, 2, 2, 3, 2, 2, 3, 9]),
      ('no más cre ce lo que el a gua se lle va', [tc_(1, 1), tc_(2, 1), tc_(2, 1), tc_(3, 1), tc_(3, 1), tc_(4, 1), tc_(4, 1), tc_(5, 1), tc_(4, 1), tc_(3, 1), tc_(4, 1), tc_(5, 1)], [2, 4, 2, 3, 2, 2, 2, 3, 3, 2, 3, 10])]
for i, (txt, alt, rit) in enumerate(V1): frase(lead, txt, ts('I', 6 + 5 * i), alt, rit)
for i, (txt, alt, rit) in enumerate(V2): frase(lead, txt, ts('II', 4 + 5 * i), alt, rit)
def coral_voces(texto, t, mel, ritmo):
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; sop = mel[i % len(mel)]
        for v, x in zip('SATB', (0, -5, -8, None)): coros[v].append(dict(t=round(t, 4), dur=round(d * .9, 4), texto=sy, nota=round(sop + x if x is not None else TON + 12, 3)))
        coro.append(dict(t=round(t, 4), dur=round(d * .9, 4), texto=sy, nota=round(sop, 3))); t += d
    return t
LUZ = ('la lu ciér na ga no se a pa ga', [tc_(0, 2), tc_(1, 2), tc_(2, 2), tc_(2, 2), tc_(3, 2), tc_(3, 2), tc_(4, 2), tc_(5, 2), tc_(4, 2), tc_(5, 2)], [2, 2, 4, 2, 4, 2, 2, 3, 3, 8])
HUNDIR = ('no se de ja hun dir', [tc_(5, 2), tc_(4, 2), tc_(3, 2), tc_(4, 2), tc_(5, 2), tc_(6, 2)], [3, 2, 3, 2, 4, 14])
for b in (1, 7): t = coral_voces(LUZ[0], ts('III', b), LUZ[1], LUZ[2]); coral_voces(HUNDIR[0], t + S16 * 2, HUNDIR[1], HUNDIR[2])
for b in (4, 12, 20): t = coral_voces(LUZ[0], ts('IV', b), LUZ[1], LUZ[2]); coral_voces(HUNDIR[0], t + S16 * 2, HUNDIR[1], HUNDIR[2])
for b in list(range(0, 4)) + list(range(8, 12)) + list(range(16, 20)):           # chops hyperpop (arriba, troceados)
    for s, sy, x in ((2, 'lu', 0), (3, 'ciér', 2), (6, 'na', 5), (7, 'ga', 7), (10, 'su', 9), (11, 'be', 12), (14, 'su', 9)):
        if R.random() < .8: chops.append(dict(t=round(ts('IV', b, s), 4), dur=round(S16 * .85, 4), texto=sy, nota=round(TON + 31 + x, 3)))
FINAL = [('que da un a ni llo don de hu bo un mon te', [tv(0, 1), tv(1, 1), tv(1, 1), tv(2, 1), tv(2, 1), tv(3, 1), tv(2, 1), tv(3, 1), tv(4, 1), tv(4, 1), tv(5, 1), tv(5, 1), tv(5, 1)], [2, 2, 3, 2, 2, 4, 2, 2, 2, 3, 2, 3, 9]),
         ('y en el a ni llo la luz', [tc_(0, 1), tc_(1, 1), tc_(2, 1), tc_(2, 1), tc_(3, 1), tc_(4, 1), tc_(5, 1), tc_(6, 1)], [2, 2, 2, 2, 4, 2, 3, 24])]
for i, (txt, alt, rit) in enumerate(FINAL):
    frase(lead, txt, ts('V', 4 + 6 * i), alt, rit)
coral_voces(FINAL[1][0], ts('V', 10), [a + 12 for a in FINAL[1][1]], FINAL[1][2])

partitura = dict(titulo='El coral que no se deja hundir', semilla=SEMILLA, terreno=f"traspuesta 2 «{TER['nombres'][0]['nombre']}», {TER['nombre']}, {TER['anchoKm']} km",
                 lamina=dict(islotes=[[round(a, 2), round(w, 2)] for a, w in ISLOTES], boca=[round(BOCA[0], 2), round(BOCA[1], 2)], radio_anillo_m=round(R_ANILLO),
                             prof_laguna_m=round(prof_laguna, 1), c_onda_ms=round(c_onda, 2), f_seiche_hz=f_seiche, octavas_arriba=octavas),
                 tonica=round(TON, 3), bpm=BPM, compas=BAR, dieciseisavo=S16, tema_v=TEMA_V, tema_c=TEMA_C, cruce=round(TC, 3), f_cruce=round(F_X, 3), t8=T8,
                 secciones=[dict(num=k, t=v[0], t1=v[1]) for k, v in SEC.items()], duracion=DUR,
                 volcan=VOLCAN, coral=CORAL, collar=COLLAR, web=ev, sub=sub, talbot=TALBOT, olas=OLAS, aves=aves, boca=boca, camaras=CAMARAS, gotas=gotas,
                 laguna=LAGUNA, luciernagas=LUCIERNAGAS,
                 sabina=[dict(eventos=lead, nivel=.9, pan=0, capa='lead'), dict(eventos=coro, nivel=.85, pan=0, capa='coro'), dict(eventos=chops, nivel=.85, pan=0, capa='chops')],
                 coros=coros, instrumentos=None)
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    inst = [d for d in os.listdir(AQUI) if d.startswith('instrumentos-')]; partitura['instrumentos'] = inst[0] if inst else None
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', DUR, 's · tónica', round(TON, 2), f'({fT(TON):.2f} Hz, seiche {f_seiche:.5f} Hz × 2^{octavas}) · laguna {prof_laguna:.1f} m, anillo {R_ANILLO:.0f} m')
    print('islotes', len(ISLOTES), '· boca', [round(x, 1) for x in BOCA], '· collar', sorted(e['paso'] for e in COLLAR))
    print('secciones', SEC, '· cruce', round(TC, 1), 's en', round(F_X, 2), 'Hz')
    print('web', {k: len(v) for k, v in ev.items()}, '· sub', len(sub), '· olas', len(OLAS), '· aves', len(aves), '· boca', len(boca), '· gotas', len(gotas), '· lead', len(lead), '· coro', len(coro), '· chops', len(chops))
