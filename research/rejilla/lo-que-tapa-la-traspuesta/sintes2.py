"""Lo que tapa la traspuesta — sintes propios de la pieza (los de «Cuento en siete» se importan de ../cuento-en-siete/sintes.py).

  mono(notas, N, timbre)   voz monofónica con glisandos: si una nota trae glis, la altura viaja desde la nota anterior durante
                           toda la nota (lo liso); si no, 14 ms de portamento (lo estriado).
     'fretless'  el bajo sin trastes: seno + armónicos 2–6 que se apagan, y el «mwah» (un formante que baja de 1.1 kHz a
                 350 Hz en 120 ms al pulsar, como el dedo que suelta la cuerda junto al diapasón); vibrato tardío en lo largo
     'zawinul'   dos sierras y un pulso por un pasabajos resonante calculado armónico por armónico; el filtro abre con el acento
"""
import numpy as np
SR = 48000
hz = lambda m: 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def _lpf(f, fc, q): x = f / fc; return 1 / np.sqrt((1 - x * x) ** 2 + (x / q) ** 2)
def _bpf(f, fc, q): x = np.maximum(f, 1e-3) / fc; return 1 / np.sqrt(1 + q * q * (x - 1 / x) ** 2)


def mono(notas, N, timbre, semilla=0):
    y = np.zeros(N); rng = np.random.default_rng(semilla)
    if not notas: return y
    notas = sorted(notas, key=lambda n: n['t'])
    frases, cur = [], [notas[0]]
    for a, b in zip(notas, notas[1:]):
        if b['t'] - (a['t'] + a['dur']) > .12: frases.append(cur); cur = [b]
        else: cur.append(b)
    frases.append(cur)
    for fr in frases:
        i0 = max(0, int((fr[0]['t'] - .01) * SR)); i1 = min(N, int((fr[-1]['t'] + fr[-1]['dur'] + .4) * SR)); n = i1 - i0
        if n <= 0: continue
        t = i0 / SR + np.arange(n) / SR
        m = np.full(n, float(fr[0]['m'])); amp = np.zeros(n); brillo = np.zeros(n); mwah = np.zeros(n)
        for j, nt in enumerate(fr):
            a = max(0, int((nt['t'] - i0 / SR) * SR)); z = min(n, a + int(nt['dur'] * SR))
            p = fr[j - 1]['m'] if j else nt['m']
            if nt.get('glis') and j:
                L = max(1, z - a); u = np.linspace(0, 1, L) ** (1.6 if nt.get('liso') else 1); m[a:a + L] = p + (nt['m'] - p) * u; m[a + L:] = nt['m']
            else:
                m[a:] = nt['m']; L = min(int(.014 * SR), n - a)
                if j and L > 0: m[a:a + L] = p + (nt['m'] - p) * np.linspace(0, 1, L)
            u = (np.arange(n) - a) / SR; v = nt.get('v', .8)
            env = np.where((u >= 0) & (u <= nt['dur']), np.minimum(1, np.clip(u, 0, None) / .005), 0)
            rel = np.where(u > nt['dur'], np.exp(-(u - nt['dur']) / (.09 if timbre == 'fretless' else .05)), 0)
            dec = np.exp(-np.clip(u, 0, None) / (1.6 if timbre == 'fretless' else 4))
            amp = np.where(u >= 0, np.maximum(amp * (u < 0), v * np.maximum(env * dec, rel)), amp)
            brillo = np.where(u >= 0, (6 + 6 * (v >= 1)) * np.exp(-np.clip(u, 0, None) / .09) + 2.2, brillo)
            mwah = np.where(u >= 0, 350 + 750 * np.exp(-np.clip(u, 0, None) / .12), mwah)
        larga = np.clip((t - fr[0]['t'] - .35) / .4, 0, 1)
        f = hz(m) * (1 + .005 * np.sin(2 * np.pi * 5.2 * t) * larga)
        x = np.zeros(n)
        if timbre == 'fretless':
            ph = 2 * np.pi * np.cumsum(f) / SR + rng.uniform(0, 6)
            for k in range(1, 9):
                g = [1, .55, .32, .22, .14, .1, .06, .04][k - 1] * (1 + 1.6 * _bpf(k * f, mwah, 2.2))
                x += g * np.sin(k * ph)
            x = np.tanh(1.3 * x * amp)
        else:
            fc = np.clip(f * brillo, 200, 14000)
            for det in (-7, 7):
                fd = f * 2 ** (det / 1200); ph = 2 * np.pi * np.cumsum(fd) / SR + rng.uniform(0, 6)
                for k in range(1, 70):
                    fk = k * fd
                    if fk.min() > 15000: break
                    x += (1 / k) * _lpf(fk, fc, 2.4) * (fk < 15000) * np.sin(k * ph) * (1 + .6 * (k % 2))   # el pulso: los impares pesan más
            x = np.tanh(1.5 * x * amp) / np.tanh(1.5)
        y[i0:i1] += x
    return y / (np.abs(y).max() + 1e-12)
