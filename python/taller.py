"""Productor didáctico. Ejecutar con --ayuda o abrir ventana.py.
Las fuentes originales de Canek se conservan en fuentes/.
"""
import argparse, hashlib, importlib.util, json, math, os, shutil, subprocess, sys, uuid
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent

def cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, archivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def ffmpeg():
    local = BASE / 'bin' / ('ffmpeg.exe' if os.name == 'nt' else 'ffmpeg')
    p = str(local) if local.is_file() else shutil.which('ffmpeg')
    if not p: raise ValueError('Falta FFmpeg. Lee manual.html, instalación. Puedes usar el motor directo mientras tanto.')
    r = subprocess.run([p, '-hide_banner', '-filters'], capture_output=True, text=True, check=True)
    if 'spectrumsynth' not in r.stdout: raise ValueError('Este FFmpeg no incluye spectrumsynth. Consigue una compilación completa.')
    return p

def validar(s):
    bpm = float(s.get('bpm', 100)); compases = int(s.get('compases', 4))
    if not 40 <= bpm <= 200 or not 1 <= compases <= 32: raise ValueError('Usa 40..200 BPM y 1..32 compases.')
    if len(s.get('pistas', [])) > 16: raise ValueError('Máximo 16 pistas por ejercicio.')
    for p in s.get('pistas', []):
        for n in p.get('notas', []):
            if not 24 <= float(n['midi']) <= 96: raise ValueError('MIDI debe estar entre 24 y 96.')
            if not 0 <= float(n.get('vel', .7)) <= 1: raise ValueError('vel debe estar entre 0 y 1.')
            if not 0 <= float(n['pulso']) < compases*4: raise ValueError('Una entrada queda fuera de la pieza.')
            if not 0 < float(n.get('dur', .5)) <= 32: raise ValueError('dur debe estar entre 0 y 32 pulsos.')
            if not -1 <= float(n.get('pan', 0)) <= 1: raise ValueError('pan debe estar entre -1 y 1.')
    return bpm, compases

