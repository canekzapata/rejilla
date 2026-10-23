"""Motor de «la máquina del tiempo»: la rejilla a 103.125 bpm (S = 56320, la fila 128 es La1).

Tres clases de cosas:
  · la PORTADORA y su groove se escriben directo en la imagen (bandas laterales con fase);
  · los instrumentos se sintetizan en el tiempo (a S) y entran por la rejilla como DFT exacta
    por columna (Pista.muestra), para que el MEDIO los pueda tocar después;
  · el medio: funciones sobre la imagen (envejecer, teléfono, quitar el tiempo, desenfocar,
    congelar) y, después de la rejilla, la sala afinada y los planos de profundidad.
Ver TEXTURAS.md: ningún sonido entra crudo.
"""
import math, sys
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfiltfilt, hilbert, fftconvolve

AQUI = Path(__file__).parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / 'pixeles'))
import motor as PM                      # (fija 98 bpm al importarse: hay que volver a fijar abajo)
import instrumentos as PI               # cantar() y silabear() de los pixeles (la cantante de yoshi 16)
import musica as M

BPM = 103.125
M.fijar_tempo(BPM)
S, T, N, H = M.S, M.T, M.N, M.H
assert S == 56320 and N == 2 * H
SR_OUT = 48000
LA = 55.0
FILA = S / N                            # 0.4297 Hz: una vez por compás
SEM = 1031
Pista = PM.Pista
q = lambda b, pos=0: b * T + pos * T / 16
SIL = PI.SIL


def suave(u):
    u = np.clip(u, 0, 1); return u * u * u * (u * (6 * u - 15) + 10)


# ═════════════ la portadora y su groove ═════════════
# patrones por dieciseisavo (0..15): golpe → fuerza
GROOVE_A = {'bajo': {0: 1, 3: .55, 6: .45, 10: .75, 13: .4, 14: .6},
            'medio': {4: 1, 12: 1, 11: .25, 15: .2},
            'alto': {i: .3 + .35 * (i % 2 == 0) + .2 * (i % 4 == 2) for i in range(16)}}
GROOVE_B = {'bajo': {0: 1, 2: .35, 5: .6, 8: .5, 9: .7, 12: .35, 15: .55},     # el de los últimos 7 s
            'medio': {3: .9, 11: 1, 7: .3},
            'alto': {i: .25 + .45 * (i % 3 == 0) for i in range(16)}}       # 3 contra 4
TAU = {'bajo': .17, 'medio': .075, 'alto': .03}
LADOS = {'bajo': 24, 'medio': 44, 'alto': 60}      # cuántas bandas laterales: la dureza del ataque
PESOS = {.5: .55, 1: 1.0, 2: .8, 3: .42, 4: .5, 5: .28, 6: .3, 7: .4, 8: .2, 10: .19, 11: .17, 12: .17,
         13: .14, 14: .19, 16: .08, 19: .13, 21: .06, 22: .07, 26: .05, 28: .05, 33: .035, 38: .04, 44: .025, 52: .02,
         61: .014, 70: .012, 83: .009, 97: .007}
BANDA = lambda n: 'bajo' if n <= 3 else ('medio' if n <= 14 else 'alto')
ROT = {n: (5 + 3.7 * (i % 5), np.random.default_rng(SEM + i).uniform(0, 2 * np.pi)) for i, n in enumerate(PESOS)}


def envolvente(golpes, tau, swing=0.0, lados=60, n=8192):
    """Un compás de envolvente periódica → c_0..c_lados (los dieciseisavos impares se atrasan `swing`)."""
    t = np.arange(n) / n * T; e = np.zeros(n)
    for paso, g in golpes.items():
        p = paso + (swing if paso % 2 else 0)
        d = (t - p * T / 16) % T
        e += g * np.exp(-d / tau) * (1 - np.exp(-d / .0035))
    return np.fft.rfft(e)[:lados + 1] / n


