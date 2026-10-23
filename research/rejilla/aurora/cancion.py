"""Rejilla 04 · «sobre la aurora» (poema de Canek Zapata, *poemas del espacio*) — loop C: la canción.

La armonía es el laberinto de `laberinto.json` (DFS sembrado sobre el Tonnetz), con la paleta
oscura del loop B.2. La narradora (Sabina) canta el poema completo con la voz magnética (Zira
una octava abajo); el robot (Zira) deletrea y repite. Cada sección aplica un gesto de imagen.

    python aurora/cancion.py            # ~30 min
    python aurora/cancion.py --mezcla   # sólo la mezcla
"""
import hashlib, json, math, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from motor import (M, E, S, N, H, T, F, SR_OUT, Pista, sintetizar, leer, euclides,
                   arena, entropia, negativo, peine, ruido)
import instrumentos as I

AQUI = Path(__file__).parent
R = AQUI.parent / 'render' / 'aurora'; R.mkdir(parents=True, exist_ok=True)
TAG = 's1015'
t16 = T / 16
q = lambda b, pos: b * T + pos * t16
LAB = json.load(open(AQUI / 'laberinto.json'))
CAMINO = [(r, bool(m), op) for r, m, op in LAB['camino']]
CALLEJONES = set(LAB['callejones'])                       # pasos 21 (Mi) y 29 (Mi♭)
mel_rng = np.random.default_rng(1015)

# ───────────── el plan: qué paso del laberinto suena en cada compás ─────────────
SECCIONES = [  # (nombre, [(paso, compases), ...])
    ('señal',     [(0, 2)] + [(p, 1) for p in range(1, 8)]),
    ('tormenta',  [(p, 1) for p in range(8, 16)]),
    ('bocinas',   [(p, 2) for p in range(16, 21)] + [(21, 1)]),
    ('entropía',  [(p, 1) for p in range(22, 28)]),
    ('helecho',   [(28, 1), (29, 5)]),
    ('confundo',  [(p, 1) for p in range(30, 39)]),
    ('se expande', [(p, 1) for p in range(39, 47)]),
    ('sistema',   [(46, 9)]),
]
PLAN = []
for sec, pasos in SECCIONES:
    for p, n in pasos:
        for k in range(n):
            r, m, op = CAMINO[p]
            PLAN.append({'sec': sec, 'paso': p, 'raiz': r, 'menor': m, 'op': op,
                         'callejon': p in CALLEJONES and k == 0 and sec != 'helecho' or (p == 29 and k == 0)})
C = len(PLAN) + 1                                          # + un compás para las colas
COLS = {sec: [b for b, x in enumerate(PLAN) if x['sec'] == sec] for sec, _ in SECCIONES}
ACORDE = [I.acorde_oscuro(x['raiz'], x['menor']) for x in PLAN]

# ───────────── el poema (completo), por sección ─────────────
LETRA = {
    'señal': ['perdimos contacto con el último robot que mandamos', 'para buscar'],
    'tormenta': ['antes, nos habló de la oscuridad', 'que llevaba meses envolviéndolo', 'bajo la tormenta de arena',
                 'mientras resonaba en la atmósfera', 'su última transmisión de radio'],
    'bocinas': ['le instalamos unas bocinas', 'una rudimentaria', 'porque sentimos que era muy raro',
                'mandar tan lejos en el espacio', 'a un robot sin darle al menos', 'algo con que pudiera emitir',
                'vibraciones sonoras'],
    'entropía': ['entre el vacío de', 'casi infinita', 'incomunicación'],
    'helecho': ['ese día', 'mi pequeño helecho', 'que escondía en una cueva', 'murió'],
    'confundo': ['hay veces que', 'en sueños confundo', 'el tono de voz', 'magnético', 'que le instalamos',
                 'a la sonda', 'con el silencio', 'que emanaba', 'del helecho'],
    'se expande': ['y siento', 'como', 'todo el', 'espacio se llena', 'de ruido y entropía', 'como una',
                   'comunicación', 'casi infinita', 'que se expande', 'envolviéndome', 'infinitos granos',
                   'de ruido', 'hormiguean mi piel'],
    'sistema': ['muchas veces pienso', 'acaso la razón de la vida', 'en este planeta', 'sea simplemente',
                'la resolución del problema', 'de la no-comunicación', 'incorporándola al sistema'],
}
# dónde empieza a cantar cada sección (compás relativo) y cuánto aire dejar entre versos (16avos)
ENTRADA = {'señal': (2, 3), 'tormenta': (0, 2), 'bocinas': (0, 3), 'entropía': (1, 6), 'helecho': (0, 4),
           'confundo': (0, 3), 'se expande': (0, 0), 'sistema': (0, 3)}
