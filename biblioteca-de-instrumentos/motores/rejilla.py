"""biblioteca de instrumentos · motor modal para rejilla (v2, loop 02: + motor «modal», los instrumentos de rejilla capturados).

Traduce una ficha a modos: valor(t) = amp · e^{-a t} · cos(2π f t + fase), el idioma de rejilla (Pista.modo en
research/rejilla/musica.py, que spectrumsynth escribe con fórmula cerrada). También los suma en el tiempo con numpy, para
pruebas y para quien no use spectrumsynth.

    import rejilla as I                       # desde la carpeta que fijó tomar.py
    K = I.ficha('marimba')                    # o json.load(...)
    I.a_pista(P, K, midi=62, t0=3.0, vel=.8, tonica='D', escala=[0,1,5,7,8])   # P = Pista de rejilla
    y = I.tiempo(I.modos(K, 62, 0.0, .8), 2.0, 44100)                          # o en el tiempo

Es una TRADUCCIÓN, no una copia muestra por muestra de Web Audio:
- exacto: parciales, caídas (la rampa exponencial de Web Audio a 1e-4 es una tasa a = ln(nivel/1e-4)/caída), pares desafinados
  del gamelán, afinación a oído, las dos lenguas, el armónico que elige la boca;
- aproximado con modos: el golpe de baqueta y el ruido del zumbido (racimos de modos sembrados en la banda), el zumbido recortado
  (armónicos sobre el pasa altos), el trémolo (bandas laterales), filtros (multiplican cada modo por |H(f)|), la boca (el deslizamiento en
  cuatro etapas que se relevan), la cabaça (filtro quieto en su punto medio);
- aproximado también: la saturación del eléctrico (función descriptiva de tanh sobre el total);
- se omite: el arranque alto de las lengüetas (shift).
Medido contra motores/web.js en pruebas/rejilla_contra_web.py.
"""
import json, math, os, random
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
NOTAS = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
FORMANTES = {'a': [800, 1200, 2500], 'e': [450, 1900, 2550], 'i': [300, 2200, 2950], 'o': [500, 900, 2400], 'u': [320, 750, 2350]}
PISO = 1e-4      # Web Audio baja las rampas exponenciales hasta aquí


def hz(m): return 440 * 2 ** ((m - 69) / 12)


def ficha(id_, carpeta=None):
    carpeta = carpeta or os.path.join(AQUI, '..', 'fichas')
    return json.load(open(os.path.join(carpeta, id_ + '.json'), encoding='utf-8'))


def pc_de(t): return t % 12 if isinstance(t, int) else max(0, NOTAS.index(t))


def lenguas(pc, escala, mid, cerca):
    iv = min([x for x in escala if x > 0] or [cerca], key=lambda x: abs(x - cerca))
    low = 12 + pc; d = (round(mid) - low) % 12
    return round(mid) - d + min([0, iv, 12], key=lambda x: abs(x - d))


def tasa(nivel, caida): return math.log(max(nivel, 2 * PISO) / PISO) / max(caida, 1e-4)


# Respuestas complejas de los filtros de Web Audio (prototipo analógico de los biquad RBJ). Ojo: en Web Audio la Q del pasa
# banda es lineal, pero la del pasa bajos y el pasa altos está en dB (por defecto 1 dB). En paralelo, las fases importan.
def Hbp(f, fc, q): s = 1j * f / fc; return (s / q) / (s * s + s / q + 1)
def Hlp(f, fc, qdb=1.0): q = 10 ** (qdb / 20); s = 1j * f / fc; return 1 / (s * s + s / q + 1)
def Hhp(f, fc, qdb=1.0): q = 10 ** (qdb / 20); s = 1j * f / fc; return s * s / (s * s + s / q + 1)
def bp(f, fc, q): return abs(Hbp(f, fc, q))
def lp(f, fc): return abs(Hlp(f, fc))
def hp(f, fc): return abs(Hhp(f, fc))


SENO = -math.pi / 2     # Web Audio arranca cada oscilador en seno, fase 0: en coseno es −π/2 (así los pares del gamelán baten igual)


def ruido_rms(fc, q, sr=44100):
    """rms del ruido uniforme ±1 (el buffer sembrado) tras un pasa banda RBJ: potencia 1/3 en el ancho equivalente π/2·fc/q."""
    return math.sqrt(min(1, (math.pi / 2) * (fc / q) / (sr / 2)) / 3)


