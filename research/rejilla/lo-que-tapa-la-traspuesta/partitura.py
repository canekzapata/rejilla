"""Lo que tapa la traspuesta — partitura. Weather Report × hyperpop × Ben Nobuto × Lachenmann, sobre el terreno 420048 de
Traspuesta y la meseta del ritornelo de Mil mesetas. Semilla fija: misma semilla, misma pieza.

LA RETÍCULA (lo estriado) sale del terreno: el relieve de 420048 son 2750 m; con curvas de nivel cada 250 m hay 11 escalones,
así que la escala se repite cada 11 semitonos (no octaviante: Boulez en «Lo liso y lo estriado»). Sus grados son los escalones
donde están las cumbres de las siluetas (de frente y de lado): {0, 5, 9, 10}. Como 11 no es 12, cada periodo cae en otras
clases de altura: la espiral misma llena la armonía. LO LISO es la altura continua: el viento sin retícula, los glisandos.

LA FORMA es el ritornelo (Mil mesetas, 1837): tres aspectos —
  I   punto gris   (Lachenmann) sin pulso: viento, aire por los tubos, arco sobre la madera, la montaña que respira. Un niño
                   canturrea para no tener miedo: la cancioncilla (las cuatro cumbres, en el orden del perfil)
  II  casa         (Weather Report) se traza el círculo: groove, bajo sin trastes, sinte y sax al unísono, percusiones; el coro
                   de vocoders canta el primer verso
  III coro         (hyperpop, Nobuto) el estribillo; tijeras: la mezcla se corta, se repite y se salta
  IV  abrir        solos: Siringua de tres gargantas (agua, montaña y pájaro) y el vocoder que improvisa; cambios y recorte;
                   una escena de pájaros (el Scenopoietes que voltea las hojas)
  V   liso         la retícula se disuelve: tormenta, todo se desliza; el coro final
  VI  coda         la cancioncilla sola en el viento; la montaña dice la última palabra
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np

SEMILLA = 420048
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__))
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-420048.f32'), np.float32).reshape(360, 360)
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-420048.json'), encoding='utf-8'))

# ── la retícula del terreno ──
EQUI = 250; PERIODO = round(TER['relieve'] / EQUI)          # 2750 / 250 = 11
def cumbres(sil):
    s = np.convolve(sil, np.ones(5) / 5, 'same')
    return [i for i in range(3, 357) if s[i] > s[i - 1] and s[i] >= s[i + 1] and s[i] > s[i - 3] and s[i] >= s[i + 3]], s
pk_f, sil_f = cumbres(H.max(0)); pk_l, sil_l = cumbres(H.max(1))
GRADOS = sorted({int(round(sil_f[i] * PERIODO)) % PERIODO for i in pk_f} | {int(round(sil_l[i] * PERIODO)) % PERIODO for i in pk_l})   # {0, 5, 9, 10}
BASE = 28                                                    # Mi1: el escalón 0 (la base del terreno)
def grado(k): q, r = divmod(k, len(GRADOS)); return BASE + q * PERIODO + GRADOS[r]
RET = [grado(k) for k in range(0, 40)]                        # la retícula entera, del grave al agudo
def cuant(m): return min(RET, key=lambda x: abs(x - m))
def idx(m): return min(range(len(RET)), key=lambda k: abs(RET[k] - m))
def paso(m, d): return RET[max(0, min(len(RET) - 1, idx(m) + d))]
# la cancioncilla: las cumbres de la silueta de lado (5), en orden, cada una tantos escalones de la retícula arriba de Do#3
# como su altura (la más baja, .49, es el escalón 0; la cumbre mayor, el 7). Las de frente casi empatan (.91 .92 1.0): daban 60 60 61
_lo, _hi = min(sil_l[i] for i in pk_l), max(sil_l[i] for i in pk_l)
CANC = [RET[idx(49) + int(round((sil_l[i] - _lo) / (_hi - _lo) * 7))] for i in pk_l]
CANC_RIT = [round(4 * (pk_l[k + 1] - pk_l[k]) / (pk_l[-1] - pk_l[0]) * 3) / 4 + .5 for k in range(len(pk_l) - 1)] + [1.5]   # duraciones (negras) por la distancia entre cumbres

# ── el reloj: I y VI sin pulso (segundos); II–V a negra = 104 en semicorcheas ──
BPM = 104; S = 60 / BPM / 4; BAR = 16 * S
T_I = 28.0
SECC = [('I', None, T_I), ('II', 16, None), ('III', 8, None), ('IV', 20, None), ('V', 8, None), ('VI', None, 17.0)]
INI = {}; t = 0.0
for nom, nb, seg in SECC:
    INI[nom] = t; t += seg if seg else nb * BAR
INI['fin'] = t; DUR = t + 5
def b(nom, k, s=0): return INI[nom] + k * BAR + s * S       # compás k de la sección, semicorchea s

# ── perfiles del terreno en el tiempo: la pieza camina por la cordillera de norte a sur ──
def fila(j): p = H[j].astype(float); return (p / (p.max() or 1)).round(4).tolist()
PERFILES = [[round(INI['fin'] * k / 24, 3), 30 + int(300 * k / 24)] for k in range(25)]   # (t, fila)

ev = {k: [] for k in ['berimbau', 'teponaztli', 'bateria', 'bateria-frito', 'marimba']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr808', stem='bateria'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)

# objetos que cantan (Lachenmann): clarinete, trombón, chelo, piano preparado, gong
clar, trombon, chelo, piano, gong, aves, agua = [], [], [], [], [], [], []
garganta, vozagua, siringa = [], [], []                   # la garganta de montaña, la voz de agua, el pájaro que contesta

# ═════════════ I · punto gris (Lachenmann) ═════════════
# sin pulso: sonidos de presión y de aire, con silencios. Cada gesto tiene su lugar en el tiempo, no en un compás.
gestos = [(0.6, 'chelo', 'legno'), (1.4, 'clar', 'aire'), (2.9, 'piano', 'caja'), (3.3, 'chelo', 'ponticello'), (5.2, 'trombon', 'aire'), (6.0, 'gong', 'roce'),
          (7.7, 'clar', 'llaves'), (8.1, 'clar', 'llaves'), (8.35, 'clar', 'llaves'), (9.4, 'chelo', 'bartok'), (10.2, 'trombon', 'frulato'), (11.5, 'clar', 'slap'),
          (12.0, 'chelo', 'tasto'), (13.6, 'piano', 'apagada'), (14.1, 'clar', 'multifonico'), (15.8, 'chelo', 'legno'), (16.0, 'chelo', 'legno'), (16.15, 'chelo', 'legno'),
          (17.5, 'trombon', 'growl'), (19.0, 'clar', 'aire'), (20.4, 'chelo', 'ponticello'), (22.0, 'gong', 'roce'), (24.5, 'clar', 'slap'), (25.3, 'chelo', 'bartok')]
for t0, ins, tec in gestos:
    m = cuant(R.choice([40, 45, 50, 52, 55]))
    if ins == 'chelo': chelo.append(dict(t=t0, m=m, v=R.uniform(.4, .8), dur=R.uniform(.3, 2.2) if tec in ('ponticello', 'tasto') else .25, tipo=tec))
    elif ins == 'clar': clar.append(dict(t=t0, m=cuant(R.choice([40, 43, 47])), v=R.uniform(.4, .7), dur=R.uniform(.2, 1.6) if tec in ('aire', 'multifonico') else .12, tipo=tec))
    elif ins == 'trombon': trombon.append(dict(t=t0, m=cuant(40), dur=R.uniform(1, 2.5), tipo=tec, v=R.uniform(.4, .7)))
    elif ins == 'piano': piano.append(dict(t=t0, m=cuant(R.choice([33, 40, 45])), v=.6, dur=.4, tipo=tec))
    elif ins == 'gong': gong.append(dict(t=t0, tipo='roce', dur=3.5, v=.4))
# la montaña respira: la garganta larga (largo 2) sin palabras, aprende 0: sólo el perfil del terreno resonando
for t0, d, m in [(2.0, 4.5, 33), (9.0, 5.0, 28), (17.0, 6.0, 33)]:
    garganta.append(dict(t=t0, dur=d, nota=m, fonemas=['a'], v=.35, aprende=0, ronco=.3, voz='montana'))
# pájaros: picos y un carpintero, al fondo
for t0 in (4.2, 4.5, 11.0, 18.6, 18.8, 23.2): aves.append(dict(t=t0, tipo='pico', m=90, dur=.05, v=.5, voz=0))
aves.append(dict(t=13.0, tipo='carpintero', m=80, dur=1.4, v=.45, voz=1))
# la cancioncilla: el agua la canturrea (como el niño en la oscuridad), dos veces, la segunda más segura
def cancioncilla(t0, oct=0, v=.6, texto=('la', 'la', 'la', 'la', 'la')):
    t = t0
    for m, d, tx in zip(CANC, CANC_RIT, texto):
        vozagua.append(dict(t=round(t, 4), dur=round(d * 4 * S * .92, 4), texto=tx, nota=m + oct, modo='canto', voz=1, v=v)); t += d * 4 * S
    return t
cancioncilla(19.0, 0, .45, ('a', 'trás', 'a', 'trás', 'a')); cancioncilla(23.4, 0, .6, ('can', 'to', 'pa', 'ra', 'ce'))

# ═════════════ II · casa (Weather Report) ═════════════
# bajo sin trastes: ostinato que sale de la silueta (16 muestras del frente, en la retícula), con glisandos de dedo
SIL16 = [cuant(BASE + 2 + 22 * sil_f[int(i * 359 / 15)]) for i in range(16)]
bajo = []
def compas_bajo(t0, tr=0, var=0):
    for s in range(16):
        if s in (3, 7, 11) and var % 2 == 0: continue        # huecos: el aire del groove
        m = SIL16[s] + tr; acento = s in (0, 6, 10)
        bajo.append(dict(t=round(t0 + s * S, 5), dur=round(S * (2.6 if s in (0, 10) else .9), 4), m=m, v=1.0 if acento else .7, glis=(s == 10)))
# los cambios del círculo: la retícula transpuesta por su propio periodo (11) y por los grados (5, 9)
CAMBIOS = [0, 0, 5, 5, -2, -2, 9 - 11, 0]
for k in range(16): compas_bajo(b('II', k), CAMBIOS[k % 8], k)
# el tema (Zawinul + Shorter al unísono): la cancioncilla desarrollada por la retícula, frases de 2 compases con respuesta
def tema(t0, tr):
    t = t0; out = []
    seq = CANC + [paso(CANC[-1], 1), paso(CANC[-1], 2), CANC[2], CANC[1], paso(CANC[0], -1), CANC[0]]
    rit = [2, 1, 1, 3, 1, 1, 2, 1, 2, 3]              # en semicorcheas × 2
    for m, d in zip(seq, rit):
        out.append(dict(t=round(t, 5), dur=round(d * 2 * S * .9, 4), m=m + tr + 12, v=1.0 if d >= 2 else .82)); t += d * 2 * S
    return out
sinte, sax = [], []
for k in (0, 2, 4, 6):
    tt = tema(b('II', k, 2), CAMBIOS[k % 8]); sinte += tt; sax += [dict(n, m=n['m'] - 12, lengua=1) for n in tt]
# percusión: el groove de Birdland a la mexicana — ride a corcheas, rim en 3-3-2, berimbau, teponaztli, caja fantasma
def groove(t0, intenso, k):
    for s in range(0, 16, 2): bat(t0 + s * S, 'ride', .5 + .25 * (s % 4 == 0), .25)
    for s in (0, 3, 6): bat(t0 + s * S, 'kick', .85)
    if intenso: bat(t0 + 10 * S, 'kick', .7); bat(t0 + 13 * S, 'kick', .6)
    for s in (4, 12): bat(t0 + s * S, 'rim' if not intenso else 'snare', .7, .05)
    for s in (2, 7, 9, 14): bat(t0 + s * S, 'snare', .16, .05)
    for s, gr in ((0, 0), (3, 1), (6, 0), (10, 1), (13, 0)): web('teponaztli', t0 + s * S, 'teponaztli', 64 + 3 * gr, .45, .3, -.25)
    for s, vel, gr in ((0, .3, 0), (2, .3, 0), (4, .85, 0), (6, .85, 1), (10, .7, 0), (12, .85, 1)): web('berimbau', t0 + s * S, 'berimbau', 52 + gr, vel, .3, .2)
for k in range(16): groove(b('II', k), k >= 8, k)

# ── el coro de vocoders: cuatro versos con su armonía en la retícula (cuatro acordes por verso) ──
VERSO1 = ['can to pa ra ha cer un ce rro', 'ce rro pa ra que ha ya a trás', 'lo que ta pa la tras pues ta', 'un pá ja ro lo can ta rá']
CORO = ['ca da cur va es u na cer ca', 'ca da co ta un es ca lón', 'el vien to no tie ne ca sa', 'pa sa y no de ja su nom bre']
FINAL = ['ma pa no te rri to rio', 'te rri to rio que se va', 'dos mil ce rros que no e xis ten', 'y un pá ja ro que los o ye']
TONICA = {'can': 0, 'ce': 0, 'ha': 1, 'trás': 1, 'ta': 0, 'pues': 1, 'pá': 1, 'rá': 1, 'cur': 1, 'cer': 1, 'co': 1, 'lón': 1, 'vien': 1, 'tie': 1, 'ca': 0,
          'pa': 0, 'de': 1, 'nom': 1, 'ma': 1, 'to': 0, 'va': 1, 'mil': 1, 'xis': 1, 'o': 0}
# el contorno de la soprano en ESCALONES de la retícula (no en semitonos: la retícula es dispareja, de 1 a 5 semitonos por paso)
CONTORNO = [[0, 0, 1, 2, 1, 2, 3, 1, 0], [1, 1, 2, 3, 2, 1, 0, -1, 0], [2, 2, 3, 4, 3, 2, 3, 1, 1], [0, 1, 2, 3, 2, 1, 0, -1, -2]]
def acorde(raiz):                                         # cuatro grados seguidos de la retícula desde la raíz: voicing de cuartas
    k = idx(raiz); return [RET[k + j] for j in (0, 2, 3, 5)]
def coral(versos, t0, compases_por_verso=2, raices=(0, 5, -2, 9)):
    voces = {v: [] for v in 'SATB'}; acs = []
    L = compases_por_verso * 16
    for vi, verso in enumerate(versos):
        sil = verso.split(); n = len(sil); tv = t0 + vi * L * S
        # ritmo: sílabas en semicorcheas sincopadas (3 3 2 …), la última se queda
        pat = [2, 1, 2, 1, 2, 2, 1, 2, 1][:n - 1]; pat = pat + [L - sum(pat)]
        s = 0
        for j, (sy, d) in enumerate(zip(sil, pat)):
            ch = raices[(j * 4) // n] if True else 0
            raiz = cuant(BASE + 12 + ch + (vi % 2) * 5)
            ac = acorde(raiz)
            if j == 0 or (j * 4) // n != ((j - 1) * 4) // n: acs.append(dict(t=round(tv + s * S, 5), raiz=raiz, tonos=ac))
            acento = TONICA.get(sy.replace('á', 'a').replace('ó', 'o'), 0) or TONICA.get(sy, 0)
            cont = CONTORNO[vi % 4]; sop = RET[idx(61) + cont[min(j, len(cont) - 1)] + (1 if acento and cont[min(j, len(cont) - 1)] < 3 else 0)]
            alt = max([x for x in RET if x < sop - 1 and x in ac + [y + PERIODO for y in ac] + [y - PERIODO for y in ac]] or [paso(sop, -2)])
            ten = paso(alt, -2); baj = raiz
            for v, m in zip('SATB', (sop, alt, ten, baj)):
                voces[v].append(dict(t=round(tv + s * S, 5), dur=round(d * S * (.9 if d < 6 else .97), 4), texto=sy, nota=m, acento=acento))
            s += d
    return voces, acs
C1, A1 = coral(VERSO1, b('II', 8))
C2, A2 = coral(CORO, b('III', 0))
C3, A3 = coral(FINAL, b('V', 0), raices=(0, -2, 5, 0))
COROS = [('II', C1), ('III', C2), ('V', C3)]
sabina = []
for nom, C in COROS:
    for vi in range(4):
        sil = [e for e in C['S'] if C['S'].index(e) >= 0][0:0]
    sabina.append(dict(eventos=[dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota']) for e in C['S']], nivel=.85, pan=0, capa='soprano'))
    if nom == 'V': sabina.append(dict(eventos=[dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota'] - 12) for e in C['S']], nivel=.6, pan=0, capa='baja'))
for nom, C in COROS:
    for e in C['S']: aves.append(dict(t=e['t'], tipo='canto', notas=[[0, e['nota'] + 12, e['dur'] * .95]], dur=e['dur'] + .02, v=.5, voz=0, coro=1))
    for e in C['A']: vozagua.append(dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota'], modo='canto', voz=1, v=.7))
    for e in C['T']: garganta.append(dict(t=e['t'], dur=e['dur'], nota=e['nota'], texto=e['texto'], v=.6, aprende=.9 if nom != 'II' else .75, voz='coro'))

# ═════════════ III · coro (hyperpop, Nobuto) ═════════════
sub = []
for k in range(8):
    t0 = b('III', k)
    for s in (0, 3, 6, 10, 13 if k % 2 else 11): bat(t0 + s * S, 'kick', 1.0)
    for s in (4, 12): bat(t0 + s * S, 'clap', .9, 0, 'bateria-frito', 'bateria-frito')
    for s in range(16):
        if k % 4 == 3 and s >= 12:
            for j in range(3): bat(t0 + s * S + j * S / 3, 'hat', .45 + .15 * j, .2)
        else: bat(t0 + s * S, 'hat', .6 if s % 2 == 0 else .35, .2)
    if k in (0, 4): web('bateria-frito', t0, 'bateria-frito', 60, 1.0, .3, 0, pieza='spray')
    compas_bajo(t0, CAMBIOS[k % 8], 1)
for a in A2 + A3:
    sub.append(dict(t=a['t'], midi=a['raiz'] if a['raiz'] < 40 else a['raiz'] - 11, vel=.9, dur=round(8 * S * .97, 4)))
# las tijeras de Nobuto: en la mezcla, la pista se corta y se pega a sí misma (repite, al revés, salta a otro momento, sube)
tijeras = []
for k in range(8):
    if k % 2 == 1: tijeras.append(dict(t=round(b('III', k, 12), 4), dur=round(4 * S, 4), tipo=R.choice(['repite', 'reversa', 'sube'])))
for k in (1, 3, 6): tijeras.append(dict(t=round(b('III', k, 8), 4), dur=round(2 * S, 4), tipo='salto', desde=round(R.uniform(2, T_I - 2), 3)))   # un pedazo del punto gris dentro del coro

# ═════════════ IV · abrir el círculo: los solos ═════════════
def linea_solo(rng, t0, largo16, rango, inicio, raiz_de):
    """improvisación en la retícula: notas en el pulso corrido (acentos cada 3), células que bajan por la retícula hacia un
    tono del acorde, saltos de periodo (11, la «octava» del terreno), tresillos; silencios a contratiempo"""
    out = []; s = rng.choice([1, 3]); m = inicio
    while s < largo16 - 1:
        lf = rng.choice([5, 7, 9, 6]); k = 0; fin = min(largo16 - .5, s + lf)
        while s < fin:
            ac = acorde(raiz_de(t0 + s * S)); acento = (k % 3 == 0)
            if acento: m = cerca_ac(ac, m + rng.choice([-5, -2, 3, 5, 11, -11]), rango)
            else: m = paso(m, rng.choice([-1, -1, 1, 2, -2]))
            m = min(max(m, rango[0]), rango[1])
            if rng.random() < .13 and s + 2 <= fin:
                for j in range(3): out.append(dict(t=round(t0 + (s + j * 2 / 3) * S, 5), dur=round(2 / 3 * S, 5), m=paso(m, j - 1), acento=j == 0)); k += 1
                s += 2
            else: out.append(dict(t=round(t0 + s * S, 5), dur=round(S, 5), m=m, acento=acento)); s += 1; k += 1
        out[-1]['dur'] = round(rng.choice([1.5, 2, 3]) * S, 5); out[-1]['acento'] = True
        s = math.floor(s) + rng.choice([1, 2, 3]); s += (s % 2 == 0) * (rng.random() < .6)
    return out
def cerca_ac(ac, obj, rango):
    cand = [x + PERIODO * q for x in ac for q in range(-4, 5)]; cand = [x for x in cand if rango[0] <= x <= rango[1]]
    return min(cand, key=lambda x: abs(x - obj)) if cand else obj
def raiz_de(t): k = int((t - INI['II']) / BAR) % 8; return cuant(BASE + 12 + CAMBIOS[k])
rng = random.Random(SEMILLA + 1)
SCAT = ['du', 'ba', 'di', 'da', 'ya', 'u', 'bo', 'pa', 'dun']
SILABAS_LETRA = ' '.join(VERSO1 + CORO).split()
def a_silabas(notas, fuente, rng):
    return [dict(n, texto=(fuente[i % len(fuente)] if fuente else rng.choice(SCAT))) for i, n in enumerate(notas)]
# a) Siringua de tres gargantas (8 compases): la montaña canta las sílabas de la letra; el agua dobla los acentos; el pájaro contesta
sol1 = a_silabas(linea_solo(rng, b('IV', 0), 8 * 16, (48, 70), 59, raiz_de), SILABAS_LETRA, rng)
for n in sol1:
    garganta.append(dict(t=n['t'], dur=n['dur'] * .95, nota=n['m'], nota2=(n['m'] - 5 if n['dur'] >= 2 * S else None), texto=n['texto'], v=.85 if n['acento'] else .65, aprende=.95, voz='solo'))
    if n['acento']: vozagua.append(dict(t=n['t'], dur=n['dur'] * .9, texto=n['texto'], nota=n['m'] + 11, modo='canto', voz=1, v=.55))
fines = [n for i, n in enumerate(sol1[:-1]) if sol1[i + 1]['t'] - (n['t'] + n['dur']) > 1.5 * S]
for n in fines:
    i = sol1.index(n); cita = sol1[max(0, i - 3):i + 1]
    siringa.append(dict(t=round(n['t'] + n['dur'] + .03, 4), tipo='canto', notas=[[round((c['t'] - cita[0]['t']) * .7, 4), c['m'] + 22, round(c['dur'] * .6, 4)] for c in cita], dur=round((cita[-1]['t'] - cita[0]['t']) * .7 + .2, 4), v=.5, voz=len(siringa) % 2))
# b) el vocoder improvisa (6 compases): Sabina canta sílabas de scat en la línea; la portadora es el sinte que toca la misma línea
sol2 = a_silabas(linea_solo(rng, b('IV', 8), 6 * 16, (60, 84), 70, raiz_de), None, rng)
sabina.append(dict(eventos=[dict(t=n['t'], dur=max(.09, n['dur']), texto=n['texto'], nota=n['m'] - 12 if n['m'] > 76 else n['m']) for n in sol2], nivel=.85, pan=0, capa='scat'))
vocsolo = [dict(t=n['t'], dur=n['dur'], m=n['m'], v=1.0 if n['acento'] else .8) for n in sol2]
# c) cambios de 1 compás (sax, Siringua, vocoder, …) y el recorte final de Nobuto (las tijeras cortan cada medio compás)
for k in range(6):
    t0 = b('IV', 14 + k); quien = ['sax', 'garganta', 'voc'][k % 3]
    lin = linea_solo(rng, t0, 16, (52, 74) if quien == 'sax' else (50, 72) if quien == 'garganta' else (62, 84), 62, raiz_de)
    if quien == 'sax': sax += [dict(n, lengua=1 if n['acento'] else 0, v=1.0 if n['acento'] else .8) for n in lin]
    elif quien == 'garganta':
        for n in a_silabas(lin, SILABAS_LETRA[k * 5:], rng): garganta.append(dict(t=n['t'], dur=n['dur'] * .95, nota=n['m'], texto=n['texto'], v=.8, aprende=.95, voz='solo'))
    else:
        l2 = a_silabas(lin, None, rng); vocsolo += [dict(t=n['t'], dur=n['dur'], m=n['m'], v=1.0 if n['acento'] else .8) for n in l2]
        sabina.append(dict(eventos=[dict(t=n['t'], dur=max(.09, n['dur']), texto=n['texto'], nota=n['m'] - 12 if n['m'] > 76 else n['m']) for n in l2], nivel=.85, pan=0, capa='scat'))
    if k >= 4: tijeras.append(dict(t=round(t0 + 8 * S, 4), dur=round(8 * S, 4), tipo='repite' if k == 4 else 'reversa'))
for k in range(20):                                      # comping de los solos: bajo y groove ligero; marimba suelta acordes
    t0 = b('IV', k); compas_bajo(t0, CAMBIOS[k % 8], k + 1); groove(t0, k >= 14, k)
    for s in rng.sample([2, 5, 7, 9, 11, 14], 2):
        for m in acorde(raiz_de(t0 + s * S))[1:]: web('marimba', t0 + s * S, 'marimba', m + 22 if m + 22 < 76 else m + 11, .42, S * 1.5, .3)
# escena de pájaros (el Scenopoietes: corta hojas y las voltea para que se vea su cara pálida, y canta encima)
for k in (4, 10, 17):
    t0 = b('IV', k, 2)
    for j in range(6): aves.append(dict(t=round(t0 + j * .13, 3), tipo='pico', m=88, dur=.04, v=.55, voz=j % 2))
    aves.append(dict(t=round(t0 + .9, 3), tipo='trino', m=cuant(88), m2=cuant(92), dur=.6, rate=22, v=.5, voz=0))
    aves.append(dict(t=round(t0 + 1.6, 3), tipo='silbido', m=cuant(93), m2=cuant(86), dur=.35, v=.5, voz=1))

# ═════════════ V · liso ═════════════
# la retícula se disuelve: el viento sube; bajo y sinte se deslizan (glisandos largos); el coro final encima
for k in range(8):
    t0 = b('V', k)
    bajo.append(dict(t=round(t0, 5), dur=round(BAR * .95, 4), m=cuant(BASE + 12 + [0, -2, 5, 0, 9 - 11, 5, -2, 0][k]), v=.9, glis=True, liso=True))
    for s in (0, 6, 10): bat(t0 + s * S, 'kick', .9)
    for s in range(0, 16, 2): bat(t0 + s * S, 'hat', .4, .2)
    bat(t0 + 12 * S, 'clap', .8, 0, 'bateria-frito', 'bateria-frito')
gong.append(dict(t=round(b('V', 0), 3), tipo='tamtam', m=28, v=.85, dureza=.7))
for k in range(0, 8, 2): chelo.append(dict(t=round(b('V', k), 3), m=cuant(40), v=.6, dur=BAR * 1.9, tipo='ponticello'))
# la tormenta: sinte en glisandos que atraviesan la retícula
for k in range(8): sinte.append(dict(t=round(b('V', k, 4), 5), dur=round(10 * S, 4), m=cuant(76 + [0, 5, -2, 9, 0, 11, 5, 0][k]), v=.7, glis=True))

# ═════════════ VI · coda ═════════════
tf = cancioncilla(INI['VI'] + 2.0, 0, .55, ('lo', 'que', 'ta', 'pa', 'la'))
garganta.append(dict(t=round(INI['VI'] + 8.0, 3), dur=2.4, nota=33, texto='a', fonemas=['a', 't', 'r', 'a', 's'], v=.5, aprende=.8, voz='montana', largo=2))
for j in range(4): aves.append(dict(t=round(INI['VI'] + 10 + j * 1.3, 3), tipo='canto', notas=[[i * .22, CANC[i] + 22, .18] for i in range(len(CANC))], dur=1.0, v=.4, voz=j % 2))
gong.append(dict(t=round(INI['VI'] + .2, 3), tipo='cruce', m=40, v=.5, abre=3))

# ── el viento: todo el tiempo, lee los perfiles; liso en I, V y VI; estriado en II–IV ──
VIENTO = dict(vel=[[0, 5], [T_I * .6, 11], [INI['II'], 6], [INI['III'], 4], [INI['IV'], 5], [INI['V'], 9], [INI['V'] + 8 * BAR * .7, 19], [INI['VI'], 8], [DUR, 4]],
              estria=[[0, 0], [INI['II'] - 2, 0], [INI['II'] + 2, .9], [INI['V'], .9], [INI['V'] + 3 * BAR, 0], [DUR, 0]], escala=GRADOS, periodo=PERIODO, base=BASE)
agua.append(dict(t=0.0, tipo='burbujeo', dur=T_I, v=.4)); agua.append(dict(t=round(INI['VI'], 3), tipo='ola', dur=12, v=.5))

partitura = dict(titulo='Lo que tapa la traspuesta', semilla=SEMILLA, terreno='traspuesta 420048 (cordillera, 2750 m de relieve)', bpm=BPM, semicorchea=S,
                 secciones={k: [round(INI[k], 4), round([INI[x] for x in ['II', 'III', 'IV', 'V', 'VI', 'fin']][['I', 'II', 'III', 'IV', 'V', 'VI'].index(k)], 4)] for k in ['I', 'II', 'III', 'IV', 'V', 'VI']},
                 duracion=round(DUR, 3), periodo=PERIODO, grados=GRADOS, base=BASE, reticula=RET[:24], cancioncilla=CANC, perfiles=PERFILES,
                 letra=dict(verso=VERSO1, coro=CORO, final=FINAL), web=ev, clarinete=clar, trombon=trombon, chelo=chelo, piano=piano, gong=gong, aves=aves, agua=agua,
                 garganta=garganta, vozagua=vozagua, siringa=siringa, sabina=sabina, coros={k: C for k, C in COROS}, acordes=dict(II=A1, III=A2, V=A3), sub=sub,
                 bajo=bajo, sinte=sinte, sax=sax, vocsolo=vocsolo, tijeras=tijeras, viento=VIENTO, tonica='E', escala=[0, 5, 9, 10], instrumentos='instrumentos-cb770f30d48e')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', round(DUR, 1), 's · periodo', PERIODO, 'grados', GRADOS, '· cancioncilla', CANC, CANC_RIT, '· retícula', RET[:14])
    print({k: len(v) for k, v in ev.items()}, '· garganta', len(garganta), '· vozagua', len(vozagua), '· sabina', sum(len(f['eventos']) for f in sabina), '· sax', len(sax), '· sinte', len(sinte), '· vocsolo', len(vocsolo), '· bajo', len(bajo), '· tijeras', len(tijeras))
