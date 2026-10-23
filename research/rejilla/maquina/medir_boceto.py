"""¿El boceto hace lo que dice? Envolvente de cada banda doblada sobre el compás (16 casillas),
comparada con los golpes escritos; profundidad de modulación por sección; y si el espectro
(la armonía) es el mismo cuando hay groove y cuando no."""
import json
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, hilbert
import boceto as B

sr, x = wavfile.read(B.R / 'boceto-norm.wav'); m = x.mean(1)
T = B.T
BANDAS = {'bajo': (35, 190), 'medio': (210, 830), 'alto': (850, 3000)}
env = {b: np.abs(hilbert(sosfiltfilt(butter(4, f, 'bandpass', fs=sr, output='sos'), m))) for b, f in BANDAS.items()}


def doblar(e, compases):
    """Promedio de la envolvente en las 16 casillas del compás, sobre esos compases."""
    casillas = np.zeros(16)
    for c in compases:
        for k in range(16):
            i = int((c * T + k * T / 16) * sr); j = int((c * T + (k + 1) * T / 16) * sr)
            casillas[k] += e[i:j].max()
    return casillas / len(compases)


def esperado(golpes, tau):
    t = np.arange(4096) / 4096 * T; e = np.zeros_like(t)
    for p, g in golpes.items():
        d = (t - p * T / 16) % T; e += g * np.exp(-d / tau) * (1 - np.exp(-d / .004))
    return np.array([e[k * 256:(k + 1) * 256].max() for k in range(16)])


def prof(e, compases):
    v = np.concatenate([e[int(c * T * sr):int((c + 1) * T * sr)] for c in compases])
    return round(20 * np.log10(np.percentile(v, 95) / (np.percentile(v, 10) + 1e-9)), 1)


med = {}
for nombre, comp, groove in (('funk de una nota (7-10)', range(6, 10), B.GROOVE_A),
                             ('vuelve otro groove (16-18)', range(15, 18), B.GROOVE_B)):
    med[nombre] = {}
    for b in BANDAS:
        a = doblar(env[b], comp); e = esperado(groove[b], B.TAU[b])
        med[nombre][b] = {'corr_con_lo_escrito': round(float(np.corrcoef(a, e)[0, 1]), 3),
                          'casilla_mas_fuerte': int(a.argmax()), 'escrita': int(e.argmax())}
med['profundidad_dB (p95/p10)'] = {sec: {b: prof(env[b], comp) for b in BANDAS} for sec, comp in
                                   (('nota sola 1-3', range(0, 3)), ('groove 7-10', range(6, 10)),
                                    ('sin tiempo 13-14', range(12, 14)), ('otro groove 16-18', range(15, 18)))}


def espectro(comp):
    v = np.concatenate([m[int(c * T * sr):int((c + 1) * T * sr)] for c in comp])
    X = np.abs(np.fft.rfft(v)); f = np.fft.rfftfreq(len(v), 1 / sr)
    bordes = 55 * 2 ** (np.arange(0, 6.01, 1 / 3))
    return np.array([X[(f >= a) & (f < b)].sum() ** 2 for a, b in zip(bordes, bordes[1:])])


g, n = espectro(range(6, 10)), espectro(range(12, 14))
med['armonia_igual (corr log tercios de octava, groove vs sin tiempo)'] = round(float(np.corrcoef(np.log(g), np.log(n))[0, 1]), 3)
print(json.dumps(med, ensure_ascii=False, indent=1))
json.dump(med, open(B.AQUI / 'medidas-boceto.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
