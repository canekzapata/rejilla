"""Lo que la cinta olvida — partitura. Cumbia rebajada de Monterrey × las cintas que se deshacen de Basinski × el cello con eco de
Arthur Russell, sobre la llanura de meandros 26 de Traspuesta y «nostosdenadie» (la de muchas vueltas, la politrópica; una sola
orden en la cinta: regresa lo que veas; me quedé porque olvidar la misión era lo más parecido a llegar). Diseño en DISENO.md.

REBAJAR = LA SINUOSIDAD. La banda del sonidero se escribe en TIEMPO DE CINTA τ (120 bpm, compás de 2 s) y la cinta corre a la
velocidad con que el río avanza valle abajo: en cada una de las 13 vueltas del meandro, v = (cuerda ÷ arco)^½ (0.57–0.82). Cada
vuelta dura en la canción lo que mide en el río (su arco). En las cuatro vueltas más sinuosas el río se corta el cuello: los dos
últimos compases de esa vuelta se quedan dando vueltas (lagos de herradura) hasta el final. Al salir de la hoja la cinta se frena.
LO VIVO (cello, voz viva, río, pájaros) se escribe también en τ, para que vaya en el groove, pero se toca en tiempo real con la
altura de la cinta en ese instante (12·log₂ v): no pasa por la cinta, la sigue.
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np
from scipy.ndimage import gaussian_filter1d
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'motor')); import cinta as CI

SEMILLA = 26
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__))
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-26.json'), encoding='utf-8'))
Q = 0.5; BAR = 4 * Q; S16 = Q / 4                                               # tiempo de cinta: 120 bpm
def t_(b, s=0.0): return b * BAR + s * S16

# ── las vueltas del río ──
P = np.array(TER['cauce']); ds = np.hypot(*np.diff(P, axis=0).T); cum = np.concatenate([[0], np.cumsum(ds)]); LT = cum[-1]
ang = np.unwrap(np.arctan2(*np.gradient(P, axis=0).T[::-1])); ks = gaussian_filter1d(np.gradient(ang), 6)
INF = list(np.nonzero(np.diff(np.sign(ks)))[0])
VUELTAS = []
for a, b in zip(INF[:-1], INF[1:]):
    arco = cum[b] - cum[a]; cuerda = float(np.hypot(*(P[b] - P[a]))); VUELTAS.append(dict(i0=int(a), i1=int(b), frac=arco / LT, sinuosidad=arco / cuerda, v=(cuerda / arco) ** .5))
BARS_TOTAL = 80
INTRO = 4
for vu in VUELTAS: vu['bars'] = max(4, int(round(vu['frac'] * BARS_TOTAL)))
b = INTRO
for k, vu in enumerate(VUELTAS): vu['b0'] = b; b += vu['bars']; vu['b1'] = b; vu['n'] = k + 1
FIN_CINTA = b; T_TAU = t_(FIN_CINTA) + 1
CORTES = sorted(sorted(range(len(VUELTAS)), key=lambda k: -VUELTAS[k]['sinuosidad'])[:4])     # las cuatro más sinuosas
for k in CORTES: VUELTAS[k]['corte'] = True
# la velocidad de la cinta en τ: constante por vuelta, con un compás de transición (coseno); al final, la cinta se frena
def v_de_tau(x):
    if x < t_(INTRO): v = .75
    else:
        v = VUELTAS[-1]['v']
        for k, vu in enumerate(VUELTAS):
            if x < t_(vu['b1']):
                v = vu['v']; xa = x - t_(vu['b0'])
                if k > 0 and xa < BAR: u = xa / BAR; v = VUELTAS[k - 1]['v'] + (vu['v'] - VUELTAS[k - 1]['v']) * (.5 - .5 * math.cos(math.pi * u))
                break
    fin = t_(FIN_CINTA) - 1.0
    if x > fin: v *= max(.14, 1 - .86 * (x - fin) / 1.0)                         # la cinta se frena al salir de la hoja (~3 s reales)
    return v
MP = CI.mapa(v_de_tau, T_TAU); TAU, TR, VV = MP
def treal(x): return float(np.interp(x, TAU, TR))
def vel(x): return float(np.interp(x, TAU, VV))
T_FIN_CINTA = treal(t_(FIN_CINTA)); DUR = T_FIN_CINTA + 26                           # coda: sólo lagos y lo vivo
CURV = {round(t_(vu['b0']), 3): (vu['sinuosidad'] - 1.4) / 1.7 for vu in VUELTAS}

# ── armonía (en la cinta: re menor) ──
TON = 62
GRADOS = {'i': [0, 3, 7], 'iv': [5, 8, 12], 'V': [7, 11, 14], 'VII': [10, 14, 17], 'VI': [8, 12, 15], 'III': [3, 7, 10]}
ANDALUZA = ['i', 'VII', 'VI', 'V']; VERSO = ['i', 'iv', 'VII', 'III', 'VI', 'iv', 'V', 'V']
def raiz(g): return TON + GRADOS[g][0]

ev = {k: [] for k in ['acordeon', 'bajo', 'guiro', 'conga', 'campana', 'sirena', 'timbal', 'organo']}
FICHA = {'acordeon': 'meleeviewer-13-acordeon', 'bajo': 'meleeviewer-13-bajo', 'guiro': 'meleeviewer-13-guiro', 'conga': 'meleeviewer-13-conga', 'campana': 'meleeviewer-13-campana',
         'sirena': 'meleeviewer-13-sirena', 'organo': 'receta-organo-roto'}
def web(stem, t, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=kw.pop('ficha', FICHA.get(stem)), midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
def timbal(t, pieza, v, pan=0.0): web('timbal', t, 60, v, .2, pan, ficha='bateria-acustico', pieza=pieza)
requinto, chelo, garganta, agua, aves, sonidero, coro, viva, coros = [], [], [], [], [], [], [], [], {v: [] for v in 'SAT'}

def cumbia(b, g, lleno=1.0, acordeon=True):
    """un compás de cumbia sonidera en τ: güiro chiqui-chá, conga, campana, la clave de la tarola, el bajo raíz–quinta, el acordeón a contratiempo"""
    for s in range(0, 16, 2): web('guiro', t_(b, s), 60, .75 if s % 4 == 0 else .55, S16 * 1.6, .35)
    for s in (3, 7, 11, 15): web('guiro', t_(b, s), 60, .35, S16 * .8, .35)
    if lleno > .3:
        for s, tono, v in ((2, 0, .6), (6, 5, .75), (7, 5, .6), (10, 0, .6), (14, 5, .75), (15, 5, .6)): web('conga', t_(b, s), 60 + tono, v, .2, -.3)
    if lleno > .5:
        for s in (0, 4, 8, 12): web('campana', t_(b, s), 72, .5 + .15 * (s == 0), .15, .4)
        for s in (4, 12): timbal(t_(b, s), 'rim', .55, .1)
    r = raiz(g)
    for s, d, n in ((0, 5, r), (6, 2, r + 7), (8, 5, r), (12, 2, r + 7), (14, 2, r + 4 if g == 'V' else r + 3)): web('bajo', t_(b, s), n - 24, .85 if s in (0, 8) else .7, d * S16 * .9, 0)
    if acordeon:
        for s in (2, 6, 10, 14): [web('acordeon', t_(b, s), TON + 12 + x, .45, S16 * 1.5, -.2) for x in GRADOS[g]]
def fill(b): [timbal(t_(b, 12 + q), ['tomhi', 'tommid', 'tomlo', 'tomlo'][q], .7 + .05 * q, -.3 + .2 * q) for q in range(4)]

def silabas(destino, texto, b, s0, alturas, ritmo, legato=.9, **kw):
    t = t_(b, s0)
    for i, sy in enumerate(texto.split()):
        d = ritmo[i % len(ritmo)] * S16; destino.append(dict(t=round(t, 4), dur=round(d * legato, 4), texto=sy, nota=round(alturas[i % len(alturas)], 3), **kw)); t += d
    return t

# ═════════ intro: el sonidero se presenta ═════════
web('sirena', t_(0), 72, .7, 3.5, 0); web('sirena', t_(2, 8), 72, .5, 2, 0)
for b in range(INTRO):
    for s, x in ((0, 7), (3, 5), (6, 3), (10, 2), (12, 0)): web('acordeon', t_(b, s), TON + 12 + x + (0 if b % 2 == 0 else -2), .55, S16 * 2.5, -.2)   # el acordeón suelto, rubato
SALUDOS = [('sa lu dos a la de mu chas vuel tas', 0, 4), ('a la que no lle va a na die', 1, 4), ('des de la lla nu ra de los me an dros', 2, 2), ('pa ra to dos los que se que da ron', 3, 0)]
for txt, b, s0 in SALUDOS: silabas(sonidero, txt, b, s0, [TON + 7] * 12, [1], legato=.85)

# ═════════ las vueltas ═════════
def coro_de(b, llamada=True):
    """llamada (la voz) y respuesta (el coro a tres): «la de muchas vueltas / la que no lleva a nadie»"""
    if llamada: silabas(coro, 'la de mu chas vuel tas', b, 0, [TON + 7, TON + 7, TON + 8, TON + 7, TON + 5, TON + 3], [2, 2, 2, 2, 3, 5])
    t = t_(b + 1); sil = 'la que no lle va a na die'.split(); rit = [1, 1, 2, 2, 2, 2, 2, 4]; mel = [10, 8, 7, 5, 7, 8, 7, 2]
    for i, sy in enumerate(sil):
        d = rit[i] * S16
        for v, x in zip('SAT', (0, -3, -7)): coros[v].append(dict(t=round(t, 4), dur=round(d * .9, 4), texto=sy, nota=round(TON + mel[i] + x, 3)))
        t += d
VERSO_TXT = [('zar pó con la bo de ga', [7, 7, 8, 10, 8, 7, 5], [2, 2, 1, 1, 2, 2, 6]), ('lle na de si len cio', [5, 5, 3, 2, 3, 0], [2, 2, 2, 2, 2, 6]),
             ('y u na so la or den', [7, 8, 10, 12, 10, 8, 7], [1, 1, 2, 2, 2, 2, 6]), ('en la cin ta', [8, 7, 5, 7], [2, 2, 4, 8]),
             ('re gre sa lo que ve as', [12, 10, 8, 7, 5, 3, 2], [2, 2, 2, 2, 2, 2, 4])]
for k, vu in enumerate(VUELTAS):
    n = vu['n']; b0, b1 = vu['b0'], vu['b1']
    prog = ANDALUZA if n in (1, 4, 5, 6, 7, 13) else VERSO
    if n <= 7 or n == 13:                                                        # la banda entera
        for b in range(b0, b1): cumbia(b, prog[(b - b0) % len(prog)], 1.0, acordeon=n not in (5, 6)); (fill(b) if b == b1 - 1 else None)
    elif n in (8, 9):                                                             # el río se endereza: queda el esqueleto
        for b in range(b0, b1): [web('guiro', t_(b, s), 60, .5, S16 * 1.6, .35) for s in range(0, 16, 2)]; [web('bajo', t_(b, s), raiz(ANDALUZA[(b - b0) % 4]) - 24, .6, S16 * 4, 0) for s in (0, 8)]
    else:                                                                         # 10–12: casi nada; el órgano sostiene
        for b in range(b0, b1, 2): [web('organo', t_(b), TON + x, .4, 2 * BAR * .95, -.3) for x in GRADOS[ANDALUZA[(b - b0) // 2 % 4]]]
        for b in range(b0, b1): web('bajo', t_(b), raiz(ANDALUZA[(b - b0) % 4]) - 24, .5, BAR * .9, 0)
    if n in (1, 4, 13): [coro_de(b, llamada=True) for b in range(b0, b1 - 1, 2)]
    if n in (2, 3):
        for i, (txt, mel, rit) in enumerate(VERSO_TXT[(n - 2) * 3:(n - 2) * 3 + 3]): silabas(coro, txt, b0 + 2 * i, 0, [TON + m for m in mel], rit)
    if n in (1, 4): [web('organo', t_(b), TON + 12 + x, .35, 2 * BAR * .95, -.3) for b in range(b0, b1, 2) for x in GRADOS[ANDALUZA[(b - b0) % 4]]]
    if n == 5:                                                                    # el solo de requinto: punteo en terceras, frases que caen al acorde
        for b in range(b0, b1):
            g = ANDALUZA[(b - b0) % 4]
            for s in range(0, 16, 2 if b % 2 else 1):
                x = [0, 3, 7, 10, 12, 10, 7, 5, 3, 2, 0, -2][(s + 3 * b) % 12]
                for y in (0, -4): requinto.append(dict(t=round(t_(b, s), 4), dur=round(S16 * 1.8, 4), m=round(raiz(g) + 12 + x + y, 3), v=.7 + .2 * (s % 4 == 0), c=int(y != 0)))
    if n == 6:                                                                    # el solo de acordeón: sube por la andaluza y se queda arriba
        for b in range(b0, b1):
            g = ANDALUZA[(b - b0) % 4]
            for s in range(0, 16, 1):
                if R.random() < .75: web('acordeon', t_(b, s), raiz(g) + 12 + [0, 2, 3, 5, 7, 8, 10, 12][(s + b) % 8] + 12 * ((b - b0) >= 2), .65, S16 * 1.3, -.1)
    if n in (5, 6, 7): silabas(sonidero, ['u na vuel ta más', 'la vuel ta nú me ro que ya na die cuen ta', 'o tra vuel ta pa ra los que se que da ron'][n - 5], b0, 4, [TON + 7] * 14, [1], legato=.85)
    if vu.get('corte'): web('sirena', t_(b1 - 1, 8), 72, .45, 1.6, .3)           # el sonidero avisa el corte
# ── lo vivo (escrito en τ para que vaya en el groove; se toca en tiempo real con la altura de la cinta) ──
V = {vu['n']: vu for vu in VUELTAS}
VIVA = [(8, 'me que dé por que ol vi dar la mi sión', [7, 7, 8, 7, 5, 3, 5, 3, 2, 0], [4, 2, 6, 2, 2, 4, 2, 2, 4, 10]),
        (9, 'e ra lo más pa re ci do a lle gar', [3, 5, 7, 8, 7, 5, 3, 2, 0, 0], [2, 2, 4, 8, 2, 2, 2, 2, 4, 12]),
        (10, 'lo que vuel ve es el re la to del re gre so', [7, 7, 8, 10, 8, 7, 5, 7, 5, 3, 2, 0], [2, 2, 4, 2, 2, 2, 2, 2, 2, 4, 2, 10]),
        (11, 'la voz que di ce re gre so mien tras se a le ja', [5, 7, 8, 7, 5, 3, 2, 3, 2, 0, -2, 0, 0], [2, 4, 2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 12])]
for n, txt, mel, rit in VIVA: silabas(viva, txt, V[n]['b0'], 0, [TON + m for m in mel], rit, legato=1.0)
for vu in VUELTAS[6:]:                                                            # el cello (Arthur Russell): notas largas, arco, a veces pizz que se vuelve eco
    for b in range(vu['b0'], vu['b1'], 2):
        g = ANDALUZA[(b - vu['b0']) // 2 % 4]
        chelo.append(dict(t=round(t_(b), 4), m=round(raiz(g) - 12 + R.choice([0, 7, 12]), 3), v=.7, dur=round(2 * BAR * .9, 4), tipo='arco'))
        if R.random() < .6: chelo.append(dict(t=round(t_(b + 1, 6), 4), m=round(raiz(g) - 12 + R.choice([3, 7, 10]), 3), v=.6, dur=.4, tipo='pizz'))
CODA_TAU = t_(FIN_CINTA)
# el río, el agua, los pájaros: en tiempo real, a lo largo de toda la pieza (el río suena más donde la vuelta es más cerrada)
for vu in VUELTAS:
    garganta.append(dict(tau=round(t_(vu['b0']), 4), dur_bars=vu['bars'], nota=TON - 24 + 7 * (vu['sinuosidad'] > 2.6), fonemas=['o' if vu['sinuosidad'] > 2.4 else 'u'], v=.3 + .2 * min(1, (vu['sinuosidad'] - 1.4) / 1.6), aprende=.2, ronco=0))

def a_real(e, tkey='t', dkey='dur', mkeys=('nota', 'm')):
    """un evento escrito en τ → tiempo real, transpuesto con la altura de la cinta en su instante"""
    x = dict(e); tau = e[tkey]; x['t'] = round(treal(tau), 4); x[dkey] = round(treal(tau + e[dkey]) - treal(tau), 4); x['tau'] = tau
    tr = 12 * math.log2(max(.05, vel(tau)))
    for mk in mkeys:
        if mk in x: x[mk] = round(x[mk] + tr, 3)
    return x
VIVA_R = [a_real(e) for e in viva]
CHELO_R = [a_real(e) for e in chelo]
GARGANTA_R = [dict(t=round(treal(g['tau']), 4), dur=round(treal(g['tau'] + g['dur_bars'] * BAR) - treal(g['tau']), 4), nota=round(g['nota'] + 12 * math.log2(vel(g['tau'] + 1)), 3),
                   fonemas=g['fonemas'], v=g['v'], aprende=g['aprende'], ronco=0) for g in garganta]
# la coda (en tiempo real): la antena
tc = T_FIN_CINTA + 3; vfin = vel(t_(VUELTAS[-1]['b0']) + 1); trf = 12 * math.log2(vfin)
for txt, mel, rit in (('se guir a pun tan do la an te na', [7, 7, 8, 7, 5, 3, 5, 3, 2], [.5, .5, .8, .5, .5, .8, .5, .5, 1.8]), ('a don de ya no con tes ta na die', [3, 3, 2, 0, 2, 0, -2, 0, 0, 0], [.5, .5, .5, .8, .5, .5, .8, .5, .8, 2.4])):
    for sy, m, d in zip(txt.split(), mel, rit): VIVA_R.append(dict(t=round(tc, 4), dur=round(d * .95, 4), texto=sy, nota=round(TON + m + trf, 3), coda=1)); tc += d
    tc += 1.2
for k in range(5): CHELO_R.append(dict(t=round(T_FIN_CINTA + 1 + 4.5 * k, 3), m=round(TON - 24 + trf + [0, 7, 3, 0, -2][k], 3), v=.6, dur=4.2, tipo='arco'))
agua += [dict(t=0.0, tipo='burbujeo', dur=round(DUR, 2), v=.35)] + [dict(t=round(treal(t_(VUELTAS[k]['b1'])) - .3, 3), tipo='ola', dur=6, v=.45) for k in CORTES]
for k in range(int(DUR / 9)):
    tt = R.uniform(0, DUR - 3); aves.append(dict(t=round(tt, 3), tipo=R.choice(['silbido', 'trino', 'chip']), m=R.choice([86, 88, 91, 93]), m2=R.choice([81, 84, 86]), dur=round(R.uniform(.3, 1.4), 3), v=round(R.uniform(.3, .6), 3), voz=k % 2))
LAGOS = [dict(vuelta=VUELTAS[k]['n'], tau0=round(t_(VUELTAS[k]['b1'] - 2), 4), tau1=round(t_(VUELTAS[k]['b1']), 4), t0=round(treal(t_(VUELTAS[k]['b1'] - 2)), 3), t1=round(treal(t_(VUELTAS[k]['b1'])), 3),
              sinuosidad=round(VUELTAS[k]['sinuosidad'], 3)) for k in CORTES]

partitura = dict(titulo='Lo que la cinta olvida', semilla=SEMILLA, terreno=f"traspuesta 26 «{TER['nombre']}», {TER['relieve']} m, {TER['anchoKm']} km, cauce de {TER['largoKm']:.1f} km",
                 tonica_cinta=TON, negra_cinta=Q, compas_cinta=BAR, T_tau=round(T_TAU, 3), duracion=round(DUR, 3), fin_cinta=round(T_FIN_CINTA, 3),
                 vueltas=[dict(n=vu['n'], b0=vu['b0'], b1=vu['b1'], frac=round(vu['frac'], 4), sinuosidad=round(vu['sinuosidad'], 3), v=round(vu['v'], 4), corte=bool(vu.get('corte')),
                               t0=round(treal(t_(vu['b0'])), 3), t1=round(treal(t_(vu['b1'])), 3)) for vu in VUELTAS],
                 intro=dict(b1=INTRO, t1=round(treal(t_(INTRO)), 3)), mapa=dict(tau=[round(float(x), 3) for x in TAU[::50]], t=[round(float(x), 3) for x in TR[::50]], v=[round(float(x), 4) for x in VV[::50]]),
                 curvatura=CURV, lagos=LAGOS, web=ev, requinto=requinto, chelo=CHELO_R, garganta=GARGANTA_R, agua=agua, aves=aves,
                 sabina=[dict(eventos=sonidero, nivel=.9, pan=0, capa='sonidero'), dict(eventos=coro, nivel=.9, pan=0, capa='coro'), dict(eventos=VIVA_R, nivel=.85, pan=0, capa='viva')],
                 coros=coros, cauce=[[round(a, 4), round(b, 4)] for a, b in P[::3]], inflexiones=[int(i) for i in INF], instrumentos='instrumentos-74126d437d07')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as f: json.dump(partitura, f, ensure_ascii=False)
    print('cinta', round(T_TAU, 1), 's (τ) →', round(T_FIN_CINTA, 1), 's reales · duración', round(DUR, 1), 's')
    for vu in partitura['vueltas']: print(f"  vuelta {vu['n']:2} compases {vu['b0']:3}–{vu['b1']:3} sinuosidad {vu['sinuosidad']:.2f} v {vu['v']:.2f} {'CORTE' if vu['corte'] else '     '} t {vu['t0']:6.1f}–{vu['t1']:6.1f}")
    print({k: len(v) for k, v in ev.items()}, '· requinto', len(requinto), '· chelo', len(CHELO_R), '· sonidero', len(sonidero), '· coro', len(coro), '· viva', len(VIVA_R), '· lagos', [(l['vuelta'], l['t0'], l['t1']) for l in LAGOS])
