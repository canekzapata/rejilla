"""Comprobar el WAV real y conservar vistas de etapas efectivamente realizadas."""
from audio_v10 import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

plt.rcParams.update({'font.family':'Segoe UI','font.size':10,'figure.facecolor':'#10201e','axes.facecolor':'#10201e',
 'text.color':'#ead3a8','axes.labelcolor':'#d8e0d7','xtick.color':'#abc8b6','ytick.color':'#abc8b6',
 'axes.edgecolor':'#607b70','savefig.facecolor':'#10201e'})

def plot(out,n,stem,fig):
    path=out/'proceso'/f'{n:02}-{stem}-s1-{out.name.split("-")[-1]}.png';assert not path.exists()
    fig.savefig(path,dpi=115,bbox_inches='tight');plt.close(fig);return path
def spans(mask,sr):
    changes=np.diff(np.r_[False,mask,False].astype(np.int8));a=np.flatnonzero(changes==1);b=np.flatnonzero(changes==-1)
    return [[float(i/sr),float(j/sr)] for i,j in zip(a,b)]
def finish():
    out,p=context();tag=out.name.split('-')[-1];m=json.loads((out/'master-v10.json').read_text(encoding='utf8'))
    sr,data=wavfile.read(out/m['wav']);assert sr==SR and len(data)==round(SR*p['duracion'])
    y=data.astype(np.float32)/2147483648;del data;gc.collect();assert np.isfinite(y).all()
    ci,cj=[round(t*SR) for t in p['centro']];center=y[ci:cj];zero=spans(np.max(abs(center),axis=1)<1e-7,SR)
    longest=max((b-a for a,b in zero),default=0)
    cutchecks=[]
    for c in p['cortes_buses']:
        a,b=round(c['t']*SR),round(c['fin']*SR);peak=float(np.max(abs(y[a:b]))) if b>a else 0
        assert peak==0,(c,peak);cutchecks.append({'t':c['t'],'fin':c['fin'],'pico_pcm':peak})
    guitar=json.loads((out/'guitarra-estados-v10.json').read_text(encoding='utf8'));string=json.loads((out/'cuerda-estados-v10.json').read_text(encoding='utf8'))
    voice=np.zeros((60*SR,2),np.float32);band=np.zeros_like(voice)
    for part in p['partes']:
        x=read(out,'mezclada-v10-'+part['id'])[:60*SR]
        if part['id'] in ['voz','duo']:voice+=x
        else:band+=x
        del x;gc.collect()
    v=np.array([np.mean(voice[i:i+2400].astype(float)**2) for i in range(0,len(voice),2400)])
    r=np.array([np.mean(band[i:i+2400].astype(float)**2) for i in range(0,len(band),2400)])
    selected=v>v.max()*.001;ratio=10*np.log10((v[selected].sum()+1e-20)/(r[selected].sum()+1e-20))
    checks={'sr':sr,'frames':len(y),'duracion':len(y)/sr,'finito':True,'sin_clipping_entero':bool(np.max(abs(y))<1),
      'pico_muestra_dbfs':db(float(np.max(abs(y)))),'silencio_centro_mayor_s':longest,
      'voz_duo_contra_instrumentos_primera_min_activos_db':float(ratio),'medida_no_equivale_a_protagonismo':True,
      'captacion_guitarra_error_z':guitar['error_z_canonico'],'captacion_guitarra_error_fase':guitar['error_fase_canonica'],
      'captacion_cuerda_error':string['error_canonico'],'cortes':cutchecks,'audicion_propia':False,
      'limite':'Sondas de señal y estados; no son un juicio de gusto ni una cuota vocal acordada.'}
    assert longest<2.1,longest
    dump(out/'verificacion-audio-v10.json',checks)
    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True)
    for x,col,label in [(voice,'#d3a380','Voz e interlocutor'),(band,'#85b5aa','Instrumentos y cuerpos articulados')]:
        n=len(x)//2400;env=np.sqrt(np.mean(x[:n*2400].reshape(n,2400,2).astype(float)**2,axis=(1,2)))
        axes[0].plot(np.arange(n)*.05,20*np.log10(env+1e-9),color=col,label=label,lw=.9)
    axes[0].set_ylim(-65,-8);axes[0].legend();axes[0].set_ylabel('dBFS RMS / 50 ms');axes[0].set_title('Primera vuelta · señales de la mezcla nueva',loc='left')
    for k,name in enumerate(['guitarra','contrabajo','krar','clarinete','voz','duo','corocuerda']):
        for e in p['eventos'][name]:
            for a,b in e['salidas']:
                if a<60:axes[1].plot([a,min(60,b)],[k,k],lw=4)
    axes[1].set_yticks(range(7),['guitarra','contrabajo','krar','clarinete','voz','duo','cuerda articulada']);axes[1].set_xlim(0,60);axes[1].set_xlabel('Segundos')
    plot(out,5,'exposicion-real',fig);del voice,band;gc.collect()
    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True)
    axes[0].plot(p['centro'][0]+np.arange(0,len(center),48)/SR,center[::48].mean(1),lw=.6,color='#d3a380');axes[0].set_ylabel('Amplitud del WAV')
    for k,name in enumerate(['guitarra','cuerda','junco1','junco2','junco3','junco4','waterphone','campana']):
        for e in p['eventos'][name]:
            for a,b in e['salidas']:
                if a>=p['centro'][0] and b<=p['centro'][1]:axes[1].plot([a,b],[k,k],lw=4)
    axes[0].set_title('Centro · salida tenue y ventanas independientes',loc='left');axes[1].set_yticks(range(8),['guitarra','cuerda','junco 1','junco 2','junco 3','junco 4','waterphone','campana']);axes[1].set_xlabel('Segundos');plot(out,6,'centro-real',fig)
    fig,axes=plt.subplots(2,1,figsize=(12,7),sharex=True,gridspec_kw={'height_ratios':[1,3]})
    block=2400;nn=len(y)//block;peak=np.max(abs(y[:nn*block].reshape(nn,block,2)),axis=(1,2));axes[0].plot(np.arange(nn)*.05,peak,lw=.7,color='#d3a380');axes[0].set_ylabel('Pico / 50 ms')
    f,t,z=spectrogram(y.mean(1),SR,nperseg=2048,noverlap=1024);stride=math.ceil(len(t)/1400);cols=len(t)//stride
    z=z[:,:cols*stride].reshape(len(f),cols,stride).mean(2);t=t[:cols*stride].reshape(cols,stride).mean(1)
    axes[1].pcolormesh(t,f,10*np.log10(z+1e-16),shading='auto',cmap='magma',vmin=-100,vmax=-35);axes[1].set_yscale('log');axes[1].set_ylim(40,18000);axes[1].set_xlabel('Segundos');axes[1].set_ylabel('Hz')
    for s in p['secciones']:
        for ax in axes:ax.axvline(s['t'],lw=.6,alpha=.35,color='white')
        axes[0].text((s['t']+s['fin'])/2,.94,s['id'],transform=axes[0].get_xaxis_transform(),ha='center',va='top')
    axes[0].set_title('Llevemos unas luciérnagas al lago · v10.1 · 4:18.667',loc='left');result=plot(out,7,'resultado-sonoro',fig)
    shutil.copyfile(result,out/f'luciernagas-resultado-audio-s1-{tag}.png')
    image=Image.open(result).convert('RGB');image.resize((1200,630)).save(out/'og.png')
    frames=[]
    for file in sorted((out/'proceso').glob('*.png')):
        im=Image.open(file).convert('RGB');im.thumbnail((1200,700));canvas=Image.new('RGB',(1200,700),'#10201e');canvas.paste(im,((1200-im.width)//2,(700-im.height)//2));frames.append(canvas.quantize(colors=128))
    gif=out/f'luciernagas-proceso-audio-s1-{tag}.gif';assert not gif.exists();frames[0].save(gif,save_all=True,append_images=frames[1:],duration=1100,loop=0,optimize=True)
    with Image.open(gif) as im:duration=sum((im.seek(i),im.info.get('duration',0))[1] for i in range(im.n_frames));count=im.n_frames
    assert duration<=10000 and gif.stat().st_size<=15*1024*1024
    (out/'proceso/README.md').write_text('# Proceso real de la realización\n\n01: recepción de partitura y fijación de fuentes, antes de sintetizar. 02: final de guitarra/cuerda/juncos y cotejo de captaciones con estados canónicos. 03: voces PSOLA y vocoders terminados. 04: mezcla de 36 partes terminada, antes del máster. 05–07: medidas y gráficos del WAV/mezcla efectivamente generados. Las primeras cuatro láminas registran hitos realizados, no fotogramas internos de síntesis; el GIF reúne esos registros y las vistas de señal.\n\nTerreno 1 / composición 2026102201. Nombre descriptivo y SHA de ejecución en todas las nuevas imágenes; no se sobrescriben entregas anteriores.\n',encoding='utf8')
    text=f'''# Llevemos unas luciérnagas al lago · realización 10.1

22 de octubre de 2026. Realización completa de la partitura 10.1 después del cotejo con **Lo que el agua dibuja** y de la precisión de Canek: complejidad ante todo. Canek autorizó escucharla. No se pega ningún tramo de un audio anterior.

- Canción completa: [{m['aac']}]({m['aac']}); [WAV 24 bits / 48 kHz]({m['wav']}). Duración 4:18.667.
- 36 partes / 1714 eventos. Sabina PSOLA, instrumentos originales de biblioteca y motores propios; guitarra, cuerda y juncos adaptados a los estados canónicos vigentes.
- Guitarra: captación completa a 105.4 s, error modal máximo {guitar['error_z_canonico']:.3g}; cuerda: recepción que asigna el estado completo y captación a 116.2 s, error {string['error_canonico']:.3g}.
- Cuatro ventanas propias, fase analítica, cruces progresivos de 90 ms, amortiguación diferente y 24 transportes recalculados. Se realiza la coda de la nueva llegada.
- Ganancias centrales fijas por campo, una sola para los cuatro juncos; sin nivelación por destello ni AGC. Voz principal −6 dB relativos y guitarra 0 dB según partitura. La medida de nivel no certifica el protagonismo percibido.
- WAV final: {m['final']['input_i']} LUFS-I, {m['final']['input_tp']} dBTP. Ganancia estática de máster {m['ganancia_estatica_db']:.2f} dB, limitador sobremuestreado ×4; conserva contrastes y cortes posteriores.
- Mayor tramo central bajo −140 dBFS aproximadamente: {longest:.3f} s. Todos los cortes generales dieron cero en el PCM final. No equivale a garantizar audibilidad a cualquier volumen.
- No hubo audición propia: las comprobaciones son de señal, rutas y estados. La valoración musical corresponde a la escucha. No se exige reconocer cada relación causal ni se simplifica para explicarla.
- [Resultado PNG](luciernagas-resultado-audio-s1-{tag}.png), [GIF real de proceso]({gif.name}): {duration/1000:.1f} s, {count} cuadros, {gif.stat().st_size} bytes. [Orden de etapas](proceso/README.md).

Se preservan partitura, grabaciones y borradores anteriores. Las fuentes de ejecución están en `fuentes/`; `partitura.json` copia exactamente la edición vigente. Los motores de biblioteca se fijaron en la entrega de partitura v8 y siguen siendo las fuentes nativas, con control vigente 10.1.
'''
    with (out/'README.md').open('x',encoding='utf8') as f:f.write(text)
    for file in ['audio_v10.py','nativos_v10.py','producir_v10.py','entregar_audio_v10.py','interpretar.cjs','motores_audio.py','estados.cjs']:
        target=out/'fuentes'/file
        if not target.exists():shutil.copyfile(B/file,target)
        elif target.read_bytes()!=(B/file).read_bytes():shutil.copyfile(B/file,out/'fuentes'/('final-'+file))
    files={str(file.relative_to(out)).replace('\\','/'):sha(file.read_bytes()) for file in out.rglob('*') if file.is_file() and 'render' not in file.relative_to(out).parts}
    fixed=B/'luciernagas-reescritura-s1-29d4afe5aad2/realizacion';vendor=B.parent/'inferencia/vendor/difonos'
    deps=[fixed/'motores.py',fixed/'campana-motor.mjs',*[fixed/'biblioteca/motores'/name for name in ['web.js','objetos.js','meleeviewer.js','rejilla.py']],*list((fixed/'biblioteca/fichas').glob('*.json')),
      vendor/'runtime/g2p.js',vendor/'runtime/difonos.js',vendor/'bancos/sabina-1-b44e7fab5cee/manifiesto.json',vendor/'bancos/sabina-1-b44e7fab5cee/banco.flac',B.parent/'cuento-en-siete/sintes.py']
    dump(out/'receta-huellas.json',{'inicio':json.loads((out/'inicio.json').read_text(encoding='utf8')),'archivos_sha256':files,'dependencias_fijadas_sha256':{str(f):sha(f.read_bytes()) for f in deps},'gif_duracion_ms':duration,'gif_bytes':gif.stat().st_size,'capturas_proceso':count})
    (B/'AUDIO-V10-ACTUAL.txt').write_text(out.name,encoding='utf8')
    print(json.dumps(checks,ensure_ascii=False),flush=True);print('CERRADO',out,flush=True)
if __name__=='__main__':finish()
