"""Conserva y termina la corrida cuya prueba de Rejilla detectó DC eliminado."""
from producir import *
out=HERE/'el-agua-no-termina-s20261021-68f9b50891ae';tag='s20261021-68f9b50891ae'
_,dry=wavfile.read(out/f'un-remolino-{tag}.wav');_,song=wavfile.read(out/f'el-agua-insiste-{tag}.wav')
meta=json.loads((out/f'impulso-y-estados-{tag}.json').read_text());smeta=json.loads((out/f'partitura-y-estados-{tag}.json').read_text())
identity=json.loads((out/f'identidad-{tag}.json').read_text())
engine=subprocess.check_output(['git','-C',str(HERE.parent),'show','21a2bee:el-agua-no-termina/motor.mjs'])
first=(out/'proceso'/f'01-modos-{tag}.png').read_bytes()
assert sha(first+VERSION.encode()+engine+identity['nonce'].encode())==identity['run_sha256']
write(out/f'motor-identidad-{tag}.mjs',engine);write(out/f'motor-entregado-{tag}.mjs',(HERE/'motor.mjs').read_bytes())
g=grid(out,dry[:SR*6],tag+'-sin-dc');dump(out/f'verificacion-rejilla-{tag}.json',g);print(g,flush=True)
f=plt.figure(figsize=(12,6.3));ax=f.add_axes([0,0,1,1]);xy,v=field(smeta['history'][70]['u'],N=100);speed=np.hypot(v[0],v[1]);ax.streamplot(xy,xy,v[0],v[1],color=speed,cmap='summer',density=2.5,linewidth=.5+2*speed/max(.01,speed.max()),arrowsize=.65);ax.set_aspect('equal',adjustable='datalim');ax.axis('off');cover=png(f);write(out/f'el-agua-campo-{tag}.png',cover)
for p in [out/'og.png',HERE/'og.png']:write(p,cover)
im=Image.open(io.BytesIO(cover)).resize((64,64));b=io.BytesIO();im.save(b,format='PNG')
for p in [out/'favicon.png',HERE/'favicon.png']:write(p,b.getvalue())
build(out,tag)
tests=json.loads((out/f'pruebas-{tag}.json').read_text())
dump(out/f'receta-{tag}.json',{'run_sha256':identity['run_sha256'],'seed':SEED,'version':VERSION,'tests':tests,'rejilla':g,'audios':{name:{'duration_s':len(y)/SR,'peak':float(abs(y).max()),'rms':float(np.sqrt(np.mean(y*y)))} for name,y in [('impulso',dry),('recorrido',song)]},'reanudacion':'La primera aserción comparó audio con DC contra imágenes sin DC. Se conserva la salida anterior y se mide también la señal representable, sin DC ni Nyquist. No se volvió a sintetizar la muestra.','fuentes':'El hash de ejecución incluye el motor inicial, cuya huella se comprobó. La entrega añade validación de rangos al mismo integrador y corrige el reparto visual de partículas; se conservan ambas fuentes.','source_sha256':{p.name:sha(p.read_bytes()) for p in [HERE/'motor.mjs',HERE/'agua.py',HERE/'interfaz.html']},'saturator_samples':{'impulso':meta['output_saturator_samples'],'recorrido':smeta['output_saturator_samples']}})
write(HERE/'abrir-agua.bat',('@echo off\r\nstart "" "%~dp0'+out.name+'\\el-agua-no-termina-'+tag+'.html"\r\n').encode('utf-8'))
print('DONE',flush=True)
