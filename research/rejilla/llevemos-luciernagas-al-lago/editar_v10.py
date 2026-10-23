"""Edición coherente de v10.1: salidas completas, PDF, XML, CSV y capturas."""
from pathlib import Path
import json,math,io,csv,xml.etree.ElementTree as ET
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A3,A2,landscape
from PIL import Image,ImageDraw,ImageFont
import fitz
from resolver_v10 import cargar,ventanas

OUT,P=cargar();TAG=OUT.name.split('-')[-1];Q=P['negra_s'];DIV=24000
def put(name,data):
    with (OUT/name).open('xb') as f:f.write(data)
def pitch(m):
    n=round(m);c=(m-n)*100;return ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B'][n%12]+str(n//12-1)+(f'({c:+.1f}c)' if abs(c)>.05 else '')
def clock(t):return f'{int(t)//60}:{t%60:06.3f}'
def midi_at(e,t):return e['midi']+(e.get('midi_fin',e['midi'])-e['midi'])*np.clip((t-e['t'])/e['dur'],0,1)
ROOT=ET.Element('score-partwise',version='4.0');ET.SubElement(ET.SubElement(ROOT,'work'),'work-title').text=P['titulo']+' / partitura v10.1'
ident=ET.SubElement(ROOT,'identification');ET.SubElement(ident,'creator',type='composer').text='Canek Zapata';pl=ET.SubElement(ROOT,'part-list')
xmlcounts={};maxerr=0.;totalwritten=0
for tr in P['partes']:
    pid='P'+str(tr['numero']);sp=ET.SubElement(pl,'score-part',id=pid);ET.SubElement(sp,'part-name').text=tr['nombre'];ET.SubElement(sp,'part-abbreviation').text=tr['id']
    part=ET.SubElement(ROOT,'part',id=pid);spans=[];laneends=[]
    for e in P['eventos'][tr['id']]:
        for wi,(a,b) in enumerate(ventanas(e,P['cortes_buses'])):
            lane=next((k for k,end in enumerate(laneends) if end<=a+1e-9),len(laneends))
            if lane==len(laneends):laneends.append(b)
            else:laneends[lane]=b
            spans.append((e,a,b,lane,wi))
    count=0
    for me in P['medidas_editoriales']:
        a,b=me['t'],me['fin'];total=round((b-a)/Q*DIV);mm=ET.SubElement(part,'measure',number=str(me['n']));at=ET.SubElement(mm,'attributes')
        ET.SubElement(at,'divisions').text=str(DIV);tm=ET.SubElement(at,'time')
        if me['free']:ET.SubElement(tm,'senza-misura')
        else:ET.SubElement(tm,'beats').text='4';ET.SubElement(tm,'beat-type').text='4'
        if me['n']==1:
            clef=ET.SubElement(at,'clef');ET.SubElement(clef,'sign').text='percussion' if tr['id'] in ['bombo','caja','hat','tom','aro','ride'] else 'G';ET.SubElement(clef,'line').text='2'
        if me['n']==1 or me['free']:
            dr=ET.SubElement(mm,'direction');ET.SubElement(ET.SubElement(dr,'direction-type'),'words').text=clock(a)+(' / segundos sin pulso' if me['free'] else ' / negra=144')
            if me['n']==1:ET.SubElement(dr,'sound',tempo='144')
        hits=[z for z in spans if z[1]<b-1e-9 and z[2]>a+1e-9];lanes=sorted({z[3] for z in hits}) or [0]
        for vi,lane in enumerate(lanes):
            if vi:ET.SubElement(ET.SubElement(mm,'backup'),'duration').text=str(total)
            cur=0
            def rest(d):
                if d>0:
                    ne=ET.SubElement(mm,'note');ET.SubElement(ne,'rest');ET.SubElement(ne,'duration').text=str(d);ET.SubElement(ne,'voice').text=str(lane+1)
            for e,u,v,_,wi in sorted([z for z in hits if z[3]==lane],key=lambda z:z[1]):
                actual=max(a,u);aa=max(cur,round((actual-a)/Q*DIV));bb=min(total,round((min(b,v)-a)/Q*DIV))
                if bb<=aa:continue
                maxerr=max(maxerr,abs(aa*Q/DIV+a-actual));rest(aa-cur);ne=ET.SubElement(mm,'note',id=f'{e["id"]}_w{wi}_m{me["n"]}')
                m=float(midi_at(e,actual));n=round(m)
                if e.get('altura_asignable',True):
                    pp=ET.SubElement(ne,'pitch');st,al=[('C',0),('C',1),('D',0),('E',-1),('E',0),('F',0),('F',1),('G',0),('A',-1),('A',0),('B',-1),('B',0)][n%12]
                    ET.SubElement(pp,'step').text=st
                    if abs(al+m-n)>1e-12:ET.SubElement(pp,'alter').text=f'{al+m-n:.10f}'
                    ET.SubElement(pp,'octave').text=str(n//12-1)
                else:
                    pp=ET.SubElement(ne,'unpitched');ET.SubElement(pp,'display-step').text='C';ET.SubElement(pp,'display-octave').text='5'
                ET.SubElement(ne,'duration').text=str(bb-aa);ET.SubElement(ne,'voice').text=str(lane+1)
                gliss=abs(e.get('midi_fin',e['midi'])-e['midi'])>1e-8
                if not gliss:
                    if u<a-1e-8:ET.SubElement(ne,'tie',type='stop')
                    if v>b+1e-8:ET.SubElement(ne,'tie',type='start')
                nts=ET.SubElement(ne,'notations');tech=ET.SubElement(nts,'technical')
                annotation=e['articulacion']+(f'; gliss hasta {pitch(midi_at(e,min(b,v)))}' if gliss else '')
                if tr['id']=='guitarra':
                    gp=e['parametros_motor'];annotation+=f'; caja {gp["caja"]}; nodo {gp["nodo"]}; parcial {gp["parcial"]}'
                ET.SubElement(tech,'other-technical').text=annotation
                if e.get('texto') and abs(actual-e['t'])<1e-7:ET.SubElement(ET.SubElement(ne,'lyric'),'text').text=e['texto']
                cur=bb;count+=1
            rest(total-cur)
    xmlcounts[tr['id']]=count;totalwritten+=count
put(f'luciernagas-partitura-v10.1-s1-{TAG}.musicxml',ET.tostring(ROOT,encoding='utf-8',xml_declaration=True))
buf=io.StringIO(newline='');w=csv.writer(buf);w.writerow(['parte','id','t_s','dur_s','midi','midi_fin','hz','vel','pan','gesto','texto','ancestro','salidas_resueltas','parametros_completos'])
for tr in P['partes']:
    for e in P['eventos'][tr['id']]:w.writerow([tr['id'],e['id'],e['t'],e['dur'],e['midi'],e.get('midi_fin',''),e['hz'],e['vel'],e['pan'],e['articulacion'],e.get('texto',''),e.get('ancestro'),json.dumps(ventanas(e,P['cortes_buses'])),json.dumps(e,ensure_ascii=False)])
put(f'luciernagas-eventos-v10.1-s1-{TAG}.csv',buf.getvalue().encode('utf-8-sig'))
pdfmetrics.registerFont(TTFont('A','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('AB','C:/Windows/Fonts/arialbd.ttf'))
PDF=OUT/f'luciernagas-partitura-v10.1-s1-{TAG}.pdf';assert not PDF.exists();W,H=landscape(A3);c=canvas.Canvas(str(PDF),pagesize=(W,H));c.setTitle(P['titulo']+' / partitura v10.1');c.setAuthor('Canek Zapata');titles=[]
def text(x,y,s,size=11,b=False,col='#172b29'):
    c.setFillColor(col);c.setFont('AB' if b else 'A',size);c.drawString(x,y,str(s))
def line(x,y,xx,yy,col='#a7b7ae',lw=.5):c.setStrokeColor(col);c.setLineWidth(lw);c.line(x,y,xx,yy)
def page(title,subtitle='',large=False):
    global W,H
    if titles:c.showPage()
    W,H=landscape(A2 if large else A3);c.setPageSize((W,H));c.setFillColor('#f5f2e7');c.rect(0,0,W,H,fill=1,stroke=0)
    titles.append(title);text(40,H-45,title,24,True);text(40,H-72,subtitle,11);text(40,25,f'Canek Zapata / Luciérnagas v10.1 / {len(titles)} / semilla 1 / {TAG}',9)
def para(s,y,size=12):
    current=''
    for word in s.split():
        candidate=(current+' '+word).strip()
        if pdfmetrics.stringWidth(candidate,'A',size)>W-90:text(40,y,current,size);y-=size*1.45;current=word
        else:current=candidate
    if current:text(40,y,current,size);y-=size*1.45
    return y
page('Llevemos unas luciérnagas al lago','Proto punk folk / partitura completa revisada / 4:18.667 / 36 partes')
y=para('La guitarra presenta una pregunta, atraviesa nueve episodios y hace que grave, borde y contrapunto recojan sus cesuras. El roce encuentra resistencia; un estado pasa a cuerda, cuatro juncos lo transforman y su llegada cambia el regreso.',H-125,15)-25
for sec in P['secciones']:
    text(40,y,clock(sec['t'])+' - '+clock(sec['fin']),12,True);text(245,y,sec['id']+' / '+sec['nombre'],12);y-=29
y=para('Edición proporcional cromática de todas las salidas. Cada parte indica su escala MIDI por ventana. MusicXML incluye las 36 partes, silencios y alteraciones fraccionarias; el JSON conserva estados, fases, curvas y rotaciones que exceden la notación ordinaria.',y-25,12)
para('No hay audio nuevo en esta entrega. Los niveles son decisiones de interpretación pendientes de escucha. El pasaje favorable cercano a 2:40 conserva su identidad de diálogo, con una fuente central recalculada; no se reutiliza el PCM anterior.',y-15,12)
page('La guitarra conduce; el conjunto responde','Episodios nuevos / alturas, duraciones y funciones localizables')
lookup={e['id']:e for es in P['eventos'].values() for e in es};y=H-120
for ep in P['desarrollo_v10']:
    text(40,y,f'{clock(ep["inicio"])} - {clock(ep["fin"])} / caja {ep["caja"]} / {ep["episodio"]}',13,True)
    es=[lookup[i] for i in ep['ids']];text(50,y-21,' / '.join(pitch(e['midi'])+f' {e["dur"]:.3f}s' for e in es),10)
    text(50,y-38,'Final de frase: grave elige llegadas; krar/clarinete responde; borde y tom recogen cesuras.',9);y-=66
page('Pantano: cuatro voces, cuatro recorridos','1:33.333 - 2:33.333 / sin pulso ni voz humana / escuchar presión, retirada y recepción')
x0,x1=190,W-55;top=H-155
for k,windows in enumerate(P['centro_v10']['ventanas_por_voz']):
    yy=top-k*62;text(40,yy,'Junco '+str(k+1),13,True)
    for a,b in windows:line(x0+(x1-x0)*(a-93.3333)/60,yy,x0+(x1-x0)*(b-93.3333)/60,yy,'#935436',7)
for sec in P['centro_v10']['segmentos']:
    x=x0+(x1-x0)*(sec['t']-93.3333)/60;line(x,top+22,x,top-214);text(x,top+35,clock(sec['t']),8)
y=top-275
for s in P['centro_v10']['segmentos']:
    if s.get('cruce'):text(40,y,f'{clock(s["fin"])} / cruce {s["cruce"]["par"]} / {s["cruce"]["angulo_rad"]:+.2f} rad / 90 ms / norma conservada en el controlador',11);y-=25
packet=P['centro_v10']['paquete'];y=para(f'La recepción se calcula desde la guitarra completa a 1:45.400. La cuerda recibe a 1:46.200; el junco, a 1:56.200. La espera aprendida es {packet["espera_aprendida_s"]:.6f} s. La masa de llegada alimenta los 24 planes posteriores: no es una captación paralela desconectada.',y-18,12)
para('Drive e impulsos del contacto se separan; la integración se parte en los ataques y deslizamientos. Las rotaciones son de envolventes complejas, no una conservación de energía acústica en julios. No hay AGC dependiente de RMS en el centro.',y-12,12)
page('Texto, interlocutores y retorno','La raíz y los tenis vuelven a tener voz; el canto principal cede episodios completos')
y=H-119
for l in P['letra']:
    text(40,y,clock(l['t']),10,True);text(135,y,l['capa'],9);text(245,y,l['texto'],11)
    if l.get('espera_heredada_s',0):text(245,y-15,f'Espera entre palabras: {l["espera_heredada_s"]:.6f} s',9,col='#935436');y-=14
    y-=26
# Partitura completa: las ventanas, no sólo los eventos internos, deciden los trazos.
for sec in P['secciones']:
    a=sec['t'];span=10 if sec['modo'].startswith('senza') else 32*Q
    while a<sec['fin']-1e-7:
        b=min(sec['fin'],a+span);page(sec['id']+' / '+clock(a)+' - '+clock(b),sec['accion'],True)
        x0,x1,top,row=300,W-42,H-130,27
        for cut in P['cortes_buses']:
            u,v=max(a,cut['t']),min(b,cut['fin'])
            if v>u:c.setFillColor('#d8dfd4');c.rect(x0+(x1-x0)*(u-a)/(b-a),top-36*row,(x1-x0)*(v-u)/(b-a),36*row+22,fill=1,stroke=0)
        for t in np.arange(math.ceil(a),b+1e-8,1):
            xx=x0+(x1-x0)*(t-a)/(b-a);line(xx,top+20,xx,top-36*row,lw=.25);text(xx+2,top+30,f'{t:.0f}s',7)
        for k,tr in enumerate(P['partes']):
            yy=top-k*row;hits=[(e,max(a,u),min(b,v)) for e in P['eventos'][tr['id']] for u,v in ventanas(e,P['cortes_buses']) if u<b and v>a]
            values=[float(midi_at(e,t)) for e,u,v in hits for t in [u,v]];lo=math.floor(min(values))-1 if values else 59;hi=math.ceil(max(values))+1 if values else 61
            text(30,yy+3,f'{tr["numero"]:02} {tr["nombre"][:35]}',8,True);text(30,yy-9,f'{tr["id"]} / MIDI {lo}-{hi}',7);line(x0,yy,x1,yy,lw=.25)
            for e,u,v in hits:
                xa=x0+(x1-x0)*(u-a)/(b-a);xb=x0+(x1-x0)*(v-a)/(b-a);ya=yy-8+16*(midi_at(e,u)-lo)/(hi-lo);yb=yy-8+16*(midi_at(e,v)-lo)/(hi-lo)
                line(xa,ya,xb,yb,'#935436' if e.get('revision')=='v10' else '#254940',1.3)
                if abs(u-e['t'])<1e-7:
                    c.setFillColor('#935436');c.circle(xa,ya,1.7,fill=1,stroke=0)
                    label=e.get('texto') or (pitch(e['midi']) if tr['id']=='guitarra' else '')
                    if label:text(min(xa+3,x1-pdfmetrics.stringWidth(label,'A',6.5)),ya+6,label,6.5)
        text(40,61,'Punto: ataque. Línea: salida. Pendiente: trayectoria en MIDI. Sombra: bus cerrado. Escala de cada parte indicada; no hay recorte de alturas.',9)
        text(40,46,'Los cruces de fase y la captación tienen controles adicionales en JSON. Reabrir salida no reexcita. Referencias históricas separadas de controles vigentes.',9);a=b
c.save()
qa=OUT/'proceso/pdf';qa.mkdir(exist_ok=False);doc=fitz.open(PDF);thumbs=[]
for i,pg in enumerate(doc):
    pix=pg.get_pixmap(matrix=fitz.Matrix(.55,.55),alpha=False);file=qa/f'pagina-{i+1:02}-s1-{TAG}.png'
    with file.open('xb') as f:f.write(pix.tobytes('png'))
    im=Image.open(file).convert('RGB');im.thumbnail((290,230));thumbs.append(im)
cols=5;sheet=Image.new('RGB',(cols*310,math.ceil(len(thumbs)/cols)*265),'#dde1d8');dr=ImageDraw.Draw(sheet)
for i,im in enumerate(thumbs):x=(i%cols)*310;y=(i//cols)*265;sheet.paste(im,(x+(310-im.width)//2,y+26));dr.text((x+7,y+7),str(i+1)+': '+titles[i][:30],fill='black')
bb=io.BytesIO();sheet.save(bb,format='PNG');put(f'proceso/05-edicion-completa-s1-{TAG}.png',bb.getvalue())
put(f'proceso/06-centro-editado-s1-{TAG}.png',doc[2].get_pixmap(matrix=fitz.Matrix(1.2,1.2),alpha=False).tobytes('png'))
put('datos/edicion-v10.1.json',json.dumps({'pdf':PDF.name,'paginas':len(doc),'titulos':titles,'divisiones':DIV,'error_temporal_XML_max_s':maxerr,'notas_XML':xmlcounts,'total_notas_XML':totalwritten},ensure_ascii=False,indent=1).encode('utf8'))
put('fuentes/editar_v10.py',Path(__file__).read_bytes());print(PDF,len(doc),'páginas; error XML',maxerr)
