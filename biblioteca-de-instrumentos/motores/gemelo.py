"""biblioteca de instrumentos · gemelo de motores/web.js en numpy/scipy (v1, loop 01).

Hace en el tiempo lo mismo que Web Audio: automatización de parámetros (setValue, rampas lineal y exponencial, setTarget),
osciladores, PeriodicWave normalizada, biquads con las fórmulas de Web Audio (la Q de pasa bajos/altos en dB, la de pasa banda
lineal), WaveShaper con interpolación lineal, parámetros movidos por señal (trémolo, ruido que sigue a la nota) y el mismo ruido
sembrado (1729). Sirve para lo que los modos no alcanzan: el zumbido, la saturación. Rejilla lo usa como pista de muestras
(ya mezcla pistas después de spectrumsynth).

    import gemelo as G
    y = G.nota(K, midi=62, vel=.8, segundos=2, sr=44100, tonica='D', escala=[0,1,5,7,8])

Medido contra web.js en pruebas/rejilla_contra_web.py. Los filtros que se mueven (cabaça, boca) cambian coeficientes en cada muestra, como
Chrome (medido: por bloque de 128 el error era −27 dB; por muestra, −72 a −98 dB).
"""
import math
import numpy as np
from scipy.signal import lfilter

NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FORMANTES = {'a': [800, 1200, 2500], 'e': [450, 1900, 2550], 'i': [300, 2200, 2950], 'o': [500, 900, 2400], 'u': [320, 750, 2350]}
_RUIDO = {}
POR_MUESTRA = True      # los filtros que se mueven cambian coeficientes en cada muestra (así lo hace Chrome: medido)


def hz(m): return 440 * 2 ** ((m - 69) / 12)


def ruido(sr):
    """El buffer sembrado de web.js (2 s): el mismo generador de 32 bits, número por número."""
    if sr in _RUIDO: return _RUIDO[sr]
    a = 1729; M = 0xFFFFFFFF; out = np.empty(sr * 2)
    imul = lambda x, y: (x * y) & M
    for i in range(sr * 2):
        a = (a + 0x6D2B79F5) & M; t = a
        t = imul(t ^ (t >> 15), t | 1)
        t = (t ^ (t + imul(t ^ (t >> 7), t | 61))) & M
        out[i] = (((t ^ (t >> 14)) & M) / 4294967296) * 2 - 1
    _RUIDO[sr] = out.astype(np.float32).astype(float)
    return _RUIDO[sr]


class Param:
    """AudioParam: eventos en el orden en que se agregan; se evalúa por muestra."""
    def __init__(self, valor): self.v0, self.ev = valor, []
    def set(self, v, t): self.ev.append(('set', t, v)); return self
    def lin(self, v, t): self.ev.append(('lin', t, v)); return self
    def exp(self, v, t): self.ev.append(('exp', t, v)); return self
    def target(self, v, t, tau): self.ev.append(('tgt', t, v, tau)); return self

    def curva(self, n, sr):
        """Tramo por tramo, como el AudioParam: un set sostiene, una rampa va del evento anterior a éste, un setTarget
        persigue su valor desde su hora hasta el siguiente evento (y el siguiente arranca desde donde iba)."""
        t = np.arange(n) / sr; y = np.full(n, float(self.v0))
        ev = [e for _, e in sorted(enumerate(self.ev), key=lambda e: (e[1][1], e[0]))]
        T0, V0, tgt = 0.0, float(self.v0), None          # tgt = (valor buscado, tau) si el tramo actual es un setTarget
        val_tgt = lambda tt: tgt[0] + (V0 - tgt[0]) * np.exp(-(tt - T0) / tgt[1])
        for e in ev:
            tipo, T1, V1 = e[0], e[1], e[2]; m = (t >= T0) & (t < T1)
            if tgt is not None:
                y[m] = val_tgt(t[m]); Vfin = float(val_tgt(T1))
            elif tipo == 'lin':
                y[m] = V0 + (V1 - V0) * (t[m] - T0) / max(T1 - T0, 1e-12); Vfin = V1
            elif tipo == 'exp' and V0 * V1 > 0:
                y[m] = V0 * (V1 / V0) ** ((t[m] - T0) / max(T1 - T0, 1e-12)); Vfin = V1
            else:
                y[m] = V0; Vfin = V0
            if tipo == 'tgt':
                T0, V0, tgt = T1, Vfin, (V1, e[3])
            elif tipo == 'set':
                T0, V0, tgt = T1, V1, None
            else:                                          # rampa: termina en su valor
                T0, V0, tgt = T1, V1, None
        m = t >= T0
        y[m] = val_tgt(t[m]) if tgt is not None else V0
        return y