def portadora(C, plan, semilla=SEM):
    """Escribe la portadora columna por columna. plan(b) → dict con:
       groove (0..1), mezcla (0 = A, 1 = B), coher {banda: 0..1}, swing, halo (0..1),
       latido (0..1), timbre (0..1: cuánto respiran los parciales), mute (silencio total),
       solo_portadora (sin bandas: un hueco en la transmisión), extra {n: a} (p. ej. el ⌖)."""
    rng = np.random.default_rng(semilla)
    fase = {n: rng.uniform(0, 2 * np.pi) for n in list(PESOS) + [23, 29, 31]}
    rho = {(n, o): rng.uniform(-np.pi, np.pi, 61) for n in list(PESOS) + [23, 29, 31] for o in (0, 1)}
    deriva = {(n, o): rng.normal(0, .25, 61) for n in PESOS for o in (0, 1)}
    halo_f = rng.uniform(0, 2 * np.pi, (C + 1, len(PESOS), 6))
    cache = {}
    Z = [np.zeros((C, H), complex), np.zeros((C, H), complex)]
    for b in range(C):
        p = plan(b)
        if p.get('mute'): continue
        sw = round(p.get('swing', 0), 3)
        for o in (0, 1):
            z = Z[o][b]
            for i, (n, a) in enumerate(list(PESOS.items()) + list(p.get('extra', {}).items())):
                k0 = int(round(128 * n))
                per, ph = ROT.get(n, (9, 0))
                a = a * (1 + p.get('timbre', .5) * .45 * math.sin(2 * math.pi * b / per + ph))
                bd = BANDA(n); L_ = LADOS[bd]
                if p.get('solo_portadora') or p.get('groove', 1) == 0 or n not in PESOS:
                    lat = np.zeros(L_ + 1, complex); lat[0] = 1
                else:
                    clave = (bd, sw)
                    if clave not in cache:
                        cache[clave] = (envolvente(GROOVE_A[bd], TAU[bd], sw, L_), envolvente(GROOVE_B[bd], TAU[bd], sw, L_))
                    cA, cB = cache[clave]
                    mz = p.get('mezcla', 0)
                    c = (1 - mz) * cA / abs(cA[0]) + mz * cB / abs(cB[0])
                    lat = c.copy(); lat[1:] *= p.get('groove', 1)
                    coh = p.get('coher', {}).get(bd, 1)
                    r = rho[(n, o if bd != 'bajo' else 0)][:L_ + 1] + deriva[(n, o if bd != 'bajo' else 0)][:L_ + 1] * b
                    lat = lat * np.exp(1j * (1 - coh) * r)
                    lat = lat / abs(lat[0])
                full = np.concatenate([np.conj(lat[:0:-1]), lat])
                lo = k0 - L_
                z[lo:k0 + L_ + 1] += a * np.exp(1j * fase[n]) * full
                if n in PESOS and p.get('halo', 0):                     # Scelsi: la nota difiere de sí misma
                    for j, d in enumerate((-3, -2, -1, 1, 2, 3)):
                        z[k0 + d] += a * p['halo'] * .09 / abs(d) ** .5 * np.exp(1j * halo_f[b, i, j])
            if p.get('latido', 0):                                       # la antena: un batido por compás
                z[129] += p['latido'] * .5 * np.exp(1j * fase[1])
    return Z[0], Z[1]


def chispa(C, plan, semilla=SEM):
    """El grano del brillo: ruido afinado (dientes en La, anchos) × la envolvente del brillo del groove,
    con el mismo swing y un enfoque que la suaviza cuando baja la coherencia. Estéreo (2, n) a S."""
    rng = np.random.default_rng(semilla + 7)
    n = int(C * T * S); out = np.zeros((2, n)); m = int(T * S)
    for o in (0, 1):
        nz = ruido_afinado(n, 18, semilla + 11 + o, hasta=15000, inclina=2)
        nz = sosfiltfilt(butter(3, 2800, 'highpass', fs=S, output='sos'), nz)
        for b in range(C):
            p = plan(b)
            if p.get('mute') or p.get('solo_portadora') or not p.get('groove', 1): continue
            mz = p.get('mezcla', 0); sw = p.get('swing', 0)
            t = np.arange(m) / S; e = np.zeros(m)
            for patron, w in ((GROOVE_A['alto'], 1 - mz), (GROOVE_B['alto'], mz)):
                for paso, g in patron.items():
                    pp = paso + (sw if paso % 2 else 0)
                    d = (t - pp * T / 16) % T
                    e += w * g ** 1.6 * np.exp(-d / .022) * (1 - np.exp(-d / .0012))
            coh = p.get('coher', {}).get('alto', 1)
            k = int((1 - coh) * .09 * S) + 1
            if k > 1: e = np.convolve(np.concatenate([e[-k:], e, e[:k]]), np.ones(k) / k, 'same')[k:-k]
            out[o, b * m:(b + 1) * m] = nz[b * m:(b + 1) * m] * e * p.get('groove', 1)
    return out / (np.abs(out).max() + 1e-12)


