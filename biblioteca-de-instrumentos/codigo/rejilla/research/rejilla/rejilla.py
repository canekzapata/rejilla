"""Rejilla 01 · el país suena.

El país que se calcula avanza una generación por segundo. Con sample_rate 65536
y FFT de 65536, spectrumsynth de ffmpeg hace que una columna de la imagen dure
exactamente un segundo y que la fila k suene exactamente a k Hz. Así una
columna = una generación, y el compás ES el segundo del país.

Ley (la del Rhythmicon): la celda h de la ventana (h = 1..voces) es el armónico
h de 110 Hz y se pulsa h veces por segundo. Su valor mod 3 es la octava
(1 = 110·h Hz, 2 = 220·h Hz). Una voz es un peine de filas separadas h Hz
alrededor de su portadora; cada diente pesa 1/sqrt(1+x²) con fase -atan(x):
la serie de Fourier exacta de una senoidal amortiguada repetida h veces por
segundo (un pluck). Oído izquierdo: tinta ×1. Oído derecho: tinta ×7, la misma
ley siete veces más lenta, en sus propias celdas.

    python rejilla.py            # render + pruebas + PNGs + GIF
"""
import argparse, json, subprocess, sys, hashlib
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.io import wavfile

AQUI = Path(__file__).parent
S = 65536            # sample rate de la rejilla: 1 fila = 1 Hz, 1 columna = 1 s
H = S // 2           # filas por oído
BASE = 110.0         # A2: el armónico h suena en 110·h Hz
GAMMA = 0.5          # ancho del pluck en dientes: tau = 1/(2π·γ·h)
XMAX = 80.0          # hasta dónde llega el chasquido del ataque (en x)