def biquad(tipo, f, q, sr):
    w = 2 * math.pi * min(f, sr / 2 * .9999) / sr; c, s = math.cos(w), math.sin(w)
    if tipo == 'bandpass':
        al = s / (2 * q); b = [al, 0, -al]
    else:
        al = s / (2 * 10 ** (q / 20))
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2] if tipo == 'lowpass' else [(1 + c) / 2, -(1 + c), (1 + c) / 2]
    a = [1 + al, -2 * c, 1 - al]
    return np.array(b) / a[0], np.array(a) / a[0]


def filtrar(x, tipo, f, q, sr):
    """f puede ser un número o una curva (se toma cada 128 muestras, como el bloque de Web Audio)."""
    if np.isscalar(f):
        b, a = biquad(tipo, f, q, sr); return lfilter(b, a, x)
    if POR_MUESTRA:                                   # coeficientes en cada muestra (forma directa I)
        y = np.empty_like(x); x1 = x2 = y1 = y2 = 0.0
        for i in range(len(x)):
            (b0, b1, b2), (_, a1, a2) = biquad(tipo, float(f[i]), q, sr)
            yi = b0 * x[i] + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2; x2, x1, y2, y1 = x1, x[i], y1, yi; y[i] = yi
        return y
    y = np.empty_like(x); zi = np.zeros(2)
    for i in range(0, len(x), 128):
        b, a = biquad(tipo, float(f[i]), q, sr); y[i:i + 128], zi = lfilter(b, a, x[i:i + 128], zi=zi)
    return y


def forma(x, curva):
    """WaveShaper: entrada −1..1 sobre la curva con interpolación lineal (sin sobremuestreo)."""
    n = len(curva); v = (n - 1) / 2 * (np.clip(x, -1, 1) + 1); i = np.minimum(np.floor(v).astype(int), n - 2); fr = v - i
    return curva[i] * (1 - fr) + curva[i + 1] * fr


def seno(f, n, sr, t0=0.0):
    """Oscilador seno con frecuencia (número o curva) desde t0."""
    t = np.arange(n) / sr; fa = np.full(n, f, float) if np.isscalar(f) else f
    fase = np.concatenate([[0.0], np.cumsum(fa[:-1])]) / sr; i0 = int(math.ceil(t0 * sr)); y = np.zeros(n)   # la fase avanza con la frecuencia de la muestra anterior
    y[i0:] = np.sin(2 * math.pi * (fase[i0:] - fase[i0])); return y


def lenguas(pc, escala, mid, cerca):
    iv = min([x for x in escala if x > 0] or [cerca], key=lambda x: abs(x - cerca))
    low = 12 + pc; d = (round(mid) - low) % 12
    return round(mid) - d + min([0, iv, 12], key=lambda x: abs(x - d))