# ═════════════ el medio: gestos sobre la imagen ═════════════
HZ = np.arange(H) * FILA


def envejecer(Z, n, semilla=0):
    """Pasar n veces por el medio: fase revuelta (más arriba), magnitud cuantizada, banda que se angosta."""
    if n <= 0: return Z
    rng = np.random.default_rng(semilla)
    Z = Z.copy()
    for g in range(int(n)):
        peso = np.clip(HZ / 3000, .05, 1.5)
        Z = Z * np.exp(1j * rng.normal(0, .5, Z.shape) * peso)
        mag = np.abs(Z); mx = mag.max() + 1e-12
        db = 20 * np.log10(mag / mx + 1e-9); paso = 1.5 + 1.2 * g
        db = np.round(db / paso) * paso
        Z = np.where(db > -66 + 3 * g, mx * 10 ** (db / 20), 0) * np.exp(1j * np.angle(Z))
        lo, hi = 90 * 1.3 ** (g + 1), 9000 / 1.4 ** (g + 1)
        Z = Z * (1 / (1 + (lo / (HZ + 1)) ** 4)) * (1 / (1 + (HZ / hi) ** 4))
    return Z


def telefono(Z, cuanto=1.0, centro=1000.0, octavas=1.3):
    """La banda de 1 kHz de Eshun («desde años luz»); cuanto ∈ [0,1] por columna o escalar."""
    g = np.exp(-.5 * (np.log2((HZ + 1) / centro) / (octavas / 2)) ** 2) * 1.6
    cu = np.broadcast_to(np.asarray(cuanto, float).reshape(-1, 1) if np.ndim(cuanto) else cuanto, (Z.shape[0], 1))
    return Z * ((1 - cu) + cu * g[None, :])


def quitar_tiempo(Z, coher, semilla=0):
    """Misma magnitud, fase revuelta según 1 - coherencia (por columna)."""
    rng = np.random.default_rng(semilla)
    co = np.asarray(coher, float).reshape(-1, 1)
    return Z * np.exp(1j * (1 - co) * rng.uniform(-np.pi, np.pi, Z.shape))


def desenfocar(Z, anchos_hz, semilla=0):
    """Desenfoque a lo largo de las filas (por columna, ancho en Hz) + fase al azar en lo desenfocado."""
    rng = np.random.default_rng(semilla); Z = Z.copy()
    for c, w in enumerate(list(anchos_hz)[:Z.shape[0]]):
        if w <= FILA: continue
        s = w / FILA; k = np.exp(-.5 * (np.arange(-int(4 * s), int(4 * s) + 1) / s) ** 2); k /= k.sum()
        mag = np.sqrt(np.convolve(np.abs(Z[c]) ** 2, k, 'same'))
        mezcla = min(1, w / 60)
        ph = np.angle(Z[c]) + mezcla * rng.uniform(-np.pi, np.pi, H)
        Z[c] = mag * np.exp(1j * ph)
    return Z


def congelar(Z, col, hasta, cae=.7, semilla=0):
    """La magnitud de una columna se queda flotando en las siguientes, con fase nueva y cayendo."""
    rng = np.random.default_rng(semilla); Z = Z.copy(); m = np.abs(Z[col])
    for i, c in enumerate(range(col + 1, hasta)):
        Z[c] += m * cae ** (i + 1) * np.exp(1j * rng.uniform(-np.pi, np.pi, H))
    return Z


