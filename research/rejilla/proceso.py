"""PNGs de las etapas y GIF del proceso de rejilla 01 (lee render/, que deja rejilla.py)."""
import hashlib, json, subprocess
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).parent
R, P = AQUI / 'render', AQUI / 'proceso'
TAG = 's20261002'
P.mkdir(exist_ok=True)

d = json.load(open(R / f'ventanas-{TAG}.json'))
m16 = np.array(Image.open(R / f'magnitud-{TAG}.png'))
p16 = np.array(Image.open(R / f'fase-{TAG}.png'))
H = m16.shape[0] // 2
SEG, V = d['segundos'], d['voces']


# ── color: OKLCh derivado de la semilla del país, nada fijo ──
def oklch(L, C, h):
    a, b = C * np.cos(np.radians(h)), C * np.sin(np.radians(h))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = np.stack([4.0767416621 * l - 3.3077115913 * m + .2309699292 * s,
                    -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s,
                    -.0041960863 * l - .7034186147 * m + 1.7076147010 * s], -1)
    rgb = np.clip(rgb, 0, 1)
    rgb = np.where(rgb <= .0031308, 12.92 * rgb, 1.055 * rgb ** (1 / 2.4) - .055)
    return (rgb * 255).round().astype(np.uint8)


h0 = int(hashlib.sha256(d['semilla'].encode()).hexdigest()[:4], 16) % 360
FONDO = oklch(.13, .02, h0 + 200)
CELDA = {1: oklch(.78, .14, h0), 2: oklch(.70, .16, h0 + 140)}
GRIS = oklch(.30, .02, h0 + 200)


def rampa(u):
    """0..1 → oscuro frío a claro cálido, en OKLCh."""
    u = np.clip(u, 0, 1)
    return oklch(.13 + .80 * u, .02 + .15 * np.sin(np.pi * np.minimum(u * 1.2, 1)), h0 + 220 - 200 * u)


def fuente(n):
    for f in ['C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/cour.ttf']:
        try: return ImageFont.truetype(f, n)
        except OSError: pass
    return ImageFont.load_default()


F, Fs = fuente(18), fuente(14)


