"""Primero sueño en el cenote — partitura. UK garage roto (Burial) × Poema sinfónico para 100 metrónomos (Ligeti) × canto gutural
(Tagaq, katajjaq), sobre el karst 43 de Traspuesta y *Primero sueño* de Sor Juana (sólo se citan los cuatro primeros versos y el
final). Diseño en DISENO.md.

LAS DOLINAS SON CÁMARAS: se leen del mapa (alto suavizado menos alto) y cada una es un resonador de Helmholtz con su volumen y su boca
(subido por octavas al registro audible) con un gotero adentro, cuyo periodo crece con el tamaño. La tónica es la cámara más grande.
EL TEMA A (la sombra que sube): 0, 3, 7, 10, 12, 15 sobre la tónica. Lo pinta la linterna, lo canta la voz, lo hace el bajo, lo vuela
el alma, se rompe y vuelve bajando al amanecer.
LOS GOTEROS SE ENCARRILAN: libres en I (todos empiezan juntos: el Ligeti de agua), se van pegando a la rejilla del garage en II,
se sueltan en III, se paran uno por uno en IV; en V queda uno.
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np
from scipy.ndimage import gaussian_filter, label, center_of_mass, maximum, sum as nsum

SEMILLA = 43
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__)); G = 360
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-43.f32'), dtype=np.float32).reshape(G, G).astype(float)
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-43.json'), encoding='utf-8'))
m_de = lambda f: 69 + 12 * math.log2(f / 440)
def octava_a(f, lo, hi):
    while f < lo: f *= 2
    while f >= hi: f /= 2
    return f

# ── las dolinas: cámaras con su gotero ──
dep = gaussian_filter(H, 5) - H; LB, n = label(dep > .012)
celda = TER['anchoKm'] * 1000 / (G - 1); REL = TER['relieve']
areas = nsum(np.ones_like(H), LB, range(1, n + 1)); prof = maximum(dep, LB, range(1, n + 1)); cms = center_of_mass(np.ones_like(H), LB, range(1, n + 1))
CAM = []
for k in range(n):
    if areas[k] < 8: continue
    A = areas[k] * celda ** 2; d = prof[k] * REL; V = A * d / 3; rad = math.sqrt(A / math.pi)
    fh_real = 343 / (2 * math.pi) * math.sqrt(A / (V * max(d, 1))); fb_real = 343 / (2 * rad)
    CAM.append(dict(id=str(len(CAM)), u=round(cms[k][1] / (G - 1), 4), v=round(cms[k][0] / (G - 1), 4), area_m2=round(A), prof_m=round(d, 1), radio_m=round(rad),
                    fh_real=fh_real, fh=round(octava_a(fh_real, 70, 140) * (1 + .5 * (rad < 150)), 2), fb=round(octava_a(fb_real, 380, 760), 2),
                    cenote=bool(d / rad > .5), pan=round(float(np.clip(2 * cms[k][1] / (G - 1) - 1, -.9, .9)), 3)))
CAM.sort(key=lambda c: -c['area_m2'])
for c in sorted(CAM, key=lambda c: -c['prof_m'] / c['radio_m'])[:3]: c['cenote'] = True   # las tres de pared más vertical: cenotes
for i, c in enumerate(CAM): c['id'] = str(i)
RMAX = max(c['radio_m'] for c in CAM)
TON = m_de(octava_a(CAM[0]['fh'], 50, 100))                                     # la tónica: la cámara más grande
TEMA = [0, 3, 7, 10, 12, 15]
def tema(i, o=0): k, r = divmod(i, len(TEMA)); return TON + 12 * (o + 2 * k) + TEMA[r]
MENOR = [0, 2, 3, 5, 7, 8, 10]
def gr(g, o=0): k, r = divmod(g, 7); return TON + 12 * (o + k) + MENOR[r]

BPM = 132; Q = 60 / BPM; BAR = 4 * Q; S16 = Q / 4
SEC = {}; t0 = 0.0
for nom, nb in (('I', 26), ('II', 32), ('III', 24), ('IV', 22), ('V', 20)): SEC[nom] = (round(t0, 3), round(t0 + nb * BAR, 3)); t0 += nb * BAR
DUR = t0 + 6
def tb(b): return b * BAR
def ts(sec, b, s=0.0): return SEC[sec][0] + b * BAR + s * S16

# ═════════ los goteros ═════════
def w_rejilla(t):                                                                # cuánto se pegan a la rejilla del garage
    a, z = SEC['II']; a3, z3 = SEC['III']
    if t < a: return 0
    if t < a + 8 * BAR: return .9 * (t - a) / (8 * BAR)
    if t < z: return .9
    if t < a3 + 6 * BAR: return .9 * (1 - (t - z) / (6 * BAR))
    if SEC['IV'][0] <= t < SEC['IV'][1]: return .5
    return 0
gotas = []; PARA = {}
orden_paro = list(range(1, len(CAM))); R.shuffle(orden_paro)
for j, k in enumerate(orden_paro): PARA[str(k)] = SEC['IV'][0] + (j + 1) / len(orden_paro) * (SEC['IV'][1] - SEC['IV'][0] - 2)
PARA['0'] = DUR - 2                                                               # queda la cámara grande (en V gotea sola)
for c in CAM:
    rn = c['radio_m'] / RMAX; P = .7 + 3.3 * rn ** .7; rmm = 1.8 + 2.8 * (1 - rn); t = 1.0 + R.uniform(0, .02)      # todos empiezan juntos
    while t < PARA[c['id']]:
        w = w_rejilla(t); g = 2 * S16; snap = round(t / g) * g; tt = (1 - w) * t + w * snap
        gotas.append(dict(t=round(tt, 4), id=c['id'], r=round(rmm * R.uniform(.92, 1.08), 3), v=round(R.uniform(.45, .9), 3)))
        t += P * R.uniform(.97, 1.03)
CAMARAS = {c['id']: dict(fh=c['fh'], fb=c['fb'], q=26 if c['cenote'] else 16, pan=c['pan'], eco=.8 if c['cenote'] else .5) for c in CAM}

# ═════════ los metrónomos de cuerda (se dan cuerda en I, se paran uno por uno en IV) ═════════
RAZ = [1, 3 / 4, 2 / 3, 5 / 4, 4 / 3, 3 / 2, 5 / 6, 7 / 8, 9 / 8, 1 / 2, 6 / 5, 4 / 5]
paros = sorted(R.uniform(SEC['IV'][0] + 2, SEC['IV'][1] - 1) for _ in RAZ)
METRO = [dict(id=i, t0=round(.8 + i * .55, 3), bpm=round(BPM * r, 3), cuerda=round(paros[i] - (.8 + i * .55), 3), compas=[4, 3, 0, 5, 0, 4, 0, 7, 0, 3, 0, 0][i], pan=round(-.85 + 1.7 * i / 11, 3), v=.55 + .2 * (r == 1))
         for i, r in enumerate(RAZ)]

# ═════════ el garage (II entero; IV roto, a medio tiempo) ═════════
ev = {k: [] for k in ['bateria', 'bateria-frito']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr909', stem='bateria'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)
SW = (.58 - .5) * 2 * S16                                                        # el swing de 58 %
def sw(s): return s * S16 + (SW if s % 2 else 0)
sub = []
def dos_pasos(sec, b, roto=False):
    t = lambda s: SEC[sec][0] + b * BAR + sw(s) + R.gauss(0, .006)            # Burial: los golpes se corren del grid
    if not roto:
        for s in ([0, 7, 10] if b % 2 == 0 else [0, 10, 13]): bat(t(s), 'kick', .95 if s == 0 else .8)
        for s in (4, 12): bat(t(s), 'snare', .8, .05); web('bateria-frito', t(s) + .01, 'bateria-frito', 60, .45, .2, -.1, pieza='clap')
        for s in (7, 15): bat(t(s), 'rim', .3, .2)
        for s in range(16):
            if s % 2 == 1 or R.random() < .3: bat(t(s), 'hat' if s % 4 != 2 else 'openhat', .25 + .2 * (s % 4 == 2), .3)
        for s, i in ((0, 0), (3, 1), (7, 2), (10, 3), (13, 2)): sub.append(dict(t=round(t(s), 4), dur=round(2.4 * S16, 4), midi=round(tema(i, -2), 3), vel=.85))   # el bajo hace el tema A
    else:
        bat(t(0), 'kick', .9); bat(t(8), 'snare', .7, .05); web('bateria-frito', t(8) + .02, 'bateria-frito', 60, .5, .2, 0, pieza='spray')
        for s in (2, 6, 11, 14):
            if R.random() < .7: bat(t(s), 'hat', .2, .35)
        sub.append(dict(t=round(t(0), 4), dur=round(7 * S16, 4), midi=round(tema([0, 3, 1, 2][b % 4], -2), 3), vel=.8))
for b in range(32):
    if b >= 2: dos_pasos('II', b)
for b in range(4, 22): dos_pasos('IV', b, roto=True)

# ═════════ la linterna mágica: el poema pintado como espectro ═════════
fT = lambda m: 440 * 2 ** ((m - 69) / 12)
trazos = [dict(tipo='triangulo', t0=SEC['I'][0] + 2, t1=SEC['I'][1] - 2, f0=fT(TON), f1=fT(TON + 51), v=.55)]           # la pirámide de sombra que sube
for i, ttema in enumerate(TEMA):                                                                                          # el tema A, nota por nota, en el filo
    trazos.append(dict(tipo='linea', t0=SEC['I'][0] + 6 + i * 6, t1=SEC['I'][0] + 11 + i * 6, f0=fT(TON + 24 + ttema), f1=fT(TON + 24 + ttema), v=.5, ancho=.9))
for k in range(40):                                                                                                       # las estrellas (III)
    a = R.uniform(*SEC['III']); trazos.append(dict(tipo='punto', t0=a, t1=a + R.uniform(.6, 2.2), f0=fT(tema(R.randint(3, 11), 2)), v=R.uniform(.3, .8)))
for k in range(5):                                                                                                        # el vuelo del alma: curvas que suben y caen
    a = SEC['III'][0] + 4 + 7.5 * k; trazos.append(dict(tipo='linea', t0=a, t1=a + 6, f0=fT(tema(k, 1)), f1=fT(tema(k + 4, 2)), v=.45, ancho=1.6))
trazos.append(dict(tipo='linea', t0=SEC['IV'][0], t1=SEC['IV'][0] + 14, f0=fT(tema(9, 2)), f1=fT(TON - 12), v=.5, ancho=2.5))   # la caída
trazos.append(dict(tipo='relleno', t0=SEC['V'][0] + 2, t1=SEC['V'][1], f0=fT(TON - 12), f1=6800, v=.5))                    # el amanecer

# ═════════ las voces ═════════
lead, coro, chops, vocales, coros = [], [], [], [], {v: [] for v in 'SATB'}
def frase(dest, texto, t, alturas, ritmo, legato=.92, **kw):
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; dest.append(dict(t=round(t, 4), dur=round(d * legato, 4), texto=sy, nota=round(alturas[i % len(alturas)], 3), **kw)); t += d
    return t
VERSOS = [('pi ra mi dal fu nes ta de la tie rra', [tema(0, 1), tema(0, 1), tema(1, 1), tema(2, 1), tema(2, 1), tema(3, 1), tema(2, 1), tema(1, 1), tema(1, 1), tema(0, 1), tema(0, 1)], [3, 2, 2, 6, 2, 2, 5, 2, 2, 3, 9]),
          ('na ci da som bra al cie lo en ca mi na ba', [tema(1, 1), tema(1, 1), tema(2, 1), tema(3, 1), tema(2, 1), tema(3, 1), tema(4, 1), tema(3, 1), tema(2, 1), tema(3, 1), tema(2, 1), tema(1, 1), tema(0, 1)], [2, 2, 3, 6, 4, 2, 4, 2, 2, 2, 2, 3, 9]),
          ('de va nos o be lis cos pun ta al ti va', [tema(2, 1), tema(3, 1), tema(3, 1), tema(4, 1), tema(3, 1), tema(4, 1), tema(5, 1), tema(4, 1), tema(3, 1), tema(4, 1), tema(3, 1), tema(2, 1)], [2, 3, 3, 2, 2, 3, 5, 3, 2, 3, 3, 9]),
          ('es ca lar pre ten dien do las es tre llas', [tema(3, 1), tema(4, 1), tema(5, 1), tema(5, 1), tema(6, 1), tema(5, 1), tema(4, 1), tema(5, 1), tema(6, 1), tema(7, 1), tema(5, 1)], [2, 2, 4, 2, 2, 3, 3, 2, 3, 4, 12])]
for i, (txt, alt, rit) in enumerate(VERSOS): frase(lead, txt, ts('I', 4 + 5 * i), alt, rit)
def coral(texto, t, mel, ritmo):
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; sop = mel[i % len(mel)]
        for v, x in zip('SATB', (0, -4, -7, None)): coros[v].append(dict(t=round(t, 4), dur=round(d * .9, 4), texto=sy, nota=round(sop + x if x is not None else TON + 12, 3)))
        coro.append(dict(t=round(t, 4), dur=round(d * .9, 4), texto=sy, nota=round(sop, 3))); t += d
for b in (10, 22): coral('es ca lar pre ten dien do las es tre llas', ts('II', b), [tema(x, 2) for x in (3, 4, 5, 5, 6, 5, 4, 5, 6, 7, 6)], [2, 2, 3, 1, 2, 3, 3, 2, 2, 4, 12])
for b in list(range(6, 10)) + list(range(18, 22)) + list(range(28, 32)):                                                  # chops a lo Burial
    for s, sy, x in ((2, 'som', 7), (3, 'bra', 5), (9, 'es', 10), (10, 'tre', 12), (11, 'llas', 10), (14, 'som', 7)):
        if R.random() < .75: chops.append(dict(t=round(ts('II', b) + sw(s) + R.gauss(0, .01), 4), dur=round(S16 * .9, 4), texto=sy, nota=round(TON + 24 + x + 12, 3)))
for b in range(8, 22):                                                                                                    # chops rotos en IV
    if b % 2 == 0: chops.append(dict(t=round(ts('IV', b, 6), 4), dur=round(S16 * 1.5, 4), texto=R.choice(['som', 'bra', 'llas']), nota=round(TON + 31 + R.choice([0, -2, -5]), 3)))
for i, v in enumerate('a o e a u o'.split()):                                                                             # las vocales largas que modulan a la cueva (III)
    vocales.append(dict(t=round(ts('III', 2 + 3.5 * i), 4), dur=round(3 * BAR, 4), texto=v, nota=round(tema(i, 1), 3)))
FINAL = [('que dan do a luz más cier ta', [tema(7, 1), tema(6, 1), tema(5, 1), tema(5, 1), tema(4, 1), tema(3, 1), tema(4, 1), tema(3, 1)], [2, 2, 3, 2, 4, 3, 3, 9]),
         ('el mun do i lu mi na do', [tema(4, 1), tema(3, 1), tema(3, 1), tema(2, 1), tema(3, 1), tema(2, 1), tema(1, 1), tema(1, 1)], [2, 3, 3, 2, 2, 2, 3, 9]),
         ('y yo des pier ta', [tema(2, 1), tema(1, 1), tema(1, 1), tema(0, 1), tema(0, 1)], [3, 3, 3, 6, 20])]                # el tema A baja
for i, (txt, alt, rit) in enumerate(FINAL):
    frase(lead, txt, ts('V', 3 + 5 * i), alt, rit); coral(txt, ts('V', 3 + 5 * i), [a + 12 for a in alt], rit)

# ═════════ katajjaq: dos gargantas que se tiran pulsos (III), y el bordón gutural (I y IV) ═════════
garganta = []
a, z = SEC['III']; t = a + 1; per = .5; lado = 0
while t < z - 2:
    garganta.append(dict(t=round(t, 4), dur=round(per * .45, 4), nota=round(TON + 12 + (5 if lado else 0) + R.choice([0, 0, 7]), 3), fonemas=[['h', 'a'], ['m', 'u'], ['h', 'e'], ['n', 'o']][(lado * 2 + int(t)) % 4],
                         v=.85, aprende=.75, ronco=.55, lado=lado))
    t += per; per = max(.16, per * .985); lado = 1 - lado                                                              # el canon se aprieta
bordon = [dict(t=round(SEC[s][0] + .5, 3), dur=round(SEC[s][1] - SEC[s][0] - 1, 3), nota=round(TON, 3), fonemas=['a'], v=.45, aprende=.1, ronco=.95) for s in ('I', 'IV')]

# ═════════ Codex: el órgano de divisores (III) y la boca (el alma, III) y la sala (IV) ═════════
TT = dict(organo=dict(notas=[dict(t=round(SEC['III'][0], 3), midi=round(TON + 24, 3), dur=round(SEC['IV'][1] - SEC['III'][0], 3), vel=.8, pan=0, ataque=2, soltar=3)],
                      controles=dict(presion=[[0, 0], [SEC['III'][0], .05], [SEC['III'][0] + 16, .95], [SEC['III'][1], .5], [SEC['IV'][0] + 8, .2], [SEC['IV'][1], .5], [DUR, 0]])),
          boca=dict(notas=[dict(t=round(ts('III', 4 + 3 * i), 4), midi=round(tema(i, 2), 3), dur=round(2.6 * BAR, 4), vel=.75, pan=0) for i in range(6)],
                    vocales=[[round(ts('III', 4 + 1.3 * i), 3), 'aoeiua'[i % 6]] for i in range(14)], consonantes=[], controles=dict(vibrato=[[0, .2], [DUR, .5]])),
          sala=dict(notas=[dict(t=round(ts('IV', b, 3), 4), midi=round(gr(R.choice([0, 2, 4, 6]), 1), 3), dur=.4, vel=.6, pan=0) for b in range(0, 22, 2)],
                    controles=dict(pliegue_0=[[0, .2], [SEC['IV'][0], .2], [SEC['IV'][1], .95], [DUR, .9]], pliegue_1=[[0, .3], [SEC['IV'][0], .9], [SEC['IV'][1], .1], [DUR, .1]])))
aves = [dict(t=round(R.uniform(SEC['I'][0] + 5, SEC['III'][1]), 3), tipo='ronco', m=R.choice([60, 62]), m2=58, dur=round(R.uniform(.3, .7), 3), v=.35, voz=0) for _ in range(9)]   # aves de noche
VINILO = [[0, .15], [SEC['II'][0], .6], [SEC['II'][1], .6], [SEC['III'][0], .2], [SEC['IV'][0], .7], [SEC['V'][0], .3], [DUR, .1]]

partitura = dict(titulo='Primero sueño en el cenote', semilla=SEMILLA, terreno=f"traspuesta 43 «{TER['nombre']}», {TER['relieve']} m, {TER['anchoKm']} km, {len(CAM)} dolinas",
                 tonica=round(TON, 3), bpm=BPM, compas=BAR, dieciseisavo=S16, tema=TEMA, secciones=[dict(num=k, t=v[0], t1=v[1]) for k, v in SEC.items()], duracion=round(DUR, 3),
                 camaras_info=CAM, camaras=CAMARAS, gotas=gotas, para=PARA, metronomos=METRO, web=ev, sub=sub, trazos=trazos, garganta=garganta, bordon=bordon, tres_tiempos=TT, aves=aves, vinilo=VINILO,
                 sabina=[dict(eventos=lead, nivel=.9, pan=0, capa='lead'), dict(eventos=coro, nivel=.85, pan=0, capa='coro'), dict(eventos=chops, nivel=.85, pan=0, capa='chops'),
                         dict(eventos=vocales, nivel=.85, pan=0, capa='vocales')], coros=coros, instrumentos=None, tres_tiempos_codigo='tres-tiempos-6b17c3ba5aa8')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    inst = [d for d in os.listdir(AQUI) if d.startswith('instrumentos-')]; partitura['instrumentos'] = inst[0] if inst else None
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', round(DUR, 1), 's · tónica', round(TON, 2), '·', len(CAM), 'cámaras (cenotes', sum(c['cenote'] for c in CAM), ') · secciones', SEC)
    print('gotas', len(gotas), '· metrónomos', len(METRO), '· garage', {k: len(v) for k, v in ev.items()}, '· katajjaq', len(garganta), '· lead', len(lead), '· coro', len(coro), '· chops', len(chops))
    print('cámaras (fh, fb):', [(c['fh'], c['fb'], c['radio_m']) for c in CAM[:6]])
