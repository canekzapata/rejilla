"""Edición de la escritura r4. Produce papel/datos y PNGs; jamás audio/video."""
from comun import *
from laminas import *
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import xml.etree.ElementTree as ET,csv
import fitz

def musicxml(out,P,tag):
    root=ET.Element('score-partwise',version='4.0');w=ET.SubElement(root,'work');ET.SubElement(w,'work-title').text=P['titulo']+' / revisión 4'
    ident=ET.SubElement(root,'identification');ET.SubElement(ident,'creator',type='composer').text='Canek Zapata';pl=ET.SubElement(root,'part-list');div=960
    sections={s['compas_inicio']-1:s['nombre'] for s in P['secciones']}
    for idx,(name,events) in enumerate(P['eventos'].items(),1):
        sp=ET.SubElement(pl,'score-part',id=f'P{idx}');ET.SubElement(sp,'part-name').text=name;part=ET.SubElement(root,'part',id=f'P{idx}');ends=[];lanes=[]
        for e in events:
            a=e['pulso'];b=a+e['dur_pulsos'];lane=next((j for j,z in enumerate(ends) if z<=a+1e-6),len(ends))
            if lane==len(ends):ends.append(b)
            else:ends[lane]=b
            lanes.append((e,lane))
        for bar in range(96):
            mm=ET.SubElement(part,'measure',number=str(bar+1))
            if bar in [0,72,80]:
                at=ET.SubElement(mm,'attributes')
                if bar==0:ET.SubElement(at,'divisions').text=str(div)
                ti=ET.SubElement(at,'time')
                if bar==72:ET.SubElement(ti,'senza-misura')
                else:ET.SubElement(ti,'beats').text='4';ET.SubElement(ti,'beat-type').text='4'
                if bar==0:cl=ET.SubElement(at,'clef');ET.SubElement(cl,'sign').text='G';ET.SubElement(cl,'line').text='2'
            if idx==1 and bar in sections:
                dire=ET.SubElement(mm,'direction');ET.SubElement(ET.SubElement(dire,'direction-type'),'words').text=sections[bar]
                if bar==0:ET.SubElement(dire,'sound',tempo='96')
                if bar==72:ET.SubElement(ET.SubElement(dire,'direction-type'),'words').text='180-200 s: referencias de segundos, sin pulso. Cortar buses métricos y colas. Ver JSON/PDF.'
            pieces=[(e,l) for e,l in lanes if e['pulso']<4*(bar+1) and e['pulso']+e['dur_pulsos']>4*bar]
            voices=sorted(set(l for e,l in pieces)) or [0]
            for vi,l in enumerate(voices):
                if vi:ET.SubElement(ET.SubElement(mm,'backup'),'duration').text=str(4*div)
                cur=0
                for e,_ in [x for x in pieces if x[1]==l]:
                    a=max(cur,max(0,round((e['pulso']-4*bar)*div)));b=min(4*div,round((e['pulso']+e['dur_pulsos']-4*bar)*div));b=max(a+1,b)
                    if a>=4*div:continue
                    b=min(4*div,b)
                    if a>cur:
                        nt=ET.SubElement(mm,'note');ET.SubElement(nt,'rest');ET.SubElement(nt,'duration').text=str(a-cur);ET.SubElement(nt,'voice').text=str(l+1)
                    nt=ET.SubElement(mm,'note');pi=ET.SubElement(nt,'pitch');m=float(e['midi']);mi=int(round(m));steps=[('C',0),('C',1),('D',0),('E',-1),('E',0),('F',0),('F',1),('G',0),('A',-1),('A',0),('B',-1),('B',0)];st,alt=steps[mi%12];ET.SubElement(pi,'step').text=st
                    alt=alt+m-mi
                    if abs(alt)>1e-9:ET.SubElement(pi,'alter').text=f'{alt:.9f}'
                    ET.SubElement(pi,'octave').text=str(mi//12-1);ET.SubElement(nt,'duration').text=str(b-a);ET.SubElement(nt,'voice').text=str(l+1)
                    if e['pulso']<4*bar:ET.SubElement(nt,'tie',type='stop')
                    if e['pulso']+e['dur_pulsos']>4*(bar+1):ET.SubElement(nt,'tie',type='start')
                    if e.get('texto') and e['pulso']>=4*bar:ET.SubElement(ET.SubElement(nt,'lyric'),'text').text=e['texto']
                    cur=b
                if cur<4*div:
                    nt=ET.SubElement(mm,'note');ET.SubElement(nt,'rest');ET.SubElement(nt,'duration').text=str(4*div-cur);ET.SubElement(nt,'voice').text=str(l+1)
    guardar(out/f'partitura-completa-r4-s22-{tag}.musicxml',ET.tostring(root,encoding='utf-8',xml_declaration=True))
    b=io.StringIO(newline='');writer=csv.writer(b);writer.writerow(['capa','segundos','duracion_s','MIDI','velocidad','texto','frase','parametros_json'])
    for c,es in P['eventos'].items():
        for e in es:writer.writerow([c,e['t'],e['dur'],e['midi'],e['vel'],e.get('texto',''),e.get('frase',''),json.dumps(e,ensure_ascii=False)])
    guardar(out/f'eventos-r4-s22-{tag}.csv',b.getvalue().encode('utf-8-sig'))

def main():
    out=ultimo();P=leer(score());tag=out.name.split('-')[-1];R=leer(out/'viaje.json');musicxml(out,P,tag)
    W,H=landscape(A4);path=out/f'partitura-revisada-s22-{tag}.pdf'
    if path.exists():raise FileExistsError(path)
    pdfmetrics.registerFont(TTFont('Ar','C:/Windows/Fonts/arial.ttf'));pdfmetrics.registerFont(TTFont('ArB','C:/Windows/Fonts/arialbd.ttf'));c=canvas.Canvas(str(path),pagesize=(W,H));c.setTitle(P['titulo']+' / partitura revisada');c.setAuthor('Canek Zapata');page=0
    INK='#1d2869';ACC='#732605'
    def text(x,y,s,size=10,bold=False,color=INK):c.setFillColor(color);c.setFont('ArB' if bold else 'Ar',size);c.drawString(x,y,str(s))
    def para(s,y,size=11,width=W-88,leading=16,x=44):
        line=''
        for word in s.split():
            trial=(line+' '+word).strip()
            if pdfmetrics.stringWidth(trial,'Ar',size)>width:text(x,y,line,size);y-=leading;line=word
            else:line=trial
        if line:text(x,y,line,size);y-=leading
        assert y>38,(page,y);return y
    def new(title,sub=''):
        nonlocal page
        if page:c.showPage()
        page+=1;c.setFillColor('#f7f0e7');c.rect(0,0,W,H,fill=1,stroke=0);text(44,H-42,title,22,True);text(44,H-65,sub,9,color=ACC);c.setStrokeColor(INK);c.setLineWidth(.4);c.line(44,35,W-44,35);text(44,20,'CANEK ZAPATA / REVISIÓN 4 / 22 OCT 2026 / PARTITURA ANTES DE PRODUCCIÓN',7);text(W-70,20,page,8)
    def staff(notes,x,y,width,bars=4):
        gap=6;c.setStrokeColor(INK);c.setLineWidth(.4)
        for j in range(5):c.line(x,y+j*gap,x+width,y+j*gap)
        bw=width/bars
        for j in range(bars+1):c.line(x+j*bw,y-3,x+j*bw,y+28)
        # Altura proporcional cromática: se etiqueta MIDI para evitar una falsa
        # lectura de figuras convencionales. El MusicXML lleva notas/ties exactos.
        for beat,m,d in notes:
            xx=x+bw*beat/4+3;yy=y+(m-64)*2
            c.setFillColor(INK);c.ellipse(xx-2.7,yy-2,xx+2.7,yy+2,stroke=0,fill=1);c.line(xx+3,yy,xx+3,yy+18);text(xx-4,y-20,f'{m:g}',6)
            c.setStrokeColor(ACC);c.line(xx,yy-8,xx+max(2,bw*d/4-3),yy-8);c.setStrokeColor(INK)
    new('Por aquí también se baila','Cumbia sonidera / recursos carnáticos / repetición y drones / contacto instrumental')
    y=para('La bolsa ahora tiene juguetes. Sus golpes enseñan una frase; el láser la atraviesa y el transporte la interrumpe. La radio conserva un silbido cuando la pasajera ya bajó.',H-105,14,leading=21)
    y=para('Treinta partes. 96 BPM. Referencia de 96 compases, 4:00 de acontecimientos y 6 s de cola prevista. Entre 3:00 y 3:20 se suspende la métrica: las divisiones del archivo son sólo coordenadas de edición.',y-8)
    for s in P['secciones']:
        text(44,y-10,f'{s["t"]:05.1f}-{s["t1"]:05.1f} s',10,True);text(154,y-10,s['nombre'],11);y-=24
    para('Parada: revisar contigo esta escritura antes de renderizar la canción. El visor se trabajará después. No hay máster nuevo ni video.',y-18,11)
    new('1 / Tema: salto, insistencia, hueco','Escritura proporcional: altura cromática y etiqueta MIDI; raya = duración. No sustituye al MusicXML.')
    for row in range(2):
        notes=[(k*4+a,m,d) for k in range(4) for a,m,d in P['tema_A'][row*4:(row+1)*4][k]]
        text(44,470-row*150,f'Compases del motivo {1+row*4}-{4+row*4}',11,True);staff(notes,50,405-row*150,W-100)
    y=para('Identidad: D-A, semitono A-Ab, Ab repetido; pregunta rota por huecos. Respuesta E-D-C y una llegada con Eb-D. Se evita volver a presentar D-F-A como única idea bajo una sucesión fija de acordes.',160)
    para('El acordeón presenta; el láser conserva los ataques y cambia la procedencia. En la coda el clarinete recuerda. Después de la avería, ciertos finales quedan desplazados 51.3 cents por la razón 11/8 frente a la cuarta temperada.',y-9)
    new('2 / Percusiones: quién pregunta y quién espera','M = dos pulsos; P = un pulso. 3M + 2P = ocho pulsos. Remates propios, no transcripción tradicional.')
    y=H-110
    for title,s in [('Aprender',4),('Contradecir el acordeón',3),('Cruzar el solo',5)]:
        r=__import__('partitura').mora(s);text(44,y,title+f' / {s} unidades por pulso',13,True);y-=30;bw=(W-100)/(8*s)
        for j in range(8*s):
            xx=50+j*bw;c.setStrokeColor(INK);c.line(xx,y-7,xx,y+(15 if j%s==0 else 6))
            if j in r['golpes']:c.setFillColor(ACC);c.circle(xx+2,y,2.5,stroke=0,fill=1)
        y-=65
    y=para('Din sostiene; ta corta; thom inflexiona el grave. Barro contesta y pandero desgrana: no doblan todos los golpes. La boca entra en remates escogidos. La lluvia lleva la carga central calculada de 0.5 a 2.3.',y)
    para('Después de 3:20 vuelve el bajo en el uno, pero la membrana omite su primer ataque. La deuda es local y audible: no desaparece todo el comienzo del compás. Revisión pendiente: balance de ese hueco al escuchar.',y-8)
    new('3 / El recorrido tiene dirección','Alturas de la hoja Mesa 22; conexiones y tiempo del autobús compuestos. No es una carretera levantada.')
    c.drawImage(ImageReader(str(next((out/'proceso').glob('01-*.png')))),44,145,width=W-88,height=(W-88)*630/1200)
    v=P['terreno_viaje'];y=para(f'Ruta cerrada de {v["distancia_m"]/1000:.3f} km; ascenso acumulado {v["ascenso_m"]:.2f} m y descenso {v["descenso_m"]:.2f} m. Sale y llega a {v["origen_m"]:.2f} m; cota máxima {v["cota_mayor_m"]:.2f} m.',126,10,leading=15)
    para('Subida: ataques más apretados y mayor presión. Bajada: reaparecen huecos y colas más largas. El viaje se frena con la integración del tráfico por tramo; las tres voces guardan fase acumulada durante toda la pieza.',y-4,10,leading=15)
    new('4 / Solo D: volver no restaura la voz','El circuito del láser y el recorrido del autobús son dos movimientos distintos sobre la misma hoja.')
    c.drawImage(ImageReader(str(next((out/'proceso').glob('03-*.png')))),150,228,width=540,height=540*630/1200)
    y=para('A rota las voces 1-2; B rota las voces 2-3. El circuito aplica A, B, inversa de A e inversa de B. C = B^-1 A^-1 BA. La norma del estado se conserva, pero C no es identidad. El signo se aplica a la onda antes de sus redes: no convertirlo en una simple etiqueta.',210,10,leading=15)
    for s in P['solo_D']:
        text(44,y,f'{s["t"]:05.1f}s / c.{s["compas"]:02} / {s["operacion"]}',9,True);text(285,y,'  '.join(f'{x:+.4f}' for x in s['pesos_con_signo']),9);y-=15
    new('5 / Avería: veinte segundos sin pulso','3:00-3:20 / inicio al 73.17% de la duración prevista. Sin subida de tensión periódica hacia un drop.')
    y=para('179.960 s: cerrar con 35 ms de salida todos los buses métricos, incluidos drones pulsados, Talbot y retardos del láser. Vaciar sus buffers; ninguna cola debe atravesar la parada. Esta orden deberá comprobarse también sobre el audio futuro.',H-110,12,leading=18)
    for t,g,m,d in P['break_libre']['eventos']:
        text(44,y-15,f'{t:.2f} s',12,True);y=para(g,y-15,12,x=145,width=W-195,leading=18)-12
    y=para('La radio habla entre gestos, no cuenta. Un dedo recuerda un único ataque a 196.23 s y no completa la célula. El motor prende a 197.61; su encendido no fija un metrónomo. No hay redoble, riser ni tempo ramp.',y-12)
    para('200.000 s: bajo y base vuelven. La membrana deja vacío su primer lugar. El campo armónico incorpora 11/8 y la fase de los tres vehículos sigue siendo la acumulada antes del corte; no se resetea al nuevo uno.',y-10)
    new('6 / La letra tiene objetos y consecuencias','Sílabas/alturas/tiempos completos en JSON y MusicXML. Radio escrita por separado.')
    y=H-104
    for line in P['letra'][:7]:
        text(44,y,f'{line["t"]:.1f} s / {line["funcion"]}',9,True,color=ACC);y=para(line['texto'],y-20,13,leading=20)-13
    new('7 / Regreso: algo se queda','El coro conserva su frase; sus acompañantes recuerdan lo que pasó.')
    y=H-104
    for line in P['letra'][7:]:
        text(44,y,f'{line["t"]:.1f} s / {line["funcion"]}',9,True,color=ACC);y=para(line['texto'],y-20,13,leading=20)-13
    para('La rotura del ala vuelve reconocible el juguete, sin convertir cada objeto en un símbolo. La salida conserva una ambigüedad preparada: ¿la llamada viene del silbato, del clarinete o de la radio que lo aprendió?',y-3,11)
    new('8 / Radio: sabe algo que la canción no explica','Avisos ficticios; habla libre, sin cantarlos al pulso del beat.')
    y=H-102
    for r in P['radio']:
        text(44,y,f'{r["t"]:.1f} s / {r["voz"]}',9,True,color=ACC);y=para(r['texto'],y-18,12,leading=18)-15
    new('9 / Instrumentos: los nuevos y los que responden','No se cuentan canales como si fueran treinta instrumentos nuevos.')
    y=H-110
    for title,body in [
        ('Ya construidos en la primera etapa','Láser de transbordos: chirp, Talbot y red de retardos. Membrana central cargada por FEM. Raspador del perfil de depósitos. Barro modal y pandero sintético.'),
        ('Nuevos en esta revisión','Bolsa: tres osciladores con topes; aceleración y curvatura del recorrido producen contactos que excitan trompo de lámina, cascabel y silbato de barro. Motor: encendidos decrecientes que fracasan. No son grabaciones realistas calibradas.'),
        ('Nuevo controlador, no timbre adicional','Transbordos no conmutativos de tres amplitudes con signo. Controla las tres capas de láser; conservar esa relación al producir y evaluar interferencias en mono.'),
        ('Biblioteca que sostiene la canción','Acordeón, bajo/conga/güiro/campana, batería acústica/808, mbira y arpa de boca, guembri, órgano, clarinete, chelo y voces Sabina. El vibráfono de r3 cede su parte a la bolsa; siguen siendo treinta partes.'),
        ('Lo que debe hacer la interpretación','Consumir carga_central, pendiente, corte_agudos_hz, fase_signo, objeto/fuerza_impacto y cortes de buses; el JSON es el contrato. MusicXML conserva alturas microtonales pero no sustituye estos parámetros.')]:
        text(44,y,title,13,True);y=para(body,y-23,11,leading=16)-20
    # Seis páginas de mapa completo. Las notas quedan íntegramente en XML/JSON;
    # este plano es de dirección y muestra actividad y espacios sin ocultarlos.
    for first in range(0,96,16):
        new(f'Plano / compases de referencia {first+1}-{first+16}','Las posiciones 73-80 se leen como segundos de tiempo libre. Trazo = duración; no es una reducción de piano.')
        x0=175;x1=W-45;y0=H-105;row=13.5;span=16*BAR
        for i in range(17):
            x=x0+(x1-x0)*i/16;c.setStrokeColor('#c8c4ba');c.setLineWidth(.3);c.line(x,y0+7,x,y0-30*row);text(x+1,y0+14,first+i+1,6)
        for j,(name,es) in enumerate(P['eventos'].items()):
            y=y0-j*row;text(44,y-2,name,7.4)
            for e in es:
                a=max(first*BAR,e['t']);b=min((first+16)*BAR,e['t']+e['dur'])
                if b>a:c.setStrokeColor(ACC if e.get('libre') else INK);c.setLineWidth(1.3);c.line(x0+(a-first*BAR)/span*(x1-x0),y,x0+(b-first*BAR)/span*(x1-x0),y)
        text(44,53,'Duraciones y alturas exactas: partitura-r4.json y MusicXML; controles y fases firmadas: JSON/CSV.',8)
    new('Antes de producir / tres pruebas de escucha','La verificación numérica no prueba belleza, inteligibilidad ni jerarquía de la mezcla.')
    y=H-115
    for s in ['1. ¿Se reconoce el mismo motivo en acordeón, juguete y láser, o la transformación borra su identidad? Comparar seco, con transbordos y con fase sin signo.',
              '2. ¿La ausencia del primer ataque de membrana se oye después del corte? Si bajo y bombo la tapan, adelgazar el primer ciclo; no explicarla sólo en las notas.',
              '3. ¿La radio conserva el silbato al final sin que la letra deba explicarlo todo? Revisar inteligibilidad, pausas y distancia de los tres posibles emisores.',
              'Comparación con El río no tiene tronco: allí once afluentes y cinco brazos derivan alturas, tempos y llegadas de la geografía. Aquí la estructura tiene relevo causal, circuito no conmutativo, reloj con memoria y avería, pero no se afirma haber igualado su riqueza sonora sin escuchar.',
              'Próxima decisión contigo: aprobar o corregir esta partitura. Después se podrá interpretar la canción y revisar la mezcla. Visor y hazvideo.py quedan para una fase posterior; el video completo lo renderiza Canek.']:
        y=para(s,y,12,leading=19)-24
    c.save()
    rd=BASE/'render'/f'revision-{tag}'/'pdf';rd.mkdir(parents=True,exist_ok=False);doc=fitz.open(path)
    previews=[]
    for j,p in enumerate(doc):
        pix=p.get_pixmap(matrix=fitz.Matrix(1.25,1.25),alpha=False);fn=rd/f'pagina-{j+1:02}.png';guardar(fn,pix.tobytes('png'));previews.append(fn)
    guardar(out/'proceso'/f'04-edicion-partitura-s22-{tag}.png',previews[5].read_bytes())
    jsave(out/'edicion.json',{'pdf':path.name,'paginas':len(doc),'raster_revision':str(rd),'musicxml':'30 partes, 96 posiciones; senza misura en 73-80; alteraciones fraccionarias; 960 ticks/pulso','canonico':'partitura-r4.json; MusicXML no transmite toda la síntesis','no_producido':['audio completo','visor','video']})
    print(json.dumps({'pdf':str(path),'paginas':len(doc),'raster':str(rd)},ensure_ascii=False))

if __name__=='__main__':main()
