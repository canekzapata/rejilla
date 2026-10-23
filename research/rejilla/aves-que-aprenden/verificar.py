from pathlib import Path
import sys,hashlib,json,subprocess,shutil
import numpy as np
from PIL import Image,ImageOps
out=Path(sys.argv[1]).resolve();base=Path(__file__).parent
def fresh(p):
    if p.exists():raise FileExistsError(p)
    return p
for name in ['estudio.py','verificar.py']:
    shutil.copyfile(base/name,fresh(out/'fuentes'/name))
shutil.copyfile(base/'fuentes.cjs',fresh(out/'fuentes'/'fuentes-v02.cjs'))
src=next(out.glob('el-pajaro-aprende-*.png'))
im=ImageOps.contain(Image.open(src).convert('RGB'),(1200,630))
canvas=Image.new('RGB',(1200,630),'#f5f1e8');canvas.paste(im,((1200-im.width)//2,(630-im.height)//2));canvas.save(fresh(out/'og.png'))
gif=next(out.glob('*.gif')); frames=[];total=0
with Image.open(gif) as im:
    assert im.info['loop']==0
    for i in range(im.n_frames):
        im.seek(i);total+=im.info['duration'];frames.append(ImageOps.contain(im.convert('RGB'),(720,400)))
assert total<=10000 and gif.stat().st_size<=15*1024*1024
contact=Image.new('RGB',(720,sum(f.height for f in frames)),'#f5f1e8');y=0
for f in frames:contact.paste(f,(0,y));y+=f.height
contact.save(fresh(base/'revision-gif-148344606fb4.png'))
checks={}
for p in out.glob('*.m4a'):
    pcm=subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','f32le','-ac','1','-'],capture_output=True,check=True).stdout
    x=np.frombuffer(pcm,dtype='<f4');assert np.isfinite(x).all() and len(x)>0
    checks[p.name]={'pico_decodificado':float(np.max(np.abs(x))),'finito':True}
inventory={'gif':{'ms':total,'bytes':gif.stat().st_size,'frames':len(frames)},'aac':checks,
 'sha256':{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}}
with fresh(out/'integridad-148344606fb4.json').open('x',encoding='utf-8') as f:json.dump(inventory,f,ensure_ascii=False,indent=2)
print(json.dumps({'gif':inventory['gif'],'pico_aac_maximo':max(x['pico_decodificado'] for x in checks.values()),'aac_verificados':len(checks)}))
