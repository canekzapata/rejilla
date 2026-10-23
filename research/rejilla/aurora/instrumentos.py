"""Instrumentos de «sobre la aurora» (los nuevos; los de Esquinas se reusan desde E)."""
import math, sys
from pathlib import Path
import numpy as np
from motor import M, E, S, N, H, T, F, rng, Pista, a_sr, afinar, dicho

# la cantante de yoshi 16 (Sabina con TD-PSOLA sílaba por sílaba); su caché va a la nuestra
YOSHI16 = Path(__file__).parents[3] / 'meleeviewer' / 'output' / 'Arte' / '2026-10-09_yoshi_es_un_vector_16_jpop'
sys.path.insert(0, str(YOSHI16))
import cantante as K
import silabas as SIL
K.CACHE = Path(__file__).parents[1] / 'render' / 'tts-cantante'


def silabear(texto):
    """'perdimos contacto' → (['per','di','mos','con','tac','to'], [3, 3])"""
    pal = [SIL.silabea(p) for p in texto.replace('—', ' ').split()]
    return [s for p in pal for s in p], [len(p) for p in pal]


def cantar(P, texto, notas, pos16, dur16, t0, g=1.0, pan=0.0):
    """La narradora canta `texto`: una nota, un inicio y una duración (en 16avos desde t0) por sílaba.
    Devuelve el informe de la cantante (error en semitonos por sílaba, medido)."""
    sil, palabras = silabear(texto)
    assert len(sil) == len(notas) == len(pos16) == len(dur16), (texto, len(sil), len(notas), len(pos16), len(dur16))
    t16 = T / 16
    frase = {'texto': texto, 'palabras': palabras,
             'silabas': [{'t': p * t16, 'dur': d * t16 * 0.96, 'nota': n, 'txt': s}
                         for s, n, p, d in zip(sil, notas, pos16, dur16)]}
    largo = (max(p + d for p, d in zip(pos16, dur16)) + 4) * t16
    y, informe = K.canta([frase], largo)
    P.muestra(a_sr(y, K.SR, S), t0, g, pan)
    return informe


def robot(P, texto, midi, t0, dur, g=1.0, pan=0.0, tartamudeo=0):
    """La rudimentaria voz: Zira leyendo español, afinada por remuestreo."""
    P.muestra(afinar(texto, midi, 'zira', largo=dur, tartamudeo=tartamudeo), t0, g, pan)


def telemetria(P, t0, texto, largo16=1 / 2, f=1760, vel=1.0, pan=0.4):
    """Pitidos de la sonda: los bits ASCII del texto, un 32avo cada uno; suena el 1."""
    bits = ''.join(f'{ord(c):08b}' for c in texto)
    paso = T / 16 * largo16
    for i, b in enumerate(bits):
        if b == '1':
            for n, amp in ((1, 1.0), (3, 0.33), (5, 0.2)):
                P.modo(f * n, 0.05 * vel * amp, t0 + i * paso, 30, ataque=3000, suelta=paso * 0.8, ar=200, pan=pan)
    return len(bits) * paso


def estatica(P, cols, nivel=1.0, lo=250, hi=5200, semilla=3):
    """Estática de radio escrita directo en la imagen: magnitud de Rayleigh en una banda y fase
    nueva cada columna (por eso cruje en cada raya: es radio)."""
    r = np.random.default_rng(semilla)
    k = np.arange(H) * F
    banda = np.exp(-0.5 * (np.log(np.maximum(k, 1) / math.sqrt(lo * hi)) / (math.log(hi / lo) / 3.2)) ** 2)
    for c, v in zip(cols, np.broadcast_to(nivel, len(cols))):
        for _ in range(1):
            mag = banda * r.rayleigh(1, H) * 2e-3 * v
            zl = mag * np.exp(1j * r.uniform(-np.pi, np.pi, H))
            zr = mag * np.exp(1j * r.uniform(-np.pi, np.pi, H))
            P.columna(c, zl, zr)