def producir(archivo, motor='directo', destino=None):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.io import wavfile
    from scipy.signal import spectrogram
    from PIL import Image, ImageOps, ImageDraw
    raw = Path(archivo).read_bytes(); s = json.loads(raw.decode('utf-8-sig'))
    if 'motor_propio' in s:
        from motores_propios import producir as producir_motor_propio
        return producir_motor_propio(archivo,destino)
    if 'prototipo' in s:
        from prototipos import producir as producir_prototipo
        return producir_prototipo(archivo,destino)
    bpm, bars = validar(s); seed = int(s.get('semilla', 20261020))
    nonce = uuid.uuid4().hex
    version = Path(__file__).read_bytes()
    ident = hashlib.sha256(raw + version + nonce.encode()).hexdigest(); tag = ident[:12]
    parent = Path(destino) if destino else BASE/'salidas'
    parent.mkdir(parents=True, exist_ok=True)
    out = parent / f'rejilla-taller-s{seed}-{tag}'; out.mkdir(exist_ok=False)
    proc = out/'proceso'; proc.mkdir()
    def nuevo(nombre, data):
        with (out/nombre).open('xb') as f: f.write(data)
    nuevo(f'partitura-s{seed}-{tag}.json', raw)
    R = cargar('musica_original', BASE/'fuentes/rejilla/musica.py')
    I = cargar('biblioteca_modal', BASE/'biblioteca-de-instrumentos/motores/rejilla.py')
    R.H = 32768; R.N = 2*R.H; R.R = 2048; R.fijar_tempo(bpm)
    sr = R.S; duracion = bars*R.T; tracks = []; Zs = []; reference = np.zeros((round(duracion*sr),2))
    print(f'Creando {bars} compases a {bpm:g} BPM, motor {motor}. Carpeta: {out}', flush=True)
    for index, p in enumerate(s.get('pistas', [])):
        P = R.Pista(p.get('nombre', f'pista-{index+1}'), bars)
        for n in p.get('notas', []):
            midi = float(n['midi']); start = float(n['pulso'])*60/bpm; hold = float(n.get('dur',.5))*60/bpm
            vel = float(n.get('vel', .7)); pan = float(n.get('pan',0))
            if 'instrumento' in p:
                K = json.loads((BASE/'biblioteca-de-instrumentos/fichas'/f"{p['instrumento']}.json").read_text(encoding='utf8'))
                I.a_pista(P,K,midi,start,vel,pan=pan,dur=hold,ny=sr/2-100)
            else:
                # Cada parcial es [razón respecto a la nota, nivel, caída a -60 dB en segundos].
                parts = p.get('parciales', [[1,1,1.2],[2,.22,.4],[3,.08,.15]])
                ataque = float(p.get('ataque',.008))
                if not .001 <= ataque <= 1: raise ValueError('ataque: .001..1 segundos.')
                for ratio, level, t60 in parts:
                    if not 0 < float(ratio) <= 32 or not 0 < float(t60) <= 30 or not 0 <= float(level) <= 2:
                        raise ValueError('Parcial fuera de rango: razón 0..32, nivel 0..2, T60 0..30.')
                    a = math.log(1000)/t60; at = max(3/ataque, a+1)
                    P.modo(R.hz(midi)*ratio, .12*vel*level, start,a,ataque=at,suelta=hold,ar=16,pan=pan,fase=0)
        y = np.column_stack([P.tiempo(0,duracion,c) for c in (0,1)])
        reference += y; tracks.append((p,P,y))
    if not tracks: raise ValueError('Agrega al menos una pista con notas.')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
    etapas = []
    def guardar(fig, paso, nombre):
        path = proc/f'{paso:02d}-{nombre}-s{seed}-{tag}.png'
        if path.exists(): raise FileExistsError(path)
        fig.savefig(path,dpi=125,bbox_inches='tight',facecolor='white'); plt.close(fig); etapas.append(path)
    fig, ax = plt.subplots(figsize=(11,4))
    for ix,(p,P,y) in enumerate(tracks):
        for n in p['notas']:
            ax.plot([n['pulso'],n['pulso']+n.get('dur',.5)],[n['midi']]*2,lw=4,label=None)
    ax.set(xlabel='Pulsos de negra (4 por compás)',ylabel='Nota MIDI',title='1. Partitura escrita: entradas, alturas y duraciones'); ax.grid(alpha=.2)
    guardar(fig,1,'partitura')
    fig, ax = plt.subplots(figsize=(11,4)); t=np.arange(len(reference))/sr
    for ix,(p,P,y) in enumerate(tracks): ax.plot(t,y[:,0]+ix*.5,lw=.5,label=p.get('nombre',str(ix+1)))
    ax.set(xlabel='Segundos',ylabel='Amplitud + separación visual',title='2. Pistas calculadas: ataques, cuerpos y colas'); ax.legend(loc='upper right'); guardar(fig,2,'pistas')
    outwav = out/f'audio-s{seed}-{tag}.wav'
    if motor == 'rejilla':
        exe = ffmpeg(); RENDER = out/'datos-espectrales'; RENDER.mkdir()
        ZL = np.zeros((bars,R.H),complex); ZR = ZL.copy()
        for p,P,y in tracks:
            print('Escribiendo espectro de '+p.get('nombre','pista'),flush=True)
            zl,zr=P.escribir(); ZL+=zl; ZR+=zr
        m16,p16,scale=R.a_imagen(ZL,ZR)
        mag=RENDER/f'magnitud-{tag}.raw'; pha=RENDER/f'fase-{tag}.raw'
        with mag.open('xb') as f: m16.tofile(f)
        with pha.open('xb') as f: p16.tofile(f)
        # Sólo cambiar el alcance de escala de visualización; los datos 16 bit se conservan completos.
        fig,ax=plt.subplots(figsize=(11,4)); edges=np.geomspace(30,min(12000,sr/2-100),400)
        selected=np.clip(np.round(np.sqrt(edges[:-1]*edges[1:])/R.F).astype(int),1,R.H-1)
        im=ax.pcolormesh(np.arange(bars+1)*R.T,edges,20*np.log10(np.maximum(np.abs(ZL[:,selected]).T,1e-7)),shading='flat',cmap='magma',vmin=-85,vmax=-25)
        ax.set(xlabel='Segundos (una columna por compás)',ylabel='Hz (vista logarítmica)',yscale='log',title='3. Magnitud escrita para FFmpeg, canal izquierdo'); fig.colorbar(im,ax=ax,label='dB, referencia coeficiente 1'); guardar(fig,3,'magnitud')
        entrada=lambda p:['-f','rawvideo','-pix_fmt','gray16le','-s',f'{bars}x{2*R.H}','-r','1','-i',str(p)]
        crudo=RENDER/f'crudo-{tag}.wav'
        subprocess.run([exe,'-hide_banner','-loglevel','error','-n',*entrada(mag),*entrada(pha),'-filter_complex',f'[0]setpts=N/TB,format=gray16le[m];[1]setpts=N/TB,format=gray16le[p];[m][p]spectrumsynth=sample_rate={sr}:channels=2:scale=lin:slide=fullframe:win_func=rect:overlap=0','-c:a','pcm_f32le',str(crudo)],check=True)
        got_sr,y=wavfile.read(crudo); audio=np.asarray(y,dtype=float)*scale
        if got_sr != sr or audio.shape != reference.shape: raise ValueError(f'Dimensión inesperada de FFmpeg: {audio.shape}, esperado {reference.shape}')
        snr=20*np.log10(max(1e-20,np.linalg.norm(reference))/max(1e-20,np.linalg.norm(reference-audio)))
    else: audio=reference; scale=None; snr=None
    if not np.isfinite(audio).all() or np.max(np.abs(audio))<1e-9: raise ValueError('Audio vacío o no finito.')
    peak=float(np.max(np.abs(audio))); gain=min(1.,.8/peak); audio*=gain
    if outwav.exists(): raise FileExistsError(outwav)
    wavfile.write(outwav,sr,np.round(np.clip(audio,-1,1)*32767).astype(np.int16))
    fig,ax=plt.subplots(figsize=(11,4)); f,tt,sp=spectrogram(audio.mean(axis=1),sr,nperseg=1024,noverlap=768)
    ax.pcolormesh(tt,f,10*np.log10(np.maximum(sp,1e-14)),shading='auto',cmap='magma',vmin=-100,vmax=-35)
    ax.set(ylim=(30,min(12000,sr/2)),yscale='log',xlabel='Segundos',ylabel='Hz (log)',title='4. Audio final: espectrograma de la mezcla'); guardar(fig,4,'espectrograma')
    frames=[]
    for path in etapas:
        img=Image.open(path).convert('RGB'); frame=ImageOps.pad(img,(1000,480),color='white'); frames.append(frame)
    gif=out/f'proceso-rejilla-s{seed}-{tag}.gif'
    frames[0].save(gif,save_all=True,append_images=frames[1:],duration=1700,loop=0,optimize=True)
    nuevo(f'receta-s{seed}-{tag}.json',json.dumps({'ejecucion':ident,'nonce':nonce,'fecha_utc':datetime.now(timezone.utc).isoformat(),'semilla':seed,'motor':motor,'bpm_solicitado':bpm,'bpm_real':240/R.T,'sample_rate':sr,'N':R.N,'H_por_canal':R.H,'segundos_por_columna':R.T,'hz_por_fila':R.F,'pico_previo':peak,'ganancia_final':gain,'snr_rejilla_vs_directo_db':None if snr is None else float(snr),'escala_magnitud':scale,'partitura_sha256':hashlib.sha256(raw).hexdigest(),'programa_sha256':hashlib.sha256(version).hexdigest(),'nota':'Normalización sólo por pico; no equivale a normalizar LUFS. El GIF reúne etapas calculadas, no capturas de una sesión en vivo.'},ensure_ascii=False,indent=2).encode())
    nuevo('proceso/README.md' if False else 'LEEME.txt',f'Audio y etapas guardados. Semilla {seed}. Ejecución {ident}.\nGIF: {len(frames)*1.7:.1f} s.\nCada PNG corresponde a un cálculo real. La vista de partitura usa pulsos ideales; el tempo espectral se redondea al sample rate entero registrado en la receta.\n'.encode())
    (proc/'README.md').write_text('Orden: partitura, pistas directas, magnitud (sólo motor Rejilla), espectrograma final.\nEl GIF reúne estas etapas calculadas. No representa borradores históricos.\n',encoding='utf8')
    hashes={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    nuevo('HUELLAS.json',json.dumps(hashes,indent=2).encode())
    print('Listo: '+str(out),flush=True); return out

if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Rejilla: producir audio, gráficas y GIF desde una partitura JSON.')
    ap.add_argument('partitura'); ap.add_argument('--motor',choices=['directo','rejilla'],default='directo'); ap.add_argument('--destino')
    a=ap.parse_args()
    try: producir(a.partitura,a.motor,a.destino)
    except Exception as e: print('No se pudo producir: '+str(e),file=sys.stderr); sys.exit(1)
