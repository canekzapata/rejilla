"""La voz principal hecha pájaro: un canto propio que persiste, recuerda y conversa.

Ver ../05-EL-PRINCIPAL-APRENDE-A-CANTAR.md (crítica y propuesta). Canek: «hacerlo pájaro»;
el agua «un poco más cantabile»; empezar por amanecer con la flauta.

El CANTO es corto y está escrito en grados de la escala del choque, no en Hz:
  ritmo     duraciones en dieciseisavos (al menos una larga)
  contorno  pasos de grado (sube y vuelve parcialmente)
  llegada   el último grado
Así atraviesa los cambios del muro: el mismo gesto, otras alturas.

Cada aparición tiene una FUNCIÓN (no se contesta todo):
  expone      el canto entero (la primera vez)
  insiste     casi intacto
  interrumpe  sólo el arranque
  amplía      el canto y un eco de su llegada
  calla       deja pasar
  contesta    (aprende) toma un rasgo de otra voz: el intervalo que devolvió el agua o el final del cenzontle
  aprende     (aprende) el final que regaló el cenzontle se queda en el canto: UN hueco de herencia;
              en cada aparición puede olvidarse (25 %), y alguna puede durar hasta el final
La frase escucha a la anterior: arranca cerca de donde llegó la última (o de la nota que
devolvió el agua, en «aprende»), en lugar de empezar donde caiga.
"""
import numpy as np


def grado_hz(escala, g):
    n = len(escala)
    o, i = divmod(int(g), n)
    return escala[i] * 2.0 ** o


def mas_cercano(escala, f):
    """El grado (con octava) más cercano a la frecuencia f."""
    mejor, gm = None, 0
    for o in range(-2, 3):
        for i, e in enumerate(escala):
            d = abs(np.log2(e * 2.0 ** o / f))
            if mejor is None or d < mejor:
                mejor, gm = d, i + o * len(escala)
    return gm


