"""El río no tiene tronco — partitura. Alice Coltrane × Steve Reich × hyperpop acuático, y Scelsi al llegar al mar. Sobre el delta
412601 de Traspuesta y la introducción de Mil mesetas (el rizoma: el árbol que se vuelve raíces por todas partes).

TODO ES UN MONOCORDIO. Cada río es una cuerda y su largo le da su altura: f = f0 · L_mayor / L. Los cinco brazos del delta son
las cinco cuerdas de un arpa (f0 = La2 = el brazo más largo; los demás a 10/9, 11/8, 20/11 y 21/10, más o menos: microtonos que
salen de los largos). El río principal es una cuerda larguísima (24 Hz): su melodía son SUS ARMÓNICOS, y baja por la serie
conforme el río baja (la altura del terreno a lo largo del canal elige el armónico). Los afluentes son cuerdas cortas.

UN SOLO RELOJ DE AGUA. El tiempo es la distancia a lo largo del agua:
  I   las fuentes (0–8 s lluvia; luego los afluentes): cada afluente es un ostinato de los armónicos de su cuerda, con su propio
      tempo (más pendiente, más rápido): se desfasan como en Reich. En su confluencia el ostinato cae al pulso del río y se disuelve
  II  el río (90 s a lo largo del canal; un paso del canal = un tiempo, ~108 bpm): la melodía del río con arpa, armonio, tambura,
      bajo y un tambor que hace de tabla; el coro de vocoders canta el verso
  III el delta (en el ápice el agua se frena 2.5×): la melodía se parte en cinco: un canon en las cinco cuerdas del arpa, cada brazo a
      su tempo (los cortos más rápido) y siguiendo las vueltas de su cauce; hyperpop acuático y el estribillo; la garganta de río
  IV  el mar (Scelsi): cada brazo, cuando su agua llega al mar, se desliza a la nota del mar y se queda ahí desviándose apenas; las
      desviaciones se cierran poco a poco (los batidos se hacen lentos) hasta el unísono; vocales que cambian, trombón con sordina
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np

SEMILLA = 412601
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__)); G = 360
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-412601.f32'), np.float32).reshape(G, G)
CANAL = json.load(open(os.path.join(AQUI, 'terreno', 'canal-412601.json')))
RED = json.load(open(os.path.join(AQUI, 'terreno', 'red-412601.json')))
DELTA = json.load(open(os.path.join(AQUI, 'terreno', 'delta.json')))
alt = lambda p: float(H[min(G - 1, round(p[1] * (G - 1))), min(G - 1, round(p[0] * (G - 1)))])
largo = lambda Q: float(np.sum(np.hypot(*np.diff(np.array(Q), axis=0).T)))
m_de = lambda f: 69 + 12 * math.log2(f / 440)

# ── las cuerdas ──
F0 = 110.0                                            # La2: el brazo más largo
BRAZOS = DELTA['brazos']; LMAX = max(b['largo'] for b in BRAZOS)
F_BRAZO = [F0 * LMAX / b['largo'] for b in BRAZOS]
L_RIO = largo(CANAL['rio']); F_RIO = F0 * LMAX / L_RIO      # ≈ 24 Hz
F_MAR = F0

# ── el reloj de agua ──
T_LLUVIA = 8.0; T_CANAL = 90.0; V = L_RIO / T_CANAL; FRENO = 2.5; VD = V / FRENO
PASO = T_CANAL / (len(CANAL['rio']) - 1)              # un paso del canal = un tiempo
S = PASO / 4                                           # la semicorchea del río
T_APICE = T_LLUVIA + T_CANAL
T_LLEGA = [T_APICE + b['largo'] / VD for b in BRAZOS]  # cuándo llega cada brazo al mar
T_MAR = min(T_LLEGA); T_FIN = max(T_LLEGA) + 30.0; DUR = T_FIN + 6
SEC = dict(I=(0, 30.0), II=(30.0, T_APICE), III=(T_APICE, T_MAR), IV=(T_MAR, T_FIN))

# ── el río: su perfil (de la fuente al ápice) y sus vueltas ──
rio = np.array(CANAL['rio'])[::-1]                    # el canal se dibuja del ápice tierra adentro: se voltea
perfil = np.array([alt(p) for p in rio]); perfil /= perfil.max()
dirs = np.unwrap(np.arctan2(np.diff(rio[:, 1]), np.diff(rio[:, 0]))); vuelta = np.concatenate([[0], np.diff(dirs)])
def armonico_rio(k): return int(round(4 + 14 * perfil[min(len(perfil) - 1, k)]))   # del 18 en la sierra al 4 en el ápice
def f_rio(n): return F_RIO * n

ev = {k: [] for k in ['marimba', 'teponaztli', 'bateria', 'bateria-frito']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def bat(t, pieza, vel, pan=0.0, kit='bateria-tr808', stem='bateria'): web(stem, t, kit, 60, vel, .2, pan, pieza=pieza)
arpa, armonio, tambura, bajo, agua, aves, tabla, trombon, gong, vozagua, garganta = [], [], [], [], [], [], [], [], [], [], []

# ═════════════ I · las fuentes (Reich) ═════════════
agua.append(dict(t=0.0, tipo='palo', dur=7.5, v=.6)); agua.append(dict(t=1.0, tipo='burbujeo', dur=12, v=.35))
ap = rio[-1]
afluentes = []
for i, Q in enumerate(RED['orientados']):
    Q = np.array(Q)
    if len(Q) < 48 or i in (13, 14): continue                         # 13 y 14 son el canal mismo
    d = np.hypot(*(np.array(CANAL['rio']) - Q[-1]).T); j = int(d.argmin())
    if d[j] > .05: continue
    paso_canal = len(CANAL['rio']) - 1 - j                             # pasos desde la fuente del canal
    t_conf = T_LLUVIA + paso_canal * PASO; L = largo(Q); t0 = max(.5, t_conf - L / V)
    alturas = np.array([alt(p) for p in Q]); pend = (alturas[0] - alturas[-1]) / max(L, 1e-3)
    afluentes.append(dict(rio=i, L=L, f=F0 * LMAX / L, t0=t0, t_conf=t_conf, pend=pend, alturas=alturas[np.linspace(0, len(Q) - 1, 6).astype(int)].tolist()))
afluentes.sort(key=lambda a: a['t0'])
pmax = max(a['pend'] for a in afluentes)
for k, a in enumerate(afluentes):
    a['tempo'] = 2.4 + 3.6 * a['pend'] / pmax                          # notas por segundo: más pendiente, más rápido (Reich: se desfasan)
    while a['f'] > 900: a['f'] /= 2
    while a['f'] < 180: a['f'] *= 2
    hs = [2 + int(round(4 * x / max(a['alturas']))) for x in a['alturas']][:5]     # su ostinato: los armónicos que dicen sus alturas
    a['ostinato'] = hs; t = a['t0']; n = 0; nr = None
    while t < a['t_conf'] + 1.5:
        cerca = max(0, (t - (a['t_conf'] - 2.5)) / 2.5)                  # los últimos 2.5 s cae al pulso del río
        f = a['f'] * hs[n % len(hs)] / 2
        if cerca > 0:                                                    # y su altura al armónico del río más cercano
            nr = max(2, round(f / F_RIO)); f = f * (1 - min(1, cerca)) + F_RIO * nr * min(1, cerca)
        vel = (.45 + .2 * (n % len(hs) == 0)) * (1 - max(0, (t - a['t_conf']) / 1.5))
        m = m_de(f); pan = -.7 + 1.4 * (k / max(1, len(afluentes) - 1))
        if a['L'] < .08: agua.append(dict(t=round(t, 4), tipo='gota', m=round(m, 3), v=round(vel * .9, 3)))
        else: web('marimba', t, 'marimba', m, vel, .25, pan)
        dt = 1 / a['tempo']; dt = dt * (1 - min(1, cerca)) + (PASO / 2) * min(1, cerca)
        t += dt; n += 1
# la lluvia cae en los afluentes: gotas sueltas
for k in range(40): agua.append(dict(t=round(R.uniform(.3, 26), 3), tipo='gota', m=round(m_de(F_RIO * R.choice([16, 18, 20, 24, 27])), 3), v=round(R.uniform(.2, .4), 3)))

# ═════════════ II · el río ═════════════
melodia = []                                           # la voz del río: una nota por paso del canal, ligada si repite el armónico
k = 0
while k < len(rio):
    n = armonico_rio(k); j = k
    while j + 1 < len(rio) and armonico_rio(j + 1) == n and j - k < 3: j += 1
    t = T_LLUVIA + k * PASO; d = (j - k + 1) * PASO
    melodia.append(dict(t=round(t, 4), dur=round(d, 4), n=n, f=f_rio(n), m=round(m_de(f_rio(n)), 3), vuelta=float(np.sum(vuelta[k:j + 1]))))
    k = j + 1
for nt in melodia:                                     # el arpa toca el río desde que entra (bajito en las fuentes)
    sube = min(1, max(.25, (nt['t'] - 10) / 20))
    arpa.append(dict(t=nt['t'], m=nt['m'], v=round(.55 * sube, 3), dur=nt['dur'], pan=0, voz='rio'))
    if abs(nt['vuelta']) > .12 and nt['dur'] >= PASO * 2:          # en las vueltas del cauce, un adorno: el armónico de al lado
        arpa.append(dict(t=round(nt['t'] + PASO, 4), m=round(m_de(f_rio(nt['n'] + (1 if nt['vuelta'] > 0 else -1))), 3), v=round(.4 * sube, 3), dur=round(PASO * .8, 4), pan=.15, voz='rio'))
# glisandos del arpa (Alice Coltrane): en cada cambio de armónico grande, una cascada por los armónicos de la cuerda del río
for a, b in zip(melodia, melodia[1:]):
    if abs(b['n'] - a['n']) >= 2 and SEC['II'][0] <= b['t'] < SEC['II'][1]:
        for q in range(8): arpa.append(dict(t=round(b['t'] - PASO + q * PASO / 8, 4), m=round(m_de(f_rio(b['n'] + 8 - q)), 3), v=.28, dur=.5, pan=-.4 + q * .1, voz='glis'))
# armonio y tambura: el bordón del río (armónicos 4 y 6 de su cuerda, y el 5 que entra y sale)
armonio.append(dict(t=6.0, dur=SEC['II'][1] - 6.0 + 2, notas=[m_de(f_rio(4)), m_de(f_rio(6)), m_de(f_rio(8))], v=.5))
tambura.append(dict(t=10.0, dur=SEC['II'][1] - 10.0, m=m_de(f_rio(4)), patron=[6, 8, 8, 4]))
for nt in melodia:                                     # el bajo: el armónico 2 o 3 de la cuerda del río, en ostinato de tres
    if nt['t'] < 28: continue
    for q, n2 in enumerate((2, 3, 2) if nt['n'] % 2 else (2, 2, 3)):
        tq = nt['t'] + q * PASO * nt['dur'] / PASO / 3
        if tq < SEC['II'][1]: bajo.append(dict(t=round(tq, 4), dur=round(PASO * .9, 4), m=round(m_de(f_rio(n2) * 2), 3), v=.85 if q == 0 else .65))
# el tambor parlante hace de tabla: dha (centro), na (borde), ge (centro grave que sube), tin (palo), con el pulso del río
TABLA = [('centro', 1.0, 0), ('borde', .5, 0), ('borde', .6, 0), ('centro', .7, 3), ('palo', .45, 0), ('borde', .55, 0), ('centro', .8, 2), ('borde', .5, 0)]
t = 30.0; k = 0
while t < SEC['II'][1] - .1:
    tipo, v, sube = TABLA[k % 8]; tabla.append(dict(t=round(t, 4), tipo=tipo, m=round(m_de(f_rio(4)) + 12, 3), v=round(v * (.8 + .2 * (k % 16 < 8)), 3), curva=[[0, sube], [.15, 0]] if sube else None))
    t += PASO / 2; k += 1
for k in range(int((SEC['II'][1] - 30) / PASO)): bat(30 + k * PASO, 'ride', .32 + .12 * (k % 2 == 0), .3)

# ── el coro de vocoders: el verso en el río, el estribillo en el delta ──
VERSO = ['el a gua no re cuer da la mon ta ña', 'ba ja con el nom bre de o tro rí o', 'ca da a rro yo que me al can za', 'se vuel ve mi voz y yo la su ya']
ESTRIBILLO = ['no ten go tron co', 'ten go de sem bo ca du ras', 'ca da bra zo di ce o tra vez lo que di je', 'lle go al mar por to das par tes']
def coral(versos, t0, n_tiempos, f_de_t, pasos_por_silaba=1.0):
    """el coro canta sobre los armónicos que suenan a esa hora: soprano = el armónico de la melodía, contralto y tenor = armónicos
    abajo que forman acorde con él (4:5:6 de la misma cuerda), bajo = la fundamental de la cuerda en su octava"""
    voces = {v: [] for v in 'SATB'}; t = t0
    for verso in versos:
        sil = verso.split(); dur = n_tiempos * PASO / len(sil)
        for j, sy in enumerate(sil):
            f_s, f_cuerda = f_de_t(t)
            n = max(4, round(f_s / f_cuerda)); fa = f_cuerda * max(3, round(n * 4 / 5)); ft = f_cuerda * max(2, round(n * 2 / 3))
            fb = f_cuerda
            while fb < 70: fb *= 2
            for v, f in zip('SATB', (f_s, fa, ft, fb)):
                while f > 700: f /= 2
                voces[v].append(dict(t=round(t, 4), dur=round(dur * (.92 if j < len(sil) - 1 else 1.4), 4), texto=sy, nota=round(m_de(f), 3)))
            t += dur
        t += PASO
    return voces
def f_rio_en(t):
    k = max(0, min(len(rio) - 1, int((t - T_LLUVIA) / PASO))); return f_rio(armonico_rio(k)) * 2, F_RIO
CORO1 = coral(VERSO, 52.0, 10, f_rio_en)
# en el delta el coro canta sobre la cuerda del brazo largo (el arpa), que es la que llega al último
def f_delta_en(t):
    k = int((t - T_APICE) / (PASO * FRENO / 2)); hs = [4, 5, 6, 5, 4, 3, 4, 6, 7, 6]
    return F_BRAZO[0] * hs[k % len(hs)], F_BRAZO[0]
CORO2 = coral(ESTRIBILLO, T_APICE + 6, 9, f_delta_en)

# ═════════════ III · el delta: canon en cinco cuerdas ═════════════
frase = [nt['n'] for nt in melodia[-8:]]               # lo último que dijo el río, en armónicos
canon = []
for i, b in enumerate(BRAZOS):
    Q = np.array(CANAL['brazos'][i]); dirb = np.unwrap(np.arctan2(np.diff(Q[:, 1]), np.diff(Q[:, 0]))); giro = np.cumsum(np.concatenate([[0], np.diff(dirb)]))
    tempo = (2 / PASO) * (LMAX / b['largo']) / FRENO * 1.5           # notas por segundo: los brazos cortos van más rápido
    t = T_APICE + i * PASO / 2; k = 0; f = F_BRAZO[i]
    while t < T_LLEGA[i] - .3:
        if k < len(frase): n = max(2, min(9, round(frase[k] * 6 / 18) + 2))       # primero la frase del río en su cuerda (canon)
        else:
            u = min(len(giro) - 1, int((t - T_APICE) / (T_LLEGA[i] - T_APICE) * len(giro)))
            n = 3 + int(round(3 + 3 * math.sin(giro[u] * 2.5 + i)))       # luego las vueltas de su cauce
        acento = k % [3, 4, 5, 3, 2][i] == 0
        canon.append(dict(t=round(t, 4), brazo=i, n=n, m=round(m_de(f * n / 2), 3), dur=round(min(1.2, 1.5 / tempo), 4), v=.62 if acento else .45))
        arpa.append(dict(t=round(t, 4), m=round(m_de(f * n / 2), 3), v=.6 if acento else .42, dur=round(min(1.6, 2 / tempo), 4), pan=b['pan'], voz='brazo%d' % i))
        t += 1 / tempo; k += 1
# hyperpop acuático: 808 al pulso del río, rachas de hats, palmas fritas; el sub en la fundamental de la cuerda larga
sub = []
for k in range(int((T_MAR + 6 - T_APICE) / PASO)):
    t0 = T_APICE + k * PASO
    if k % 4 in (0, 2) or k % 8 == 7: bat(t0, 'kick', .95)
    if k % 4 in (1, 3): bat(t0, 'clap', .8, 0, 'bateria-frito', 'bateria-frito')
    for q in range(4):
        if k % 8 == 6 and q >= 2:
            for j in range(3): bat(t0 + q * S + j * S / 3, 'hat', .4 + .15 * j, .25)
        else: bat(t0 + q * S, 'hat', .5 if q % 2 == 0 else .3, .25)
    if k % 4 == 0: sub.append(dict(t=round(t0, 4), midi=round(m_de(F_BRAZO[0] / 2), 3), vel=.85, dur=round(PASO * 3.6, 4)))
web('bateria-frito', T_APICE, 'bateria-frito', 60, 1.0, .3, 0, pieza='spray')
# la garganta de río: en el delta canta el tenor del estribillo con sus cinco bocas
for e in CORO2['T']: garganta.append(dict(t=e['t'], dur=e['dur'], nota=e['nota'], texto=e['texto'], v=.7, aprende=.85, voz='coro'))
for e in CORO1['T']: garganta.append(dict(t=e['t'], dur=e['dur'], nota=e['nota'], texto=e['texto'], v=.6, aprende=.8, voz='coro'))
# la voz de agua canta la contralto; Sabina la soprano (moduladora)
for C in (CORO1, CORO2):
    for e in C['A']: vozagua.append(dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota'], modo='canto', voz=1, v=.65))
sabina = [dict(eventos=[dict(t=e['t'], dur=e['dur'], texto=e['texto'], nota=e['nota']) for e in C['S']], nivel=.85, pan=0, capa='soprano') for C in (CORO1, CORO2)]
# aves del delta: garzas (ronco) y gaviotas (silbido que cae) sobre los brazos
for k in range(14):
    t = R.uniform(T_APICE + 2, T_FIN - 8); i = R.randrange(5)
    aves.append(dict(t=round(t, 3), tipo=R.choice(['ronco', 'silbido', 'silbido']), m=round(m_de(F_BRAZO[i] * R.choice([8, 9, 10, 12])), 3), m2=round(m_de(F_BRAZO[i] * 6), 3), dur=round(R.uniform(.2, .5), 3), v=.45, voz=k % 2))

# ═════════════ IV · el mar (Scelsi) ═════════════
# cada brazo, al llegar, se desliza a la nota del mar (La2 o su octava) y se queda; su desviación empieza en lo que lo separaba
# del mar (en cents, dentro de ±45) y se cierra en el tiempo que le queda (τ = resto / 4.5): los batidos se hacen lentos hasta el unísono
mar = []
for i, t1 in enumerate(T_LLEGA):
    f_ult = F_BRAZO[i] * canon[[c['brazo'] for c in canon].index(i) if i in [c['brazo'] for c in canon] else 0]['n'] / 2
    oct_mar = F_MAR * (2 if i % 2 else 1)
    dev0 = ((1200 * math.log2(F_BRAZO[i] / F0) + 600) % 100 - 50) * .9
    mar.append(dict(brazo=i, t=round(t1, 3), dur=round(T_FIN - t1, 3), desde=round(m_de(oct_mar * 1.12), 3), m=round(m_de(oct_mar), 3), dev0=round(dev0, 2), tau=round((T_FIN - t1) / 4.5, 2), pan=BRAZOS[i]['pan'],
                    vocal=['a', 'o', 'u', 'o', 'a'][i]))
# la garganta de río dice «mar» en la nota del mar: la vocal se abre y se cierra (a → o → u), la siringe entre dos caras (bifonía a un cuarto de tono)
for k, (vc, d) in enumerate([('a', 9), ('o', 9), ('u', 8), ('o', 7)]):
    t = T_MAR + 2 + sum(x[1] for x in [('a', 9), ('o', 9), ('u', 8), ('o', 7)][:k])
    garganta.append(dict(t=round(t, 3), dur=d - .2, nota=m_de(F_MAR), nota2=m_de(F_MAR) + .5 * (1 - k / 4), fonemas=(['m', vc] if k == 0 else [vc]), v=.55, aprende=.75, voz='mar'))
trombon.append(dict(t=round(T_MAR + 4, 3), dur=round(T_FIN - T_MAR - 6, 3), m=m_de(F_MAR), tipo='normal', v=.5))
trombon.append(dict(t=round(T_MAR + 14, 3), dur=12, m=m_de(F_MAR) + .25, tipo='growl', v=.45))
gong.append(dict(t=round(T_MAR, 3), tipo='arco', m=m_de(F_MAR) - 12, dur=round(T_FIN - T_MAR - 4, 3), v=.45))
agua.append(dict(t=round(T_MAR - 2, 3), tipo='ola', dur=round(T_FIN - T_MAR + 6, 3), v=.55))
for k in range(5): agua.append(dict(t=round(T_MAR + 8 + k * 7, 3), tipo='ola', dur=9, v=.35))
sabina.append(dict(eventos=[dict(t=round(T_MAR + 3, 3), dur=10, texto='mar', nota=m_de(F_MAR * 2)), dict(t=round(T_MAR + 14, 3), dur=12, texto='a', nota=m_de(F_MAR * 2) + .3)], nivel=.6, pan=0, capa='mar'))

glitch = [round(T_APICE + k * 8 * PASO - S * 2, 4) for k in range(1, int((T_MAR - T_APICE) / (8 * PASO)))]
partitura = dict(titulo='El río no tiene tronco', semilla=SEMILLA, terreno='traspuesta 412601 (delta)', f0=F0, f_rio=F_RIO, f_brazos=F_BRAZO, paso=PASO, semicorchea=S,
                 tiempos=dict(lluvia=T_LLUVIA, apice=T_APICE, llegan=T_LLEGA, mar=T_MAR, fin=T_FIN), secciones=SEC, duracion=DUR, melodia=melodia, afluentes=afluentes,
                 canon=canon, mar=mar, web=ev, arpa=arpa, armonio=armonio, tambura=tambura, bajo=bajo, agua=agua, aves=aves, tabla=tabla, trombon=trombon, gong=gong,
                 vozagua=vozagua, garganta=garganta, sabina=sabina, coros=dict(II=CORO1, III=CORO2), sub=sub, glitch=glitch, delta=DELTA,
                 letra=dict(verso=VERSO, estribillo=ESTRIBILLO), instrumentos='instrumentos-6cfb608fb387')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('duración', round(DUR, 1), 's · ápice', round(T_APICE, 1), '· llegan', [round(x, 1) for x in T_LLEGA], '· fin', round(T_FIN, 1))
    print('cuerdas: río', round(F_RIO, 2), 'Hz · brazos', [round(f, 1) for f in F_BRAZO], '· afluentes', len(afluentes), [(a['rio'], round(a['f'], 1), round(a['t0'], 1), round(a['t_conf'], 1)) for a in afluentes])
    print({k: len(v) for k, v in ev.items()}, '· arpa', len(arpa), '· canon', len(canon), '· melodía', len(melodia), '· tabla', len(tabla), '· garganta', len(garganta), '· vozagua', len(vozagua), '· agua', len(agua))
