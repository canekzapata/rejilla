"""¿La espiral quedó? Razón de altura medida entre secciones con la misma armonía escrita (pista tonal),
y balance por sección."""
import json, math
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
import cancion as K

R = K.R
marcas = json.load(open(R / 'partitura.json', encoding='utf-8'))['marcas']
ini = {s: t for s, t in marcas}
fin = {s: t2 for (s, _), (_, t2) in zip(marcas, marcas[1:] + [('fin', 1e9)])}
sr, ton = wavfile.read(R / 'tl-tonal.wav'); ton = ton.mean(1)


def seg(s): return ton[int(ini[s] * sr):int(min(fin[s], len(ton) / sr) * sr)]


def logspec(x):
    X = np.abs(np.fft.rfft(x)); f = np.fft.rfftfreq(len(x), 1 / sr); g = np.geomspace(60, 5000, 9000)
    return np.log10(np.interp(g, f, X) + 1e-9), g


def picos(x, n=14):
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)))); f = np.fft.rfftfreq(len(x), 1 / sr)
    m = (f > 150) & (f < 1500); fm, Xm = f[m], X[m]
    loc = np.where((Xm[1:-1] > Xm[:-2]) & (Xm[1:-1] > Xm[2:]))[0] + 1
    return np.sort(fm[loc[np.argsort(Xm[loc])[-n:]]])


def razon(a, b, lec_b=1.0):
    """La razón que mejor empata los parciales del primer compás de a con los del primero de b.
    (La correlación de espectros se iba a la nota común de Mi mayor y Do mayor y daba 1.0.)"""
    pa = picos(seg(a)[:int(K.T0 * sr)]); pb = picos(seg(b)[:int(K.T0 / lec_b * sr)])
    mejores = []
    for r in np.arange(.6, 1.7, .0002):
        d = np.abs(np.log(pa[:, None] * r / pb[None, :])).min(1)
        mejores.append(((d < .004).sum(), -d[d < .004].sum() if (d < .004).any() else 0, r))
    return max(mejores)[2]


med = {}
for a, b, esperada in (('verso 1', 'verso 2', 5 / 4), ('coro 1', 'coro 2', 5 / 4), ('coro 1', 'puente', 4 / 5),
                       ('coro 1', 'coro final', 25 / 32)):
    r = razon(a, b, .8 if b == 'puente' else 1.0)
    med[f'{a} → {b}'] = {'medida': round(r, 4), 'esperada': round(esperada, 4),
                          'error_cents': round(1200 * math.log2(r / esperada), 1)}
sr2, x = wavfile.read(R / f'los-pixeles-y-la-luna-{K.TAG}.wav'); m = x.astype(float).mean(1) / 32768
bands = [('sub', 20, 80), ('low', 80, 250), ('mid', 250, 2000), ('pres', 2000, 6000), ('air', 6000, 20000)]
fb = {n: sosfilt(butter(4, [lo, hi], 'bandpass', fs=sr2, output='sos') if hi < sr2 / 2 else butter(4, lo, 'highpass', fs=sr2, output='sos'), m) for n, lo, hi in bands}
voz = wavfile.read(R / 'tl-voz.wav')[1].mean(1); musica = wavfile.read(R / 'mx-musica.wav')[1].mean(1)
bal = {}
for s, t in marcas:
    i, j = int(t * sr2), int(min(fin[s], len(m) / sr2) * sr2)
    if j - i < sr2: continue
    r = m[i:j].std()
    bal[s] = {'rms': round(20 * math.log10(r + 1e-12), 1),
              **{n: round(20 * math.log10(fb[n][i:j].std() / r + 1e-12), 1) for n, _, _ in bands},
              'voz_menos_musica_dB': round(20 * math.log10((voz[i:j].std() + 1e-12) / (musica[i:j].std() + 1e-12)), 1)}
med['balance'] = bal
print(json.dumps(med, ensure_ascii=False, indent=1))
json.dump(med, open(K.AQUI / f'medidas-espiral-{K.TAG}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
