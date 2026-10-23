"""Trabajos separados de producción; siempre reciben la carpeta nueva por entorno."""
import sys,os,subprocess
from audio_v10 import context,B,stage
out,p=context();env={**os.environ,'LUCI_AUDIO_OUT':str(out)}
def run(*args):subprocess.run(list(args),cwd=B,env=env,check=True)
job=sys.argv[1]
if job=='voz':run('node','interpretar.cjs','voz')
elif job=='aro':
    env['LUCI_V10_ARO']='1';run('node','interpretar.cjs','web','aro')
elif job=='campana':run(sys.executable,'motores_audio.py','campana')
elif job=='biblioteca':
    run('node','interpretar.cjs','web')
    run('node','interpretar.cjs','objetos')
    run(sys.executable,'motores_audio.py','modales')
    run('node','estados.cjs','organo')
    run(sys.executable,'motores_audio.py','arpa','terminal','androide','fotones','sala','boca')
    run(sys.executable,'motores_audio.py','campana')
elif job=='vocoders':
    run(sys.executable,'motores_audio.py','vocoders')
    stage(out,3,'Voces y portadoras nuevas',['Sabina PSOLA: solista, interlocutor y guías de coro','La cuerda articula su propia portadora','Los cuatro juncos alimentan el otro vocoder','Prosodia y respiraciones tomadas de la partitura vigente'])
else:raise ValueError(job)
