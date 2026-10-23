"""Mediciones corregidas del loop B (sobre los audios ya renderizados de las demos)."""
import json, math
import numpy as np
from scipy.io import wavfile
from motor import M, S, T, F, SR_OUT, afinar, arena, Pista
import demos as D

MED = {}


def f0_ancho(x, sr, lo=70, hi=1200):
    """Tono por autocorrelación normalizada (YIN simplificado) en un rango ancho."""
    n = len(x); seg = x[int(n * .3):int(n * .8)]; seg = seg - seg.mean()
    L = len(seg); taus = np.arange(int(sr / hi), int(sr / lo))
    d = np.array([np.sum((seg[:L - t] - seg[t:]) ** 2) for t in taus])
    cmnd = d * np.arange(1, len(d) + 1) / np.cumsum(d)
    debajo = np.where(cmnd < 0.15)[0]
    i = debajo[0] if len(debajo) else np.argmin(cmnd)
    while i + 1 < len(cmnd) and cmnd[i + 1] < cmnd[i]: i += 1
    return sr / taus[i]


# d05: el robot, con detector de rango ancho
letras = ['uve', 'i', 'de', 'a', 'e', 'ene', 'o', 'te', 'erre', 'o', 'planeta']
_, voces = D.LAM
alturas = [voces[0] + 12, voces[3] - 12, voces[2] + 12, voces[1], voces[3] + 12, voces[0], voces[2] - 12,
           voces[3] + 12, voces[1] - 12, voces[0] + 12, voces[1]]
MED['d05_robot_st'] = [(s, n, round(12 * math.log2(f0_ancho(afinar(s, n, 'zira', largo=2.2 * T / 16), S) / M.hz(n)), 2))
                       for s, n in zip(letras, alturas)]

# d07: entropía. Espectro largo de cada compás vs el compás 0, y envolvente (10 ms) vs el compás 0
sr, y = wavfile.read(D.R / 'd07.wav'); y = y[:, 0].astype(float)
B = int(T * sr); bars = [y[b * B:(b + 1) * B] for b in range(4)]
spec = [np.log10(np.abs(np.fft.rfft(b)) + 1e-9) for b in bars]
w = int(.01 * sr)
env = [np.sqrt(np.convolve(b ** 2, np.ones(w) / w, 'same'))[::w] for b in bars]
sm = lambda a: np.convolve(a, np.ones(400) / 400, 'same')
MED['d07_espectro_largo_corr'] = [round(float(np.corrcoef(sm(spec[0]), sm(s))[0, 1]), 3) for s in spec]
MED['d07_envolvente_corr'] = [round(float(np.corrcoef(env[0], e)[0, 1]), 3) for e in env]

# d11: prolación. Desplazamiento en log-frecuencia que mejor alinea cada lectura con la de 1×
def logspec(x, sr):
    X = np.abs(np.fft.rfft(x)); fr = np.fft.rfftfreq(len(x), 1 / sr)
    g = np.geomspace(40, 8000, 6000)
    return np.log10(np.interp(g, fr, X) + 1e-9), g
ref, g = logspec(wavfile.read(D.R / 'd11-0.wav')[1][:, 0].astype(float), SR_OUT)
paso = math.log(g[1] / g[0])
razones = []
for k in range(3):
    s, _ = logspec(wavfile.read(D.R / f'd11-{k}.wav')[1][:, 0].astype(float), SR_OUT)
    lags = range(0, 1000); c = [np.corrcoef(ref[:len(ref) - l], s[l:])[0, 1] for l in lags]
    razones.append(round(math.exp(paso * int(np.argmax(c))), 4))
MED['d11_razon_medida'] = razones

# arena: barrido de calidad JPEG, error de la columna en dB contra el original, por generación
P = Pista('arena', 5); D.groove(P, 4, [D.LAM])
ZL, _ = P.escribir()
barr = {}
for cal in (45, 70, 85):
    fila = []
    for g in (1, 2, 4, 8, 16):
        Z2 = arena(ZL, [0, 1, 2, 3], [g] * 4, calidad=cal)
        fila.append(round(float(20 * np.log10(np.linalg.norm(Z2[1] - ZL[1]) / np.linalg.norm(ZL[1]))), 1))
    barr[cal] = fila
MED['arena_error_dB_por_calidad_gen1-2-4-8-16'] = barr

print(json.dumps(MED, ensure_ascii=False, indent=1))
viejo = json.load(open(D.DEMOS / 'medidas.json', encoding='utf-8')); viejo.update(MED)
for k in ('d05_robot', 'd07_factor_de_cresta', 'd11_picos_Hz', 'd11_razones'): viejo.pop(k, None)   # mediciones mal planteadas
json.dump(viejo, open(D.DEMOS / 'medidas.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
