"""Datos del video: la partitura de la entrega vigente, cuándo dice Siringua cada palabra (con la velocidad del cambio de tono y los
cortes, igual que mezcla.py) y la curva del bombeo (sidechain, 100 Hz). Todo lo que el video dibuja sale de aquí.
    python video/preparar.py <entrega> <carpeta-de-render>   → video/datos.json"""
import json, os, sys
import numpy as np
E, RUN = sys.argv[1], sys.argv[2]; AQUI = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(E, 'partitura.json'), encoding='utf-8')); S = json.load(open(os.path.join(RUN, 'siringua.json'), encoding='utf-8'))
VEL = {0: 1, 7: 1.5, 12: 2, 5: 4 / 3}                    # como transponer() en mezcla.py: subir = acelerar (sampler)
pal = []
for s in P['siringua']:
    v = VEL[s['transponer']]
    if s['modo'] == 'entera':
        for w in S['palabras']: pal.append(dict(t=round(s['t'] + w['t'] / v, 4), dur=round(w['dur'] / v, 4), texto=w['texto'], st=s['transponer'], corte=False))
    else:
        t = s['t']
        for i in s['palabras']:
            for j in range(3): pal.append(dict(t=round(t + j * s['paso'], 4), dur=round(s['paso'], 4), texto=S['palabras'][i]['texto'], st=s['transponer'], corte=True, rep=j))
            t += 3 * s['paso']
duck = np.load(os.path.join(RUN, 'duck.npy'))
datos = dict(titulo=P['titulo'], semilla=P['semilla'], bpm=P['bpm'], duracion=P['duracion'], secciones=P['secciones'], glitch=P['glitch'], tonica=P['tonica'], escala=P['escala'],
             frase=P['frase'], web=P['web'], sub=P['sub'], dundun=P['dundun'], tambor_habla=P['tambor_habla'], aves_objeto=P['aves_objeto'], aves_jardin=P['aves_jardin'],
             agua=P['agua'], waterphone=P['waterphone'], palabras=pal, duck=[round(float(x), 3) for x in duck], duck_hz=100, entrega=os.path.basename(os.path.normpath(E)))
json.dump(datos, open(os.path.join(AQUI, 'datos.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(len(pal), 'palabras;', sum(len(v) for v in P['web'].values()), 'notas web;', len(duck), 'puntos de bombeo')
