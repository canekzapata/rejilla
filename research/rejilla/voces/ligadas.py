"""Voces ligadas: cuatro voces nuevas, más violín que explosión, junto a la cantante robótica (que NO se toca:
se importa de yoshi 16 tal cual y canta primero, como referencia). Las cinco cantan la misma frase de
«NADIE A BORDO» con las mismas notas y el mismo ritmo, a 103.125 bpm.

  v0 robótica          la cantante de yoshi 16 como está (sílabas-isla, consonante entera, altura en escalones)
  v1 ligada            sílabas encimadas, consonantes en sordina, portamento, vibrato tardío, arco por frase
  v2 voz de arco       una cuerda frotada (altura continua) que pronuncia: lleva la envolvente espectral de v1
  v3 sostenuto         la robótica tal cual, pero cada espectro se queda sonando y se funde con el siguiente (Scelsi)
  v4 vocoder ligado    portadora que se desliza con la melodía; envolventes lentas (60 ms) y consonantes atenuadas

    python voces/ligadas.py          → render/voces/v0..v4.wav + medidas.json
"""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfiltfilt, iirpeak, lfilter, stft, istft, resample_poly

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent / 'maquina'))
import nave as V                                        # tempo, melodía nómada, silabeo, cantante (vía pixeles)

K = V.PI.K                                              # la cantante de yoshi 16 (sin modificar)
A = K.A                                                 # su PSOLA y su curva de tono
SRV = K.SR                                              # 44.1 kHz: a lo que dice el TTS
SR = 48000
R = AQUI.parent / 'render' / 'voces'; R.mkdir(parents=True, exist_ok=True)
SEM = 7
TEXTO = 'veo la Tierra entera del tamaño de mi mano,'
COMPASES = 3.5


def partitura():
    sil, palabras = V.PI.silabear(TEXTO)
    tonicas, k = set(), 0
    for p, n in zip(TEXTO.replace(',', ' ').split(), palabras):
        try: tonicas.add(k + V.SIL.tonica(p))
        except Exception: tonicas.add(k)
        k += n
    notas = V.nomada(len(sil), tonicas, SEM, 57.0)
    pos, dur = V.ritmo_hablado(palabras, tonicas, COMPASES, SEM)
    t16 = V.T / 16
    return sil, palabras, notas, [p * t16 + .25 for p in pos], [d * t16 for d in dur]


SIL_, PALABRAS, NOTAS, INI, DUR = partitura()
LARGO = INI[-1] + DUR[-1] + 1.9


# ───────────── la curva de altura de lo ligado ─────────────
def curva_ligada(sr, glis=.085, vib_st=.2, vib_hz=5.4, retraso=.2):
    """MIDI por muestra: cada nota se sostiene y se desliza a la siguiente en los últimos `glis` s (cambio
    de dedo); el vibrato entra tarde (después de `retraso` s de nota), como en el violín."""
    n = int(LARGO * sr); t = np.arange(n) / sr
    m = np.full(n, NOTAS[0], float)
    for i, (a, nota) in enumerate(zip(INI, NOTAS)):
        b = INI[i + 1] if i + 1 < len(INI) else LARGO
        sel = (t >= a) & (t < b); m[sel] = nota
        if i + 1 < len(INI):
            g0 = b - glis; s2 = (t >= g0) & (t < b)
            u = (t[s2] - g0) / glis; u = u * u * (3 - 2 * u)
            m[s2] = nota + (NOTAS[i + 1] - nota) * u
    prof = np.zeros(n)
    for i, a in enumerate(INI):
        b = INI[i + 1] if i + 1 < len(INI) else LARGO
        sel = (t >= a) & (t < b)
        prof[sel] = vib_st * np.clip((t[sel] - a - retraso) / .3, 0, 1) * (1 if b - a > .32 else .3)
    rng = np.random.default_rng(SEM)
    hz = vib_hz + .25 * np.sin(2 * np.pi * t * .7 + rng.uniform(0, 6))
    return m + prof * np.sin(2 * np.pi * np.cumsum(hz) / sr)


def hz(midi): return 440 * 2 ** ((np.asarray(midi) - 69) / 12)


# ───────────── v0: la robótica, como está ─────────────
def v0():
    frase = {'texto': TEXTO, 'palabras': PALABRAS,
             'silabas': [{'t': a, 'dur': d * .96, 'nota': n, 'txt': s} for s, n, a, d in zip(SIL_, NOTAS, INI, DUR)]}
    y, _ = K.canta([frase], LARGO)
    return y


