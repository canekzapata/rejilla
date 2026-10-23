"""Las islas del cielo — partitura. Joropo llanero × changa tuki × el espectralismo de las cascadas, sobre los tepuyes 2572 de
Traspuesta (tres mesas: «El Pico Grande», «El Cerro», «El Cerro de los Helechos»). Diseño en DISENO.md.

EL AISLAMIENTO: al principio hay un tema, una afinación y un compás (la meseta, antes de la erosión). La erosión separa tres mesas
y el tema se parte: cada isla lo canta a su manera y muta por su lado, generación por generación (cambia un grado, invierte dos
notas vecinas, liga dos corcheas). Su afinación se corre hacia el tono de su propia pared (la pared como tubo: f = c/2H; la isla
más alta, más grave) y cada una agrupa las corcheas en su compás (3/4, 6/8, 4). Al final el agua de las tres cascadas baja al
llano y las variantes se juntan en un tema nuevo: el consenso, nota por nota, de lo que cada isla aprendió. No es el de antes.
EL PULSO COMÚN: la negra del changa (144 bpm) es la negra con puntillo del joropo en 6/8 (la corchea, a 432): un compás de changa
= dos compases de joropo = 12 corcheas («D», 1.667 s).
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np
from scipy.ndimage import label, binary_dilation

SEMILLA = 2572
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__)); GG = 360
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-2572.json'), encoding='utf-8'))
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-2572.f32'), dtype=np.float32).reshape(GG, GG).astype(float)
m_de = lambda f: 69 + 12 * math.log2(f / 440)
fT = lambda m: 440 * 2 ** ((m - 69) / 12)

# ── la lámina: las tres mesas, sus paredes ──
LB, n = label(H > .5); km = TER['anchoKm'] * 1000 / (GG - 1)
cumbres = [x for x in TER['nombres'] if x['clase'] == 'cumbre']
ISLAS = []
for k in range(1, n + 1):
    msk = LB == k
    if msk.sum() < 600: continue
    anillo = binary_dilation(msk, iterations=18) & ~binary_dilation(msk, iterations=6)
    tope = float(np.median(H[msk])) * TER['relieve']; base = float(np.median(H[anillo])) * TER['relieve']
    ys, xs = np.nonzero(msk); u, v = xs.mean() / (GG - 1), ys.mean() / (GG - 1)
    nom = min(cumbres, key=lambda c: (c['u'] - u) ** 2 + (c['v'] - v) ** 2)['nombre'] if cumbres else f'TEPUY {k}'
    ISLAS.append(dict(u=round(u, 4), v=round(v, 4), area_km2=round(float(msk.sum()) * km * km / 1e6, 2), tope_m=round(tope), base_m=round(base), pared_m=round(tope - base), nombre=nom))
ISLAS.sort(key=lambda i: i['u'])
for i, isla in enumerate(ISLAS): isla['pan'] = round(-.7 + 1.4 * i / max(1, len(ISLAS) - 1), 2)
H_MEDIA = float(np.mean([i['pared_m'] for i in ISLAS]))
f_tubo = 343 / (2 * H_MEDIA); f = f_tubo; octv = 0
while f < 55: f *= 2; octv += 1
TON = m_de(f)                                                                    # la tónica: la pared media como tubo, subida por octavas
for isla in ISLAS: isla['cents_meta'] = round(float(np.clip(-1200 * math.log2(isla['pared_m'] / H_MEDIA), -45, 45)), 1)   # más alta, más grave
METROS = [[0, 2, 4, 6, 8, 10], [0, 3, 6, 9], [0, 4, 8]]                         # dónde acentúa cada isla: 3/4, 6/8, 4
for i, isla in enumerate(ISLAS): isla['compas'] = ['3/4', '6/8', '4'][i % 3]; isla['acentos'] = METROS[i % 3]

ESCALA = [0, 2, 3, 5, 7, 8, 11]                                                  # menor armónica (el séptimo grado llanero)
def gr(g, o=0): k, r = divmod(int(g), 7); return TON + 12 * (o + k) + ESCALA[r]
TEMA = [4, 3, 2, 1, 0, 1, 2, 4, 5, 4, 2, 0]                                      # 12 corcheas: un D
LIGA = [False] * 12                                                              # una corchea ligada a la anterior no se toca

BPM_J = 216; NEGRA = 60 / BPM_J; CORCHEA = NEGRA / 2; D = 12 * CORCHEA; Q = 3 * CORCHEA   # Q: la negra del changa (144 bpm)
SEC = {}; t0 = 0.0
for nom, nd in (('I', 22), ('II', 26), ('III', 30), ('IV', 34), ('V', 26)): SEC[nom] = (round(t0, 4), round(t0 + nd * D, 4)); t0 += nd * D
DUR = round(t0 + 10, 3)
def td(sec, d, c=0): return SEC[sec][0] + d * D + c * CORCHEA

# ═════════ el tema se parte y muta (III–IV), y se junta (V) ═════════
GEN = 4                                                                          # una generación cada 4 D
n_gen = (30 + 34) // GEN
VARIANTES = []                                                                   # VARIANTES[isla][gen] = (grados, ligas)
for i in range(len(ISLAS)):
    rr = random.Random(SEMILLA * 7 + i); g, l = TEMA[:], LIGA[:]; hist = [(g[:], l[:])]
    for _ in range(n_gen):
        x = rr.random(); p = rr.randrange(12)
        if x < .6: g[p] = max(-2, min(9, g[p] + rr.choice([-1, 1])))
        elif x < .85 and p < 11: g[p], g[p + 1] = g[p + 1], g[p]
        elif p > 0: l[p] = not l[p]
        hist.append((g[:], l[:]))
    VARIANTES.append(hist)
def distancia(a, b): return sum(1 for x, y in zip(a, b) if x != y)
finales = [VARIANTES[i][-1][0] for i in range(len(ISLAS))]
CONSENSO = [int(np.median([f[p] for f in finales])) for p in range(12)]           # el tema nuevo: la mediana de lo aprendido aparte
CENTS_LLANO = float(np.mean([i['cents_meta'] for i in ISLAS]))                     # la afinación del llano: el promedio de las islas
def cents(i, t):
    a, z = SEC['III'][0], SEC['IV'][1]; v5, z5 = SEC['V'][0], SEC['V'][0] + 12 * D
    if t < a: return 0.0
    if t < z: u = (t - a) / (z - a); return ISLAS[i]['cents_meta'] * u * u * (3 - 2 * u)
    if t < z5: u = (t - v5) / (z5 - v5); return ISLAS[i]['cents_meta'] * (1 - u) + CENTS_LLANO * u
    return CENTS_LLANO
def gen_en(t): return int(np.clip((t - SEC['III'][0]) // (GEN * D), 0, n_gen))

# ═════════ el arpa, el cuatro, los capachos ═════════
PROG = [(0, 'i'), (4, 'V7'), (3, 'iv'), (4, 'V7'), (0, 'i'), (5, 'VI'), (6, 'VII'), (4, 'V7')]   # por compás de 3/4
ACORDE = {'i': [0, 3, 7], 'iv': [5, 8, 12], 'V7': [7, 11, 14, 17], 'VI': [8, 12, 15], 'VII': [10, 14, 17]}
def acorde(b): return ACORDE[PROG[b % 8][1]]
arpas = {k: [] for k in ['meseta', 'isla0', 'isla1', 'isla2']}; cuatro = []; capachos = []
def arpa_D(dest, t, grados, ligas, ac1, ac2, acentos, cc=0.0, o=1, bajo=True, v=.7):
    for c in range(12):
        if ligas[c]: continue
        d = 1
        while c + d < 12 and ligas[c + d]: d += 1
        m = gr(grados[c], o) + cc / 100; acento = c in acentos
        dest.append(dict(t=round(t + c * CORCHEA, 4), dur=round(d * CORCHEA * 1.6, 4), m=round(m, 3), v=round(v * (1 if acento else .62), 3), c=int(round(m))))
    if bajo:                                                                     # el bordoneo: la raíz y la quinta abajo, en los acentos
        for k, c in enumerate(acentos[:3]):
            ac = ac1 if c < 6 else ac2; m = TON + ac[0] + (7 if k % 2 else 0) + cc / 100
            dest.append(dict(t=round(t + c * CORCHEA, 4), dur=round(CORCHEA * 2.5, 4), m=round(m, 3), v=round(v * .85, 3), c=int(round(m))))
def cuatro_D(t, ac1, ac2, cc=0.0, v=.55):
    for c in range(12):
        ac = ac1 if c < 6 else ac2; fuerte = c in (0, 3, 6, 9); voz = sorted({(x % 12) for x in ac} | {ac[0] % 12})[:4]
        while len(voz) < 4: voz.append(voz[0] + 12)
        for s, x in enumerate(voz):
            cuatro.append(dict(t=round(t + c * CORCHEA + .008 * s, 4), dur=round(CORCHEA * (.9 if fuerte else .45), 4), m=round(TON + 24 + x + cc / 100, 3), v=round(v * (1 if fuerte else .55), 3), c=s))
def capachos_D(t, v=.6):
    for c in range(12): capachos.append(dict(t=round(t + c * CORCHEA, 4), dur=round(CORCHEA * (.8 if c % 3 == 0 else .5), 4), v=round(v * (1 if c % 3 == 0 else .5), 3), pan=.25))

for d in range(22):                                                              # I · la meseta: un tema, todos juntos
    t = td('I', d); b = 2 * d
    if d >= 2: arpa_D(arpas['meseta'], t, TEMA, LIGA, acorde(b), acorde(b + 1), METROS[1], o=1, v=.7)
    if d >= 6: cuatro_D(t, acorde(b), acorde(b + 1)); capachos_D(t, .5)
for d in range(26):                                                              # II · el levantamiento: todo sube una cuarta hacia el final
    t = td('II', d); b = 2 * d; sube = 5 * 100 * min(1, d / 20)
    arpa_D(arpas['meseta'], t, TEMA, LIGA, acorde(b), acorde(b + 1), METROS[1], cc=sube, o=1, v=.72); cuatro_D(t, acorde(b), acorde(b + 1), cc=sube); capachos_D(t, .6)
SUBE = 500                                                                       # desde el levantamiento todo queda una cuarta arriba (en cents)
for sec, nd in (('III', 30), ('IV', 34)):                                        # III–IV · las islas: cada una su variante, su afinación, su compás
    for d in range(nd):
        t = td(sec, d); b = 2 * d; g = gen_en(t)
        for i in range(len(ISLAS)):
            gg, ll = VARIANTES[i][g]
            arpa_D(arpas[f'isla{i}'], t, gg, ll, acorde(b), acorde(b + 1), ISLAS[i]['acentos'], cc=SUBE + cents(i, t), o=1, v=.66)
        if sec == 'III' and d < 8: cuatro_D(t, acorde(b), acorde(b + 1), cc=SUBE, v=.4)
for d in range(26):                                                              # V · el llano: el consenso, la afinación común, el 6/8
    t = td('V', d); b = 2 * d
    for i in range(len(ISLAS)):
        if d < 12: arpa_D(arpas[f'isla{i}'], t, CONSENSO, [False] * 12, acorde(b), acorde(b + 1), METROS[1], cc=SUBE + cents(i, t), o=1, v=.6 * (1 - d / 14))
    if d >= 8: arpa_D(arpas['meseta'], t, CONSENSO, [False] * 12, acorde(b), acorde(b + 1), METROS[1], cc=SUBE + CENTS_LLANO, o=1, v=.7)
    if d >= 4: cuatro_D(t, acorde(b), acorde(b + 1), cc=SUBE + CENTS_LLANO, v=.5); capachos_D(t, .55)

# ═════════ el changa tuki (II desde la mitad, III a pedazos, IV entero) ═════════
web = {k: [] for k in ['bateria']}; tukis = []; sub = []
def bat(t, pieza, vel, pan=0.0): web['bateria'].append(dict(t=round(t, 5), ficha='bateria-tr909', midi=60, vel=round(vel, 3), dur=.2, pan=pan, pieza=pieza))
def changa(sec, d0, d1, lleno=True, cc=0.0):
    for d in range(d0, d1):
        t = td(sec, d); ac = acorde(2 * d)
        for k in range(4): bat(t + k * Q, 'kick', .95)
        if lleno:
            for k in (1, 3): bat(t + k * Q, 'clap', .7, .05)
            for k in range(4): bat(t + k * Q + Q / 2, 'openhat' if k % 2 else 'hat', .45, .3)
            for s in (3, 6, 10, 13):                                             # el tuki: stabs en los dieciseisavos del changa
                if R.random() < .75: tukis.append(dict(t=round(t + s * Q / 4, 4), notas=[round(TON + 24 + x + cc / 100, 3) for x in ac], dur=.11, v=.7, pan=round(R.uniform(-.4, .4), 2)))
            if d % 8 == 7:
                k, tt = 0, t + 3 * Q
                while tt < t + D - .01: bat(tt, 'snare', .4 + .5 * k / 14, .05); tt += Q / 4 * (.96 ** k); k += 1
        for k in (0, 2): sub.append(dict(t=round(t + k * Q, 4), dur=round(Q * 1.6, 4), midi=round(TON - 12 + ac[0] + cc / 100, 3), vel=.85))
changa('II', 14, 26, lleno=False, cc=0); changa('III', 0, 30, lleno=False, cc=SUBE)
for d in range(0, 30, 6): changa('III', d, d + 2, lleno=True, cc=SUBE)
changa('IV', 0, 34, lleno=True, cc=SUBE)
changa('V', 0, 4, lleno=False, cc=SUBE + CENTS_LLANO)

# ═════════ la campana de distancias imposibles (de Codex): la vecindad cambia con la erosión ═════════
camp = dict(initial=dict(fold=0, depth=.7, tension=7, damping=.5, midi=round(TON + 12 + SUBE / 100, 3), pickup=0), events=[])
for sec in SEC:
    a, z = SEC[sec]; t = a + .3
    while t < z - .5:
        if sec in ('I', 'II'): zona = R.randrange(64)
        elif sec == 'V': zona = R.randrange(64)
        else: i = R.randrange(len(ISLAS)); zona = 4 * R.randrange(16) + i                   # cada isla toca su familia (mod 4)
        camp['events'].append(dict(t=round(t, 3), hit=zona, vel=round(R.uniform(.4, .8), 3))); t += D * R.choice([.5, 1, 1.5])
camp['events'] += [dict(t=SEC['III'][0], params=dict(fold=.4)), dict(t=SEC['III'][0] + 15 * D, params=dict(fold=1, depth=1.2)),
                   dict(t=SEC['IV'][0], params=dict(depth=1.8)), dict(t=SEC['V'][0] + 6 * D, params=dict(fold=.3, depth=.9))]
camp['events'].sort(key=lambda e: e['t'])

# ═════════ las aves: un canto ancestral; cada isla lo aprende aparte ═════════
MOTIVO = [[0, 9], [.08, 11], [.16, 12], [.3, 11], [.38, 9], [.52, 14]]            # [dt, grado] en la octava alta
aves = []
def canto(t, grados, cc, pan, voz, v=.45):
    aves.append(dict(t=round(t, 3), tipo='canto', notas=[[dt, round(gr(g, 2) + cc / 100, 3), .07] for (dt, _), g in zip(MOTIVO, grados)], dur=.65, m=round(gr(grados[0], 2), 3), v=v, voz=voz, pan=pan))
for _ in range(10): canto(R.uniform(*SEC['I']), [g for _, g in MOTIVO], 0, R.uniform(-.6, .6), R.randint(0, 1))
for sec in ('III', 'IV'):
    for _ in range(26):
        t = R.uniform(*SEC[sec]); i = R.randrange(len(ISLAS)); g = gen_en(t)
        rr = random.Random(i * 1000 + g); gs = [x + (rr.choice([-1, 0, 0, 1]) * (g > 0)) for _, x in MOTIVO]
        canto(t, gs, SUBE + cents(i, t), ISLAS[i]['pan'], i % 2)
for _ in range(10): canto(R.uniform(*SEC['V']), [x for _, x in MOTIVO], SUBE + CENTS_LLANO, R.uniform(-.5, .5), R.randint(0, 1))

# ═════════ las cascadas: una por isla; su duración es su pared ═════════
CASCADAS = [dict(t=round(SEC['IV'][0] + 2 + 9 * i, 3), H=isla['pared_m'], f=round(fT(TON + 12) * 2 ** ((SUBE + isla['cents_meta']) / 1200), 3), pan=isla['pan']) for i, isla in enumerate(ISLAS)]
LLUVIA = [[0, 0], [SEC['V'][0], 0], [SEC['V'][0] + 6 * D, .5], [SEC['V'][0] + 16 * D, 1.0], [DUR - 4, .6], [DUR, 0]]

# ═════════ las voces ═════════
lead, coro, chops = [], [], []; islas_voz = {f'isla{i}': [] for i in range(len(ISLAS))}; coros = {v: [] for v in 'SATB'}
def frase(dest, texto, t, alturas, ritmo, legato=.92, **kw):
    for k, sy in enumerate(texto.split()):
        d = ritmo[k % len(ritmo)] * CORCHEA; dest.append(dict(t=round(t, 4), dur=round(d * legato, 4), texto=sy, nota=round(alturas[k % len(alturas)], 3), **kw)); t += d
    return t
def con_tema(grados, o, cc=0.0): return [gr(g, o) + cc / 100 for g in grados]
I_TXT = ['u na so la tie rra u na so la voz', 'can tá ba mos pa re jo ba jo el mis mo sol']
for k, txt in enumerate(I_TXT):
    t = td('I', 8 + 6 * k); alt = con_tema(TEMA, 2); rit = [2, 1, 2, 1, 3, 1, 2, 1, 2, 1, 6]
    frase(coro, txt, t, alt, rit)
    for v, x in zip('SATB', (0, -3, -7, None)):
        frase(coros[v], txt, t, [a + x if x is not None else TON + 12 for a in alt], rit)
frase(lead, 'la tie rra se le van tó', td('II', 6), con_tema([4, 4, 5, 4, 2, 1, 0], 2, 0), [2, 2, 2, 2, 2, 2, 8])
frase(lead, 'y el a gua em pe zó a cor tar', td('II', 12), con_tema([0, 1, 2, 2, 4, 5, 4, 2, 0], 2, 300), [2, 1, 2, 2, 2, 2, 2, 2, 8])
III_TXT = ['ca da quien se que dó en su ci ma', 'a pren dien do la can ción de me mo ria', 'y la me mo ria se le fue tor cien do']
for k, txt in enumerate(III_TXT):
    t = td('III', 4 + 8 * k); g = VARIANTES[k % len(ISLAS)][gen_en(t)][0]
    frase(lead, txt, t, con_tema(g, 2, SUBE + cents(k % len(ISLAS), t)), [2, 1, 2, 1, 2, 2, 1, 2, 2, 6])
CANCION = 'la mis ma can ción a pren di da en o tra ci ma'
for rep in range(3):                                                             # IV · el canon de dialectos: cada isla su variante y su afinación
    for i in range(len(ISLAS)):
        t = td('IV', 4 + 10 * rep + 2 * i); g = VARIANTES[i][gen_en(t)][0]
        frase(islas_voz[f'isla{i}'], CANCION, t, con_tema(g, 2, SUBE + cents(i, t)), [2, 1, 2, 2, 1, 2, 1, 2, 2, 1, 2, 2, 6])
for d in range(0, 34):
    if d % 4 in (1, 2):
        for s, sy, x in ((2, 'ci', 0), (3, 'ma', 3), (8, 'can', 7), (9, 'ción', 5)):
            if R.random() < .75: chops.append(dict(t=round(td('IV', d) + s * Q / 4, 4), dur=round(Q / 4 * .85, 4), texto=sy, nota=round(TON + 31 + x + SUBE / 100, 3)))
V_TXT = ['a ba jo el a gua jun ta lo que ba jó', 'no es la can ción de an tes', 'es la que a pren di mos a par te', 'y la can ta mos jun tos']
for k, txt in enumerate(V_TXT):
    t = td('V', 4 + 5 * k); alt = con_tema(CONSENSO, 2, SUBE + CENTS_LLANO)
    frase(lead, txt, t, alt, [2, 1, 2, 1, 2, 2, 1, 2, 2, 1, 6])
    if k == 3:
        frase(coro, txt, t, [a + 12 for a in alt[:7]], [2, 1, 2, 1, 2, 2, 8])
        for v, x in zip('SATB', (0, -3, -7, None)): frase(coros[v], txt, t, [a + x + 12 if x is not None else TON + 12 + SUBE / 100 for a in alt[:7]], [2, 1, 2, 1, 2, 2, 8])

partitura = dict(titulo='Las islas del cielo', semilla=SEMILLA, terreno=f"traspuesta 2572, {TER['nombre']}, {TER['anchoKm']} km, {TER['relieve']} m",
                 islas=ISLAS, pared_media_m=round(H_MEDIA), f_tubo_hz=f_tubo, octavas_arriba=octv, tonica=round(TON, 3), sube_cents=SUBE, cents_llano=round(CENTS_LLANO, 2),
                 bpm_joropo=BPM_J, corchea=CORCHEA, D=D, Q=Q, secciones=[dict(num=k, t=v[0], t1=v[1]) for k, v in SEC.items()], duracion=DUR,
                 tema=TEMA, consenso=CONSENSO, generacion_D=GEN, variantes=[[[g, l] for g, l in v] for v in VARIANTES],
                 distancias_finales=[distancia(TEMA, f) for f in finales], distancia_consenso=distancia(TEMA, CONSENSO),
                 arpas=arpas, cuatro=cuatro, capachos=capachos, web=web, tuki=tukis, sub=sub, campana=camp, aves=aves, cascadas=CASCADAS, lluvia=LLUVIA,
                 sabina=[dict(eventos=lead, nivel=.9, pan=0, capa='lead'), dict(eventos=coro, nivel=.85, pan=0, capa='coro'), dict(eventos=chops, nivel=.85, pan=0, capa='chops')] +
                        [dict(eventos=ev, nivel=.85, pan=ISLAS[int(k[-1])]['pan'], capa=k) for k, ev in islas_voz.items()],
                 coros=coros, instrumentos=None)
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    inst = [d for d in os.listdir(AQUI) if d.startswith('instrumentos-')]; partitura['instrumentos'] = inst[0] if inst else None
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', DUR, 's · tónica', round(TON, 2), f'({fT(TON):.2f} Hz: pared media {H_MEDIA:.0f} m como tubo, {f_tubo:.4f} Hz × 2^{octv})')
    for i in ISLAS: print('  isla', i['nombre'], 'pared', i['pared_m'], 'm, tope', i['tope_m'], '· cents', i['cents_meta'], '·', i['compas'], '· pan', i['pan'])
    print('secciones', SEC, '· D', round(D, 4), 's')
    print('tema', TEMA, '→ variantes finales', finales, '(distancias', partitura['distancias_finales'], ') → consenso', CONSENSO, '(distancia', partitura['distancia_consenso'], ')')
    print('arpas', {k: len(v) for k, v in arpas.items()}, '· cuatro', len(cuatro), '· capachos', len(capachos), '· 909', len(web['bateria']), '· tuki', len(tukis), '· campana', len(camp['events']), '· aves', len(aves), '· cascadas', [(c['H'], c['t']) for c in CASCADAS])
    print('voces: lead', len(lead), 'coro', len(coro), 'chops', len(chops), {k: len(v) for k, v in islas_voz.items()})
