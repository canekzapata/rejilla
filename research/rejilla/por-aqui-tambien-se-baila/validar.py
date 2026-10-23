"""Validación de primera etapa. Rechaza un máster completo o video accidental."""
from comun import *
from instrumentos import matriz_cruce
import xml.etree.ElementTree as ET,fitz
def main():
 out=ultimo();P=leer(score());D=leer(depo());T=leer(out/'trafico.json');report={'partitura_vigente':score().name,'deposito_vigente':depo().name,'capas':len(P['eventos']),'eventos':sum(map(len,P['eventos'].values()))};assert len(P['eventos'])==30
 for name,es in P['eventos'].items():
  assert es and all(np.isfinite(e['pulso']) and e['dur']>0 and e['t']>=0 and e['t']+e['dur']<=P['duracion_prevista'] for e in es),name
  assert all(es[k]['t']<=es[k+1]['t'] for k in range(len(es)-1)),name
 assert abs(D['volumen_entrada_m3']-D['volumen_salida_m3']-D['volumen_depositado_m3'])/D['volumen_entrada_m3']<1e-12
 assert D['error_balance_relativo']<1e-12 and T['intervenciones_guarda']==0 and T['min_distancia_m']>5.2
 report['deposito']={'error_balance_relativo':D['error_balance_relativo'],'max_m':float(np.max(D['depositos_m'])),'caminos_unicos':len(np.unique(np.array(D['caminos']),axis=0)),'salidas':np.unique(np.array(D['caminos'])[:,-1]).tolist()};report['trafico']={k:T[k] for k in ['v_min','v_max','fraccion_v_menor_08','min_distancia_m','intervenciones_guarda','caos']}
 tr=P['traza_trafico'];delta=[abs(e['pulso_efectivo']-e['pulso_nominal']) for e in tr if not e['suprimido']];assert max(delta)>.1;report['escritura_trafico']={'entradas_suspendidas':sum(e['suprimido'] for e in tr),'max_desfase_pulsos':max(delta),'eventos_con_traza':len(tr),'limite':'cierre de ocho pulsos compuesto; no es el tiempo físico de llegada'}
 for r in P['moras']:assert 3*r['M']+2*r['silencio']==8*r['subdivision'] and r['aterrizaje_pulsos']==8
 assert not any('requinto' in name for name in P['eventos'])
 for name in ['voz-verso','voz-respuesta','radio-chofer','radio-pasajera']:
  assert not any(e['t']<68*BAR and e['t']+e['dur']>52*BAR for e in P['eventos'][name]),name
 xml=ET.parse(next(out.glob('*.musicxml'))).getroot();assert len(xml.findall('part'))==30;measures=0
 for pt in xml.findall('part'):
  assert len(pt.findall('measure'))==96
  for mm in pt.findall('measure'):
   vv={}
   for n in mm.findall('note'):v=n.findtext('voice');vv[v]=vv.get(v,0)+int(n.findtext('duration'))
   assert all(d==4*960 for d in vv.values());measures+=1
 report['musicxml']={'partes':30,'compases_por_parte':96,'compases_revisados':measures,'divisiones_por_pulso':960}
 files={**leer(BASE/'procedencia.json')['fuentes'],**{str(lib().relative_to(BASE)).replace('\\','/')+'/'+p:h for p,h in leer(lib()/'manifiesto.json')['archivos'].items()}}
 for p,h in files.items():assert sha(BASE/p)==h,p
 assert sha(out/'datos/h-22.f32')==sha(BASE/'render/geometria-instrumentada-22/h-22.f32'),'instrumentar cambió alturas';report['fuentes_cotejadas']=len(files);report['instrumentacion_conserva_alturas']=True
 aud=[]
 for p in out.glob('*.wav'):
  sr,y=wavfile.read(p);dur=len(y)/sr;assert dur<45 and np.isfinite(y).all() and abs(y).max()<=1 and abs(y).max()>1e-7,p;aud.append({'archivo':p.name,'segundos':dur,'pico':float(abs(y).max())})
 report['sondas']=aud;assert not list(BASE.rglob('*.mp4'));assert not (out/(out.name+'.wav')).exists();report['master_producido']=False;report['video_renderizado']=False
 bench=leer(out/'sondas-instrumentos-r2.json');assert bench['laser']['error_ortogonalidad']<1e-12;assert all(v.get('Talbot_diferencia_energia',0)<1e-10 for v in bench['laser']['lecturas']);assert bench['raspador']['diferencia_relativa']>.01;report['instrumentos']={'cruces_error':bench['laser']['error_ortogonalidad'],'raspador_cambio_relativo':bench['raspador']['diferencia_relativa'],'membrana_contra_sin_carga':float(np.linalg.norm(np.array(bench['membrana']['ratios_con_carga'])-bench['membrana']['ratios_sin_carga']))}
 pdf=next(out.glob('*.pdf'));doc=fitz.open(pdf);assert len(doc)==15
 for page in doc:
  for b in page.get_text('blocks'):assert b[0]>=25 and b[1]>=14 and b[2]<=page.rect.width-20 and b[3]<=page.rect.height-14
 report['pdf']={'paginas':15,'texto_dentro_de_margenes':True,'rasterizadas':15,'tipo':'dirección y notación proporcional; MusicXML completo aparte'};report['limite']='Revisión numérica y visual; sin audición propia. Parada para revisión con Canek antes de mezcla.';name='validacion-primera-etapa-r2.json' if (out/'validacion-primera-etapa.json').exists() else 'validacion-primera-etapa.json';jsave(out/name,report);print('30 capas, 2880 compases XML, fuentes, sondas y PDF: correctos. Sin máster ni video.')
if __name__=='__main__':main()
