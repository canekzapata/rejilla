"""Lo que el agua dibuja — instrumentos nuevos (Python, 48 kHz). La guitarra de cárcava vive en motor/carcava.js (node).

  lluvia_xenakis   la tormenta como nube estocástica de glisandos, como en *Pithoprakta* (1956): las gotas llegan como proceso de
                   Poisson y cada una es una recta en el plano altura–tiempo cuya velocidad (semitonos por segundo) sigue la
                   distribución de Maxwell–Boltzmann, f(v) ∝ v² e^{−v²/a²}: la «temperatura» a sube con la tormenta. Tres
                   toques: pizzicato-glisando (la gota), arco-glisando (el chorro) y col legno (el golpe en la arcilla).
  trueno           el modelo de Few: el canal del rayo es una caminata tortuosa de segmentos de 8 m; cada uno suelta una onda N
                   que llega a quien escucha a r/343 s, más fuerte si el segmento queda de lado (perpendicular a la visual), más
                   oscura mientras más lejos (absorción del aire). El retumbo ES la forma del rayo, leída por distancias.
  crecida          el hidrograma: la lluvia que cae, convolucionada con un hidrograma unitario gamma, da el caudal Q(t) en la boca;
                   el rugido sigue a Q y los PEDREGONES (el arrastre de fondo) caen a tasa ∝ (Q − Q_c)^{3/2}, como la ley de
                   Meyer-Peter y Müller del transporte de sedimento.
  hats808          el hi-hat de la TR-808: seis cuadradas en razones metálicas (205.3 … 800 Hz) por un pasabanda agudo.
  picos_primos     los redobles del drill desde «Los ceros que tocan a los primos»: −2 Σ cos(γ_n u) con los 2000 ceros de zeta;
                   los picos que se DETECTAN en la suma (no una lista de primos) caen en u = log p^k. Un redoble recorre u
                   linealmente: los golpes llegan en accelerando (ida) o en ritardando hacia el tiempo fuerte (vuelta).
  ocho_ocho        el 808 del drill: seno saturado, golpe de tono, notas que se DESLIZAN a la siguiente (portamento exponencial).
  viento           el viento seco de la arcilla: ruido con ráfagas y el silbido eólico de los pastos secos (Strouhal: f = 0.2 v/d).
"""
import json, math, os, sys
import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt, find_peaks
SR = 48000
AQUI = os.path.dirname(os.path.abspath(__file__))
hz = lambda m: 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)
def _pan(y, p): a = (p + 1) * math.pi / 4; return np.stack([y * math.cos(a), y * math.sin(a)], 1)
def _bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x, axis=0)
def _lp(x, fc, o=2): return sosfilt(butter(o, fc, 'low', fs=SR, output='sos'), x, axis=0)
def _hp(x, fc, o=2): return sosfilt(butter(o, fc, 'high', fs=SR, output='sos'), x, axis=0)
SRB = 16000                                                                                          # lo grave se calcula a 16 kHz y se sube (la memoria es poca)
def _f(x, tipo, fc, o=2): return sosfilt(butter(o, fc, tipo, fs=SRB, output='sos'), x, axis=0).astype(np.float32)
def _sube(x, N):
    from scipy.signal import resample_poly
    y = resample_poly(x, 3, 1, axis=0).astype(np.float32); out = np.zeros((N,) + y.shape[1:], np.float32); out[:min(N, len(y))] = y[:N]; return out


# ───────────── la lluvia de Xenakis ─────────────
def maxwell(rng, a, n=None):
    """|v| con densidad 4/(a³√π) v² e^{−v²/a²}: la norma de tres normales de desviación a/√2 (a = la velocidad más probable)."""
    return np.linalg.norm(rng.normal(0, 1, (3,) if n is None else (n, 3)) * (np.asarray(a)[..., None] if n is not None else a) / math.sqrt(2), axis=-1)


