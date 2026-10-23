"""PNG de antes y después (v2 → v3), con la MISMA escala de color para los dos (la de la v2; con escalas propias no se ve la diferencia): el grave de un drop (0–400 Hz, lineal) y la frase de Siringua (0.3–5 kHz).
    python comparar.py <entrega-v2> <entrega-v3>"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
A, Bv = sys.argv[1], sys.argv[2]; h = Bv.rsplit('-', 1)[1]; BAR = 1.5; SR = 48000; FONDO = (10, 11, 16)
fn = lambda n: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
def leer(d): sr, x = wavfile.read(os.path.join(d, os.path.basename(d) + '.wav')); return x.astype(float).mean(1) / 32768
def espectro(x, t0, t1, f0, f1, alto, N=8192, hop=1024, log=False):
    x = x[int(t0 * SR):int(t1 * SR)]; win = np.hanning(N); fr = [np.abs(np.fft.rfft(x[i:i + N] * win)) for i in range(0, len(x) - N, hop)]
    S = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(N, 1 / SR); filas = (np.geomspace(f0, f1, alto) if log else np.linspace(f0, f1, alto))[::-1]
    return S[np.searchsorted(f, filas)]
def panel(img, ref, tinta, alto):
    img = np.clip((img - (ref - 60)) / 60, 0, 1)
    return Image.fromarray((np.power(img[..., None], 1.2) * np.array(tinta) + np.array(FONDO) * (1 - img[..., None])).astype(np.uint8)).resize((780, alto))
v2, v3 = leer(A), leer(Bv)
im = Image.new('RGB', (1600, 640), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '06  antes (v2) → después (v3), misma escala de color', font=fn(20), fill=(240, 232, 218))
for k, (x, nom) in enumerate([(v2, 'v2'), (v3, 'v3')]):
    X = 20 + k * 800
    g = espectro(x, 26 * BAR, 28 * BAR, 0, 400, 250); v = espectro(x, 2 * BAR, 6 * BAR, 300, 5000, 250, N=2048, hop=512, log=True)
    if k == 0: rg, rv = g.max(), v.max()
    d.text((X, 44), f'{nom} · el grave de un drop (compases 26–28, 0–400 Hz)', font=fn(14), fill=(200, 200, 210)); im.paste(panel(g, rg, (236, 190, 130), 250), (X, 64))
    d.text((X, 330), f'{nom} · Siringua dice la frase (compases 2–6, 0.3–5 kHz)', font=fn(14), fill=(200, 200, 210)); im.paste(panel(v, rv, (150, 200, 235), 250), (X, 350))
p = os.path.join(Bv, 'proceso', f'06-antes-despues-misma-escala-s1810-{h}.png'); assert not os.path.exists(p); im.save(p); print(p)
