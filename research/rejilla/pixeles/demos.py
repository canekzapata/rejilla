"""Loop B de «los pixeles y la luna»: instrumentos y gestos, cada uno probado por la rejilla y medido.

    python pixeles/demos.py            # todas
    python pixeles/demos.py p04        # una
"""
import json, math, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from motor import M, S0, T0, N, H, SR_OUT, rng, Pista, reloj, q, sintetizar, leer, tornasol, arena, cinta
import instrumentos as I

AQUI = Path(__file__).parent
R = AQUI.parent / 'render' / 'pixeles-demos'; R.mkdir(parents=True, exist_ok=True)
DEMOS = AQUI / 'demos'; DEMOS.mkdir(exist_ok=True)
MED = json.load(open(DEMOS / 'medidas.json', encoding='utf-8')) if (DEMOS / 'medidas.json').exists() else {}
L = lambda compases: int(round(compases * T0 * SR_OUT))


def suave(u):
    u = np.clip(u, 0, 1); return u * u * u * (u * (6 * u - 15) + 10)


def recorrido(vs, u):
    """Recorrer versiones (mismo largo) con potencia constante según u (0..k-1, por muestra)."""
    k = len(vs); n = len(vs[0]); i = np.clip(np.floor(u).astype(int), 0, k - 2); f = np.clip(u - i, 0, 1)
    out = np.zeros_like(vs[0])
    for j in range(k):
        w = np.where(i == j, np.cos(f * np.pi / 2), 0) + np.where(i + 1 == j, np.sin(f * np.pi / 2), 0)
        out += w[:, None] * vs[j]
    return out


def a_largo(x, n):
    return x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x),) + x.shape[1:])])


def render(nombre, P, sr=None):
    ZL, ZR = P.escribir()
    esc = sintetizar(ZL, ZR, R / f'{nombre}.wav', sr)
    return leer(R / f'{nombre}.wav', esc), (ZL, ZR)


def guardar(nombre, y, lufs=-16):
    crudo = R / f'{nombre}-crudo.wav'
    wavfile.write(crudo, SR_OUT, (y / (np.abs(y).max() + 1e-12) * .8).astype(np.float32))
    fin = R / f'{nombre}.final.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(crudo), '-af',
                    f'loudnorm=I={lufs}:TP=-1.5:LRA=11,aresample={SR_OUT}', '-c:a', 'pcm_s16le', str(fin)], check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(fin), '-c:a', 'aac', '-b:a', '192k',
                    str(DEMOS / f'{nombre}.m4a')], check=True)
    print('  ', nombre, 'lista', flush=True)


# ───────────── frases que se reusan ─────────────
CINCO = [0, 3.2, 6.4, 9.6, 12.8]                         # el bajo en 5 contra 4: cinco notas parejas en el compás


def verso(P, R_, compases=4):
    """El groove del verso (escrito en Mi): batería de máquina cuadrada, bajo 5:4, guitarra cortada a
    contratiempo, Rhodes en la pista R_. Tríadas que suben por terceras sobre el pedal de Mi."""
    for b in range(compases):
        bajo, tri = I.VERSO[b % 4]
        for pos in (0, 7, 10): I.bombo80(P, q(b, pos), .9)
        for pos in (4, 12): I.caja80(P, q(b, pos), .8)
        for pos in range(16): I.hat80(P, q(b, pos), .55 if pos % 2 == 0 else .3)
        for k, pos in enumerate(CINCO):
            pop = k in (1, 3)
            I.bajo_dedos(P, bajo + (12 if pop else 0), q(b, pos), M.T / 16 * (2.2 if pop else 2.8), .9 if k == 0 else .75, pop=pop)
        for pos in (2, 6, 9, 14): I.guitarra_cortada(P, tri, q(b, pos), .8 if pos != 9 else .55)
        for i, n in enumerate(tri): I.rhodes(R_, n - 12, q(b, 0) + .01 * i, .7, M.T * .95, pan=-.3 + .3 * i)


