"""Rejilla toma instrumentos de la biblioteca: arpa de boca, berimbau, saron, balafón y marimba suenan juntos.

Los instrumentos vienen de ../../../biblioteca-de-instrumentos, fijados por huella en instrumentos-77a5750fe244/ (tomar.py).
Cada uno va por la vía que mide la biblioteca (fichas/fidelidad-rejilla.json):
- por MODOS en la rejilla (spectrumsynth es el único que toca): arpa de boca, saron, marimba;
- por el GEMELO en el tiempo (lo no lineal y el berimbau): balafón, berimbau.
Escala In sobre D, 100 bpm (una columna = un compás de 2.4 s). Una prueba exacta compara lo que pintó ffmpeg con los mismos
modos sumados en el tiempo.

    python biblioteca/suenan_juntos.py
"""
import hashlib, json, math, os, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile

AQUI = Path(__file__).parent
sys.path.insert(0, str(AQUI.parent))
import musica as Mu                                   # la maquinaria de la rejilla: Pista, a_imagen, sintetizar

INSTR = AQUI / 'instrumentos-77a5750fe244'
sys.path.insert(0, str(INSTR / 'motores'))
import rejilla as RJ, gemelo as GM                    # los motores, de la copia fijada (no de la biblioteca viva)

TON, ESC, BPM, SR = 'D', [0, 1, 5, 7, 8], 100, 48000
FIDELIDAD = json.load(open(INSTR / 'fichas' / 'fidelidad-rejilla.json', encoding='utf-8'))
K = {i: RJ.ficha(i, INSTR / 'fichas') for i in ('arpaboca', 'berimbau', 'saron', 'balafon', 'marimba')}
Mu.fijar_tempo(BPM)
B = 60 / BPM                                          # un tiempo


def midi(o, g):
    n = len(ESC); q = g // n
    return 12 * (o + 1) + 2 + ESC[g - q * n] + 12 * q


