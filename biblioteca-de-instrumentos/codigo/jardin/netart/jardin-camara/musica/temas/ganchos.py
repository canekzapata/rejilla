#!/usr/bin/env python3
"""Generador de temas v0 · ganchos sobre subarmónicos.

Lo que gustó del estudio 1 se queda: el acompañamiento subarmónico abajo (acordes
R/4, R/5, R/6, R/7 que baten, con bajo). Lo que no gustó se cambia: el gancho ya no
camina por segundas neutras ni lo toca una lengüeta. Ahora la semilla construye:

  materia   referencia R y un camino de 4 acordes subarmónicos que se enlazan por
            una nota compartida (R' = R·b/a, con a, b en 4…7)
  gancho    ritmo de células pegables + contorno en notas del acorde (saltos de tercera
            o más); el mismo contorno se reacomoda en cada acorde
  cuerpo    timbre del lead (fm, cuadrada, voz, sierra), tempo, swing y bombo

Un crítico rechaza los ganchos que se parecen al estudio 1: más de un paso menor a
230 cents seguido, ningún salto de quinta o rango menor a una octava.

Uso:  python ganchos.py [--semillas 7 23 47 99 1031 2026]
Escribe una carpeta NUEVA en ../estudios/ (nombre + hash de ejecución); nunca sobrescribe.
"""
import argparse, hashlib, json, secrets, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "estudio1"))
import afinidades as A  # síntesis de pad, bajo, batería, mezcla y medidas

SR = A.SR
PROGRAMA = "ganchos-subarmonicos-v0"
DIVISORES = (4, 5, 6, 7)

# células rítmicas de un compás (pasos de 16avo): sincopadas, con anticipaciones
CELULAS = [
    [0, 3, 6, 8, 12],
    [0, 2, 3, 6, 10, 12],
    [2, 4, 7, 10, 12],
    [0, 6, 8, 11, 14],
    [0, 4, 6, 10, 11],
    [3, 6, 8, 10, 14],
    [0, 3, 6, 10, 13],
    [0, 2, 6, 7, 10, 14],
]
PLANES = ["AAAB", "AABA", "ABAB", "AAAC", "ABAC"]
BOMBOS = [[0, 10], [0, 6, 10], [0, 7, 10], [0, 8, 11], [0, 3, 8, 10]]
TIMBRES = ["fm", "cuadrada", "voz", "sierra"]


# ---------------------------------------------------------------- materia
def acorde(R):
    return sorted(R / n for n in DIVISORES)


def bajo_de(R):
    """Raíz percibida de 10:12:15 (R/6, R/5, R/4) es R/6; el bajo va en 45–85 Hz."""
    b = R / 6
    while b > 85:
        b /= 2
    while b < 45:
        b *= 2
    return b


def camino(rng, R0, n=4):
    """Paseo de acordes subarmónicos enlazados por nota compartida que cierra en R0."""
    for _ in range(2000):
        Rs = [R0]
        for i in range(n - 1):
            a, b = rng.choice(DIVISORES, 2, replace=False)
            R = Rs[-1] * b / a
            if not (0.7 * R0 < R < 1.45 * R0) or any(abs(R / x - 1) < 1e-6 for x in Rs):
                break
            Rs.append(R)
        else:
            ultimo = Rs[-1]
            # el último tiene que compartir nota con el primero para que el ciclo cierre
            if any(abs(ultimo / a - R0 / b) < 1e-6 for a in DIVISORES for b in DIVISORES):
                return Rs
    raise RuntimeError("sin camino")


def compartida(R1, R2):
    for a in DIVISORES:
        for b in DIVISORES:
            if abs(R1 / a - R2 / b) < 1e-6:
                return R1 / a
    return None


def notas_lead(R, lo=290, hi=980):
    """Notas del acorde (y R/9 como color) en el registro del gancho."""
    s = set()
    for n in DIVISORES + (9,):
        f = R / n
        while f < lo:
            f *= 2
        while f <= hi:
            s.add(round(f, 6))
            f *= 2
    return sorted(s)