def _gliss(e, n):
    """altura y fase de una gota: recta en semitonos, m(τ) = m0 + v τ."""
    tau = np.arange(n) / SR; m = e['m0'] + e['v'] * np.minimum(tau, e['dur']); f = hz(m)
    return tau, f, 2 * np.pi * np.cumsum(f) / SR


def lluvia_xenakis(gotas, N, semilla=0, toque=('pizz',)):
    """gotas: [{t, m0, v (st/s, con signo), dur, a, pan, toque}] → estéreo, sólo las del toque pedido."""
    rng = np.random.default_rng(semilla); y = np.zeros((N, 2), np.float32)
    for e in gotas:
        if e['toque'] not in toque: continue
        i0 = int(e['t'] * SR)
        if i0 >= N: continue
        if e['toque'] == 'pizz':
            td = float(np.clip(.32 * (440 / hz(e['m0'])) ** .35, .06, .45)); n = min(N - i0, int(min(e['dur'] + .05, 5 * td) * SR))
            tau, f, ph = _gliss(e, n); x = sum((.62 ** k) * np.sin(k * ph) * (f * k < 12000) for k in range(1, 5)) * np.exp(-tau / td)
            x *= np.minimum(1, tau / .0015)
        elif e['toque'] == 'arco':
            n = min(N - i0, int((e['dur'] + .09) * SR)); tau, f, ph = _gliss(e, n); kmax = int(max(1, min(10, 7000 / max(f.max(), 1))))
            x = sum(np.sin(k * ph) / k * (1 if k % 2 else .7) for k in range(1, kmax + 1))
            x += .08 * _bp(rng.standard_normal(n), 1500, 6000, 1)                                       # el arco raspa
            x *= np.minimum(1, tau / .05) * np.clip((e['dur'] + .09 - tau) / .09, 0, 1) * (1 + .1 * np.sin(2 * np.pi * 5.2 * tau))
        else:                                                                                          # col legno: la madera en la cuerda, un golpe
            n = min(N - i0, int(.09 * SR)); tau = np.arange(n) / SR; f0 = float(hz(e['m0']))
            x = np.sin(2 * np.pi * f0 * tau) * np.exp(-tau / .025) + .7 * _bp(rng.standard_normal(n), max(200, f0 * .7), min(15000, f0 * 3.5), 1) * np.exp(-tau / .008)
        y[i0:i0 + len(x)] += _pan(x * e['a'], e['pan'])
    return y / (np.abs(y).max() + 1e-12)


# ───────────── el trueno (Few) ─────────────
def trueno(dist_m, semilla=0, alto=3500.0, paso=8.0):
    """Un rayo que cae a dist_m (horizontal) de quien escucha. Devuelve (estéreo, retraso del primer sonido en s)."""
    rng = np.random.default_rng(semilla)
    def canal(p0, n, sube):
        P = [np.array(p0, float)]; d = np.array([0, 0, 1.0]) if sube else rng.normal(0, 1, 3)
        for _ in range(n):
            d = d + rng.normal(0, .55, 3); d[2] = abs(d[2]) * (1 if sube else rng.choice([-1, 1])) + (.6 if sube else 0); d /= np.linalg.norm(d)
            P.append(P[-1] + d * paso)
            if sube and P[-1][2] > alto: break
        return np.array(P)
    pr = canal([dist_m, 0, 0], 4000, True); segs = [(pr, 1.0)]
    for k in rng.choice(len(pr) - 1, 40):                                                              # ramas: más chicas, más débiles
        segs.append((canal(pr[k], int(rng.integers(20, 90)), False), .35))
    ondas = []
    for P, w in segs:
        mid = (P[1:] + P[:-1]) / 2; dv = P[1:] - P[:-1]; r = np.linalg.norm(mid, axis=1)
        sen = np.linalg.norm(np.cross(dv / paso, mid / r[:, None]), axis=1)                           # la emisión es lateral (Few)
        ondas += [(ri, w * (.15 + sn) / ri, mid_[1]) for ri, sn, mid_ in zip(r, sen, mid)]
    r = np.array([o[0] for o in ondas]); a = np.array([o[1] for o in ondas]); lado = np.array([o[2] for o in ondas])
    r0 = r.min(); n = int(((r.max() - r0) / 343 + 1.5) * SR); y = np.zeros((n, 2))
    tauN = int(.004 * SR); onda = np.linspace(1, -1, tauN)                                              # la onda N
    bins = np.linspace(r0, r.max() + 1, 25)
    for b0, b1 in zip(bins, bins[1:]):
        sel = (r >= b0) & (r < b1)
        if not sel.any(): continue
        z = np.zeros((n, 2)); idx = ((r[sel] - r0) / 343 * SR).astype(int)
        pan = np.clip(lado[sel] / 800, -1, 1)
        np.add.at(z[:, 0], idx, a[sel] * (1 - pan) / 2); np.add.at(z[:, 1], idx, a[sel] * (1 + pan) / 2)
        z = np.stack([np.convolve(z[:, k], onda)[:n] for k in range(2)], 1)
        rm = (b0 + b1) / 2; fc = 120 + 9000 * math.exp(-rm / 1400)                                    # el aire se come lo agudo con la distancia
        y += _lp(z, min(fc, 15000), 2)
    y = _hp(y, 22, 2)
    return y / (np.abs(y).max() + 1e-12), r0 / 343