def coro(P, compases=4, voz=True):
    """El coro pixel (en Mi): seco y cuantizado; pared espectral en polos hexatónicos; bajo en
    corcheas rectas (aquí no hay 5:4: el pixel es cuadrado)."""
    for b in range(compases):
        raiz, menor = I.CORO[b % 8]
        I.pared_espectral(P, raiz + 12, menor, q(b, 0), M.T * .98, 1.2, semilla=b)
        for pos in (0, 6, 8, 11): I.bombo80(P, q(b, pos), .95)
        for pos in (4, 12): I.caja80(P, q(b, pos), .9)
        for pos in range(0, 16, 2): I.hat80(P, q(b, pos), .5)
        for pos in range(0, 16, 2): I.bajo_dedos(P, raiz - 12 if raiz - 12 >= 36 else raiz, q(b, pos), M.T / 16 * 1.6, .8)


# ───────────── demos ─────────────
def p01():
    """el verso: batería de máquina cuadrada, bajo en 5 contra 4 con pops de octava, guitarra cortada
    a contratiempo, Rhodes con cinta; Mi, Do/Mi, Sol#/Mi, Do/Mi (raíces que suben por terceras)."""
    P, Rh = Pista('p01', 5), Pista('p01r', 5)
    verso(P, Rh)
    y, _ = render('p01', P); r, _ = render('p01r', Rh)
    return y + cinta(r)


def p02():
    """tornasol: un órgano sobre Mi y un peine de interferencia (película de aceite) que se mueve:
    cinco grosores (τ = 0.4 … 3 ms) renderizados aparte y tejidos con una curva continua."""
    P = Pista('p02', 5)
    for b in range(4):
        for n in (40, 52, 59, 64, 68, 71): I.organo(P, n, q(b, 0), M.T * .99, .8)
    ZL, ZR = P.escribir()
    taus = [0.4, 0.8, 1.4, 2.2, 3.0]
    vs = []
    for k, tau in enumerate(taus):
        cols = list(range(5))
        esc = sintetizar(tornasol(ZL, cols, tau), tornasol(ZR, cols, tau * 1.07), R / f'p02-{k}.wav')
        vs.append(a_largo(leer(R / f'p02-{k}.wav', esc), L(4)))
    t = np.arange(L(4)) / SR_OUT / T0
    u = (len(taus) - 1) * (.5 - .5 * np.cos(np.pi * t / 2))           # sube y baja el grosor del aceite
    MED['p02_primera_muesca_Hz'] = [round(1000 / (2 * tau)) for tau in taus]
    return recorrido(vs, u)


def p03():
    """el coro pixel: pared espectral en polos hexatónicos (Mi → Do menor → La♭ → Mi menor), seco, y
    Sabina canta «los pixeles no tienen sombra» (Sol# en Mi → Sol natural en Do menor: el roce fantasmal);
    luego Zira canta los bits de «luna» como «cero / uno»."""
    P = Pista('p03', 5)
    coro(P)
    MED['p03_cantante'] = I.cantar(P, 'los pixeles no tienen sombra', [59, 64, 63, 64, 67, 67, 63, 60, 60],
                                   [1, 3, 4, 6, 17, 19, 20, 22, 24], [2, 1, 2, 3, 2, 1, 2, 2, 6], q(0, 0), g=1.3)
    I.cantar(P, 'los pixeles no tienen sombra', [59, 64, 63, 64, 67, 67, 63, 60, 60],
             [1, 3, 4, 6, 17, 19, 20, 22, 24], [2, 1, 2, 3, 2, 1, 2, 2, 6], q(0, 0), voz='zira', g=.45, transporte=-12)
    MED['p03_bits_luna'] = I.ceros_y_unos(P, 'luna', q(2, 0))
    y, _ = render('p03', P)
    return y


def p04():
    """lectura compensada: el mismo verso escrito con el reloj a S/(5/4) (compases 5/4 más largos,
    alturas en Mi) y leído a S: suena una tercera mayor justa arriba (Sol#) AL MISMO TEMPO."""
    with reloj(5 / 4):
        P, Rh = Pista('p04', 5), Pista('p04r', 5)
        verso(P, Rh)
    y, _ = render('p04', P); r, _ = render('p04r', Rh)
    return y + cinta(r)


