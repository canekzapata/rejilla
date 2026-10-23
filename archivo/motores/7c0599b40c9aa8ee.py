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


def fuente(n):
    for f in ['C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/cour.ttf']:
        try: return ImageFont.truetype(f, n)
        except OSError: pass
    return ImageFont.load_default()



AQUI = Path(__file__).parent
R = AQUI / 'render' / 'cancion'
P = AQUI / 'proceso' / 'cancion'
P.mkdir(parents=True, exist_ok=True)
TAG = M.TAG

V = dict(np.load(R / 'vistas.npz'))
info = json.load(open(R / 'partitura.json'))
esc = info['escalas']
C = next(iter(V.values())).shape[0]
CW = 22                                    # px por compás

def fuente(n):
    for f in ['C:/Windows/Fonts/consola.ttf', 'C:/Windows/Fonts/cour.ttf']:
        try: return ImageFont.truetype(f, n)
        except OSError: pass
    return ImageFont.load_default()



AQUI = Path(__file__).parent
R = AQUI / 'render' / 'cancion'
P = AQUI / 'proceso' / 'cancion'
P.mkdir(parents=True, exist_ok=True)
TAG = M.TAG

V = dict(np.load(R / 'vistas.npz'))
info = json.load(open(R / 'partitura.json'))
esc = info['escalas']
C = next(iter(V.values())).shape[0]
CW = 22                                    # px por compás

h0 = (M.SEM * 47) % 360                    # tono base derivado de la semilla
FONDO = oklch(.12, .02, h0 + 200)
ORDEN = ['bombo', 'bajo', 'bateria', 'pad', 'teclas', 'voz', 'congelado']
TONO = {n: h0 + i * 360 / len(ORDEN) * 1.0 for i, n in enumerate(ORDEN)}
NOMBRE = {'bombo': 'bombo', 'bajo': 'bajo', 'bateria': 'caja y hats', 'pad': 'pad', 'teclas': 'rhodes y campanas',
          'voz': 'voz', 'congelado': 'coro congelado'}
