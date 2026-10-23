"""Rejilla adapter. Uses the very same JS fluid and voice as the browser."""
from pathlib import Path
import json, subprocess, tempfile, math
import numpy as np
HERE=Path(__file__).resolve().parent

def render(partitura, duracion=12, sr=24000):
    if not 0 < duracion <= 180 or sr not in (24000,32768,48000):
        raise ValueError('Duración 0..180 y sr 24000, 32768 o 48000')
    (HERE/'tmp').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='agua-',dir=HERE/'tmp') as d:
        p=Path(d);s={**partitura,'duration':duracion,'sr':sr}
        (p/'score.json').write_text(json.dumps(s),encoding='utf-8')
        subprocess.run(['node',str(HERE/'renderizar.mjs'),str(p/'score.json'),str(p/'audio')],check=True)
        y=np.fromfile(p/'audio.raw',dtype='<f4').reshape(-1,2).copy()
        meta=json.loads((p/'audio.json').read_text())
    if not np.isfinite(y).all():raise ValueError('Audio no finito')
    return y,meta

def coeficientes_rejilla(audio,sr=24000):
    """channels × 1-second columns × bins, INCLUDING DC and Nyquist."""
    y=np.asarray(audio,dtype=np.float64)
    if y.ndim==1:y=y[:,None]
    n=math.ceil(len(y)/sr)
    y=np.pad(y,((0,n*sr-len(y)),(0,0)))
    return (np.fft.rfft(y.reshape(n,sr,-1),axis=1)/sr).transpose(2,0,1)