def recorte(A, alto=.12, bajo=-.3, abajo=-.6, n=40):
    """Armónicos (1..n) de un seno de amplitud A pasado por la curva del zumbido (1 arriba de .12, −.6 abajo de −.3, 0 entre)."""
    x = A * np.sin(2 * np.pi * np.arange(4096) / 4096); y = np.where(x > alto, 1.0, np.where(x < bajo, abajo, 0.0))
    return np.abs(np.fft.rfft(y))[1:n + 1] * 2 / 4096


def _racimo(rng, fc, q, nivel, caida, t0, ny, n=28):
    """Ruido en banda como racimo de modos sembrados: ancho fc/q; `nivel` es el rms que tendría ese ruido."""
    ancho = fc / q; out = []
    for _ in range(n):
        f = fc + (rng.random() - .5) * ancho * 1.6
        if 30 < f < ny:
            g = nivel * bp(f, fc, q) * math.sqrt(2 / n)
            out.append(dict(f=f, amp=g, a=tasa(nivel, caida), t0=t0, ataque=2000, fase=rng.uniform(0, 2 * math.pi)))
    return out


def modos(K, midi, t0, vel, tonica='C', escala=(0, 2, 4, 7, 9), dur=.7, ny=20000):
    """Lista de modos {f, amp, a, t0, ataque, suelta, ar, fase} para una nota."""
    S, mot, v = K['fisica'], K['motor'], max(2e-4, vel)
    pc, escala = pc_de(tonica), list(escala)
    rng = random.Random(f"{K['id']}:{round(midi * 100)}")
    out = []
    if mot == 'golpe':
        mid = lenguas(pc, escala, midi, 5) if S.get('tongues') else midi
        f = hz(mid); sc = min(2.5, max(.3, (262 / f) ** S['dk'])); L = .3 * v * S['gain']
        cents = ((abs(math.sin(mid * 12.9898 + 7.233) * 43758.5453) % 1) * 2 - 1) * S['loose'] if S.get('loose') else 0
        # el bule o la caja va en paralelo con el sonido directo (suma compleja); el pasa bajos del eléctrico va en serie
        filtro = lambda x: abs((Hlp(x, S['lp']) if S.get('lp') else 1) * (1 + (S['body'][2] * Hbp(x, S['body'][0], S['body'][1]) if S.get('body') else 0)))
        for k, p in enumerate(S['parts']):
            r, g, d = p[:3]; at = p[3] if len(p) > 3 else .002
            ff = f * r * 2 ** ((cents * 1.6 if k else cents) / 1200); dd = d * sc
            if ff > ny: continue
            for dh in ([-S['pair'] / 2, S['pair'] / 2] if S.get('pair') else [0]):
                lv = g / (1.6 if S.get('pair') else 1); A = L * lv * filtro(ff + dh)
                base = dict(a=tasa(lv, dd), t0=t0, ataque=3 / at, fase=SENO)
                if S.get('trem'):                                   # trémolo = portadora + bandas laterales
                    rt, dp = S['trem']; m = dp / 2
                    out += [dict(base, f=ff + dh, amp=A * (1 - m)), dict(base, f=ff + dh + rt, amp=A * m / 2), dict(base, f=ff + dh - rt, amp=A * m / 2)]
                else:
                    out.append(dict(base, f=ff + dh, amp=A))
        if S.get('drive'):
            gd = 1 + S['drive'] * 6; tot = sum(m['amp'] for m in out) / L or 1
            for m in out:
                x = m['amp'] / L; y = math.tanh(gd * tot) / math.tanh(gd) * x / tot        # el total se comprime; cada modo conserva su parte
                m['amp'] = L * y; m['a'] *= min(1, (math.tanh(gd * tot) / math.tanh(gd)) / tot)
        if S.get('click'):
            cf, q, cg, cd = S['click']; out += _racimo(rng, min(cf, ny), q, L * cg * ruido_rms(min(cf, ny), q) * filtro(cf), cd, t0, ny)
        if S.get('buzz'):                                           # zumbido: armónicos del recorte sobre el pasa altos + ruido que sigue a la nota
            # la membrana pega mientras la barra vibra arriba del umbral: pulsos de altura fija que se cortan cuando la nota baja de .12
            amt, hpf = S['buzz']; g0, d0 = S['parts'][0][1], S['parts'][0][2] * sc; a1 = tasa(g0, d0); tb = max(.01, math.log(g0 / .12) / a1)
            c = recorte(g0 * .6)
            for k in range(1, 40):
                fk = f * k
                if fk > min(ny, 9000): break
                out.append(dict(f=fk, amp=L * amt * 1.4 * hp(fk, hpf) * c[k - 1], a=.3, t0=t0, ataque=1500, suelta=tb, ar=60, fase=SENO))
            ruido_medio = max(0, 2 * g0 * .5 / math.pi - .05)       # el ruido sigue al valor absoluto de la nota (media del rectificado)
            out += _racimo(rng, hpf * 1.8, 1.4, L * amt * 2.5 * ruido_rms(hpf * 1.8, 1.4) * ruido_medio * 2, d0, t0, ny)
    elif mot == 'boca':
        dm = 12 * (S['octava'] + 1) + pc
        while hz(dm) > S['maxHz']: dm -= 12
        while hz(dm) < S['minHz']: dm += 12
        f0 = hz(dm); h = round(hz(midi) / f0)
        while h > S['armonicos'][1]: h = round(h / 2)
        while h < S['armonicos'][0]: h *= 2
        ft = h * f0
        mejor = min(((abs(math.log(FORMANTES[vw][k] / ft)), vw, k) for vw in 'aeiou' for k in (0, 1)))
        hold = max(.25, dur); L = .3 * v * S['gain']
        xs = np.linspace(0, 2 * np.pi, 8192, endpoint=False); norma = float(np.abs(sum(np.sin(k * xs) / k ** S['brillo'] for k in range(1, 64))).max())
        desde = ft * 2 ** (S['deslizar'] if h % 2 else -S['deslizar'])
        boca = lambda t: ft + (desde - ft) * math.exp(-max(0, t - .005) / .035)      # setTargetAtTime: la boca llega deslizándose
        fuente = lambda t: .35 + .65 * math.exp(-math.log(1 / .35) / .2 * 2 * t)    # el golpe de la lengüeta y lo que sostiene

        tau = S['qBoca'] / (math.pi * ft)        # un resonador de Q alta tarda en llenarse: Q/(π·f) segundos

        def H(fk, fm, t=1.0):
            F = list(FORMANTES[mejor[1]]); F[mejor[2]] = fm
            return abs(sum((S['nivelBoca'] * (1 - math.exp(-t / tau)) if j == mejor[2] else S['nivelOtros']) * Hbp(fk, F[j], S['qBoca'] if j == mejor[2] else S['qOtros']) for j in range(3))
                       + S['cuerpo'] * Hlp(fk, f0 * 2.5))
        # El «boing»: la boca en camino, por etapas que se relevan (cada una suena con la boca a medio camino);
        # al final, la boca quieta sobre el armónico, sostenida hasta soltar.
        etapas = [(0, .02), (.02, .05), (.05, .1)]
        for k in range(1, 64):
            fk = k * f0
            if fk > ny: break
            A = L / k ** S['brillo'] / norma
            for a0, a1 in etapas:
                tm = (a0 + a1) / 2
                out.append(dict(f=fk, amp=A * H(fk, boca(tm), tm) * fuente(tm), a=.05, t0=t0 + a0, ataque=(2000 if a0 == 0 else 150), suelta=a1 - a0, ar=150, fase=SENO + 2 * math.pi * fk * a0))   # fase continua entre etapas
            Hq = H(fk, ft)
            out.append(dict(f=fk, amp=A * Hq * .65 * math.exp(-10.5 * .1), a=10.5, t0=t0 + .1, ataque=150, fase=SENO + 2 * math.pi * fk * .1))
            out.append(dict(f=fk, amp=A * Hq * .35, a=.05, t0=t0 + .1, ataque=150, suelta=hold - .1, ar=4, fase=SENO + 2 * math.pi * fk * .1))
    elif mot == 'arco':
        mid = lenguas(pc, escala, midi, S['cerca']); f = hz(mid); chiado = vel < S['chiado']
        sc = min(1.6, max(.5, (130 / f) ** .4)); L = .3 * v * S['gain']; c0, c1, ct, cq, cg = S['cabaca']
        for k in range(1, S['parciales'] + 1):
            fn = k * f * math.sqrt(1 + S['inarmonia'] * k * k)
            if fn > ny: break
            lv = abs(math.sin(k * math.pi * S['golpe'])) / k ** .55; d = (S['caidaChiado'] if chiado else S['caida']) / (1 + .12 * k) * sc
            # la cabaça se abre de c0 a c1 en ct segundos: la ganancia efectiva es el promedio de |seco + cg·H(t)|² pesado por la caída
            a_ = tasa(lv, d); ts = np.linspace(0, 3 / a_, 200); c = np.where(ts < ct, c0 * (c1 / c0) ** (ts / ct), c1)
            G = np.abs(S['seco'] + cg * np.array([Hbp(fn, ci, cq) for ci in c])) ** 2; w = np.exp(-2 * a_ * ts)
            out.append(dict(f=fn, amp=L * lv * math.sqrt(float((G * w).sum() / w.sum())), a=a_, t0=t0, ataque=1500, fase=SENO))
        Z = lambda fc, q, g, d, t: _racimo(rng, fc, q, L * g * ruido_rms(fc, q), d, t, ny)
        out += Z(2500, 1.5, .5, .012, t0)
        if chiado: out += Z(3400, 2, .7, .07, t0)
        out += Z(7000, 1.2, .22, .045, t0) + Z(7600, 1.2, .12, .035, t0 + .11)
    elif mot == 'modal':
        # capturado de rejilla: los modos que escribió la función en la nota de referencia más cercana, transportados
        refs = S['referencias']
        if 'golpe' in refs: ref, k = refs['golpe'], 1.0
        else:
            r = min(refs, key=lambda x: abs(int(x) - midi)); ref, k = refs[r], 2 ** ((midi - int(r)) / 12)
        g = vel / .8
        for m in ref['modos']:
            out.append(dict(m, f=m['f'] * k, amp=m['amp'] * g, t0=t0 + m['t0']))
        for sg in ref['segs']:
            out.append(dict(seg=True, B=complex(*sg['B']) * g, f=sg['f'] * k, a=sg['a'], ts=t0 + sg['ts'], te=None if sg['te'] is None else t0 + sg['te'], pan=sg['pan'], amp=abs(complex(*sg['B'])) * g))
    else:
        raise ValueError(f"el motor de rejilla no sabe tocar «{mot}» ({K['id']})")
    return [m for m in out if m['amp'] > 1e-6 and 20 < m['f'] < ny]


