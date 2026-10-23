"""Proceso del piano preparado (instrumento 2 de «objetos que cantan»). Carpeta exclusiva proceso/piano-<id12>/.

  01  la misma nota (La3) sin preparar y con cada preparación: su espectro (los parciales los decide la física)
  02  medidas: afinación, inarmonía, T60 y zumbido por preparación
  03  el piano que se prepara mientras suena (espectrograma): el tornillo entra poco a poco
  GIF la cuerda con el tornillo entrando y el espectro que se vuelve campana
  m4a muestrario: normal, cada preparación, la frase a lo Cage, lo percutivo y el piano que se prepara
    python proceso_piano.py p4
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = Path(__file__).resolve().parent; R = AQUI / 'render'; ET = sys.argv[1]
TIPOS = ['normal', 'tornillo', 'tornillo-suelto', 'goma', 'papel', 'moneda']
ORDEN = TIPOS + ['cage', 'percusivo', 'se-prepara']
nonce = os.urandom(16).hex(); h = hashlib.sha256()
for f in [AQUI / 'motor' / 'piano.js', Path(__file__)] + [R / f'{ET}-piano-{n}.wav' for n in ORDEN]: h.update(f.read_bytes())
h.update(nonce.encode()); ID = h.hexdigest(); C = ID[:12]; SAL = AQUI / 'proceso' / f'piano-{C}'; os.mkdir(SAL)
MED = json.load(open(R / f'medidas-piano-{ET}.json', encoding='utf-8'))


def oklch(L, Cc, hh):
    a, b = Cc * np.cos(np.radians(hh)), Cc * np.sin(np.radians(hh))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = np.clip([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                   -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], 0, 1)
    rgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return tuple(int(round(c * 255)) for c in rgb)


def fuente(n):
    try: return ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
    except OSError: return ImageFont.load_default()


h0 = int(C[:4], 16) % 360
FONDO, TXT, TEN, REJ = oklch(.13, .02, h0), oklch(.92, .03, h0), oklch(.55, .04, h0), oklch(.25, .03, h0)
F, Fs, Fg = fuente(14), fuente(12), fuente(22); W = 1500
lee = lambda n: (lambda q: (q[0], q[1].astype(float) / 32768))(wavfile.read(R / f'{ET}-piano-{n}.wav'))


def png(im, n):
    with open(SAL / n, 'xb') as f: im.save(f, 'PNG')


# 01 La3 (la cuarta nota de la demo: t = 3 × 1.4 s) en cada preparación
im = Image.new('RGB', (W, 80 + 120 * len(TIPOS)), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'la misma tecla (La3, 220 Hz) sin preparar y con cada preparación: espectro 0-3 kHz', fill=TXT, font=Fg)
for k, tipo in enumerate(TIPOS):
    sr, x = lee(tipo); a = int((3 * 1.4 + .03) * sr); seg = x[a:a + 32768] * np.hanning(32768)
    S = 20 * np.log10(np.abs(np.fft.rfft(seg)) + 1e-9); fr = np.fft.rfftfreq(32768, 1 / sr); m = fr < 3000; S = S[m]; fr = fr[m]
    y0 = 60 + k * 120; col = oklch(.8, .13, h0 + 50 * k); d.text((30, y0), tipo, fill=col, font=F)
    Xs = lambda f: 180 + (W - 210) * f / 3000; Ys = lambda v: y0 + 105 - 95 * max(0, (v - S.max() + 55) / 55)
    for n in range(1, 14): d.line([(Xs(220 * n), y0 + 8), (Xs(220 * n), y0 + 106)], fill=REJ)
    d.line([(Xs(f), Ys(v)) for f, v in zip(fr[::2], S[::2])], fill=col, width=1)
d.text((30, im.height - 18), 'líneas tenues: los armónicos de 220 Hz (donde caerían en una cuerda sin preparar)', fill=TEN, font=Fs)
png(im, f'01-la-misma-tecla-{C}.png')

# 02 medidas (La3)
im = Image.new('RGB', (W, 120 + 34 * len(TIPOS)), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'medidas de La3 por preparación: afinación del parcial grave, inarmonía y T60', fill=TXT, font=Fg)
for j, h_ in enumerate(['preparación', 'f1 (cents)', 'inarmonía (cents)', 'T60 (s)']): d.text((30 + 260 * j, 64), h_, fill=TEN, font=F)
for i, tipo in enumerate(TIPOS):
    q = [r for r in MED[tipo] if r['nota'] == 57][0]; y = 96 + 34 * i
    for j, v in enumerate([tipo, f"{q['f1_cents']:+d}", q['inarmonia_cents'], q['T60_s']]): d.text((30 + 260 * j, y), str(v), fill=TXT, font=F)
png(im, f'02-medidas-{C}.png')

# 03 el piano que se prepara: espectrograma
sr, x = lee('se-prepara'); N, hop = 4096, 512
cols = [np.abs(np.fft.rfft(x[a:a + N] * np.hanning(N))) for a in range(0, len(x) - N, hop)]
Sg = 20 * np.log10(np.array(cols).T + 1e-7); fr = np.fft.rfftfreq(N, 1 / sr); Sg = Sg[np.searchsorted(fr, np.geomspace(60, 5000, 360))]
Sg = np.clip((Sg - Sg.max() + 70) / 70, 0, 1)
def esp(cols_hasta, ancho, alto):
    sub = Sg[:, :max(2, cols_hasta)]; m = Image.fromarray((sub[::-1] * 255).astype(np.uint8)).resize((max(2, int(ancho * sub.shape[1] / Sg.shape[1])), alto), Image.BILINEAR)
    return Image.composite(Image.new('RGB', m.size, oklch(.86, .11, h0 + 70)), Image.new('RGB', m.size, FONDO), m)
im = Image.new('RGB', (W, 520), FONDO); d = ImageDraw.Draw(im)
d.text((24, 16), 'un piano que se prepara mientras suena: Re3 repetido; el tornillo entra (ρ 0 → 0.65) y desde los 5 s vibra contra la cuerda', fill=TXT, font=Fg)
im.paste(esp(Sg.shape[1], W - 60, 420), (30, 70))
png(im, f'03-se-prepara-{C}.png')

# GIF: la cuerda con el tornillo entrando + el espectrograma creciendo
frames = []
for k in range(48):
    t = (k + 1) / 48 * (len(x) / sr); rho = min(.65, max(0, (t - 1) / 6) * .65)
    fr_ = Image.new('RGB', (760, 400), FONDO); d = ImageDraw.Draw(fr_)
    d.text((16, 12), f't = {t:4.1f} s · tornillo ρ = {rho:.2f}' + (' · vibra contra la cuerda' if t > 5 else ''), fill=TXT, font=F)
    d.line([(40, 60), (720, 60)], fill=TEN, width=2); d.text((16, 52), 'cejilla', fill=TEN, font=Fs); d.text((690, 66), 'puente', fill=TEN, font=Fs)
    xt = 720 - .13 * 680; amp = 10 * (1 - rho)
    d.line([(40 + i, 60 + amp * np.sin(np.pi * i / 680) * np.sin(t * 9)) for i in range(0, 681, 4)], fill=oklch(.8, .1, h0 + 30), width=2)
    d.ellipse([xt - 6 - 6 * rho, 54 - 6 * rho, xt + 6 + 6 * rho, 66 + 6 * rho], outline=oklch(.85, .15, h0 + 200), width=3)
    fr_.paste(esp(int(Sg.shape[1] * k / 47) + 1, 720, 280), (20, 100))
    frames.append(fr_)
pal = frames[-1].quantize(colors=64, method=Image.Quantize.MEDIANCUT); frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
gif = AQUI / f'el-piano-que-se-prepara-{C}.gif'
with open(gif, 'xb') as fh: frames[0].save(fh, 'GIF', save_all=True, append_images=frames[1:] + [frames[-1]] * 3, duration=190, loop=0, optimize=True)

partes = []
for n in ORDEN:
    sr, x = lee(n); partes += [x / (np.abs(x).max() + 1e-9) * .8, np.zeros(int(.4 * sr))]
wav = R / f'muestrario-piano-{C}.wav'; wavfile.write(wav, sr, (np.concatenate(partes) * 32767).astype(np.int16))
m4a = AQUI / f'muestrario-piano-preparado-{C}.m4a'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(wav), '-af', 'loudnorm=I=-16:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
sha = lambda q: hashlib.sha256(Path(q).read_bytes()).hexdigest()
with open(SAL / f'receta-{C}.json', 'x', encoding='utf-8') as fh:
    json.dump({'id': ID, 'nonce': nonce, 'etiqueta': ET, 'orden_muestrario': ORDEN, 'medidas': MED,
               'archivos': {str(q.relative_to(AQUI)).replace('\\', '/'): sha(q) for q in sorted(SAL.glob('*.png')) + [gif, m4a]}}, fh, ensure_ascii=False, indent=1)
print(C, f'gif {gif.stat().st_size / 1e6:.2f} MB {190 * (len(frames) + 3) / 1000:.1f} s')
