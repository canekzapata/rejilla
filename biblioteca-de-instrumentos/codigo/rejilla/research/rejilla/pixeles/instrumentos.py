"""Instrumentos de «los pixeles y la luna». Todo en segundos y Hz: sirve con cualquier reloj."""
import math, sys
from pathlib import Path
import numpy as np
from motor import M, E, rng, a_sr, chop, q

YOSHI16 = Path(__file__).parents[3] / 'meleeviewer' / 'output' / 'Arte' / '2026-10-09_yoshi_es_un_vector_16_jpop'
sys.path.insert(0, str(YOSHI16))
import cantante as K
import silabas as SIL
K.CACHE = Path(__file__).parents[1] / 'render' / 'tts-cantante'
TONO = {'mi': 0}


def rnd(): return rng.uniform(0, 6.28)


# ───────────── la voz ─────────────
def silabear(texto):
    pal = [SIL.silabea(p) for p in texto.replace('—', ' ').replace(',', ' ').split()]
    return [s for p in pal for s in p], [len(p) for p in pal]


def cantar(P, texto, notas, pos16, dur16, t0, voz='sabina', g=1.0, pan=0.0, transporte=0):
    """La cantante de yoshi 16 (TD-PSOLA por sílaba), al reloj de la pista (se remuestrea a P.S)."""
    sil, palabras = silabear(texto)
    assert len(sil) == len(notas) == len(pos16) == len(dur16), (texto, len(sil), len(notas))
    t16 = M.T / 16
    frase = {'texto': texto, 'palabras': palabras,
             'silabas': [{'t': p * t16, 'dur': d * t16 * .96, 'nota': n + transporte, 'txt': s}
                         for s, n, p, d in zip(sil, notas, pos16, dur16)]}
    vv, vc = K.VOZ, K.CACHE
    K.VOZ = {'sabina': 'Microsoft Sabina Desktop', 'zira': 'Microsoft Zira Desktop'}[voz]
    K.CACHE = vc.parent / ('tts-cantante' if voz == 'sabina' else f'tts-cantante-{voz}')
    try:
        y, inf = K.canta([frase], (max(p + d for p, d in zip(pos16, dur16)) + 4) * t16)
    finally:
        K.VOZ, K.CACHE = vv, vc
    P.muestra(a_sr(y, K.SR, P.S), t0, g, pan)
    return inf


def ceros_y_unos(P, palabra, t0, alto=76, bajo=71, g=.5, paso16=1):
    """Zira canta los bits ASCII de la palabra: «uno» arriba, «cero» abajo, uno por dieciseisavo."""
    bits = ''.join(f'{ord(c):08b}' for c in palabra)
    for i, b in enumerate(bits):
        y = chop('uno' if b == '1' else 'cero', alto if b == '1' else bajo, 'zira', largo=M.T / 16 * paso16 * .92, sr=P.S)
        P.muestra(y, t0 + i * paso16 * M.T / 16, g * (1 if b == '1' else .75), pan=.55 if b == '1' else -.55)
    return bits


# ───────────── la banda ─────────────
def bajo_dedos(P, midi, t0, dur, vel, pop=False):
    """Bajo de dedos; `pop`: la octava tirada con el dedo (más armónicos arriba, más corta)."""
    f = M.hz(midi)
    arm = ((1, 1.0, 2.6), (2, .55, 4.5), (3, .28, 7), (4, .12, 10)) if not pop else \
          ((1, .7, 5), (2, .6, 7), (3, .45, 10), (4, .3, 14), (5, .2, 18), (6, .12, 24), (7, .07, 30))
    for n, amp, a in arm:
        P.modo(n * f, .34 * vel * amp, t0, a, ataque=500 if not pop else 1500, suelta=dur, ar=26, fase=rnd())


def guitarra_cortada(P, notas, t0, vel, pan=-.45):
    """Rasgueo apagado muy seco: la cuerda casi no suena, se oye la púa."""
    for i, n in enumerate(notas):
        f = M.hz(n)
        for k, amp in ((1, 1), (2, .5), (3, .35), (4, .2), (5, .12)):
            P.modo(k * f, .022 * vel * amp, t0 + .004 * i, 26 + 6 * k, ataque=2500, pan=pan, fase=rnd())
    for f in (2400, 3300, 4700): P.modo(f, .006 * vel, t0, 260, pan=pan, fase=rnd())


def rhodes(P, midi, t0, vel, dur, pan=0.0):
    f = M.hz(midi); b = .5 + .5 * vel
    for mult, amp, a in ((1, 1.0, 1.3 + f / 600), (2, .25 * b, 3.0), (3, .07 * b, 5.5)):
        P.modo(f * mult, .14 * vel * amp, t0, a, ataque=240, suelta=dur, ar=6, pan=pan, fase=rnd())
    P.modo(f * 7.03, .008 * vel * b, t0, 24, ataque=900, pan=pan)