class Principal:
    def __init__(self, rng, modo, guarda=False, vericuetos=False, crecer=False):
        self.modo = modo
        self.vericuetos = vericuetos    # v1.8: el canto se tuerce a lo Monk, cada vez más con el tiempo
        self.crecer = crecer            # v1.8: el canto gana notas y sube de registro (florecer)
        self.historial = []
        self.guarda = guarda            # v2: no calla dos veces seguidas; un regalo no se tira si calla
        self.ultima_funcion = None
        for _ in range(50):           # un canto con cuerpo: al menos 3 grados de rango y que no regrese a su nota
            n = int(rng.integers(3, 5))
            ritmo = [int(rng.choice([4, 6, 8])) if k % 2 == 0 else int(rng.choice([2, 3])) for k in range(n)]
            pasos = [int(rng.choice([1, 2, 2, 3])) for _ in range(n - 2)]
            pasos.append(-int(rng.choice([1, 2])))                 # sube y vuelve parcialmente
            contorno = [0] + list(np.cumsum(pasos).tolist())
            if max(contorno) - min(contorno) >= 3 and contorno[-1] != 0:
                break
        self.canto = {"ritmo": ritmo, "contorno": contorno}
        self.herencia = None            # el final regalado: un paso de grado que reemplaza la llegada
        self.ultima_hz = None
        self.apariciones = 0

    def contorno_vigente(self):
        c = list(self.canto["contorno"])
        if self.herencia is not None:
            c[-1] = c[-2] + self.herencia
        return c

    def frase(self, rng, escala, inicio_hz=None, rasgo=None, progreso=0.0, gemela=None):
        """Devuelve (notas, funcion) con notas = [(paso16, hz, dur16, vel, adorno)]."""
        if not escala:
            return [], "calla"
        esc = [e for e in escala]
        self.apariciones += 1
        if self.apariciones == 1:
            funcion = "expone"
        else:
            opciones = ["insiste", "interrumpe", "amplia", "calla"]
            pesos = [0.45, 0.2, 0.15, 0.2]
            if self.guarda and self.ultima_funcion == "calla":
                pesos[-1] = 0.0
            if self.vericuetos and self.historial[-2:] == ["insiste", "insiste"]:
                pesos[0] = 0.0           # no más de dos «insiste» seguidos
            if self.modo == "aprende" and rasgo is not None:
                opciones += ["contesta"]
                pesos += [1.2 if rasgo.get("tipo") == "final" else 0.35]   # un final regalado casi siempre se contesta
            p = np.array(pesos) / sum(pesos)
            funcion = str(rng.choice(opciones, p=p))
        if self.modo == "aprende" and self.herencia is not None and rng.random() < 0.15:
            self.herencia = None         # se olvida
        self.ultima_funcion = funcion
        self.historial.append(funcion)
        if funcion == "calla":
            return [], funcion
        # de dónde arranca: cerca de donde llegó la última frase, o de lo que devolvió el agua
        ref = inicio_hz or self.ultima_hz
        g0 = mas_cercano(esc, ref) if ref else len(esc) // 2
        contorno = self.contorno_vigente()
        ritmo = list(self.canto["ritmo"])
        if funcion == "contesta" and rasgo is not None:
            if rasgo.get("tipo") == "final":
                contorno[-1] = contorno[-2] + rasgo["paso"]
                if rng.random() < 0.8:                  # lo que oyó deja consecuencia: lo aprende
                    self.herencia = rasgo["paso"]
                    funcion = "aprende"
            elif rasgo.get("tipo") == "intervalo":
                contorno = contorno[:-1] + [contorno[-2] + rasgo["paso"]]
        if funcion == "interrumpe":
            contorno, ritmo = contorno[:2], ritmo[:2]
        # florecer: el canto gana notas que siguen subiendo, más mientras avanza la pieza
        if self.crecer and progreso > 0.25:
            for k in range(int((progreso - 0.25) * 6)):
                contorno = contorno + [contorno[-1] + [2, 1, 2, -1][k % 4]]
                ritmo = ritmo + [[2, 4][k % 2]]
        # vericuetos a lo Monk: cada vez más probables con el tiempo; extraños, no tristes
        trucos, desplaza, silencio_en, corrida, arpa = [], 0, None, None, None
        if self.vericuetos and funcion not in ("expone",) and rng.random() < 0.15 + 0.75 * progreso:
            n_trucos = 1 + int(progreso > 0.5 and rng.random() < 0.5)
            nombres = ["desplaza", "ensancha", "secuencia", "invierte", "tonos", "silencio", "chafada", "arpa"]
            peso = np.array([1, 1, 1, 1, 1, 1, 1, 2.4]); peso = peso / peso.sum()   # el arpa, más seguido (Canek la pidió)
            for tr in rng.choice(nombres, n_trucos, replace=False, p=peso):
                tr = str(tr)
                trucos.append(tr)
                if tr == "desplaza":
                    desplaza = int(rng.choice([1, 3]))              # cae fuera de su lugar
                elif tr == "ensancha":
                    contorno = [2 * c for c in contorno]              # los saltos se abren
                elif tr == "secuencia":
                    base, rb, s = contorno[:3], ritmo[:3], int(rng.choice([1, 2]))
                    contorno = base + [c + s for c in base] + [c + 2 * s for c in base]
                    ritmo = [max(1, d // 2) for d in rb] * 2 + rb   # sube en escalones, y el último se estira
                elif tr == "invierte":
                    contorno = [-c for c in contorno]
                elif tr == "silencio":
                    silencio_en = 1                                   # un hueco a media frase
                elif tr == "arpa":
                    arpa = 1 if rng.random() < 0.7 else -1          # carrera rápida por la escala del choque (tan, arpa)
                elif tr == "tonos":
                    corrida = 1 if rng.random() < 0.6 else -1        # corridita de tonos enteros justos
        # toda la frase se mueve junta de octava: el contorno nunca se rompe
        fs = [grado_hz(esc, g0 + c) for c in contorno]
        piso = 250 + (300 * progreso if self.crecer else 0)          # florecer: el registro sube con el tiempo
        while max(fs) > 1300:
            fs = [f / 2 for f in fs]
        while min(fs) < piso and max(fs) * 2 <= 1300:
            fs = [f * 2 for f in fs]
        notas, t = [], desplaza
        for k, (f, d) in enumerate(zip(fs, ritmo)):
            vel = 0.9 if k == 0 else 0.8
            if "chafada" in trucos and d >= 4 and gemela is not None:
                g = gemela(f)
                if g:
                    notas.append((max(0, t - 0.4), g[0], 0.4, 0.5, "chafada"))
            notas.append((t, f, d, vel, "llegada" if k == len(fs) - 1 else None))
            t += d + (1 if d >= 4 else 0) + (3 if silencio_en == k else 0)
        if corrida:
            f = notas[-1][1]
            for r in (9 / 8, 10 / 9, 9 / 8):
                f = f * r if corrida > 0 else f / r
                notas.append((t, f, 1, 0.65, "corrida"))
                t += 1
        if arpa:
            # 6–12 notas en fusas por la escala del momento, cruzando una octava o más; casi siempre sube
            g = mas_cercano(esc, notas[-1][1])
            k = int(rng.integers(6, 13))
            fr = [grado_hz(esc, g + arpa * (j + 1)) for j in range(k)]
            while max(fr) > 1600:
                fr = [f / 2 for f in fr]
            while min(fr) < 250 and max(fr) * 2 <= 1600:
                fr = [f * 2 for f in fr]
            for j, f in enumerate(fr):
                notas.append((t, f, 0.5, 0.6 + 0.25 * j / k, "arpa"))
                t += 0.5
        if funcion == "amplia":
            f = notas[-1][1]
            notas.append((t + 2, f, 4, 0.55, "eco"))
        self.ultima_hz = notas[-1][1]
        if trucos:
            funcion = funcion + "+" + "+".join(trucos)
        return notas, funcion


def regalo_del_cenzontle(rng, canto_hz, escala):
    """El ave toma las dos primeras notas, las comprime y les pone un final propio (un paso
    de grado nuevo). Devuelve (notas_hz para el ave, rasgo para el principal)."""
    if len(canto_hz) < 2 or not escala:
        return None, None
    paso = int(rng.choice([-3, -2, 2, 3, 4]))
    g = mas_cercano(escala, canto_hz[1])
    final = grado_hz(escala, g + paso)
    return [canto_hz[0], canto_hz[1], final], {"tipo": "final", "paso": paso}