CENTRO = {'señal': 60, 'tormenta': 60, 'bocinas': 61, 'entropía': 57, 'helecho': 57, 'confundo': 59,
          'se expande': 63, 'sistema': 59}                     # dónde vive la voz en cada sección
FINAL = {'se expande': 2}                                      # la última sílaba de cada verso (16avos)
FIJO = {'ese día': (0, 1), 'mi pequeño helecho': (0, 7), 'que escondía en una cueva': (1, 1), 'murió': (5, 5)}
# 'una rudimentaria' deja un hueco para que el robot diga «voz»; 'para buscar' deja el hueco del deletreo
HUECO = {'una rudimentaria': 10, 'para buscar': 40}


def acorde_en(abs16):
    b = min(len(ACORDE) - 1, abs16 // 16)
    bajo, voces = ACORDE[b]
    return sorted({n % 12 for n in [bajo] + voces}), bajo % 12


def melodia(linea, inicio16, prev, centro=60, final=4):
    """Una línea cantada. Ritmo por acentos (tónica = 2 dieciseisavos, átona = 1, la última larga,
    a veces la tónica llega tarde). Alturas: un contorno por verso (arco, baja, sube u ola) alrededor
    del centro de la sección; las tónicas caen en notas del acorde, las átonas pueden rozar el grano
    de medio tono; se castiga repetir la misma nota tres veces; la última, raíz o quinta."""
    sil, pal = I.silabear(linea)
    tonicas, k = set(), 0
    for p in linea.replace('—', ' ').replace(',', ' ').split():
        ss = I.SIL.silabea(p); t = I.SIL.tonica(p)
        if t is not None: tonicas.add(k + t)
        k += len(ss)
    forma = mel_rng.choice(['arco', 'baja', 'sube', 'ola'])
    def contorno(u):
        return {'arco': 5 * math.sin(math.pi * u), 'baja': 4 - 8 * u, 'sube': -3 + 7 * u,
                'ola': 4 * math.sin(2 * math.pi * u)}[forma]
    notas, pos, dur, t = [], [], [], 0
    n = len(sil)
    for i, s in enumerate(sil):
        ton = i in tonicas
        if ton and i and mel_rng.uniform() < .35: t += 1
        d = final if i == n - 1 else (2 if ton else 1)
        pcs, raiz = acorde_en(inicio16 + t)
        objetivo = .3 * prev + .7 * (centro + contorno(i / max(1, n - 1)))
        cand = [m for m in range(52, 72) if m % 12 in pcs]
        if i == n - 1:
            cand = [m for m in range(52, 72) if m % 12 in (raiz, (raiz + 7) % 12)]
        elif not ton:
            cand += [m + 1 for m in cand if 52 <= m + 1 < 72]
        def costo(c):
            rep = 2.5 if len(notas) >= 2 and notas[-1] == notas[-2] == c else 0
            salto = 0 if ton else max(0, abs(c - prev) - 3) * .8        # las átonas no saltan
            return abs(c - objetivo) + rep + salto + mel_rng.uniform(0, .9)
        m = min(cand, key=costo)
        notas.append(m); pos.append(t); dur.append(d); prev = m; t += d
    return notas, pos, dur, t, prev


def colocar_letra():
    """Todas las líneas en el tiempo: [(sección, línea, inicio16 absoluto, notas, pos, dur)]."""
    versos, prev = [], 60
    for sec, lineas in LETRA.items():
        b0 = COLS[sec][0]; ent, aire = ENTRADA[sec]
        cur = (b0 + ent) * 16 + 1
        fin_sec = (COLS[sec][-1] + 1) * 16
        for ln in lineas:
            if ln in FIJO: cur = (b0 + FIJO[ln][0]) * 16 + FIJO[ln][1]
            notas, pos, dur, largo, prev = melodia(ln, cur, prev, CENTRO[sec], FINAL.get(sec, 4))
            versos.append((sec, ln, cur, notas, pos, dur))
            cur += largo + aire + HUECO.get(ln, 0)
            if cur % 2 == 0: cur += 1                                 # que el siguiente verso entre a contratiempo
        if cur > fin_sec + 4: print(f'  ¡ojo! {sec}: la letra se pasa {cur - fin_sec} dieciseisavos')
    return versos


# ───────────── la banda ─────────────
OST7 = [0, 1, 7, 0, 13, 7, 6]


def banda(P, b, x, kit=True, ost=True, piano=True, organo=0.0, vel=1.0):
    bajo, voces = ACORDE[b]
    if piano:
        for pos, du, v in ((0, 6, .5), (7, 5, .38)):
            for i, n in enumerate(voces): E.piano(P['armonia'], n, q(b, pos) + 0.012 * i, v * vel, du * t16, pan=-.3 + .2 * i)
    if organo:
        for n in [bajo + 12] + voces: I.organo(P['armonia'], n, q(b, 0), T * .97, organo * vel)
    for pos, du in ((0, 7), (10, 5)): E.sub808(P['bajo'], bajo, q(b, pos), du * t16, .5 * vel)
    if kit:
        for pos in euclides(5, 16, 2): I.subbombo(P['bombo'], q(b, pos), .6 * vel)
        I.placa(P['bateria'], q(b, 12), .8 * vel)
        if b % 2: I.placa(P['bateria'], q(b, 6), .35 * vel, pan=-.4)
        for pos in euclides(7, 16, 1): I.polvo(P['bateria'], q(b, pos), .4 * vel)
    if ost:
        for k in range(16):
            i = b * 16 + k
            I.preparado(P['ostinato'], bajo + 12 + OST7[i % 7], q(b, k), (.55 + .35 * (i % 7 == 0)) * vel, pan=.35)


def robot_nota(b, k):
    """Las alturas del robot: notas del acorde con saltos de Dolphy (novenas, séptimas mayores)."""
    bajo, voces = ACORDE[b]
    return [voces[0] + 24, voces[3] + 12, voces[2] + 12, voces[1] + 12, voces[3] + 24, voces[0] + 12, voces[2],
            voces[3] + 24, voces[1], voces[0] + 24, voces[1] + 12][k % 11]


def componer():
    nombres = ['bombo', 'bateria', 'bajo', 'ostinato', 'armonia', 'helecho', 'voz', 'magnetica', 'robot', 'radio', 'ruido']
    P = {n: Pista(n, C) for n in nombres}

    # la narradora y su voz magnética
    versos = colocar_letra()
    informe = []
    for sec, ln, cur, notas, pos, dur in versos:
        t0 = cur * t16
        g = .75 if sec == 'sistema' else 1.0                   # los corchetes: la coda más quedita
        informe += I.cantar_con(P['voz'], ln, notas, pos, dur, t0, 'sabina', g=g)
        I.cantar_con(P['magnetica'], ln, notas, pos, dur, t0, 'zira', g=.35 * g, transporte=-12)

    for b, x in enumerate(PLAN):
        sec = x['sec']; rel = b - COLS[sec][0]; cj = x['callejon']
        if sec == 'señal':
            if rel < 3: I.estatica(P['radio'], [b], [1.0, .7, .45][rel])
            if rel == 1: I.telemetria(P['robot'], q(b, 2), 'vida')
            banda(P, b, x, kit=rel >= 4, ost=rel >= 2, piano=rel >= 3, organo=.25 if rel < 3 else 0)
            if rel in (4, 5):   # el robot deletrea v i d a e n o t r o (11 golpes en 32) y dice «planeta»
                letras = ['uve', 'i', 'de', 'a', 'e', 'ene', 'o', 'te', 'erre', 'o', 'planeta']
                if rel == 4:
                    for k, (s, p) in enumerate(zip(letras, euclides(11, 32))):
                        I.robot(P['robot'], s, robot_nota(b, k), q(b, p), (8 if s == 'planeta' else 2.2) * t16, g=.85,
                                pan=(robot_nota(b, k) - 64) / 24)
        elif sec == 'tormenta':
            banda(P, b, x, organo=.18)
            if rel == 7: I.robot(P['robot'], 'radio', robot_nota(b, 3), q(b, 13), 3 * t16, g=.7, tartamudeo=3)
        elif sec == 'bocinas':
            if cj:   # callejón Mi: la banda se detiene; sólo el robot y la estática
                I.estatica(P['radio'], [b], [.8])
                for k, (s, p) in enumerate((('ruido', 2), ('y', 6), ('entropía', 8))):
                    I.robot(P['robot'], s, robot_nota(b, k * 3), q(b, p), (6 if s == 'entropía' else 3) * t16, g=.9)
            else:
                banda(P, b, x, organo=.15 if rel % 2 else 0)
                if rel % 2 == 1:   # el gancho: «voz», tartamudeado
                    I.robot(P['robot'], 'voz', robot_nota(b, rel), q(b, 14), 2 * t16, g=.85, tartamudeo=2)
        elif sec == 'entropía':
            banda(P, b, x, kit=rel < 4, piano=True, organo=.2, vel=1 - .1 * rel)
            silabas = ['in', 'co', 'mu', 'ni', 'ca', 'ción']
            for k, p in enumerate(euclides(6, 16, rel)):
                I.robot(P['robot'], silabas[k], robot_nota(b, k + rel), q(b, p), 1.5 * t16, g=.5, pan=(-1) ** k * .6)
        elif sec == 'helecho':
            if rel == 0: banda(P, b, x, kit=False, ost=True, piano=True, organo=.2)
            elif rel == 1:   # callejón Mi♭: stop-time, la estática y el robot
                I.estatica(P['radio'], [b], [.6])
            if rel == 2:     # el helecho escribe su partitura en vidrio frotado, crece y muere
                bajo, voces = ACORDE[b]
                eb = sorted({n % 12 for n in [bajo] + voces})
                notas = sorted(48 + n + 12 * o for n in eb for o in range(0, 3))
                I.helecho_oscuro(P['helecho'], q(b, 0), 4, notas, puntos=170)
                for n in [bajo + 12] + voces: I.organo(P['armonia'], n, q(b, 0), 3 * T, .3)
        elif sec == 'confundo':
            banda(P, b, x, kit=True, ost=True, piano=rel % 2 == 0, organo=.18, vel=.75)
            if rel in (3, 4): I.robot(P['robot'], 'magnético', robot_nota(b, rel), q(b, 10), 6 * t16, g=.6)
        elif sec == 'se expande':
            banda(P, b, x, organo=.25, vel=1.05)
            for pos in range(0, 32):                                   # granos de ruido
                if mel_rng.uniform() < .55: I.polvo(P['bateria'], q(b, pos / 2), .22, pan=mel_rng.uniform(-.9, .9))
            if rel % 2 == 1:
                I.robot(P['robot'], 'ruido' if rel % 4 == 1 else 'entropía', robot_nota(b, rel), q(b, 14), 2 * t16, g=.7,
                        tartamudeo=3)
        elif sec == 'sistema':
            bajo, voces = ACORDE[b]
            if rel == 0:
                for n in [bajo, bajo + 12] + voces: I.organo(P['armonia'], n, q(b, 0), T * 6.5, .28)
            E.sub808(P['bajo'], bajo, q(b, 0), T * .95, .3)
            if rel == 6:
                I.telemetria(P['robot'], q(b, 6), 'vida', vel=.5)
    return P, versos, informe


# ───────────── gestos de imagen por sección ─────────────
def gestos(n, ZL, ZR):
    t = COLS['tormenta']
    if n in ('voz', 'magnetica'): gens = [0, 0, 1, 1, 2, 3, 4, 6]
    else: gens = [0, 1, 2, 3, 4, 6, 9, 14]
    if n not in ('radio', 'ruido'): ZL, ZR = arena(ZL, t, gens), arena(ZR, t, gens)
    e = COLS['entropía']
    eps = np.linspace(.15, 1, len(e)) * (.5 if n in ('voz', 'magnetica') else 1)
    if n not in ('radio', 'ruido'): ZL, ZR = entropia(ZL, e, eps, 7), entropia(ZR, e, eps, 8)
    if n in ('ostinato', 'armonia'):                               # el regreso, en espejo
        for c in COLS['entropía'] + COLS['confundo']:
            ZL[c] = np.conj(ZL[c]); ZR[c] = np.conj(ZR[c])
    if n in ('voz', 'magnetica'):                                  # confundo la voz con el silencio
        neg = [c for i, c in enumerate(COLS['confundo']) if i % 2 == 1]
        ZL, ZR = negativo(ZL, neg), negativo(ZR, neg)
    if n == 'ruido':                                               # la no-comunicación, incorporada al sistema
        bajo, voces = ACORDE[COLS['sistema'][0]]
        w = peine([bajo, bajo + 12] + voces + [v + 12 for v in voces])
        z = ruido(semilla=23) * 2e-3
        for i, c in enumerate(COLS['sistema']):
            al = min(1, i / 4)
            filtro = (1 - al) + al * w * 6
            ZL[c] = z * filtro; ZR[c] = z * filtro * np.exp(1j * .9)
    return ZL, ZR


PROLACION = ['armonia', 'voz', 'magnetica', 'robot', 'ostinato']


def main(solo=None):
    P, versos, informe = componer()          # siempre se compone todo: las semillas avanzan igual
    errs = [abs(s['error_st']) for s in informe if s['error_st'] is not None]
    print(f'C={C} compases, {C * T:.1f} s · sílabas cantadas {len(informe)}, error mediano {np.median(errs):.2f} st, '
          f'máx {max(errs):.2f} st')
    json.dump({'versos': [(s, l, c, n, p, d) for s, l, c, n, p, d in versos], 'informe': informe,
               'plan': PLAN, 'cols': COLS}, open(R / 'partitura.json', 'w', encoding='utf-8'), ensure_ascii=False, default=str)
    escalas, vistas = {}, {}
    if solo:                                  # rehacer sólo algunas pistas: lo demás se queda
        escalas = json.load(open(R / 'escalas.json'))['escalas']
        vistas = dict(np.load(R / 'vistas.npz'))
    v0, v1 = COLS['se expande'][0], COLS['se expande'][-1] + 1
    for n, p in P.items():
        if solo and n not in solo: continue
        ZL, ZR = p.escribir()
        vistas[n + '-escrita'] = M.vista(ZL + ZR)
        ZL, ZR = gestos(n, ZL, ZR)
        vistas[n] = M.vista(ZL + ZR)
        escalas[n] = sintetizar(ZL, ZR, R / f'{n}.wav')
        if n in PROLACION:   # la comunicación se multiplica: la misma imagen a 3/2× y a 2×
            for k, sr in ((1, S * 3 // 2), (2, 2 * S)):
                escalas[f'{n}-p{k}'] = sintetizar(np.ascontiguousarray(ZL[v0:v1]), np.ascontiguousarray(ZR[v0:v1]),
                                                  R / f'{n}-p{k}.wav', sr=sr)
        del ZL, ZR
        print('  pista', n, 'lista')
    np.savez_compressed(R / 'vistas.npz', **vistas)
    json.dump({'escalas': escalas}, open(R / 'escalas.json', 'w'))
    linea_de_tiempo(escalas)
    mezclar()


def linea_de_tiempo(escalas):
    v0, v1 = COLS['se expande'][0], COLS['se expande'][-1] + 1
    largo = lambda c: int(round(c * T * SR_OUT))
    for n in json.load(open(R / 'escalas.json'))['escalas']:
        if '-p' in n: continue
        y = leer(R / f'{n}.wav', escalas[n])
        if n in PROLACION:
            seg = largo(v1 - v0)
            for k, pan in ((1, -.7), (2, .7)):
                z = leer(R / f'{n}-p{k}.wav', escalas[f'{n}-p{k}'])
                z = np.concatenate([z] * 3)[:seg]
                gL, gR = M.paneo(pan)
                y[largo(v0):largo(v0) + seg, 0] += .45 * gL * z[:, 0]
                y[largo(v0):largo(v0) + seg, 1] += .45 * gR * z[:, 1]
        wavfile.write(R / f'tl-{n}.wav', SR_OUT, y.astype(np.float32))


NOMBRES = ['bombo', 'bateria', 'bajo', 'ostinato', 'armonia', 'helecho', 'voz', 'magnetica', 'robot', 'radio', 'ruido']
GANANCIA = {'bombo': .55, 'bateria': 6.5, 'bajo': .9, 'ostinato': 2.5, 'armonia': 2.6, 'helecho': 1.6, 'voz': 1.6,
            'magnetica': 2.3, 'robot': 2.6, 'radio': 1.0, 'ruido': 1.3}


def mezclar():
    g = GANANCIA
    ent = sum([['-i', str(R / f'tl-{n}.wav')] for n in NOMBRES], [])
    i = {n: k for k, n in enumerate(NOMBRES)}
    v = lambda n: f"[{i[n]}]volume={g[n]}"
    grafo = ';'.join([
        f"{v('bombo')},asplit=3[k][kc1][kc2]",
        f"{v('bateria')}[dr]", f"{v('bajo')}[ba0]", f"{v('ostinato')}[os]", f"{v('armonia')}[ar0]",
        f"{v('helecho')}[he]", f"{v('voz')},highpass=f=120,equalizer=f=2800:t=o:w=1.4:g=3[vo]",
        f"{v('magnetica')},lowpass=f=3000[mg]", f"{v('robot')},highpass=f=150[ro]", f"{v('radio')}[ra]",
        f"{v('ruido')}[ru]",
        "[ar0][kc1]sidechaincompress=threshold=0.05:ratio=3:attack=6:release=200:makeup=1[ar]",
        "[ba0][kc2]sidechaincompress=threshold=0.06:ratio=3:attack=4:release=150:makeup=1[ba]",
        "[os][ar][he][vo][mg][ro][ru]amix=inputs=7:normalize=0,asplit[seco][w0]",
        "aevalsrc=d=4:s=48000:exprs='(random(0)*2-1)*exp(-t*1.3)|(random(1)*2-1)*exp(-t*1.3)',lowpass=f=4500,highpass=f=200[ir]",
        "[w0][ir]afir=dry=0:wet=1[rev]",
        "[seco][rev]amix=inputs=2:weights=1 0.16:normalize=0[musica]",
        "[k][dr][ba][musica][ra]amix=inputs=5:normalize=0,highpass=f=24,"
        "acompressor=threshold=0.22:ratio=2.2:attack=15:release=220:makeup=1,"
        "loudnorm=I=-14:TP=-1.2:LRA=11,aresample=48000[out]",
    ])
    final = R / f'sobre-la-aurora-{TAG}.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *ent, '-filter_complex', grafo,
                    '-map', '[out]', '-c:a', 'pcm_s16le', str(final)], check=True)
    m4a = AQUI / f'sobre-la-aurora-{TAG}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(final), '-c:a', 'aac', '-b:a', '224k', str(m4a)], check=True)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(final), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    tail = r[r.rfind('Summary:'):]
    val = lambda key: float(tail.split(key)[1].split()[0])
    med = {'I_LUFS': val('I:'), 'LRA': val('LRA:'), 'pico_dBTP': val('Peak:'),
           'duracion_s': round(wavfile.read(final)[1].shape[0] / SR_OUT, 2),
           'sha256_m4a': hashlib.sha256(m4a.read_bytes()).hexdigest()}
    print(med)
    json.dump(med, open(AQUI / f'medidas-cancion-{TAG}.json', 'w'), indent=1)


if __name__ == '__main__':
    if '--mezcla' in sys.argv: mezclar()
    elif '--pistas' in sys.argv: main(solo=sys.argv[sys.argv.index('--pistas') + 1].split(','))
    elif '--letra' in sys.argv:          # revisar sólo dónde cae la letra y qué notas canta
        for sec, ln, cur, notas, pos, dur in colocar_letra():
            print(f'{sec:11s} c{cur // 16:2d}.{cur % 16:<2d} {ln:40s} {notas}')
    else: main()
