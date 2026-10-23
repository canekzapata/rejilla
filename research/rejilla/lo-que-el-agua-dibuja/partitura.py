"""Lo que el agua dibuja — partitura. Blues del Delta con slide × drill × las nubes de glisandos de Xenakis (*Pithoprakta*), sobre las
tierras malas 67 de Traspuesta. Su historia la dice la lámina: ARCILLAS → LLUVIAS RARAS Y VIOLENTAS → CÁRCAVAS → TIERRAS MALAS; la
canción termina en la boca de su cárcava mayor, Yucha Ka'nu («río grande», en mixteco). Diseño en DISENO.md.

EL SLIDE TOCA EL TERRENO. La cárcava mayor mide 7.7 km y baja 127 m. Su perfil (altitud contra distancia, de la cabecera a la boca)
es la partitura de la guitarra: un semitono cada 7 m, la boca en la tónica (una octava arriba). Cada coro de 12 compases la guitarra
camina la cárcava de arriba abajo; sus notas son el perfil cuantizado a la escala de blues (o a los tonos del acorde en IV y V) y,
entre nota y nota, el vidrio se desliza por el perfil mismo. Donde le llega un afluente, la guitarra toca su riff: cae desde la
altura del afluente hasta la de la junta.
LA LLUVIA ES XENAKIS. Cada tormenta es una nube de glisandos: gotas de Poisson, rectas en altura–tiempo con velocidades de Maxwell
(la «temperatura» sube con la tormenta). Cada gota cae en un lugar del cuenco (más abajo, más cuenca) y SUENA a la altura del terreno
donde cae (dos octavas arriba): la que cae en la cabecera, aguda; la que cae cerca de la boca, grave.
CADA GOTA ERODA. La cárcava se ahonda con la ley de potencia de corriente, dz/dt = −K Q^½ S (Q: las gotas que cayeron aguas arriba
en ese cuarto de segundo; S: la pendiente), resuelta implícita aguas arriba desde la boca, que no se mueve (el nivel de base). Las
gargantas retroceden aguas arriba. El slide se hunde tormenta tras tormenta: el coro siguiente camina la cárcava nueva. La erosión
está EXAGERADA (miles de años en tres tormentas); su forma es la de la ley.
EL RAYO Y EL TRUENO. Los rayos caen en los cerros con nombre de la lámina; quien escucha está en la boca. El trueno llega a r/343 s
del relámpago y su retumbo es la forma del rayo leída por distancias (Few).
LA CRECIDA. Lo que llueve llega a la boca después: el hidrograma (la lluvia por una gamma) da el caudal; con él suben el rugido y los
pedregones del arrastre de fondo.
EL DRILL. Blues a 70 por negra = drill a 140: el mismo pulso. Los hi-hats redoblan con los ceros de zeta (los primos en accelerando
o en ritardando hacia el tiempo fuerte) y el 808 se desliza de nota en nota.
LA TÓNICA. La cárcava mayor como tubo abierto, f = 343 / (2 · 7699 m), subida 12 octavas: 91.25 Hz.
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np
from scipy.ndimage import gaussian_filter1d
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); import sintes11 as S11

SEMILLA = 67
R = random.Random(SEMILLA); RG = np.random.default_rng(SEMILLA)
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-67.json'), encoding='utf-8'))
CAU = json.load(open(os.path.join(AQUI, 'terreno', 'cauce-67.json'), encoding='utf-8'))
m_de = lambda f: 69 + 12 * math.log2(f / 440)

# ── la cárcava: el perfil, la tónica, los afluentes ──
PF = np.array(CAU['perfil']); LARGO = float(PF[-1, 0]); NX = 400; XS = np.linspace(0, LARGO, NX); DX = XS[1]
Z0 = np.interp(XS, PF[:, 0], PF[:, 1]); Z0 = gaussian_filter1d(Z0, 1.5, mode='nearest'); Z0 = np.minimum.accumulate(Z0)   # un cauce siempre baja
Z_BOCA = float(Z0[-1]); U_C = np.interp(XS, PF[:, 0], PF[:, 2]); V_C = np.interp(XS, PF[:, 0], PF[:, 3])
f = 343 / (2 * LARGO); octv = 0
while f < 55: f *= 2; octv += 1
TON = m_de(f)
M_POR_SEMI = 7.0                                                                                  # metros por semitono
def m_terreno(z): return TON + 12 + (np.asarray(z) - Z_BOCA) / M_POR_SEMI
AFL = [a for a in CAU['afluentes'] if a['largo'] >= 300]
BOCA = dict(u=float(U_C[-1]), v=float(V_C[-1]))
NOMBRES = {n['nombre']: n for n in TER['nombres']}

# ── el tiempo ──
BPM = 70; NEGRA = 60 / BPM; COMPAS = 4 * NEGRA; T8 = NEGRA / 3; G = NEGRA / 8                         # T8: corchea de tresillo (shuffle); G: semicorchea a 140
FORMA = [('I', 'ARCILLAS', 14, 'coro'), ('t1', 'LLUVIAS RARAS Y VIOLENTAS', 4, 'tormenta'), ('II', 'LLUVIAS RARAS Y VIOLENTAS', 12, 'coro'),
         ('t2', 'CÁRCAVAS', 4, 'tormenta'), ('IIIr', 'CÁRCAVAS', 8, 'rap'), ('III', 'CÁRCAVAS', 12, 'coro'),
         ('t3', 'TIERRAS MALAS', 6, 'tormenta'), ('IV', 'TIERRAS MALAS', 12, 'coro'), ('V', "YUCHA KA'NU", 8, 'boca')]
SEC = {}; t0 = 0.0
for k, nom, nb, tipo in FORMA: SEC[k] = dict(t=round(t0, 4), t1=round(t0 + nb * COMPAS, 4), compases=nb, nombre=nom, tipo=tipo); t0 += nb * COMPAS
DUR = round(t0 + 7.0, 3)
def ts(sec, b, u=0.0): return SEC[sec]['t'] + b * COMPAS + u * T8                                  # u en corcheas de tresillo
BLUES = [0, 0, 0, 0, 5, 5, 0, 0, 7, 5, 0, 7]
ACORDES = {'I': [0, 0] + BLUES, 'II': BLUES, 'III': BLUES, 'IV': BLUES, 'IIIr': [0, 0, 0, 0, 5, 5, 0, 0], 'V': [0, 0, 5, 0, 7, 5, 0, 0], 't1': [0] * 4, 't2': [0] * 4, 't3': [0] * 6}
def acorde_en(t):
    for k, s in SEC.items():
        if s['t'] <= t < s['t1']: return ACORDES[k][min(len(ACORDES[k]) - 1, int((t - s['t']) / COMPAS))]
    return 0
ESCALA = {0: [0, 3, 5, 6, 7, 10], 5: [0, 3, 5, 9, 10], 7: [2, 5, 7, 10, 11]}
def cuantiza(m, ac):
    c = [TON + o * 12 + g for o in range(-2, 5) for g in ESCALA[ac]]; return min(c, key=lambda x: abs(x - m))

# ═════════ las tormentas: gotas de Xenakis, erosión, rayos ═════════
TORMENTAS = dict(t1=dict(pico=26, toques=dict(pizz=.85, col=.15), rayos=['YUKU ISO']),
                 t2=dict(pico=42, toques=dict(pizz=.7, arco=.15, col=.15), rayos=['LA CUCHILLA DEL ORIENTE', 'EL PORTICHUELO']),
                 t3=dict(pico=95, toques=dict(pizz=.5, arco=.35, col=.15), rayos=["YUKU KUA'A", "YUKU YA'A", 'YUKU LULU']))
IMAX = max(v['pico'] for v in TORMENTAS.values())
FR_LL = 20                                                                                          # la intensidad de lluvia, a 20 Hz
lluvia_I = np.zeros(int(DUR * FR_LL) + 1); tl = np.arange(len(lluvia_I)) / FR_LL
for k, T in TORMENTAS.items():
    a, z = SEC[k]['t'], SEC[k]['t1']; tp = a + .45 * (z - a); x = np.clip((tl - a) / (tp - a), 0, None)
    forma = np.where(tl < a, 0, np.where(tl <= tp, x ** 2 * np.exp(2 * (1 - x)), np.exp(-(tl - tp) / ((z - tp) * .55))))
    forma = np.where(tl > z, np.exp(-(z - tp) / ((z - tp) * .55)) * np.exp(-(tl - z) / 5.0), forma)     # la llovizna que se queda
    lluvia_I = np.maximum(lluvia_I, T['pico'] * forma)
lluvia_I[lluvia_I < .4] = 0
# dónde cae cada gota: el cauce mayor (más abajo, más cuenca: Hack, A ∝ x^1.67) o un afluente (todo entra por su junta)
A_MAIN = (XS + 300) ** 1.67; dA = np.gradient(A_MAIN); A_AFL = np.array([a['largo'] ** 1.67 for a in AFL]); A_TOT = A_MAIN[-1] + A_AFL.sum()
def lugar():
    r = R.random() * A_TOT
    if r < A_MAIN[-1]: i = int(np.searchsorted(np.cumsum(dA) / dA.sum(), R.random())); return min(i, NX - 1), None
    j = int(np.searchsorted(np.cumsum(A_AFL), r - A_MAIN[-1])); return int(np.argmin(np.abs(XS - AFL[min(j, len(AFL) - 1)]['en']))), min(j, len(AFL) - 1)
def toque_de(T, tt, a):
    if tt - a < 1.6 and R.random() < .6: return 'col'                                              # Pithoprakta empieza con golpes de madera
    r = R.random(); acc = 0
    for k, p in T['toques'].items():
        acc += p
        if r < acc: return k
    return 'pizz'
gotas = []; PASO_E = .25
fin_ll = len(lluvia_I) / FR_LL; tt = 0.0
while True:
    lam = IMAX + 1; tt += RG.exponential(1 / lam)
    if tt >= fin_ll - .05: break
    I = float(np.interp(tt, tl, lluvia_I))
    if R.random() > I / lam: continue
    k = [kk for kk in TORMENTAS if SEC[kk]['t'] <= tt][-1]; T = TORMENTAS[k]
    i, j = lugar(); temp = 3 + 15 * I / IMAX
    v = float(S11.maxwell(RG, temp)) * (-1 if R.random() < .7 else 1)
    toque = toque_de(T, tt, SEC[k]['t']) if tt < SEC[k]['t1'] else 'pizz'
    dur = R.uniform(.15, .9) if toque == 'pizz' else (R.uniform(.5, 2.5) if toque == 'arco' else .08)
    gotas.append(dict(t=round(tt, 4), i=i, afl=j, temp=round(temp, 2), v=round(v, 3), dur=round(dur, 3), toque=toque, a=round(R.uniform(.35, 1), 3),
                      pan=round(float(np.clip((U_C[i] - .5) * 1.6 + R.gauss(0, .15), -1, 1)), 3)))
# la erosión: cada cuarto de segundo, las gotas que cayeron hacen el caudal Q_i (las de aguas arriba de i) y la cárcava se ahonda
def erosiona(K):
    z = Z0.copy(); snaps = [(0.0, z.copy())]; tg = np.array([g['t'] for g in gotas]); ig = np.array([g['i'] for g in gotas])
    for w0 in np.arange(0, fin_ll, PASO_E):
        sel = (tg >= w0) & (tg < w0 + PASO_E)
        if not sel.any(): continue
        Q = np.cumsum(np.bincount(ig[sel], minlength=NX)).astype(float)
        c = K * np.sqrt(Q) * PASO_E / DX
        for i in range(NX - 2, -1, -1): z[i] = (z[i] + c[i] * z[i + 1]) / (1 + c[i])                 # implícito, aguas arriba desde la boca
        snaps.append((round(float(w0 + PASO_E), 3), z.copy()))
    return snaps
K = 1.0; OBJETIVO = 30.0                                                                            # lo más que se ahonda un punto, en m (exagerado)
for _ in range(3):
    sn = erosiona(K); K *= OBJETIVO / float(np.max(Z0 - sn[-1][1]))
SNAPS = erosiona(K); TSN = np.array([s[0] for s in SNAPS]); ZSN = np.array([s[1] for s in SNAPS])
def z_en(t): return ZSN[max(0, int(np.searchsorted(TSN, t, 'right')) - 1)]
for g in gotas:                                                                                      # cada gota suena a la altura del terreno donde cae, dos octavas arriba
    zt = z_en(g['t'])[g['i']] + (AFL[g['afl']]['baja'] * R.random() if g['afl'] is not None else 0)
    g['m0'] = round(float(m_terreno(zt)) + 24 + R.gauss(0, 3), 3)
    # r2: el arco llegaba a midi 172 (arriba de Nyquist: aliasing) y a −4. Ninguna gota glisa más de dos octavas, y si se saldría de
    # midi 40–112 cambia de dirección: la rapidez |v| (la de Maxwell) no cambia.
    g['dur'] = round(min(g['dur'], 24 / max(abs(g['v']), 1e-6)), 3) if g['toque'] != 'col' else g['dur']
    if not 40 <= g['m0'] + g['v'] * g['dur'] <= 112: g['v'] = -g['v']
# los rayos: caen en los cerros con nombre; quien escucha está en la boca
rayos = []
for k, T in TORMENTAS.items():
    for n, nom in enumerate(T['rayos']):
        c = NOMBRES[nom]; d = math.hypot(c['u'] - BOCA['u'], c['v'] - BOCA['v']) * TER['anchoKm'] * 1000
        llega = SEC[k]['t'] + COMPAS * (.5 + 1.3 * n); rayos.append(dict(lugar=nom, u=c['u'], v=c['v'], dist_m=round(d), retraso_s=round(d / 343, 2), relampago=round(llega - d / 343, 3), llega=round(llega, 3), tormenta=k, semilla=SEMILLA * 10 + len(rayos)))

# ═════════ la guitarra de cárcava ═════════
FR = 200; NC = int(DUR * FR) + 2; TC = np.arange(NC) / FR
notas = []                                                                                         # (t, m o None si es «vivo», desliz, v, púa, x_vivo, desde)
def caminar(t_a, t_b, d_a, d_b): return lambda t: d_a + (d_b - d_a) * np.clip((t - t_a) / (t_b - t_a), 0, 1)
TRAMOS = []                                                                                        # (t_a, t_b, función d(t)) — dónde está el vidrio
def m_paseo(t, d): return float(np.interp(d, XS, m_terreno(z_en(t))))
def nota(t, m, v=.75, desliz=None, pua=True, desde=0.0, vivo=None):
    notas.append(dict(t=round(t, 4), m=None if m is None else round(float(m), 3), v=round(v, 3), desliz=round(desliz if desliz is not None else .09, 3), pua=pua, desde=desde, vivo=vivo))
def coro_guitarra(sec, b0, nb, d_a, d_b, densidad=1.0, riffs=True):
    a, z = ts(sec, b0), ts(sec, b0 + nb); dfun = caminar(a, z, d_a, d_b); TRAMOS.append((a, z, d_a, d_b))
    tiempos = []
    for b in range(nb):
        pos = b % 4; tb = ts(sec, b0 + b)
        cand = {0: [0, 9, 10, 11], 1: [0, 6, 8, 10], 2: [0, 2, 3, 5, 6, 8, 9, 11], 3: [0, 2, 3, 5, 6, 8, 9, 11]}[pos]
        prob = {0: .45, 1: .4, 2: .72, 3: .85}[pos] * densidad
        for u in cand:
            if u == 0 or R.random() < prob: tiempos.append(tb + u * T8)
    juntas = []
    if riffs:
        for af in AFL:
            if min(d_a, d_b) <= af['en'] <= max(d_a, d_b) and af['en'] > 1:
                tj = a + (af['en'] - d_a) / (d_b - d_a) * (z - a); juntas.append((tj, af))
    tiempos = [t for t in tiempos if all(abs(t - tj) > .3 for tj, _ in juntas)]
    for t in tiempos:
        mq = cuantiza(m_paseo(t, float(dfun(t))), acorde_en(t)); nota(t, mq, v=R.uniform(.55, .85), desliz=None, desde=-2 if R.random() < .25 else 0)
    for tj, af in juntas:                                                                           # el riff del afluente: cae de su altura a la de la junta
        mj = m_paseo(tj, af['en']); arriba = mj + af['baja'] / M_POR_SEMI
        nota(tj - .32, arriba, v=.9, desliz=.04); nota(tj, cuantiza(mj, acorde_en(tj)), v=.0, desliz=.3, pua=False)
def tormenta_guitarra(sec):
    a, z = SEC[sec]['t'], SEC[sec]['t1']; cava = z_en(a) - z_en(z + 6); cava[-NX // 30:] = 0              # el vidrio se queda donde esta tormenta excava más
    xk = int(np.argmax(cava)); TRAMOS.append((a, z, float(XS[xk]), float(XS[xk])))
    t = a + T8
    while t < z - .2:
        nota(t, None, v=R.uniform(.35, .65) * (1 + .4 * math.sin(math.pi * (t - a) / (z - a))), desliz=.02, vivo=xk); t += NEGRA / 6
    return xk
# I: la guitarra sube la cárcava (de la boca a la cabecera) y luego la baja, virgen
TRAMOS.append((ts('I', 0), ts('I', 2), LARGO, 0))
for b in range(2):
    for u in (0, 3, 6, 9): t = ts('I', b, u); nota(t, cuantiza(m_paseo(t, LARGO * (1 - (t - ts('I', 0)) / (2 * COMPAS))), 0), v=.7, desliz=.25)
coro_guitarra('I', 2, 12, 0, LARGO, .8)
NUDOS = {}
NUDOS['t1'] = tormenta_guitarra('t1'); coro_guitarra('II', 0, 12, 0, LARGO)
NUDOS['t2'] = tormenta_guitarra('t2'); coro_guitarra('IIIr', 0, 8, 0, LARGO, .25); coro_guitarra('III', 0, 12, 0, LARGO, 1.1)
NUDOS['t3'] = tormenta_guitarra('t3'); coro_guitarra('IV', 0, 12, 0, LARGO, 1.15)
coro_guitarra('V', 0, 6, float(XS[NUDOS['t3']]), LARGO, .7, riffs=True)
nota(ts('V', 6), m_paseo(ts('V', 6), LARGO), v=.85, desliz=.4); nota(ts('V', 7, 6), m_paseo(ts('V', 7), LARGO), v=.5, desliz=.1)
notas.sort(key=lambda n: n['t'])
# la curva: entre nota y nota el vidrio se desliza; sobre la nota, vibrato de slide y un poco del perfil mismo
curva = np.zeros(NC); ant = cuantiza(m_terreno(Z0[-1]), 0)
for k, n in enumerate(notas):
    a = int(n['t'] * FR); b = int(notas[k + 1]['t'] * FR) if k + 1 < len(notas) else NC
    if b <= a: continue
    tt = TC[a:b] - n['t']
    if n['vivo'] is not None: meta = np.array([m_terreno(z_en(n['t'] + x)[n['vivo']]) for x in tt])
    else: meta = np.full(len(tt), n['m'])
    ini = ant if n['desde'] == 0 or not n['pua'] else meta[0] + n['desde']
    s = np.clip(tt / max(n['desliz'], 1e-3), 0, 1); s = s * s * (3 - 2 * s)
    vib = np.clip((tt - .12) / .4, 0, 1) * .22 * np.sin(2 * np.pi * 5.6 * tt) if n['vivo'] is None else 0
    curva[a:b] = ini + (meta - ini) * s + vib; ant = float(meta[-1])
curva[:int(notas[0]['t'] * FR)] = curva[int(notas[0]['t'] * FR)]
PUAS = [[n['t'], n['v']] for n in notas if n['pua'] and n['v'] > 0]
# el pulgar: el bajo monótono del Delta en las cuerdas al aire (la raíz del acorde), con la palma
pulgar_p, pulgar_c = [], np.full(NC, TON)
for k, s in SEC.items():
    if s['tipo'] not in ('coro', 'boca'): continue
    for b in range(s['compases']):
        for u in (0, 3, 6, 9):
            t = ts(k, b, u); ac = acorde_en(t)
            if k == 'V' and b >= 6 and u: continue
            pulgar_p.append([round(t, 4), .85 if u == 0 else .6]); pulgar_c[int(t * FR):] = TON + ac
GUITARRA = dict(fr=FR, dur=DUR, semilla=SEMILLA, cuerdas=[
    dict(nombre='slide', curva=[round(float(x), 3) for x in curva], pulsos=PUAS, t60=2.4, brillo=.72, abierta=round(TON + 7, 3), entorchada=True, pan=-.2, empuje=2.8),
    dict(nombre='pulgar', curva=[round(float(x), 3) for x in pulgar_c], pulsos=pulgar_p, t60=.45, brillo=.45, abierta=round(TON, 3), entorchada=False, pan=.05, empuje=2.0)])

# ═════════ el drill: hats con redobles primos, 808 que se desliza, bombo, tarola, palmas ═════════
PICOS, PINFO = S11.picos_primos(72)
hats, web = [], {'bateria808': [], 'bateria-frito': []}
def w(stem, t, ficha, pieza, vel=.8, pan=0.0): web[stem].append(dict(t=round(t, 5), ficha=ficha, midi=60, vel=round(vel, 3), dur=.2, pan=pan, pieza=pieza))
ocho = []
P808 = [[(0, 0, 6, 1), (7, 0, 3, 0), (10, 12, 5, 1), (16, 0, 6, 0), (23, 7, 3, 1), (26, 0, 4, 0), (30, -2, 2, 1)],
        [(0, 0, 6, 0), (7, 0, 3, 1), (10, 3, 4, 1), (14, 0, 2, 0), (16, 0, 6, 1), (23, 12, 3, 1), (26, 10, 3, 1), (29, 7, 3, 0)]]
REDOBLES = []
def drill(sec, b0, nb, fuerza=1.0, ghost=.3, palmas=False, triples=False):
    for b in range(b0, b0 + nb):
        tb = ts(sec, b); ac = acorde_en(tb); r0 = TON - 12 + ac
        for mitad in (0, 16):
            for s, v in ((0, .95), (10, .8)): w('bateria808', tb + (mitad + s) * G, 'bateria-tr808', 'kick', v * fuerza)
            if R.random() < .4: w('bateria808', tb + (mitad + 7) * G, 'bateria-tr808', 'kick', .6 * fuerza)
            w('bateria808', tb + (mitad + 8) * G, 'bateria-tr808', 'snare', .9 * fuerza, .05)
            if palmas: w('bateria-frito', tb + (mitad + 8) * G + .006, 'bateria-frito', 'clap', .55 * fuerza, -.1)
            if R.random() < ghost: w('bateria808', tb + (mitad + 15) * G, 'bateria-tr808', 'snare', .35 * fuerza, .05)
        for s, x, d, gl in P808[b % 2]: ocho.append(dict(t=round(tb + s * G, 4), dur=round(d * G, 4), m=round(r0 + x, 3), v=.9 * fuerza, desliz=round(1.6 * G, 4) if gl else 0))
        # hats: shuffle en tresillos; el último tiempo de cada dos compases, un redoble primo
        red = None
        if b % 2 == 1: red = (tb + 3 * NEGRA, NEGRA, False) if R.random() < .6 else (tb + 3 * NEGRA, NEGRA / 2, True)
        elif R.random() < .3 * fuerza: red = (tb + 1 * NEGRA + NEGRA / 2, NEGRA / 2, True)
        for u in range(12):
            t = tb + u * T8
            if red and red[0] - .01 <= t < red[0] + red[1]: continue
            if u % 3 == 1 and not (triples and R.random() < .7): continue
            hats.append(dict(t=round(t, 5), v=round((.6 if u % 3 == 0 else .4) * fuerza, 3), abierto=(u == 11 and R.random() < .25), pan=.25))
        if red:
            r = S11.redoble(red[0], red[1], PICOS, ida=red[2], v=.75 * fuerza); hats.extend(r); REDOBLES.append(dict(t=round(red[0], 4), D=round(red[1], 4), ida=red[2], golpes=len(r)))
drill('II', 2, 10, .85); drill('IIIr', 0, 8, 1.0, .45, True); drill('III', 0, 12, 1.0, .5, True, True); drill('IV', 0, 12, 1.05, .55, True, True); drill('V', 0, 4, .8, .2)
hats.sort(key=lambda h: h['t'])

# ═════════ las voces (Sabina) ═════════
lead, doble, resp, resp3, resp8, rap, chops, rio = [], [], [], [], [], [], [], []
coros = {v: [] for v in 'SATB'}
def frase(dest, texto, t, alturas, ritmo, base, legato=.9, unidad=T8, **kw):
    for k, sy in enumerate(texto.replace('/', ' ').split()):
        d = ritmo[k % len(ritmo)] * unidad; dest.append(dict(t=round(t, 4), dur=round(d * legato, 4), texto=sy, nota=round(base + alturas[k % len(alturas)], 3), **kw)); t += d
    return t
LB = TON + 24
VERSOS = {
 'I': [('la tie rra es ta ba li sa / na die la ha bí aes cri to', [10, 12, 12, 10, 12, 10, 7, 7, 5, 7, 5, 3, 5, 3, 0, 0], [1, 2, 1, 2, 1, 2, 1, 5, 1, 2, 1, 2, 1, 2, 1, 6]),
       ('lle gó la llu via de no che / y con el de do hi zoun rí o', [7, 10, 12, 10, 7, 7, 5, 3, 3, 3, 5, 6, 5, 3, 0, 3, 0], [1, 2, 1, 2, 1, 2, 1, 5, 1, 1, 1, 2, 1, 2, 1, 2, 6])],
 'II': [('ca da go ta que ca e / se lle vaun po co de ce rro', [12, 12, 10, 12, 10, 7, 7, 10, 7, 5, 7, 5, 3, 0, 0], [1, 2, 1, 2, 1, 2, 5, 1, 2, 1, 2, 1, 2, 1, 6]),
        ('el a gua no tie ne pri sa / pe ro nun ca se can sa', [7, 7, 10, 12, 10, 7, 6, 5, 5, 3, 5, 3, 0, 3, 0], [1, 1, 2, 1, 2, 1, 2, 5, 1, 2, 1, 2, 1, 2, 6])],
 'III': [('lo queel a gua di bu ja / no lo bo rra na die', [12, 15, 12, 10, 12, 10, 7, 7, 5, 3, 5, 3, 0, 0], [1, 2, 1, 2, 2, 1, 5, 1, 2, 1, 2, 2, 1, 6]),
         ('ca da tor men ta que pa sa / me de jaun po co más hon da', [10, 10, 12, 10, 7, 7, 6, 5, 5, 5, 3, 5, 3, 3, 0, 0], [1, 2, 1, 2, 1, 2, 1, 5, 1, 2, 1, 2, 1, 2, 1, 6])],
 'IV': [('me di cen tie rra ma la / por quea quí no cre ce na da', [12, 12, 15, 12, 10, 12, 10, 7, 7, 10, 7, 5, 3, 0, 0], [1, 2, 1, 2, 1, 2, 5, 1, 2, 1, 2, 1, 2, 1, 6]),
        ('pe ro mí ra me las ve nas / ca dau naes u na llu via', [7, 10, 12, 15, 12, 10, 7, 7, 5, 7, 5, 3, 5, 3, 0, 0], [1, 1, 2, 1, 2, 1, 2, 5, 1, 2, 1, 2, 1, 2, 1, 6])]}
RESPUESTA = {'I': ('lo queel a gua di bu ja', [7, 7, 10, 7, 5, 3, 0], [1, 1, 2, 1, 2, 2, 5]), 'II': ('go ta por go ta', [10, 7, 7, 5, 3], [1, 2, 1, 2, 6]),
             'III': ('más hon da', [7, 5, 0], [2, 2, 8]), 'IV': ('lo queel a gua di bu ja', [7, 7, 10, 7, 5, 3, 0], [1, 1, 2, 1, 2, 2, 5])}
def responde(sec, b, txt, alt, rit):
    t = ts(sec, b, 8)                                                          # en el tercer compás de la línea, tiempo 3
    frase(resp, txt, t, alt, rit, LB); frase(resp3, txt, t, [a - 5 for a in alt], rit, LB); frase(resp8, txt, t, alt, rit, LB - 12)
    for v, x in zip('SATB', (0, -5, -12, None)): frase(coros[v], txt, t, [a + x if x is not None else -24 for a in alt], rit, LB)
for sec, b0 in (('I', 2), ('II', 0), ('III', 0), ('IV', 0)):
    (A, a1, r1), (B, a2, r2) = VERSOS[sec]
    for k, (txt, alt, rit) in enumerate(((A, a1, r1), (A, a1, r1), (B, a2, r2))):
        frase(lead, txt, ts(sec, b0 + 4 * k), alt, rit, LB)
        if sec == 'IV': frase(doble, txt, ts(sec, b0 + 4 * k) + .012, alt, rit, LB - 12)
        if sec == 'III' and k == 1: responde(sec, b0 + 4 * k + 2, 'lo queel a gua di bu ja', [7, 7, 10, 7, 5, 3, 0], [1, 1, 2, 1, 2, 2, 5])
        else: responde(sec, b0 + 4 * k + 2, *RESPUESTA[sec])
frase(lead, 'yu cha ka nu rí o gran de / to do lo que ba ja lle ga', ts('V', 2), [7, 7, 10, 7, 5, 7, 5, 3, 3, 3, 5, 3, 0, -2, 0, 0], [1, 2, 1, 2, 1, 2, 1, 5, 1, 2, 1, 2, 1, 2, 1, 8], LB)
for b in (0, 4):
    frase(rio, 'lo queel a gua di bu ja', ts('V', b, 0), [7, 7, 10, 7, 5, 3, 0], [2, 2, 4, 2, 4, 4, 10], TON + 12)
responde('V', 6, 'lo queel a gua di bu ja', [7, 7, 10, 7, 5, 3, 0], [1, 1, 2, 1, 2, 2, 8])
RAP = [('de yu ku i so has ta el bo que rón', 'r'), ('ba ja la tie rra sin pe dir per dón', 'r'), ('go ta por go ta pie dra por pie dra', 't'), ('el ce rro se va la cár ca va que da', 't'),
       ('no trai go pri sa trai go la cuen ta', 'r'), ('ca da tor men ta me de ja más hon da', 'r'), ('de la cu chi lla al rí o sa la do', 't'), ('lo queel a gua di bu ja yaes tá di bu ja do', 't')]
for b, (txt, flow) in enumerate(RAP):
    sil = txt.split(); un = NEGRA / 4 if flow == 'r' else NEGRA / 6; t = ts('IIIr', b) + G
    for k, sy in enumerate(sil):
        x = (0, 0, 2, 0, -1, 0, 3, 0)[k % 8] - (3 if k == len(sil) - 1 else 0)
        rap.append(dict(t=round(t, 4), dur=round(un * .88 if k < len(sil) - 1 else NEGRA * .7, 4), texto=sy, nota=round(TON + 17 + x, 3))); t += un
for sec in ('III', 'IV'):
    for b in range(12):
        if b % 4 not in (2, 3): continue
        pal = [('cár', 7), ('ca', 5), ('va', 0)] if b % 2 == 0 else [('hon', 10), ('da', 7), ('hon', 10), ('da', 3)]
        for j, (sy, x) in enumerate(pal):
            if R.random() < .8: chops.append(dict(t=round(ts(sec, b) + (20 + 2 * j) * G, 4), dur=round(G * 1.6, 4), texto=sy, nota=round(TON + 36 + x, 3)))
for l in (lead, doble, resp, resp3, resp8, rap, chops, rio): l.sort(key=lambda e: e['t'])

# ═════════ viento y lo demás ═════════
VIENTO = [[0, 9], [SEC['t1']['t'], 11], [SEC['t1']['t1'], 13], [SEC['II']['t'] + 6, 5], [SEC['t2']['t'], 12], [SEC['IIIr']['t'] + 4, 4], [SEC['t3']['t'], 13], [SEC['t3']['t1'], 14],
          [SEC['IV']['t'] + 6, 6], [SEC['V']['t'], 3], [DUR, 1]]
# lo que se mide de la cárcava: cuánto se hundió el slide en cada coro, y el nudo de cada tormenta
def perfil_m(t): return m_terreno(z_en(t))
HUNDE = {k: dict(tiempo=SEC[k]['t'], hondo_medio_m=round(float(np.mean(Z0 - z_en(SEC[k]['t']))), 2), hondo_max_m=round(float(np.max(Z0 - z_en(SEC[k]['t']))), 2),
                 donde_max_m=round(float(XS[np.argmax(Z0 - z_en(SEC[k]['t']))])), slide_medio_st=round(float(np.mean(perfil_m(0) - perfil_m(SEC[k]['t']))), 2)) for k in ('II', 'IIIr', 'IV', 'V')}
NUDO = {k: dict(x_m=round(float(XS[x])), cae_st=round(float(m_terreno(z_en(SEC[k]['t'])[x]) - m_terreno(z_en(SEC[k]['t1'] + 6)[x])), 2)) for k, x in NUDOS.items()}
PERFILES = {k: [round(float(x), 2) for x in z_en(SEC[k]['t'])[::4]] for k in ('I', 'II', 'IIIr', 'IV', 'V')}
partitura = dict(titulo='Lo que el agua dibuja', semilla=SEMILLA, terreno=f"traspuesta 67, {TER['nombre']}, {TER['anchoKm']} km, {TER['relieve']} m", historia=['ARCILLAS', 'LLUVIAS RARAS Y VIOLENTAS', 'CÁRCAVAS', 'TIERRAS MALAS'],
                 carcava=dict(nombre="YUCHA KA'NU", largo_m=round(LARGO), z_cabecera=round(float(Z0[0]), 2), z_boca=round(Z_BOCA, 2), m_por_semitono=M_POR_SEMI, nx=NX, afluentes=AFL, boca=BOCA,
                              u=[round(float(x), 5) for x in U_C[::4]], v=[round(float(x), 5) for x in V_C[::4]], K=K, objetivo_m=OBJETIVO, hunde=HUNDE, nudos=NUDO, perfiles_cada_4=PERFILES),
                 tonica=round(TON, 3), octavas_arriba=octv, bpm=BPM, negra=NEGRA, compas=COMPAS, escala=[0, 3, 5, 6, 7, 10],
                 secciones=[dict(num=k, nombre=s['nombre'], tipo=s['tipo'], t=s['t'], t1=s['t1'], t_real=s['t'], t1_real=s['t1'], compases=s['compases']) for k, s in SEC.items()],
                 duracion=DUR, lluvia=dict(fr=FR_LL, intensidad=[round(float(x), 2) for x in lluvia_I]), gotas=gotas, tormentas=TORMENTAS, rayos=rayos,
                 guitarra=GUITARRA, tramos_guitarra=TRAMOS, notas_guitarra=len(notas), hats=hats, redobles=REDOBLES, picos_primos=dict(n=len(PICOS), encontradas=PINFO['encontradas'], de=PINFO['potencias_de_primos']),
                 ocho=ocho, web=web, viento=VIENTO,
                 sabina=[dict(eventos=lead, nivel=.9, pan=0, capa='lead'), dict(eventos=doble, nivel=.8, pan=0, capa='doble'), dict(eventos=resp, nivel=.85, pan=0, capa='respuesta'),
                         dict(eventos=resp3, nivel=.8, pan=0, capa='respuesta3'), dict(eventos=resp8, nivel=.8, pan=0, capa='respuesta8'), dict(eventos=rap, nivel=.95, pan=0, capa='rap'),
                         dict(eventos=chops, nivel=.85, pan=0, capa='chops'), dict(eventos=rio, nivel=.9, pan=0, capa='rio')],
                 coros=coros, instrumentos=None)
if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    partitura['instrumentos'] = '../../../biblioteca-de-instrumentos'
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(partitura, fo, ensure_ascii=False)
    print('duración', DUR, 's ·', sum(s['compases'] for s in SEC.values()), 'compases · tónica', round(TON, 2), f'({440 * 2 ** ((TON - 69) / 12):.2f} Hz)')
    print('cárcava', round(LARGO), 'm,', round(float(Z0[0]), 1), '→', round(Z_BOCA, 1), 'm · slide', round(float(m_terreno(Z0[0])), 1), '→', round(float(m_terreno(Z_BOCA)), 1), '· K', round(K, 5))
    print('gotas', len(gotas), {t: sum(g['toque'] == t for g in gotas) for t in ('pizz', 'arco', 'col')}, '· rayos', [(r['lugar'], r['dist_m'], r['retraso_s']) for r in rayos])
    print('hunde', HUNDE); print('nudos', NUDO)
    print('guitarra', len(notas), 'notas,', len(PUAS), 'púas · hats', len(hats), '· redobles', len(REDOBLES), '· picos primos', len(PICOS), PINFO['encontradas'], '/', PINFO['potencias_de_primos'])
    print('voces', {k: len(v) for k, v in dict(lead=lead, doble=doble, resp=resp, rap=rap, chops=chops, rio=rio).items()}, '· 808', len(ocho), '· web', {k: len(v) for k, v in web.items()})
    print('secciones', [(k, round(s['t'], 1)) for k, s in SEC.items()])
