"""Cuento en siete — partitura. Math rock × Bach × Grisey × hyperpop, con un coro de vocoders y un dúo de bebop entre sinte y sax.
Semilla fija: misma semilla, misma pieza.

El reloj es la semicorchea (S) a negra = 144. Los compases se miden en semicorcheas: 14 (7/8) y, en los coros, 14 + 18
(7/8 + 9/8 = dos de 4/4: el math rock que se cuadra cada dos compases).

La armonía es espectral: cada acorde es un pedazo de la serie armónica de una fundamental (otonal) o de su espejo, la serie
subarmónica (utonal: oscura). Las fundamentales siguen el ciclo de terceras mayores de Coltrane (E, C, G#) con sus dominantes.
Los parciales 7, 11 y 13 se quedan en su altura justa (−31, −49 y +41 cents) en lo que sostiene; las líneas rápidas se redondean.

Forma (compases):
  I   espectro    0–10   el pedal de Mi del trombón se abre en sus parciales (Grisey, Partiels); el espectro se estira
  II  invención  10–26   invención a dos voces en 7/8 (Bach): sujeto, respuesta, estrecho, aumentación; el ciclo de terceras
  III coro       26–42   coral a cuatro voces: Sabina modula a los vocoders (pájaro, agua, berimbau, arpa de boca, sinte)
  IV  dúo        42–66   sinte y sax: bebop supersincopado. Cambios de 2 → 1 → ½ compás, canon y hoquetus. Los pájaros
                          (Bird) contestan cada final de frase del sax
  V   coro       66–82   el coro otra vez, con el sujeto en estrecho y el dúo en los huecos
  VI  coda       82–88   el espectro se recoge: de inarmónico a armónico, y sólo queda la fundamental
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys

SEMILLA = 1910
R = random.Random(SEMILLA)
BPM = 144; S = 60 / BPM / 4
LETRA = ['cuen to en sie te y me so bra el a gua', 'cuen to en cin co y me fal ta el ai re',
         'cuen to en on ce y el pá ja ro can ta', 'y to do lo que no ca be en la bo ca']
ACENTO = [[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0], [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0],
          [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0], [0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 1, 0]]
# el ritmo de cada verso en semicorcheas (64 = un par 14 + 18 y otro): síncopa de math rock, el último se queda
RITMO = [2, 3, 3, 2, 3, 3, 2, 3, 3, 2, 6, 32]

# ── compases ──
SEC = [('I', 10, [14]), ('II', 16, [14]), ('III', 16, [14, 18]), ('IV', 24, [14]), ('V', 16, [14, 18]), ('VI', 6, [14])]
COMP = []                                                # (inicio en semicorcheas, largo, sección, índice en la sección)
p = 0
for nom, n, met in SEC:
    for i in range(n):
        L = met[i % len(met)]; COMP.append((p, L, nom, i)); p += L
TOTAL16 = p
DUR = TOTAL16 * S + 7
def c0(b, s=0): return ((COMP[b][0] if b < len(COMP) else TOTAL16 + 14 * (b - len(COMP))) + s) * S   # hora del compás b, semicorchea s
def bars(nom): return [b for b, c in enumerate(COMP) if c[2] == nom]
def sec_en(t): return next((c[2] for c in reversed(COMP) if c[0] * S <= t + 1e-9), 'I')

# ── armonía espectral ──
E1 = 28.0
def m_parcial(f, k): return f + 12 * math.log2(k)
CENTS = {7: -31, 11: -49, 13: 41}
def acorde(fund, tipo):
    """tonos del acorde (midi con microtonos). otonal: parciales 4 5 6 7 9 11 13 de fund (en la octava 1).
    utonal: subarmónicos 4 5 6 7 9 de la nota que está dos octavas arriba (la serie al revés: oscuro)."""
    if tipo == 'o': return [m_parcial(fund, k) for k in (4, 5, 6, 7, 9, 11, 13)]
    top = fund + 24 + 12
    return sorted(top - 12 * math.log2(k) for k in (4, 5, 6, 7, 9))
def pcs(ac): return sorted({round(m % 12, 2) for m in ac})
def cerca(ac, objetivo, rango=(0, 127)):
    """el tono del acorde (en cualquier octava) más cercano a objetivo, dentro del rango"""
    best = None
    for m in ac:
        for o in range(-6, 7):
            x = m + 12 * o
            if rango[0] <= x <= rango[1] and (best is None or abs(x - objetivo) < abs(best - objetivo)): best = x
    return best
def redondo(m): return float(round(m))

FUND = dict(E=28, F=29, G=31, Gs=32, A=33, B=35, C=24 + 12, Ds=27)
CICLO = [(FUND['E'], 'u'), (FUND['G'], 'o'), (FUND['C'] - 12, 'u'), (FUND['Ds'], 'o'), (FUND['Gs'], 'u'), (FUND['B'], 'o')]   # Coltrane: E → G7 → C → D#7 → G# → B7 → E

ev = {k: [] for k in ['pluck', 'marimba', 'gyil', 'berimbau', 'berimbau-coro', 'arpaboca', 'arpaboca-coro', 'teponaztli', 'bateria', 'bateria-frito', 'bajo']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw):
    ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr808', stem='bateria'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)

# ═════════════════ I · espectro (Grisey) ═════════════════
# el trombón toca Mi2 (parcial 2 de E1); el espectro aparece parcial por parcial, del grave al agudo, y al final se estira
espectro = dict(fund=E1, parciales=[], estira=[])         # estira: [[t, sigma]] — f_k = f1 · k^(1 + sigma)
I = bars('I')
for k in range(2, 25):
    t = c0(0) + (k - 2) * (c0(10) - c0(0)) / 26 + R.uniform(0, .3)
    espectro['parciales'].append(dict(k=k, t=round(t, 3), v=round(1 / k ** .55, 3)))
espectro['estira'] = [[0, 0], [c0(5), 0], [c0(10), .045], [c0(10) + 2.5, .045]]
espectro['ritmo'] = dict(desde=c0(7), hasta=c0(10))      # al final del I los parciales laten en 2+2+3: el espectro se vuelve pulso
espectro['coda'] = dict(t0=c0(82), t1=c0(88) + 6, estira=[[c0(82), .045], [c0(85), 0]])
trombon = [dict(t=c0(0) + .1, dur=c0(10) - c0(0) + .3, m=40, tipo='normal', v=.75),
           dict(t=c0(82), dur=c0(88) - c0(82) + 4, m=40, tipo='normal', v=.6)]
wah = [[0, .1], [c0(4), .35], [c0(9), 1], [c0(10), .2], [c0(82), .9], [c0(88), .1]]
waterphone = [dict(t=c0(0) + .3, tipo='arco', m=m_parcial(E1, 11), dur=6, v=.5, agua=2.5, ola=.25),
              dict(t=c0(4), tipo='arco', m=m_parcial(E1, 13), dur=6, v=.45, agua=2, ola=.35),
              dict(t=c0(26), tipo='golpe', m=m_parcial(E1, 21), dur=4, v=.5, agua=1, ola=.4),
              dict(t=c0(82), tipo='arco', m=m_parcial(E1, 7) + 12, dur=8, v=.5, agua=3, ola=.2)]
gong = [dict(t=c0(0), tipo='cruce', m=m_parcial(E1, 4), v=.6, abre=3), dict(t=c0(6), tipo='arco', m=m_parcial(E1, 2), dur=c0(10) - c0(6), v=.5),
        dict(t=c0(26), tipo='tamtam', m=m_parcial(E1, 2), v=.8, dureza=.6), dict(t=c0(64), tipo='arco', m=m_parcial(E1, 2), dur=c0(66) - c0(64), v=.6),
        dict(t=c0(66), tipo='tamtam', m=m_parcial(E1, 2), v=.9, dureza=.7), dict(t=c0(82), tipo='cruce', m=m_parcial(E1, 4), v=.5, abre=2)]
for b in range(2, 10):                                    # arpa de boca: sube por la serie de Mi (Stimmung)
    h = [4, 5, 6, 7, 8, 9, 11, 13][b - 2]
    web('arpaboca', c0(b), 'arpaboca', m_parcial(E1, h), .55, (COMP[b][1] * S) * .95, -.15)
aves = []                                                  # pájaros de siringe (objetos que cantan)
for b in range(4, 10):
    if R.random() < .7:
        k = R.choice([16, 18, 20, 21, 22, 24]); m = m_parcial(E1, k)
        aves.append(dict(t=c0(b) + R.uniform(.2, 1.0), tipo='silbido', m=m, m2=m + R.choice([-5, 2, 7]), dur=round(R.uniform(.15, .4), 3), v=.5, voz=b % 2))
agua = [dict(t=0.0, tipo='burbujeo', dur=c0(10), v=.55)]

# ═════════════════ II · invención en 7/8 ═════════════════
# sujeto de 14 semicorcheas en la escala acústica de Mi (parciales 8–14): arpegio que sube, escala que baja, un salto
SUJ = [64, 68, 71, 76, 74, 73, 71, 70, 71, 66, 68, 64, 70, 63]
CS = [m - 9 for m in reversed(SUJ)]                         # contrasujeto: el sujeto al revés, una sexta abajo
def estira(m, sigma, eje=64): return eje + (m - eje) * (1 + sigma)
def sigma_inv(t): a, z = c0(10), c0(26); return .03 * min(1, max(0, (t - a) / (z - a)))   # la fuga se estira como un espectro
def frase(stem, ficha, b, s, notas, tr=0, inv=False, aum=1, vel=.62, pan=0.0, oct=0, salta=()):
    t = c0(b, s)
    for i, m in enumerate(notas):
        if i in salta: t += S * aum; continue
        x = (2 * notas[0] - m) if inv else m
        x = estira(x + tr + 12 * oct, sigma_inv(t))
        web(stem, t, ficha, x, vel + .18 * (i % 7 == 0) + .08 * (i % 7 == 4), S * aum * .9, pan); t += S * aum
II = bars('II'); b0 = II[0]
P1, P2 = ('pluck', 'consola-pluck'), ('marimba', 'marimba')
frase(*P1, b0, 0, SUJ, pan=-.35)
frase(*P2, b0 + 1, 0, SUJ, tr=7 - 12, pan=.35); frase(*P1, b0 + 1, 0, CS, tr=12, pan=-.35)
for j, tr in enumerate([0, -4, 4, 0]):                       # episodio: la cabeza del sujeto por el ciclo de terceras (E C G# E)
    frase(*P1, b0 + 2 + j // 2, 7 * (j % 2), SUJ[:7], tr=tr, pan=-.35)
    frase(*P2, b0 + 2 + j // 2, 7 * (j % 2), CS[7:], tr=tr - 12, pan=.35)
frase(*P2, b0 + 4, 0, SUJ, tr=-4 - 12, pan=.35); frase(*P1, b0 + 4, 0, CS, tr=-4 + 12, pan=-.35)
frase(*P1, b0 + 5, 0, SUJ, tr=4, pan=-.35); frase(*P2, b0 + 5, 0, CS, tr=4, pan=.35)
for j in range(2):                                           # hoquetus: el sujeto partido nota a nota entre las dos voces
    for i, m in enumerate(SUJ):
        st = P1 if i % 2 == j else P2
        web(st[0], c0(b0 + 6 + j, i), st[1], estira(m + (0 if st is P1 else -12) + 5 * j, sigma_inv(c0(b0 + 6))), .7, S * .9, -.35 if st is P1 else .35)
frase(*P1, b0 + 8, 0, SUJ, inv=True, pan=-.35); frase(*P2, b0 + 8, 3, SUJ, inv=True, tr=7 - 12, pan=.35, salta=(11, 12, 13))   # estrecho a la corchea con puntillo
frase(*P1, b0 + 9, 0, SUJ, tr=-4, pan=-.35); frase(*P2, b0 + 9, 3, SUJ, tr=-4 - 5, pan=.35, salta=(11, 12, 13))
for j in range(2):                                           # 5 contra 7: una célula de 5 que se corre sobre el compás
    for i in range(14):
        cel = [71, 68, 76, 70, 64]
        web('pluck', c0(b0 + 10 + j, i), 'consola-pluck', estira(cel[(i + 14 * j) % 5] + 4 * j, sigma_inv(c0(b0 + 10))), .6 + .2 * ((i + 14 * j) % 5 == 0), S * .9, -.35)
    frase(*P2, b0 + 10 + j, 0, SUJ[::2], aum=2, tr=-12 + 4 * j, pan=.35)
frase(*P2, b0 + 12, 0, SUJ, aum=2, tr=-24, pan=.35, vel=.7)  # aumentación en el grave y el sujeto contra sí mismo arriba
for j in range(2): frase(*P1, b0 + 12 + j, 0, SUJ, tr=12 * j, pan=-.35)
frase(*P1, b0 + 14, 0, SUJ, pan=-.35); frase(*P2, b0 + 14, 0, SUJ, tr=-8, pan=.35)   # décimas paralelas
for i, m in enumerate([64, 71, 76, 80, 83]):                  # cadencia: el acorde de Mi (parciales 4 6 8 10 12) sostenido
    web('marimba', c0(b0 + 15, i), 'marimba', m - 12, .65, S * 8, .35); web('pluck', c0(b0 + 15, i), 'consola-pluck', m, .6, S * 8, -.35)

# percusiones de math rock: 7/8 en 2+2+3, el bombo empuja, la caja cae en el 4 y en el 11; toms al final de cada 4 compases
def groove7(b, intenso, ride=True):
    L = COMP[b][1]; t = lambda s: c0(b, s)
    for s in (0, 6) if L == 14 else (0, 6, 12): bat(t(s), 'kick', .95)
    if intenso: bat(t(10), 'kick', .7)
    for s in (4, 11) if L == 14 else (4, 10, 16): bat(t(s), 'snare', .85, .05)
    for s in range(0, L, 2): bat(t(s), 'ride' if ride else 'hat', .55 + .25 * (s in (0, 4, 8)), .25)
    for s in (2, 9, 13) if L == 14 else (2, 8, 14): bat(t(s), 'snare', .18, .05)       # notas fantasma
for b in II:
    i = b - b0
    if i < 4:
        for s in (0, 4, 8): bat(c0(b, s), 'rim', .55, -.1)
        bat(c0(b), 'kick', .8)
    else: groove7(b, i >= 8)
    if i % 4 == 3 and i > 2:
        for k, (s, pz) in enumerate([(8, 'tomhi'), (9, 'tomhi'), (10, 'tommid'), (11, 'tommid'), (12, 'tomlo'), (13, 'tomlo')]): bat(c0(b, s), pz, .7 + .04 * k, -.3 + .1 * k)
    for s, gr in [(0, 0), (4, 0), (8, 1), (11, 1)]: web('teponaztli', c0(b, s), 'teponaztli', 64 + gr * 3, .5 + .15 * (s == 0), .3, -.2)
    if i >= 2:
        for s, vel, gr in [(0, .3, 0), (2, .3, 0), (4, .85, 0), (8, .85, 1), (11, .7, 0)]: web('berimbau', c0(b, s), 'berimbau', 52 + gr, vel, .3, .2)
tambor = [dict(t=c0(b0 + 3) + .02, tipo='habla', texto='cuento en siete', m=50, dur=S * 2, v=.8, alto=5),
          dict(t=c0(b0 + 11) + .02, tipo='habla', texto='cuento en cinco', m=50, dur=S * 2, v=.8, alto=5)]
for b in II[4:]:                                             # gotas afinadas doblando las entradas (el agua cuenta en 5)
    for s in range(0, 14, 5 if b % 2 else 3): agua.append(dict(t=c0(b, s), tipo='gota', m=redondo(m_parcial(E1, R.choice([16, 18, 20, 24]))), v=.42))
golpes_barra = []                                            # objeto que cantan, barra: el acento de cada compás
for b in II[8:]: golpes_barra.append(dict(t=c0(b), m=m_parcial(E1, 8), v=.7)); golpes_barra.append(dict(t=c0(b, 11), m=m_parcial(E1, 12), v=.5))

# ═════════════════ III / V · coro de vocoders ═════════════════
F_ = FUND
# cuatro acordes por verso, en las sílabas 0, 3, 7 y 10 (las que llevan acento): el ritmo armónico del coral
CORO_ACORDES = [[(F_['E'], 'o'), (F_['G'], 'o'), (F_['C'] - 12, 'u'), (F_['B'], 'o')],
                [(F_['E'], 'u'), (F_['Ds'], 'o'), (F_['Gs'], 'u'), (F_['B'], 'o')],
                [(F_['C'] - 12, 'o'), (F_['Ds'], 'o'), (F_['Gs'], 'u'), (F_['G'], 'o')],
                [(F_['C'] - 12, 'u'), (F_['B'], 'o'), (F_['E'], 'u'), (F_['E'], 'o')]]
CAMBIA = [0, 3, 7, 10]
# el contorno de la soprano (semitonos sobre La4 = 69), compuesto a mano: arco por verso, el tercero el más alto
CONTORNO = [[-2, 0, 2, 5, 3, 2, 0, 7, 5, 3, 2, -2], [-2, 0, 2, 5, 3, 2, 0, 8, 7, 5, 3, 0],
            [0, 2, 3, 7, 5, 3, 2, 10, 8, 7, 5, 3], [7, 5, 3, 2, 3, 5, 7, 12, 10, 7, 3, 2]]
def coral(barras):
    """coral a cuatro (Bach): la soprano lleva la letra; en las sílabas con acorde nuevo cada voz va al tono del acorde más
    cercano (sin repetir la nota si puede moverse); en las otras, nota de paso o bordadura hacia el acorde siguiente.
    Devuelve las sílabas de cada voz [{t, dur, texto, nota, acento}] y los acordes con su hora y su duración."""
    voces = {v: [] for v in 'SATB'}; acordes = []
    prev = dict(S=71, A=64, T=57, B=40); RANG = dict(S=(62, 77), A=(55, 70), T=(47, 62))
    for verso in range(4):
        b = barras[2 * verso * 2]                       # cada verso ocupa dos pares (4 compases: 14 18 14 18 = 64)
        t0 = c0(b); s = 0
        silabas = LETRA[verso].split(); k = -1
        for j, (sil, d) in enumerate(zip(silabas, RITMO)):
            if j in CAMBIA:
                k += 1; fund, tipo = CORO_ACORDES[verso][k]; ac = acorde(fund, tipo)
                fin = t0 + (sum(RITMO[:CAMBIA[k + 1]]) if k < 3 else 64) * S
                acordes.append(dict(t=round(t0 + s * S, 5), fin=round(fin, 5), fund=fund, tipo=tipo, tonos=ac))
            ac_ = ACENTO[verso][j]; nuevo = j in CAMBIA; n = {}
            for v in 'SAT':
                lo, hi = RANG[v]
                if v == 'S':
                    obj = 69 + CONTORNO[verso][j]
                elif v == 'A': lo, hi = lo, min(hi, n['S'] - 3); obj = prev['A'] + (1 if j % 2 else -1)
                else: lo, hi = lo, min(hi, n['A'] - 2); obj = prev['T'] + (-1 if j % 2 else 1)
                if nuevo or v == 'S' and ac_:
                    x = cerca(ac, obj, (lo, hi))
                    if abs(x - prev[v]) < .3:                 # no se queda quieta si hay otro tono cerca
                        alt = [cerca(ac, prev[v] + d_, (lo, hi)) for d_ in (2.5, -2.5)]
                        alt = [a for a in alt if a is not None and abs(a - prev[v]) > .3]
                        x = alt[0] if alt else x
                else:                                          # nota de paso por la escala del acorde (redonda)
                    esc = sorted({round(m) % 12 for m in ac} | {round(m_parcial(fund, kk)) % 12 for kk in (9, 11, 13)})
                    paso = 1 if obj > prev[v] else -1
                    x = (round(obj) if v == 'S' else prev[v] + paso)
                    while round(x) % 12 not in esc: x += paso
                    x = min(max(x, lo), hi)
                n[v] = redondo(x) if v == 'S' else round(x, 3)
            baj = fund + 12 if fund + 12 >= 36 else fund + 24
            n['B'] = baj
            for v in 'SATB':
                voces[v].append(dict(t=round(t0 + s * S, 5), dur=round(d * S * (.92 if d < 30 else .98), 4), texto=sil, nota=round(n[v], 3), acento=ac_))
            prev.update(S=n['S'], A=n['A'], T=n['T']); s += d
    return voces, acordes
CORO1, ACORDES1 = coral(bars('III'))
CORO2, ACORDES2 = coral(bars('V'))

def coro_capas(voces, intenso):
    # pájaro (soprano): la siringe canta la línea; vocoder de Sabina en la mezcla
    for e in voces['S']:
        aves.append(dict(t=e['t'], tipo='canto', notas=[[0, e['nota'] + 12, e['dur'] * .95]], dur=e['dur'] + .02, v=.55, voz=0, coro=1))
    # berimbau (tenor): el arco suena en semicorcheas mientras dura la sílaba; su tónica es la nota del tenor
    for e in voces['T']:
        n = max(1, int(round(e['dur'] / S)))
        for k in range(min(n, 8)):
            web('berimbau-coro', e['t'] + k * S, 'berimbau', e['nota'], .8 if k == 0 else .45 + .2 * (k % 3 == 0), .2, .15, tonica=int(round(e['nota'])) % 12)
    # arpa de boca (bajo): la lengüeta es la fundamental del acorde, la boca elige el armónico de la soprano (Stimmung)
    for e, s in zip(voces['B'], voces['S']):
        web('arpaboca-coro', e['t'], 'arpaboca', s['nota'], .7, e['dur'], -.2, tonica=int(round(e['nota'])) % 12)
coro_capas(CORO1, False); coro_capas(CORO2, True)
vozagua = []                                                 # el agua canta la contralto con su propia voz (vozagua: burbujas en los formantes)
for voces in (CORO1, CORO2):
    for e in voces['A']: vozagua.append(dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota'], modo='canto', voz=1, v=.7))
sabina = []                                                  # la moduladora: Sabina canta la soprano (y en el V, una octava abajo también)
for voces, extra in ((CORO1, False), (CORO2, True)):
    for verso in range(4):
        sil = voces['S'][12 * verso:12 * verso + 12]
        sabina.append(dict(eventos=[dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota']) for e in sil], nivel=.85, pan=0, capa='soprano'))
        if extra: sabina.append(dict(eventos=[dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota'] - 12) for e in sil], nivel=.6, pan=0, capa='baja'))

# batería del coro: hyperpop sobre 7 + 9 — 808, palmas fritas, hats con rachas, sidechain (en la mezcla)
sub = []
def groove_coro(b, intenso):
    L = COMP[b][1]; t = lambda s: c0(b, s)
    kicks = (0, 6, 10) if L == 14 else (0, 6, 10, 14)
    for s in kicks: bat(t(s), 'kick', 1.0)
    for s in (4, 11) if L == 14 else (4, 12): bat(t(s), 'clap', .85, 0, 'bateria-frito', 'bateria-frito')
    racha = (L == 18 and COMP[b][3] % 4 == 3)
    for s in range(L):
        if racha and s >= 12:
            for j in range(3): bat(t(s) + j * S / 3, 'hat', .45 + .15 * j, .2)
        elif s % 2 == 0 or intenso: bat(t(s), 'hat', .6 if s % 2 == 0 else .35, .2)
    if intenso and COMP[b][3] % 2:
        for s in (3, 7): bat(t(s), 'openhat', .4, -.2)
for nom, intenso in (('III', False), ('V', True)):
    for b in bars(nom):
        groove_coro(b, intenso)
        if COMP[b][3] in (0, 8): web('bateria-frito', c0(b), 'bateria-frito', 60, 1.0, .3, 0, pieza='spray')
    for a in (ACORDES1 if nom == 'III' else ACORDES2):
        f = a['fund']; f = f if f >= 26 else f + 12
        while f > 37: f -= 12
        sub.append(dict(t=a['t'], midi=f, vel=.9, dur=round((a['fin'] - a['t']) * .97, 4)))
glitch = [c0(b) - 4 * S for b in (34, 42, 74, 82)]           # al final de los versos 2 y 4: la mezcla tartamudea

# ═════════════════ IV · dúo de bebop supersincopado ═════════════════
IV = bars('IV'); d0 = IV[0]
def cambio(t):
    """el acorde que suena en t: dos por compás (8 + 6 semicorcheas), siguiendo el ciclo de 6; con 7/8 y dos cambios por
    compás, el ciclo cae en otro lugar del compás cada vez (6 contra 2)"""
    k16 = round((t - c0(d0)) / S); b = k16 // 14; r = k16 % 14
    k = 2 * b + (0 if r < 8 else 1)
    fund, tipo = CICLO[k % len(CICLO)]
    return fund, tipo, acorde(fund, tipo)
def escala_de(fund, tipo):
    """escala de bebop espectral: la serie 8–15 (escala acústica + la séptima mayor de paso) o, utonal, su espejo"""
    if tipo == 'o': return sorted({round(m_parcial(fund, k)) % 12 for k in (8, 9, 10, 11, 12, 13, 14, 15)})
    top = fund + 48; return sorted({round(top - 12 * math.log2(k)) % 12 for k in (8, 9, 10, 11, 12, 13, 14, 15)})
def en_escala(m, esc): return round(m) % 12 in esc

def ritmo_frase(rng, largo16):
    """el esqueleto: semicorcheas con huecos, tresillos de semicorchea (3 en 2) y quintillos (5 en 4) que cruzan el pulso.
    Las frases empiezan a contratiempo y los acentos van cada 3 (o 5) notas: el acento se corre sobre el 7/8 (supersíncopa)."""
    out = []; s = rng.choice([1, 1, 3, 2, 5]) * 1.0
    while s < largo16 - 1:
        lf = rng.choice([7, 9, 11, 13, 6, 10])
        cada = rng.choice([3, 3, 5, 2])
        k = 0; fin = min(largo16 - .5, s + lf)
        while s < fin:
            r = rng.random()
            if r < .12 and s + 2 <= fin:                    # tresillo: 3 notas en dos semicorcheas
                for j in range(3): out.append([s + j * 2 / 3, 2 / 3, k % cada == 0]); k += 1
                s += 2
            elif r < .18 and s + 4 <= fin:                  # quintillo: 5 en 4 (el pulso se estira)
                for j in range(5): out.append([s + j * .8, .8, k % cada == 0]); k += 1
                s += 4
            else:
                out.append([s, 1, k % cada == 0]); k += 1; s += 1
        if out: out[-1][1] = rng.choice([1, 1.5, 2, 3]); out[-1][2] = True      # el final de frase: corto y acentuado (du-BAH)
        s = math.floor(s) + rng.choice([1, 1, 2, 3])  # silencio: el siguiente entra fuera del tiempo
        s = s if rng.random() < .7 else (s // 2) * 2 + 1                        # 70 %: impar = a contratiempo
    return out

def linea_bebop(rng, t0, largo16, rango, inicio):
    """las alturas: en cada acento un tono del acorde (del acorde que viene si el acento cae una semicorchea antes del
    cambio: anticipación); entre acentos, células de bebop que terminan en él: aproximación cromática, encierro (arriba
    en la escala, abajo cromático), corrida de escala, arpegio del 3 al 9 de Parker. A veces la frase se va medio tono
    arriba (side-slipping) y regresa."""
    esq = ritmo_frase(rng, largo16); notas = []; m = inicio; i = 0
    while i < len(esq):
        j = i
        while j < len(esq) and not esq[j][2]: j += 1   # el siguiente acento
        if j >= len(esq): j = len(esq) - 1
        tA = t0 + esq[j][0] * S
        fund, tipo, ac = cambio(tA + S * 1.01)          # anticipación: el acento ve el acorde de una semicorchea después
        esc = escala_de(fund, tipo)
        sube = m < (rango[0] + rango[1]) / 2 + rng.uniform(-6, 6)
        objetivo = cerca(ac, m + (rng.choice([3, 4, 5, 7]) if sube else -rng.choice([2, 3, 4, 5])), rango)
        objetivo = redondo(objetivo)
        n = j - i                                       # cuántas notas antes del acento
        cel = []
        if n == 1: cel = [objetivo + rng.choice([-1, 1])]
        elif n == 2:
            arr = objetivo + 1; arr = arr if en_escala(arr, esc) else objetivo + 2
            cel = [arr, objetivo - 1]
        elif n >= 3:
            if rng.random() < .45:                       # arpegio 3-5-7-9 (o al revés) hacia el objetivo
                arp = sorted({redondo(cerca(ac, objetivo + d, rango)) for d in (-14, -10, -7, -4)})
                cel = (arp if sube else arp[::-1])[:n - 1] + [objetivo + rng.choice([-1, 1])]
            else:                                         # corrida de escala con el paso cromático en su lugar
                paso = -1 if sube else 1; x = objetivo
                for _ in range(n):
                    x += paso
                    while not en_escala(x, esc) and rng.random() < .75: x += paso
                    cel.append(x)
                cel = cel[::-1]
            while len(cel) < n: cel.insert(0, cel[0] + rng.choice([-2, -1, 1, 2]))
            cel = cel[-n:]
        if rng.random() < .1: cel = [c + 1 for c in cel]  # side-slip: medio tono afuera y de regreso al acento
        for k, c in enumerate(cel + [objetivo]):
            c = min(max(c, rango[0] - 2), rango[1] + 2)
            s, d, acento = esq[i + k]
            notas.append(dict(t=round(t0 + s * S, 5), dur=round(d * S, 5), m=c, acento=bool(acento) or k == len(cel), fantasma=(not acento and rng.random() < .3)))
        m = objetivo; i = j + 1
    # la nota larga sobre el séptimo parcial queda justa (−31 cents): lo contemporáneo es la afinación, no sólo el ritmo
    for nt in notas:
        fund, tipo, ac = cambio(nt['t'])
        if nt['dur'] >= 2 * S and tipo == 'o' and abs(((nt['m'] - m_parcial(fund, 7)) % 12)) < .6: nt['m'] = round(nt['m'] - .31, 3)
    return notas

def transforma(notas, t_de, t_a, modo, eje=None, rng=None):
    """el sinte contesta al sax con lo que Bach le haría al sujeto: inversión, retrógrado, desplazamiento de una semicorchea"""
    out = []
    eje = eje if eje is not None else notas[0]['m']
    for n in notas:
        x = dict(n); x['t'] = round(n['t'] - t_de + t_a, 5)
        if 'inv' in modo: x['m'] = 2 * eje - n['m']
        if 'des' in modo: x['t'] = round(x['t'] + S, 5)
        out.append(x)
    if 'ret' in modo:
        T0, T1 = t_a, max(n['t'] + n['dur'] for n in out)
        out = [dict(n, t=round(T0 + (T1 - (n['t'] + n['dur'])), 5)) for n in out][::-1]
    if rng is not None:                                   # y lo reacomoda al acorde del lugar nuevo (el acento sí cae en tono)
        for n in out:
            if n['acento']: n['m'] = redondo(cerca(cambio(n['t'])[2], n['m'], (n['m'] - 3, n['m'] + 3)) or n['m'])
    return out

rng = random.Random(SEMILLA + 4)
SAX_R, SIN_R = (49, 75), (55, 84)                          # el sax (La2–Mib5 suena afinado en objeto.js); el sinte, arriba
sax, sinte = [], []
def bloque(b, nb): return c0(b), sum(COMP[x][1] for x in range(b, b + nb))
# IVa: cambios de 2 compases
for k in range(4):
    b = d0 + 2 * k; t0, L = bloque(b, 2)
    if k % 2 == 0: sax += linea_bebop(rng, t0, L, SAX_R, 64 if k == 0 else sax[-1]['m'])
    else:
        prev = [n for n in sax if c0(b - 2) <= n['t'] < t0]
        sinte += transforma(prev, c0(b - 2), t0, 'inv des' if k == 1 else 'ret', eje=prev[0]['m'] + 7, rng=rng)
# IVb: 1 compás y luego medio (8 | 6)
for k in range(4):
    b = d0 + 8 + k; t0, L = bloque(b, 1)
    (sax if k % 2 == 0 else sinte).extend(linea_bebop(rng, t0, L, SAX_R if k % 2 == 0 else SIN_R, 66 if k % 2 == 0 else 74))
for b in range(d0 + 12, d0 + 16):
    sax += linea_bebop(rng, c0(b), 8, SAX_R, sax[-1]['m'])
    sinte += linea_bebop(rng, c0(b, 8), 6, SIN_R, 76)
# IVc: juntos. Canon del sinte a 3 semicorcheas (estrecho), una sexta arriba; luego hoquetus y unísono
t0, L = bloque(d0 + 16, 4)
canon = linea_bebop(rng, t0, L, SAX_R, 62); sax += canon
sinte += [dict(n, t=round(n['t'] + 3 * S, 5), m=n['m'] + 9) for n in canon if n['t'] + 3 * S < c0(d0 + 20)]
t0, L = bloque(d0 + 20, 3)
hoq = linea_bebop(rng, t0, L, (55, 79), 67)
for i, n in enumerate(hoq): (sax if i % 2 == 0 else sinte).append(dict(n, acento=True))
UNI = [64, 67, 71, 70, 64, 63, 76, 74, 71, 66, 64, 0, 76, 64]   # el riff final al unísono (math rock): 0 = silencio
for i, m in enumerate(UNI):
    if m:
        for lst, o in ((sax, 0), (sinte, 12)): lst.append(dict(t=round(c0(d0 + 23, i), 5), dur=S * (.9 if i < 13 else 3), m=m + o - 12 * (lst is sax and m > 72), acento=i in (0, 6, 12), fantasma=False))
sax.sort(key=lambda n: n['t']); sinte.sort(key=lambda n: n['t'])

# los pájaros (Bird) contestan cada final de frase del sax: las últimas 3–5 notas, dos octavas arriba, en canto de Messiaen
fines = [n for i, n in enumerate(sax[:-1]) if sax[i + 1]['t'] - (n['t'] + n['dur']) > 1.5 * S and n['t'] < c0(d0 + 20)]
for n in fines[::2]:
    i = sax.index(n); cita = sax[max(0, i - 4):i + 1]
    t = n['t'] + n['dur'] + .03
    aves.append(dict(t=round(t, 4), tipo='canto', notas=[[round(c['t'] - cita[0]['t'], 4) * .8, c['m'] + 24, round(c['dur'] * .7, 4)] for c in cita],
                     dur=round((cita[-1]['t'] - cita[0]['t']) * .8 + .2, 4), v=.5, voz=len(aves) % 2))

# sección rítmica del dúo: walking en 7 (4+4+3+3), ride en 2+2+3, la caja comenta y suelta «bombas» en los acentos del sax
for b in IV:
    pos = (0, 4, 8, 11)
    for k, s in enumerate(pos):
        fund, tipo, ac = cambio(c0(b, s))
        sig = cambio(c0(b, pos[k + 1]) if k < 3 else c0(b + 1) if b + 1 < len(COMP) else c0(b, s))
        raiz = fund + 12 if fund + 12 >= 33 else fund + 24
        while raiz > 45: raiz -= 12
        if k == 0 or s == 8: n = raiz
        elif k == 3: n = (sig[0] % 12) + 12 * math.floor(raiz / 12) + rng.choice([-1, 1])     # aproximación cromática al siguiente
        else: n = redondo(cerca(ac, raiz + rng.choice([3, 4, 7]), (31, 50)))
        web('bajo', c0(b, s), 'consola-bass', n, .85 if k in (0, 2) else .7, S * (pos[k + 1] - s if k < 3 else 3) * .95, 0)
    for s in range(0, 14, 2): bat(c0(b, s), 'ride', .5 + .25 * (s in (0, 4, 8)), .25)
    bat(c0(b, 4), 'hat', .5, .2); bat(c0(b, 11), 'hat', .5, .2)
    bat(c0(b), 'kick', .7)
for n in sax + sinte:
    if n['acento'] and rng.random() < .22 and c0(d0) <= n['t'] < c0(d0 + 23): bat(n['t'], rng.choice(['snare', 'kick', 'snare', 'tomlo']), .75, -.05)
    elif not n['acento'] and rng.random() < .08: bat(n['t'], 'snare', .2, .05)
for b in IV[-1:]:
    for i, m in enumerate(UNI):
        if m: bat(c0(b, i), 'kick' if i % 3 == 0 else 'snare', .9); bat(c0(b, i), 'tommid', .6)
# comping: la marimba suelta acordes de tres notas en lugares sincopados (2 por medio compás)
for b in IV[:-1]:
    for s in rng.sample([1, 3, 5, 6, 9, 10, 12, 13], 3):
        fund, tipo, ac = cambio(c0(b, s))
        for o in (52, 57, 62): web('marimba', c0(b, s), 'marimba', redondo(cerca(ac, o, (48, 70))), .45, S * 1.5, .3)

# ═════════════════ V · coro + invención + dúo en los huecos ═════════════════
V = bars('V')
for k, b in enumerate(V):
    if COMP[b][1] == 14: frase(*P1, b, 0, SUJ, tr=[0, -4, 4, 0][(k // 4) % 4], pan=-.35, vel=.5)
    else: frase(*P2, b, 2, SUJ, tr=[0, -4, 4, 0][(k // 4) % 4] - 12, pan=.35, vel=.5)
    groove7(b, True, ride=False) if False else None
huecos = []                                               # en el silencio largo de cada verso (la última sílaba sostenida) entra el dúo
for verso in range(4):
    sil = CORO2['S'][12 * verso:12 * verso + 12]
    t0 = sil[-1]['t'] + 4 * S; L = 24
    (sax if verso % 2 == 0 else sinte).extend(linea_bebop(rng, t0, L, SAX_R if verso % 2 == 0 else SIN_R, 64 if verso % 2 == 0 else 76))
sax.sort(key=lambda n: n['t']); sinte.sort(key=lambda n: n['t'])

# ═════════════════ VI · coda ═════════════════
VI = bars('VI')
for k, h in enumerate([16, 13, 11, 9, 7, 6, 5, 4]):        # la serie baja hasta su fundamental
    web('arpaboca', c0(VI[0]) + k * 3 * S * 2, 'arpaboca', m_parcial(E1, h), .5, 4.5 if k < 7 else 8, -.15)
for b in VI[1:5]:                                           # un pájaro dice el sujeto, lento (Messiaen)
    aves.append(dict(t=c0(b) + .1, tipo='canto', notas=[[i * S * 2, m + 24, S * 1.8] for i, m in enumerate(SUJ[:7])], dur=14 * S + .2, v=.45, voz=b % 2))
agua.append(dict(t=c0(VI[0]), tipo='ola', dur=c0(VI[-1]) + 6 - c0(VI[0]), v=.5))
agua.append(dict(t=c0(26), tipo='burbujeo', dur=c0(42) - c0(26), v=.35))
for b in IV[::2]: agua.append(dict(t=c0(b, 7), tipo='gota', m=redondo(m_parcial(E1, 20)), v=.35))

# el sax y el sinte en la forma que piden sus motores
SAX = [dict(t=n['t'], dur=n['dur'], m=n['m'], lengua=1 if (n['acento'] or n['dur'] >= 2 * S) else 0, v=.62 if n['fantasma'] else (1.0 if n['acento'] else .84)) for n in sax]
SINTE = [dict(t=n['t'], dur=n['dur'], m=n['m'], v=.6 if n['fantasma'] else (1.0 if n['acento'] else .8)) for n in sinte]
# la barra del objeto: el acento de los compases del V también
for b in V[::2]: golpes_barra.append(dict(t=c0(b), m=m_parcial(E1, 8), v=.6))

partitura = dict(titulo='Cuento en siete', semilla=SEMILLA, bpm=BPM, semicorchea=S, compases=COMP, secciones=[s[0] for s in SEC],
                 duracion=DUR, tonica='E', escala=[0, 2, 4, 6, 7, 9, 10], letra=LETRA, web=ev, espectro=espectro, trombon=trombon, wah=wah,
                 waterphone=waterphone, gong=gong, aves=aves, agua=agua, tambor=tambor, golpes_barra=golpes_barra, vozagua=vozagua,
                 sabina=sabina, coro=dict(III=CORO1, V=CORO2), acordes=dict(III=ACORDES1, V=ACORDES2), sub=sub, glitch=glitch,
                 sax=SAX, sinte=SINTE, instrumentos='instrumentos-dedf969a0fe6')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False, indent=0)
    print('duración', round(DUR, 1), 's ·', {k: len(v) for k, v in ev.items()}, '· sax', len(SAX), '· sinte', len(SINTE), '· aves', len(aves), '· agua', len(agua), '· sabina', len(sabina))
