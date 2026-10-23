"""Medir el watervoicephone (render/<et>-vozagua-*.wav, eventos en el .json):
  por palabra cantada: f0 mediana (YIN de la cantante) contra la nota pedida (cents) y % de cuadros con altura
  por vocal sostenida: picos de la envolvente armónica (¿caen en los formantes? con doble, ¿se ven las dos vocales?)
    python herramientas/medir_vozagua.py v2
"""
import glob, json, sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ.parents[2] / 'meleeviewer' / 'output' / 'Arte' / '2026-10-09_yoshi_es_un_vector_16_jpop'))
import cantante as K
FOR = {'a': [800, 1200, 2500], 'e': [450, 1900, 2550], 'i': [300, 2300, 3000], 'o': [500, 880, 2400], 'u': [330, 780, 2300]}
et = sys.argv[1]
for f in sorted(glob.glob(str(RAIZ / 'render' / f'{et}-vozagua-*.wav'))):
    sr, x = wavfile.read(f); x = x.astype(float) / 32768; J = json.load(open(f[:-4] + '.json', encoding='utf-8'))
    nombre = Path(f).stem[len(et) + 1:]; print(f'== {nombre}  rms crudo {20 * np.log10(np.sqrt(np.mean(x ** 2)) * J["pico"] / .9):.1f} dB')
    for e in J['eventos']:
        a, b = int((e['t'] + .25 * e['dur']) * sr), int((e['t'] + .85 * e['dur']) * sr); seg = x[a:b]
        lin = f"  {e['texto']:9s}"
        if e.get('nota') and e.get('modo', 'canto') != 'susurro':
            f0, _ = K.A.curva(seg, sr); v = f0[~np.isnan(f0)]; fp = 440 * 2 ** ((e['nota'] - 69) / 12)
            lin += f" voz {e.get('voz', 1):.2f}  altura {round(1200 * np.log2(np.median(v) / fp)) if len(v) else '—':>5} c  con altura {100 * len(v) / max(1, len(f0)):3.0f} %"
        if e.get('doble') or len(set(e['texto'])) == 1:
            # la envolvente: amplitud de cada armónico k·f0 (con la f0 pedida); los picos a menos de 15 dB del máximo
            fp = 440 * 2 ** ((e['nota'] - 69) / 12); n = np.arange(len(seg)); h = np.hanning(len(seg))
            amp = np.array([20 * np.log10(abs(np.sum(seg * h * np.exp(-2j * np.pi * k * fp * n / sr))) + 1e-9) for k in range(1, int(3600 / fp))])
            pk = [k for k in range(len(amp)) if (k == 0 or amp[k] >= amp[k - 1]) and (k == len(amp) - 1 or amp[k] >= amp[k + 1]) and amp[k] > amp.max() - 15]
            lin += '  picos de la envolvente: ' + '  '.join(f'{round((k + 1) * fp)} ({amp[k] - amp.max():.0f})' for k in pk)
        if e.get('doble'): lin += f"  [pedidas {e['texto'][0]} {FOR[e['texto'][0]][:2]} + {e['doble']} {FOR[e['doble']][:2]}]"
        print(lin)