def a_pista(P, K, midi, t0, vel, pan=0.0, **kw):
    """Escribe la nota en una Pista de rejilla (Pista.modo: amp, a, ataque, suelta, ar, fase)."""
    for m in modos(K, midi, t0, vel, **kw):
        if m.get('seg'): P.seg(m['B'], m['f'], m['a'], m['ts'], m['te'], pan + m['pan']); continue
        P.modo(m['f'], m['amp'], m['t0'], m['a'], ataque=m.get('ataque'), suelta=m.get('suelta'), ar=m.get('ar'), pan=pan + m.get('pan', 0.0), fase=m['fase'])


def tiempo(ms, segundos, sr=44100, canal=None):
    """Suma los modos en el tiempo, con la misma envolvente que Pista.modo (e^{-at} − e^{-ataque·t}, normalizada al pico).
    canal=None: mono, sin paneo; canal 0/1: izquierdo/derecho con la ley de potencia constante de rejilla."""
    t = np.arange(int(segundos * sr)) / sr; y = np.zeros_like(t)
    for m in ms:
        g = 1.0 if canal is None else (math.cos, math.sin)[canal]((m.get('pan', 0.0) + 1) * math.pi / 4)
        if m.get('seg'):                             # un pedazo crudo de rejilla: Re(B·e^{(−a+2πif)(t−ts)}) entre ts y te
            ok = (t >= m['ts']) & (t < (m['te'] if m['te'] is not None else t[-1] + 1))
            if ok.any(): y[ok] += g * np.real(m['B'] * np.exp(complex(-m['a'], 2 * math.pi * m['f']) * (t[ok] - m['ts'])))
            continue
        u = t - m['t0']; ok = u >= 0
        if not ok.any(): continue
        a, at, uu = m['a'], m.get('ataque'), u[ok]
        env = np.exp(-a * uu)
        if at and at > a:
            tp = math.log(at / a) / (at - a); env = (env - np.exp(-at * uu)) / (math.exp(-a * tp) - math.exp(-at * tp))
        if m.get('suelta'):
            L = m['suelta']; tras = uu > L
            env[tras] = env[tras][0] * np.exp(-(m.get('ar') or 12) * (uu[tras] - L)) if tras.any() else env[tras]
        y[ok] += g * m['amp'] * env * np.cos(2 * math.pi * m['f'] * uu + m['fase'])
    return y