# ---------------------------------------------------------------- gancho
def contorno(rng, k):
    """Movimientos en la lista de notas del acorde: saltos de 1 a 3 lugares (≥ tercera)."""
    arquetipo = rng.choice(["arco", "pregunta", "zigzag", "cae-y-sube"])
    if arquetipo == "arco":
        base = [+1, +2, +1, -1, -2, -1, +1]
    elif arquetipo == "pregunta":
        base = [+2, -1, +2, +1, -3, +1, +2]
    elif arquetipo == "zigzag":
        base = [+2, -1, +2, -1, +2, -3, +1]
    else:
        base = [-2, -1, +3, +1, -2, +2, -1]
    movs = [int(m + rng.choice([-1, 0, 0, 0, 1])) or m for m in base[: k - 1]]
    return arquetipo, movs


def critico(frase):
    """Rechaza ganchos que repitan el problema del estudio 1."""
    hz = [f for _, f, _ in frase]
    cents = [1200 * np.log2(b / a) for a, b in zip(hz, hz[1:])]
    pasos = [abs(c) < 230 and abs(c) > 1 for c in cents]
    racha = mx = 0
    for p in pasos:
        racha = racha + 1 if p else 0
        mx = max(mx, racha)
    saltos = sum(abs(c) >= 690 for c in cents)
    rango = 1200 * np.log2(max(hz) / min(hz))
    ok = mx <= 1 and saltos >= 1 and rango >= 1150
    return ok, {"pasos_cortos_seguidos_max": mx, "saltos_de_quinta_o_mas": int(saltos),
                "rango_cents": round(float(rango)), "notas": len(hz)}


def gancho(rng, Rs):
    """Frase de 4 compases (uno por acorde). Devuelve [(paso_absoluto, hz, dur_pasos)]."""
    for intento in range(500):
        plan = rng.choice(PLANES)
        celdas = {c: CELULAS[i] for c, i in zip("ABC", rng.choice(len(CELULAS), 3, replace=False))}
        arq, movs = contorno(rng, max(len(c) for c in celdas.values()))
        inicio = rng.uniform(0.3, 0.6)
        frase = []
        for compas, (letra, R) in enumerate(zip(plan, Rs)):
            cel = celdas[letra]
            tonos = notas_lead(R)
            i = int(round(inicio * (len(tonos) - 1)))
            idx = [i]
            for m in movs[: len(cel) - 1]:
                idx.append(int(np.clip(idx[-1] + m, 0, len(tonos) - 1)))
            if letra != "A":                          # la B/C contesta: invierte el contorno
                idx = [int(np.clip(2 * idx[0] - j, 0, len(tonos) - 1)) for j in idx]
            for j, paso in enumerate(cel):
                sig = cel[j + 1] if j + 1 < len(cel) else 16
                dur = min(4, sig - paso) if j + 1 < len(cel) else min(4, 16 - paso)
                frase.append((compas * 16 + paso, tonos[idx[j]], max(1, dur)))
        ok, med = critico(frase)
        if ok:
            med.update({"plan": plan, "arquetipo": arq,
                        "celulas": {k: v for k, v in celdas.items() if k in plan}, "intentos": intento + 1})
            return frase, med
    raise RuntimeError("el crítico rechazó todo")


# ---------------------------------------------------------------- timbres del lead
def env(n, a, d, s, r):
    return A.env_adsr(n, a, d, s, r)


def lead(timbre, f, dur, rng, vel=1.0):
    n = int((dur + 0.25) * SR)
    t = np.arange(n) / SR
    if timbre == "fm":           # piano eléctrico oscuro: índice que se cierra
        idx = 0.4 + 2.2 * np.exp(-t / 0.18)
        x = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
        x += 0.25 * np.sin(2 * np.pi * 2 * f * t + 0.6 * idx * np.sin(2 * np.pi * 2 * f * t)) * np.exp(-t / 0.4)
        e = env(n, 0.004, 0.55, 0.35, 0.18)
    elif timbre == "cuadrada":   # pulso estrecho con filtro que baja
        fc = 900 + 2600 * np.exp(-t / 0.12)
        x = np.zeros(n)
        k = 1
        while f * k < 9000:
            a = np.sin(np.pi * k * 0.3) / k
            x += a / np.sqrt(1 + (f * k / fc) ** 4) * np.sin(2 * np.pi * f * k * t)
            k += 1
        e = env(n, 0.006, 0.2, 0.6, 0.08)
    elif timbre == "voz":        # vocal «o» redonda, sin vibrato de lengüeta
        x = np.zeros(n)
        vib = 1 + 0.002 * np.clip((t - 0.2) / 0.3, 0, 1) * np.sin(2 * np.pi * 4.6 * t)
        for k in range(1, 30):
            fk = f * k
            if fk > 7000:
                break
            g = (1 / k) * (A.formante(fk, 480, 0.3, 4) + A.formante(fk, 850, 0.25, 2.5)) / 6
            x += g * np.sin(2 * np.pi * np.cumsum(fk * vib) / SR + rng.uniform(0, 6))
        sos = butter(2, [300, 1200], btype="band", fs=SR, output="sos")
        x += 0.06 * sosfilt(sos, rng.standard_normal(n))
        e = env(n, 0.05, 0.3, 0.75, 0.15)
    else:                        # sierra con filtro que se abre y cierra (funk de los ochenta)
        fc = 500 + 2500 * np.exp(-t / 0.08)
        x = np.zeros(n)
        k = 1
        while f * k < 9000:
            res = 1 + 1.5 * np.exp(-0.5 * ((f * k - fc) / (0.25 * fc)) ** 2)
            x += res / k / np.sqrt(1 + (f * k / fc) ** 4) * np.sin(2 * np.pi * f * k * t)
            k += 1
        e = env(n, 0.004, 0.18, 0.5, 0.06)
    x = x / (np.max(np.abs(x)) + 1e-9)
    return vel * x * e


