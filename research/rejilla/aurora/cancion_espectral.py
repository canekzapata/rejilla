"""Rejilla 04 · «sobre la aurora» — loop E: la pared espectral.

Canek: «los acordes de piano son raros y deberían ser súper contemporáneos, como pared de sonidos
armónicos». Música espectral (Grisey, Murail): cada acorde del laberinto se vuelve el espectro de
su fundamental virtual (mayor = armónicos 4:5:6, menor = 10:12:15), una pared de 30 a 50 parciales
con los armónicos «entre teclas» (7, 11, 13). En entropía la serie se estira poco a poco (la pared
se vuelve metálica) y en confundo se va enderezando.

Parte de la versión TEJIDA (guardada, tag aurora-tejida-guardar): copia todas sus pistas y rehace
sólo la armonía (pared en lugar de piano; el órgano se queda). Salida nueva: no pisa la tejida.

    python aurora/cancion_espectral.py
"""
import json, shutil
import numpy as np
from pathlib import Path
import cancion as K
import cancion_tejida as D
import instrumentos as I
from motor import M, S, sintetizar, leer

ORIGEN = D.R2                                                 # render/aurora-tejida
D.R2 = ORIGEN.parent / 'aurora-espectral'; D.R2.mkdir(parents=True, exist_ok=True)
D.TAG = 's1015-espectral'


def estiramiento(b):
    """Cuánto se abre la serie en el compás b: 0 casi siempre; crece en la entropía y se endereza en confundo."""
    sec = K.PLAN[b]['sec']
    if sec == 'entropía':
        i = b - K.COLS['entropía'][0]; return .009 * i / (len(K.COLS['entropía']) - 1)
    if sec == 'confundo':
        i = b - K.COLS['confundo'][0]; return .007 * (1 - i / (len(K.COLS['confundo']) - 1))
    return 0.0


banda_original = K.banda
def banda(P, b, x, kit=True, ost=True, piano=True, organo=0.0, vel=1.0):
    """La misma banda, pero donde iba el piano va la pared espectral (oleadas en 0 y en 7)."""
    banda_original(P, b, x, kit=kit, ost=ost, piano=False, organo=organo, vel=vel)
    if piano:
        for pos, du, v in ((0, 6.5, 1.0), (7, 8.5, .7)):
            I.pared_espectral(P['armonia'], x['raiz'], x['menor'], K.q(b, pos), du * K.t16, v * vel,
                              estira=estiramiento(b), semilla=b * 16 + pos)
K.banda = banda


def main():
    # 1. todo lo de la tejida, menos la armonía
    esc = json.load(open(ORIGEN / 'escalas.json'))['escalas']
    for f in ORIGEN.glob('*.wav'):
        if f.name.startswith('armonia') or f.name.startswith('tl-') or f.name.startswith('sobre-la-aurora'): continue
        destino = D.R2 / f.name
        if not destino.exists(): shutil.copy2(f, destino)
    esc = {k: v for k, v in esc.items() if not k.startswith('armonia')}
    viejo = leer(ORIGEN / 'armonia.wav', json.load(open(ORIGEN / 'escalas.json'))['escalas']['armonia'])

    # 2. la armonía nueva, con sus versiones (arena, espejo, ruido) y su prolación
    P, _, _ = K.componer()
    ZL, ZR = P['armonia'].escribir()
    esc['armonia'] = sintetizar(ZL, ZR, D.R2 / 'armonia.wav')
    for (sec, nom), (zl, zr) in D.versiones('armonia', ZL, ZR).items():
        esc[f'armonia|{sec}|{nom}'] = sintetizar(zl, zr, D.R2 / f'armonia__{sec}__{nom}.wav')
    v0, v1 = K.COLS['se expande'][0], K.COLS['se expande'][-1] + 1
    for k, sr in ((1, S * 3 // 2), (2, 2 * S)):
        esc[f'armonia|prolacion|{k}'] = sintetizar(np.ascontiguousarray(ZL[v0:v1]), np.ascontiguousarray(ZR[v0:v1]),
                                                   D.R2 / f'armonia__prolacion__{k}.wav', sr=sr)
    json.dump({'escalas': esc}, open(D.R2 / 'escalas.json', 'w'))

    # 3. el mismo nivel que tenía la armonía (medido en las secciones con banda)
    nuevo = leer(D.R2 / 'armonia.wav', esc['armonia'])
    cols = K.COLS['tormenta'] + K.COLS['bocinas'] + K.COLS['se expande']
    sl = lambda y: np.concatenate([y[D.L(c):D.L(c + 1)] for c in cols])
    razon = float(sl(viejo).std() / (sl(nuevo).std() + 1e-12))
    K.GANANCIA['armonia'] *= razon
    print(f'armonía: la pared se iguala a la armonía vieja ×{razon:.2f} → ganancia {K.GANANCIA["armonia"]:.2f}')
    json.dump({'ganancia_armonia': K.GANANCIA['armonia'], 'razon': razon}, open(D.R2 / 'nivel.json', 'w'))

    D.tejer()
    D.mezclar()


if __name__ == '__main__':
    main()
