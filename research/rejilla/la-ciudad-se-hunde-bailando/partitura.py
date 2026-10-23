"""La ciudad se hunde bailando — partitura. Cumbiatón chilango: cumbia rebajada × dembow × sonidero × electrónica, con la radio
de onda corta (a lo *Hymnen*), sobre el campo de conos 769 de Traspuesta (como la Sierra de Santa Catarina o el Xitle). Diseño en
DISENO.md.

LO REBAJADO ES EL HUNDIMIENTO. La Ciudad de México se hunde porque se le saca el agua al lago de abajo. La canción va de 1900 a 2026:
cada metro que se hunde el centro rebaja el disco 0.4 semitonos (tempo y tono juntos, como bajarle la velocidad a la tornamesa). La
curva es APROXIMADA, del orden de lo medido en el centro histórico (casi nada a principios de siglo, lo más rápido a mediados, unos
9 m al final). Cada metro, la sirena del sonidero.
DOS RELOJES: la música del disco (96 bpm en «tiempo de disco») se rebaja con el varispeed; el MC, las sirenas, los ecos y la radio
van en tiempo real (no se rebajan: son en vivo).
EL ECO DEL VALLE: el MC está en el Cerro de los Lagos; sus saludos rebotan en los conos vecinos con su distancia real (343 m/s).
LA TÓNICA: la altura media de los conos sobre su base, como tubo (f = c/2h), subida por octavas.
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys
import numpy as np
from scipy.ndimage import maximum_filter, minimum_filter, gaussian_filter

SEMILLA = 769
R = random.Random(SEMILLA)
AQUI = os.path.dirname(os.path.abspath(__file__)); GG = 360; SR = 48000
TER = json.load(open(os.path.join(AQUI, 'terreno', 'terreno-769.json'), encoding='utf-8'))
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-769.f32'), dtype=np.float32).reshape(GG, GG).astype(float)
m_de = lambda f: 69 + 12 * math.log2(f / 440)
fT = lambda m: 440 * 2 ** ((m - 69) / 12)

# ── la lámina: los conos, sus alturas, sus nombres; el MC en el Cerro de los Lagos ──
km = TER['anchoKm'] * 1000 / (GG - 1); hs = gaussian_filter(H, 2)
pk = (hs == maximum_filter(hs, 15)) & (hs > np.percentile(hs, 85)); base = minimum_filter(hs, 41)
CONOS = [dict(u=round(x / (GG - 1), 4), v=round(y / (GG - 1), 4), alto_m=round(float((hs[y, x] - base[y, x]) * TER['relieve']), 1)) for y, x in zip(*np.nonzero(pk))]
nombres = [n for n in TER['nombres'] if n['clase'] == 'cumbre']
for c in CONOS:
    n = min(nombres, key=lambda n: (n['u'] - c['u']) ** 2 + (n['v'] - c['v']) ** 2); dd = math.hypot(n['u'] - c['u'], n['v'] - c['v']) * TER['anchoKm'] * 1000
    c['nombre'] = n['nombre'] if dd < 400 else None
MC = next((c for c in CONOS if c['nombre'] == 'EL CERRO DE LOS LAGOS'), max(CONOS, key=lambda c: c['alto_m']))
for c in CONOS: c['dist_m'] = round(math.hypot(c['u'] - MC['u'], c['v'] - MC['v']) * TER['anchoKm'] * 1000)
ECOS = sorted([c for c in CONOS if c is not MC], key=lambda c: c['dist_m'])[:5]
ECOS = [dict(c, retraso_s=round(c['dist_m'] * 2 / 343, 3)) for c in ECOS]                       # ida y vuelta
H_MEDIA = float(np.mean([c['alto_m'] for c in CONOS])); f = 343 / (2 * H_MEDIA); octv = 0
while f < 55: f *= 2; octv += 1
TON = m_de(f)
LUGARES = [n['nombre'] for n in TER['nombres'] if n['clase'] in ('cumbre', 'lago', 'hondonada', 'especial')]

# ── los dos relojes ──
BPM = 96; NEGRA = 60 / BPM; COMPAS = 4 * NEGRA; S16 = NEGRA / 4
SEC = {}; p0 = 0.0
ANIOS = {'I': (1900, 1930), 'II': (1930, 1950), 'III': (1950, 1970), 'IV': (1970, 2010), 'V': (2010, 2026)}
for nom, nb in (('I', 12), ('II', 14), ('III', 16), ('IV', 18), ('V', 10)): SEC[nom] = (round(p0, 4), round(p0 + nb * COMPAS, 4)); p0 += nb * COMPAS
P_DUR = p0                                                                                        # duración del disco (tiempo de disco)
HUNDE = [[1900, 0], [1930, .5], [1940, 1.2], [1950, 2.8], [1960, 5.0], [1970, 6.6], [1990, 7.6], [2010, 8.5], [2026, 9.0]]   # m, aproximado
def anio_de(p):
    for k, (a, z) in SEC.items():
        if a <= p <= z: y0, y1 = ANIOS[k]; return y0 + (y1 - y0) * (p - a) / (z - a)
    return 2026
def hunde(anio): return float(np.interp(anio, [a for a, _ in HUNDE], [b for _, b in HUNDE]))
SEMI_POR_M = .4
def razon(p): return 2 ** (-SEMI_POR_M * hunde(anio_de(p)) / 12)
T0 = 22.0                                                                                         # el intro de radio (tiempo real) antes del disco
pp = np.linspace(0, P_DUR, 20001); rr = np.array([razon(x) for x in pp]); tau = T0 + np.concatenate([[0], np.cumsum(np.diff(pp) / ((rr[1:] + rr[:-1]) / 2))])
def real(p): return float(np.interp(p, pp, tau))                                                 # tiempo real de una posición del disco
FIN_DISCO = real(P_DUR); DUR = round(FIN_DISCO + 12, 3)                                           # 12 s de radio al final
VARISPEED = [[round(float(a), 4), round(float(b), 4)] for a, b in zip(pp[::50], tau[::50])]

ESCALA = [0, 2, 3, 5, 7, 8, 10]
def gr(g, o=0): k, r = divmod(int(g), 7); return TON + 12 * (o + k) + ESCALA[r]
ANDALUZ = [[0, 3, 7], [-2, 2, 5], [-4, 0, 3], [-5, -1, 2]]                                      # i – VII – VI – V
def acorde(b): return ANDALUZ[b % 4]
def ts(sec, b, s=0.0): return SEC[sec][0] + b * COMPAS + s * S16

# ═════════ el disco (tiempo de disco) ═════════
web = {k: [] for k in ['guiro', 'conga', 'campana', 'shaker', 'bateria808', 'bateria-frito']}
def w(stem, t, ficha, midi=60, vel=.8, dur=.2, pan=0.0, **kw): web[stem].append(dict(t=round(t, 5), ficha=ficha, midi=round(midi, 3), vel=round(vel, 3), dur=round(dur, 4), pan=pan, **kw))
bajo, teclado = [], []
def cumbia(sec, b0, b1, fuerza=1.0):
    for b in range(b0, b1):
        t = ts(sec, b); ac = acorde(b)
        for s in range(0, 16, 4): w('guiro', t + s * S16, 'meleeviewer-13-guiro', 60, .7 * fuerza, NEGRA * .45, .2); w('guiro', t + (s + 2) * S16, 'meleeviewer-13-guiro', 60, .45 * fuerza, S16 * .7, .2); w('guiro', t + (s + 3) * S16, 'meleeviewer-13-guiro', 60, .45 * fuerza, S16 * .7, .2)
        for s, m, v in ((0, 55, .7), (4, 64, .8), (7, 67, .6), (8, 55, .7), (12, 64, .8), (14, 67, .6), (15, 67, .5)): w('conga', t + s * S16 + R.gauss(0, .004), 'meleeviewer-13-conga', m, v * fuerza, .2, -.3)
        for s in (0, 4, 6, 8, 12): w('campana', t + s * S16, 'meleeviewer-13-campana', 72, (.55 if s != 6 else .35) * fuerza, .15, .35)
        for s in range(0, 16, 2): w('shaker', t + s * S16, 'meleeviewer-2-shaker', 60, (.3 if s % 4 else .4) * fuerza, .08, .45)
        for s, x, d in ((0, ac[0], 3), (6, ac[2] - 12, 1.5), (8, ac[0], 3), (14, ac[2] - 12, 1.5)): bajo.append(dict(t=round(t + s * S16, 4), dur=round(d * S16, 4), m=round(TON - 12 + x, 3), v=.85))
def dembow(sec, b0, b1, frito=False):
    for b in range(b0, b1):
        t = ts(sec, b)
        for s in (0, 4, 8, 12): w('bateria808', t + s * S16, 'bateria-tr808', 60, .95, .2, 0, pieza='kick')
        for s in (3, 6, 11, 14): w('bateria808', t + s * S16, 'bateria-tr808', 60, .8, .2, .05, pieza='snare')
        for s in range(0, 16, 2): w('bateria808', t + s * S16, 'bateria-tr808', 60, .35, .1, .3, pieza='hat')
        if frito:
            for s in (3, 11): w('bateria-frito', t + s * S16 + .01, 'bateria-frito', 60, .5, .2, -.1, pieza='clap')
        if b % 4 == 3:
            k, tt = 0, t + 12 * S16
            while tt < t + COMPAS - .01: w('bateria808', tt, 'bateria-tr808', 60, .35 + .5 * k / 14, .1, .05, pieza='snare'); tt += S16 / 2 * (.96 ** k); k += 1
RIFF = [(0, 4, 2), (2, 2, 1), (3, 1, 1), (4, 2, 2), (6, 0, 2), (8, 4, 2), (10, 5, 1), (11, 4, 1), (12, 2, 2), (14, 1, 2)]   # (16avo, grado, dur) — el riff del teclado
def riff(sec, b0, b1, o=1, adorno=False):
    for b in range(b0, b1):
        t = ts(sec, b); sube = 2 if b % 4 == 2 else 0
        for s, g, d in RIFF:
            teclado.append(dict(t=round(t + s * S16, 4), dur=round(d * S16 * .95, 4), m=round(gr(g + sube, o), 3), v=.7))
            if adorno and s in (3, 11) and R.random() < .6: teclado.append(dict(t=round(t + (s + .5) * S16, 4), dur=round(S16 * .45, 4), m=round(gr(g + sube + 1, o), 3), v=.55))
cumbia('I', 0, 12, .9); riff('I', 4, 12)
cumbia('II', 0, 14); riff('II', 0, 14); dembow('II', 6, 14)
cumbia('III', 0, 16); dembow('III', 0, 16, frito=True); riff('III', 8, 16, adorno=True)
cumbia('IV', 0, 18); dembow('IV', 0, 18, frito=True); riff('IV', 0, 18, o=1, adorno=True); riff('IV', 8, 16, o=2, adorno=True)
cumbia('V', 0, 10, .8); dembow('V', 0, 6); riff('V', 2, 10)
TALBOT = dict(loop_desde=round(ts('II', 8), 4), ciclo=round(2 * COMPAS, 4), tramos=[[ts('III', 4), '1/3'], [ts('III', 8), '1/2'], [ts('III', 12), '0']])

# las voces del disco (Sabina, se rebajan con el disco)
lead, coro, chops = [], [], []; coros = {v: [] for v in 'SATB'}
def frase(dest, texto, t, alturas, ritmo, legato=.92, **kw):
    for k, sy in enumerate(texto.split()):
        d = ritmo[k % len(ritmo)] * S16; dest.append(dict(t=round(t, 4), dur=round(d * legato, 4), texto=sy, nota=round(alturas[k % len(alturas)], 3), **kw)); t += d
    return t
CORO = [('la ciu dad se hun de bai lan do', [gr(4, 2), gr(4, 2), gr(3, 2), gr(2, 2), gr(1, 2), gr(2, 2), gr(1, 2), gr(0, 2)], [2, 2, 2, 2, 4, 2, 2, 8]),
        ('y no se va a pa rar', [gr(0, 2), gr(1, 2), gr(2, 2), gr(2, 2), gr(1, 2), gr(0, 2), gr(-1, 2)], [2, 2, 2, 2, 2, 2, 12])]
def coro_en(sec, b):
    t = ts(sec, b)
    for txt, alt, rit in CORO:
        frase(coro, txt, t, alt, rit)
        for v, x in zip('SATB', (0, -3, -7, None)): frase(coros[v], txt, t, [a + x if x is not None else TON + 12 for a in alt], rit)
        t += 2 * COMPAS
for sec, b in (('I', 8), ('II', 10), ('IV', 4), ('IV', 14), ('V', 4)): coro_en(sec, b)
V1 = [('don de hu bo un la go a ho ra hay pi so', [gr(2, 2), gr(2, 2), gr(3, 2), gr(4, 2), gr(4, 2), gr(3, 2), gr(2, 2), gr(2, 2), gr(1, 2), gr(2, 2), gr(1, 2), gr(0, 2)], [2, 2, 2, 2, 2, 4, 2, 2, 2, 2, 2, 8]),
      ('y el pi so se a cuer da del a gua', [gr(0, 2), gr(1, 2), gr(2, 2), gr(2, 2), gr(3, 2), gr(4, 2), gr(3, 2), gr(2, 2), gr(1, 2), gr(0, 2)], [2, 2, 2, 2, 2, 4, 2, 2, 2, 10])]
V2 = [('ca da a ño bai la mos más a ba jo', [gr(4, 2), gr(4, 2), gr(5, 2), gr(4, 2), gr(3, 2), gr(3, 2), gr(2, 2), gr(1, 2), gr(1, 2), gr(0, 2), gr(-1, 2)], [2, 2, 2, 4, 2, 2, 2, 2, 2, 2, 8]),
      ('y la can ción se po ne más es pe sa', [gr(0, 2), gr(0, 2), gr(1, 2), gr(2, 2), gr(2, 2), gr(1, 2), gr(1, 2), gr(0, 2), gr(-1, 2), gr(-1, 2), gr(-2, 2)], [2, 2, 2, 4, 2, 2, 2, 2, 2, 2, 10])]
for k, (txt, alt, rit) in enumerate(V1): frase(lead, txt, ts('II', 2 + 4 * k), alt, rit)
for k, (txt, alt, rit) in enumerate(V2): frase(lead, txt, ts('IV', 8 + 3 * k), alt, rit)
for b in range(0, 18):
    if b % 4 in (1, 3):
        for s, sy, x in ((2, 'hun', 7), (3, 'de', 5), (10, 'bai', 3), (11, 'lan', 5), (12, 'do', 0)):
            if R.random() < .75: chops.append(dict(t=round(ts('IV', b, s), 4), dur=round(S16 * .85, 4), texto=sy, nota=round(TON + 31 + x, 3)))

# ═════════ en vivo (tiempo real): el MC, las sirenas, la radio ═════════
mc = []
def dice(texto, t, base, inflex=(0, 0, 2, 0, -1, 0, 3, 0), sil=.13):
    for k, sy in enumerate(texto.split()): mc.append(dict(t=round(t + k * sil, 4), dur=round(sil * .9, 4), texto=sy, nota=round(base + inflex[k % len(inflex)], 3)))
    return t + len(texto.split()) * sil
MCB = TON + 19                                                                                   # el MC habla alrededor de una quinta arriba de la octava
dice('es to es so ni do tex co co', 15.0, MCB, (0, 0, 2, 4, 2, 0, 5, 3, 0))                      # por la radio, antes de que entre el disco
NUM = {1900: 'mil no ve cien tos', 1930: 'mil no ve cien tos trein ta', 1950: 'mil no ve cien tos cin cuen ta', 1970: 'mil no ve cien tos se ten ta', 2010: 'dos mil diez'}
for sec, (a, _) in ANIOS.items(): dice(NUM[a], real(SEC[sec][0]) + .2, MCB + 2)
SALUDOS = ['sa lu dos pa to da la gen te del ' + (n.lower().replace('el ', '', 1) if n.lower().startswith('el ') else n.lower()) for n in LUGARES[:9]]
def silabear(s):
    import re
    out = []
    for p in s.split():
        out += re.findall(r'[^aeiouáéíóú]*[aeiouáéíóú]+(?:[^aeiouáéíóú]*$|[^aeiouáéíóú](?=[^aeiouáéíóú]))?', p) or [p]
    return ' '.join(out)
for k, s in enumerate(SALUDOS):                                                                  # III y IV: saludos a los lugares de la lámina
    sec, b = ('III', 2 + 3 * k) if k < 4 else ('IV', 1 + 3 * (k - 4))
    dice(silabear(s), real(ts(sec, b)), MCB, sil=.12)
for sec, b in (('III', 15), ('IV', 7), ('IV', 17)): dice('a ba jo a ba jo', real(ts(sec, b, 8)), MCB + 3, (0, 0, 2, 0, 0, 2), .17)
sirenas = []; m_ant = 0
for p in np.linspace(0, P_DUR, 4000):
    m = int(hunde(anio_de(p)))
    if m > m_ant: sirenas.append(dict(t=round(real(p), 3), dur=2.4, f0=420, f1=1150, pan=round(R.uniform(-.6, .6), 2), metro=m)); m_ant = m
radio_voz = []
dice_r = lambda txt, t, b: [radio_voz.append(dict(t=round(t + k * .14, 4), dur=.125, texto=sy, nota=round(b + (2 if k % 5 == 2 else 0), 3))) for k, sy in enumerate(txt.split())]
dice_r('a quí ra dio va lle el pro nós ti co llu via en el o rien te', 1.0, TON + 17)
dice_r('a vi so la ciu dad ba jó o tro cen tí me tro', real(ts('III', 8)) + .5, TON + 17)
dice_r('se a cer ca la tor men ta', FIN_DISCO + 2, TON + 17)
CANCIONES = ['la-duna-que-canta/la-duna-que-canta-s675-bdb5c6908d35/la-duna-que-canta-s675-bdb5c6908d35.m4a',
             'cuento-en-siete/cuento-en-siete-s1910-052e69cc9507/cuento-en-siete-s1910-052e69cc9507.m4a',
             'el-coral-que-no-se-deja-hundir/el-coral-que-no-se-deja-hundir-s2-392be7657db0/el-coral-que-no-se-deja-hundir-s2-392be7657db0.m4a',
             'catalogo-agua-que-habla/catalogo-agua-que-habla-s1810-9e95611d123f/catalogo-agua-que-habla-s1810-9e95611d123f.m4a']
ESTACIONES = [dict(f=6.8, tipo='musica', fuente=CANCIONES[0], desde=40.0, nivel=.8), dict(f=8.4, tipo='voz', nivel=1.0),
              dict(f=9.7, tipo='horaria', nivel=.6), dict(f=11.1, tipo='musica', fuente=CANCIONES[1], desde=60.0, nivel=.8),
              dict(f=12.6, tipo='musica', fuente=CANCIONES[2], desde=150.0, nivel=.7), dict(f=13.9, tipo='musica', fuente=CANCIONES[3], desde=20.0, nivel=.8),
              dict(f=15.2, tipo='sonidero', nivel=1.0)]
i3 = real(ts('III', 8))
RADIO = dict(intro=dict(desde=0, hasta=T0 + 1.5, dial=[[0, 6.0], [3, 6.8], [5, 6.85], [7, 8.0], [9, 8.4], [10.5, 8.42], [11.5, 9.7], [12.5, 9.72], [13.5, 11.1], [14.3, 12.0], [15.0, 15.2], [T0 + 1.5, 15.2]]),
             interludio=dict(desde=round(i3 - .3, 3), hasta=round(i3 + 6.5, 3), dial=[[0, 15.2], [1.2, 12.6], [2.6, 12.62], [3.6, 8.4], [5.2, 8.42], [6.8, 15.2]]),
             final=dict(desde=round(FIN_DISCO - 6, 3), hasta=DUR, dial=[[0, 15.2], [5, 15.2], [9, 16.5], [12, 13.9], [15, 13.92], [18, 17.5]]),
             estaciones=ESTACIONES)

for _l in (lead, coro, chops, mc, radio_voz): _l.sort(key=lambda e: e['t'])                       # Sabina los quiere en orden (el MC se arma por partes)
partitura = dict(titulo='La ciudad se hunde bailando', semilla=SEMILLA, terreno=f"traspuesta 769, {TER['nombre']}, {TER['anchoKm']} km, {TER['relieve']} m",
                 conos=CONOS, mc_en=MC, ecos=ECOS, lugares=LUGARES, altura_media_conos_m=round(H_MEDIA, 1), octavas_arriba=octv, tonica=round(TON, 3),
                 bpm=BPM, compas=COMPAS, dieciseisavo=S16, secciones=[dict(num=k, t=v[0], t1=v[1], anios=ANIOS[k], t_real=round(real(v[0]), 3), t1_real=round(real(v[1]), 3)) for k, v in SEC.items()],
                 hundimiento_m=HUNDE, semitonos_por_metro=SEMI_POR_M, disco_s=P_DUR, inicio_disco=T0, fin_disco=round(FIN_DISCO, 3), duracion=DUR, varispeed=VARISPEED,
                 razon_final=round(razon(P_DUR), 4), web=web, bajo=bajo, teclado=teclado, talbot=TALBOT, sirenas=sirenas, radio=RADIO,
                 sabina=[dict(eventos=lead, nivel=.9, pan=0, capa='lead'), dict(eventos=coro, nivel=.85, pan=0, capa='coro'), dict(eventos=chops, nivel=.85, pan=0, capa='chops'),
                         dict(eventos=mc, nivel=.95, pan=0, capa='mc'), dict(eventos=radio_voz, nivel=.9, pan=0, capa='radio')],
                 coros=coros, instrumentos=None)
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    inst = [d for d in os.listdir(AQUI) if d.startswith('instrumentos-')]; partitura['instrumentos'] = inst[0] if inst else None
    with open(os.path.join(out, 'partitura.json'), 'x', encoding='utf-8') as fo: json.dump(partitura, fo, ensure_ascii=False)
    print('duración real', DUR, 's · disco', round(P_DUR, 1), 's → real', round(FIN_DISCO - T0, 1), 's · razón final', round(razon(P_DUR), 4), f'({-SEMI_POR_M * 9:.1f} semitonos)')
    print('tónica', round(TON, 2), f'({fT(TON):.2f} Hz: conos de {H_MEDIA:.0f} m como tubo × 2^{octv}) · {len(CONOS)} conos · MC en', MC['nombre'])
    print('ecos', [(e['nombre'], e['dist_m'], e['retraso_s']) for e in ECOS])
    print('sirenas', [(s['metro'], s['t']) for s in sirenas]); print('lugares', LUGARES)
    print('secciones (real)', [(s, round(real(a), 1), round(real(z), 1)) for s, (a, z) in SEC.items()])
    print('web', {k: len(v) for k, v in web.items()}, '· bajo', len(bajo), '· teclado', len(teclado), '· mc', len(mc), '· coro', len(coro), '· lead', len(lead), '· chops', len(chops), '· radio', len(radio_voz))