# ---------------------------------------------------------------- tema completo
def tema(semilla):
    rng = np.random.default_rng(semilla)
    R0 = float(rng.uniform(1150, 1650))
    Rs = camino(rng, R0)
    frase, med = gancho(rng, Rs)
    bpm = int(rng.choice([88, 96, 104, 112, 120]))
    swing = float(rng.choice([0.0, 0.08, 0.14]))
    bombo_p = BOMBOS[rng.integers(len(BOMBOS))]
    timbre = str(rng.choice(TIMBRES))
    beat = 60 / bpm
    step, bar = beat / 4, 4 * beat
    compases = 16
    total = compases * bar + 3
    P = {k: A.Pista(total) for k in ("bombo", "caja", "hats", "bajo", "pad", "lead", "brillo")}
    ev = {"bombos": [], "lead": [], "acordes": []}

    def hum(t, ms=3):
        return t + rng.normal(0, ms / 1000)

    for c in range(compases):
        R = Rs[c % 4]
        tc = c * bar
        ev["acordes"].append({"compas": c, "R": R, "pad_hz": acorde(R), "bajo_hz": bajo_de(R)})
        quiebre = c in (10, 11)
        intro = c < 2
        # pad subarmónico abajo, lo que gustó: batimiento por sección
        desaf = 1.4 if quiebre else 0.6
        for v in acorde(R):
            P["pad"].pon(tc, (0.75 if not intro else 0.5) * A.voz_pad(v, bar, rng, desaf, 1200))
        # bajo
        b = bajo_de(R)
        if quiebre or intro:
            P["bajo"].pon(tc, 0.8 * A.voz_bajo(b, 3.5 * beat, rng))
        else:
            for paso, mult, d, vel in [(0, 1, 3, 1.0), (6, 1, 2, 0.7), (8, 2, 1, 0.6), (10, 1, 2, 0.85), (14, 1, 1, 0.6)]:
                P["bajo"].pon(hum(tc + paso * step), vel * A.voz_bajo(b * mult, d * step, rng))
        # batería
        if quiebre:
            P["bombo"].pon(tc, 0.7 * A.bombo(rng))
            ev["bombos"].append(tc)
        elif not intro:
            for p in bombo_p:
                P["bombo"].pon(hum(tc + p * step, 2), A.bombo(rng))
                ev["bombos"].append(tc + p * step)
            for p in (4, 12):
                P["caja"].pon(hum(tc + p * step), (0.8 + 0.2 * rng.random()) * A.caja(rng))
        if not quiebre:
            for p in range(0, 16, 2):
                sw = swing * step if p % 4 == 2 else 0
                P["hats"].pon(hum(tc + p * step + sw), (1.0 if p % 4 == 2 else 0.55) * (0.6 + 0.4 * rng.random()) * A.hat(rng))

    # gancho: compases 2–9 (dos veces), fragmento en el quiebre, vuelta 12–15 una octava arriba
    def tocar(c0, notas, mult=1.0, vel=1.0):
        for paso, f, d in notas:
            sw = swing * step if paso % 4 == 2 else 0
            t = hum(c0 * bar + paso * step + sw)
            P["lead"].pon(t, vel * lead(timbre, f * mult, d * step, rng, 0.85 + 0.15 * rng.random()))
            ev["lead"].append({"t": t, "hz": f * mult, "dur": d * step})

    tocar(2, frase)
    tocar(6, frase)
    tocar(10, [n for n in frase if n[0] < 6], vel=0.8)
    tocar(12, frase, mult=2.0 if max(f for _, f, _ in frase) < 600 else 1.0)
    # cierre: el primer acorde sostenido y la primera nota del gancho
    tf = compases * bar
    for v in acorde(Rs[0]):
        P["pad"].pon(tf, 0.5 * A.voz_pad(v, 2.0, rng, 0.4, 1200))
    P["bajo"].pon(tf, 0.7 * A.voz_bajo(bajo_de(Rs[0]), 1.5, rng))
    P["lead"].pon(tf, lead(timbre, frase[0][1], 1.2, rng, 0.8))

    genoma = {"semilla": semilla, "R": Rs, "acordes_hz": [acorde(R) for R in Rs],
              "notas_compartidas": [compartida(Rs[i], Rs[(i + 1) % 4]) for i in range(4)],
              "bajos_hz": [bajo_de(R) for R in Rs], "bpm": bpm, "swing": swing, "bombo": bombo_p,
              "timbre": timbre, "gancho": [{"paso": p, "hz": round(f, 3), "dur": d} for p, f, d in frase],
              "critico": med}
    return P, ev, total, genoma


