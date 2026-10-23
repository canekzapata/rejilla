"""Auditoría de escritura, sólo lectura. No importa el generador ni renderiza audio.

Los conteos describen la partitura; no puntúan su calidad ni predicen su escucha.
Ejecutar: python -X utf8 auditar_critica.py
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import numpy as np
from instrumentos import transporte

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'luciernagas-partitura-s1-054923e7c401'
SCORE = OUT / 'partitura-v4.json'
P = json.loads(SCORE.read_text('utf8'))
PLANS = json.loads((OUT / 'datos/transportes.json').read_text('utf8'))
E = P['eventos']
C0, C1 = P['centro']
BAR = P['negra_s'] * 4
ALL = [(k, e) for k, events in E.items() for e in events]


def unique(values):
    return len({json.dumps(v, sort_keys=True) for v in values})


def window(a, b):
    events = [(k, e) for k, e in ALL if a <= e['t'] < b - 1e-7]
    return {'inicio_s': a, 'fin_s': b, 'ataques': len(events),
            'partes_con_ataque': len({k for k, _ in events})}


vocal = []
for line in P['letra']:
    if line['capa'] != 'voz' or line['t'] >= C0:
        continue
    events = sorted((e for e in E['voz'] if e['frase'] == line['frase']), key=lambda e: e['t'])
    vocal.append({'frase': line['frase'], 'inicio_s': line['t'],
                  'ventana_s': line['fin'] - line['t'],
                  'midi': [e['midi'] for e in events],
                  'velocidades': sorted({e['vel'] for e in events})})

center = sorted([(k, e) for k, e in ALL if C0 <= e['t'] < C1], key=lambda x: x[1]['t'])
groups = [center[i:i+3] for i in range(0, len(center), 3)]
penalty_difference = 0.0
for plan in PLANS:
    no_penalty = transporte(plan['source'], plan['target'], plan['a'], plan['b'], 0)
    penalty_difference = max(penalty_difference,
                             float(np.max(abs(np.array(plan['pi']) - no_penalty['pi']))))

wall = next(s for s in P['secciones'] if s['id'] == 'VIII')
wall_windows = [window(wall['t'] + j*8*BAR, wall['t'] + (j+1)*8*BAR) for j in range(3)]
kit = ['bombo', 'caja', 'hat', 'tom', 'aro', 'ride']
report = {
    'partitura': str(SCORE.relative_to(ROOT)),
    'sha256_partitura': hashlib.sha256(SCORE.read_bytes()).hexdigest(),
    'limite': 'Lectura de escritura y modelos; sin audición. Los ataques cuentan notas de acorde por separado.',
    'eventos': len(ALL),
    'partes': len(E),
    'guitarra_eventos': len(E['guitarra']),
    'componentes_bateria_eventos': sum(len(E[k]) for k in kit),
    'guitarra_mas_bateria_porcentaje': 100*(len(E['guitarra'])+sum(len(E[k]) for k in kit))/len(ALL),
    'filiacion': {
        'eventos_con_ancestro': sum(bool(e.get('ancestro')) for _, e in ALL),
        'ancestros_distintos': dict(Counter(e.get('ancestro') for _, e in ALL if e.get('ancestro'))),
        'advertencia': 'Un identificador existente no verifica una transformación musical.'},
    'voz_antes_centro': vocal,
    'voz_ventanas_distintas_antes_centro': unique([round(v['ventana_s'], 6) for v in vocal]),
    'centro': {
        'gestos': len(center),
        'grupos_consecutivos_de_tres': [
            {'inicios_relativos_s': [round(e['t']-C0, 6) for _, e in g],
             'partes': [k for k, _ in g]} for g in groups],
        'oscuridades_s': [[round(a-C0, 6), round(b-C0, 6)] for a, b in P['oscuridades']],
        'inicio_a_inicio_grupos_s': [round(groups[j+1][0][1]['t']-groups[j][0][1]['t'], 6)
                                   for j in range(len(groups)-1)]},
    'transportes': {
        'planes': len(PLANS),
        'fuentes_distintas': unique([x['source'] for x in PLANS]),
        'distribuciones_origen_distintas': unique([x['a'] for x in PLANS]),
        'distribuciones_destino_distintas': unique([x['b'] for x in PLANS]),
        'matrices_pi_distintas_a_9_decimales': unique([
            np.where(abs(np.array(x['pi'])) < 1e-9, 0, np.round(x['pi'], 9)).tolist()
            for x in PLANS]),
        'cambio_maximo_pi_al_quitar_penalizacion': penalty_difference,
        'distancias_destino_a_nueva_fuente_max_por_paso_semitonos': [
            round(max(abs(a-b) for a, b in zip(x['target'], y['source'])), 6)
            for x, y in zip(PLANS, PLANS[1:])],
        'advertencia': 'La distancia anterior compara índices, no demuestra un salto audible; hay aristas y pausas.'},
    'reentrada_primera_mitad_de_segundo': window(C1-1e-7, C1+.5),
    'pared_tres_ventanas_iguales': wall_windows,
    'advertencia_densidad': 'Conteo de inicios; no energía, volumen, voces independientes ni densidad percibida.'
}
print(json.dumps(report, ensure_ascii=False, indent=2))