def p05():
    """el puente vaporwave: la imagen del coro leída a 4/5 SIN compensar (más lenta y una tercera abajo,
    78 bpm) y enterrándose en datamosh: versiones JPEG 0, 4 y 12 tejidas con una curva."""
    P = Pista('p05', 5)
    coro(P)
    ZL, ZR = P.escribir()
    vs = []
    for k, g in enumerate((0, 4, 12)):
        cols = list(range(5))
        esc = sintetizar(arena(ZL, cols, [g] * 5), arena(ZR, cols, [g] * 5), R / f'p05-{k}.wav', sr=S0 * 4 / 5)
        vs.append(a_largo(leer(R / f'p05-{k}.wav', esc), L(5)))
    t = np.arange(L(5)) / SR_OUT / T0
    return cinta(recorrido(vs, 2 * suave((t - .5) / 4.3)), prof_ms=3.2, f=.4)


def p06():
    """el paro de cinta: el último acorde (pared + Rhodes) leído a 1, .85, .7, .55 y .4: cada lectura
    más lenta y más grave, tejidas con una curva (no por escalones)."""
    P = Pista('p06', 3)
    I.pared_espectral(P, 64, False, q(0, 0), M.T * 2, 1.2, semilla=3)
    for i, n in enumerate((52, 59, 64, 68, 71)): I.rhodes(P, n, q(0, 0) + .01 * i, .7, M.T * 2)
    ZL, ZR = P.escribir()
    tasas = [1, .85, .7, .55, .4]
    largo = L(2 / .4)
    vs = []
    for k, tasa in enumerate(tasas):
        esc = sintetizar(ZL, ZR, R / f'p06-{k}.wav', sr=S0 * tasa)
        vs.append(a_largo(leer(R / f'p06-{k}.wav', esc), largo))
    t = np.arange(largo) / SR_OUT / T0
    y = recorrido(vs, (len(tasas) - 1) * suave(t / 3.2))
    return y * (1 - suave((t - 3.6) / 1.4))[:, None]


TODAS = ['p01', 'p02', 'p03', 'p04', 'p05', 'p06']
TITULO = {k: ' '.join(globals()[k].__doc__.split()) for k in TODAS}


def medir_p04():
    """¿Subió 5/4 sin cambiar el tempo? Desplazamiento del espectro en log-frecuencia y periodo del pulso."""
    def logspec(x):
        X = np.abs(np.fft.rfft(x)); f = np.fft.rfftfreq(len(x), 1 / SR_OUT); g = np.geomspace(60, 6000, 8000)
        return np.log10(np.interp(g, f, X) + 1e-9), g
    def periodo(x):
        e = np.abs(x)[::48]; e = np.convolve(e, np.ones(20) / 20, 'same'); e -= e.mean()
        ac = np.correlate(e, e, 'full')[len(e) - 1:]; lo, hi = int(.2 * 1000), int(3 * 1000)
        return (lo + np.argmax(ac[lo:hi])) / 1000
    a = leer(R / 'p01.wav')[:, 0]; b = leer(R / 'p04.wav')[:, 0]
    la, g = logspec(a); lb, _ = logspec(b); paso = math.log(g[1] / g[0])
    c = [np.corrcoef(la[:len(la) - l], lb[l:])[0, 1] for l in range(0, 600)]
    MED['p04_razon_de_altura'] = round(math.exp(paso * int(np.argmax(c))), 4)
    MED['p04_periodo_s_verso_vs_compensado'] = [round(periodo(a), 3), round(periodo(b), 3)]
    MED['p04_duracion_s_verso_vs_compensado'] = [round(len(a) / SR_OUT, 3), round(len(b) / SR_OUT, 3)]


if __name__ == '__main__':
    for n in (sys.argv[1:] or TODAS):
        guardar(n, globals()[n]())
        if n == 'p04': medir_p04()
        json.dump(MED, open(DEMOS / 'medidas.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
    print(json.dumps({k: v for k, v in MED.items() if k != 'p03_cantante'}, ensure_ascii=False))
