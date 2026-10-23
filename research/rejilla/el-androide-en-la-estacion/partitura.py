"""El androide en la estación — partitura. Electro de Drexciya × el Vangelis de Blade Runner × hyperpop, sobre la lámina 2038 de
Traspuesta (un archipiélago: el año en que se presentó Sutura) y dos textos del CEP: el robot desertor de «el gran poema no vino»
(ejecuto → me oxido → estoy tierra; comprender fue traicionar) y «La máquina de llegar tarde» (Sutura, la red de estaciones cuyo
primer convoy no salió; el horario que aprendió a tener hambre; la pantalla que pierde las consonantes y conserva «una pulsación
cada diecisiete segundos»). Diseño completo en DISENO.md.

LA PULSACIÓN DE 17 s ES LA TÓNICA Y EL TEMPO: 2¹⁰/17 = 60.24 Hz (la tónica), 2⁵/17 = 1.882 Hz (la negra: 112.9 bpm), así que
8 compases = 17 s = un periodo. La canción dura quince pulsaciones de la pantalla de Sutura.
ARRIBA ES LA RETÍCULA, ABAJO LA SERIE: el silicio toca en frigio temperado sobre la tónica; el carbono, en la serie armónica de la
misma tónica (afinación justa: los parciales 8–16). El descenso derrite la retícula.
EL DESCENSO POR GRADIENTE: la terminal vectorial baja por la máxima pendiente desde la cumbre del archipiélago hasta la costa, y
bajo el agua (la batimetría la inventamos: la distancia a la costa) sigue alejándose de la orilla. Altura → vector_x (de metal a
vocal: de silicio a carbono), pendiente → vector_y.
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys, unicodedata
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

SEMILLA = 2038
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__)); G = 360
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-2038.f32'), dtype=np.float32).reshape(G, G).astype(float)
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-2038.json'), encoding='utf-8'))
m_de = lambda f: 69 + 12 * math.log2(f / 440)

# ── la pulsación de Sutura ──
TON = 1024 / 17; R0 = m_de(TON); Q = 17 / 32; BAR = 4 * Q; S16 = Q / 4; PER = 8 * BAR      # 60.24 Hz · 112.9 bpm · 17 s
FRIG = [0, 1, 3, 5, 7, 8, 10]
def fr(g, o=0): k, r = divmod(g, 7); return R0 + 12 * (o + k) + FRIG[r]                   # silicio: frigio temperado
def serie(n, o=0): return R0 + 12 * o + 12 * math.log2(n)                                 # carbono: el parcial n de la tónica
def t_(b, s=0.0): return b * BAR + s * S16                                                 # compás b, dieciseisavo s
SECC = [(0, 'I', 'SUTURA'), (16, 'II', 'ARRIBA · EJECUTO'), (40, 'III', 'COMPRENDER'), (56, 'IV', 'DESCENSO'),
        (72, 'V', 'ABAJO · ME OXIDO'), (96, 'VI', 'HAY SERVICIO EN OTRA FORMA'), (112, 'VII', 'ESTOY TIERRA')]
INI = {s: b for b, s, _ in SECC}; FIN_BAR = 120; DUR = t_(FIN_BAR) + 6

# ── el descenso por gradiente sobre el archipiélago ──
mar = H <= 1e-4
prof = -np.sqrt(distance_transform_edt(mar)) / math.sqrt(distance_transform_edt(mar).max())   # batimetría inventada: distancia a la costa
Z = gaussian_filter(np.where(mar, prof, H), 1.5)
p0 = TER['rasgos']['picos'][0]; y, x = p0['v'] * (G - 1), p0['u'] * (G - 1); camino = []
gy, gx = np.gradient(Z)
for _ in range(4000):
    iy, ix = int(round(y)), int(round(x)); camino.append((x / (G - 1), y / (G - 1), float(Z[iy, ix])))
    dy, dx = gy[iy, ix], gx[iy, ix]; n = math.hypot(dx, dy)
    if n < 1e-5 or not (1 <= ix < G - 2 and 1 <= iy < G - 2): break
    y -= .7 * dy / n; x -= .7 * dx / n
CAM = np.array(camino); zc = CAM[:, 2]; pend = np.abs(np.gradient(zc)); pend = pend / (pend.max() or 1)
COSTA = int(np.argmax(zc <= 0)) if (zc <= 0).any() else len(zc) - 1
def camino_en(s): i = min(len(CAM) - 1, int(s * (len(CAM) - 1))); return CAM[i], pend[i]
PERFIL_ISLA = [round(float(v), 4) for v in np.interp(np.linspace(0, COSTA, 48), np.arange(len(zc)), np.maximum(zc, 0)) / max(zc.max(), 1e-6)]

ev = {k: [] for k in ['bateria', 'bateria-frito']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr808', stem='bateria'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)
TT = {k: dict(notas=[], controles={}) for k in ['boca', 'arpa', 'cuerda', 'sala', 'organo', 'cristal', 'estacion', 'terminal', 'plasma', 'androide', 'fotones']}
def nota(ins, t, m, dur, vel=.8, pan=0.0, **kw): TT[ins]['notas'].append(dict(t=round(t, 4), midi=round(m, 3), dur=round(dur, 4), vel=round(vel, 3), pan=pan, **kw))
sub, traductor, anden, soprano, coros = [], [], [], [], {v: [] for v in 'SATB'}
impresora, torniquete, campana, agua, pulsos = [], [], [], [], [round(k * PER, 3) for k in range(16)]

def silabas_a(texto, t0, alturas, ritmo, destino, legato=.92, **kw):
    """una frase cantada: una sílaba por nota; ritmo en dieciseisavos; devuelve el final"""
    t = t0
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; destino.append(dict(t=round(t, 4), dur=round(d * legato, 4), texto=sy, nota=round(alturas[i % len(alturas)], 3), **kw)); t += d
    return t

# ═════════ I · SUTURA (la estación sola) ═════════
lluvia = [[0, .35], [t_(8), .5], [t_(16) - 2, .45], [t_(16), .15], [t_(INI['IV']), .2], [t_(INI['IV'] + 4), .9], [t_(INI['V']), .5], [t_(INI['V'] + 4), .1],
          [t_(INI['VI']), .1], [t_(INI['VII']), .4], [DUR, .3]]
for b in (1, 9): campana += [dict(t=round(t_(b), 3), m=round(fr(4, 3), 3), v=.75), dict(t=round(t_(b, 3), 3), m=round(fr(2, 3), 3), v=.65)]   # dos tonos: quinta y tercera menor
ANDEN = [('su tu ra', 2), ('no hay ser vi cio dis po ni ble', 3), ('el con voy de las cua tro do ce', 10), ('se re tra sa', 12)]
for txt, b in ANDEN:                                                     # la voz de andén: recitado en la nota de la campana, cae al final
    n = len(txt.split()); alt = [fr(4, 2)] * (n - 1) + [fr(2, 2)]
    silabas_a(txt, t_(b), alt, [2] * (n - 1) + [5], anden, legato=.85)
for k, (b, ch, v) in enumerate([(5, 22, .7), (6, 9, .6), (13, 26, .75), (14, 14, .6)]): impresora.append(dict(t=round(t_(b, 2), 3), chars=ch, v=v, pan=.35))
torniquete += [dict(t=round(t_(4, 7), 3), v=.8, pan=-.5), dict(t=round(t_(11, 5), 3), v=.7, pan=-.3), dict(t=round(t_(15, 1), 3), v=.75, pan=-.6)]

# ═════════ II · ARRIBA · EJECUTO (electro de Drexciya, silicio en frigio) ═════════
ACORDES = [0, 0, 1, 1, 0, 0, 6, 5]                                       # i i bII bII i i bVII bVI (por compás)
def acorde(g): return [fr(g, 0), fr(g + 2, 0), fr(g + 4, 0), fr(g + 7, 0)]
KICK, SNARE, HAT_AC = [0, 6, 10], [4, 12], {2, 6, 10, 14}
def electro(b, lleno=True, medio=False):
    for s in ([0, 8] if medio else KICK): bat(t_(b, s), 'kick', .95 if s == 0 else .8); sub.append(dict(t=round(t_(b, s), 4), dur=round(3 * S16, 4), midi=round(fr(ACORDES[b % 8], -1), 3), vel=.9))
    for s in ([8] if medio else SNARE): bat(t_(b, s), 'clap' if b % 4 == 3 else 'snare', .8, .05)
    if lleno:
        for s in range(16): bat(t_(b, s), 'hat', .32 + .25 * (s in HAT_AC), .3)
        if b % 2: bat(t_(b, 14), 'cowbell', .35, -.35)
    for s in ([2, 9, 13] if not medio else [9]):
        nota('fotones', t_(b, s), fr(ACORDES[b % 8], 1) + R.choice([0, 7, 12]), .35, .55 + .2 * (s == 9), R.choice([-.45, .3, 0]))
RIFF_AN = [(0, 0, 0), (3, 0, 1), (6, 2, 0), (8, 0, 0), (10, 4, 0), (11, 3, 0), (14, 0, 1)]   # (16avo, grado sobre el acorde, octava)
def androide(b, v=.8):
    g = ACORDES[b % 8]
    for s, d, o in RIFF_AN: nota('androide', t_(b, s), fr(g + d, o), 1.6 * S16, v * (1 if s in (0, 8) else .8))
def cristal_arp(b):
    a = acorde(ACORDES[b % 8]); orden = [0, 2, 1, 3, 2, 1, 3, 0]
    for s in range(0, 16, 2 if b % 2 == 0 else 1):
        nota('cristal', t_(b, s), a[orden[s % 8]] + 24 + (12 if s >= 12 else 0), S16 * 1.5, .45 + .2 * (s % 4 == 0), .4 * math.sin(s))
for b in range(INI['II'], INI['III']):
    electro(b, lleno=b >= INI['II'] + 2); androide(b)
    if b >= INI['II'] + 4 and (b // 2) % 2 == 0: cristal_arp(b)
    if (b - INI['II']) % 4 == 3: impresora.append(dict(t=round(t_(b, 12), 3), chars=5, v=.55, pan=.6))   # la impresora en los huecos
# el traductor canta el horario abajo (frases largas, medidas, registro estrecho; LPC limpio)
V2 = [('cua tro do ce es ta ción nor te', 18, [fr(0, 1), fr(0, 1), fr(1, 1), fr(0, 1), fr(-1, 1), fr(-1, 1), fr(0, 1), fr(2, 1), fr(0, 1)], [2, 2, 2, 4, 2, 2, 4, 2, 8]),
      ('die cio cho ki los de se mi llas', 22, [fr(2, 1), fr(2, 1), fr(1, 1), fr(0, 1), fr(1, 1), fr(0, 1), fr(-2, 1), fr(-1, 1), fr(0, 1)], [3, 1, 4, 2, 2, 2, 2, 4, 10]),
      ('e je cu to', 25, [fr(4, 1), fr(4, 1), fr(3, 1), fr(0, 1)], [1, 1, 2, 6]),
      ('do ce en pun to ha cia el fu tu ro', 28, [fr(0, 1)] * 3 + [fr(1, 1)] * 2 + [fr(2, 1), fr(1, 1), fr(0, 1), fr(-1, 1), fr(-2, 1), fr(0, 1)], [2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 8]),
      ('u na pro me sa', 31, [fr(4, 1), fr(3, 1), fr(2, 1), fr(1, 1), fr(0, 1)], [4, 2, 4, 2, 10]),
      ('ce rra do por fal ta de ví a', 34, [fr(0, 1), fr(1, 1), fr(0, 1), fr(-1, 1), fr(0, 1), fr(1, 1), fr(3, 1), fr(1, 1), fr(0, 1)], [2, 2, 4, 2, 2, 2, 2, 4, 8]),
      ('e je cu to el re tra so', 37, [fr(4, 1), fr(4, 1), fr(3, 1), fr(0, 1), fr(-1, 1), fr(0, 1), fr(1, 1), fr(0, 1)], [1, 1, 2, 4, 2, 2, 4, 12])]
for txt, b, alt, rit in V2: silabas_a(txt, t_(b), alt, rit, traductor)
# la terminal en la cumbre: pad de acordes (metal y pulso: silicio)
for b in range(INI['II'] + 8, INI['III'], 2):
    for m in acorde(ACORDES[b % 8])[1:]: nota('terminal', t_(b), m + 12, 2 * BAR * .95, .5, .3 * (m % 2 - .5))

# ═════════ III · COMPRENDER (diálogo: el traductor dice, el simbionte contesta) ═════════
def vocal_de(sy):
    s = ''.join(c for c in unicodedata.normalize('NFD', sy) if unicodedata.category(c) != 'Mn')
    return next((c for c in s if c in 'aeiou'), 'a')
def cons_de(sy):
    c = sy[0].lower()
    if c in 'mnñ': return 'm'
    if c in 'tdpbr': return 't'
    if c in 'kcgqxj': return 'k'
    if c in 'szfy' or sy.startswith('ch'): return 's'
    return None
BOCA = dict(vocales=[[0, 'a']], consonantes=[], notas=[])
def boca(texto, t0, alturas, ritmo, consonantes=1.0, vel=.75):
    t = t0
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; c = cons_de(sy)
        if c and consonantes > 0: BOCA['consonantes'].append([round(t, 4), c, round(.7 * consonantes, 3)])
        BOCA['vocales'].append([round(t + .03, 4), vocal_de(sy)])
        nota('boca', t, alturas[i % len(alturas)], d * .95, vel); t += d
    return t
DIAL = [('tra', 'tra duz co al hon go', 40, [fr(0, 1), fr(1, 1), fr(0, 1), fr(-1, 1), fr(0, 1), fr(-2, 1)], [2, 2, 2, 2, 3, 5]),
        ('boca', 'nos o yes y te mo jas', 42, [serie(12, 1), serie(13, 1), serie(14, 1), serie(12, 1), serie(11, 1), serie(10, 1), serie(9, 1)], [1, 1, 2, 1, 1, 2, 8]),
        ('tra', 'tra duz co a la ra íz', 44, [fr(2, 1), fr(1, 1), fr(0, 1), fr(1, 1), fr(2, 1), fr(3, 1), fr(1, 1)], [2, 2, 2, 1, 1, 2, 6]),
        ('boca', 'nos co mes y te lle nas', 46, [serie(14, 1), serie(13, 1), serie(12, 1), serie(10, 1), serie(12, 1), serie(14, 1), serie(16, 1)], [1, 2, 1, 1, 1, 2, 8]),
        ('tra', 'en ten dí', 48, [fr(4, 1), fr(3, 1), fr(0, 1)], [3, 1, 12])]
for quien, txt, b, alt, rit in DIAL:
    if quien == 'tra': silabas_a(txt, t_(b), alt, rit, traductor)
    else: boca(txt, t_(b), alt, rit)
def coro_hit(texto, b, s0, alturas, ritmo):
    t = t_(b, s0)
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; sop = alturas[i % len(alturas)]
        for v, n in zip('SATB', (sop, sop - 5, sop - 9, R0 + 24)): coros[v].append(dict(t=round(t, 4), dur=round(d * .88, 4), texto=sy, nota=round(n, 3)))
        soprano.append(dict(t=round(t, 4), dur=round(d * .88, 4), texto=sy, nota=round(sop, 3))); t += d
coro_hit('y se te ca yó la pa la', 49, 4, [fr(4, 3), fr(4, 3), fr(3, 3), fr(4, 3), fr(5, 3), fr(4, 3), fr(1, 3), fr(0, 3)], [1, 1, 1, 1, 2, 1, 1, 4])
silabas_a('trai cio né al en ten der', t_(52), [fr(0, 1), fr(1, 1), fr(3, 1), fr(1, 1), fr(0, 1), fr(-1, 1), fr(-2, 1)], [2, 2, 4, 2, 2, 2, 14], traductor)
coro_hit('trai cio né', 54, 0, [fr(1, 3), fr(0, 3), fr(-2, 3)], [2, 2, 8])
for b in range(INI['III'], INI['IV']):
    electro(b, lleno=(b - INI['III']) % 4 != 3, medio=False); androide(b, .65)
    if b % 2 == 0:                                                            # cuerdas de estación (Blade Runner): acordes que crecen
        for m, p in zip(acorde(ACORDES[b % 8]), (-.7, -.2, .2, .7)): nota('estacion', t_(b), m + 12, 2 * BAR, .55, p)
    if b % 4 == 1:                                                            # metales de plasma: un golpe en el cambio
        for m in acorde(ACORDES[(b + 1) % 8])[1:]: nota('plasma', t_(b, 14), m + 12, 6 * S16, .7, .2)

# ═════════ IV · DESCENSO (la retícula se derrite; bajo el agua; medio tiempo) ═════════
for b in range(INI['IV'], INI['V']):
    electro(b, lleno=False, medio=True)
    if b % 2 == 0:
        g = ACORDES[b % 8]; u = (b - INI['IV']) / 16                          # el bajo de androide se desliza de la retícula a la serie
        nota('androide', t_(b), fr(g, 0) * (1 - u) + serie(8 + (b // 2) % 4, -1) * u + (12 if u > .5 else 0), 2 * BAR * .9, .75)
    if b % 4 == 0: agua.append(dict(t=round(t_(b), 3), tipo='burbujeo', dur=round(4 * BAR, 3), v=.55))
agua.append(dict(t=round(t_(INI['V']) - 3, 3), tipo='ola', dur=10, v=.6))
silabas_a('ba jo', t_(58), [fr(0, 1), fr(-1, 1)], [4, 12], traductor, legato=1.0)
silabas_a('ba jo', t_(62), [fr(-1, 1), fr(-2, 1)], [4, 14], traductor, legato=1.0)
silabas_a('el a gua no fir ma con ve nios', t_(66), [serie(8, 0), serie(9, 0), serie(10, 0), serie(9, 0), serie(8, 0), serie(7, 0), serie(8, 0), serie(9, 0), serie(8, 0)],
          [2, 4, 2, 2, 4, 2, 2, 4, 10], traductor, legato=1.0)
for b in range(INI['IV'], FIN_BAR - 2, 2): nota('sala', t_(b, 3), serie(R.choice([8, 10, 12, 14]), 0), .4, .55)   # la cueva: golpes que el pliegue gira
TT['sala']['controles'] = dict(pliegue_0=[[0, 0], [t_(INI['IV']), .2], [t_(INI['V']), .8], [t_(INI['VI']), .4], [DUR, .9]],
                               pliegue_1=[[0, .2], [t_(INI['IV']), .3], [t_(INI['V'] + 8), .9], [t_(INI['VI']), .2], [DUR, .7]])

# ═════════ V · ABAJO · ME OXIDO (polifonía de carbono en la serie; estribillo hyperpop; solos) ═════════
CUERDAS_ARPA = [serie(n, 1) for n in (8, 10, 12, 14, 16)]
TT['arpa']['cuerdas_midi'] = [round(m, 3) for m in CUERDAS_ARPA]; TT['arpa']['enlaces'] = []
for b in range(INI['V'], INI['VII'] + 4):                                   # el micelio: se pulsa una cuerda y la vibración viaja a otra
    k = (b * 3) % 5
    if b < INI['VI'] or b % 2 == 0: nota('arpa', t_(b, R.choice([0, 3, 6])), CUERDAS_ARPA[k], .3, .8, cuerda=k)
    TT['arpa']['enlaces'].append([round(t_(b, 8), 3), k, (k + 2) % 5, 1.3])
TT['cuerda']['base_midi'] = round(serie(8, 0), 3)
for b in range(INI['V'], INI['VI'], 4): nota('cuerda', t_(b), serie(R.choice([8, 9, 10, 12]), 0), 4 * BAR * .9, .75)
TT['cuerda']['controles'] = dict(presion=[[0, 0], [t_(INI['V']), .2], [t_(INI['V'] + 8), .85], [t_(INI['V'] + 16), .4], [t_(INI['VI']), .7], [DUR, 0]],
                                 arco=[[0, 0], [t_(INI['V']), .3], [t_(INI['V'] + 8), .9], [t_(INI['V'] + 12), 0], [t_(INI['V'] + 16), .7], [DUR, 0]])
nota('organo', t_(INI['V']), serie(4, 3), t_(FIN_BAR) - t_(INI['V']) - 1, .8, ataque=2, soltar=3)   # el órgano de divisores: presión que sube, baja y vuelve (se acuerda)
TT['organo']['controles'] = dict(presion=[[0, 0], [t_(INI['V']), .05], [t_(INI['V'] + 10), .95], [t_(INI['V'] + 18), .5], [t_(INI['VI']), .5], [t_(INI['VI'] + 6), .1], [t_(INI['VII']), .5], [DUR, .5]])
def groove_carbono(b):                                                      # el groove se entibia: shuffle, golpes de fotones en la serie
    for s in (0, 7, 10): bat(t_(b, s), 'kick', .85); sub.append(dict(t=round(t_(b, s), 4), dur=round(3 * S16, 4), midi=round(serie(8, -1), 3), vel=.85))
    for s in (4, 12): web('bateria-frito', t_(b, s), 'bateria-frito', 60, .8, .2, 0, pieza='clap')
    for s in range(16):
        sw = .35 * S16 if s % 2 else 0
        if s % 2 == 0 or R.random() < .5: bat(t_(b, s) + sw, 'hat', .25 + .2 * (s % 4 == 2), .3)
    if b % 2: [bat(t_(b, 12 + q * .5), 'hat', .2 + .04 * q, -.3) for q in range(8)]          # ráfaga
    nota('fotones', t_(b, 9), serie(R.choice([8, 10, 12]), 1), .3, .6, .3)
for b in range(INI['V'], INI['VI']): groove_carbono(b)
for b in range(INI['V'], INI['VI']):                                         # el bajo de androide en la serie
    for s, n_ in ((0, 8), (3, 8), (6, 12), (10, 10), (13, 9)): nota('androide', t_(b, s), serie(n_, -1) + 12, 1.8 * S16, .75)
CORO_V = [('me o xi do', 72, 0, [serie(16, 2), serie(15, 2), serie(14, 2), serie(12, 2)], [2, 1, 1, 4]),
          ('me o xi do', 73, 0, [serie(14, 2), serie(14, 2), serie(13, 2), serie(12, 2)], [1, 1, 2, 4]),
          ('go te a lo que co mí', 74, 0, [serie(12, 2), serie(14, 2), serie(15, 2), serie(14, 2), serie(12, 2), serie(10, 2), serie(12, 2)], [1, 1, 2, 1, 1, 2, 8]),
          ('me o xi do', 76, 4, [serie(10, 2), serie(12, 2), serie(14, 2), serie(16, 2)], [1, 1, 1, 5]),
          ('me o xi da mos', 77, 4, [serie(16, 2), serie(14, 2), serie(13, 2), serie(12, 2), serie(10, 2)], [1, 1, 1, 1, 8]),
          ('go te a lo que co mi mos', 78, 4, [serie(12, 2), serie(13, 2), serie(14, 2), serie(16, 2), serie(14, 2), serie(12, 2), serie(10, 2), serie(8, 2)], [1, 1, 1, 1, 2, 1, 1, 8])]
for txt, b, s0, alt, rit in CORO_V: coro_hit(txt, b, s0, alt, rit)
for txt, b, s0, alt, rit in CORO_V[:3]: silabas_a(txt, t_(b, s0), [a - 36 for a in alt], rit, traductor)    # el traductor dobla abajo
# solos: la terminal vectorial baja por la batimetría (80–88), el bajo de androide (88–92)
t = t_(80); i = 0
while t < t_(88) - .2:
    n_ = [8, 9, 10, 12, 14, 15, 16, 18, 20, 21][(i * 3 + (i // 4)) % 10]; d = [1, 1, 2, 1, 3, 1, 2, 4][i % 8] * S16
    nota('terminal', t, serie(n_, 1), d * 1.1, .7 + .2 * (i % 5 == 0), .1, solo=1); t += d; i += 1
for b in range(88, 92):
    for s in range(0, 16, 1 if b % 2 else 2): nota('androide', t_(b, s), serie([8, 10, 12, 11, 9, 8, 7, 8][(s + b) % 8], -1) + 12 + 12 * (s % 5 == 0), 1.1 * S16, .85, solo=1)
coro_hit('di go yo y sa len dos', 92, 0, [serie(12, 2), serie(14, 2), serie(16, 2), serie(14, 2), serie(12, 2), serie(10, 2), serie(9, 2)], [2, 2, 3, 1, 2, 2, 4])
coro_hit('la lu ciér na ga no se a pa ga', 94, 0, [serie(16, 2), serie(15, 2), serie(14, 2), serie(12, 2), serie(14, 2), serie(16, 2), serie(14, 2), serie(12, 2), serie(10, 2), serie(8, 2)],
         [1, 1, 2, 1, 1, 2, 1, 1, 1, 5])
# la terminal: la mano del descenso (vector) en el tiempo
pts_x, pts_y = [], []
for k in range(0, 121):
    tt = t_(INI['II']) + (t_(INI['VI']) - t_(INI['II'])) * k / 120; cst = COSTA / max(1, len(CAM) - 1)
    s_ = float(np.interp(tt, [t_(INI['II']), t_(64), t_(INI['VI'])], [0, cst, 1])); (cx, cy, z), pd = camino_en(s_)   # la costa se cruza a la mitad del descenso
    pts_x.append([round(tt, 3), round(float(np.clip((1 - z) / 2, 0, 1)), 3)]); pts_y.append([round(tt, 3), round(float(pd), 3)])
TT['terminal']['controles'] = dict(vector_x=pts_x, vector_y=pts_y)

# ═════════ VI · HAY SERVICIO EN OTRA FORMA (el mensaje pierde las consonantes, los espacios; queda la pulsación) ═════════
MSG = ['no hay ser vi cio dis po ni ble', 'hay ser vi cio en o tra for ma']
for i, txt in enumerate(MSG): boca(txt, t_(97 + 3 * i), [serie(n, 1) for n in (12, 12, 14, 12, 10, 12, 14, 12, 9)], [2, 2, 2, 2, 2, 2, 2, 2, 6])
for i, txt in enumerate(MSG): boca(txt, t_(104 + 2 * i), [serie(n, 1) for n in (12, 12, 14, 12, 10, 12, 14, 12, 9)], [2, 2, 2, 2, 2, 2, 2, 2, 4], consonantes=0)
t = t_(108)
for sy in (MSG[0] + ' ' + MSG[1]).split():                                   # sin espacios: una sola vocal que se desliza
    BOCA['vocales'].append([round(t, 4), vocal_de(sy)]); t += S16 * 1.5
nota('boca', t_(108), serie(12, 1), t - t_(108), .55)
for b in range(INI['VI'], INI['VII']):
    if b < 104: groove_carbono(b) if b % 2 == 0 else None
    for s, n_ in ((0, 8), (8, 12)): nota('androide', t_(b, s), serie(n_, -1) + 12, 3 * S16, .5)
impresora.append(dict(t=round(t_(110, 4), 3), chars=12, v=.6, pan=.4))     # imprime un último boleto: hay servicio en otra forma

# ═════════ VII · ESTOY TIERRA ═════════
silabas_a('es toy tie rra', t_(113), [serie(8, 0), serie(9, 0), serie(10, 0), serie(8, 0)], [4, 6, 4, 14], traductor, legato=1.0)
silabas_a('el gran po e ma no vi no', t_(116), [serie(7, 0), serie(8, 0), serie(9, 0), serie(8, 0), serie(7, 0), serie(8, 0), serie(7, 0), serie(6, 0)], [2, 4, 2, 2, 4, 2, 4, 14], traductor, legato=1.0)
campana += [dict(t=round(t_(118), 3), m=round(fr(4, 3), 3), v=.5), dict(t=round(t_(118, 3), 3), m=round(fr(2, 3), 3), v=.45)]
for b in range(INI['VII'], FIN_BAR, 2): nota('estacion', t_(b), serie(8, 1), 2 * BAR, .35, -.4); nota('estacion', t_(b), serie(12, 1), 2 * BAR, .3, .4)

# ═════════ las curvas: el óxido, el convoy, las luciérnagas ═════════
OXIDO = [[0, 0], [t_(INI['III']), 0], [t_(INI['IV']), .25], [t_(INI['V']), .72], [t_(INI['VI']), .85], [t_(INI['VII']), .97], [DUR, 1]]
CONVOY = dict(dir=[[0, 1], [t_(INI['IV']) - .01, 1], [t_(INI['IV']), -1], [t_(INI['V'] + 8), -1], [t_(INI['V'] + 8) + 4, .4], [t_(INI['VII']), .4], [DUR, 1]],
              cerca=[[0, .15], [t_(14), .9], [t_(16), .25], [t_(INI['III']), .35], [t_(INI['IV']), .7], [t_(INI['V']), .3], [t_(INI['VI']), .15], [t_(INI['VII']), .25], [DUR, .1]])
LUC = dict(t0=round(t_(INI['V']), 3), t1=round(DUR, 3), K=[[t_(INI['V']), 0], [t_(INI['V'] + 8), 0], [t_(INI['V'] + 16), 3], [DUR, 3]],
           forz=[[t_(INI['V']), 0], [t_(INI['VI']), 0], [t_(INI['VI'] + 8), 1.5], [DUR, 1.5]], notas=[round(serie(n, 3), 3) for n in (8, 9, 10, 12, 14, 15)])
GUIA = [dict(e, nota=round(e['nota'] + 24, 3)) for e in traductor]          # Sabina canta la guía del traductor dos octavas arriba

partitura = dict(titulo='El androide en la estación', semilla=SEMILLA, terreno=f"traspuesta 2038 «{TER['nombre']}», relieve {TER['relieve']} m, {TER['anchoKm']} km",
                 tonica_hz=TON, raiz=round(R0, 4), negra=Q, compas=BAR, dieciseisavo=S16, periodo=PER, frigio=FRIG,
                 secciones=[dict(bar=b, t=round(t_(b), 3), num=s, nombre=n) for b, s, n in SECC], duracion=round(DUR, 3), fin=round(t_(FIN_BAR), 3),
                 camino=[[round(a, 4), round(b, 4), round(c, 4)] for a, b, c in CAM[::2]], costa=COSTA / max(1, len(CAM) - 1), perfil_isla=PERFIL_ISLA,
                 web=ev, tres_tiempos=TT, boca_trazos=BOCA, sub=sub, traductor=traductor, oxido=OXIDO, convoy=CONVOY, luciernagas=LUC,
                 impresora=impresora, torniquete=torniquete, campana=campana, lluvia=lluvia, pulsos=pulsos, agua=agua,
                 sabina=[dict(eventos=GUIA, nivel=.9, pan=0, capa='guia'), dict(eventos=anden, nivel=.9, pan=0, capa='anden'), dict(eventos=soprano, nivel=.85, pan=0, capa='soprano')],
                 coros=coros, instrumentos='instrumentos-d25f002f7e96', tres_tiempos_codigo=[d for d in os.listdir(AQUI) if d.startswith('tres-tiempos-')][0])
for k in ('vocales', 'consonantes'): TT['boca'][k] = BOCA[k]
TT['boca']['controles'] = dict(vibrato=[[0, .1], [t_(INI['VI']), .3], [t_(104), .6], [DUR, .2]])
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', round(DUR, 1), 's · tónica', round(TON, 2), 'Hz (midi', round(R0, 2), ') · negra', round(Q, 4), 's ·', round(60 / Q, 1), 'bpm · periodo', PER, 's')
    print('camino', len(CAM), 'pasos · costa en', round(COSTA / max(1, len(CAM) - 1), 2), '· z', round(zc.max(), 2), '→', round(zc.min(), 2))
    print({k: len(v) for k, v in ev.items()}, {k: len(v['notas']) for k, v in TT.items()}, '· traductor', len(traductor), '· anden', len(anden), '· soprano', len(soprano), '· sub', len(sub))
