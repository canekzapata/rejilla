"""QA del archivo entregado: duración, picos, final, vacío y regreso."""
from audio_comun import *
from scipy.io import wavfile

def main():
    out,cfg,P,work=contexto();E=leer(out/'audio-entrega.json');M=leer(out/'mezcla-medidas.json');F=leer(out/'fuentes-verificadas.json');path=out/E['master']
    p=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,text=True,check=True);meta=json.loads(p.stdout);s=meta['streams'][0]
    assert int(s['sample_rate'])==48000 and int(s['channels'])==2 and s['codec_name']=='pcm_s24le'
    assert abs(float(meta['format']['duration'])-246)<.001
    sr,z=wavfile.read(path);y=z.astype(np.float32)/2**31;assert np.isfinite(y).all();peak=float(abs(y).max());assert peak<1
    tail=float(np.sqrt(np.mean(y[-round(sr*.05):]**2)));assert tail<1e-6
    quiet={}
    for a,b in [(180.1,180.65),(183.8,184.3),(185.95,187.15),(191,192.4),(194,196)]:
        rms=float(np.sqrt(np.mean(y[round(a*sr):round(b*sr)]**2)));quiet[f'{a}-{b}']=rms;assert rms<1e-5,(a,b,rms)
    assert M['averia']['pico_bus_metrico']==0 and M['averia']['rms_bus_libre']>1e-4
    assert float(M['aac']['input_tp'])<-.8 and -17<float(M['aac']['input_i'])<-13
    assert M['rejilla']['SNR_sin_DC_Nyquist_dB']>50
    assert F['signos_negativos_aplicados']>0 and F['cargas_FEM_distintas']>3
    assert len(M['canales'])==30
    # El ataque que falta es el de membrana. La base sí vuelve al inicio.
    first=min(e['t'] for c in ['membrana-din','membrana-ta','membrana-thom'] for e in P['eventos'][c] if e['t']>=200)
    assert first>=200.6
    corr=float(np.sum(y[:,0]*y[:,1])/np.sqrt(np.sum(y[:,0]**2)*np.sum(y[:,1]**2)));mono=float(np.sqrt(np.mean(y.mean(1)**2))/(np.sqrt(np.mean(y**2))+1e-12));assert corr>-.1 and mono>.5
    run=cfg;first_png=next((out/'proceso').glob('01-*.png'));h=hashlib.sha256(first_png.read_bytes()+cfg['version'].encode()+cfg['nonce'].encode()+(out/'fuentes-fijadas/audio_comun.py').read_bytes()).hexdigest();assert h==cfg['hash']
    receipt={'WAV':{'archivo':E['master'],'sha256':sha(path),'sr':sr,'canales':2,'bits':24,'segundos':len(y)/sr,'pico_muestra':peak,'DC':float(np.mean(y)),'rms_ultimos_50ms':tail},'AAC':{'archivo':E['escucha'],'sha256':sha(out/E['escucha']),'LUFS_I':float(M['aac']['input_i']),'true_peak_dBTP':float(M['aac']['input_tp']),'LRA_LU':float(M['aac']['input_lra'])},'averia_bus_metrico_cero':True,'ventanas_de_silencio_rms':quiet,'primer_ataque_membrana_regreso_s':first,'correlacion_estereo':corr,'relacion_rms_mono_estereo':mono,'rejilla_SNR_dB':M['rejilla']['SNR_sin_DC_Nyquist_dB'],'treinta_partes_activas':True,'identificador_reproducible':True,'audicion':'No hubo audición propia; comprobaciones de señal y estructura, no evaluación perceptual de música o dicción.','visor_y_video':'no producidos'}
    jsave(out/'audio-verificado.json',receipt);print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':main()