def ventanas_img(hasta=SEG, cw=14, ch=6):
    """Las dos ventanas del país, una generación por renglón (un renglón = un segundo)."""
    w = V * cw
    img = np.zeros((SEG * ch, 2 * w + cw * 2, 3), np.uint8); img[:] = FONDO
    e = d['der']['escala']
    for t in range(hasta):
        for lado, filas, x0 in [('izq', d['izq']['filas'][t], 0), ('der', d['der']['filas'][t // e], w + 2 * cw)]:
            for i, v in enumerate(filas):
                c = CELDA[v] if v else GRIS
                pad = 1 if v else 3
                img[t * ch + pad // 2: (t + 1) * ch - pad // 2 - (1 if not v else 0), x0 + i * cw + pad: x0 + (i + 1) * cw - pad] = c
    return img


def banda(mitad, fmax=6000, alto=420):
    """Magnitud de un oído (0..fmax Hz), max-pool vertical, en dB."""
    a = m16[mitad].astype(float)[::-1][:fmax] / 65535   # abajo = 0 Hz → índice = Hz
    paso = fmax // alto
    a = a[:paso * alto].reshape(alto, paso, -1).max(1)[::-1]
    db = 20 * np.log10(a + 1e-6)
    return (db + 70) / 70


def fase_banda(mitad, fmax=6000, alto=420):
    a = p16[mitad].astype(float)[::-1][:fmax] / 65535
    mag = m16[mitad].astype(float)[::-1][:fmax] / 65535
    paso = fmax // alto
    idx = mag[:paso * alto].reshape(alto, paso, -1).argmax(1)
    a = np.take_along_axis(a[:paso * alto].reshape(alto, paso, -1), idx[:, None], 1)[:, 0][::-1]
    mm = mag[:paso * alto].reshape(alto, paso, -1).max(1)[::-1]
    col = oklch(np.full(a.shape, .72), np.full(a.shape, .14), h0 + 360 * a)
    k = np.clip((20 * np.log10(mm + 1e-6) + 60) / 60, 0, 1)[..., None]
    return (col * k + FONDO * (1 - k)).astype(np.uint8)


def ancho(img, cw):
    return np.repeat(img, cw, axis=1)


def rotulo(img, textos):
    im = Image.fromarray(img); dr = ImageDraw.Draw(im)
    tc = tuple(int(c) for c in oklch(.85, .05, h0 + 40))
    for (x, y), s, f in textos: dr.text((x, y), s, fill=tc, font=f)
    return np.array(im)


def marco(img, pad=24, arriba=34):
    out = np.zeros((img.shape[0] + pad + arriba, img.shape[1] + 2 * pad, 3), np.uint8); out[:] = FONDO
    out[arriba:arriba + img.shape[0], pad:pad + img.shape[1]] = img
    return out


# 01 · datos: las dos ventanas del país
v = marco(ventanas_img())
v = rotulo(v, [((24, 8), f"izq: tinta x1, {V} celdas, 1 gen/s", Fs), ((24 + V * 14 + 28, 8), f"der: tinta x7, la misma ley 7 veces más lenta", Fs)])
Image.fromarray(v).save(P / f'01-ventanas-del-pais-{TAG}.png')

# 02 · la ley de una voz: el peine (h=3, valor 1) y lo que suena
h, c, g = 3, 330, 1.5
j = np.arange(-40, 41); k = c + j * h; x = j / .5
w = np.cos(np.pi / 2 * np.abs(x) / 81) ** 2 / np.sqrt(1 + x * x)
W2, H2 = 1200, 520
im = np.zeros((H2, W2, 3), np.uint8); im[:] = FONDO
for kk, ww in zip(k, w):
    px = int((kk - 200) / 260 * (W2 - 80)) + 40
    if 40 <= px < W2 - 40:
        alto = int(ww * 200); im[240 - alto:240, px - 1:px + 2] = CELDA[1]
t = np.linspace(0, 1, W2 - 80, endpoint=False)
spec = np.zeros(65536 // 2 + 1, complex); spec[k] = w * np.exp(-1j * np.arctan(x))
y = np.fft.irfft(spec, 65536); y = y[(t * 65536).astype(int)]; y /= np.abs(y).max()
for i, yy in enumerate(y):
    yy = int(380 - yy * 110); im[min(yy, 380):max(yy, 380) + 1, 40 + i] = CELDA[2]
im = rotulo(im, [((40, 14), "una voz: celda h=3, valor 1  ->  peine de filas cada 3 Hz alrededor de 330 Hz", F),
                 ((40, 40), "cada diente pesa 1/sqrt(1+x^2), fase -atan(x): un pluck exacto, 3 veces por segundo", Fs),
                 ((40, 250), "200 Hz                                       espectro (filas = Hz)                                   460 Hz", Fs),
                 ((40, 495), "0 s                                         lo que suena: un segundo, una generación                    1 s", Fs)])
Image.fromarray(im).save(P / f'02-ley-de-una-voz-{TAG}.png')

# 03 · la partitura: magnitud de los dos oídos (0–6000 Hz), una columna por segundo
cw = 12
izq, der = banda(slice(H, 2 * H)), banda(slice(0, H))
part = np.concatenate([ancho(rampa(der), cw), np.zeros((8, SEG * cw, 3), np.uint8) + FONDO, ancho(rampa(izq), cw)])
part = rotulo(marco(part), [((24, 8), "partitura de magnitud · arriba oído derecho, abajo izquierdo · 0–6000 Hz · 1 columna = 1 s = 1 generación", Fs)])
Image.fromarray(part).save(P / f'03-partitura-magnitud-{TAG}.png')

# 04 · la fase (el tiempo dentro del segundo), coloreada por ángulo donde hay magnitud
fa = np.concatenate([ancho(fase_banda(slice(0, H)), cw), np.zeros((8, SEG * cw, 3), np.uint8) + FONDO, ancho(fase_banda(slice(H, 2 * H)), cw)])
fa = rotulo(marco(fa), [((24, 8), "partitura de fase · el color es el ángulo · -atan(x) en cada diente", Fs)])
Image.fromarray(fa).save(P / f'04-partitura-fase-{TAG}.png')

# 05 · espectrograma de lo que salió de ffmpeg
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(R / f'el-pais-suena-{TAG}.wav'), '-lavfi',
                'showspectrumpic=s=1400x700:mode=separate:scale=log:fscale=lin:stop=6000:color=magma:legend=1',
                str(P / f'05-espectrograma-{TAG}.png')], check=True)

# GIF: el país baja renglón por renglón y la partitura se escribe columna por columna
frames = []
alto_p = izq.shape[0]
for t in list(range(1, SEG + 1)) + [SEG] * 8:
    ve = ventanas_img(t, ch=9)
    pi = ancho(rampa(izq), 6)[:, :t * 6]; pd = ancho(rampa(der), 6)[:, :t * 6]
    lienzo = np.zeros((max(ve.shape[0], 2 * alto_p + 8) + 50, ve.shape[1] + SEG * 6 + 40, 3), np.uint8); lienzo[:] = FONDO
    lienzo[40:40 + ve.shape[0], 10:10 + ve.shape[1]] = ve
    x0 = ve.shape[1] + 30
    lienzo[40:40 + alto_p, x0:x0 + pd.shape[1]] = pd
    lienzo[48 + alto_p:48 + 2 * alto_p, x0:x0 + pi.shape[1]] = pi
    if t < SEG:
        lienzo[40:48 + 2 * alto_p, x0 + t * 6:x0 + t * 6 + 2] = CELDA[1]
        lienzo[40 + (t - 1) * 9:40 + t * 9, 4:8] = CELDA[1]
    lienzo = rotulo(lienzo, [((10, 10), f"el país suena · gen {t:3d} = {t:3d} s · fila k = k Hz", F)])
    frames.append(Image.fromarray(lienzo).convert('P', palette=Image.ADAPTIVE, colors=64))
gif = AQUI / f'proceso-{TAG}.gif'
frames[0].save(gif, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True)
dur = 90 * len(frames) / 1000
print('gif', gif.name, f'{gif.stat().st_size / 1e6:.2f} MB', f'{dur:.1f} s', frames[0].size)
