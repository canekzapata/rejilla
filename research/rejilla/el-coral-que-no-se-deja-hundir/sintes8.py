"""El coral que no se deja hundir — instrumentos propios (48 kHz).

  crecer_coral(...)      EL CORAL QUE CRECE: un corte vertical del arrecife. El plancton baja del agua iluminada (caminata
                         al azar con deriva hacia abajo) y se pega donde toca coral: agregación limitada por difusión (DLA),
                         ramas que suben hacia la luz. Devuelve las partículas en orden de llegada (x, y, padre).
  coral(parts, ...)      cada partícula es un MODO: su altura en el arrecife es su altura de tono (cuantizada al modo 3 de
                         Messiaen), su x es su lugar en el estéreo. Al pegarse hace un clic de piedra; luego resuena largo,
                         como una barra de caliza (parciales 1 y 2.76) y las olas la vuelven a excitar. Empieza como un clic,
                         termina como un órgano de cientos de modos. Los modos que caen en la misma nota se suman en un
                         oscilador por nota (con tres voces apenas desafinadas): barato, y así suena el órgano.
  volcan(...)            EL VOLCÁN QUE SE HUNDE: una garganta (fuente glotal + formantes que se oscurecen de «a» a «u») cuya
                         altura baja de verdad, sin parar, y un rumor de magma. Bajo el nivel del mar se apaga el brillo
                         (pasa bajos que baja con la profundidad). Al final se BORRA con la vuelta de 2π del Astrolabio
                         (reparto hermite): cada armónico m tiene una testigo y una viajera con fase −(m+½)θ; en θ = 2π se
                         anulan exactamente.
  olas(...)              LA OLA QUE SE PARTE EN EL ARRECIFE: una ola larga que entra a lo bajo se parte en N solitones de KdV
                         (κ = 1…N, como el sech² de amplitud N(N+1)); en la orilla llegan uno tras otro, el más alto primero.
                         Se calcula con resolver_solitones_kay_moses del Solitón de Toda–KdV (la copia de rejilla) en un punto
                         fijo (la orilla) mientras corre el tiempo de evolución τ. Cada solitón que llega revienta: ruido
                         filtrado con el perfil q(x_orilla, τ).
  boca_pajaro(ev, N)     LOS PÁJAROS DE BOCA (los músicos de Martin Denny imitaban aves con la boca): silbido humano con
                         soplo, trinos de lengua (modulación de 18–30 Hz), chasquidos de lengua y «uhú» de búho con la mano.
  laguna(f, curva, N)    el seiche de la laguna (la ola estacionaria que va y viene dentro del anillo), subido por octavas:
                         un dron de dos senos que respira a su propio periodo.
"""
import math, os, sys
import numpy as np
from scipy.signal import butter, sosfilt
SR = 48000
AQUI = os.path.dirname(os.path.abspath(__file__))
hz = lambda m: 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)
MODO3 = [0, 2, 3, 4, 6, 7, 8, 10, 11]                         # Messiaen, modo 3 (transposición limitada: 4)


def _pan(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def _bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)


# ═════════ el coral ═════════
def crecer_coral(W=120, H=80, n=900, base=None, semilla=0, deriva=.62):
    """DLA en un corte vertical (y = 0 abajo). base: alturas iniciales por columna (el flanco del volcán viejo).
    Las partículas nacen arriba de la copa actual y caminan con deriva hacia abajo (el plancton cae); se pegan al tocar."""
    rng = np.random.default_rng(semilla); G = np.zeros((W, H + 4), bool); padre_de = -np.ones((W, H + 4), int)
    base = np.zeros(W, int) if base is None else np.asarray(base, int)
    for x in range(W):
        G[x, :base[x] + 1] = True; padre_de[x, base[x]] = -1 - x       # el sustrato (padre negativo = roca)
    parts, top = [], int(base.max())
    for k in range(n):
        x, y = int(rng.integers(0, W)), min(H + 2, top + 6)
        for paso in range(20000):
            r = rng.random()
            if r < deriva: y -= 1
            elif r < deriva + (1 - deriva) * .45: x -= 1
            elif r < deriva + (1 - deriva) * .9: x += 1
            else: y += 1
            x %= W; y = min(max(y, 0), H + 2)
            vec = [(x, y - 1), ((x - 1) % W, y), ((x + 1) % W, y), ((x - 1) % W, y - 1), ((x + 1) % W, y - 1)]
            pegado = [(a, b) for a, b in vec if 0 <= b < H + 4 and G[a, b]]
            if pegado and y <= H:
                a, b = pegado[0]; G[x, y] = True; padre_de[x, y] = len(parts)
                parts.append((x, y, int(padre_de[a, b]))); top = max(top, y); break
        if top >= H: break
    return parts, base