def ventanas(voces, segundos):
    out = subprocess.run(['node', str(AQUI / 'pais-ventana.mjs'), str(voces), str(segundos)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def voz(Z, h, v):
    """Suma al espectro Z (complejo, H filas) la voz h con valor v."""
    c = BASE * h * v
    jmax = int(XMAX * GAMMA)
    j = np.arange(-jmax, jmax + 1)
    k = (c + j * h).astype(int)
    x = j / GAMMA
    taper = np.cos(np.pi / 2 * np.abs(x) / (XMAX + 1)) ** 2
    w = taper / np.sqrt(1 + x * x) / (4 * np.pi * GAMMA)
    ok = (k > 0) & (k < H)
    np.add.at(Z, k[ok], w[ok] * np.exp(-1j * np.arctan(x[ok])))


def partitura(d):
    seg, V = d['segundos'], d['voces']
    ZL = np.zeros((seg, H), complex)
    ZR = np.zeros((seg, H), complex)
    e = d['der']['escala']
    for t in range(seg):
        for h, v in enumerate(d['izq']['filas'][t], 1):
            if v: voz(ZL[t], h, v)
        for h, v in enumerate(d['der']['filas'][t // e], 1):
            if v: voz(ZR[t], h, v)
    return ZL, ZR


def imagenes(ZL, ZR):
    """Magnitud y fase en 16 bits, como las lee spectrumsynth:
    abajo el oído izquierdo, arriba el derecho; dentro de cada mitad, abajo = 0 Hz."""
    mag = np.concatenate([np.abs(ZR)[:, ::-1], np.abs(ZL)[:, ::-1]], axis=1).T
    pha = np.concatenate([np.angle(ZR)[:, ::-1], np.angle(ZL)[:, ::-1]], axis=1).T
    escala = mag.max()
    m16 = np.round(mag / escala * 65535).astype(np.uint16)
    p16 = np.round((pha + np.pi) / (2 * np.pi) * 65535).astype(np.uint16)
    return m16, p16, escala


def sintetizar(mpng, ppng, wav):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(mpng), '-i', str(ppng),
                    '-filter_complex',
                    '[0]format=gray16le[m];[1]format=gray16le[p];'
                    f'[m][p]spectrumsynth=sample_rate={S}:channels=2:scale=lin:slide=fullframe:'
                    'win_func=rect:overlap=0:orientation=vertical',
                    '-c:a', 'pcm_f32le', str(wav)], check=True)


def prueba_exacta(ZL, ZR, m16, p16, wav):
    """Lo que sale de ffmpeg contra la irfft de numpy de la misma imagen cuantizada."""
    sr, x = wavfile.read(wav)
    assert sr == S, sr
    errs = []
    for t in [0, 1, len(ZL) // 2, len(ZL) - 1]:
        for ch, mitad in [(0, slice(H, 2 * H)), (1, slice(0, H))]:
            mag = m16[mitad, t][::-1].astype(float) / 65535
            pha = p16[mitad, t][::-1].astype(float) / 65535 * 2 * np.pi - np.pi
            spec = np.zeros(S // 2 + 1, complex)
            spec[:H] = mag * np.exp(1j * pha)
            y = np.fft.irfft(spec, S) * S   # amplitud 2·mag por fila, como mide ffmpeg
            seg = x[t * S:(t + 1) * S, ch]
            errs.append(np.abs(seg - y).max() / (np.abs(y).max() + 1e-12))
    return max(errs)


def mezclar(crudo, final, m4a):
    """48 kHz, un poco de cruce entre oídos, cuarto corto como en RASTRUM, pico a -1 dB."""
    grafo = ("aresample=48000,pan=stereo|c0=c0+0.22*c1|c1=c1+0.22*c0,asplit[dry][w0];"
             "aevalsrc=d=3:s=48000:exprs='(random(0)*2-1)*exp(-t*1.6)|(random(1)*2-1)*exp(-t*1.6)',"
             "lowpass=f=5000[ir];[w0]highpass=f=180[w1];[w1][ir]afir=dry=0:wet=1[rev];"
             "[dry][rev]amix=inputs=2:weights=1 0.22:normalize=0,"
             "loudnorm=I=-15:TP=-1.5:LRA=11,aresample=48000")
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(crudo),
                    '-filter_complex', grafo, '-c:a', 'pcm_s16le', str(final)], check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(final),
                    '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)


def medir(wav):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(wav), '-af', 'ebur128=peak=true',
                        '-f', 'null', '-'], capture_output=True, text=True).stderr
    tail = r[r.rfind('Summary:'):]
    val = lambda key: tail.split(key)[1].split()[0]
    return {'I_LUFS': float(val('I:')), 'LRA': float(val('LRA:')), 'pico_dBTP': float(val('Peak:'))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voces', type=int, default=24)
    ap.add_argument('--segundos', type=int, default=98)
    a = ap.parse_args()

    render = AQUI / 'render'; render.mkdir(exist_ok=True)
    d = ventanas(a.voces, a.segundos)
    tag = 's20261002'
    json.dump(d, open(render / f'ventanas-{tag}.json', 'w'))

    ZL, ZR = partitura(d)
    m16, p16, escala = imagenes(ZL, ZR)
    mpng, ppng = render / f'magnitud-{tag}.png', render / f'fase-{tag}.png'
    Image.fromarray(m16).save(mpng); Image.fromarray(p16).save(ppng)

    crudo = render / f'crudo-{tag}.wav'
    sintetizar(mpng, ppng, crudo)
    err = prueba_exacta(ZL, ZR, m16, p16, crudo)
    print(f'prueba exacta: ffmpeg vs irfft, error relativo máx = {err:.2e}')
    assert err < 1e-3, 'spectrumsynth no está leyendo la rejilla como creemos'

    final, m4a = render / f'el-pais-suena-{tag}.wav', AQUI / f'el-pais-suena-{tag}.m4a'
    mezclar(crudo, final, m4a)
    m = medir(final)
    m['sha256_m4a'] = hashlib.sha256(m4a.read_bytes()).hexdigest()
    m['error_exacto'] = float(err)
    print(m)
    json.dump(m, open(AQUI / f'medidas-{tag}.json', 'w'), indent=1)


if __name__ == '__main__':
    main()
