"""La duna que canta — partitura. Gnawa × blues del desierto (tishoumaren) × Steve Reich × hyperpop seco, sobre la duna 675 de
Traspuesta («TALI», barjanes: arena en movimiento, viento del noreste) y las lecturas de teoría (LECTURAS.md).

TODO SE MIDE CONTRA LA DUNA (Darmstadt: cada valor es relativo). La nota es la de una duna que brama: f₀ = 0.4·√(g/d) con un
grano de d = 0.26 mm → 77.7 Hz (un mi bemol grave, un poco bajo). La escala es la pentatónica menor sobre f₀ (la de los gnawa
y la de Tinariwen). EL PULSO ES LA NOTA CUATRO OCTAVAS ABAJO (Stockhausen, la unidad del tiempo musical; Gruppen): la corchea
del 12/8 vale f₀/16 = 4.86 golpes por segundo, así que cuando una avalancha acelera las palmas cuatro octavas, el ritmo SE
VUELVE la nota de la duna (Kontakte X, al revés: clics → altura → clics).

LA FORMA ES D'EAU ET DE PIERRE (Grisey): un sonido absoluto, liso (el bramido pp de la duna con su viento) y piedras que lo
perturban (las avalanchas), cada una con más grado de cambio que la anterior.
  I    sonido absoluto · Ryoan-ji   la duna respira; la garganta de duna canta el contorno de las crestas como glisandos (Cage)
                                    sobre golpes sueltos sembrados (la grava rastrillada)
  II   gnawa                        guembri con sersera, qraqeb en 12/8, palmas; Sabina llama y el coro de vocoders responde
                                    («todavía llega algo»); entra el hyperpop seco (808 sin reverb)
  III  avalancha 1                  las palmas aceleran de 4.86 a 77.7 Hz: la duna canta (grado de cambio 1)
  IV   blues del desierto · fase    guitarra del desierto con ligados; Clapping Music (Reich) — la segunda palma se corre un pulso
                                    cada dos compases: la duna migra; la letra ya sin yo; solo de guitarra NÓMADA (Khannanov):
                                    sin compás, el perfil de cada cresta es la melodía, acentos por gradación
  V    avalancha 2                  la duna brama entera, una segunda duna de grano más fino (93 Hz) encima: batido; regresa a
                                    clics (Kontakte X completo: ritmo → tono → ritmo)
  VI   correr al revés              la arena negra y la blanca mezcladas: el gnawa suena al revés y no se separa; el vocoder de
                                    duna canta solo («correr al revés no los separa», Smithson)
  VII  una palabra                  Scelsi: la nota sola con profundidad; la letra se contrae a una palabra: algo → al
La letra sale de la caja de arena de Li Po (netart/poemario): granos de *Todavía llega algo*, y con cada avalancha se va la
primera persona.
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np

SEMILLA = 675
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__)); G = 360
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-675.f32'), dtype=np.float32).reshape(G, G)
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-675.json'), encoding='utf-8'))
m_de = lambda f: 69 + 12 * math.log2(f / 440)

# ── la duna da la nota y el pulso ──
GRANO = 0.26e-3; F0 = 0.4 * math.sqrt(9.81 / GRANO); RAIZ = m_de(F0)          # 77.7 Hz
GRANO2 = 0.18e-3; F0B = 0.4 * math.sqrt(9.81 / GRANO2)                        # la segunda duna, más fina: 93.4 Hz
T3 = 16 / F0; BAR = 12 * T3                                                   # corchea = 4 octavas abajo del bramido; 12/8
PENTA = [0, 3, 5, 7, 10]
def grado(g, oct_=0): o, r = divmod(g, 5); return RAIZ + 12 * (oct_ + o) + PENTA[r]
def t_(b, s=0.0): return b * BAR + s * T3                                     # compás b, tresillo s

SECC = [(0, 'I', 'SONIDO ABSOLUTO · RYOAN-JI'), (10, 'II', 'GNAWA'), (30, 'III', 'AVALANCHA'), (34, 'IV', 'BLUES DEL DESIERTO · FASE'),
        (62, 'V', 'LA DUNA BRAMA'), (68, 'VI', 'CORRER AL REVÉS'), (76, 'VII', 'UNA PALABRA')]
FIN_BAR = 86; DUR = t_(FIN_BAR) + 7
INI = {s: b for b, s, _ in SECC}

# ── las crestas: un transecto por cada pico, del noreste (barlovento, ladera suave) al suroeste (cara de avalancha, abrupta) ──
def transecto(p, n=48, alcance=.11):
    s = np.linspace(alcance, -alcance, n); u = p['u'] + s / math.sqrt(2); v = p['v'] - s / math.sqrt(2)
    x = np.clip(u * (G - 1), 0, G - 1); y = np.clip(v * (G - 1), 0, G - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int); x1, y1 = np.minimum(x0 + 1, G - 1), np.minimum(y0 + 1, G - 1); fx, fy = x - x0, y - y0
    h = H[y0, x0] * (1 - fx) * (1 - fy) + H[y0, x1] * fx * (1 - fy) + H[y1, x0] * (1 - fx) * fy + H[y1, x1] * fx * fy
    return h / (h.max() or 1)
PICOS = sorted(TER['rasgos']['picos'], key=lambda p: -p['prom'])[:15]          # quince crestas, como las quince piedras de Ryoan-ji
CRESTAS = [transecto(p) for p in PICOS]
def nomada(perfil, t0, base_g=2, rango=8, unidad=.075, v0=.5):
    """el perfil como melodía (Khannanov): grados de la pentatónica que siguen la altura; la ladera suave da notas largas, la
    cara de avalancha corre hacia abajo; los acentos por gradación (más fuerte cuanto más alto, sin tiempo fuerte)"""
    gs = [base_g + int(round(h * rango)) for h in perfil]; notas = []; t = t0; i = 0
    while i < len(gs):
        j = i
        while j + 1 < len(gs) and gs[j + 1] == gs[i]: j += 1
        d = (j - i + 1) * unidad; h = float(perfil[i:j + 1].max())
        if h > .04: notas.append(dict(t=round(t, 4), dur=round(d, 4), g=gs[i], v=round(v0 + (1 - v0) * h, 3), h=round(h, 3)))
        t += d; i = j + 1
    return notas, t

ev = {k: [] for k in ['bateria', 'bateria-frito', 'palmas1', 'palmas2', 'tende']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr808', stem='bateria'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)
guembri, guitarra, qraqeb, sub, garganta = [], [], [], [], []

# ═════════ I · sonido absoluto · Ryoan-ji ═════════
# la garganta de duna canta el contorno de cuatro crestas (glisandos continuos, liso), sobre golpes sueltos en lugares sembrados
t = t_(1)
for k in range(4):
    perfil = CRESTAS[k]; d = R.uniform(4.2, 5.6)
    curva = [[round(i / (len(perfil) - 1), 4), round(grado(5, 0) + 9 * float(h), 3)] for i, h in enumerate(perfil)]
    garganta.append(dict(t=round(t, 3), dur=round(d, 3), nota=curva[0][1], curva=curva, fonemas=[['a'], ['u'], ['o'], ['a']][k], v=.55, aprende=.55, ronco=0, ryoanji=k))
    t += d + R.uniform(.6, 1.4)
for _ in range(9):                                                            # la grava: un solo golpe, aquí o allá
    tg = R.uniform(t_(.5), t_(INI['II']) - 1)
    if R.random() < .5: qraqeb.append(dict(t=round(tg, 4), v=round(R.uniform(.3, .6), 3), pan=round(R.uniform(-.7, .7), 2)))
    else: web('tende', tg, 'meleeviewer-13-conga', 55, R.uniform(.4, .7), .3, R.uniform(-.5, .5))

# ═════════ II · gnawa ═════════
QRAQEB = [(0, 1), (2, .55), (3, .8), (5, .55), (6, .9), (8, .55), (9, .8), (11, .55)]   # el galope: largo-corto, acento en 1 4 7 10
RIFF_G = [(0, 0, 0, 1.6), (2, 0, 0, .9), (3, 2, 0, .9), (5, 1, 0, .9), (6, 0, 0, 1.6), (8, -1, 0, .9), (9, 0, 0, .9), (10, 1, 1, .9),   # (tresillo, grado, liga, largo)
          (12, 3, 0, 1.6), (14, 2, 1, .9), (15, 1, 0, .9), (17, 0, 0, .9), (18, 0, 0, 1.6), (20, -1, 0, .9), (21, -2, 0, 1.4), (23, -1, 1, .9)]
def guembri_2(b, oct_=-1, v=.85):
    for s, g, liga, d in RIFF_G:
        guembri.append(dict(t=round(t_(b, s), 4), dur=round(d * T3, 4), m=round(grado(g, oct_), 3), v=round(v * (1 if s % 6 == 0 else .8), 3), liga=liga, c=0))
def qraqeb_bar(b, v=1.0, pan=0.0):
    for s, a in QRAQEB: qraqeb.append(dict(t=round(t_(b, s) + R.gauss(0, .004), 4), v=round(a * v, 3), pan=pan))
def hyper(b, lleno=True):
    """hyperpop seco: 808 sin reverb; bombo en 0, 7 y 9 (contra el galope), clap en 6, hats en seisillos con ráfagas"""
    for s, v in ((0, 1), (7, .8), (9, .7)) if lleno else ((0, .9),):
        bat(t_(b, s), 'kick', v); sub.append(dict(t=round(t_(b, s), 4), dur=round(2.5 * T3, 4), midi=round(grado(0, -1), 3), vel=v))
    if lleno:
        web('bateria-frito', t_(b, 6), 'bateria-frito', 60, .85, .2, 0, pieza='clap')
        for q in range(24):
            if q % 2 == 0 or R.random() < .3: bat(t_(b, q / 2), 'hat', .25 + .25 * (q % 4 == 0), .25)
        if b % 2 == 1:                                                         # la ráfaga: 1/8 de tresillo en el último tiempo
            for q in range(8): bat(t_(b, 9 + q * 3 / 8), 'hat', .2 + .05 * q, -.25)
for b in range(INI['II'], INI['III']):
    if (b - INI['II']) % 2 == 0: guembri_2(b)
    qraqeb_bar(b, .9 if b >= INI['II'] + 2 else .6, .3)
    if b >= INI['II'] + 4:
        for s in (0, 3, 6, 9): web('palmas1', t_(b, s), 'meleeviewer-3-clap', 60, .55 + .2 * (s == 0), .2, -.35)
    if b >= INI['II'] + 8: hyper(b)
    if b % 2 == 0 and b >= INI['II'] + 2: web('tende', t_(b), 'meleeviewer-13-conga', 55, .7, .3, -.2)

# ── la letra (granos de «Todavía llega algo», caja de arena de Li Po) ──
LLAMADAS_1 = ['yo ya no es ta ré e xac ta men te a quí', 'con fir mo que no lle vo a na die', 're gis tro u na lí ne a a zul', 'la luz ca yó so bre mis cá ma ras']
LLAMADAS_2 = ['ya no es ta rá e xac ta men te a quí', 'que no lle va a na die', 'u na lí ne a a zul', 'las flo res del de sier to re na cen con la mí ni ma llu via']   # sin yo
RESPUESTA = 'to da ví a lle ga al go'
REVES = ['co rrer al re vés', 'no los se pa ra']
FINAL = ['to da ví a lle ga al go', 'lle ga al go', 'al go', 'al']
lead, soprano, coros = [], [], {v: [] for v in 'SATB'}
def llamada(texto, b, perfil):
    """Sabina llama con la melodía de una cresta (una sílaba por nota de la cresta, melisma si sobran)"""
    sil = texto.split(); notas, _ = nomada(perfil, t_(b), base_g=5, rango=5, unidad=.11)
    notas = [n for n in notas if n['h'] > .15] or notas
    paso_ = max(T3 * 1.0, min(T3 * 2, (2 * BAR - T3) / len(sil))); t = t_(b)
    for i, sy in enumerate(sil):
        n = notas[min(len(notas) - 1, int(i * len(notas) / len(sil)))]
        lead.append(dict(t=round(t, 4), dur=round(paso_ * (.92 if i < len(sil) - 1 else 1.6), 4), texto=sy, nota=round(grado(n['g'], 0), 3)))
        t += paso_
def respuesta(b, texto=RESPUESTA):
    sil = texto.split(); ritmo = [1, 1, 2, 2, 1, 1, 2, 4][:len(sil)]; s = 0
    MEL = [7, 6, 5, 5, 6, 5, 4, 3]
    for i, (sy, d) in enumerate(zip(sil, ritmo)):
        sop = grado(MEL[i % 8], 0); dur = d * T3 * (.92 if i < len(sil) - 1 else 1.0)
        for v, n in zip('SATB', (sop, grado(MEL[i % 8] - 2, 0), grado(MEL[i % 8] - 4, 0), grado(0, -1))):
            coros[v].append(dict(t=round(t_(b, s), 4), dur=round(dur, 4), texto=sy, nota=round(n, 3)))
        soprano.append(dict(t=round(t_(b, s), 4), dur=round(dur, 4), texto=sy, nota=round(sop, 3)))
        s += d
for i, txt in enumerate(LLAMADAS_1):
    b = INI['II'] + 4 + 4 * i; llamada(txt, b, CRESTAS[4 + i]); respuesta(b + 2)
# la garganta de duna canta el tenor de las respuestas
for e in coros['T']: garganta.append(dict(t=e['t'], dur=e['dur'], nota=round(e['nota'] - 12, 3), texto=e['texto'], v=.6, aprende=.85, ronco=0))

# ═════════ III · avalancha 1 (grado de cambio 1) ═════════
A1 = t_(INI['III']); A1f = t_(INI['IV'])
for s in range(0, 12, 3): web('palmas1', t_(INI['III'], s), 'meleeviewer-3-clap', 60, .7, .2, -.35)   # las palmas que la duna va a acelerar
qraqeb_bar(INI['III'], .7, .3)

# ═════════ IV · blues del desierto · fase ═════════
CLAP = [1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0]                                   # Clapping Music (Reich, 1972): 3-2-1-2
RIFF_GT = [(0, 4, 1, 0), (1, 3, 1, 1), (2, 2, 1, 0), (3, 0, 1, 0), (5, 2, 0, 0), (6, 4, 1, 0), (7, 5, 1, 1), (8, 4, 1, 1), (9, 2, 1, 0), (11, 0, 1, 0),   # (tresillo, grado, oct, liga)
           (12, 1, 1, 0), (13, 0, 1, 1), (14, 4, 0, 0), (15, 3, 0, 0), (17, 2, 0, 0), (18, 0, 1, 0), (20, 4, 0, 0), (21, 2, 0, 1), (22, 0, 0, 0)]
def guitarra_2(b, v=.75):
    for s, g, o, liga in RIFF_GT:
        guitarra.append(dict(t=round(t_(b, s), 4), dur=round(T3 * .95, 4), m=round(grado(g, o + 1), 3), v=round(v * (1 if s % 6 == 0 else .8), 3), liga=liga, c=1))
    for s in (0, 12): guitarra.append(dict(t=round(t_(b, s), 4), dur=round(6 * T3, 4), m=round(grado(0, 0), 3), v=round(v * .7, 3), c=0))   # el bordón al aire
FASE0 = INI['IV'] + 2
for b in range(INI['IV'], INI['V']):
    if (b - INI['IV']) % 2 == 0 and b < INI['IV'] + 16: guitarra_2(b)
    if (b - INI['IV']) % 2 == 0: guembri_2(b, v=.6)
    k = (b - FASE0) // 2 if FASE0 <= b < FASE0 + 24 else (0 if b < FASE0 else 12)
    for s in range(12):
        if CLAP[s] and b >= INI['IV'] + 1: web('palmas1', t_(b, s), 'meleeviewer-3-clap', 60, .6 + .15 * (s == 0), .2, -.55)
        if CLAP[(s + k) % 12] and FASE0 <= b < FASE0 + 24: web('palmas2', t_(b, s), 'meleeviewer-2-clap', 62, .6 + .15 * (s == 0), .2, .55)
    if b % 2 == 0: web('tende', t_(b), 'meleeviewer-13-conga', 55, .6, .3, -.2)
    qraqeb_bar(b, .45, .4)
    if b >= INI['IV'] + 4: hyper(b, lleno=(b - INI['IV']) % 4 != 3)
for i, txt in enumerate(LLAMADAS_2):
    b = INI['IV'] + 2 + 4 * i; llamada(txt, b, CRESTAS[8 + i]); respuesta(b + 2)
for e in coros['T']:
    if e['t'] >= A1f and e['t'] < t_(INI['V']): garganta.append(dict(t=e['t'], dur=e['dur'], nota=round(e['nota'] - 12, 3), texto=e['texto'], v=.6, aprende=.85, ronco=0))
# el solo de guitarra, nómada: tres crestas seguidas, sin compás; la cara de avalancha baja con deslices
t = t_(INI['IV'] + 18); solo_crestas = []
for k in (12, 13, 14, 10, 11, 7, 6, 9):
    notas, t2 = nomada(CRESTAS[k], t, base_g=3, rango=9, unidad=.085, v0=.4); solo_crestas.append(dict(cresta=k, t0=round(t, 3), t1=round(t2, 3)))
    prev = None
    for n in notas:
        baja = prev is not None and n['g'] < prev - 1                       # la cara de avalancha: desliz
        guitarra.append(dict(t=n['t'], dur=n['dur'], m=round(grado(n['g'], 1), 3), v=n['v'], c=1, liga=1 if prev is not None and abs(n['g'] - prev) == 1 and n['dur'] < .2 else 0,
                             desliz=round(min(.12, n['dur'] * .6), 3) if baja else 0, solo=1))
        prev = n['g']
    t = t2 + T3 * R.choice([2, 3, 4])
    if t > t_(INI["V"]) - 4.5: break

# ═════════ V · la duna brama (avalancha 2) · VI · correr al revés · VII · una palabra ═════════
A2 = t_(INI['V']); A2f = t_(INI['VI'])
for s in range(0, 12, 3): web('palmas1', t_(INI['V'], s), 'meleeviewer-3-clap', 60, .75, .2, -.35)
REVES_DE = (t_(INI['II'] + 4), t_(INI['II'] + 12))                            # lo que suena al revés en VI (y no se separa)
for i, txt in enumerate(REVES):                                               # el vocoder de duna canta solo; Sabina modula
    b = INI['VI'] + 1 + 3 * i; sil = txt.split()
    for j, sy in enumerate(sil):
        d = T3 * (3 if j == len(sil) - 1 else 2)
        soprano.append(dict(t=round(t_(b, 2 * j), 4), dur=round(d, 4), texto=sy, nota=round(grado([7, 6, 5, 6, 4][j % 5] - i, 0), 3), solo_vocoder=1))
for i, txt in enumerate(FINAL):                                               # se contrae a una palabra
    b = INI['VII'] + 1 + 2 * i; sil = txt.split()
    for j, sy in enumerate(sil):
        d = T3 * (2 if j < len(sil) - 1 else 5)
        e = dict(t=round(t_(b, 2 * j), 4), dur=round(d, 4), texto=sy, nota=round(grado([7, 6, 5, 5, 6, 5, 4, 3][j + 8 - len(sil)], 0), 3))
        lead.append(e); garganta.append(dict(t=e['t'], dur=e['dur'], nota=round(e['nota'] - 12, 3), texto=sy, v=.55, aprende=.9, ronco=0, solo=1))

# ═════════ la duna, el viento ═════════
r1 = lambda: round(R.uniform(.9, 1.1), 3)
DUNA = dict(   # f(t), K(t) en múltiplos del umbral de Kuramoto, flujo(t) 0–1
    f=[[0, F0], [A1 - .1, F0], [A1, F0 / 16], [A1 + BAR * .9, F0 / 16], [A1 + BAR * 2.6, F0], [A2, F0], [A2 + .01, F0 / 16], [A2 + BAR * .6, F0 / 16], [A2 + BAR * 1.4, F0],
       [A2 + BAR * 4.2, F0], [A2 + BAR * 5.6, F0 / 8], [A2f, F0 / 16], [t_(INI['VII']) - .1, F0 / 16], [t_(INI['VII']), F0], [DUR, F0 * 2 ** (-8 / 1200)]],
    K=[[0, 1.2], [t_(4), 1.6], [t_(8), 1.1], [t_(INI['II']), .4], [A1 - .1, .4], [A1, 3], [A1 + BAR * 3.2, 3], [A1f, .5], [A2 - .1, .5], [A2, 3.5], [A2 + BAR * 5, 3.5], [A2f - 1, 1.2],
       [A2f, .3], [t_(INI['VII']), .3], [t_(INI['VII']) + 2, 2.2], [t_(INI['VII'] + 6), 1.5], [t_(FIN_BAR - 2), 1.0], [DUR, .2]],
    flujo=[[0, 0], [3, .3], [t_(INI['II']) - 2, .3], [t_(INI['II']), .12], [A1 - .2, .12], [A1, .5], [A1 + BAR * 2.6, 1], [A1 + BAR * 3.4, .8], [A1f, .15], [A2 - .1, .15], [A2, .6],
           [A2 + BAR * 1.4, 1], [A2 + BAR * 4.2, 1], [A2f, .4], [A2f + 2, .1], [t_(INI['VII']), .1], [t_(INI['VII']) + 3, .55], [t_(FIN_BAR - 3), .5], [t_(FIN_BAR) + 4, 0], [DUR, 0]])
DUNA2 = dict(f=[[0, F0B], [DUR, F0B]], K=[[0, 0], [A2 + BAR * 1.6, 0], [A2 + BAR * 2.2, 3], [A2 + BAR * 4, 3], [A2 + BAR * 4.6, 0], [DUR, 0]],
             flujo=[[0, 0], [A2 + BAR * 1.4, 0], [A2 + BAR * 2.2, .8], [A2 + BAR * 4, .8], [A2 + BAR * 4.8, 0], [DUR, 0]])
PERFILES = [[round(DUR * k / 14, 3), [round(float(x), 4) for x in CRESTAS[k]]] for k in range(15)]
VIENTO = dict(vel=[[0, 6], [t_(INI['II']), 9], [A1, 16], [A1f, 8], [A2, 18], [A2f, 7], [t_(INI['VII']), 10], [DUR, 4]],
              estria=[[0, 0], [t_(INI['II']) - 2, 0], [t_(INI['II']) + 2, .85], [A2, .85], [A2 + 3, 0], [DUR, 0]],
              escala=PENTA, periodo=12, base=round(RAIZ + 24, 3))

partitura = dict(titulo='La duna que canta', semilla=SEMILLA, terreno=f"traspuesta 675 «{TER['nombre']}» ({', '.join(TER['historia'])}), relieve {TER['relieve']} m",
                 grano_mm=GRANO * 1e3, f0=round(F0, 4), f0b=round(F0B, 4), raiz=round(RAIZ, 4), tresillo=round(T3, 6), compas=round(BAR, 6), escala=PENTA,
                 secciones=[dict(bar=b, t=round(t_(b), 3), num=s, nombre=n) for b, s, n in SECC], duracion=round(DUR, 3), fin=round(t_(FIN_BAR), 3),
                 picos=[dict(u=round(p['u'], 4), v=round(p['v'], 4), prom=round(p['prom'], 4)) for p in PICOS], crestas=[[round(float(x), 4) for x in c] for c in CRESTAS],
                 web=ev, guembri=guembri, guitarra=guitarra, qraqeb=qraqeb, sub=sub, garganta=garganta, duna=DUNA, duna2=DUNA2, viento=VIENTO, perfiles=PERFILES,
                 sabina=[dict(eventos=lead, nivel=.9, pan=0, capa='lead'), dict(eventos=soprano, nivel=.85, pan=0, capa='soprano')], coros=coros,
                 reves=dict(de=[round(x, 3) for x in REVES_DE], a=[round(t_(INI['VI']), 3), round(t_(INI['VII']), 3)]), clapping=CLAP, fase0=round(t_(FASE0), 3),
                 avalanchas=[[round(A1, 3), round(A1f, 3)], [round(A2, 3), round(A2f, 3)]], solo=solo_crestas,
                 letra=dict(llamadas_1=LLAMADAS_1, llamadas_2=LLAMADAS_2, respuesta=RESPUESTA, reves=REVES, final=FINAL), instrumentos='instrumentos-381572fc353a')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', round(DUR, 1), 's · f0', round(F0, 2), 'Hz (midi', round(RAIZ, 2), ') · tresillo', round(T3, 4), 's · compás', round(BAR, 3), 's · 2ª duna', round(F0B, 1), 'Hz')
    print({k: len(v) for k, v in ev.items()}, '· guembri', len(guembri), '· guitarra', len(guitarra), '· qraqeb', len(qraqeb), '· garganta', len(garganta), '· lead', len(lead), '· soprano', len(soprano))
    print('solo', solo_crestas)