# ───────────── la crecida ─────────────
def hidrograma(lluvia, fr, k=3.0, theta=2.2):
    """lluvia: gotas por segundo muestreadas a fr Hz → caudal en la boca (normalizado a su pico): convolución con una gamma."""
    t = np.arange(int(8 * k * theta * fr)) / fr; uh = t ** (k - 1) * np.exp(-t / theta); uh /= uh.sum()
    q = np.convolve(lluvia, uh)[:len(lluvia)]; return q / (q.max() + 1e-12)


def crecida(Q, fr, N, semilla=0, Qc=.22):
    """Q a fr Hz (0–1) → (rugido estéreo, pedregones estéreo, tasa de pedregones a fr Hz). El rugido se calcula a 16 kHz."""
    rng = np.random.default_rng(semilla); n = N // 3 + 1; tb = np.arange(n, dtype=np.float32) / SRB; q = np.interp(tb, np.arange(len(Q)) / fr, Q).astype(np.float32)
    nudos = np.arange(0, tb[-1] + 2, .25)
    lento = np.interp(tb, nudos, rng.uniform(.6, 1.4, len(nudos))).astype(np.float32)
    ruge = np.zeros((n, 2), np.float32)
    for k in range(2):
        pardo = _f(np.cumsum(rng.standard_normal(n).astype(np.float32) * .02), 'high', 30, 1)                 # ruido pardo, sin deriva
        ruge[:, k] += _f(pardo, 'band', [40, 260]) * q ** .8 * lento
        blanco = rng.standard_normal(n).astype(np.float32) * .05
        ruge[:, k] += .55 * _f(blanco * 3, 'band', [260, 900]) * q * lento + .22 * _f(blanco * 3, 'band', [900, 3200]) * q ** 1.4 * lento
        del pardo, blanco
    ruge = _sube(ruge, N)
    tasa = 28 * np.clip(Q - Qc, 0, None) ** 1.5 / (1 - Qc) ** 1.5                                      # Meyer-Peter–Müller: (τ − τc)^{3/2}
    piedra = np.zeros((N, 2), np.float32); L = int(.12 * SR); tl = np.arange(L) / SR
    tt = 0.0; T = N / SR
    while True:
        lam = float(np.interp(tt, np.arange(len(Q)) / fr, tasa)); lmax = max(lam, .05); tt += rng.exponential(1 / lmax)
        if tt >= T - .15: break
        if rng.random() > lam / lmax: continue
        f0 = rng.uniform(80, 420); x = np.sin(2 * np.pi * f0 * tl) * np.exp(-tl / rng.uniform(.015, .05)) + .5 * rng.standard_normal(L) * np.exp(-tl / .002)
        i = int(tt * SR); piedra[i:i + L] += _pan(x * rng.uniform(.25, 1), rng.uniform(-.8, .8))
    return ruge / (np.abs(ruge).max() + 1e-12), piedra / (np.abs(piedra).max() + 1e-12), tasa


