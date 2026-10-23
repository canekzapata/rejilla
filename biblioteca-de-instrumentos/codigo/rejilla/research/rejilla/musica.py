"""Rejilla 02 · una canción escrita en la rejilla.

Cada sonido es una suma de modos: resonancias amortiguadas e^{(-a+2πif)t}.
Un modo que empieza en t0 y se apaga (o se suelta) cae en una o varias columnas
de la rejilla; para cada columna, los coeficientes de Fourier de ese pedazo
tienen fórmula cerrada (una serie geométrica), así que se escriben directo en
la imagen sin pasar nunca por el tiempo. ffmpeg (spectrumsynth) es el único
que convierte la imagen en sonido.

Rejilla: sample_rate 52429, 65536 filas por oído → una columna = un compás de
2.5 s (96 bpm), una fila = 0.4 Hz. Las notas no tienen que caer en una fila:
la fórmula pinta la fuga exacta a las filas vecinas.

    python musica.py        # partitura → ffmpeg por pista → prueba exacta → mezcla
"""
import json, math, subprocess, hashlib
from pathlib import Path
import numpy as np
from scipy.io import wavfile

AQUI = Path(__file__).parent
RENDER = AQUI / 'render' / 'cancion'
TAG = 's1009'
S = 52429                  # sample rate de la rejilla
H = 65536                  # filas por oído
N = 2 * H                  # FFT
T = N / S                  # un compás (2.49995 s, 96 bpm)
F = S / N                  # Hz por fila (0.4)
R = 2048                   # filas a cada lado de un modo que se escriben
SEM = 1009
rng = np.random.default_rng(SEM)


def hz(midi): return 440.0 * 2 ** ((midi - 69) / 12)


def fijar_tempo(bpm):
    """Otra pieza, otro tempo: la columna sigue siendo un compás de 4/4."""
    global S, T, F
    S = round(N / (4 * 60 / bpm))
    T = N / S
    F = S / N
    return S


def paneo(p):              # -1 izq … 1 der, potencia constante
    t = (p + 1) * math.pi / 4
    return math.cos(t), math.sin(t)


