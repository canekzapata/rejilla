"""El laberinto armónico de «sobre la aurora».

Las 24 tríadas mayores y menores viven en el Tonnetz: cada una tiene tres vecinas a las que
se llega moviendo una sola voz (P: la tercera medio tono; L: medio tono la otra; R: un tono).
Se excava un laberinto (DFS sembrado) y la música lo recorre tal cual: avanza por pasillos,
choca con callejones sin salida y regresa por donde vino.

    python aurora/laberinto.py
"""
import json, random
from pathlib import Path

NOTAS = ['La', 'Si♭', 'Si', 'Do', 'Do♯', 'Re', 'Mi♭', 'Mi', 'Fa', 'Fa♯', 'Sol', 'La♭']   # 0 = La


def nombre(t):
    r, m = t
    return NOTAS[r % 12] + ('m' if m else '')


def P(t): r, m = t; return (r, not m)
def L(t): r, m = t; return ((r + 4) % 12, True) if not m else ((r + 8) % 12, False)
def R(t): r, m = t; return ((r + 9) % 12, True) if not m else ((r + 3) % 12, False)


def laberinto(semilla, inicio=(0, True)):
    rnd = random.Random(semilla)
    visto, pila, camino, callejones = {inicio}, [inicio], [(inicio, 'entra')], []
    while pila:
        t = pila[-1]
        vecinos = [(op, f(t)) for op, f in (('P', P), ('L', L), ('R', R)) if f(t) not in visto]
        if vecinos:
            op, s = rnd.choice(vecinos)
            visto.add(s); pila.append(s); camino.append((s, op))
        else:
            if camino[-1][1] != 'regresa': callejones.append(len(camino) - 1)
            pila.pop()
            if pila: camino.append((pila[-1], 'regresa'))
    return camino, callejones


if __name__ == '__main__':
    import sys; sys.stdout.reconfigure(encoding='utf-8')
    camino, callejones = laberinto(1015)
    print(len(camino), 'pasos,', len(callejones), 'callejones sin salida')
    for i, (t, op) in enumerate(camino):
        print(f'{i:2d} {nombre(t):5s} {op}{"   ← callejón" if i in callejones else ""}')
    json.dump({'camino': [[t[0], t[1], op] for t, op in camino], 'callejones': callejones},
              open(Path(__file__).parent / 'laberinto.json', 'w'), indent=0)