def chisporroteo(P, t0, t1, densidad=12, g=0.25, semilla=5):
    """Crujidos sueltos (muestras de unos cuantos samples) entre t0 y t1."""
    r = np.random.default_rng(semilla)
    for t in np.sort(r.uniform(t0, t1, int(densidad * (t1 - t0)))):
        w = r.normal(0, 1, int(S * 0.0015)) * np.hanning(int(S * 0.0015))
        P.muestra(w, t, g * r.uniform(.3, 1), pan=r.uniform(-.7, .7))


def kalimba(P, midi, t0, vel, pan=0.0):
    f = M.hz(midi)
    for mult, amp, a in ((1, 1.0, 2.4), (2.0, 0.05, 6), (5.93, 0.22, 14), (9.1, 0.05, 26)):
        P.modo(f * mult, 0.12 * vel * amp, t0, a, ataque=3000, pan=pan, fase=rng.uniform(0, 6.28))


def organo(P, midi, t0, dur, vel, pan=0.0):
    """Órgano cósmico (Sun Ra): registros 16'-8'-5⅓'-4'-2⅔'-2' y dos copias que baten más rápido
    entre más agudo el armónico (un Leslie hecho de batimientos)."""
    f = M.hz(midi)
    for n, amp in ((1, 1.0), (2, 0.8), (3, 0.5), (4, 0.4), (6, 0.25), (8, 0.2)):
        for det, p in ((-1, pan - 0.4), (1, pan + 0.4)):
            P.modo(n * f + det * 0.9 * n, 0.018 * vel * amp, t0, 0.06, ataque=45, suelta=dur, ar=7,
                   pan=max(-1, min(1, p)), fase=rng.uniform(0, 6.28))


def vocal(txt, voz='sabina'):
    """Envolvente espectral de la vocal (tramo más sonoro, suavizada a 1.6× el tono)."""
    from scipy.signal import butter, sosfilt
    x, tono = dicho(txt, voz)
    v = sosfilt(butter(4, [200, 1000], 'bandpass', fs=S, output='sos'), x)
    L = min(int(0.08 * S), len(x)); e = np.convolve(v * v, np.ones(L), 'valid')
    i0 = int(np.argmax(e)); seg = x[i0:i0 + L] * np.hanning(L)
    X = np.abs(np.fft.rfft(seg, 1 << 15)); fr = np.fft.rfftfreq(1 << 15, 1 / S)
    ancho = int(1.6 * tono / (fr[1] - fr[0]))
    X = np.convolve(X, np.ones(ancho) / ancho, 'same'); X /= X.max()
    return lambda f: float(np.interp(f, fr, X))


def coro(P, acorde, t0, dur, vel, env, pan=0.0):
    """Un acorde que dice una vocal (el de Esquinas)."""
    for i, n in enumerate(acorde): E.coro_vocal(P, n, t0, dur, vel, env, pan=pan - 0.3 + 0.2 * i)


# ───────────── armonía del laberinto ─────────────
def acorde(raiz_la0, menor, registro=57):
    """Tríada del laberinto (raíz en semitonos desde La) con su color: menor → m9, mayor → maj9.
    Voicing cerrado alrededor de `registro` y bajo aparte."""
    r = 45 + raiz_la0 % 12                       # La2 = 45
    tonos = [0, 3, 7, 10, 14] if menor else [0, 4, 7, 11, 14]
    voces = sorted(((r + t - registro) % 12) + registro for t in tonos[1:])
    bajo = r - 12 if r - 12 >= 33 else r
    return bajo, voces


BARNSLEY = [(0, 0, 0, .16, 0, 0, .01), (.85, .04, -.04, .85, 0, 1.6, .85), (.2, -.26, .23, .22, 0, 1.6, .07),
            (-.15, .28, .26, .24, 0, .44, .07)]


