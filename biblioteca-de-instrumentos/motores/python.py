"""biblioteca de instrumentos · motor «python» (loop 02): toca una ficha llamando a la función ORIGINAL de un proyecto, desde la copia
de su código que guarda la biblioteca (codigo/…, con su huella en codigo/PROCEDENCIA.json). Para instrumentos que no son datos sino
programas en el tiempo (numpy), como los del jardín.

    import python as PY
    y, sr = PY.nota(K, midi=62, vel=.8, dur=1.2)

fisica.firma dice cómo se llama:
  linea  → f(f0[], env[], onsets, rng)          (jardín: farfisa, flauta, cuerda, theremin, trautonium, ondas, hammond, voz)
  golpe  → golpe(f_desde, f_hasta, rng, vel)    (jardín: tambor parlante, que habla bajando a su nota)
  gesto  → silbido/trino (a, b, d), gorjeo(notas, rng), llamado(a, b)   (jardín: aves)
"""
import importlib.util, math, os, sys
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); BIB = os.path.dirname(AQUI); AGENT = os.path.dirname(BIB)
_MOD = {}


def hz(m): return 440 * 2 ** ((m - 69) / 12)


def modulo(archivo, rutas_extra=()):
    """Importa la copia (codigo/…) con un nombre único, con su carpeta en sys.path para sus hermanos."""
    if archivo in _MOD: return _MOD[archivo]
    p = os.path.join(BIB, *archivo.split('/')); carpeta = os.path.dirname(p)
    nombre = 'bib_' + archivo.replace('/', '_').replace('.', '_').replace('-', '_')
    sys.path.insert(0, carpeta)
    try:
        spec = importlib.util.spec_from_file_location(nombre, p); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    finally:
        sys.path.remove(carpeta)
    _MOD[archivo] = mod; return mod


def semilla(K, midi): return int.from_bytes(f"{K['id']}:{round(midi * 100)}".encode()[:8].ljust(8, b'\0'), 'little') % (2 ** 32)


def nota(K, midi, vel=.8, dur=1.0):
    S = K['fisica']; mod = modulo(S['archivo']); sr = getattr(mod, 'SR', 48000); rng = np.random.default_rng(semilla(K, midi)); f = hz(midi)
    for k, v in S.get('fijar', {}).items():             # p. ej. el banco de difonos, que la copia no encuentra por ruta relativa:
        d = BIB                                          # se busca subiendo desde donde esté la biblioteca (o su copia fijada)
        while not os.path.exists(os.path.join(d, v)) and os.path.dirname(d) != d: d = os.path.dirname(d)
        if not os.path.exists(os.path.join(d, v)): raise FileNotFoundError(f"{K['id']} necesita {v} (no viaja con tomar.py): tócalo desde dentro de herramientas/agent")
        setattr(mod, k, type(getattr(mod, k))(os.path.join(d, v)))
    fn = getattr(mod, S['funcion']); firma = S['firma']
    if firma == 'linea':                                # la misma línea que arma el jardín: altura, envolvente y ataques con el perfil del instrumento
        perfil = mod.PERFIL.get(S['funcion']) or next(iter(mod.PERFIL.values()))
        t0, f0, env, onsets = mod.linea([(0.25, f, dur, vel)], perfil, rng)
        y = fn(f0, env, onsets, rng)
    elif firma == 'golpe':
        fr = getattr(mod, 'registro', lambda x: x)(f); y = fn(fr * S.get('habla', 1.15), fr, rng, vel=vel)
    elif firma == 'gesto':
        g = S['gesto']
        y = (fn(f, f * 1.5, dur) if g in ('silbido', 'trino') else fn([f, f * 1.12, f * 1.26, f * 1.5], rng) if g == 'gorjeo' else fn(f, f * 1.33)) * vel
    else:
        raise ValueError(f'firma desconocida: {firma}')
    y = np.asarray(y, float)
    return (y.mean(1) if y.ndim > 1 else y), sr
