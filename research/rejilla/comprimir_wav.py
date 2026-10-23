"""Comprime los WAV de rejilla SIN PERDER NADA y borra cada WAV sólo si la copia comprimida es idéntica (18 oct 2026, pedido de Canek).

  · WAV de enteros (16/24 bits) → FLAC.
  · WAV de float (32 bits) → WavPack (.wv): FLAC no guarda float; WavPack sí, exacto.
  · Verificación: el WAV original y el comprimido se decodifican con ffmpeg al MISMO formato crudo (s32le para enteros, f32le para
    float) y se compara la huella SHA-256 del audio. Si no coincide, se borra el comprimido y el WAV se queda.
  · Registro: compresion-wav.jsonl (ruta, tamaños, huella del archivo WAV original, huella del audio, formato).
  · No toca .git. Si ya existe el comprimido con el mismo nombre, no lo pisa: verifica contra él.

    python comprimir_wav.py --probar 5          # sólo 5 archivos (prueba)
    python comprimir_wav.py                     # todos (4 procesos)
    python comprimir_wav.py --restaurar x.wv    # regresar a WAV: ffmpeg -i x.wv -c:a pcm_f32le x.wav (o pcm_s16le/pcm_s24le)
"""
import argparse, hashlib, json, os, struct, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
AQUI = os.path.dirname(os.path.abspath(__file__)); REG = os.path.join(AQUI, 'compresion-wav.jsonl')


def formato(p):
    with open(p, 'rb') as h: d = h.read(4096)
    i = d.find(b'fmt '); tag, ch, sr, _, _, bits = struct.unpack('<HHIIHH', d[i + 8:i + 24])
    if tag == 0xFFFE: tag = struct.unpack('<H', d[i + 32:i + 34])[0]
    return ('float' if tag == 3 else 'entero'), bits, ch, sr


def huella_pcm(p, crudo):
    """Huella del audio decodificado, leído a pedazos (los WAV grandes no caben en memoria cuatro veces)."""
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', p, '-map', '0:a:0', '-f', crudo, '-c:a', 'pcm_' + crudo, '-'], stdout=subprocess.PIPE)
    h, n = hashlib.sha256(), 0
    for bloque in iter(lambda: pr.stdout.read(1 << 22), b''): h.update(bloque); n += len(bloque)
    if pr.wait() != 0: raise RuntimeError('ffmpeg no pudo decodificar ' + p)
    return h.hexdigest(), n


def uno(p):
    tipo, bits, ch, sr = formato(p)
    if tipo == 'float': dst, args, crudo = p[:-4] + '.wv', ['-c:a', 'wavpack'], 'f32le'
    else: dst, args, crudo = p[:-4] + '.flac', ['-c:a', 'flac', '-compression_level', '8'] + (['-sample_fmt', 's32'] if bits > 16 else []), 's32le'
    archivo = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    hecho = os.path.exists(dst)
    if not hecho: subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', p, '-map', '0:a:0'] + args + [dst], check=True)
    a, na = huella_pcm(p, crudo); b, nb = huella_pcm(dst, crudo)
    ok = a == b and na == nb and na > 0
    fila = dict(wav=os.path.relpath(p, AQUI).replace('\\', '/'), a=os.path.relpath(dst, AQUI).replace('\\', '/'), tipo=f'{tipo}{bits}', canales=ch, sr=sr,
                bytes_wav=os.path.getsize(p), bytes_nuevo=os.path.getsize(dst), sha256_wav=archivo, sha256_audio=a, identico=ok, vacio=na == 0)
    if ok: os.remove(p)
    elif not hecho: os.remove(dst)                        # no coincidió: se quita el comprimido, el WAV se queda
    return fila


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--probar', type=int); ap.add_argument('--restaurar'); ap.add_argument('-j', type=int, default=4); a = ap.parse_args()
    if a.restaurar:
        reg = {json.loads(l)['a']: json.loads(l) for l in open(REG, encoding='utf-8')}; f = reg[os.path.relpath(os.path.abspath(a.restaurar), AQUI).replace('\\', '/')]
        c = {'float32': 'pcm_f32le', 'entero16': 'pcm_s16le', 'entero24': 'pcm_s24le'}[f['tipo']]
        subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', a.restaurar, '-c:a', c, a.restaurar.rsplit('.', 1)[0] + '.wav'], check=True); return
    wavs = []
    for r, ds, fs in os.walk(AQUI):
        ds[:] = [d for d in ds if d != '.git']
        wavs += [os.path.join(r, f) for f in fs if f.lower().endswith('.wav')]
    wavs.sort(key=os.path.getsize)
    if a.probar: wavs = wavs[:a.probar // 2] + wavs[-(a.probar - a.probar // 2):]
    total = sum(map(os.path.getsize, wavs)); t0 = time.time(); hechos = vacios = 0; antes = despues = 0; malos = []
    print(f'{len(wavs)} WAV, {total / 2**30:.2f} GB', flush=True)
    with ProcessPoolExecutor(a.j) as ex, open(REG, 'a', encoding='utf-8') as log:
        fut = {ex.submit(uno, p): p for p in wavs}
        for k, f in enumerate(as_completed(fut), 1):
            try: fila = f.result()
            except Exception as e: malos.append((fut[f], str(e)[:120])); continue
            log.write(json.dumps(fila, ensure_ascii=False) + '\n'); log.flush()
            if fila['identico']: hechos += 1; antes += fila['bytes_wav']; despues += fila['bytes_nuevo']
            elif fila.get('vacio'): vacios += 1          # WAV sin audio (p. ej. un TTS fallido): se queda tal cual
            else: malos.append((fila['wav'], 'no idéntico: el WAV se quedó'))
            if k % 100 == 0 or k == len(wavs): print(f'{k}/{len(wavs)}  {antes / 2**30:.2f} GB → {despues / 2**30:.2f} GB  {time.time() - t0:.0f} s', flush=True)
    print(f'listo: {hechos} comprimidos e idénticos; {vacios} WAV vacíos se quedaron; {antes / 2**30:.2f} GB → {despues / 2**30:.2f} GB; problemas: {len(malos)}')
    for m in malos[:20]: print('  ', *m)


if __name__ == '__main__':
    main()
