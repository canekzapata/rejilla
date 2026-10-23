"""PNGs y GIF del proceso de suenan_juntos: la partitura, cada pista por su vía (spectrumsynth o gemelo) y la mezcla.

    python biblioteca/proceso_suenan_juntos.py biblioteca/suenan-juntos-<h> render/biblioteca-<h>
"""
import json, sys, wave, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile

out, render = Path(sys.argv[1]), Path(sys.argv[2]); h = out.name.rsplit('-', 1)[1]; pr = out / 'proceso'; pr.mkdir(exist_ok=False)
sys.path.insert(0, str(Path(__file__).parent)); import suenan_juntos as SJ
receta = json.loads((out / 'receta.json').read_text(encoding='utf-8'))
fn = lambda s: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', s)
TINTA = {'arpaboca': (236, 200, 140), 'saron': (150, 200, 235), 'marimba': (210, 160, 230), 'berimbau': (140, 225, 170), 'balafon': (240, 150, 120)}
W, FONDO = 1100, (10, 11, 16)


def nuevo(nombre):
    p = pr / nombre; assert not p.exists(), p; return p


def leer(p):
    sr, x = wavfile.read(p); x = x.astype(float); return sr, (x.mean(1) if x.ndim > 1 else x)


def espectro(x, sr, dur, alto=300, fmax=8000):
    N, hop = 4096, 1024; win = np.hanning(N); fr = [np.abs(np.fft.rfft(x[i:i + N] * win)) for i in range(0, min(len(x), int(dur * sr)) - N, hop)]
    S = 20 * np.log10(np.array(fr).T + 1e-9); f = np.fft.rfftfreq(N, 1 / sr)
    filas = np.geomspace(50, fmax, alto)[::-1]; img = S[np.searchsorted(f, filas)]
    return np.clip((img - (img.max() - 65)) / 65, 0, 1)


def panel(img, tinta, titulo, nota):
    rgb = (np.power(img[..., None], 1.3) * np.array(tinta) + np.array(FONDO) * (1 - img[..., None])).astype(np.uint8)
    pic = Image.fromarray(rgb).resize((W, img.shape[0]), Image.BILINEAR); can = Image.new('RGB', (W, img.shape[0] + 64), FONDO); can.paste(pic, (0, 60))
    d = ImageDraw.Draw(can); d.text((16, 10), titulo, font=fn(21), fill=(240, 232, 218)); d.text((16, 36), nota, font=fn(14), fill=(150, 150, 165)); return can


ev = SJ.partitura(); dur = max(e[1] for e in ev) + 2.0
# 01 · la partitura: cada instrumento en su renglón, cada nota en su altura
can = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(can); d.text((16, 10), '01  partitura: quién entra y cuándo (9 compases, 100 bpm, In sobre D)', font=fn(19), fill=(240, 232, 218))
filas = list(TINTA); x_ = lambda t: 130 + int(t / dur * (W - 150))
for k, inst in enumerate(filas):
    y0 = 50 + k * 72; d.text((16, y0 + 24), inst, font=fn(15), fill=TINTA[inst]); d.line([130, y0 + 66, W - 20, y0 + 66], fill=(32, 34, 46))
    notas = [e for e in ev if e[0] == inst]; lo, hi = min(e[2] for e in notas), max(e[2] for e in notas) + 1
    for _, t, m, v, dd, _ in notas:
        yy = y0 + 60 - int((m - lo) / max(1, hi - lo) * 52); d.rectangle([x_(t), yy - 3, max(x_(t) + 2, x_(t + dd)), yy + 2], fill=tuple(int(c * (.45 + .55 * v)) for c in TINTA[inst]))
can.save(nuevo(f'01-partitura-{h}.png'))
# 02–06 · cada pista por su vía
paneles = []
for k, inst in enumerate(filas):
    sr, x = leer(render / f'{inst}.wav'); m = receta['medidas'][inst]
    nota = (f"vía: modos escritos en la rejilla → spectrumsynth · {m['modos']} segmentos · prueba exacta {m['error_exacto']:.1e}" if 'modos' in m['via']
            else f"vía: gemelo numpy de web.js · {m['gemelo_vs_web_db']} dB contra Web Audio")
    p = panel(espectro(x, sr, dur, 220), TINTA[inst], f'{k + 2:02d}  {inst}', nota); p.save(nuevo(f'{k + 2:02d}-{inst}-{h}.png')); paneles.append(p)
# 07 · la mezcla
sr, x = leer(render / 'mezcla.wav'); mezcla = panel(espectro(x, sr, dur, 360), (236, 228, 214), '07  mezcla: los cinco juntos', 'cuarto pequeño y loudnorm −14, como las canciones de rejilla')
mezcla.save(nuevo(f'07-mezcla-{h}.png'))
# GIF: las pistas se van sumando (cada panel un momento) y luego la mezcla con el cursor que avanza
cuadros = []
for p in paneles: cuadros += [p.resize((W, 424))] * 2
for j in range(1, 21):
    f = mezcla.copy(); dr = ImageDraw.Draw(f); xx = int(W * j / 20); dr.rectangle([xx, 60, W, mezcla.height - 4], fill=FONDO); dr.line([xx, 60, xx, mezcla.height - 4], fill=(240, 232, 218), width=2); cuadros.append(f.resize((W, 424)))
cuadros += [mezcla.resize((W, 424))] * 4
gif = out / f'suenan-juntos-{h}.gif'; assert not gif.exists()
cuadros[0].save(gif, save_all=True, append_images=cuadros[1:], duration=280, loop=0, optimize=True)
print(gif, gif.stat().st_size // 1024, 'KB', len(cuadros) * .28, 's')