def helecho(P, t0, compases, notas, puntos=420, crece=.78, semilla=1015, vel=.8):
    """El helecho escribe su partitura: cada punto del IFS de Barnsley es una campanita.
    y (0..10) → nota de `notas` (de grave a agudo), x → paneo. La densidad crece como crece la
    planta; al llegar a `crece` del tiempo deja de brotar y lo que queda se apaga (muere).
    Devuelve los eventos (t, nota, pan) para dibujarlos."""
    r = np.random.default_rng(semilla)
    p = np.cumsum([a[6] for a in BARNSLEY])
    x = y = 0.0
    for _ in range(20):                                   # descartar el arranque del IFS
        a, b, c, d, e, f, _p = BARNSLEY[np.searchsorted(p, r.uniform(0, 1))]
        x, y = a * x + b * y + e, c * x + d * y + f
    dur = compases * T * crece
    ev = []
    for i in range(puntos):
        a, b, c, d, e, f, _p = BARNSLEY[np.searchsorted(p, r.uniform(0, 1))]
        x, y = a * x + b * y + e, c * x + d * y + f
        t = t0 + dur * math.sqrt((i + r.uniform(0, 1)) / puntos)      # cada vez más denso
        n = notas[min(len(notas) - 1, int(y / 10.01 * len(notas)))]
        pan = max(-1, min(1, (x - 0.25) / 2.4))
        E.campana(P, n, t, vel * r.uniform(.35, 1), pan=pan)
        ev.append((t, n, pan))
    return ev


# ───────────── paleta oscura (loop B.2: «no jazz-pop de boutique») ─────────────
def acorde_oscuro(raiz_la0, menor):
    """Tríada del laberinto vestida oscura: raíz y quinta graves, la tercera aislada arriba y un
    grano de segunda menor pegado a una nota del acorde (♭9 en los menores, ♭6 en los mayores)."""
    bajo = 33 + raiz_la0 % 12                          # La1 … Sol#2
    tercera = 3 if menor else 4
    voces = [bajo + 12, bajo + 19, bajo + 24 + tercera, bajo + 25 if menor else bajo + 20]
    return bajo, sorted(voces)


def preparado(P, midi, t0, vel, pan=0.0):
    """Piano preparado: parciales inarmónicos (un tornillo entre las cuerdas), golpe seco y apagado."""
    f = M.hz(midi)
    for mult, amp, a in ((1, 1.0, 7), (2.32, .45, 12), (3.87, .3, 17), (5.43, .17, 24), (7.1, .09, 32)):
        P.modo(f * mult, 0.15 * vel * amp, t0, a, ataque=1800, pan=pan, fase=rng.uniform(0, 6.28))


def subbombo(P, t0, vel):
    P.modo(46, 1.0 * vel, t0, 4.2, ataque=500)
    P.modo(71, 0.25 * vel, t0, 16, ataque=700)
    for f in (900, 1400, 2100): P.modo(f, 0.012 * vel, t0, 160, fase=rng.uniform(0, 6.28))


def placa(P, t0, vel, pan=0.15):
    """Placa de metal grave (en vez de clap): modos inarmónicos de una placa, largos y oscuros."""
    for f, amp, a in ((183, 1, 7), (417, .7, 9), (689, .5, 11), (1131, .35, 14), (1702, .2, 18), (2389, .1, 24)):
        P.modo(f * (1 + rng.normal(0, .002)), 0.07 * vel * amp, t0, a, ataque=2500, pan=pan, fase=rng.uniform(0, 6.28))


MODOS_POLVO = np.exp(np.random.default_rng(77).uniform(math.log(2500), math.log(8000), 30))
def polvo(P, t0, vel, pan=-0.35):
    """Hat apagado: menos aire, más polvo."""
    for f in MODOS_POLVO:
        P.modo(f, 0.014 * vel, t0, 70 * rng.uniform(.8, 1.2), ataque=5000, pan=pan, fase=rng.uniform(0, 6.28))


def vidrio(P, midi, t0, vel, pan=0.0, dur=1.2):
    """Vidrio frotado: el arco entra despacio (ataque lento) y el vidrio sigue sonando."""
    f = M.hz(midi)
    for mult, amp, a in ((1, 1.0, 1.0), (2.01, .28, 1.8), (3.03, .1, 3.0), (4.62, .05, 5.0)):
        P.modo(f * mult, 0.05 * vel * amp, t0, a, ataque=5.5, suelta=dur, ar=2.2, pan=pan, fase=rng.uniform(0, 6.28))


