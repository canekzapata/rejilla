from audio_comun import *
from laminas import *

def main():
    out,cfg,P,work=contexto();R=work/'fuentes';N=round(cfg['duracion']*SR);tag=out.name.split('-')[-1];info={}
    f,ax=figura('Las treinta partes ya son señales','Captura de fuentes reales antes de procesar espacios, clima y mezcla')
    for j,c in enumerate(P['eventos']):
        y=rawread(R,c,N);assert np.isfinite(y).all();ar=activo(y);assert ar>1e-9,(c,'muda');q=y[:N//1024*1024].reshape(-1,1024,2);v=np.sqrt(np.mean(q*q,axis=(1,2)));ax[0].plot(np.arange(len(v))*1024/SR,v/(v.max()+1e-12)*.7+j,lw=.55)
        info[c]={'rms_activo':ar,'pico':float(abs(y).max()),'muestras':len(y),'canales_guardados':(R/(c+'.f32')).stat().st_size//(N*4),'sha256':sha(R/(c+'.f32'))}
    ax[0].set_yticks(range(30),list(P['eventos']),fontsize=6);ax[0].set_xlabel('segundos de las fuentes sin mezcla');ax[0].axvspan(180,200,alpha=.12,color='#b69b72');salva(f,out/'proceso'/f'02-treinta-fuentes-reales-s22-{tag}.png')
    met=leer(out/'instrumentos-interpretados.json');signs=[s for es in met['laser'].values() for e in es for s in e['signos']];assert -1 in signs
    cargas={m['carga_calculada'] for c in ['membrana-din','membrana-ta','membrana-thom'] for m in met[c]};assert len(cargas)>3
    info={'partes':info,'muestras_por_canal':N,'duracion_s':N/SR,'signos_negativos_aplicados':signs.count(-1),'cargas_FEM_distintas':len(cargas),'clima_y_corte':'pendientes en mezcla; las fuentes de biblioteca conservan sus colas originales','nota':'verificación numérica; no audición propia'}
    jsave(out/'fuentes-verificadas.json',info);print('30 fuentes finitas y activas; signos aplicados; FEM con',len(cargas),'cargas distintas')

if __name__=='__main__':main()
