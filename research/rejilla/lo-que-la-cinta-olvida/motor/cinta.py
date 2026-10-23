"""cinta.py — la cinta de meandro: un instrumento imposible para «Lo que la cinta olvida».

La banda del sonidero se escribe en TIEMPO DE CINTA τ y se toca en tiempo real t. La cinta corre a la velocidad con que el río
avanza valle abajo: en cada vuelta del meandro, v = (cuerda ÷ arco)^½. Donde el río se enreda, la cinta se arrastra (la cumbia
se rebaja: más lenta y más grave a la vez, como un disco a menos revoluciones); donde se endereza, corre.

  mapa(v_de_tau, T_tau)        → (tau, t): la relación entre los dos relojes, t(τ) = ∫ dτ / v(τ), en una rejilla de 1 kHz
  a_tiempo_real(t_de, tau)     → función que lleva un instante de cinta a tiempo real (para escribir la parte viva)
  tocar(x, mp, N, curv, sem)   la cinta suena: lee x (estéreo, en τ) en τ(t) con wow (la curvatura del río), flutter, pérdida de
                               agudos que crece al ir lento (la cabeza lee menos), saturación suave y siseo
  lago(y, t0, t1, fin, sem)    el lago de herradura: el tramo [t0, t1] de la salida se queda dando vueltas hasta `fin` y se
                               gasta en cada pasada (Basinski): el óxido se cae en huecos que se acumulan EN EL MISMO LUGAR del
                               loop, el filtro se cierra, la altura se desvía un poco y el nivel baja. Devuelve también las
                               medidas de cada pasada (nivel, fracción perdida, corte del filtro).
"""
import math
import numpy as np
from scipy.signal import butter, sosfiltfilt, sosfilt
SR = 48000


def mapa(v_de_tau, T_tau, FR=1000):
    tau = np.arange(int(T_tau * FR) + 1) / FR
    v = np.asarray([v_de_tau(x) for x in tau])
    t = np.concatenate([[0], np.cumsum(1 / v[:-1]) / FR])
    return tau, t, v


def a_tiempo_real(tau, t):
    return lambda x: float(np.interp(x, tau, t))


def _filtra_variable(x, corte):
    """pasabajas que cambia con el tiempo, sin clics: mezcla de cuatro versiones fijas (sin filtro, 8, 4 y 2 kHz) según el corte de cada muestra"""
    vers = np.stack([x] + [sosfiltfilt(butter(2, c, 'low', fs=SR, output='sos'), x, axis=0) for c in (8000, 4000, 2000)])
    p = np.clip(np.log2(16000 / np.maximum(corte, 1)), 0, 2.999); k = p.astype(int); f = (p - k)[:, None]; n = np.arange(len(x))
    return vers[k, n] * (1 - f) + vers[k + 1, n] * f


def tocar(x, mp, N, curv=None, semilla=0):
    """x: estéreo en tiempo de cinta (muestras a SR). mp = (tau, t, v). curv(t) ∈ [0,1]: curvatura del río (el wow)."""
    tau, tg, v = mp; rng = np.random.default_rng(semilla)
    t = np.arange(N) / SR; ta = np.interp(t, tg, tau)                               # τ(t)
    vt = np.interp(ta, tau, v)
    c = np.zeros(N) if curv is None else np.asarray([curv(s) for s in t[::480]]).repeat(480)[:N]
    wow = (.004 + .012 * c) * np.sin(2 * math.pi * .55 * t + 1.3 * np.sin(2 * math.pi * .13 * t))     # la vuelta tira de la cinta
    flutter = .0015 * np.sin(2 * math.pi * 6.3 * t) + .0008 * np.sin(2 * math.pi * 11.7 * t + 1)
    ta = ta + np.cumsum(vt * (wow + flutter)) / SR
    pos = np.clip(ta * SR, 0, len(x) - 2); i0 = pos.astype(int); f = (pos - i0)[:, None]
    y = x[i0] * (1 - f) + x[i0 + 1] * f
    y = _filtra_variable(y, 16000 * vt ** 1.6)                                       # la cabeza lee menos al ir lento
    y = np.tanh(1.4 * y / (np.abs(y).max() + 1e-12)) / math.tanh(1.4)               # saturación de cinta
    sis = sosfilt(butter(1, [1500, 9000], 'band', fs=SR, output='sos'), rng.standard_normal((N, 2)), axis=0) * 10 ** (-48 / 20)
    return y + sis, vt


def lago(y, t0, t1, fin, semilla=0, final_db=-16, perdida=.55):
    """y: estéreo en tiempo real (la salida de la cinta). El loop [t0, t1] da vueltas desde t1 hasta fin. El desgaste se reparte
    entre las pasadas que caben: en la última el nivel bajó `final_db`, el filtro llegó a 1.2 kHz y se perdió `perdida` del loop."""
    rng = np.random.default_rng(semilla); a, b = int(t0 * SR), int(t1 * SR); L = b - a
    loop = y[a:b].copy(); out = np.zeros_like(y); dano = np.ones(L); medidas = []
    borde = int(.02 * SR); ramp = np.linspace(0, 1, borde); n_tot = max(1, int((fin - t1) * SR // (L - borde)))
    x = b; k = 0
    while x < int(fin * SR):
        u = k / n_tot
        # el óxido se cae: huecos nuevos en lugares al azar, que se quedan en el mismo lugar del loop (Basinski)
        while np.mean(dano < .5) < perdida * u ** 1.3:
            c = rng.integers(0, L); w = int(rng.uniform(.01, .06) * SR); s0, s1 = max(0, c - w // 2), min(L, c + w // 2)
            dano[s0:s1] *= rng.uniform(.03, .4)
        d = np.convolve(dano, np.ones(240) / 240, 'same')                            # bordes suaves (5 ms)
        corte = 9000 * (1200 / 9000) ** u
        p = sosfiltfilt(butter(2, corte, 'low', fs=SR, output='sos'), loop, axis=0) * d[:, None] * 10 ** (final_db * u / 20)
        desv = 1 - .012 * u                                                          # la altura se desvía (la cinta se estira)
        idx = np.clip(np.arange(L) * desv, 0, L - 1); p = np.stack([np.interp(idx, np.arange(L), p[:, j]) for j in range(2)], 1)
        p[:borde] *= ramp[:, None]; p[-borde:] *= ramp[::-1][:, None]
        m = min(L, len(out) - x)
        if m <= 0: break
        out[x:x + m] += p[:m]
        medidas.append(dict(pasada=k, t=round(x / SR, 2), nivel_db=round(20 * math.log10(np.sqrt(np.mean(p ** 2)) + 1e-12), 1),
                            perdido=round(float(np.mean(dano < .5)), 3), corte_hz=round(corte)))
        x += L - borde; k += 1
    return out, medidas
