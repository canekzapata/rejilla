"""¿Por quién se toma la tierra? — partitura. Mulatu Astatke (jazz etíope) × Scelsi × dub techno, sobre el volcán 177 de Traspuesta
(«La Aguja del Zacatal»: estratovolcán que colapsa en herradura y renace con un cono interior) y «La geología de la moral» de Mil
mesetas (la tierra como cuerpo sin órganos; los estratos; la doble articulación; Challenger que hace bramar a la tierra).

LA FORMA ES LA VIDA DEL VOLCÁN. Traspuesta da el mismo volcán a cualquier edad; seis edades, seis estratos de la canción:
  1 levantamiento (joven, 4100 m) · 2 cono y erosión (disectado) · 3 colapso de flanco · 4 cono interior y cráter anidado ·
  5 caldera vieja · 6 cuello volcánico (1230 m: sólo queda la garganta).
EL MAGMA ES UNA NOTA (Scelsi): un bordón cuya altura sale del relieve, f = 55 Hz · 4100 m / relieve; mientras el volcán se gasta
el bordón sube unos cents, y cuando sólo queda el cuello salta a 183 Hz. Todo se afina sobre él: cada edad tiene su qenet etíope
(tizita menor, bati, anchihoye, ambassel…) con raíz en el bordón (microtonal: sigue al volcán).
LA DOBLE ARTICULACIÓN: primero la sedimentación —dos unidades (arenisca y esquisto: un acorde claro y uno oscuro) que se alternan
en orden estadístico (Markov)—; luego el plegamiento: la secuencia se dobla sobre sí misma (palíndromo) y queda un riff estable.
Dub techno: los acordes son estratos (cada uno con su eco), el 4/4 a 120 debajo del 12/8 etíope (tres contra dos).
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np

SEMILLA = 177
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__)); G = 360
CORTES = json.load(open(os.path.join(AQUI, 'terreno', 'cortes-177.json'), encoding='utf-8'))
m_de = lambda f: 69 + 12 * math.log2(f / 440)
BPM = 120; B = 60 / BPM; BAR = 4 * B; T3 = BAR / 12           # tiempo de 4/4 y la corchea de tresillo del 12/8

# ── las edades: cuándo empieza cada una (en compases de 2 s) ──
EDADES = [(0, 'LEVANTAMIENTO', 0.03), (12, 'CONO · EROSIÓN', 0.5), (36, 'COLAPSO DE FLANCO', 0.62), (45, 'CONO INTERIOR · CRÁTER ANIDADO', 0.62),
          (72, 'CALDERA VIEJA', 0.8), (89, 'CUELLO', 0.97)]
FIN_BAR = 103; DUR = FIN_BAR * BAR + 6
REL = {c['edad']: c['relieve'] for c in CORTES}
def bordon(edad): return 55.0 * 4100 / REL[edad]               # el magma
QENET = {0: [0, 2, 3, 7, 8], 1: [0, 2, 3, 7, 8], 2: [0, 1, 5, 6, 9], 3: [0, 1, 5, 7, 8], 4: [0, 3, 5, 7, 10], 5: [0, 4, 7, 10, 14]}   # tizita menor, anchihoye, ambassel, bati menor; el cuello: armónicos
NOMBRE_QENET = {0: 'tizita menor', 1: 'tizita menor', 2: 'anchihoye', 3: 'ambassel', 4: 'bati menor', 5: 'armónicos del bordón'}
def edad_en(b):
    k = 0
    for i, (b0, _, _) in enumerate(EDADES):
        if b >= b0: k = i
    return k
def raiz(k): return m_de(bordon(EDADES[k][2]))                # midi (con microtonos) del bordón de esa edad
def grado(k, g, oct_):
    q = QENET[k]; o, r = divmod(g, len(q)); return raiz(k) + 12 * (oct_ + o) + q[r]
def t_(b, x=0.0): return b * BAR + x

ev = {k: [] for k in ['vibrafono', 'krar', 'masenqo', 'conga', 'organo', 'bateria', 'bateria-frito']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr808', stem='bateria'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)

# ═════════ el magma (Scelsi): una nota que se pudre por dentro, de principio a fin ═════════
magma = []
for i, (b0, nom, e) in enumerate(EDADES):
    b1 = EDADES[i + 1][0] if i + 1 < len(EDADES) else FIN_BAR
    magma.append(dict(t=round(t_(b0), 3), dur=round(t_(b1) - t_(b0), 3), f=round(bordon(e), 4), m=round(m_de(bordon(e)), 3), edad=e, nombre=nom))

# ═════════ la sedimentación: dos unidades en orden estadístico (Markov) y luego plegadas ═════════
# A = arenisca (acorde claro, abierto, arriba), B = esquisto (oscuro, cerrado, abajo); quedarse en la misma capa: 0.7
sedimento = ['A']
for _ in range(95): sedimento.append(sedimento[-1] if R.random() < .7 else ('B' if sedimento[-1] == 'A' else 'A'))
pliegue = sedimento[:8] + sedimento[:8][::-1]                 # la segunda articulación: la secuencia doblada sobre sí misma
def acorde(k, capa):
    if capa == 'A': return [grado(k, g, 1) for g in (0, 2, 4, 6)]          # abierto: cada dos grados, octava 3
    return [grado(k, g, 0) for g in (0, 1, 2, 3)]                           # cerrado: grados seguidos, octava 2 (cluster oscuro)
estratos = []                                                  # los acordes del dub (cada uno con su eco en la mezcla)
for b in range(4, FIN_BAR - 6):
    k = edad_en(b)
    if k == 2: continue                                        # en el colapso no hay estratos: se caen
    seq = sedimento if k in (0,) else pliegue                  # primero la sedimentación; desde la erosión, plegado
    for x in (0.0, 1.5 * B) if k in (1, 3) else (0.0,):
        capa = seq[(2 * b + (x > 0)) % len(seq)]
        estratos.append(dict(t=round(t_(b, x + .5 * B), 4), capa=capa, notas=[round(n, 3) for n in acorde(k, capa)], v=.7 if capa == 'A' else .8, edad=k))

# ═════════ el groove (12/8 etíope sobre 4/4 de dub techno) ═════════
def groove(b, k, lleno):
    bat(t_(b), 'kick', .9)
    for q in (1, 2, 3): bat(t_(b, q * B), 'kick', .8 if lleno else .0001)
    for q in (1, 3): bat(t_(b, q * B), 'rim', .45 if not lleno else .6, -.1)
    for s in range(12):                                         # el 12/8: shaker de tresillos con acento en 1 4 7 10 y fantasma
        bat(t_(b, s * T3), 'hat', .38 + .22 * (s % 3 == 0), .3)
    for s, gr, v in ((0, 0, .8), (3, 1, .5), (5, 0, .6), (6, 1, .75), (9, 0, .5), (11, 1, .6)):   # conga (kebero): tumba y quinto
        web('conga', t_(b, s * T3), 'meleeviewer-13-conga', 60 + 5 * gr, v, .2, -.25)
    if lleno and b % 2: bat(t_(b, 3.5 * B), 'openhat', .35, .2)
bajo = []
RIFF_BAJO = [(0, 0, 1.5), (1.5, 2, .5), (2, 4, 1.0), (3, 3, .5), (3.5, 1, .5)]  # (tiempo, grado, dur en tiempos)
def bajo_compas(b, k):
    for x, g, d in RIFF_BAJO: bajo.append(dict(t=round(t_(b, x * B), 4), dur=round(d * B * .9, 4), m=round(grado(k, g, 1) - 12, 3), v=.9 if x == 0 else .7))
krar = []
for b in range(12, 36):
    k = edad_en(b); groove(b, k, b >= 16); bajo_compas(b, k)
    for s in range(12):                                         # krar: ostinato de tresillos, el pliegue elige el grado
        g = [0, 2, 4, 2, 1, 3][s % 6] + (1 if pliegue[(b + s) % len(pliegue)] == 'B' else 0)
        web('krar', t_(b, s * T3), 'meleeviewer-3-krar', grado(k, g, 2), .55 + .2 * (s % 3 == 0), T3 * 1.6, .35)
# los metales (Mulatu): riff de pregunta y respuesta en el qenet, sax + trompeta con sordina + trombón a la octava
metales = []
FRASE = [(0, 4), (.5, 3), (1, 2), (1.5, 0), (2.5, 1), (3, 2)]
def riff(b, k, transp=0):
    for x, g in FRASE:
        for ins, oct_ in (('sax', 2), ('trompeta', 3), ('trombon', 1)):
            metales.append(dict(t=round(t_(b, x * B), 4), dur=round(B * .45, 4), m=round(grado(k, g + transp, oct_), 3), ins=ins, v=.85))
for b in range(20, 36, 4): riff(b, edad_en(b)); riff(b + 2, edad_en(b), 2)

# ═════════ el colapso: la tierra brama ═════════
COL0, COL1 = EDADES[2][0], EDADES[3][0]
colapso = dict(t0=t_(COL0), t1=t_(COL1))
for b in range(COL0, COL1):                                     # redobles de toms que caen, sin pulso fijo
    for j in range(R.randint(3, 7)): bat(t_(b, R.uniform(0, BAR)), R.choice(['tomlo', 'tommid', 'tomlo', 'kick']), R.uniform(.5, .95), R.uniform(-.6, .6))
tamtam = [dict(t=round(t_(COL0), 3), tipo='tamtam', m=round(raiz(2) - 12, 3), v=.95, dureza=.8), dict(t=round(t_(COL0 + 4), 3), tipo='roce', dur=10, v=.6),
          dict(t=round(t_(EDADES[5][0]) - 1, 3), tipo='arco', m=round(raiz(5), 3), dur=14, v=.4)]
for nota in acorde(2, 'B'): metales.append(dict(t=round(t_(COL0 + 1), 4), dur=round(BAR * 3, 4), m=round(nota + 12, 3), ins='trombon', v=.7, growl=1))

# ═════════ cono interior y cráter anidado: renace ═════════
for b in range(COL1, EDADES[4][0]):
    k = edad_en(b); groove(b, k, True); bajo_compas(b, k)
    # cráter anidado: un ritmo dentro de otro — la conga en 3 dentro del 12/8, el krar en 4 dentro de cada tresillo
    for s in range(0, 12, 3): web('krar', t_(b, s * T3), 'meleeviewer-3-krar', grado(k, [0, 3, 1, 4][(s // 3 + b) % 4], 2), .6, T3 * 2.5, .35)
    if b % 2 == 0: web('bateria-frito', t_(b, 2 * B), 'bateria-frito', 60, .8, .3, 0, pieza='clap')
for b in range(COL1 + 4, EDADES[4][0] - 4, 4): riff(b, edad_en(b), 1)
# el vibráfono de Mulatu: solo en ambassel, frases que empiezan a contratiempo y caen al bordón
vibra = []; rng = random.Random(SEMILLA + 1)
b = COL1 + 13
while b < EDADES[4][0] - 1:
    k = edad_en(b); t = t_(b, rng.choice([.5, 1, 1.5]) * B); g = rng.randint(4, 8)
    for j in range(rng.randint(5, 11)):
        g += rng.choice([-1, -1, 1, -2, 2]); g = max(2, min(10, g))
        d = rng.choice([T3, T3, 2 * T3, B / 2])
        web('vibrafono', t, 'vibrafono', grado(k, g, 3), .62 + .25 * (j == 0), d * 1.6, .1); t += d
    web('vibrafono', t, 'vibrafono', grado(k, 0, 3), .8, B * 2, .1)
    b += 2

# ═════════ caldera vieja: el dub se deshace; masenqo y washint ═════════
for b in range(EDADES[4][0], EDADES[5][0]):
    k = edad_en(b)
    if b < EDADES[4][0] + 8: bat(t_(b), 'kick', .5); bajo_compas(b, k) if b % 2 == 0 else None
    for s in (0, 7): web('conga', t_(b, s * T3), 'meleeviewer-13-conga', 60, .35, .2, -.3)
for j, (b, gs) in enumerate([(EDADES[4][0] + 2, [0, 3, 2, 1, 0]), (EDADES[4][0] + 6, [4, 3, 1, 0]), (EDADES[4][0] + 10, [2, 3, 4, 3, 1, 0])]):
    for i, g in enumerate(gs): web('masenqo', t_(b, i * 1.5 * B), 'meleeviewer-3-masenqo', grado(4, g, 2), .7, 1.5 * B * .95, -.2)
washint = [dict(t=round(t_(EDADES[4][0] + 4 + 4 * j, i * B * 1.2), 3), dur=round(B * 1.1, 3), m=round(grado(4, g, 3), 3), v=.75) for j, gs in enumerate([[4, 3, 2], [3, 1, 0, 1]]) for i, g in enumerate(gs)]
lagos = [dict(t=round(t_(b, R.uniform(0, BAR)), 3), tipo='gota', m=round(grado(4, R.randint(0, 9), 4), 3), v=.35) for b in range(EDADES[4][0], EDADES[5][0]) for _ in range(3)]   # los tres lagos de la caldera

# ═════════ el órgano (wah) que sostiene los estratos desde la erosión ═════════
for b in range(12, EDADES[4][0], 2):
    k = edad_en(b)
    if k == 2: continue
    for n in acorde(k, 'B')[1:]: web('organo', t_(b), 'receta-organo-roto', n + 12, .5, BAR * 1.9, -.3)

# ═════════ la letra ═════════
VERSO = ['ca pa so bre ca pa', 'a re na y pi za rra', 'lo que se que da se do bla', 'y lo do bla do se vuel ve mon te']
PUENTE = ['se me ca e el flan co', 'me que da la bo ca a bier ta']
ESTRIBILLO = ['la tie rra no se to ma', 'por na die', 'se to ma por ca pas', 'se to ma por fue go']
FINAL = ['ya no hay mon ta ña', 'só lo la gar gan ta', 'só lo la gar gan ta can ta']
def coral(versos, b0, compases_por_verso, k_de, ritmo=None):
    voces = {v: [] for v in 'SATB'}
    for vi, verso in enumerate(versos):
        sil = verso.split(); t0 = t_(b0 + vi * compases_por_verso); L = compases_por_verso * 12   # en tresillos
        pat = (ritmo or [2, 1, 2, 1, 3, 1, 2, 1, 2, 2])[:len(sil) - 1]; pat += [max(3, L - sum(pat) - 1)]
        s = 0
        for j, (sy, d) in enumerate(zip(sil, pat)):
            k = k_de(b0 + vi * compases_por_verso)
            sop = grado(k, [4, 5, 4, 3, 4, 6, 5, 4, 3, 2, 1, 0][j % 12] + (1 if vi == 1 else 0), 3)
            for v, n in zip('SATB', (sop, sop - [3, 4, 5][j % 3], sop - 7 - (j % 2), raiz(k) + 24)):
                voces[v].append(dict(t=round(t0 + s * T3, 4), dur=round(d * T3 * (.92 if j < len(sil) - 1 else 1.0), 4), texto=sy, nota=round(n, 3)))
            s += d
    return voces
C_VERSO = coral(VERSO, 24, 2, edad_en)
C_ESTRIB = coral(ESTRIBILLO, COL1 + 4, 2, edad_en, ritmo=[1, 2, 1, 2, 2, 1, 2])
C_ESTRIB2 = coral(ESTRIBILLO, COL1 + 20, 2, edad_en, ritmo=[1, 2, 1, 2, 2, 1, 2])
# la garganta de volcán: brama en el colapso (el puente, ronca, sin afinar casi), canta el tenor de los coros y el final sola
garganta = []
for vi, verso in enumerate(PUENTE):
    for j, sy in enumerate(verso.split()):
        garganta.append(dict(t=round(t_(COL0 + 2 + 3 * vi, j * 2 * T3), 4), dur=round(2 * T3 * .95, 4), nota=round(raiz(2) + 12 + R.uniform(-1, 1), 3), texto=sy, v=.9, aprende=.7, ronco=.9))
for C in (C_VERSO, C_ESTRIB, C_ESTRIB2):
    for e in C['T']: garganta.append(dict(t=e['t'], dur=e['dur'], nota=e['nota'] - 12, texto=e['texto'], v=.6, aprende=.85, ronco=0))
C_FINAL = coral(FINAL, EDADES[5][0] + 2, 3, lambda b: 5, ritmo=[2, 2, 2, 2, 3, 2, 2, 2])
for e in C_FINAL['S']: garganta.append(dict(t=e['t'], dur=e['dur'], nota=round(e['nota'] - 24, 3), texto=e['texto'], v=.75, aprende=.95, ronco=.1, solo=1))
for b in range(0, 12, 3): garganta.append(dict(t=round(t_(b, .3), 3), dur=round(BAR * 2.4, 3), nota=round(raiz(0) + 12, 3), fonemas=['a'], v=.35, aprende=0, ronco=.4))   # el volcán joven respira
sabina = [dict(eventos=[dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota']) for e in C['S']], nivel=.85, pan=0, capa='soprano') for C in (C_VERSO, C_ESTRIB, C_ESTRIB2)]
# los perfiles de la garganta: el corte del volcán a cada edad, a su hora (con una edad intermedia para que el tubo se deforme)
perfiles = [[round(t_(b0), 3), next(c['perfil'] for c in CORTES if c['edad'] == e)] for b0, _, e in EDADES]
perfiles.insert(1, [round(t_(6), 3), next(c['perfil'] for c in CORTES if c['edad'] == 0.25)])
caldera = [[0, 0], [t_(COL0), 0], [t_(COL0) + 1.5, 1], [t_(EDADES[4][0]), .8], [t_(EDADES[5][0]), .2], [DUR, 0]]
brama = [[0, 0], [t_(COL0), 0], [t_(COL0) + .5, 1], [t_(COL1), .5], [t_(COL1) + 6, .05], [DUR, 0]]
# la caldera como resonador de Helmholtz: f = c/2π·√(A/(V·L)) con el volumen y la brecha del corte a los 0.62; sube por octavas a 20–40 Hz
c0 = np.array(next(c['perfil'] for c in CORTES if c['edad'] == 0.62)) * 4100; borde = c0[40:85].max(); fondo = c0[50:75]
dx = 27000 / 120                                                 # 27 km de hoja en 120 muestras del corte
V = float(np.sum(np.maximum(0, borde - fondo)) * dx) * 2000      # ×2 km de ancho
A = float((borde - fondo.min()) * 1500); Lb = 2000.0             # la brecha: 1.5 km de ancho, 2 km de largo
fH_real = 343 / (2 * math.pi) * math.sqrt(A / (V * Lb)); fH = fH_real
while fH < 20: fH *= 2

partitura = dict(titulo='¿Por quién se toma la tierra?', semilla=SEMILLA, terreno='traspuesta 177 (estratovolcán que colapsa y renace) a seis edades', bpm=BPM, compas=BAR, tresillo=T3,
                 edades=[dict(bar=b0, t=round(t_(b0), 3), nombre=n, edad=e, bordon_hz=round(bordon(e), 3), qenet=NOMBRE_QENET[i], escala=QENET[i]) for i, (b0, n, e) in enumerate(EDADES)],
                 duracion=round(DUR, 3), fin=round(t_(FIN_BAR), 3), magma=magma, sedimento=''.join(sedimento), pliegue=''.join(pliegue), estratos=estratos, web=ev, bajo=bajo, metales=metales,
                 washint=washint, lagos=lagos, tamtam=tamtam, garganta=garganta, sabina=sabina, coros=dict(verso=C_VERSO, estribillo=C_ESTRIB, estribillo2=C_ESTRIB2, final=C_FINAL),
                 perfiles=perfiles, caldera=caldera, brama=brama, helmholtz=dict(V_m3=round(V), A_m2=round(A), L_m=Lb, f_real_hz=fH_real, f_hz=round(fH, 3)), colapso=colapso,
                 letra=dict(verso=VERSO, puente=PUENTE, estribillo=ESTRIBILLO, final=FINAL), instrumentos='instrumentos-ae827aaa3b6e')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', round(DUR, 1), 's · bordón por edad', [round(bordon(e), 2) for _, _, e in EDADES], 'Hz · Helmholtz real', f'{fH_real:.5f}', 'Hz → ', round(fH, 2), 'Hz')
    print('sedimento', ''.join(sedimento[:32]), '· pliegue', ''.join(pliegue))
    print({k: len(v) for k, v in ev.items()}, '· estratos', len(estratos), '· metales', len(metales), '· bajo', len(bajo), '· garganta', len(garganta), '· sabina', sum(len(s['eventos']) for s in sabina))
