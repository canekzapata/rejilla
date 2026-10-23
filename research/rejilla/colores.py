"""Color OKLCh (derivado, nunca paleta fija) y fuente, compartidos por los scripts de proceso."""
import numpy as np
from PIL import ImageFont


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
