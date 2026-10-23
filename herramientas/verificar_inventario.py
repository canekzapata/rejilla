"""Cotejar todas las copias de fuentes y la procedencia de esta edición."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def main():
    inventory = json.loads((ROOT/'INVENTARIO-INSTRUMENTOS.json').read_text(encoding='utf8'))
    rows = inventory['actual']+inventory['anterior']
    provenance = json.loads((ROOT/'PROCEDENCIA.json').read_text(encoding='utf8'))
    errors = []
    for row in rows:
        p = ROOT/row['copia']
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != row['sha256']:
            errors.append(row['copia'])
    for rel, row in provenance['archivos'].items():
        p = ROOT/rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != row['sha256']:
            errors.append(rel)
    if errors:
        raise RuntimeError('Copias ausentes o distintas: '+', '.join(sorted(set(errors))))
    print(f'OK: {len(rows)} filas de inventario y {len(provenance["archivos"])} copias con huellas correctas.')


if __name__ == '__main__':
    main()