# ───────────── segmentos: un modo entre ts y te ─────────────
# valor(t) = Re(B · e^{(-a + 2πif)(t - ts)}) para ts ≤ t < te
class Pista:
    def __init__(self, nombre, columnas):
        self.nombre, self.C = nombre, columnas
        self.segs = []      # (B, f, a, ts, te, gL, gR, grupo)
        self.grupo = 0      # los segmentos de una misma nota deciden sus filas juntos

    def seg(self, B, f, a, ts, te, pan):
        if f <= 20 or f >= S / 2 - 50: return
        gL, gR = paneo(pan)
        if te is None or te == math.inf:
            te = ts + math.log(1e5) / max(a, 1e-3)
        te = min(te, self.C * T)
        if te > ts: self.segs.append((complex(B), f, a, ts, te, gL, gR, self.grupo))

    def modo(self, f, amp, t0, a, ataque=None, suelta=None, ar=None, pan=0.0, fase=0.0):
        """Modo con ataque (e^{-at} - e^{-a2 t}) y, si hay suelta, release con tasa ar."""
        self.grupo += 1
        B = amp * np.exp(1j * fase)
        if ataque:  # normalizar el pico de e^{-at}-e^{-a2 t}
            tp = math.log(ataque / a) / (ataque - a)
            B /= (math.exp(-a * tp) - math.exp(-ataque * tp))
        fin = t0 + suelta if suelta else None
        self.seg(B, f, a, t0, fin, pan)
        if ataque: self.seg(-B, f, ataque, t0, fin, pan)
        if suelta:
            L = suelta
            env = math.exp(-a * L) - (math.exp(-ataque * L) if ataque else 0)
            B1 = B * env * np.exp(2j * math.pi * f * L)
            self.seg(B1, f, ar or 12.0, t0 + L, None, pan)

    def escribir(self):
        """Los coeficientes exactos de cada pedazo de cada modo, columna por columna."""
        ZL = np.zeros((self.C, H), complex); ZR = np.zeros((self.C, H), complex)
        todas = np.arange(1, H)
        ph_todas = -2j * math.pi * todas / N
        # Si la raya del compás corta un modo con amplitud, el pedazo tiene un escalón en la
        # orilla de la columna y su fuga llega a TODAS las filas: se escriben todas (con ±R
        # filas sonaba un clic de 1 ms en cada raya; lo atrapó la prueba exacta). Y la nota
        # entera (ataque, cuerpo y release) usa las mismas filas, para que sus escalones internos
        # se sigan cancelando.
        completa = set()
        for B, f, a, ts, te, gL, gR, g in self.segs:
            ms, me = ts * S, te * S
            for b in range(int(ms // N), min(self.C, int(math.ceil(me / N)))):
                corte = 0.0
                if ms < b * N: corte = abs(B) * math.exp(-a * (b * N - ms) / S)
                if me > (b + 1) * N: corte = max(corte, abs(B) * math.exp(-a * ((b + 1) * N - ms) / S))
                if corte > 2e-5: completa.add((g, b))
        for B, f, a, ts, te, gL, gR, g in self.segs:
            ms, me = ts * S, te * S
            kc = f / F
            k_v = np.arange(max(1, int(kc) - R), min(H, int(kc) + R + 1))
            if k_v.size == 0: continue
            ph_v = -2j * math.pi * k_v / N
            for b in range(int(ms // N), min(self.C, int(math.ceil(me / N)))):
                m0 = max(math.ceil(ms), b * N); m1 = min(math.ceil(me), (b + 1) * N)
                M = m1 - m0
                if M <= 0: continue
                k, ph = (todas, ph_todas) if (g, b) in completa else (k_v, ph_v)
                c = 0
                for Bc, pc in ((B / 2, complex(-a, 2 * math.pi * f)), (B.conjugate() / 2, complex(-a, -2 * math.pi * f))):
                    q = pc / S + ph
                    pre = Bc * np.exp(pc * (m0 - ms) / S) * np.exp(ph * (m0 - b * N))
                    c = c + pre * (np.expm1(M * q) / np.expm1(q))
                c /= N
                ZL[b, k] += gL * c; ZR[b, k] += gR * c
        return ZL, ZR

    def tiempo(self, t0, t1, canal=0):
        """El mismo sonido sumado directo en el tiempo (sólo para la prueba exacta)."""
        n = np.arange(int(round(t0 * S)), int(round(t1 * S)))
        t = n / S; y = np.zeros(len(n))
        for B, f, a, ts, te, gL, gR, _ in self.segs:
            ok = (n >= math.ceil(ts * S)) & (n < math.ceil(te * S))
            if not ok.any(): continue
            g = gL if canal == 0 else gR
            y[ok] += g * np.real(B * np.exp(complex(-a, 2 * math.pi * f) * (t[ok] - ts)))
        return y


# ───────────── instrumentos (modales) ─────────────
def rhodes(P, midi, t0, vel, dur, pan=0.0):
    f = hz(midi); b = 0.6 + 0.6 * vel          # la fuerza abre el timbre
    for mult, amp, a in ((1, 1.0, 1.4 + f / 500), (2, 0.30 * b, 3.2), (3, 0.09 * b, 5.5), (4, 0.035 * b, 8.0)):
        P.modo(f * mult, 0.16 * vel * amp, t0, a, ataque=260, suelta=dur, ar=7, pan=pan, fase=rng.uniform(0, 6.28))
    P.modo(f * 7.03, 0.010 * vel * b, t0, 22, ataque=900, pan=pan)   # la campanita de la púa


def campana(P, midi, t0, vel, pan=0.0):
    f = hz(midi)
    for mult, amp, a in ((1, 1.0, 2.2), (2.76, 0.35, 4.5), (5.40, 0.16, 8.0), (8.93, 0.06, 13)):
        P.modo(f * mult, 0.07 * vel * amp, t0, a, ataque=1200, pan=pan, fase=rng.uniform(0, 6.28))


def pad(P, midi, t0, dur, vel):
    f = hz(midi)
    for det, pan in ((-0.55, -0.6), (0.55, 0.6)):                  # dos copias que baten
        for mult, amp in ((1, 1.0), (2, 0.16), (3, 0.05)):
            P.modo(f * mult + det * mult, 0.05 * vel * amp, t0, 0.07, ataque=1.4, suelta=dur, ar=1.3,
                   pan=pan, fase=rng.uniform(0, 6.28))


def bajo(P, midi, t0, dur, vel):
    f = hz(midi)
    for mult, amp, a in ((1, 1.0, 2.0), (2, 0.38, 4.0), (3, 0.12, 7.0), (4, 0.04, 10)):
        P.modo(f * mult, 0.42 * vel * amp, t0, a, ataque=160, suelta=dur, ar=22, fase=rng.uniform(0, 6.28))


def voz(P, midi, t0, dur, vel, pan=0.0):
    """La melodía: algo entre flauta y campana de vidrio, doble y apenas desafinada."""
    f = hz(midi)
    for det, p, g in ((0.0, pan, 1.0), (0.45, pan + 0.35, 0.45), (-0.45, pan - 0.35, 0.45)):
        for mult, amp, a in ((1, 1.0, 0.8), (2, 0.14, 1.8), (3, 0.06, 3.0), (4, 0.02, 4.0)):
            P.modo((f + det) * mult, 0.10 * vel * amp * g, t0, a, ataque=38, suelta=dur, ar=5,
                   pan=max(-1, min(1, p)), fase=rng.uniform(0, 6.28))


# la batería: modos fijos (cada tambor es siempre el mismo objeto), fase nueva en cada golpe
MODOS_CAJA = np.exp(rng.uniform(math.log(900), math.log(7500), 90))
MODOS_HAT = np.exp(rng.uniform(math.log(6000), math.log(17000), 46))
MODOS_CLIC = np.exp(rng.uniform(math.log(1500), math.log(5000), 8))


def bombo(P, t0, vel):
    P.modo(51, 0.95 * vel, t0, 7.5, ataque=500)
    P.modo(77, 0.30 * vel, t0, 20, ataque=700)
    P.modo(118, 0.10 * vel, t0, 40, ataque=900)
    for f in MODOS_CLIC: P.modo(f, 0.012 * vel, t0, 260, fase=rng.uniform(0, 6.28))


def caja(P, t0, vel, pan=0.08):
    P.modo(186, 0.38 * vel, t0, 24, ataque=1500, pan=pan)
    P.modo(331, 0.20 * vel, t0, 30, ataque=1500, pan=pan)
    for f in MODOS_CAJA:
        P.modo(f, 0.045 * vel * (900 / f) ** 0.25, t0, rng.uniform(26, 38), ataque=3000, pan=pan, fase=rng.uniform(0, 6.28))


def hat(P, t0, vel, abierto=False, pan=-0.25):
    a = 9 if abierto else 75
    for f in MODOS_HAT:
        P.modo(f, 0.022 * vel, t0, a * rng.uniform(0.85, 1.15), ataque=4000, pan=pan, fase=rng.uniform(0, 6.28))


# ───────────── la canción ─────────────
VOZ = {  # acordes: bajo + voces del Rhodes (MIDI)
    'Dmaj9': (38, (54, 57, 61, 64)), 'C#m9': (37, (52, 56, 59, 63)), 'Bm9': (35, (50, 54, 57, 61)),
    'E13': (40, (50, 56, 61, 66)), 'Amaj9': (33, (56, 59, 61, 64)), 'F#m9': (42, (56, 57, 61, 64)),
    'Dm9': (38, (53, 57, 60, 64)),
}
VERSO = ['Dmaj9', 'C#m9', 'Bm9', 'E13']
CORO = ['Amaj9', 'F#m9', 'Dmaj9', 'E13']
FORMA = (  # (sección, compases)
    [('intro', c) for c in VERSO] +
    [('verso', c) for c in VERSO * 2] +
    [('coro', c) for c in CORO * 2] +
    [('verso2', c) for c in VERSO * 2] +
    [('coro', c) for c in CORO * 2] +
    [('quiebre', c) for c in ['Bm9', 'C#m9', 'Dmaj9', 'E13']] +
    [('final', c) for c in CORO + ['Amaj9', 'F#m9', 'Dmaj9', 'Dm9']] +
    [('outro', 'Amaj9')] * 4
)
COLAS = 2                     # compases de silencio para que suenen las colas
C = len(FORMA) + COLAS

MELODIA = [  # coro: (posición en 16avos, nota, duración en 16avos)
    [(0, 76, 4), (4, 73, 2), (6, 71, 2), (8, 73, 5), (14, 69, 2)],
    [(0, 71, 4), (4, 69, 2), (6, 68, 4), (10, 64, 4), (14, 66, 2)],
    [(0, 69, 6), (6, 66, 2), (8, 69, 2), (10, 73, 4), (14, 76, 2)],
    [(0, 74, 4), (4, 73, 2), (6, 71, 8)],
    [(0, 76, 4), (4, 73, 2), (6, 71, 2), (8, 73, 4), (12, 76, 2), (14, 78, 2)],
    [(0, 80, 6), (6, 76, 2), (8, 73, 4), (12, 71, 4)],
    [(0, 69, 4), (4, 71, 2), (6, 73, 2), (8, 76, 4), (12, 78, 2), (14, 76, 2)],
    [(0, 73, 6), (6, 71, 2), (8, 68, 8)],
]
CIERRE = [(0, 72, 6), (6, 69, 2), (8, 64, 10)]     # sobre Dm9: el Do natural del iv menor
CONTRA = [  # verso 2: la voz contesta
    [(8, 73, 4), (12, 69, 4)], [(8, 71, 4), (12, 68, 4)], [(8, 69, 4), (12, 66, 4)], [(6, 68, 2), (8, 71, 8)],
    [(8, 73, 4), (12, 69, 4)], [(8, 71, 4), (12, 68, 4)], [(8, 69, 4), (12, 66, 4)], [(4, 73, 4), (8, 74, 4), (12, 76, 4)],
]

SWING = 0.58
def t16(compas, pos):
    """Tiempo de un 16avo con swing y una pizca de mano humana (sembrada)."""
    p = pos + (2 * (SWING - 0.5) if int(pos) % 2 == 1 else 0)
    return compas * T + p * T / 16 + rng.normal(0, 0.004)


def componer():
    P = {n: Pista(n, C) for n in ['bombo', 'bateria', 'bajo', 'teclas', 'pad', 'voz']}
    idx = {}
    for b, (sec, ch) in enumerate(FORMA):
        idx.setdefault(sec, []).append(b)
        k = idx[sec].index(b)               # compás dentro de la sección
        raiz, voces = VOZ[ch]
        sig = FORMA[b + 1][1] if b + 1 < len(FORMA) else ch
        raiz_sig = VOZ[sig][0]
        lleno = sec in ('coro', 'final')

        # pad: siempre, menos en el quiebre (ahí suena el congelado)
        if sec != 'quiebre':
            vp = {'intro': 1.0, 'verso': 0.55, 'verso2': 0.6, 'coro': 0.8, 'final': 0.9, 'outro': 1.0}[sec]
            if sec == 'outro' and k == 3: vp = 0.0
            for n in voces: pad(P['pad'], n, b * T, T * (1.0 if sec != 'outro' or k < 2 else 2.0), vp)

        # Rhodes
        if sec in ('intro', 'quiebre'):
            for i, n in enumerate(voces): rhodes(P['teclas'], n, b * T + 0.03 * i, 0.55, T * 0.95, pan=-0.3 + 0.2 * i)
        elif sec == 'outro':
            if k < 2:
                for i in range(8):
                    n = (voces + tuple(v + 12 for v in voces))[i]
                    rhodes(P['teclas'], n, t16(b, 2 * i), 0.5 - 0.03 * i, T / 4, pan=-0.4 + 0.1 * i)
            elif k == 2:
                for i, n in enumerate(voces): rhodes(P['teclas'], n, b * T + 0.04 * i, 0.5, 2 * T, pan=-0.3 + 0.2 * i)
                campana(P['teclas'], 81, b * T + 0.6, 0.9, pan=0.2)
        else:
            golpes = [(0, 6, 0.8), (6, 2, 0.5), (10, 5, 0.65)] if not lleno else [(0, 5, 0.85), (6, 2, 0.5), (10, 3, 0.6), (14, 2, 0.55)]
            for pos, du, v in golpes:
                acorde = VOZ[sig][1] if pos == 14 else voces      # empuja el acorde que viene
                for i, n in enumerate(acorde): rhodes(P['teclas'], n, t16(b, pos) + 0.012 * i, v, du * T / 16, pan=-0.25 + 0.17 * i)
        if sec == 'final':
            for j, pos in enumerate([2, 6, 10, 14]):
                campana(P['teclas'], voces[(j + k) % 4] + 24, t16(b, pos), 0.55, pan=0.6 - 0.4 * (j % 2) * 3)

        # bajo
        if sec in ('verso', 'verso2', 'coro', 'final'):
            if lleno: pat = [(0, 0, 5), (6, 0, 2), (8, 7, 3), (11, 12, 2), (15, raiz_sig - 1 - raiz, 1)]
            else: pat = [(0, 0, 6), (7, 0, 2), (10, 12, 3), (14, 7, 2)]
            for pos, iv, du in pat: bajo(P['bajo'], raiz + iv, t16(b, pos), du * T / 16 * 0.9, 0.9 if pos == 0 else 0.7)
        elif sec == 'outro' and k == 2:
            bajo(P['bajo'], raiz, b * T, 2 * T, 0.8)
        elif sec == 'quiebre' and k == 3:
            bajo(P['bajo'], raiz, t16(b, 12), T / 4, 0.7)

        # batería
        if sec in ('verso', 'verso2', 'coro', 'final'):
            for pos in ([0, 7, 10] + ([14] if k % 4 == 3 else [])) if not lleno else [0, 6, 10]:
                bombo(P['bombo'], t16(b, pos), 1.0 if pos == 0 else 0.8)
            if not (sec == 'verso' and k < 4):
                caja(P['bateria'], t16(b, 4), 0.9); caja(P['bateria'], t16(b, 12), 0.95)
                caja(P['bateria'], t16(b, 7), 0.18); caja(P['bateria'], t16(b, 15), 0.14)
            for pos in range(0, 16, 2): hat(P['bateria'], t16(b, pos), 0.75 if pos % 4 == 2 else 0.55)
            if lleno:
                for pos in range(1, 16, 2): hat(P['bateria'], t16(b, pos), 0.22)
                if k % 2 == 1: hat(P['bateria'], t16(b, 14.0), 0.5, abierto=True)
        if sec == 'quiebre' and k == 3:      # redoble que crece hacia el coro final
            for i, pos in enumerate(range(8, 16)): caja(P['bateria'], t16(b, pos), 0.15 + 0.08 * i)

        # voz
        if sec in ('coro', 'final'):
            frase = MELODIA[k % 8] if not (sec == 'final' and k == 7) else CIERRE
            for pos, n, du in frase:
                voz(P['voz'], n, t16(b, pos), du * T / 16, 1.0 if sec == 'coro' else 1.1)
                if sec == 'final' and k >= 4: voz(P['voz'], n + 12, t16(b, pos), du * T / 16, 0.3, pan=0.3)
        elif sec == 'verso2':
            for pos, n, du in CONTRA[k]: voz(P['voz'], n, t16(b, pos), du * T / 16, 0.7, pan=-0.2)
    return P


def compases_de(sec):
    return [b for b, (s, _) in enumerate(FORMA) if s == sec]


def a_imagen(ZL, ZR):
    mag = np.empty((2 * H, ZL.shape[0])); pha = np.empty_like(mag)
    mag[:H] = np.abs(ZR).T[::-1]; mag[H:] = np.abs(ZL).T[::-1]
    pha[:H] = np.angle(ZR).T[::-1]; pha[H:] = np.angle(ZL).T[::-1]
    escala = mag.max() or 1.0
    m16 = np.round(mag / escala * 65535).astype('<u2')
    p16 = np.round((pha + np.pi) / (2 * np.pi) * 65535).astype('<u2')
    return m16, p16, escala


def sintetizar(m16, p16, wav):
    W = m16.shape[1]
    mr, pr = wav.with_suffix('.mag.raw'), wav.with_suffix('.fase.raw')
    m16.tofile(mr); p16.tofile(pr)
    entrada = lambda r: ['-f', 'rawvideo', '-pix_fmt', 'gray16le', '-s', f'{W}x{2 * H}', '-r', '1', '-i', str(r)]
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *entrada(mr), *entrada(pr), '-filter_complex',
                    '[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];'
                    f'[m][p]spectrumsynth=sample_rate={S}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0',
                    '-c:a', 'pcm_f32le', str(wav)], check=True)
    mr.unlink(); pr.unlink()


# vista: frecuencia logarítmica de 30 Hz a 14 kHz, para los PNGs y el GIF
VISTA = 720
_bordes = np.round(np.geomspace(30, 14000, VISTA + 1) / F).astype(int)
def vista(Z):
    a = np.abs(Z)
    return np.stack([a[:, _bordes[i]:max(_bordes[i + 1], _bordes[i] + 1)].max(1) for i in range(VISTA)], 1)


def main():
    RENDER.mkdir(parents=True, exist_ok=True)
    P = componer()
    print('compases', len(FORMA), f'duración {C * T:.1f} s', {n: len(p.segs) for n, p in P.items()})

    medias, vistas, escalas = {}, {}, {}
    coro2 = compases_de('coro')[8:16]
    for n, p in P.items():
        ZL, ZR = p.escribir()
        if n in ('teclas', 'pad', 'voz'):
            medias[n] = (np.abs(ZL[coro2]).mean(0), np.abs(ZR[coro2]).mean(0))
        vistas[n] = vista(ZL + ZR)
        m16, p16, esc = a_imagen(ZL, ZR)
        escalas[n] = esc
        sintetizar(m16, p16, RENDER / f'{n}.wav')
        if n == 'bajo':  # prueba exacta: lo que pintó ffmpeg contra el mismo bajo sumado en el tiempo
            sr, x = wavfile.read(RENDER / 'bajo.wav')
            t0, t1 = 12 * T, 15 * T
            y = p.tiempo(t0, t1, 0) / esc
            seg = x[int(round(t0 * S)):int(round(t0 * S)) + len(y), 0]
            err = np.abs(seg - y).max() / np.abs(y).max()
            print(f'prueba exacta (bajo, compases 12-14): error relativo máx {err:.2e}')
            escalas['error_exacto_bajo'] = float(err)
        del ZL, ZR
        print('  pista', n, 'lista')

    # el quiebre: el coro 2 congelado. Magnitud media de teclas+pad+voz, fase al azar fija por fila
    # (filas enteras: la misma fase en cada columna empata sin costura)
    q = compases_de('quiebre')
    cols = list(range(q[0] - 1, q[-1] + 2))
    fz = np.random.default_rng(SEM + 1)
    Zc = []
    for ch in (0, 1):
        m = sum(medias[n][ch] * escalas[n] for n in medias)
        m = (m / m.max()) ** 1.6                       # más contraste: que se oigan notas, no niebla
        Zc.append(m * np.exp(1j * fz.uniform(-np.pi, np.pi, H)))
    ZL = np.zeros((C, H), complex); ZR = np.zeros((C, H), complex)
    for c in cols: ZL[c], ZR[c] = Zc[0], Zc[1]
    vistas['congelado'] = vista(ZL + ZR)
    m16, p16, esc = a_imagen(ZL, ZR); escalas['congelado'] = esc
    sintetizar(m16, p16, RENDER / 'congelado.wav')
    del ZL, ZR

    np.savez_compressed(RENDER / 'vistas.npz', **vistas)
    json.dump({'escalas': escalas, 'forma': FORMA, 'T': T, 'quiebre_cols': cols}, open(RENDER / 'partitura.json', 'w'))
    mezclar(escalas, cols)


GANANCIA = {'bombo': 0.50, 'bateria': 0.95, 'bajo': 0.40, 'teclas': 0.90, 'pad': 0.45, 'voz': 1.15, 'congelado': 0.035}


def mezclar(esc, cols):
    """Ganancias de mezcla × la escala de cada imagen; sidechain del bombo; reverb de cuarto; master."""
    g = GANANCIA
    pistas = list(g)
    ent = sum([['-i', str(RENDER / f'{n}.wav')] for n in pistas], [])
    ini, fin = (cols[0] + 0.5) * T, (cols[-1] + 0.5) * T
    vol = lambda n: f"[{pistas.index(n)}]aresample=48000,volume={g[n] * esc[n]:.6f}"
    grafo = ';'.join([
        f"{vol('bombo')},asplit=3[k][kc1][kc2]",
        f"{vol('bateria')}[dr]",
        f"{vol('bajo')}[ba0]",
        f"{vol('teclas')}[te]",
        f"{vol('pad')}[pa]",
        f"{vol('voz')}[vo]",
        f"{vol('congelado')},volume='if(lt(t,{ini}),0,if(lt(t,{ini + 2 * T}),(t-{ini})/{2 * T},if(lt(t,{fin - 1.2 * T}),1,max(0,({fin}-t)/{1.2 * T}))))':eval=frame[cg]",
        "[te][pa][cg]amix=inputs=3:normalize=0[arm0]",
        "[arm0][kc1]sidechaincompress=threshold=0.06:ratio=3:attack=6:release=220:makeup=1[arm]",
        "[ba0][kc2]sidechaincompress=threshold=0.08:ratio=2.5:attack=4:release=140:makeup=1[ba]",
        "[arm][vo]amix=inputs=2:normalize=0,asplit[seco][w0]",
        "aevalsrc=d=3.2:s=48000:exprs='(random(0)*2-1)*exp(-t*1.9)|(random(1)*2-1)*exp(-t*1.9)',lowpass=f=6500,highpass=f=250[ir]",
        "[w0][ir]afir=dry=0:wet=1[rev]",
        "[seco][rev]amix=inputs=2:weights=1 0.11:normalize=0[musica]",
        "[k][dr][ba][musica]amix=inputs=4:normalize=0,highpass=f=28,equalizer=f=3200:t=o:w=1.6:g=5,treble=g=3:f=7000,"
        "acompressor=threshold=0.25:ratio=2:attack=20:release=250:makeup=1,"
        "loudnorm=I=-14:TP=-1.2:LRA=9,aresample=48000[out]",
    ])
    final = RENDER / f'cancion-{TAG}.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *ent, '-filter_complex', grafo,
                    '-map', '[out]', '-c:a', 'pcm_s16le', str(final)], check=True)
    m4a = AQUI / f'cancion-{TAG}.m4a'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(final),
                    '-c:a', 'aac', '-b:a', '224k', str(m4a)], check=True)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(final), '-af', 'ebur128=peak=true',
                        '-f', 'null', '-'], capture_output=True, text=True).stderr
    tail = r[r.rfind('Summary:'):]
    val = lambda key: float(tail.split(key)[1].split()[0])
    med = {'I_LUFS': val('I:'), 'LRA': val('LRA:'), 'pico_dBTP': val('Peak:'), 'duracion_s': round(C * T, 2),
           'error_exacto_bajo': esc.get('error_exacto_bajo'),
           'sha256_m4a': hashlib.sha256(m4a.read_bytes()).hexdigest()}
    print(med)
    json.dump(med, open(AQUI / f'medidas-cancion-{TAG}.json', 'w'), indent=1)


if __name__ == '__main__':
    import sys
    if '--mezcla' in sys.argv:          # rehacer sólo la mezcla, sin volver a sintetizar
        p = json.load(open(RENDER / 'partitura.json'))
        mezclar(p['escalas'], p['quiebre_cols'])
    else:
        main()