def coral(parts, tiempos, W, H, f_bajo, f_alto, ton_midi, N, excita=None, semilla=0, clic=.5):
    """parts: [(x, y, padre)]; tiempos: cuándo se pega cada una. La altura y → tono (f_bajo en y=0, f_alto en y=H, log),
    cuantizada al modo 3 sobre la tónica. excita: envolvente (N/SR·200 muestras a 200 Hz) que vuelve a sonar al coral."""
    rng = np.random.default_rng(semilla); FR = 200; nfr = N * FR // SR + 2; tf = np.arange(nfr) / FR
    esc = sorted({ton_midi + 12 * o + g for o in range(-4, 6) for g in MODO3})
    def nota(y):
        m = 69 + 12 * math.log2(f_bajo * (f_alto / f_bajo) ** (y / H) / 440)
        return min(esc, key=lambda e: abs(e - m))
    notas, env, panes = {}, {}, {}
    exc = np.zeros(nfr) if excita is None else np.interp(tf, np.arange(len(excita)) / FR, excita)
    for (x, y, _), t in zip(parts, tiempos):
        m = nota(y); u = np.clip(tf - t, 0, None); on = tf >= t
        tau = 5.0 + 9.0 * (1 - y / H)                                   # lo hondo resuena más largo
        e = on * (np.exp(-u / tau) * .8 + .2 + .6 * exc) * np.minimum(1, u / .02)
        env[m] = env.get(m, 0) + e; panes.setdefault(m, []).append(2 * x / W - 1); notas[m] = notas.get(m, 0) + 1
    y = np.zeros((N, 2)); t = np.arange(N) / SR
    for m, e in env.items():
        f = float(hz(m)); a = np.interp(t, tf, e) / math.sqrt(notas[m] + 3)
        s = np.zeros(N)
        for det in (-.0015, 0, .0016):
            ph = rng.uniform(0, 2 * math.pi)
            s += np.sin(2 * math.pi * f * (1 + det) * t + ph) + .22 * np.sin(2 * math.pi * 2.756 * f * (1 + det) * t + 1.3 * ph)
        y += _pan(s * a / 3, float(np.clip(np.mean(panes[m]), -.9, .9)))
    clics = np.zeros((N, 2)); L = int(.03 * SR); tl = np.arange(L) / SR
    for (x, yy, _), tt in zip(parts, tiempos):                           # el clic de piedra al pegarse
        i = int(tt * SR)
        if i + L >= N: continue
        g = _bp(rng.standard_normal(L), 1800, 7000) * np.exp(-tl / .004) * clic * (.4 + .6 * rng.random())
        clics[i:i + L] += _pan(g, 2 * x / W - 1)
    return y / (np.abs(y).max() + 1e-12), clics / (np.abs(clics).max() + 1e-12), {'modos': len(parts), 'notas_distintas': len(notas)}


# ═════════ el volcán ═════════
VOC = {'a': (730, 1090, 2440), 'o': (470, 850, 2500), 'u': (350, 700, 2400)}