# ═════════════ instrumentos en el tiempo (a S) ═════════════
def ruido_afinado(n, ancho=6.0, semilla=0, hasta=9000, inclina=-3.0):
    """Ruido que pasa por un peine en La: con dientes angostos es casi la nota, anchos es soplo."""
    rng = np.random.default_rng(semilla)
    X = np.fft.rfft(rng.normal(0, 1, n)); f = np.fft.rfftfreq(n, 1 / S)
    k = np.round(f / LA); d = f - k * LA
    peine = np.exp(-.5 * (d / ancho) ** 2) * (k >= 1) * (f < hasta) * (f / 1000 + .05) ** (inclina / 6)
    y = np.fft.irfft(X * peine, n)
    return y / (np.abs(y).max() + 1e-12)


def envolvente_de(y, ms=8, sr=S):
    e = np.abs(hilbert(y)); k = max(1, int(ms / 1000 * sr))
    return np.convolve(e, np.ones(k) / k, 'same')


def voz_portadora(y, bandas=22, semilla=0, parciales_max=90):
    """Vocoder de canales cuyas portadoras son los parciales del La: la portadora dice las vocales."""
    rng = np.random.default_rng(semilla)
    t = np.arange(len(y)) / S; out = np.zeros(len(y))
    bordes = np.geomspace(110, 5200, bandas + 1)
    for lo, hi in zip(bordes, bordes[1:]):
        e = envolvente_de(sosfiltfilt(butter(3, [lo, hi], 'bandpass', fs=S, output='sos'), y), 9)
        ns = [n for n in range(1, parciales_max) if lo <= n * LA < hi]
        if not ns: continue
        car = sum(np.sin(2 * np.pi * n * LA * t + rng.uniform(0, 6.3)) for n in ns) / math.sqrt(len(ns))
        out += e * car
    return out / (np.abs(out).max() + 1e-12) * np.abs(y).max()


def aire(y, cuanto=.35, semilla=0):
    """El aliento de la voz, encasillado: ruido afinado ancho × envolvente de lo agudo de la voz."""
    e = envolvente_de(sosfiltfilt(butter(4, 3800, 'highpass', fs=S, output='sos'), y), 5)
    r = sosfiltfilt(butter(2, 3000, 'highpass', fs=S, output='sos'), ruido_afinado(len(y), 22, semilla, hasta=14000, inclina=0))
    return y + cuanto * r * e / (e.max() + 1e-12) * np.abs(y).max()


def bajo_elastico(notas, largo, semilla=0):
    """El ectoplasma de Bootsy. notas: (t0, dur, midi, midi_desde, glis_s, vel). Fase continua (glissa),
    formante que abre con cada ataque (squelch) y saturación suave."""
    n = int(largo * S); t = np.arange(n) / S
    f = np.full(n, np.nan); amp = np.zeros(n); abre = np.zeros(n)
    for t0, dur, midi, desde, glis, vel in notas:
        a, z = int(t0 * S), min(n, int((t0 + dur) * S))
        if a >= n: continue
        tt = t[a:z] - t0
        m = midi + (desde - midi) * np.exp(-tt / max(glis, 1e-3) * 3) if desde is not None else np.full(len(tt), midi)
        f[a:z] = 440 * 2 ** ((m - 69) / 12)
        env = (1 - np.exp(-tt / .006)) * np.exp(-tt / (dur * .9 + .05))
        rel = np.clip((dur - tt) / .03, 0, 1)
        amp[a:z] = np.maximum(amp[a:z], vel * env * rel)
        abre[a:z] = np.maximum(abre[a:z], vel * np.exp(-tt / .09))
    f = np.interp(t, t[~np.isnan(f)], f[~np.isnan(f)]) if (~np.isnan(f)).any() else np.full(n, 55.0)
    fase = 2 * np.pi * np.cumsum(f) / S
    y = np.zeros(n)
    centro = 180 + 1400 * abre                                       # el formante: de 180 Hz a 1.6 kHz
    for k in range(1, 16):
        fk = k * f
        g = (1 / k ** .8) * (1 + 2.5 * np.exp(-.5 * (np.log2(fk / centro) / .45) ** 2))
        y += g * np.sin(k * fase) * (fk < 6000)
    y = np.tanh(1.6 * y * amp) * .8
    return y


