"""Render corto de una ficha modal, golpe/boca/arco o Python. Rechaza sobrescribir."""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
import numpy as np
from scipy.io import wavfile

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / 'biblioteca-de-instrumentos'

def cargar(nombre):
    spec = importlib.util.spec_from_file_location('bib_' + nombre, BIB / 'motores' / (nombre + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('ficha')
    ap.add_argument('--midi', type=float, default=60)
    ap.add_argument('--dur', type=float, default=.7)
    ap.add_argument('--salida', type=Path, required=True)
    a = ap.parse_args()
    if not 0 < a.dur <= 30:
        ap.error('--dur debe estar entre 0 y 30 segundos')
    if a.salida.exists():
        ap.error('La salida ya existe; usa otro nombre')
    if a.ficha not in json.loads((BIB / 'fichas/todas.json').read_text(encoding='utf-8')):
        ap.error('Ficha desconocida. Lista las disponibles con biblioteca-de-instrumentos/tomar.py --lista')
    k = json.loads((BIB / 'fichas' / (a.ficha + '.json')).read_text(encoding='utf-8'))
    sr = 44100
    if k['motor'] in ('golpe', 'boca', 'arco'):
        y = cargar('gemelo').nota(k, a.midi, .8, segundos=a.dur + 1.3, sr=sr, dur=a.dur)
    elif k['motor'] == 'modal':
        mod = cargar('rejilla')
        y = mod.tiempo(mod.modos(k, a.midi, .05, .8, dur=a.dur), a.dur + 1.3, sr)
    elif k['motor'] == 'python':
        y, sr = cargar('python').nota(k, a.midi, dur=a.dur)
    else:
        ap.error('Esta vía usa ' + k['motor'] + '; consulta el motor JS y su ficha')
    y = np.asarray(y)
    if not np.isfinite(y).all() or not np.any(y):
        raise RuntimeError('El motor no produjo señal finita no muda')
    peak = float(np.max(np.abs(y)))
    y = y * min(1., .98 / peak)
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    with a.salida.open('xb') as f:
        wavfile.write(f, sr, (y * 32767).astype(np.int16))
    print(str(a.salida), '·', len(y) / sr, 'segundos')

if __name__ == '__main__':
    main()
