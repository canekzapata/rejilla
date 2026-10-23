"""Catálogo de agua que habla — partitura (Messiaen × hyperpop). Semilla fija: misma semilla, misma pieza.

160 bpm, 64 compases (96 s), modo 2 de Messiaen (octatónico) sobre D. Capas en ciclos que no coinciden: marimba en 7 semicorcheas
(con valor añadido cada cuarta vuelta), mbira en 5, el tema del gamelán en un ritmo no retrogradable de 20 (3 5 2 | 2 5 3), canon
del gendér al doble de lento. Los tambores que hablan dicen la frase de Siringua: su ritmo y su entonación. Las aves cantan como en
un catálogo (mirlo, jilguero, llamados); el agua es percusión (gotas afinadas) y voz (Siringua). El hyperpop: 808, rachas de hats,
sidechain, la voz subida de tono y cortada, cortes glitch.
    python partitura.py <carpeta>     → <carpeta>/partitura.json
"""
import json, math, os, random, sys

SEMILLA = 1810
R = random.Random(SEMILLA)
BPM = 160; B = 60 / BPM; S = B / 4; BAR = 4 * B; COMPASES = 64
TON, MODO2 = 'D', [0, 1, 3, 4, 6, 7, 9, 10]            # D Eb F F# G# A B C
FRASE = 'el agua aprende a tocar tu nombre'
# las sílabas de la frase, con su acento (1 = tónica) y su duración en semicorcheas: así la «dicen» los tambores
SILABAS = [('el', 0, 1), ('a', 1, 2), ('gua', 0, 1), ('a', 0, 1), ('pren', 1, 2), ('de', 0, 1), ('a', 0, 1), ('to', 0, 1), ('car', 1, 2), ('tu', 0, 1), ('nom', 1, 2), ('bre', 0, 3)]
SEC = dict(A=(0, 8), B1=(8, 16), B2=(16, 24), C=(24, 40), D=(40, 48), E=(48, 60), F=(60, 64))


def bar(b, s=0): return b * BAR + s * S                 # compás b, semicorchea s
def en(sec, b): a, z = SEC[sec]; return a <= b < z
def sec_de(b): return next(k for k, (a, z) in SEC.items() if a <= b < z)
def g(o, k):                                            # grado k del modo 2 en la octava o (D = grado 0)
    n = len(MODO2); q, r = divmod(k, n); return 12 * (o + 1) + 2 + MODO2[r] + 12 * q


ev = {k: [] for k in ['marimba', 'mbira', 'saron', 'gender', 'gyil', 'berimbau', 'teponaztli', 'arpaboca', 'bateria', 'bateria-frito']}
def web(stem, t, ficha, midi=60, vel=.8, dur=.3, pan=0.0, **kw): ev[stem].append(dict(t=round(t, 5), ficha=ficha, midi=midi, vel=round(vel, 3), dur=dur, pan=pan, **kw))

# ── arpa de boca: la resonancia de D (Messiaen: «accord de résonance»). Pide armónicos 4 5 6 7 9 11 13 de D2 ──
ARM = {4: 62, 5: 66, 6: 69, 7: 72, 9: 76, 11: 80, 13: 82}
for b in range(0, 8, 1):                                 # A: sube por la resonancia, una nota larga por compás
    h = [4, 5, 6, 7, 6, 9, 7, 11][b]; web('arpaboca', bar(b), 'arpaboca', ARM[h], .7, BAR * .9, -.1)
for b in range(24, 40):                                  # C: lead que rebota en corcheas, como un sinte de hyperpop
    for k, h in enumerate([4, 7, 11, 7, 9, 13, 11, 6] if b % 2 == 0 else [4, 7, 9, 11, 13, 11, 9, 7]):
        web('arpaboca', bar(b, 2 * k), 'arpaboca', ARM[h], .62 + .15 * (k % 2 == 0), 2 * S * .8, -.1)