def volcan(f_t, prof_t, theta_t, vocal_t, N, semilla=0, rumor=.35):
    """f_t, prof_t, theta_t, vocal_t: curvas [[t, v]]. prof: metros bajo el mar (negativo = arriba del agua).
    vocal_t: 0 = «a», 1 = «o», 2 = «u». theta: el giro del Astrolabio (0 → 2π borra)."""
    rng = np.random.default_rng(semilla); t = np.arange(N) / SR
    cur = lambda c: np.interp(t, [a for a, _ in c], [b for _, b in c])
    f = cur(f_t) * (1 + .004 * np.sin(2 * np.pi * 4.6 * t) + .002 * np.sin(2 * np.pi * .23 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR; th = cur(theta_t); voc = cur(vocal_t)
    src = np.zeros(N)
    for m in range(1, 31):                                               # pulso glotal: 1/m^1.4, hasta 6 kHz
        ok = f * m < 6000
        if not ok.any(): break
        a = (1 / m ** 1.4) * ok
        testigo = np.sin(m * ph); viajera = np.sin(m * ph - (m - .5) * th)    # armónico m = modo de Hermite m−1: fase −(m−½)θ; en 2π, −1 para todos
        src += a * (testigo + viajera) * .5
    # formantes que se mueven de «a» a «u» (por bloques)
    out = np.zeros(N); B = 2048
    from scipy.signal import iirpeak, lfilter
    z = [np.zeros(2) for _ in range(3)]
    for i in range(0, N, B):
        j = min(N, i + B); v = float(voc[(i + j) // 2]); k0 = min(1, int(v)); w = v - k0
        fa = [VOC['aou'[k0]][q] * (1 - w) + VOC['aou'[min(2, k0 + 1)]][q] * w for q in range(3)]
        for q, (ff, g) in enumerate(zip(fa, (1, .55, .2))):
            b, a = iirpeak(ff, ff / (70 + 30 * q), fs=SR); yq, z[q] = lfilter(b, a, src[i:j], zi=z[q]); out[i:j] += g * yq
    rum = sosfilt(butter(2, [25, 220], 'band', fs=SR, output='sos'), rng.standard_normal(N)) * (1 + .6 * np.sin(2 * np.pi * .07 * t)) * rumor
    rum *= np.abs(np.cos(th / 4))                                        # el magma también se apaga con la vuelta
    y = out / (np.abs(out).max() + 1e-12) + rum / (np.abs(rum).max() + 1e-12) * rumor
    # el nivel del mar: bajo el agua se apaga el brillo (pasa bajos por bloques, de 7 kHz arriba del agua a 300 Hz hondo)
    p = cur(prof_t); res = np.zeros(N); zi = np.zeros((1, 2))
    for i in range(0, N, B):
        j = min(N, i + B); pp = float(p[(i + j) // 2]); fc = 7000 if pp <= 0 else max(300, 7000 * math.exp(-pp / 40))
        sos = butter(2, fc, 'low', fs=SR, output='sos'); res[i:j], zi = sosfilt(sos, y[i:j], zi=zi)
    return res / (np.abs(res).max() + 1e-12)


# ═════════ la ola que se parte ═════════
def _resolver():
    sys.path.insert(0, os.path.join(AQUI, '..', 'soliton-toda-kdv')); import soliton_toda_kdv as S
    return S.resolver_solitones_kay_moses


def ola(t0, n_sol, N, dur=3.0, x_orilla=6.0, semilla=0, brillo=1.0):
    """Una ola que se parte en n_sol solitones (κ = 1…n): se mira en la orilla x_orilla mientras τ corre de 0 a τ1.
    Devuelve (sonido estéreo de esa ola, perfil q en la orilla, tiempos de llegada de cada cresta)."""
    res = _resolver(); rng = np.random.default_rng(semilla)
    kap = np.arange(1, n_sol + 1, dtype=float); t0s = np.zeros(n_sol)
    tau1 = (x_orilla + 2.5) / (4 * 1.0 ** 2) * 1.05                      # hasta que llega el más lento
    FR = 400; n = int(dur * FR); taus = np.linspace(0, tau1, n)
    q = np.array([res(np.array([x_orilla]), kap, t0s, tau, 1.0)[0][:, 0].sum() for tau in taus])
    q = q / (q.max() + 1e-12)
    picos = [i for i in range(1, n - 1) if q[i] > q[i - 1] and q[i] >= q[i + 1] and q[i] > .05]
    L = int(dur * SR) + int(1.5 * SR); tt = np.arange(L) / SR; env = np.interp(tt, np.arange(n) / FR, q, right=0)
    rev = np.zeros(L)
    for i in picos:                                                     # cada cresta que llega revienta: espuma que se apaga
        a = int(i / FR * SR); k = np.arange(L - a) / SR; rev[a:] += q[i] * np.exp(-k / (.35 + .5 * q[i]))
    ruido = rng.standard_normal((L, 2))
    cuerpo = sosfilt(butter(2, [80, 900], 'band', fs=SR, output='sos'), ruido, axis=0) * env[:, None]
    espuma = sosfilt(butter(2, [900, 9000 * brillo], 'band', fs=SR, output='sos'), ruido, axis=0) * rev[:, None]
    y = cuerpo * .8 + espuma * .9; y[:, 1] = np.roll(y[:, 1], int(.008 * SR))
    out = np.zeros((N, 2)); a = int(t0 * SR); m = min(L, N - a)
    if m > 0: out[a:a + m] = y[:m]
    return out, q, [t0 + i / FR for i in picos]


# ═════════ pájaros de boca ═════════
def boca_pajaro(eventos, N, semilla=0):
    """eventos: {t, tipo: 'silbido'|'trino'|'chasquido'|'buho', m, m2, dur, v, pan}."""
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2))
    for e in eventos:
        i = int(e['t'] * SR); d = e.get('dur', .3); L = int((d + .15) * SR)
        if i + L >= N: continue
        t = np.arange(L) / SR; v = e.get('v', .6); u = np.clip(t / d, 0, 1)
        env = np.minimum(1, t / .015) * np.clip((d - t) / .04, 0, 1)
        if e['tipo'] in ('silbido', 'trino'):
            f = hz(e['m']) * (hz(e.get('m2', e['m'])) / hz(e['m'])) ** u * (1 + .006 * np.sin(2 * np.pi * 5.5 * t))
            g = np.sin(2 * np.pi * np.cumsum(f) / SR) + .04 * np.sin(4 * np.pi * np.cumsum(f) / SR)
            soplo = _bp(rng.standard_normal(L), 1500, 6000) * .06
            if e['tipo'] == 'trino': env = env * (.55 + .45 * np.sin(2 * np.pi * e.get('rate', 24) * t) ** 2)
            s = (g + soplo) * env
        elif e['tipo'] == 'chasquido':
            s = np.zeros(L)
            for k in range(e.get('n', 1)):
                a = int(k * e.get('cada', .09) * SR); n2 = min(L - a, int(.025 * SR))
                if n2 > 0: s[a:a + n2] += _bp(rng.standard_normal(n2), 1100, 2600) * np.exp(-np.arange(n2) / SR / .003)
        else:                                                           # «uhú»: hueco de las manos (dos senos graves con soplo)
            f = hz(e['m']) * (1 - .06 * u)
            s = (np.sin(2 * np.pi * np.cumsum(f) / SR) + .5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)) * env * np.exp(-u * .8)
            s += _bp(rng.standard_normal(L), 200, 900) * .05 * env
        y[i:i + L] += _pan(s * v, e.get('pan', 0))
    return y / (np.abs(y).max() + 1e-12)


# ═════════ la laguna ═════════
def laguna(f, curva, N, semilla=0):
    """el seiche de la laguna (subido por octavas): dos senos a f y 3f/2·2 con un batido de 0.2 Hz; respira a su periodo."""
    t = np.arange(N) / SR; a = np.interp(t, [x for x, _ in curva], [v for _, v in curva])
    y = (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 1.0023 * t + 1) + .25 * np.sin(2 * np.pi * 3 * f * t)) * a * (.8 + .2 * np.sin(2 * np.pi * t / 9.7))
    return np.stack([y, np.roll(y, int(.013 * SR))], 1) / 1.75