def morse(texto, olvido, punto=None, parciales=(16, 19, 24), semilla=0):
    """Morse con los parciales agudos de la portadora. olvido 0 → código; 1 → ritmo sin código."""
    TAB = {'a': '.-', 'b': '-...', 'c': '-.-.', 'd': '-..', 'e': '.', 'f': '..-.', 'g': '--.', 'h': '....', 'i': '..',
           'j': '.---', 'l': '.-..', 'm': '--', 'n': '-.', 'o': '---', 'p': '.--.', 'q': '--.-', 'r': '.-.', 's': '...',
           't': '-', 'u': '..-', 'v': '...-', 'x': '-..-', 'y': '-.--', 'z': '--..'}
    rng = np.random.default_rng(semilla)
    punto = punto or T / 16
    eventos, t = [], 0.0
    simbolos = [(s, li) for li, letra in enumerate(texto) for s in (TAB.get(letra, '') + ' ')]
    for i, (s, _) in enumerate(simbolos):
        o = olvido(i / len(simbolos))
        if s == ' ': t += punto * (2 + o * rng.uniform(-1.5, 2)); continue
        d = (1 if s == '.' else 3) * punto
        d = (1 - o) * d + o * 2 * punto * rng.uniform(.6, 1.4)
        eventos.append((t, d)); t += d + punto * (1 + o * rng.uniform(-.5, 1.5))
    n = int((t + .5) * S); tt = np.arange(n) / S; y = np.zeros(n)
    car = sum(np.sin(2 * np.pi * k * LA * tt + rng.uniform(0, 6.3)) / (1 + .2 * j) for j, k in enumerate(parciales))
    for t0, d in eventos:
        a, z = int(t0 * S), int((t0 + d) * S); L_ = z - a; r = min(L_ // 2, int(.004 * S))
        e = np.ones(L_); e[:r] = np.linspace(0, 1, r); e[-r:] = np.linspace(1, 0, r)
        y[a:z] += car[a:z] * e
    return y / (np.abs(y).max() + 1e-12)


def tierra(texto, semilla=0, tomas=(-1, 0, 1)):
    """El coro de la Tierra: tres tomas de Zira desfasadas + una Sabina hablada bajito. Estéreo (2, n) a S."""
    rng = np.random.default_rng(semilla)
    capas = []
    for i, rap in enumerate(tomas):
        y = PM.tts(texto, 'zira', rap, sr=S)
        capas.append((y, int(rng.uniform(.02, .06) * S * (i > 0)), rng.uniform(-.6, .6), 1.0 if rap == 0 else .62))
    y = PM.tts(texto, 'sabina', -1, sr=S)
    capas.append((y, int(.035 * S), rng.uniform(-.2, .2), .2))
    n = max(len(c[0]) + c[1] for c in capas)
    st = np.zeros((2, n))
    for y, d, pan, g in capas:
        gl, gr = M.paneo(pan); st[0, d:d + len(y)] += gl * g * y; st[1, d:d + len(y)] += gr * g * y
    return st / (np.abs(st).max() + 1e-12)


def palabra(texto, rapidez=4, voz='sabina'):
    y = PM.tts(texto, voz, rapidez, sr=S)
    k = min(len(y) // 4, int(.004 * S)); y = y.copy(); y[:k] *= np.linspace(0, 1, k); y[-k:] *= np.linspace(1, 0, k)
    return y


# ═════════════ la nave canta (melodía nómada en la escala de la portadora) ═════════════
ESCALA = [57, 60 - .025, 62 - .02, 64 + .02, 67 - .31]           # La Do Re Mi Sol(7/4), MIDI fraccionario
GRADOS = [m + 12 * o for o in (-1, 0, 1) for m in ESCALA]


def nomada(n_sil, tonicas, semilla=0, desde=57.0, registro=(52, 72)):
    """Pasos de la escala; la tercera (salto de grado mayor) es un hoyo para acelerar; sin nota meta:
    las dos últimas sílabas bajan y se dispersan."""
    rng = np.random.default_rng(semilla)
    g = [abs(x - desde) for x in GRADOS]; i = int(np.argmin(g)); out = []
    for k in range(n_sil):
        paso = rng.choice([-1, 1, 1, -1, 2, -2, 0], p=[.24, .24, .14, .1, .1, .08, .1])
        if k in tonicas and rng.random() < .5: paso = 2 if GRADOS[i] < np.mean(registro) else -2
        i = int(np.clip(i + paso, 0, len(GRADOS) - 1))
        while GRADOS[i] < registro[0]: i += 1
        while GRADOS[i] > registro[1]: i -= 1
        out.append(GRADOS[i])
    if n_sil >= 3:
        out[-1] = out[-2] - rng.choice([2, 3, 5]); out[-2] = min(out[-2], out[-3])
    return out


def ritmo_hablado(silabas_por_palabra, tonicas_glob, compases, semilla=0, holgura=.82):
    """Tónicas en dieciseisavos fuertes (a veces adelantadas), átonas corridas; cabe en `compases`."""
    rng = np.random.default_rng(semilla)
    n = sum(silabas_por_palabra); total = compases * 16 * holgura
    dur = np.array([2.0 if k in tonicas_glob else 1.0 for k in range(n)])
    dur[-1] = 3.5
    dur *= total / dur.sum()
    dur = np.maximum(np.round(dur * 2) / 2, .5)
    pos = np.concatenate([[0], np.cumsum(dur)[:-1]])
    pos = pos + rng.choice([0, 0, 0, -.5, .5], n) * (np.arange(n) > 0)
    return pos.tolist(), (dur * .95).tolist()


def cantar_nave(P, texto, t0, compases, semilla=0, desde=57.0, g=1.0, pan=0.0):
    sil, palabras = PI.silabear(texto)
    tonicas, k = set(), 0
    for p, nsil in zip(texto.replace('—', ' ').replace(',', ' ').split(), palabras):
        try: tonicas.add(k + SIL.tonica(p))
        except Exception: tonicas.add(k)
        k += nsil
    notas = nomada(len(sil), tonicas, semilla, desde)
    pos, dur = ritmo_hablado(palabras, tonicas, compases, semilla)
    return PI.cantar(P, texto, notas, pos, dur, t0, 'sabina', g, pan)


# ═════════════ después de la rejilla: espacio ═════════════
def sala_afinada(x, cola=2.6, afinado=.6, semilla=0, sr=SR_OUT, predelay=.012):
    """Reverb cuya cola resuena en La (Lucier). x estéreo (n, 2) → solo la cola, estéreo."""
    rng = np.random.default_rng(semilla); n = int(cola * sr)
    t = np.arange(n) / sr; out = np.zeros_like(x)
    for o in (0, 1):
        r = rng.normal(0, 1, n) * np.exp(-t * 6.9 / cola)
        R = np.fft.rfft(r); f = np.fft.rfftfreq(n, 1 / sr)
        k = np.round(f / LA); d = f - k * LA
        peine = np.exp(-.5 * (d / 3.5) ** 2) * (k >= 1)
        R = R * ((1 - afinado) + afinado * 3 * peine) * (1 / (1 + (f / 7000) ** 2))
        ir = np.fft.irfft(R, n); ir[:int(predelay * sr)] = 0; ir /= np.sqrt((ir ** 2).sum()) + 1e-12
        out[:, o] = fftconvolve(x[:, o], ir)[:len(x)]
    return out


PLANOS = {'cerca': (1.0, 0.0, .10, .6), 'medio': (.7, .012, .22, 1.0),
          'lejos': (.25, .04, .55, 1.3), 'telefono': (1.0, .02, .3, .2)}


def en_plano(x, plano, sr=SR_OUT, semilla=0):
    """x estéreo (n,2) → (seco, envío): brillo, pre-retraso, cuánto va a la sala, ancho."""
    brillo, pre, envio, ancho = PLANOS[plano]
    y = x.copy()
    if brillo < 1:
        lp = sosfiltfilt(butter(2, 3000 + 6000 * brillo, 'lowpass', fs=sr, output='sos'), y, axis=0)
        y = brillo * y + (1 - brillo) * lp
    if pre: y = np.concatenate([np.zeros((int(pre * sr), 2)), y])[:len(x)]
    mid, side = (y[:, 0] + y[:, 1]) / 2, (y[:, 0] - y[:, 1]) / 2
    y = np.stack([mid + ancho * side, mid - ancho * side], 1)
    return y * (1 - envio * .5), y * envio
