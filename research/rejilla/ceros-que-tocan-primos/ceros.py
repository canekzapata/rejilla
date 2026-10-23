"""Los ceros no triviales de la zeta de Riemann, calculados aquí (sin mpmath) con la fórmula de Riemann–Siegel.

Z(t) = 2 Σ_{n ≤ N} n^{−1/2} cos(θ(t) − t ln n) + (−1)^{N−1} (t/2π)^{−1/4} C0(p),   N = ⌊√(t/2π)⌋, p = √(t/2π) − N
Z(t) es real y cambia de signo en cada cero ½ + iγ. Se muestrea fino con Riemann–Siegel (rápido) para encerrar
los cambios de signo, y cada cero se afina por bisección sobre Z calculada con Euler–Maclaurin (ζ(½+it) directa,
error ~1e-10; Riemann–Siegel con sólo C0 se equivoca ~0.008 en los primeros). Comprobación: los primeros contra los valores publicados y la cuenta contra
N(T) ≈ θ(T)/π + 1 (Riemann–von Mangoldt).

python ceros.py [cuántos]   → datos/ceros-zeta-<cuántos>.json
"""
import json, math, sys, hashlib
from pathlib import Path
import numpy as np

CONOCIDOS = [14.134725142, 21.022039639, 25.010857580, 30.424876126, 32.935061588,
             37.586178159, 40.918719012, 43.327073281, 48.005150881, 49.773832478]


def theta(t):
    t = np.asarray(t, float)
    return t / 2 * np.log(t / (2 * math.pi)) - t / 2 - math.pi / 8 + 1 / (48 * t) + 7 / (5760 * t ** 3)


def Z(t):
    t = np.atleast_1d(np.asarray(t, float))
    a = np.sqrt(t / (2 * math.pi)); N = np.floor(a).astype(int); p = a - N
    th = theta(t); s = np.zeros_like(t)
    for n in range(1, int(N.max()) + 1):
        m = N >= n
        s[m] += np.cos(th[m] - t[m] * math.log(n)) / math.sqrt(n)
    c = np.cos(2 * math.pi * p)
    c = np.where(np.abs(c) < 1e-9, 1e-9, c)                    # C0 tiene singularidades removibles en p = 1/4, 3/4
    C0 = np.cos(2 * math.pi * (p * p - p - 1 / 16)) / c
    return 2 * s + np.where(N % 2 == 1, 1.0, -1.0) * (t / (2 * math.pi)) ** -0.25 * C0


B2K = [1 / 6, -1 / 30, 1 / 42, -1 / 30, 5 / 66, -691 / 2730, 7 / 6, -3617 / 510]


def Z_em(t):
    """Z(t) = Re(e^{iθ(t)} ζ(½ + it)) con ζ por Euler–Maclaurin (N > t/2π, 8 términos de Bernoulli)."""
    s = 0.5 + 1j * t; N = int(t / (2 * math.pi)) + 25
    n = np.arange(1, N, dtype=float)
    z = np.sum(n ** (-s)) + N ** (1 - s) / (s - 1) + 0.5 * N ** (-s)
    fac, poch = 1.0, s
    for k, b in enumerate(B2K, 1):
        fac *= (2 * k - 1) * (2 * k) if k > 1 else 2
        if k > 1: poch *= (s + 2 * k - 3) * (s + 2 * k - 2)
        z += b / fac * poch * N ** (-s - 2 * k + 1)
    th = float(theta(t)) + 31 / (80640 * t ** 5)
    return float((np.exp(1j * th) * z).real)


def ceros(cuantos, paso=0.005):
    T = 2 * math.pi * math.exp(1 + 0.0)
    while theta(T) / math.pi + 1 < cuantos + 3: T *= 1.05      # techo con margen
    out = []; t0 = 10.0
    while t0 < T and len(out) < cuantos:
        t = np.arange(t0, min(T, t0 + 200.0), paso); z = Z(t)
        for i in np.nonzero(np.sign(z[:-1]) != np.sign(z[1:]))[0]:
            a, b = t[i] - paso, t[i + 1] + paso; za = Z_em(a)
            if np.sign(za) == np.sign(Z_em(b)): a, b = t[i], t[i + 1]; za = Z_em(a)
            for _ in range(42):                                    # bisección sobre Z de Euler–Maclaurin
                m = (a + b) / 2; zm = Z_em(m)
                if np.sign(zm) == np.sign(za): a, za = m, zm
                else: b = m
            out.append((a + b) / 2)
        t0 = t[-1]
    return np.array(out[:cuantos])


def comprobar(g):
    T = float(g[-1]) + 0.01
    return {'cuantos': len(g), 'ultimo_gamma': round(float(g[-1]), 6),
            'error_max_primeros_10': float(np.max(np.abs(g[:10] - CONOCIDOS))),
            'cuenta_contra_riemann_von_mangoldt': {'encontrados': len(g), 'N_T_suave': round(float(theta(T) / math.pi + 1), 2)},
            'separacion_minima': round(float(np.min(np.diff(g))), 5)}


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    g = ceros(n); c = comprobar(g); print(json.dumps(c, ensure_ascii=False))
    d = Path(__file__).resolve().parent / 'datos'; d.mkdir(exist_ok=True)
    datos = json.dumps([round(float(x), 9) for x in g])
    destino = d / f'ceros-zeta-{n}.json'
    if destino.exists(): raise SystemExit(f'ya existe {destino}: no se pisa')
    destino.write_text(json.dumps({'gammas': json.loads(datos), 'comprobacion': c, 'metodo': 'Riemann–Siegel con C0, bisección',
                                   'sha256_gammas': hashlib.sha256(datos.encode()).hexdigest()}, ensure_ascii=False), encoding='utf-8')
    print('→', destino)
