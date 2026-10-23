"""Verificaciones de la entrega: archivos decodificables, dinámica y nota final, sin sobrescribir."""
import hashlib,json,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.io import wavfile
from scipy.signal import correlate,find_peaks
out=Path(sys.argv[1]).resolve();P=json.loads((out/'partitura.json').read_text(encoding='utf8'))
sr,x=wavfile.read(next(out.glob('lo-que-no-sono-*.wav')));x=x.astype(float)/2**31
assert sr==48000 and x.shape==(186*sr,2) and np.isfinite(x).all()
assert np.max(np.abs(x))<1
gif=next(out.glob('*.gif'));im=Image.open(gif);dur=0;frames=[]
for k in range(im.n_frames):
    im.seek(k);dur+=im.info['duration'];im.convert('RGB').load();frames.append(im.size)
assert dur<=10000 and gif.stat().st_size<=15*1024**2 and len(frames)==3
for f in list((out/'proceso').glob('*.png'))+[out/'og.png']:
    with Image.open(f) as png:png.verify()
assert Image.open(out/'og.png').size==(1200,630)
# La última nota se identifica sobre cuatro segundos, no con el bin más cercano de una FFT corta.
y=x[176*sr:180*sr].mean(axis=1);n=2**19
spec=np.abs(np.fft.rfft(y*np.hanning(len(y)),n));freq=np.fft.rfftfreq(n,1/sr)
peak=int(np.argmax(spec));f=float(freq[peak]);expected=440*2**((P['final']['nota']-69)/12)
cents=float(1200*np.log2(f/expected));assert abs(cents)<8,(f,expected)
# Después de 173 s no hay base ni palabras; la cola final está aislada.
tail_stems={}
for name in ['teclas','bajo','percusion','voz-mezcla']:
    _,v=wavfile.read(out/'render'/f'{name}.wav');tail_stems[name]=float(np.max(np.abs(v[174*sr:])))
assert max(tail_stems.values())==0
# Afinación sobre los cuerpos de las sílabas finales largas: autocorrelación, no transitorios de consonantes.
_,voice=wavfile.read(out/'render/voz.wav');voice=voice.mean(axis=1);errors=[]
for frase in P['frases']:
    e=frase['eventos'][-1];f0=440*2**((e['nota']-69)/12)
    seg=voice[int((e['t']+.35)*sr):int((e['t']+.75)*sr)][::3].astype(float)
    seg-=seg.mean();ac=correlate(seg,seg,mode='full',method='fft')[len(seg)-1:]
    lo=int((sr/3)/(f0*1.35));hi=int((sr/3)/(f0*.75));peaks,_=find_peaks(ac[lo:hi]);
    if not len(peaks):continue
    j=lo+peaks[np.argmax(ac[lo:hi][peaks])]
    delta=.5*(ac[j-1]-ac[j+1])/(ac[j-1]-2*ac[j]+ac[j+1]);est=(sr/3)/(j+delta)
    errors.append({'silaba':e['texto'],'nota':e['nota'],'cents':round(float(1200*np.log2(est/f0)),2)})
result={'duracion_s':len(x)/sr,'pico_muestra_dBFS':round(float(20*np.log10(np.abs(x).max())),2),
  'nota_final':{'midi':P['final']['nota'],'esperada_Hz':expected,'medida_Hz':f,'error_cents':cents},
  'silencio_base_despues_174_s':tail_stems,'gif':{'frames':len(frames),'duracion_s':dur/1000,'bytes':gif.stat().st_size},
  'afinacion_silabas_largas':{'metodo':'autocorrelación local alrededor de la nota escrita; orientativo, no escucha humana',
       'mediana_error_absoluto_cents':float(np.median([abs(e['cents']) for e in errors])),'detalle':errors}}
with (out/'verificacion.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
# Manifiesto final incluye documentación y revisiones posteriores a la receta inicial.
sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*') if p.is_file()}
files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file() and 'render' not in p.parts}
with (out/'manifest-final.json').open('x',encoding='utf8') as f:json.dump({'fuentes_finales_sha256':sources,'archivos_sha256':files},f,indent=2)
print(json.dumps(result,ensure_ascii=False,indent=1))