def helecho_oscuro(P, t0, compases, notas, puntos=170, crece=.78, semilla=1015, vel=.8):
    """El mismo helecho (cada punto del IFS escribe una nota), ahora en vidrio frotado."""
    r = np.random.default_rng(semilla)
    p = np.cumsum([a[6] for a in BARNSLEY]); x = y = 0.0
    for _ in range(20):
        a, b, c, d, e, f, _p = BARNSLEY[np.searchsorted(p, r.uniform(0, 1))]; x, y = a * x + b * y + e, c * x + d * y + f
    dur = compases * T * crece; ev = []
    for i in range(puntos):
        a, b, c, d, e, f, _p = BARNSLEY[np.searchsorted(p, r.uniform(0, 1))]; x, y = a * x + b * y + e, c * x + d * y + f
        t = t0 + dur * math.sqrt((i + r.uniform(0, 1)) / puntos)
        n = notas[min(len(notas) - 1, int(y / 10.01 * len(notas)))]
        pan = max(-1, min(1, (x - 0.25) / 2.4))
        vidrio(P, n, t, vel * r.uniform(.35, 1), pan=pan, dur=r.uniform(.5, 1.6))
        ev.append((t, n, pan))
    return ev


def cantar_con(P, texto, notas, pos16, dur16, t0, voz='sabina', g=1.0, pan=0.0, transporte=0):
    """`cantar` con otra voz de la cantante (Zira también canta: la voz magnética)."""
    vieja_voz, viejo_cache = K.VOZ, K.CACHE
    K.VOZ = {'sabina': 'Microsoft Sabina Desktop', 'zira': 'Microsoft Zira Desktop'}[voz]
    K.CACHE = viejo_cache.parent / f'tts-cantante-{voz}'
    try:
        return cantar(P, texto, [n + transporte for n in notas], pos16, dur16, t0, g, pan)
    finally:
        K.VOZ, K.CACHE = vieja_voz, viejo_cache


# ───────────── pared espectral (loop E: «acordes súper contemporáneos, pared de sonidos armónicos») ─────────────
def fundamental_virtual(raiz_la0, menor):
    """El acorde como espectro: mayor = armónicos 4:5:6 (fundamental dos octavas bajo la raíz);
    menor = 10:12:15 (fundamental 3⅓ octavas bajo la raíz). Raíz en el registro La2–Sol#3."""
    raiz = M.hz(45 + raiz_la0 % 12)
    return (raiz / 4, 4) if not menor else (raiz * 2 / 10, 10)


def pared_espectral(P, raiz_la0, menor, t0, dur, vel=1.0, estira=0.0, lo=105, hi=4000, semilla=0, pan=0.0,
                    escalonado=0.55):
    """Pared de parciales de la fundamental virtual del acorde. Entran de grave a agudo (escalonado,
    en segundos), cada uno con su respiración; arriba del armónico 24 sólo uno de cada dos.
    `estira` > 0 abre la serie (f_n = f0·n^(1+estira)): la pared se vuelve metálica (Murail)."""
    r = np.random.default_rng(semilla)
    f0, n0 = fundamental_virtual(raiz_la0, menor)
    parciales = [n for n in range(1, 80) if lo <= f0 * n <= hi and (n <= 24 or n % 2 == 0)]
    if not parciales: return 0
    nmin, nmax = parciales[0], parciales[-1]
    for n in parciales:
        f = f0 * n ** (1 + estira)
        u = (n - nmin) / max(1, nmax - nmin)                     # 0 grave … 1 agudo
        acorde = n in (n0, n0 * 5 // 4 if not menor else 12, n0 * 3 // 2 if not menor else 15) or \
                 any(n == k * m for k in (2, 4) for m in ((n0, n0 * 5 // 4, n0 * 3 // 2) if not menor else (10, 12, 15)))
        amp = 0.016 * vel * (1.6 if acorde else 1.0) / (1 + (f0 * n / 700) ** 1.4) * 2.2 * r.uniform(.7, 1.15)   # caída suave, sin techo duro
        ataque = 2.2 + 6 * r.uniform()                           # oleada, no golpe
        a = 0.35 + 1.4 * u                                       # los agudos se apagan antes
        P.modo(f, amp, t0 + escalonado * u + r.uniform(0, .08), a, ataque=ataque, suelta=dur, ar=1.6 + 2 * u,
               pan=max(-1, min(1, pan + (u - .5) * 1.4 * (1 if n % 2 else -1))), fase=r.uniform(0, 6.28))
    return len(parciales)