# ───────────── el hi-hat de la 808 y los redobles primos ─────────────
_METAL = None
def _metal():
    global _METAL
    if _METAL is None:
        t = np.arange(int(2 * SR)) / SR; x = sum(np.sign(np.sin(2 * np.pi * f * t + k)) for k, f in enumerate((205.3, 304.4, 369.6, 522.7, 540.0, 800.0)))
        _METAL = _hp(_bp(x, 6500, 13000, 2), 7000, 2)
    return _METAL


def hats808(golpes, N, semilla=0):
    """golpes: [{t, v, abierto, pan}] → estéreo."""
    rng = np.random.default_rng(semilla); M = _metal(); y = np.zeros((N, 2), np.float32)
    for g in golpes:
        i0 = int(g['t'] * SR); L = int((.6 if g.get('abierto') else .12) * SR); L = min(L, N - i0)
        if L <= 0: continue
        o = int(rng.integers(0, len(M) - L)); tl = np.arange(L) / SR
        env = np.exp(-tl / (.19 if g.get('abierto') else .022)) * np.minimum(1, tl / .0004)
        y[i0:i0 + L] += _pan(M[o:o + L] * env * g['v'], g.get('pan', .25))
    return y / (np.abs(y).max() + 1e-12)


def picos_primos(nmax=72, cache=os.path.join(AQUI, 'datos', 'picos-primos.json')):
    """Los picos de −2 Σ w_n cos(γ_n u) (2000 ceros) entre u = log 1.8 y log nmax, DETECTADOS en la suma: [(u, altura)]."""
    if os.path.exists(cache):
        d = json.load(open(cache, encoding='utf-8'))
        if d['nmax'] == nmax: return d['picos'], d
    sys.path.insert(0, os.path.join(AQUI, '..', 'ceros-que-tocan-primos')); import ceros_primos as CP
    du = 2e-5; u = np.arange(math.log(1.8), math.log(nmax) + .02, du); s = CP.suma(u, CP.GAMMA[-1] * 1.0001)
    w = int(.04 / du) | 1; d = s - np.convolve(s, np.ones(w) / w, 'same')
    ruido = 1.4826 * np.median(np.abs(d - np.median(d)))
    pk, _ = find_peaks(d, height=6 * ruido, distance=int(.004 / du))
    picos = [[round(float(u[k]), 6), round(float(d[k] / ruido), 2)] for k in pk]
    # comprobación: ¿cada pico cae en un log p^k?
    pp = [(math.log(n), lam, n) for n, lam in CP.potencias_de_primos(nmax)]
    acierta = [min(pp, key=lambda q: abs(q[0] - p[0])) for p in picos]
    info = dict(nmax=nmax, ceros=len(CP.GAMMA), picos=picos, ruido=float(ruido),
                cae_en=[(a[2], round(abs(a[0] - p[0]), 6)) for a, p in zip(acierta, picos)],
                potencias_de_primos=len(pp), encontradas=len({a[2] for a, p in zip(acierta, picos) if abs(a[0] - p[0]) < .002}))
    os.makedirs(os.path.dirname(cache), exist_ok=True); json.dump(info, open(cache, 'w', encoding='utf-8'))
    return picos, info


def redoble(t0, D, picos, ida=True, v=.8, u0=math.log(1.8), u1=None):
    """Un redoble de D segundos: u recorre [u0, u1] (ida: accelerando) o al revés (vuelta: ritardando que cae en t0 + D)."""
    u1 = u1 or max(p[0] for p in picos) + .01; out = []
    hmax = max(p[1] for p in picos)
    for u, h in picos:
        if not (u0 <= u <= u1): continue
        x = (u - u0) / (u1 - u0); t = t0 + D * (x if ida else 1 - x)
        out.append(dict(t=round(t, 5), v=round(v * (.35 + .65 * (h / hmax) ** .7), 3), pan=round(.3 * (x - .5), 3)))
    return sorted(out, key=lambda g: g['t'])


