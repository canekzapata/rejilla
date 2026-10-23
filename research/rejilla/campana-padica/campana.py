"""Use the same JS resonator from Rejilla/Python. No duplicated physics.

Requires Node.js and numpy. Input events: {t, hit?, vel?, params?, clear?}.
Parameters: fold, depth, tension, damping, midi, pickup. Units: seconds, Hz via MIDI.
"""
from pathlib import Path
import json,subprocess,tempfile
import numpy as np
ROOT=Path(__file__).resolve().parent

def render(partitura,duracion=10,sr=24000):
    scratch=ROOT/'tmp';scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='campana-',dir=scratch) as work:
        work=Path(work);score={**partitura,'duration':duracion,'sr':sr}
        inp=work/'partitura.json';inp.write_text(json.dumps(score),encoding='utf-8')
        subprocess.run(['node',str(ROOT/'renderizar.mjs'),str(inp),str(work/'audio')],check=True,capture_output=True)
        audio=np.fromfile(work/'audio.raw',dtype='<f4').reshape(-1,2).copy()
        receipt=json.loads((work/'audio.json').read_text(encoding='utf-8'))
    return audio,receipt

def coeficientes_rejilla(audio,sr=24000):
    """Full complex sampled DFT, one second per column. Includes DC/Nyquist.

    Return channels × columns × (sr/2+1). Direct inverse rFFT recovers the audio.
    A spectrumsynth writer must explicitly handle the endpoint rows; this helper
    does not claim the closed-form modal writing of Rejilla's other instruments.
    """
    y=np.asarray(audio,dtype=np.float64)
    if y.ndim==1:y=y[:,None]
    columns=(len(y)+sr-1)//sr
    y=np.pad(y,((0,columns*sr-len(y)),(0,0))).reshape(columns,sr,-1)
    return (np.fft.rfft(y,axis=1)/sr).transpose(2,0,1)
