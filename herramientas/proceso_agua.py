"""Dibujar etapas reales de una producción del Agua, sin reconstruir borradores históricos."""
import hashlib
import io
import json
from pathlib import Path
import uuid


def guardar(run, entrega):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.io import wavfile
    from PIL import Image, ImageOps
    run = Path(run)
    p = json.loads((run/'partitura.json').read_text(encoding='utf8'))
    sr, audio = wavfile.read(entrega['wav'])
    audio = audio.astype(float)/32768
    etapas = []

    def etapa(fig, nombre):
        raw = io.BytesIO()
        fig.savefig(raw, format='png', dpi=110, bbox_inches='tight')
        plt.close(fig)
        etapas.append((nombre, raw.getvalue()))

    fig, ax = plt.subplots(figsize=(10, 4))
    for row in p['sabina']:
        for e in row['eventos']:
            ax.plot([e['t'], e['t']+e['dur']], [e['nota']]*2, lw=2)
    ax.set(title='1. Eventos de voz en la partitura', xlabel='Segundos', ylabel='Nota MIDI')
    etapa(fig, 'eventos-de-voz')
    h = json.loads((run/'hidrograma.json').read_text())
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(np.arange(len(h['Q']))/h['fr'], h['Q'])
    ax.set(title='2. Caudal calculado desde la lluvia', xlabel='Segundos', ylabel='Caudal normalizado')
    etapa(fig, 'hidrograma')
    fig, ax = plt.subplots(figsize=(10, 4))
    step = max(1, len(audio)//12000)
    ax.plot(np.arange(0, len(audio), step)/sr, audio[::step, 0], lw=.45)
    ax.set(title='3. Mezcla final de las 23 capas', xlabel='Segundos', ylabel='Amplitud, canal izquierdo', ylim=(-1, 1))
    etapa(fig, 'mezcla-final')
    nonce = uuid.uuid4().hex
    full = hashlib.sha256(etapas[0][1]+Path(__file__).read_bytes()+nonce.encode()).hexdigest()
    tag = full[:12]
    dest = Path(entrega['carpeta'])/('proceso-agua-'+tag)
    dest.mkdir(exist_ok=False)
    frames = []
    for i, (name, raw) in enumerate(etapas, 1):
        path = dest/f'{i:02d}-{name}-s{p["semilla"]}-{tag}.png'
        with path.open('xb') as f:
            f.write(raw)
        frames.append(ImageOps.pad(Image.open(io.BytesIO(raw)).convert('RGB'), (900, 420), color='white'))
    gif = dest/f'proceso-agua-s{p["semilla"]}-{tag}.gif'
    frames[0].save(gif, save_all=True, append_images=frames[1:], duration=1900, loop=0, optimize=True)
    (dest/'README.md').write_text('Etapas calculadas de esta ejecución: eventos de la partitura, hidrograma y mezcla final.\nEl GIF reúne estos cálculos; no son capturas históricas ni pasos internos de un generador.\nDuración: 5.7 s, en loop. Semilla: '+str(p['semilla'])+'\n', encoding='utf8')
    hashes = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in dest.iterdir() if f.is_file()}
    (dest/'receta.json').write_text(json.dumps(dict(ejecucion=full, nonce=nonce, semilla=p['semilla'], version=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), sha256=hashes), indent=2), encoding='utf8')
    return str(dest)