for b in range(40, 48, 2): web('arpaboca', bar(b), 'arpaboca', ARM[[5, 7, 9, 13][(b - 40) // 2]], .6, 2 * BAR * .9, -.1)
for b in range(48, 60):
    for k, h in enumerate([4, 11, 7, 13, 9, 11, 7, 5]): web('arpaboca', bar(b, 2 * k), 'arpaboca', ARM[h], .65, 2 * S * .8, -.1)
for k, h in enumerate([4, 5, 6, 7, 9, 11, 13]): web('arpaboca', bar(60) + k * B * .5, 'arpaboca', ARM[h], .55, BAR * 3, -.1)

# ── marimba: ostinato de 7 semicorcheas (valor añadido: cada cuarta vuelta dura 8) ──
t = bar(8); k = 0; vuelta = 0
OST7 = [0, 4, 2, 6, 3, 7, 5]
while t < bar(60):
    b = int(t // BAR)
    if not en('D', b) and b >= 8:
        web('marimba', t, 'marimba', g(3, OST7[k % 7]) + (12 if en('C', b) or en('E', b) else 0), .55 + .25 * (k % 7 == 0), .3, -.35)
    k += 1; t += S * (2 if (k % 7 == 0 and vuelta % 4 == 3) else 1)
    if k % 7 == 0: vuelta += 1
# ── mbira: ciclo de 5 en la octava 4, oscura (con sus chapitas) ──
for i in range(int((bar(60) - bar(8)) / S)):
    t = bar(8) + i * S; b = int(t // BAR)
    if en('D', b) or i % 2: continue
    web('mbira', t, 'mbira', g(4, [0, 2, 5, 1, 3][(i // 2) % 5]), .5 + .2 * ((i // 2) % 5 == 0), .4, .4)

# ── gamelán: el tema en ritmo no retrogradable 3 5 2 | 2 5 3 (20 semicorcheas); el gendér en canon al doble de lento ──
TEMA = [0, 3, 6, 7, 4, 1]; PAL = [3, 5, 2, 2, 5, 3]
def tema(stem, ficha, t0, t1, octava, aum, vel, pan):
    t, k = t0, 0
    while t < t1:
        b = int(t // BAR)
        if not en('D', b): web(stem, t, ficha, g(octava, TEMA[k % 6] + (k // 6) % 3), vel, PAL[k % 6] * S * aum, pan)
        t += PAL[k % 6] * S * aum; k += 1
tema('saron', 'saron', bar(16), bar(60), 4, 1, .62, -.5)
tema('gender', 'gender', bar(16) + 10 * S, bar(60), 3, 2, .55, .5)
for b in range(40, 48, 2):                              # D: el gendér sostiene el acorde de resonancia
    for k, n in enumerate([g(3, 0), g(3, 3), g(4, 1), g(4, 6)]): web('gender', bar(b, k), 'gender', n, .5, BAR * 1.8, .3)
for k, n in enumerate([g(2, 0), g(3, 0), g(3, 4), g(4, 1), g(4, 3), g(4, 6), g(5, 2)]): web('gender', bar(60) + k * S * 3, 'gender', n, .5, BAR * 3, (k - 3) * .2)
# ── gyil: golpes con zumbido en los contratiempos de los drops ──
for b in list(range(24, 40)) + list(range(48, 60)):
    for s in (3, 7, 10, 14): web('gyil', bar(b, s), 'gyil', g(4, [6, 3, 7, 1][s % 4]), .55, .2, .25)

# ── berimbau: toque de Angola en corcheas (chi chi DON din) desde B1 ──
for b in range(8, 60):
    if en('D', b): continue
    for m in range(2):
        t = bar(b, 8 * m)
        for dt, vel, gr in [(0, .3, 0), (2 * S, .3, 0), (4 * S, .85, 0), (6 * S, .85, 1)]: web('berimbau', t + dt, 'berimbau', g(3, gr), vel, .3, .15)
# ── teponaztli: dos lenguas, ritmo no retrogradable 2 3 5 3 2 (15) ──
t = bar(8); k = 0
while t < bar(60):
    if not en('D', int(t // BAR)): web('teponaztli', t, 'teponaztli', g(4, 0 if k % 5 in (0, 2, 4) else 3), .6, .3, -.2)
    t += [2, 3, 5, 3, 2][k % 5] * S; k += 1

# ── batería 808 (tr808 y frita) ──
for b in range(16, 60):
    s = sec_de(b)
    if s == 'D': continue
    if s == 'B2':
        for x in (0, 10): web('bateria', bar(b, x), 'bateria-tr808', 60, .95, .3, 0, pieza='kick')
        web('bateria-frito', bar(b, 8), 'bateria-frito', 60, .8, .3, 0, pieza='clap')
    else:
        for x in (0, 4, 8, 12): web('bateria', bar(b, x), 'bateria-tr808', 60, 1.0, .3, 0, pieza='kick')
        for x in (4, 12): web('bateria-frito', bar(b, x), 'bateria-frito', 60, .85, .3, 0, pieza='clap')
        racha = b % 4 == 3                                                    # rachas de hats al final de cada 4 compases
        for x in range(16):
            if racha and x >= 12:
                for j in range(3): web('bateria', bar(b, x) + j * S / 3, 'bateria-tr808', 60, .5 + .15 * j, .1, .2, pieza='hat')
            else: web('bateria', bar(b, x), 'bateria-tr808', 60, .7 if x % 2 == 0 else .45, .1, .2, pieza='hat')
        if b in (24, 48): web('bateria-frito', bar(b), 'bateria-frito', 60, 1.0, .3, 0, pieza='spray')
        for x in (2, 6, 10, 14): web('bateria', bar(b, x), 'bateria-tr808', 60, .4, .1, -.2, pieza='openhat') if b % 2 else None

# ── sub 808 (rejilla, esquinas): sigue al bombo, D1 con saltos ──
sub = []
for b in list(range(24, 40)) + list(range(48, 60)):
    for x, n in ((0, 26), (6, 26), (10, 38 if b % 2 else 29)): sub.append(dict(t=bar(b, x), midi=n, vel=.9, dur=3 * S))
for b in range(16, 24): sub.append(dict(t=bar(b), midi=26, vel=.8, dur=BAR * .6))

# ── tambores que hablan ──
def frase_tambor(t0):                                  # el dùndún dice la frase: tónicas agudas que caen, átonas graves
    out, t = [], t0
    for sil, ac, d in SILABAS:
        out.append(dict(t=t, midi=g(3, 3) if ac else g(3, 0), vel=.95 if ac else .6, habla=1.3 if ac else 1.08, sil=sil)); t += d * S * 2
    return out
dundun = []
for b in [9, 11, 13, 15, 17, 19, 21, 23, 25, 29, 33, 37, 49, 53, 57]: dundun += frase_tambor(bar(b))
tambor_habla = [dict(t=bar(b) + .05, texto=tx) for b, tx in [(12, 'el agua aprende'), (20, 'a tocar tu nombre'), (41, 'el agua aprende a tocar'), (44, 'tu nombre'), (46, 'tu nombre')]]

# ── aves: un catálogo (Messiaen). Mirlo: trinos y silbidos agudos; jilguero (jardín): trinos y gorjeos; llamados repetidos ──
aves_obj, aves_jardin = [], []
def frase_ave(t0, intensidad):
    t = t0
    for _ in range(R.randint(2, 4 + intensidad)):
        k = R.randint(0, 15); m = g(6, k % 8) + (12 if k > 12 else 0)
        if R.random() < .5: aves_obj.append(dict(t=t, tipo='trino', m=m, m2=g(6, (k + 2) % 8), dur=round(R.uniform(.25, .7), 3), rate=R.choice([18, 24, 30])))
        else: aves_obj.append(dict(t=t, tipo='silbido', m=m, m2=m + R.choice([-7, -4, 3, 5, 9]), dur=round(R.uniform(.12, .35), 3)))
        t += R.uniform(.18, .55)
    return t
for b in range(0, 64):
    s = sec_de(b)
    n = {'A': .7, 'B1': .35, 'B2': .35, 'C': .5, 'D': 1.0, 'E': .5, 'F': .8}[s]
    if R.random() < n: frase_ave(bar(b) + R.uniform(0, BAR * .5), 2 if s == 'D' else 0)
    if s in ('D', 'A', 'F') and R.random() < .6:
        aves_jardin.append(dict(t=bar(b) + R.uniform(.3, 1.2), ficha=R.choice(['jardin-ave-gorjeo', 'jardin-ave-llamado', 'jardin-ave-trino', 'jardin-ave-silbido']), midi=g(5, R.randint(0, 7)), vel=.6, dur=.4, pan=R.uniform(-.8, .8)))
    if s in ('C', 'E') and b % 2 == 1:                  # en los drops, llamados cuantizados a semicorcheas
        for x in (13, 14, 15): aves_jardin.append(dict(t=bar(b, x), ficha='jardin-ave-llamado', midi=g(6, 3), vel=.55, dur=.2, pan=.6))

# ── agua: burbujeo, olas, gotas afinadas como percusión, waterphone ──
agua = [dict(t=0.0, tipo='burbujeo', dur=BAR * 8, v=.7), dict(t=bar(40), tipo='burbujeo', dur=BAR * 8, v=.75), dict(t=bar(60), tipo='ola', dur=BAR * 4, v=.6)]
for b in range(8, 60):
    if sec_de(b) in ('B1', 'B2', 'C', 'E'):
        for x in (1, 5, 9, 11, 15) if b % 2 else (3, 7, 13):
            agua.append(dict(t=bar(b, x), tipo='gota', m=g(5, (b + x) % 8), v=.5))
waterphone = [dict(t=bar(0) + .2, tipo='arco', vara=3, dur=5.5, v=.6, agua=2, ola=.3), dict(t=bar(4), tipo='arco', vara=8, dur=5, v=.5, agua=2.5, ola=.4),
              dict(t=bar(40), tipo='arco', vara=5, dur=8, v=.5, agua=2, ola=.3), dict(t=bar(60), tipo='arco', vara=2, dur=6, v=.6, agua=3, ola=.5)]

# ── Siringua: la frase dicha (A, D) y en el drop subida de tono, cortada y repetida ──
siringua = [dict(t=bar(2), transponer=0, modo='entera'), dict(t=bar(42), transponer=0, modo='entera'),
            dict(t=bar(56), transponer=12, modo='entera')]
for b in range(24, 40, 2): siringua.append(dict(t=bar(b, 8), transponer=7, modo='corte', palabras=[1, 1, 1, 2] if b % 4 == 0 else [4, 6], paso=S))
for b in range(48, 56, 2): siringua.append(dict(t=bar(b, 8), transponer=12, modo='corte', palabras=[1, 2, 4, 6], paso=2 * S))

glitch = [31, 39, 47, 55]                               # al final de esos compases, la mezcla tartamudea

partitura = dict(titulo='Catálogo de agua que habla', semilla=SEMILLA, bpm=BPM, compases=COMPASES, duracion=COMPASES * BAR + 6, tonica=TON, escala=MODO2,
                 frase=FRASE, secciones=SEC, web=ev, sub=sub, dundun=dundun, tambor_habla=tambor_habla, aves_objeto=aves_obj, aves_jardin=aves_jardin,
                 agua=agua, waterphone=waterphone, siringua=siringua, glitch=glitch, instrumentos='instrumentos-48b8a06e1049')
if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    json.dump(partitura, open(os.path.join(out, 'partitura.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print({k: len(v) for k, v in ev.items()}, 'sub', len(sub), 'dùndún', len(dundun), 'aves', len(aves_obj) + len(aves_jardin), 'agua', len(agua), 'siringua', len(siringua))