def bombo80(P, t0, vel):
    P.modo(58, 1.0 * vel, t0, 13, ataque=650); P.modo(96, .28 * vel, t0, 30, ataque=900)
    for f in (1700, 2600): P.modo(f, .012 * vel, t0, 250, fase=rnd())


MODOS_CAJA = np.exp(np.random.default_rng(81).uniform(math.log(1300), math.log(6500), 60))
def caja80(P, t0, vel, pan=.05):
    """Caja seca de máquina (sin la reverb compuerta de los 80: eso sería cliché)."""
    P.modo(205, .3 * vel, t0, 30, ataque=1600, pan=pan); P.modo(355, .16 * vel, t0, 36, ataque=1600, pan=pan)
    for f in MODOS_CAJA: P.modo(f, .03 * vel, t0, rng.uniform(38, 52), ataque=4000, pan=pan, fase=rnd())


MODOS_HAT = np.exp(np.random.default_rng(82).uniform(math.log(6500), math.log(15000), 34))
def hat80(P, t0, vel, pan=-.25, abierto=False):
    for f in MODOS_HAT: P.modo(f, .014 * vel, t0, (14 if abierto else 110) * rng.uniform(.85, 1.15), ataque=6000, pan=pan, fase=rnd())


# de «sobre la aurora» (copiados: allá viven en un motor a 104 bpm)
def placa(P, t0, vel, pan=.15):
    for f, amp, a in ((183, 1, 7), (417, .7, 9), (689, .5, 11), (1131, .35, 14), (1702, .2, 18), (2389, .1, 24)):
        P.modo(f * (1 + rng.normal(0, .002)), .07 * vel * amp, t0, a, ataque=2500, pan=pan, fase=rnd())


def organo(P, midi, t0, dur, vel, pan=0.0):
    f = M.hz(midi)
    for n, amp in ((1, 1.0), (2, .8), (3, .5), (4, .4), (6, .25), (8, .2)):
        for det, p in ((-1, pan - .4), (1, pan + .4)):
            P.modo(n * f + det * .9 * n, .018 * vel * amp, t0, .06, ataque=45, suelta=dur, ar=7, pan=max(-1, min(1, p)), fase=rnd())


def pared_espectral(P, raiz_midi, menor, t0, dur, vel=1.0, estira=0.0, lo=105, hi=4000, semilla=0, pan=0.0, escalonado=.55):
    """Acorde = espectro de su fundamental virtual (mayor 4:5:6, menor 10:12:15), en oleadas."""
    r = np.random.default_rng(semilla)
    raiz = M.hz(raiz_midi)
    f0, n0 = (raiz / 4, 4) if not menor else (raiz * 2 / 10, 10)
    tri = (4, 5, 6) if not menor else (10, 12, 15)
    parc = [n for n in range(1, 80) if lo <= f0 * n <= hi and (n <= 24 or n % 2 == 0)]
    if not parc: return 0
    nmin, nmax = parc[0], parc[-1]
    for n in parc:
        f = f0 * n ** (1 + estira); u = (n - nmin) / max(1, nmax - nmin)
        del_acorde = any(n == k * m for k in (1, 2, 4) for m in tri)
        amp = .016 * vel * (1.6 if del_acorde else 1.0) / (1 + (f0 * n / 700) ** 1.4) * 2.2 * r.uniform(.7, 1.15)
        P.modo(f, amp, t0 + escalonado * u + r.uniform(0, .08), .35 + 1.4 * u, ataque=2.2 + 6 * r.uniform(),
               suelta=dur, ar=1.6 + 2 * u, pan=max(-1, min(1, pan + (u - .5) * 1.4 * (1 if n % 2 else -1))), fase=r.uniform(0, 6.28))
    return len(parc)


# ───────────── la armonía (escrita en Mi) ─────────────
# verso: pedal de Mi y tríadas que suben por terceras mayores (Mi, Do, Sol#): la tríada aumentada de raíces
VERSO = [(52, (64, 68, 71)), (52, (60, 64, 67)), (52, (63, 68, 72)), (52, (60, 64, 67))]   # E, C/E, G#/E, C/E
# coro: polos hexatónicos (cero notas en común entre cada par): Mi ↔ Dom, La♭ ↔ Mim, Do ↔ La♭m
CORO = [(52, False), (48, True), (56, False), (52, True), (48, False), (56, True), (52, False), (48, True)]
