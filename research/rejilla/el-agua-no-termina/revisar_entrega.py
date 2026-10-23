from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json,hashlib
p=Path(__file__).resolve().parent/'el-agua-no-termina-s20261021-68f9b50891ae';tag='s20261021-68f9b50891ae'
g=Image.open(p/f'el-agua-proceso-{tag}.gif');sheet=Image.new('RGB',(1200,900),'#091519');draw=ImageDraw.Draw(sheet);duration=0
for i in range(g.n_frames):
    g.seek(i);duration+=g.info['duration'];im=ImageOps.contain(g.convert('RGB'),(395,275));sheet.paste(im,((i%3)*400,(i//3)*300));draw.text(((i%3)*400+8,(i//3)*300+278),str(i+1),fill='white')
with (p/f'revision-proceso-{tag}.png').open('xb') as f:sheet.save(f,format='PNG')
files=sorted((p/'proceso').glob('*.png'));print('PNGs',len(files));print('OG',Image.open(p/'og.png').size);print('GIF',g.n_frames,'frames',duration,'ms',g.size,(p/f'el-agua-proceso-{tag}.gif').stat().st_size,'bytes')
manifest=json.loads((p/f'manifiesto-{tag}.json').read_text())
for name,expected in manifest['files'].items():assert hashlib.sha256((p/name).read_bytes()).hexdigest()==expected,name
print('Huellas del manifiesto verificadas')
