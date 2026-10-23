"""Lo que el agua dibuja — PNGs de etapas y GIF del proceso.
    python proceso.py <carpeta-de-render> <carpeta-de-entrega> [--b 03,04]
01 las tierras malas 67: la cárcava mayor (Yucha Ka'nu), sus afluentes, los rayos y quien escucha en la boca · 02 el perfil de la
cárcava y cómo se ahonda tormenta tras tormenta (el eje de la derecha: la altura del slide) · 03 la guitarra camina la cárcava (la
curva de altura que le da la partitura) · 04 la lluvia de Xenakis: cada gota es una recta en altura–tiempo, como la partitura
gráfica de *Pithoprakta*; y sus velocidades contra Maxwell · 05 la lluvia, la crecida (el hidrograma) y los pedregones; los truenos
· 06 un redoble primo: la suma de los ceros de zeta y los golpes que suenan · 07 las capas solas · 08 la mezcla · GIF: la lámina,
el vidrio que baja la cárcava, la lluvia y el perfil que se hunde. Colores OKLCh sembrados (s67).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile
AQUI = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, AQUI); import sintes11 as S11
RUN, OUT = sys.argv[1], sys.argv[2]; P = json.load(open(os.path.join(OUT, 'partitura.json'), encoding='utf-8'))
h = os.path.basename(OUT).rsplit('-', 1)[1]; s = P['semilla']; pr = os.path.join(OUT, 'proceso')
B = sys.argv[sys.argv.index('--b') + 1].split(',') if '--b' in sys.argv else None
if B is None: os.makedirs(pr, exist_ok=False)
DUR = P['duracion']; SR = 48000; W = 1700; G = 360
fn = lambda n: ImageFont.truetype('C:/Windows/Fonts/consola.ttf', n)
def nuevo(nombre):
    if B is not None: nombre = nombre[:2] + 'b' + nombre[2:]
    p = os.path.join(pr, nombre); assert not os.path.exists(p); return p
def guardar(img, nombre):
    if B is None or nombre[:2] in B: img.save(nuevo(nombre))
def oklch(L, C, hdeg):
    a, b = C * math.cos(math.radians(hdeg)), C * math.sin(math.radians(hdeg))
    l_, m_, s_ = L + .3963377774 * a + .2158037573 * b, L - .1055613458 * a - .0638541728 * b, L - .0894841775 * a - 1.2914855480 * b
    l, m, s3 = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = (4.0767416621 * l - 3.3077115913 * m + .2309699292 * s3, -1.2684380046 * l + 2.6097574011 * m - .3413193965 * s3, -.0041960863 * l - .7034186147 * m + 1.7076147010 * s3)
    return tuple(int(255 * min(1, max(0, (12.92 * c if c <= .0031308 else 1.055 * c ** (1 / 2.4) - .055)))) for c in rgb)
ARC = 35 + (s * .7) % 20; AG = 215 + (s * 1.3) % 25
FONDO = oklch(.13, .025, ARC); TXT = oklch(.93, .03, ARC); TENUE = oklch(.6, .04, ARC); BARRO = oklch(.68, .13, ARC); AGUA = oklch(.76, .12, AG); RAYO = oklch(.9, .15, 95); CAL = oklch(.8, .1, ARC + 20)
SEC = {e['num']: (e['t'], e['t1']) for e in P['secciones']}
NOM = {'I': 'I ARCILLAS', 't1': 'tormenta', 'II': 'II LLUVIAS', 't2': 'tormenta', 'IIIr': 'III CÁRCAVAS (rap)', 'III': 'III', 't3': 'tormenta', 'IV': 'IV TIERRAS MALAS', 'V': "V YUCHA KA'NU"}
def secciones(d, x0, Wd, y0, y1):
    for k, (a, _) in SEC.items():
        xa = x0 + int(a / DUR * Wd); d.line([xa, y0, xa, y1], fill=oklch(.35, .04, ARC)); d.text((xa + 4, y0 + 2), NOM[k], font=fn(11), fill=AGUA if k.startswith('t') else TENUE)
C = P['carcava']; CU = np.array(C['u']); CV = np.array(C['v'])

# 01 · la lámina
H = np.fromfile(os.path.join(AQUI, 'terreno', 'h-67.f32'), dtype=np.float32).reshape(G, G); a = (H - H.min()) / np.ptp(H)
gy, gx = np.gradient(a); som = np.clip(.55 + 9 * (gx - gy), 0, 1)
img_m = (np.array(oklch(.18, .03, ARC))[None, None] + (som * (.35 + .65 * a))[..., None] * (np.array(oklch(.75, .1, ARC)) - np.array(oklch(.18, .03, ARC)))[None, None]).astype(np.uint8)
def lamina(lado, hasta_t=None, gotas_t=None, vidrio=None):
    im = Image.fromarray(img_m).resize((lado, lado)); d = ImageDraw.Draw(im)
    d.line([(u * lado, v * lado) for u, v in zip(CU, CV)], fill=AGUA, width=3)
    for af in C['afluentes']:
        k = min(len(CU) - 1, int(af['en'] / C['largo_m'] * len(CU))); x, y = CU[k] * lado, CV[k] * lado; d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=CAL, width=2)
    bx, by = C['boca']['u'] * lado, C['boca']['v'] * lado; d.ellipse([bx - 8, by - 8, bx + 8, by + 8], outline=TXT, width=3)
    if gotas_t is not None:
        for g in P['gotas']:
            if gotas_t - .6 <= g['t'] <= gotas_t:
                k = min(len(CU) - 1, g['i'] // 4); x, y = CU[k] * lado + np.sin(g['t'] * 997) * 30, CV[k] * lado + np.cos(g['t'] * 991) * 30; d.point([(x, y)], fill=AGUA); d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=AGUA)
    if vidrio is not None:
        k = min(len(CU) - 1, int(vidrio / C['largo_m'] * len(CU))); x, y = CU[k] * lado, CV[k] * lado; d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=BARRO, outline=TXT)
    return im, d
img = Image.new('RGB', (W, 760), FONDO); im, _ = lamina(700); img.paste(im, (20, 40)); d = ImageDraw.Draw(img)
d.text((14, 10), f"01  tierras malas 67 de Traspuesta ({P['terreno'].split(', ', 2)[2]}): la cárcava mayor, Yucha Ka'nu, {C['largo_m']} m de {C['z_cabecera']:.0f} a {C['z_boca']:.0f} m", font=fn(15), fill=TXT)
for r in P['rayos']:
    x0, y0 = 20 + r['u'] * 700, 40 + r['v'] * 700; d.line([x0 - 8, y0 - 14, x0 + 2, y0, x0 - 4, y0, x0 + 6, y0 + 14], fill=RAYO, width=2)
x1 = 760
d.text((x1, 60), 'la historia de la lámina = la forma de la canción:', font=fn(14), fill=TXT)
for k, hh in enumerate(P['historia'] + ["YUCHA KA'NU (la boca)"]): d.text((x1 + 10, 86 + 22 * k), f'{"I II III IV V".split()[k]:>4}  {hh.lower()}', font=fn(13), fill=BARRO)
d.text((x1, 220), f"afluentes (los riffs de la guitarra): {len(C['afluentes'])}", font=fn(14), fill=CAL)
for k, af in enumerate(C['afluentes']): d.text((x1 + 10, 244 + 19 * k), f"en {af['en']:6.0f} m · {af['largo']:5} m de largo · cae {af['baja']:4.1f} m = {af['baja'] / C['m_por_semitono']:4.1f} semitonos", font=fn(12), fill=TENUE)
d.text((x1, 400), 'los rayos (quien escucha está en la boca, el círculo):', font=fn(14), fill=RAYO)
for k, r in enumerate(P['rayos']): d.text((x1 + 10, 424 + 19 * k), f"{r['tormenta']}  {r['lugar'].lower():<26} {r['dist_m']:>5} m → el trueno tarda {r['retraso_s']:5.1f} s", font=fn(12), fill=TENUE)
d.text((x1, 560), f"la tónica: la cárcava como tubo abierto, 343 / (2 · {C['largo_m']} m) × 2^{P['octavas_arriba']} = {440 * 2 ** ((P['tonica'] - 69) / 12):.2f} Hz", font=fn(13), fill=TXT)
d.text((x1, 584), f"el slide: un semitono cada {C['m_por_semitono']:.0f} m de altitud; la boca, en la tónica (una octava arriba)", font=fn(13), fill=TXT)
guardar(img, f'01-lamina-y-carcava-s{s}-{h}.png')

# 02 · el perfil que se ahonda
img = Image.new('RGB', (W, 580), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f"02  el perfil de Yucha Ka'nu y cómo lo ahonda la lluvia (dz/dt = −K Q^½ S, implícito desde la boca, fija; exagerado: lo más hondo, {P['carcava']['hunde']['V']['hondo_max_m']:.0f} m)", font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 70, 50, W - 200, 440; zmin, zmax = C['z_boca'] - 4, C['z_cabecera'] + 3
X = lambda dd: x0 + dd / C['largo_m'] * Wd; Y = lambda z: y0 + (zmax - z) / (zmax - zmin) * Hd
nP = len(C['perfiles_cada_4']['I']); dd = np.linspace(0, C['largo_m'], nP)
for j, (k, zz) in enumerate(C['perfiles_cada_4'].items()):
    col = oklch(.85 - .12 * j, .12, ARC + j * 40) if j else TXT; d.line([(X(a_), Y(z)) for a_, z in zip(dd, zz)], fill=col, width=3 if j in (0, 4) else 1)
    d.text((X(dd[nP // 4 + 18 * j]) + 6, Y(zz[nP // 4 + 18 * j]) - 16), {'I': 'virgen (I)', 'II': 'tras la 1ª tormenta', 'IIIr': 'tras la 2ª', 'IV': 'tras la 3ª', 'V': 'en la boca (V)'}[k], font=fn(11), fill=col)
for af in C['afluentes']: d.line([X(af['en']), y0 + Hd, X(af['en']), y0 + Hd - 12], fill=CAL, width=2)
for j, (k, n) in enumerate(C['nudos'].items()): d.line([X(n['x_m']), y0 + Hd, X(n['x_m']), y0 + Hd + 8 + 14 * j], fill=AGUA); d.text((X(n['x_m']) + 4, y0 + Hd + 4 + 14 * j), f"{k}: el vidrio se hunde {n['cae_st']:.1f} st", font=fn(11), fill=AGUA)
for m_ in range(int(P['tonica'] + 12), int(P['tonica'] + 32), 2):
    z = C['z_boca'] + (m_ - P['tonica'] - 12) * C['m_por_semitono']
    if zmin <= z <= zmax: d.text((x0 + Wd + 10, Y(z) - 6), f'{z:5.0f} m  midi {m_}', font=fn(10), fill=TENUE)
d.text((x0, y0 + Hd + 50), 'distancia desde la cabecera (m) →  · marcas: las juntas de los afluentes · abajo: cuánto se hundió el vidrio en cada tormenta', font=fn(11), fill=TENUE)
guardar(img, f'02-perfil-que-se-ahonda-s{s}-{h}.png')

# 03 · la guitarra camina la cárcava
cu = P['guitarra']['cuerdas'][0]; curva = np.array(cu['curva']); fr = P['guitarra']['fr']
img = Image.new('RGB', (W, 480), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f"03  la guitarra de cárcava: la altura del vidrio (midi) a lo largo de la canción; {len(cu['pulsos'])} púas; en las tormentas se queda donde más excava y se hunde", font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 60, 50, W - 120, 360; lo, hi = curva.min() - 1, curva.max() + 1
tt = np.arange(len(curva)) / fr; Xt = lambda t: x0 + t / DUR * Wd; Ym = lambda m: y0 + (hi - m) / (hi - lo) * Hd
paso = max(1, len(curva) // 6000); d.line([(Xt(t), Ym(m)) for t, m in zip(tt[::paso], curva[::paso])], fill=BARRO, width=1)
for t, v in cu['pulsos'][::2]: d.ellipse([Xt(t) - 1.5, Ym(np.interp(t, tt, curva)) - 1.5, Xt(t) + 1.5, Ym(np.interp(t, tt, curva)) + 1.5], fill=TXT)
d.line([Xt(0), Ym(P['tonica'] + 12), Xt(DUR), Ym(P['tonica'] + 12)], fill=TENUE); d.text((Xt(DUR) - 160, Ym(P['tonica'] + 12) + 3), 'la boca = la tónica', font=fn(11), fill=TENUE)
secciones(d, x0, Wd, y0 + Hd + 8, y0 + Hd + 40)
guardar(img, f'03-guitarra-camina-s{s}-{h}.png')

# 04 · la lluvia de Xenakis
img = Image.new('RGB', (W, 640), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f"04  la lluvia de Xenakis: {len(P['gotas'])} gotas, cada una una recta altura–tiempo (como la partitura gráfica de Pithoprakta); color: pizz, arco, col legno", font=fn(14), fill=TXT)
gs = P['gotas']; m0s = np.array([g['m0'] for g in gs]); lo, hi = m0s.min() - 4, m0s.max() + 4
TCOL = {'pizz': AGUA, 'arco': BARRO, 'col': RAYO}
lo, hi = 38, 114
for fila, k in enumerate(('t1', 't2', 't3')):
    a0, z0 = SEC[k][0], SEC[k][1] + 4; x0 = 20 + fila * 380; Wd, Hd, y0 = 360, 440, 60
    d.text((x0, 40), f'{k}  ({len([g for g in gs if a0 <= g["t"] < z0])} gotas)', font=fn(12), fill=TXT)
    pan = Image.new('RGB', (Wd, Hd), FONDO); dp = ImageDraw.Draw(pan)
    for g in gs:
        if not (a0 <= g['t'] < z0): continue
        xa = (g['t'] - a0) / (z0 - a0) * Wd; xb = (g['t'] + g['dur'] - a0) / (z0 - a0) * Wd
        ya = (hi - g['m0']) / (hi - lo) * Hd; yb = (hi - (g['m0'] + g['v'] * g['dur'])) / (hi - lo) * Hd
        dp.line([xa, ya, xb, yb], fill=TCOL[g['toque']], width=1)
    img.paste(pan, (x0, y0)); d.rectangle([x0, y0, x0 + Wd, y0 + Hd], outline=oklch(.3, .03, ARC))
x0, y0, Wd, Hd = 1180, 80, 480, 300; w = np.array([abs(g['v']) / g['temp'] for g in gs]); hb, eb = np.histogram(w, 30, (0, 3), density=True)
for k, hv in enumerate(hb): d.rectangle([x0 + k * Wd / 30, y0 + Hd - hv / 1.0 * Hd, x0 + (k + 1) * Wd / 30 - 2, y0 + Hd], fill=AGUA)
xx = np.linspace(0, 3, 200); mw = 4 / math.sqrt(math.pi) * xx ** 2 * np.exp(-xx ** 2)
d.line([(x0 + x / 3 * Wd, y0 + Hd - m / 1.0 * Hd) for x, m in zip(xx, mw)], fill=RAYO, width=3)
d.text((x0, y0 - 24), '|v| / a de cada gota contra Maxwell, 4/√π · w² e^(−w²)', font=fn(12), fill=TXT)
d.text((x0, y0 + Hd + 10), 'la «temperatura» a sube con la tormenta: 3 → 18 semitonos/s', font=fn(12), fill=TENUE)
d.text((20, 540), 'midi 38 (abajo) a 114 (arriba) · altura de cada gota al caer = la altura del terreno donde cae, dos octavas arriba (cabecera aguda, boca grave); 70% bajan', font=fn(12), fill=TENUE)
guardar(img, f'04-lluvia-xenakis-s{s}-{h}.png')

# 05 · la lluvia, la crecida y los truenos
Hh = json.load(open(os.path.join(RUN, 'hidrograma.json'))); Q = np.array(Hh['Q']); I = np.array(P['lluvia']['intensidad']); tasa = np.array(Hh['tasa']); frh = Hh['fr']
img = Image.new('RGB', (W, 440), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), '05  la lluvia (gotas/s), el caudal en la boca (hidrograma gamma) y los pedregones (crecen como (Q − Qc)^3/2); los rayos y cuándo llega su trueno', font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 60, 50, W - 120, 300; tq = np.arange(len(Q)) / frh; Xt = lambda t: x0 + t / DUR * Wd
d.line([(Xt(t), y0 + Hd - i / I.max() * Hd) for t, i in zip(tq, I)], fill=AGUA, width=2)
d.line([(Xt(t), y0 + Hd - q * Hd) for t, q in zip(tq, Q)], fill=BARRO, width=3)
d.line([(Xt(t), y0 + Hd - q / max(tasa.max(), 1e-9) * Hd * .6) for t, q in zip(tq, tasa)], fill=CAL, width=1)
for r in P['rayos']:
    d.line([Xt(r['relampago']), y0, Xt(r['relampago']), y0 + 30], fill=RAYO, width=2); d.line([Xt(r['relampago']), y0 + 15, Xt(r['llega']), y0 + 15], fill=RAYO)
    d.text((Xt(r['llega']) + 3, y0 + 2 + 14 * (P['rayos'].index(r) % 3)), f"{r['lugar'].lower()} {r['retraso_s']:.0f} s", font=fn(10), fill=RAYO)
d.text((x0 + 10, y0 + Hd - 40), 'azul: la lluvia · barro: el caudal · claro: los pedregones', font=fn(11), fill=TENUE)
secciones(d, x0, Wd, y0 + Hd + 8, y0 + Hd + 40)
guardar(img, f'05-crecida-y-truenos-s{s}-{h}.png')

# 06 · un redoble primo
picos, info = S11.picos_primos(72)
sys.path.insert(0, os.path.join(AQUI, '..', 'ceros-que-tocan-primos')); import ceros_primos as CP
u = np.arange(math.log(1.8), math.log(72) + .02, 2e-4); sm = CP.suma(u, CP.GAMMA[-1] * 1.0001)
img = Image.new('RGB', (W, 420), FONDO); d = ImageDraw.Draw(img)
d.text((14, 10), f"06  los redobles del drill: −2 Σ cos(γ u) con 2000 ceros de zeta; {len(picos)} picos detectados en la suma caen en {info['encontradas']} de las {info['potencias_de_primos']} potencias de primo ≤ 72", font=fn(14), fill=TXT)
x0, y0, Wd, Hd = 60, 50, W - 120, 200; Xu = lambda uu: x0 + (uu - u[0]) / (u[-1] - u[0]) * Wd
smn = (sm - np.median(sm)) / (np.abs(sm).max() + 1e-9)
d.line([(Xu(uu), y0 + Hd / 2 - v * Hd / 2) for uu, v in zip(u[::3], smn[::3])], fill=AGUA, width=1)
for uu, hh in picos: d.ellipse([Xu(uu) - 3, y0 + 4, Xu(uu) + 3, y0 + 10], fill=RAYO)
for n in (2, 3, 4, 5, 7, 8, 9, 11, 13, 16, 17, 19, 23, 25, 27, 29, 31, 32, 37, 41, 43, 47, 49, 53, 59, 61, 64, 67, 71): d.text((Xu(math.log(n)) - 6, y0 + Hd + 4), str(n), font=fn(10), fill=TENUE)
r0 = P['redobles'][0]; y1 = y0 + Hd + 40
d.text((x0, y1), f"un redoble en la canción ({'ida: accelerando' if r0['ida'] else 'vuelta: ritardando hacia el tiempo fuerte'}, {r0['D']:.2f} s): los golpes son esos picos, en el tiempo", font=fn(12), fill=TXT)
for g in S11.redoble(r0['t'], r0['D'], picos, r0['ida']): xg = x0 + (g['t'] - r0['t']) / r0['D'] * Wd; d.line([xg, y1 + 30, xg, y1 + 30 + 60 * g['v']], fill=BARRO, width=3)
guardar(img, f'06-redobles-primos-s{s}-{h}.png')

# 07 · capas solas, 08 · mezcla
def leer(n, est):
    x = np.fromfile(os.path.join(RUN, n + '.f32'), dtype=np.float32); return x.reshape(-1, 2).mean(1) if est else x
def espectro(x, alto, f0=40, f1=10000, hop=8192):
    n = 8192; fr_ = np.fft.rfftfreq(n, 1 / SR); win = np.hanning(n); cols = []
    for i in range(0, len(x) - n, hop): cols.append(np.abs(np.fft.rfft(x[i:i + n] * win)))
    S = np.array(cols).T; fl = np.geomspace(f0, f1, alto); M = np.array([np.interp(fl, fr_, c) for c in S.T]).T
    M = 20 * np.log10(M / (M.max() + 1e-12) + 1e-9); return np.clip((M + 70) / 70, 0, 1)[::-1]
def pinta(M, col): return (M[..., None] * np.array(col)[None, None, :] + (1 - M[..., None]) * np.array(FONDO)[None, None, :]).astype(np.uint8)
CAPAS = [('guitarra', 1), ('pulgar', 1), ('lluvia', 1), ('arco', 1), ('col-legno', 1), ('trueno', 1), ('crecida', 1), ('pedregones', 1), ('viento', 1), ('hats', 1), ('bajo808', 0),
         ('bateria808', 1), ('sabina-lead', 1), ('sabina-respuesta', 1), ('sabina-rap', 1), ('sabina-chops', 1), ('sabina-rio', 1)]
alto = 26; x0 = 170; im = Image.new('RGB', (W, 50 + (alto + 4) * len(CAPAS)), FONDO); d = ImageDraw.Draw(im)
d.text((14, 10), '07  las capas solas antes de mezclar', font=fn(14), fill=TXT)
for k, (c, st) in enumerate(CAPAS):
    col = oklch(.78, .13, ARC + (AG + 360 - ARC) * k / len(CAPAS)); y0 = 44 + k * (alto + 4)
    im.paste(Image.fromarray(pinta(espectro(leer(c, st), alto), col)).resize((W - x0 - 10, alto)), (x0, y0)); d.text((8, y0 + 7), c, font=fn(11), fill=col)
guardar(im, f'07-capas-s{s}-{h}.png')
sr, x = wavfile.read(os.path.join(OUT, os.path.basename(OUT) + '.wav')); x = x.astype(np.float32).mean(1) / 32768
mez = Image.new('RGB', (W, 400), FONDO); mez.paste(Image.fromarray(pinta(espectro(x, 330, 30, 12000), oklch(.92, .05, ARC))).resize((W - 20, 330)), (10, 50)); d = ImageDraw.Draw(mez)
d.text((14, 10), f'08  Lo que el agua dibuja (s{s}): la mezcla, {len(x) / sr:.0f} s', font=fn(18), fill=TXT); secciones(d, 10, W - 20, 44, 385)
guardar(mez, f'08-mezcla-s{s}-{h}.png')

# GIF: la lámina, el vidrio que baja, la lluvia y el perfil que se hunde
TR = P['tramos_guitarra']
def vidrio_en(t):
    for a_, z_, da, db in TR:
        if a_ <= t < z_: return da + (db - da) * (t - a_) / (z_ - a_)
    return None
cuadros = []; NC = 34
for j in range(1, NC + 1):
    t = DUR * j / NC; c = Image.new('RGB', (W, 800), FONDO); im, _ = lamina(390, gotas_t=t, vidrio=vidrio_en(t)); c.paste(im, (20, 6)); dd_ = ImageDraw.Draw(c)
    rot = [NOM[k] for k, (a_, z_) in SEC.items() if a_ <= t][-1]; dd_.text((440, 26), rot if not rot.startswith('torm') else 'LLUEVE: XENAKIS', font=fn(30), fill=AGUA if rot.startswith('torm') else TXT)
    k = [kk for kk in C['perfiles_cada_4'] if SEC[kk][0] <= t]; zz = C['perfiles_cada_4'][k[-1] if k else 'I']
    x0, y0, Wd, Hd = 440, 90, 1200, 280; zmin, zmax = C['z_boca'] - 4, C['z_cabecera'] + 3
    dd_.line([(x0 + a_ / C['largo_m'] * Wd, y0 + (zmax - z) / (zmax - zmin) * Hd) for a_, z in zip(np.linspace(0, C['largo_m'], len(zz)), C['perfiles_cada_4']['I'])], fill=TENUE, width=1)
    dd_.line([(x0 + a_ / C['largo_m'] * Wd, y0 + (zmax - z) / (zmax - zmin) * Hd) for a_, z in zip(np.linspace(0, C['largo_m'], len(zz)), zz)], fill=BARRO, width=3)
    vd = vidrio_en(t)
    if vd is not None:
        zv = np.interp(vd, np.linspace(0, C['largo_m'], len(zz)), zz); xv, yv = x0 + vd / C['largo_m'] * Wd, y0 + (zmax - zv) / (zmax - zmin) * Hd; dd_.ellipse([xv - 7, yv - 7, xv + 7, yv + 7], fill=TXT)
    c.paste(mez, (0, 400)); xx = 10 + int((W - 20) * t / DUR); dd_.rectangle([xx, 450, W - 10, 780], fill=FONDO); dd_.line([xx, 450, xx, 780], fill=TXT, width=2)
    cuadros.append(c.resize((1100, 518)))
gif = os.path.join(OUT, f'lo-que-el-agua-dibuja-s{s}-{h}.gif'); cuadros[0].save(gif, save_all=True, append_images=cuadros[1:] + [cuadros[-1]] * 2, duration=270, loop=0, optimize=True)
cuadros[-1].save(nuevo(f'09-lamina-y-mezcla-s{s}-{h}.png'))
if B is None and os.path.exists(os.path.join(RUN, 'sondas.json')):
    json.dump(json.load(open(os.path.join(RUN, 'sondas.json'), encoding='utf-8')), open(os.path.join(OUT, 'sondas.json'), 'x', encoding='utf-8'), ensure_ascii=False, indent=1)
print(gif, os.path.getsize(gif) // 1024, 'KB')