# ---------------------------------------------------------------- salida
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--semillas", type=int, nargs="*", default=[7, 23, 47, 99, 1031, 2026])
    ap.add_argument("--salida", default=str(Path(__file__).resolve().parent.parent / "estudios"))
    args = ap.parse_args()

    codigo = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    nonce = secrets.token_hex(16)
    sem = ",".join(map(str, args.semillas))
    ejec = hashlib.sha256((PROGRAMA + codigo + sem + nonce).encode()).hexdigest()
    corto = ejec[:12]
    carpeta = Path(args.salida) / f"ganchos-subarmonicos-{corto}"
    carpeta.mkdir(parents=False, exist_ok=False)
    tmp = Path(tempfile.mkdtemp(prefix="ganchos-"))
    reg = {"ejecucion_sha256": ejec, "nonce": nonce, "codigo_sha256": codigo, "programa": PROGRAMA,
           "semillas": args.semillas, "temas": {}}
    mezclas = []
    for s in args.semillas:
        P, ev, total, gen = tema(s)
        pistas = {k: p.x for k, p in P.items()}
        mix, stems = A.mezclar(pistas, ev, s)
        mix = mix[: int((total + 1.0) * SR)]
        wav = tmp / f"s{s}.wav"
        A.escribir_wav(wav, mix)
        dest = carpeta / f"gancho-s{s}-{corto}.m4a"
        A.m4a(wav, dest)
        rms = np.sqrt(np.mean(mix ** 2))
        mezclas.append(mix / rms * 0.12)
        gen["archivo"] = dest.name
        gen["contenido_sha256"] = hashlib.sha256(dest.read_bytes()).hexdigest()
        gen["duracion_s"] = round(len(mix) / SR, 2)
        gen["finito"] = bool(np.all(np.isfinite(mix)))
        gen["bandas"] = A.balance(mix)
        reg["temas"][str(s)] = gen
        c = gen["critico"]
        print(f"s{s}: {gen['timbre']:8s} {gen['bpm']} bpm  plan {c['plan']}  {c['arquetipo']:10s} "
              f"saltos {c['saltos_de_quinta_o_mas']}  pasos-cortos-seguidos {c['pasos_cortos_seguidos_max']}  "
              f"rango {c['rango_cents']}c  {gen['duracion_s']} s", flush=True)
    # todas seguidas, con un respiro de 1 s, para oírlas de corrido
    hueco = np.zeros((SR, 2))
    tejido = np.concatenate(sum([[m, hueco] for m in mezclas], [])[:-1])
    tejido = tejido / np.max(np.abs(tejido)) * 0.89
    wav = tmp / "tejido.wav"
    A.escribir_wav(wav, tejido)
    dest = carpeta / f"seis-ganchos-tejidos-{corto}.m4a"
    A.m4a(wav, dest)
    reg["tejido"] = {"archivo": dest.name, "contenido_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                     "orden": args.semillas}
    with open(carpeta / f"receta-{corto}.json", "x", encoding="utf-8") as fh:
        json.dump(reg, fh, ensure_ascii=False, indent=1)
    print(carpeta)


if __name__ == "__main__":
    main()
