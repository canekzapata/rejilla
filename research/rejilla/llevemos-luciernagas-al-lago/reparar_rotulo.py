"""Corrección de una etiqueta de la página 24; conserva el PDF anterior."""
from pathlib import Path
import json,fitz
ROOT=Path(__file__).resolve().parent;OUT=ROOT/(ROOT/'ULTIMA.txt').read_text().strip();TAG=OUT.name.split('-')[-1]
src=OUT/f'partitura-luciernagas-r5-s1-{TAG}.pdf';dest=OUT/f'partitura-luciernagas-r6-s1-{TAG}.pdf'
if dest.exists():raise FileExistsError(dest)
doc=fitz.open(src);page=doc[23];spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for l in b['lines'] for s in l['spans'] if 'presión apenas' in s['text']]
assert len(spans)==1
s=spans[0];rect=fitz.Rect(s['bbox']);page.add_redact_annot(rect,fill=(244/255,241/255,223/255));page.apply_redactions(images=0,graphics=0)
font=fitz.Font(fontfile='C:/Windows/Fonts/arial.ttf');label='presión apenas suficiente';x=min(s['origin'][0],page.rect.width-48-font.text_length(label,fontsize=s['size']))
page.insert_font(fontname='ArFix',fontfile='C:/Windows/Fonts/arial.ttf');page.insert_text((x,s['origin'][1]),label,fontname='ArFix',fontsize=s['size'],color=(138/255,60/255,36/255))
doc.save(dest,garbage=3,deflate=True);doc.close()
with (OUT/'datos/correccion-rotulo.json').open('x',encoding='utf8') as f:json.dump({'pagina':24,'cambio':'mover etiqueta dentro del margen; notas y duraciones intactas','origen':src.name,'vigente':dest.name},f,ensure_ascii=False,indent=1)
with (OUT/'fuentes/reparar_rotulo.py').open('xb') as f:f.write(Path(__file__).read_bytes())
qa=ROOT/'tmp'/('pdf-r6-'+TAG);qa.mkdir(parents=True,exist_ok=False);doc=fitz.open(dest)
for i in [1,4,23,27,33]:
 pix=doc[i].get_pixmap(matrix=fitz.Matrix(.9,.9),alpha=False);(qa/f'pagina-{i+1:02}.png').write_bytes(pix.tobytes('png'))
print(dest)