# ───────────── el 808 que se desliza ─────────────
def ocho_ocho(notas, N, fr=1000):
    """notas: [{t, dur, m, v, desliz (s: se desliza a la siguiente en sus últimos desliz s)}] → mono."""
    notas = sorted(notas, key=lambda n: n['t']); M = int(N / SR * fr) + 2; m = np.full(M, np.nan); amp = np.zeros(M)
    for k, n in enumerate(notas):
        a, z = int(n['t'] * fr), int((n['t'] + n['dur']) * fr); m[a:z] = n['m']
        sig = notas[k + 1] if k + 1 < len(notas) else None
        if n.get('desliz') and sig and sig['t'] - (n['t'] + n['dur']) < .02:
            d = int(n['desliz'] * fr); s = np.linspace(0, 1, d) ** 2; b = max(a, z - d); m[b:z] = n['m'] + (sig['m'] - n['m']) * s[-(z - b):]
        tl = np.arange(z - a) / fr; amp[a:z] = np.maximum(amp[a:z], n['v'] * np.exp(-tl / 2.2))
    m = np.where(np.isnan(m), 0, m); n = N // 3 + 1; t = np.arange(n) / SRB; mm = np.interp(t, np.arange(M) / fr, m); aa = np.interp(t, np.arange(M) / fr, amp)
    aa = sosfiltfilt(butter(1, 120, fs=SRB, output='sos'), aa)                                         # sin chasquidos al cortar
    golpe = np.zeros(n)
    for k, nn in enumerate(notas):                                                                      # golpe de tono al pegar (no en las ligadas)
        if k and notas[k - 1].get('desliz') and nn['t'] - (notas[k - 1]['t'] + notas[k - 1]['dur']) < .02: continue
        i = int(nn['t'] * SRB); L = min(n - i, int(.06 * SRB)); golpe[i:i + L] = np.maximum(golpe[i:i + L], np.exp(-np.arange(L) / (.012 * SRB)))
    f = hz(mm) * (1 + 1.2 * golpe); y = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SRB) * aa).astype(np.float32)
    y = _sube(_f(y, 'low', 6000, 4), N)
    return y / (np.abs(y).max() + 1e-12)


# ───────────── el viento seco ─────────────
def viento(curva, N, semilla=0, d=.004):
    """curva: [[t, m/s]] → (estéreo, v a 16 kHz). Ráfagas lentas; el pasto seco (tallos de d m) silba a f = 0.2 v / d."""
    rng = np.random.default_rng(semilla); n = N // 3 + 1; t = np.arange(n) / SRB; v0 = np.interp(t, *zip(*curva))
    nudos = np.arange(0, t[-1] + 4, .7)
    raf = np.interp(t, nudos, rng.normal(0, 1, len(nudos))); raf = sosfiltfilt(butter(1, .5, fs=SRB, output='sos'), raf)
    v = np.clip(v0 * (1 + .35 * raf / (np.abs(raf).max() + 1e-9)), 0, None).astype(np.float32); del raf, v0
    y = np.zeros((n, 2), np.float32)
    for k in range(2): y[:, k] += _f(rng.standard_normal(n).astype(np.float32), 'band', [180, 1400], 1) * (v / 10) ** 2
    nudos_silbo = np.arange(0, t[-1] + 2, .05)
    f = .2 * v / d * (1 + .01 * np.interp(t, nudos_silbo, rng.normal(0, 1, len(nudos_silbo))))
    silbo = (np.sin(2 * np.pi * np.cumsum(f) / SRB) * np.clip(v - 5, 0, None) / 6 * .25).astype(np.float32)
    y += _pan(silbo, .4).astype(np.float32); y = _sube(y, N)
    return y / (np.abs(y).max() + 1e-12), v