def nota(K, midi, vel, segundos=2.0, sr=44100, tonica='C', escala=(0, 2, 4, 7, 9), dur=.7):
    S, mot, v = K['fisica'], K['motor'], max(2e-4, vel); n = int(round(segundos * sr)); at = 0.0
    pc = tonica % 12 if isinstance(tonica, int) else NOTAS.index(tonica); escala = list(escala); ny = sr * .45
    R = ruido(sr); nz = lambda: np.resize(R, n)
    env = Param(0).set(0, at)
    if mot == 'golpe':
        mid = lenguas(pc, escala, midi, 5) if S.get('tongues') else midi
        f = hz(mid); sc = min(2.5, max(.3, (262 / f) ** S['dk'])); suma = np.zeros(n); end = .05
        cents = ((abs(math.sin(mid * 12.9898 + 7.233) * 43758.5453) % 1) * 2 - 1) * S['loose'] if S.get('loose') else 0
        for k, p in enumerate(S['parts']):
            r, g, d = p[:3]; a = p[3] if len(p) > 3 else .002
            ff = f * r * 2 ** ((cents * 1.6 if k else cents) / 1200); dd = d * sc
            if ff > ny: continue
            for dh in ([-S['pair'] / 2, S['pair'] / 2] if S.get('pair') else [0]):
                fr = ff + dh
                if S.get('shift'): fr = Param(fr).set(fr * 2 ** (S['shift'] / 1200), at).exp(fr, at + .05).curva(n, sr)
                lv = g / (1.6 if S.get('pair') else 1)
                suma += seno(fr, n, sr) * Param(0).set(0, at).lin(lv, at + a).exp(1e-4, at + a + dd).curva(n, sr)
            end = max(end, a + dd)
        if S.get('click'):
            cf, q, cg, cd = S['click']
            suma += filtrar(nz(), 'bandpass', min(ny, cf), q, sr) * Param(1).set(0, at).lin(cg, at + .001).exp(1e-4, at + .001 + cd).curva(n, sr)
        salida = suma
        if S.get('trem'):
            rt, dp = S['trem']; salida = salida * ((1 - dp / 2) + seno(rt, n, sr) * dp / 2)
        if S.get('lp'): salida = filtrar(salida, 'lowpass', S['lp'], 1, sr)
        if S.get('drive'):
            gd = 1 + S['drive'] * 6; x = np.arange(1024) / 511.5 - 1; salida = forma(salida, np.tanh(x * gd) / math.tanh(gd))
        mezcla = salida.copy()
        if S.get('buzz'):
            amt, hpf = S['buzz']; x = np.arange(1024) / 511.5 - 1
            cv = np.where(x > .12, 1.0, np.where(x < -.3, -.6, 0.0)); rc = np.maximum(0, np.abs(x) - .05)
            mezcla += filtrar(forma(suma, cv), 'highpass', hpf, 1, sr) * amt * 1.4
            mezcla += filtrar(nz(), 'bandpass', hpf * 1.8, 1.4, sr) * forma(suma, rc) * amt * 2.5
        if S.get('body'):
            bf, q, bg = S['body']; cuerpo = filtrar(suma, 'bandpass', bf, q, sr) * bg
            mezcla += cuerpo if not (S.get('trem') or S.get('lp') or S.get('drive')) else 0   # en web.js el cuerpo entra a la cadena si la hay
        L = .3 * v * S['gain']; env.set(L, at).set(L, at + end).exp(1e-4, at + end + .08)
        y = mezcla
    elif mot == 'boca':
        dm = 12 * (S['octava'] + 1) + pc
        while hz(dm) > S['maxHz']: dm -= 12
        while hz(dm) < S['minHz']: dm += 12
        f0 = hz(dm); h = round(hz(midi) / f0)
        while h > S['armonicos'][1]: h = round(h / 2)
        while h < S['armonicos'][0]: h *= 2
        ft = h * f0; t = np.arange(n) / sr
        onda = sum(np.sin(2 * math.pi * k * f0 * t) / k ** S['brillo'] for k in range(1, 64) if k * f0 < sr / 2)
        xs = np.linspace(0, 2 * np.pi, 8192, endpoint=False); onda /= np.abs(sum(np.sin(k * xs) / k ** S['brillo'] for k in range(1, 64))).max()
        hold = max(.25, dur); src = onda * Param(1).set(0, at).lin(1, at + .003).exp(.35, at + .2).target(1e-4, at + hold, .25).curva(n, sr)
        mejor = min(((abs(math.log(FORMANTES[vw][k] / ft)), vw, k) for vw in 'aeiou' for k in (0, 1)))
        F = FORMANTES[mejor[1]]; desde = ft * 2 ** (S['deslizar'] if h % 2 else -S['deslizar']); y = np.zeros(n)
        for j, fq in enumerate(F):
            if j == mejor[2]:
                fc = Param(fq).set(desde, at).target(ft, at + .005, .035).curva(n, sr)
                y += filtrar(src, 'bandpass', fc, S['qBoca'], sr) * S['nivelBoca']
            else:
                y += filtrar(src, 'bandpass', fq, S['qOtros'], sr) * S['nivelOtros']
        y += filtrar(src, 'lowpass', f0 * 2.5, 1, sr) * S['cuerpo']
        L = .3 * v * S['gain']; end = hold + 1.1; env.set(L, at).set(L, at + end - .1).exp(1e-4, at + end)
    elif mot == 'arco':
        mid = lenguas(pc, escala, midi, S['cerca']); f = hz(mid); chiado = vel < S['chiado']; sc = min(1.6, max(.5, (130 / f) ** .4))
        suma = np.zeros(n); end = .1
        for k in range(1, S['parciales'] + 1):
            fn = k * f * math.sqrt(1 + S['inarmonia'] * k * k)
            if fn > ny: break
            lv = abs(math.sin(k * math.pi * S['golpe'])) / k ** .55; d = (S['caidaChiado'] if chiado else S['caida']) / (1 + .12 * k) * sc
            suma += seno(fn, n, sr) * Param(0).set(0, at).lin(lv, at + .002).exp(1e-4, at + .002 + d).curva(n, sr); end = max(end, d + .002)
        c0, c1, ct, cq, cg = S['cabaca']
        y = suma * S['seco'] + filtrar(suma, 'bandpass', Param(c0).set(c0, at).exp(c1, at + ct).curva(n, sr), cq, sr) * cg

        def golpe_ruido(fc, q, lv, d, t=0.0):
            nonlocal end
            end = max(end, t + d + .002)
            return filtrar(nz(), 'bandpass', min(ny, fc), q, sr) * Param(0).set(0, at + t).lin(lv, at + t + .002).exp(1e-4, at + t + .002 + d).curva(n, sr)
        y = y + golpe_ruido(2500, 1.5, .5, .012)
        if chiado: y = y + golpe_ruido(3400, 2, .7, .07)
        y = y + golpe_ruido(7000, 1.2, .22, .045) + golpe_ruido(7600, 1.2, .12, .035, .11)
        L = .3 * v * S['gain']; env.set(L, at).set(L, at + end).exp(1e-4, at + end + .06)
    else:
        raise ValueError(f"el gemelo no sabe tocar «{mot}» ({K['id']})")
    return y * env.curva(n, sr)
