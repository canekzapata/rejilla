"""El proceso del loop de voces ligadas (acuerdo de nombres del 13 de octubre: carpeta exclusiva
`proceso/voces-<hash12>/`, nada se escribe encima).

  01-05  una ficha por voz: espectrograma, envolvente (dB) y curva de altura medida
  06     la comparación: huecos, golpe de ataque, transiciones cortadas, glissando
  GIF    las cinco fichas con su cabeza lectora
  m4a    el muestrario TEJIDO: las cinco voces encadenadas cada cuatro compases sobre la portadora
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, sosfiltfilt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).parent.parent))
from colores import oklch, fuente
import ligadas as LG
import importlib.util as _iu                            # las utilidades de la máquina (portadora sin raya, sala afinada);
_spec = _iu.spec_from_file_location('demos_maquina', Path(__file__).parent.parent / 'maquina' / 'demos.py')
D = _iu.module_from_spec(_spec); _spec.loader.exec_module(D)   # por ruta: pixeles/ también tiene un demos.py
V = LG.V

VERSION = 'voces-ligadas 1'
AQUI = Path(__file__).parent; R = LG.R
VOCES = [('v0', 'robótica (referencia, sin tocar)'), ('v1', 'ligada'), ('v2', 'voz de arco'),
         ('v3', 'sostenuto espectral'), ('v4', 'vocoder ligado')]
MED = json.load(open(R / 'medidas.json', encoding='utf-8'))
CLAVE = {'v0': 'v0 robótica', 'v1': 'v1 ligada', 'v2': 'v2 voz de arco', 'v3': 'v3 sostenuto', 'v4': 'v4 vocoder ligado'}

nonce = os.urandom(16).hex(); h = hashlib.sha256()
for p in [AQUI / 'ligadas.py', Path(__file__)] + [R / f'{v}.wav' for v, _ in VOCES]: h.update(p.read_bytes())
h.update(VERSION.encode()); h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]
SAL = AQUI / 'proceso' / f'voces-{C}'; SAL.parent.mkdir(exist_ok=True); os.mkdir(SAL)

h0 = 300 + np.random.default_rng(1031).uniform(-15, 15)
hexo = lambda L, Cc, hh: '#%02x%02x%02x' % tuple(int(c) for c in oklch(L, Cc, hh))
FONDO, TXT = hexo(.12, .04, h0), hexo(.92, .03, h0 + 40)
LINEA = {v: hexo(.78, .15, h0 - 250 + 55 * i) for i, (v, _) in enumerate(VOCES)}


def lee(v):
    sr, x = wavfile.read(R / f'{v}.wav'); x = x.astype(float)
    if x.ndim > 1: x = x.mean(1)
    return (resample_poly(x, 160, 147) if sr == LG.SRV else x) / (np.abs(x).max() + 1e-12)


X = {v: lee(v) for v, _ in VOCES}
fichas = []
for i, (v, nombre) in enumerate(VOCES):
    x = X[v]; sr = LG.SR
    fig = plt.figure(figsize=(12, 6.2), facecolor=FONDO)
    ax = fig.add_axes([.06, .38, .9, .5]); ax.set_facecolor(FONDO)
    ax.specgram(x, NFFT=2048, Fs=sr, noverlap=1792, cmap='magma', vmin=-110, vmax=-20, scale='dB')
    ax.set_yscale('symlog', linthresh=500); ax.set_ylim(80, 9000); ax.set_xlim(0, len(x) / sr)
    f0, son = LG.A.curva(resample_poly(x, 147, 160), LG.SRV); t = np.arange(len(f0)) / LG.SRV
    ax.plot(t[::200], f0[::200], color=LINEA[v], lw=2.2)
    ax.tick_params(colors=TXT, labelsize=8); [s.set_color(TXT) for s in ax.spines.values()]
    for a in LG.INI: ax.axvline(a, color=TXT, alpha=.18, lw=.8)
    ax2 = fig.add_axes([.06, .08, .9, .24]); ax2.set_facecolor(FONDO)
    w = int(.01 * sr); e = np.array([np.sqrt((x[k:k + w] ** 2).mean()) for k in range(0, len(x) - w, w)]) + 1e-9
    ax2.fill_between(np.arange(len(e)) * .01, -60, np.maximum(20 * np.log10(e / e.max()), -60), color=LINEA[v], alpha=.8)
    ax2.set_ylim(-60, 2); ax2.set_xlim(0, len(x) / sr); ax2.axhline(-40, color=TXT, alpha=.3, lw=.8, ls='--')
    ax2.tick_params(colors=TXT, labelsize=8); [s.set_color(TXT) for s in ax2.spines.values()]
    ax2.set_ylabel('dB', color=TXT, fontsize=8)
    m = MED[CLAVE[v]]
    fig.text(.06, .94, f'{v} · {nombre}', color=TXT, fontsize=15, family='monospace')
    fig.text(.06, .905, f'huecos {m["huecos_pct"]} %  ·  golpe {m["ataque_dB_por_10ms_p95"]} dB/10ms  ·  '
             f'transiciones cortadas {m["transiciones_cortadas_pct"]} %  ·  glissando {m["glissando_ms_mediana"]} ms   '
             f'(línea: altura medida; abajo: envolvente, la raya es -40 dB)', color=LINEA[v], fontsize=8.5, family='monospace')
    p = SAL / f'{i + 1:02d}-{v}-{nombre.split(" (")[0].replace(" ", "-")}-{C}.png'
    with open(p, 'xb') as f: fig.savefig(f, format='png', dpi=100, facecolor=FONDO)
    plt.close(fig); fichas.append(Image.open(p).convert('RGB'))

# 06 la comparación
fig, axs = plt.subplots(1, 4, figsize=(13, 4.2), facecolor=FONDO)
for ax, (k, tit) in zip(axs, (('huecos_pct', 'huecos en la frase (%)'), ('ataque_dB_por_10ms_p95', 'golpe de ataque (dB/10 ms)'),
                              ('transiciones_cortadas_pct', 'cambios de nota cortados (%)'), ('glissando_ms_mediana', 'glissando (ms)'))):
    ax.set_facecolor(FONDO)
    vals = [MED[CLAVE[v]][k] or 0 for v, _ in VOCES]
    ax.bar(range(5), vals, color=[LINEA[v] for v, _ in VOCES])
    ax.set_xticks(range(5)); ax.set_xticklabels([v for v, _ in VOCES], color=TXT, fontsize=9)
    ax.set_title(tit, color=TXT, fontsize=10, family='monospace'); ax.tick_params(colors=TXT, labelsize=8)
    [s.set_color(TXT) for s in ax.spines.values()]
fig.suptitle('cinco voces, la misma frase: de la explosión al arco', color=TXT, family='monospace')
fig.tight_layout()
with open(SAL / f'06-comparacion-{C}.png', 'xb') as f: fig.savefig(f, format='png', dpi=100, facecolor=FONDO)
plt.close(fig)

# GIF: cada ficha con su cabeza lectora
frames = []
for (v, _), im in zip(VOCES, fichas):
    im = im.resize((im.width * 2 // 3, im.height * 2 // 3), Image.LANCZOS)
    x0, x1 = int(.06 * im.width), int(.96 * im.width); dur = len(X[v]) / LG.SR
    for k in range(8):
        t = LG.INI[0] + (LG.INI[-1] + LG.DUR[-1] - LG.INI[0]) * k / 7
        fr = im.copy(); d = ImageDraw.Draw(fr); xx = x0 + (x1 - x0) * t / dur
        d.line([(xx, int(.1 * im.height)), (xx, int(.92 * im.height))], fill=tuple(int(c) for c in oklch(.95, .05, h0 + 40)), width=2)
        frames.append(fr)
pal = frames[9].quantize(colors=200, method=Image.Quantize.MEDIANCUT)
frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'voces-ligadas-s{LG.SEM}-{C}.gif'
with open(gif, 'xb') as f: frames[0].save(f, 'GIF', save_all=True, append_images=frames[1:], duration=240, loop=0, optimize=True)

# el muestrario tejido: cada voz entra cada 4 compases, con la portadora y su latido de hilo
CADA = 4
total = CADA * len(VOCES) + 2; n = D.L(total)
mezcla_ = np.zeros((n, 2))
for i, (v, _) in enumerate(VOCES):
    x = X[v] / (np.sqrt((X[v] ** 2).mean()) + 1e-12) * .1
    st = np.stack([x, x], 1)
    seco, envio = V.en_plano(D.largo(st, n - D.L(CADA * i)), 'medio')
    mezcla_[D.L(CADA * i):] += seco + .5 * V.sala_afinada(envio, 2.2, .6, i)
plan = lambda b: {'groove': 0, 'halo': .55, 'timbre': .5, 'latido': .8}
hilo = D.largo(D.liso('hilo-voces', lambda off: D.portadora_off(total, plan, off), total), n)
hilo = hilo / (np.sqrt((hilo ** 2).mean()) + 1e-12) * .1 * .2
y = mezcla_ + hilo
wav = R / 'muestrario-voces.wav'
wavfile.write(wav, LG.SR, (y / np.abs(y).max() * .9).astype(np.float32))
m4a = AQUI / f'voces-ligadas-s{LG.SEM}-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
mm = np.abs(y.mean(1)); mm /= mm.max(); w = int(.05 * LG.SR)
e = 20 * np.log10(np.array([mm[i:i + w].max() for i in range(0, len(mm) - w, w)]) + 1e-9)
silencio_max = 0; run = 0
for v_ in e:
    run = run + 1 if v_ < -60 else 0; silencio_max = max(silencio_max, run)

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receta = {'id': ID, 'version': VERSION, 'nonce': nonce, 'semilla': LG.SEM, 'texto': LG.TEXTO, 'medidas': MED,
          'muestrario': {'cada_compases': CADA, 'orden': [v for v, _ in VOCES], 'silencio_mas_largo_s': round(silencio_max * .05, 2)},
          'archivos': {str(p.relative_to(AQUI)).replace('\\', '/'): sha(p) for p in sorted(SAL.glob('*.png')) + [gif, m4a]}}
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as f: json.dump(receta, f, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {240 * len(frames) / 1000:.1f} s · muestrario {n / LG.SR:.0f} s · silencio más largo {silencio_max * .05:.2f} s')