# ───────────── v1: ligada ─────────────
def estira(v, largo, rng):
    """Alargar una vocal con lazos de su parte estable, fundidos (sin repetir siempre el mismo pedazo)."""
    if len(v) >= largo: return v[:largo]
    p0, p1 = int(len(v) * .2), int(len(v) * .8)
    if p1 - p0 < int(SRV * .04): return np.pad(v, (0, largo - len(v)), mode='reflect')[:largo] if len(v) > 1 else np.zeros(largo)
    out = v[:p1].copy(); f = min(int(SRV * .03), (p1 - p0) // 3)
    while len(out) < largo - (len(v) - p1):
        a = rng.integers(p0, max(p0 + 1, p1 - f * 3)); lazo = v[a:p1]
        r = np.linspace(0, 1, f); out[-f:] = out[-f:] * np.cos(r * np.pi / 2) + lazo[:f] * np.sin(r * np.pi / 2)
        out = np.concatenate([out, lazo[f:]])
    return np.concatenate([out[:largo - (len(v) - p1)], v[p1:]])[:largo]


def v1(sordina=.3, encime=.07):
    rng = np.random.default_rng(SEM)
    segs, como = K.segmenta(TEXTO, PALABRAS)
    curva = curva_ligada(SRV)
    n = int(LARGO * SRV); voc = np.zeros(n); con = np.zeros(n)
    for i, ((x, a, b, p), nota) in enumerate(zip(segs, NOTAS)):
        seg = x[a:b]
        _, son = A.curva(seg, SRV); idx = np.nonzero(son)[0]
        if len(idx) > SRV * .03: i0, i1 = idx[0], idx[-1]
        else: i0, i1 = 0, len(seg)
        c, v = seg[:i0], seg[i0:i1]
        o = int(INI[i] * SRV)
        ultima = i + 1 == len(INI)
        fin = int(INI[i + 1] * SRV) if not ultima else int((INI[i] + DUR[i] + .7) * SRV)
        L = fin - o + int(encime * SRV)
        v, _ = A.aplana(v, SRV, nota) if len(v) > SRV * .03 else (v, None)
        v = estira(v, L, rng)
        destino = lambda k, o=o: hz(curva[min(o + k, n - 1)])
        v, _ = A.psola(v, SRV, destino)                        # la altura del arco: portamento + vibrato tardío
        e = np.ones(len(v)); fi, fo = int(.035 * SRV), int((.55 if ultima else encime) * SRV)   # la última se dispersa
        e[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2; e[-fo:] = np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
        z = min(n, o + len(v)); voc[o:z] += (v * e)[:z - o]
        c = c[-int(.045 * SRV):]                                # la consonante: corta, en sordina, antes del tiempo
        if len(c) > 8:
            c = sosfiltfilt(butter(2, 5500, 'lowpass', fs=SRV, output='sos'), c) * sordina
            ce = np.sin(np.linspace(0, np.pi, len(c))) ** .5
            a0 = max(0, o - len(c) + int(.012 * SRV)); con[a0:a0 + len(c)] += (c * ce)[:n - a0]
    t = np.arange(n) / SRV; u = np.clip((t - INI[0]) / (INI[-1] + DUR[-1] - INI[0]), 0, 1)
    arco = .62 + .38 * np.sin(np.pi * u) ** .8                 # una sola respiración por frase
    return (voc * arco + con) / (np.abs(voc).max() + 1e-12)


# ───────────── v2: la voz de arco (una cuerda que pronuncia) ─────────────
def cepstral(M, coef=34):
    """Envolvente espectral suave (cepstro con liftro) de cada cuadro de magnitud M (frecuencia × cuadros)."""
    c = np.fft.irfft(np.log(M + 1e-9), axis=0)
    c[coef:-coef] = 0
    return np.exp(np.fft.rfft(c, axis=0).real)[:M.shape[0]]


def cuerda(curva_midi, sr, semilla=0):
    """Cuerda frotada: armónicos con fase continua, un poco de jitter de arco y ruido de crin."""
    rng = np.random.default_rng(semilla); n = len(curva_midi)
    f = hz(curva_midi) * (1 + .0018 * np.convolve(rng.normal(0, 1, n), np.ones(400) / 400, 'same') * 20)
    ph = 2 * np.pi * np.cumsum(f) / sr; y = np.zeros(n)
    for k in range(1, 60):
        fk = k * f
        if fk.min() > 9000: break
        y += np.sin(k * ph + rng.uniform(0, 6)) / k ** .95 * (fk < 9000) * (1 + .08 * np.sin(2 * np.pi * rng.uniform(.3, 1.2) * np.arange(n) / sr))
    crin = sosfiltfilt(butter(2, [2500, 9000], 'bandpass', fs=sr, output='sos'), rng.normal(0, 1, n)) * .05
    return y / np.abs(y).max() + crin


def v2(fuente):
    """La cuerda lleva la envolvente espectral de la voz ligada (cuadro a cuadro), suavizada en el tiempo."""
    x = resample_poly(fuente, 160, 147)                        # 44.1 → 48 kHz
    cu = curva_ligada(SR)[:len(x)]; x = x[:len(cu)]
    s = cuerda(cu, SR, SEM)
    nper = 2048
    _, _, X = stft(x, SR, nperseg=nper, noverlap=nper - 256); _, _, Sx = stft(s, SR, nperseg=nper, noverlap=nper - 256)
    Ev, Es = cepstral(np.abs(X)), cepstral(np.abs(Sx))
    Ev = np.apply_along_axis(lambda r: np.convolve(r, np.ones(5) / 5, 'same'), 1, Ev)   # ~25 ms: ligado
    Y = Sx / (Es + 1e-9) * Ev
    _, y = istft(Y, SR, nperseg=nper, noverlap=nper - 256)
    for fc, q, g in ((290, 3, .5), (470, 4, .3), (2900, 2.5, .35)):                       # la caja del violín
        b, a = iirpeak(fc, q, SR); y = y + g * lfilter(b, a, y)
    return y / (np.abs(y).max() + 1e-12)


# ───────────── v3: la robótica, sostenida (sostenuto espectral) ─────────────
def v3(robotica, sostener=1.3, mezcla=.85):
    x = resample_poly(robotica, 160, 147); nper, hop = 4096, 512
    _, _, X = stft(x, SR, nperseg=nper, noverlap=nper - hop)
    M = np.abs(X); S = np.zeros_like(M); cae = 10 ** (-3 / (sostener * SR / hop))
    for j in range(M.shape[1]):
        S[:, j] = np.maximum(M[:, j], (S[:, j - 1] * cae) if j else 0)
    k = np.arange(M.shape[0])[:, None]
    rng = np.random.default_rng(SEM)
    fase = np.cumsum(np.broadcast_to(2 * np.pi * k * hop / nper, M.shape) + rng.normal(0, .35, M.shape), axis=1)
    _, s = istft(S * np.exp(1j * fase), SR, nperseg=nper, noverlap=nper - hop)
    s = s[:len(x)]; s = np.pad(s, (0, len(x) - len(s)))
    y = .6 * x / (np.abs(x).max() + 1e-12) + mezcla * s / (np.abs(s).max() + 1e-12)
    return y / np.abs(y).max()


# ───────────── v4: el vocoder ligado ─────────────
def v4(moduladora, bandas=22):
    x = resample_poly(moduladora, 160, 147)
    cu = curva_ligada(SR)[:len(x)]; x = x[:len(cu)]; n = len(x)
    bordes = np.geomspace(110, 5200, bandas + 1); centros = np.sqrt(bordes[:-1] * bordes[1:])
    lp = butter(2, 8, 'lowpass', fs=SR, output='sos')                                   # envolventes de ~60 ms
    E = np.array([sosfiltfilt(lp, np.abs(sosfiltfilt(butter(3, [lo, hi], 'bandpass', fs=SR, output='sos'), x)))
                  for lo, hi in zip(bordes, bordes[1:])]).clip(0)
    # consonantes atenuadas: lo agudo y sordo pesa .3
    sordo = sosfiltfilt(lp, np.abs(sosfiltfilt(butter(3, 4000, 'highpass', fs=SR, output='sos'), x)))
    sonoro = sosfiltfilt(lp, np.abs(sosfiltfilt(butter(3, [100, 1200], 'bandpass', fs=SR, output='sos'), x)))
    voz = np.clip(sonoro / (sonoro + sordo + 1e-9), .3, 1)
    f = hz(cu); ph = 2 * np.pi * np.cumsum(f) / SR; y = np.zeros(n)
    lc = np.log(centros)
    rng = np.random.default_rng(SEM)
    for k in range(1, 48):
        fk = k * f
        pos = np.interp(np.log(np.clip(fk, 1, None)), lc, np.arange(bandas))
        i0 = np.clip(np.floor(pos).astype(int), 0, bandas - 2); w = np.clip(pos - i0, 0, 1)
        amp = E[i0, np.arange(n)] * (1 - w) + E[i0 + 1, np.arange(n)] * w
        amp *= (fk > 100) & (fk < 5200)
        y += amp * np.sin(k * ph + rng.uniform(0, 6))
    y *= voz
    return y / (np.abs(y).max() + 1e-12)


# ───────────── medir ─────────────
def medir(y, sr):
    """huecos: % de cuadros de 10 ms bajo -40 dB (del máximo) dentro de la frase · ataque: percentil 95 de la
    subida de la envolvente (dB por 10 ms) · transiciones: % de cambios de nota con la línea cortada y mediana del glissando 10→90 %."""
    a, b = int(INI[0] * sr), int((INI[-1] + DUR[-1]) * sr)
    seg = y[a:b]; w = int(.01 * sr)
    rms = np.array([np.sqrt((seg[i:i + w] ** 2).mean()) for i in range(0, len(seg) - w, w)]) + 1e-9
    db = 20 * np.log10(rms / rms.max())
    huecos = float((db < -40).mean())
    e5 = 20 * np.log10(np.array([np.sqrt((seg[i:i + w // 2] ** 2).mean()) for i in range(0, len(seg) - w // 2, w // 2)]) + 1e-9)
    subida = np.diff(e5) * 2                                    # dB por 10 ms
    ataque = float(np.percentile(subida[subida > 0], 95)) if (subida > 0).any() else 0.0
    # transiciones: en cada cambio de nota, ¿la línea se corta (hueco sordo) o se desliza, y en cuánto tiempo?
    x44 = resample_poly(y, 147, 160) if sr == SR else y
    f0, son = A.curva(x44, SRV)
    m = 69 + 12 * np.log2(f0 / 440)
    cortes, glis = 0, []
    for i in range(len(INI) - 1):
        d = NOTAS[i + 1] - NOTAS[i]
        if abs(d) < .5: continue
        a0, b0 = int((INI[i + 1] - .15) * SRV), int((INI[i + 1] + .15) * SRV)
        tramo = m[a0:b0:int(SRV * .002)]
        if np.isnan(tramo).mean() > .15: cortes += 1; continue
        tramo = np.interp(np.arange(len(tramo)), np.nonzero(~np.isnan(tramo))[0], tramo[~np.isnan(tramo)])
        rel = (tramo - NOTAS[i]) / d
        try:
            t10 = np.nonzero(rel > .1)[0][0]; t90 = np.nonzero(rel > .9)[0][0]
            glis.append(max(0, t90 - t10) * 2)
        except IndexError: cortes += 1
    n_tr = sum(1 for i in range(len(INI) - 1) if abs(NOTAS[i + 1] - NOTAS[i]) >= .5)
    return {'huecos_pct': round(100 * huecos, 1), 'ataque_dB_por_10ms_p95': round(ataque, 1),
            'transiciones_cortadas_pct': round(100 * cortes / max(n_tr, 1), 1),
            'glissando_ms_mediana': int(np.median(glis)) if glis else None}


if __name__ == '__main__':
    med = {}
    y0 = v0(); wavfile.write(R / 'v0.wav', SRV, (y0 / np.abs(y0).max() * .8).astype(np.float32)); med['v0 robótica'] = medir(y0, SRV)
    y1 = v1(); wavfile.write(R / 'v1.wav', SRV, (y1 * .8).astype(np.float32)); med['v1 ligada'] = medir(y1, SRV)
    y2 = v2(y1); wavfile.write(R / 'v2.wav', SR, (y2 * .8).astype(np.float32)); med['v2 voz de arco'] = medir(y2, SR)
    y3 = v3(y0); wavfile.write(R / 'v3.wav', SR, (y3 * .8).astype(np.float32)); med['v3 sostenuto'] = medir(y3, SR)
    y4 = v4(y1); wavfile.write(R / 'v4.wav', SR, (y4 * .8).astype(np.float32)); med['v4 vocoder ligado'] = medir(y4, SR)
    med['_partitura'] = {'texto': TEXTO, 'silabas': SIL_, 'notas_midi': [round(n, 2) for n in NOTAS],
                         'inicios_s': [round(a, 3) for a in INI], 'duraciones_s': [round(d, 3) for d in DUR]}
    json.dump(med, open(R / 'medidas.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in med.items() if not k.startswith('_')}, ensure_ascii=False, indent=1))