def partitura():
    """(instrumento, t, midi, vel, dur, pan). 9 compases: el arpa sola, entra el berimbau, luego el saron, el balafón y la marimba."""
    ev = []
    arpa = [(4, 0), (4, 2), (4, 3), (5, 0), (4, 3), (4, 2), (5, 2), (5, 0), (4, 3), (4, 1), (4, 2), (4, 0), (5, 0), (4, 4), (4, 3), (4, 0), (4, 2), (4, 0)]
    for k, (o, g) in enumerate(arpa): ev.append(('arpaboca', k * 2 * B, midi(o, g), .75, 2 * B * .85, -.15))
    for c in range(1, 9):                                              # toque de Angola: chi chi DON din, cada dos tiempos
        for m in range(2):
            t = c * 4 * B + m * 2 * B
            ev += [('berimbau', t, midi(3, 0), .3, .4, .35), ('berimbau', t + .5 * B, midi(3, 0), .3, .4, .35),
                   ('berimbau', t + B, midi(3, 0), .8, .4, .35), ('berimbau', t + 1.5 * B, midi(3, 1), .8, .4, .35)]
    balungan = [2, 3, 2, 1, 0, 1, 2, 4]
    for c in range(3, 9):
        for k in range(4): ev.append(('saron', c * 4 * B + k * B, midi(4, balungan[(c * 4 + k) % 8]), .55, .5, -.45))
    for c in range(5, 9):
        for k in range(8): ev.append(('balafon', c * 4 * B + k * .5 * B, midi(5, [0, 2, 1, 3, 0, 2, 4, 3][k]), .7 if k % 2 == 0 else .45, .3, .55))
    for c in range(6, 9):
        for k in (0, 3, 6): ev.append(('marimba', c * 4 * B + k * .5 * B, midi(3, [0, 2, 1][k // 3]), .6, .5, -.05))
    return ev


def main():
    ev = partitura(); dur = 9 * 4 * B + 3.0; cols = math.ceil(dur / Mu.T) + 1
    ident = hashlib.sha256(json.dumps(ev).encode() + open(INSTR / 'manifiesto.json', 'rb').read() + os.urandom(16)).hexdigest()
    h = ident[:12]; out = AQUI / f'suenan-juntos-{h}'; out.mkdir(exist_ok=False); render = AQUI.parent / 'render' / f'biblioteca-{h}'; render.mkdir(parents=True, exist_ok=False)
    via = {i: FIDELIDAD[i]['rejilla'] for i in K}
    print('vías:', via, f'| {len(ev)} notas, {dur:.1f} s, S={Mu.S}')
    pistas, medidas = {}, {}
    for inst in K:
        notas = [e for e in ev if e[0] == inst]
        wav = render / f'{inst}.wav'
        if via[inst] == 'modos':
            P = Mu.Pista(inst, cols)
            for _, t, m, v, d, pan in notas: RJ.a_pista(P, K[inst], m, t, v, pan=pan, tonica=TON, escala=ESC, dur=d)
            ZL, ZR = P.escribir(); m16, p16, esc = Mu.a_imagen(ZL, ZR); Mu.sintetizar(m16, p16, wav)
            sr, x = wavfile.read(wav); a = min(n[1] for n in notas) + .5; b = a + 4   # prueba exacta donde el instrumento suena: ffmpeg contra los mismos modos en el tiempo
            y = P.tiempo(a, b, 0) / esc; seg = x[int(round(a * sr)):int(round(a * sr)) + len(y), 0]
            medidas[inst] = dict(via='modos (spectrumsynth)', modos=len(P.segs), escala=float(esc), error_exacto=float(np.abs(seg - y).max() / np.abs(y).max()))
            pistas[inst] = (wav, esc)
        else:
            n = int(dur * SR); L = np.zeros(n); R = np.zeros(n)
            for _, t, m, v, d, pan in notas:
                y = GM.nota(K[inst], m, v, 2.6, SR, tonica=TON, escala=ESC, dur=d); i = int(t * SR); y = y[:n - i]
                gl, gr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
                L[i:i + len(y)] += y * gl; R[i:i + len(y)] += y * gr
            wavfile.write(wav, SR, np.stack([L, R], 1).astype(np.float32)); medidas[inst] = dict(via='gemelo (tiempo)', gemelo_vs_web_db=FIDELIDAD[inst]['gemelo_db'])
            pistas[inst] = (wav, 1.0)
        print(' ', inst, medidas[inst])
    # mezcla: cada pista × su escala, un cuarto pequeño (como musica.py) y loudnorm −14
    nombres = list(pistas); ent = sum([['-i', str(pistas[i][0])] for i in nombres], [])
    vol = {'arpaboca': 1.0, 'berimbau': .9, 'saron': .8, 'balafon': .75, 'marimba': .9}
    grafo = ';'.join([f"[{k}]aresample={SR},volume={vol[i] * pistas[i][1]:.6f}[p{k}]" for k, i in enumerate(nombres)] + [
        ''.join(f'[p{k}]' for k in range(len(nombres))) + f"amix=inputs={len(nombres)}:normalize=0,asplit[seco][w0]",
        f"aevalsrc=d=2.6:s={SR}:exprs='(random(0)*2-1)*exp(-t*2.2)|(random(1)*2-1)*exp(-t*2.2)',lowpass=f=6000,highpass=f=250[ir]",
        "[w0][ir]afir=dry=0:wet=1[rev]", "[seco][rev]amix=inputs=2:weights=1 0.09:normalize=0,highpass=f=30,loudnorm=I=-14:TP=-1.2:LRA=9[out]"])
    m4a = out / f'suenan-juntos-{h}.m4a'; mezcla = render / 'mezcla.wav'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', *ent, '-filter_complex', grafo, '-map', '[out]', '-ar', str(SR), '-c:a', 'pcm_f32le', str(mezcla)], check=True)
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-i', str(mezcla), '-c:a', 'aac', '-b:a', '192k', str(m4a)], check=True)
    receta = dict(ejecucion=ident, instrumentos=str(INSTR.name), biblioteca=json.load(open(INSTR / 'manifiesto.json', encoding='utf-8'))['biblioteca_commit'],
                  tonica=TON, escala=ESC, bpm=BPM, S=Mu.S, notas=len(ev), medidas=medidas, m4a_sha256=hashlib.sha256(m4a.read_bytes()).hexdigest())
    (out / 'receta.json').write_text(json.dumps(receta, ensure_ascii=False, indent=1), encoding='utf-8')
    print('→', out, '| render en', render)
    return out, render, ev


if __name__ == '__main__':
    main()
