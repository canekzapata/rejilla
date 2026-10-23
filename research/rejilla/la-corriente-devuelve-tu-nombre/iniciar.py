"""Imagen inicial real, identidad exclusiva y protocolo de eco."""
from comun import *
from PIL import Image,ImageDraw
D=leer(BASE/'procedencia.json');initial=json.loads(subprocess.run(['node','eco.mjs','--inicial'],cwd=BASE,capture_output=True,text=True,check=True).stdout)
K=np.array(initial['K']);u=np.array(initial['u']).reshape(-1,3,2);im=Image.new('RGB',(1200,630),'#090b19');d=ImageDraw.Draw(im)
for x in np.linspace(0,2*np.pi,45):
 for y in np.linspace(0,2*np.pi,25):
  phase=K[:,:3]@np.array([x,y,.4]);v=np.sum(u[:,:,0]*np.cos(phase)[:,None]-u[:,:,1]*np.sin(phase)[:,None],axis=0);a=(35+x/6.283*1130,35+y/6.283*560);b=(a[0]+v[0]*38,a[1]+v[1]*38);d.line([a,b],fill='#9a96ff',width=2)
b=io.BytesIO();im.save(b,format='PNG');nonce=os.urandom(24).hex();h=hashlib.sha256(b.getvalue()+VERSION.encode()+nonce.encode()+Path(__file__).read_bytes()+(BASE/'eco.mjs').read_bytes()).hexdigest();out=BASE/f'la-corriente-s{SEED}-{h[:12]}';out.mkdir(exist_ok=False);(out/'proceso').mkdir();(BASE/'render'/h[:12]).mkdir(parents=True,exist_ok=False)
guardar(out/'proceso'/f'01-impulso-inicial-s{SEED}-{h[:12]}.png',b.getvalue());jsave(out/'ejecucion.json',{'hash':h,'nonce':nonce,'version':VERSION,'semilla':SEED,'imagen_sha256':hashlib.sha256(b.getvalue()).hexdigest(),'inicial':initial,'fecha_local':'2026-10-21'})
(BASE/'ULTIMA.txt').write_text(out.name,encoding='utf-8');print(out,flush=True)
subprocess.run(['node','eco.mjs',str(out)],cwd=BASE,check=True)
