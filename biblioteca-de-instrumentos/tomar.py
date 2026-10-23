"""Tomar instrumentos de la biblioteca: copia las fichas elegidas y los motores a una carpeta del proyecto, fijados por huella.

    python tomar.py marimba arpaboca berimbau --a ../research/rejilla/instrumentos
    python tomar.py --todos --a ../meleeviewer/vendor/instrumentos
    python tomar.py --lista

Crea <destino>/instrumentos-<huella12>/ con las fichas, los motores y manifiesto.json (SHA-256 de cada archivo y la huella).
La huella sale del contenido: la misma selección de la misma versión da la misma carpeta. Si ya existe y es idéntica, se usa
tal cual; si existe y es distinta, se rechaza: nunca se sobreescribe. La biblioteca anota en usos.jsonl quién tomó qué, para
saber qué obra usa qué versión. El proyecto carga motores/web.js (o motores/rejilla.py) de ESA carpeta, no de la biblioteca:
así la obra sigue sonando igual aunque la biblioteca avance.
"""
import argparse, datetime, hashlib, json, os, shutil, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
FICHAS, MOTORES = os.path.join(AQUI, 'fichas'), os.path.join(AQUI, 'motores')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ids', nargs='*', help='fichas a tomar (ver --lista)')
    ap.add_argument('--a', dest='destino', help='carpeta del proyecto donde se fija la copia')
    ap.add_argument('--todos', action='store_true')
    ap.add_argument('--lista', action='store_true')
    a = ap.parse_args()
    indice = json.load(open(os.path.join(FICHAS, 'todas.json'), encoding='utf-8'))      # todas las que suenan (indice.json es sólo la página)
    if a.lista:
        for i in indice:
            f = json.load(open(os.path.join(FICHAS, i + '.json'), encoding='utf-8'))
            print(f"{i:13} {f['nombre']:20} {f['familia']:45} motor {f['motor']}")
        return
    ids = indice if a.todos else a.ids
    faltan = [i for i in ids if i not in indice]
    if a.destino is None and not a.lista: pass
    if not ids or faltan or not a.destino:
        sys.exit('uso: tomar.py <ids…> --a <carpeta>   ' + (f'(no existen: {", ".join(faltan)})' if faltan else ''))
    archivos = {f'fichas/{i}.json': os.path.join(FICHAS, i + '.json') for i in sorted(set(ids))}
    # las fichas que tocan código original (motor python u objeto) se llevan la copia de ese código: toda su carpeta (sus hermanos se importan)
    for i in set(ids):
        K = json.load(open(os.path.join(FICHAS, i + '.json'), encoding='utf-8')); S = K['fisica']
        if K['motor'] == 'meleeviewer': archivos[S['escenario']] = os.path.join(AQUI, *S['escenario'].split('/'))      # su escenario
        carpeta = (os.path.dirname(S['archivo']) if K['motor'] == 'python' else S.get('carpeta', 'codigo/rejilla/research/rejilla/objetos/motor/').rstrip('/') if K['motor'] == 'objeto' else None)
        if carpeta:
            for f in sorted(os.listdir(os.path.join(AQUI, *carpeta.split('/')))):
                if f.endswith(('.py', '.js')): archivos[f'{carpeta}/{f}'] = os.path.join(AQUI, *carpeta.split('/'), f)
    if os.path.exists(os.path.join(FICHAS, 'fidelidad-rejilla.json')): archivos['fichas/fidelidad-rejilla.json'] = os.path.join(FICHAS, 'fidelidad-rejilla.json')
    for m in sorted(os.listdir(MOTORES)):
        if m.endswith(('.js', '.py')): archivos[f'motores/{m}'] = os.path.join(MOTORES, m)
    hashes = {k: sha(v) for k, v in archivos.items()}
    huella = hashlib.sha256(''.join(f'{k}:{h}\n' for k, h in sorted(hashes.items())).encode()).hexdigest()
    dest = os.path.join(os.path.abspath(a.destino), f'instrumentos-{huella[:12]}')
    if os.path.exists(dest):
        viejo = json.load(open(os.path.join(dest, 'manifiesto.json'), encoding='utf-8'))
        if viejo.get('archivos') != hashes: sys.exit(f'{dest} existe y es distinta: no se sobreescribe')
        print(f'ya estaba, idéntica: {dest}')
        return
    try:
        commit = subprocess.run(['git', '-C', AQUI, 'rev-parse', '--short=12', 'HEAD'], capture_output=True, text=True).stdout.strip()
        sucio = bool(subprocess.run(['git', '-C', AQUI, 'status', '--porcelain', 'fichas', 'motores'], capture_output=True, text=True).stdout.strip())
    except OSError:
        commit, sucio = '', True
    os.makedirs(dest, exist_ok=False)
    for k, src in archivos.items():
        d = os.path.join(dest, *k.split('/'))
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if os.path.exists(d): sys.exit('no se sobreescribe ' + d)
        shutil.copyfile(src, d)
    man = {'huella': huella, 'tomado': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
           'biblioteca_commit': commit + (' (con cambios sin commitear)' if sucio else ''), 'fichas': sorted(set(ids)), 'archivos': hashes,
           'uso': 'navegador: <script src="instrumentos-%s/motores/web.js"></script> → Instrumentos.tocar(ctx, destino, ficha, nota, {tonica, escala})' % huella[:12]}
    with open(os.path.join(dest, 'manifiesto.json'), 'x', encoding='utf-8') as fh: json.dump(man, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(AQUI, 'usos.jsonl'), 'a', encoding='utf-8') as fh:
        fh.write(json.dumps({'huella': huella, 'destino': os.path.relpath(dest, os.path.dirname(AQUI)).replace('\\', '/'), 'fichas': man['fichas'],
                             'tomado': man['tomado'], 'commit': man['biblioteca_commit']}, ensure_ascii=False) + '\n')
    print(f'{len(ids)} fichas → {dest}')


if __name__ == '__main__':
    main()
