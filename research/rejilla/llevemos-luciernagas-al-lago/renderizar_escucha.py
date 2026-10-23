"""Make a first, explicitly unmastered listening realization of Luciérnagas v8.

The score's 36 lanes are rendered from their exact event times and audible
windows. This is a synthesis sketch, not the later master or the final sound
design; the voice model is a compact formant synthesis rather than Difonos.
"""
from __future__ import annotations

import hashlib
import json
import math
import secrets
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

VERSION = "luci-escucha-1.0"
SR = 22050
TAU = 2 * math.pi
BASE = Path(__file__).resolve().parent
SCORE_DIR = BASE / "luciernagas-reescritura-s1-29d4afe5aad2"
SCORE_PATH = SCORE_DIR / "partitura-v8.json"
IMAGE_PATH = SCORE_DIR / "luciernagas-partitura-final-s1-29d4afe5aad2.png"
OUT_BASE = BASE

FAMILY = {
    "guitarra": "string", "pua": "metal", "krar": "string", "berimbau": "reed",
    "arpa": "string", "cuerda": "bow", "organo": "organ", "clarinete": "reed",
    "chelo": "bow", "contrabajo": "bass", "bajo": "bass", "androide": "bass",
    "terminal": "terminal", "piano": "piano", "mbira": "metal", "arpaboca": "string",
    "campana": "bell", "waterphone": "water", "gong": "gong", "bombo": "kick",
    "caja": "snare", "hat": "hat", "tom": "tom", "aro": "rim", "ride": "ride",
    "fotones": "spark", "junco1": "reed", "junco2": "reed", "junco3": "reed",
    "junco4": "reed", "voz": "voice", "duo": "voice", "corocuerda": "voice_bow",
    "corojunco": "vocoder", "boca": "voice", "sala": "room",
}

GAIN = {
    "string": .070, "metal": .060, "reed": .048, "bow": .055, "organ": .045,
    "bass": .075, "terminal": .035, "piano": .058, "bell": .050, "water": .040,
    "gong": .045, "kick": .070, "snare": .043, "hat": .025, "tom": .052,
    "rim": .027, "ride": .030, "spark": .027, "voice": .042, "voice_bow": .033,
    "vocoder": .031, "room": .020,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def vowel(text: str) -> str:
    for c in text.lower():
        if c in "aeiouáéíóú":
            return {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"}.get(c, c)
    return "a"


def formant_weights(freqs: np.ndarray, v: str) -> np.ndarray:
    forms = {"a": (800, 1250, 2700), "e": (500, 1900, 2600),
             "i": (300, 2250, 3000), "o": (500, 900, 2500), "u": (350, 700, 2350)}[v]
    widths = (320, 500, 700)
    z = np.zeros_like(freqs)
    for f, w, amp in zip(forms, widths, (1., .7, .25)):
        z += amp * np.exp(-.5 * ((freqs - f) / w) ** 2)
    return .035 + z


def event_signal(part: str, ev: dict, n: int, sr: int, rng: np.random.Generator) -> np.ndarray:
    """Synthesize one audible window, retaining score pitch curves and phase cues."""
    if n < 2:
        return np.zeros(n, np.float64)
    t = np.arange(n, dtype=np.float64) / sr
    duration = n / sr
    m0 = float(ev.get("midi", 60.))
    m1 = float(ev.get("midi_fin", m0))
    f0 = 440. * 2 ** ((m0 - 69.) / 12.)
    k = math.log(2.) * (m1 - m0) / (12. * max(duration, 1e-9))
    freq = f0 * np.exp(k * t)
    if "fase_inicial_rad" in ev:
        phase0 = float(ev["fase_inicial_rad"])
    elif "estado_complejo" in ev:
        phase0 = math.atan2(float(ev["estado_complejo"][1]), float(ev["estado_complejo"][0]))
    else:
        phase0 = 0.
    if abs(k) < 1e-10:
        phase = phase0 + TAU * f0 * t
    else:
        phase = phase0 + TAU * f0 * np.expm1(k * t) / k

    vel = float(ev.get("vel", .4))
    mass = max(0., float(ev.get("amplitud_relativa", math.sqrt(max(0., ev.get("masa", 1.))))))
    amp = min(1.25, max(.04, vel)) * min(1., mass if "masa" in ev or "amplitud_relativa" in ev else 1.)
    articul = str(ev.get("articulacion", "" )).lower()
    family = FAMILY[part]

    if family in {"kick", "snare", "hat", "tom", "rim", "ride"}:
        noise = rng.standard_normal(n)
        if family == "kick":
            sweep = 45. * np.exp(-t * 22.) + max(30., f0 * .2)
            ph = TAU * np.cumsum(sweep) / sr
            y = np.sin(ph) * np.exp(-t * (8. + 5 * (1 - vel))) + noise * np.exp(-t * 90.) * .025
        elif family == "snare":
            y = noise * np.exp(-t * 32.) * .48 + np.sin(phase) * np.exp(-t * 18.) * .12
        elif family in {"hat", "ride", "rim"}:
            y = noise * np.exp(-t * (22. if family == "ride" else 55.)) * (.2 if family == "ride" else .35)
            if family == "rim":
                y += np.sin(phase * 2.31) * np.exp(-t * 26.) * .25
        else:
            sweep = max(40., f0 * 1.5) * np.exp(-t * 4.)
            y = np.sin(TAU * np.cumsum(sweep) / sr) * np.exp(-t * 10.)
            y += noise * np.exp(-t * 34.) * .06
    else:
        partial_limit = min(30, max(3, int((sr * .44) / max(40., float(np.max(freq))))))
        y = np.zeros(n, np.float64)
        v = vowel(str(ev.get("texto", "a")))
        for h in range(1, partial_limit + 1):
            hf = freq * h
            if family in {"bell", "water", "gong", "metal", "spark"}:
                ratios = {"bell": 1.0 + .0017 * h * h, "water": 1.0 + .004 * h,
                          "gong": 1.0 + .0023 * h * h, "metal": 1.0 + .0009 * h,
                          "spark": 1.0 + .0005 * h * h}
                local_phase = phase * ratios[family]
                decay = {"bell": 1.1, "water": 2.7, "gong": 3.2, "metal": .9, "spark": .35}[family]
                weight = (1. / h ** 1.35) * math.exp(-duration / decay * .18)
                if h in (2, 3, 5, 8):
                    weight *= 1.7
                y += np.sin(local_phase) * weight * np.exp(-t / decay)
            elif family in {"voice", "vocoder", "voice_bow"}:
                spectral = formant_weights(hf, v)
                weight = spectral / (h ** .7)
                if family == "vocoder":
                    weight *= .6 + .4 * np.sin(TAU * (2.5 + h * .071) * t) ** 2
                if family == "voice_bow":
                    weight *= 1. + .28 * np.sin(TAU * 5. / 1000 * t)
                y += np.sin(phase * h) * weight
            elif family in {"bow", "organ", "reed", "terminal", "room"}:
                exponent = 1.15 if family in {"bow", "reed"} else 1.45
                weight = 1. / h ** exponent
                if family == "organ":
                    weight *= (1. + .55 * (h in (2, 3, 5)))
                if family == "terminal":
                    weight *= .6 + .4 * np.sin(TAU * (4. + h * .17) * t)
                if family == "room":
                    weight *= math.exp(-duration * .08) / (1. + .035 * h * h)
                y += np.sin(phase * h + .02 * h * h) * weight
            else:  # strings, bass, and piano
                exponent = {"bass": .82, "piano": 1.55, "string": 1.25}.get(family, 1.2)
                weight = 1. / h ** exponent
                if family == "string":
                    weight *= 1. + .08 * math.sin(h * 1.37)
                y += np.sin(phase * h + .01 * h * h) * weight
        if family in {"string", "piano", "metal", "bell", "water", "gong", "spark"}:
            decay = {"string": 1.5, "piano": .75, "metal": .85, "bell": 1.1,
                     "water": 2.7, "gong": 3.2, "spark": .35}.get(family, 1.)
            y *= np.exp(-t / max(.16, decay * (.32 + vel)))
        elif family == "bass":
            y = np.tanh(1.8 * y) / 1.8
        if family in {"voice", "vocoder", "voice_bow"}:
            syllable = str(ev.get("texto", "" )).lower()
            if any(c in syllable for c in "stxjch"):
                consonant = rng.standard_normal(n) * np.exp(-t * 45.) * .08
                y += consonant
        elif family in {"reed", "terminal"}:
            y += rng.standard_normal(n) * .003

    # Envelopes avoid clicks and keep short syllables and plectrum attacks legible.
    attack = min(.018 if family in {"bell", "metal", "spark"} else .035, duration * .35)
    release = min(.060, duration * .45)
    env = np.ones(n, np.float64)
    if attack > 0:
        env *= np.minimum(1., t / attack) ** 1.4
    if release > 0:
        env *= np.minimum(1., (duration - t) / release) ** .7
    if family in {"bow", "voice", "vocoder", "voice_bow", "organ", "reed", "terminal", "room", "bass"}:
        env *= np.minimum(1., t / max(.025, duration * .10)) ** .7
    return y * env * amp


def mono_to_stereo(dst: np.ndarray, mono: np.ndarray, start: int, pan: float, gain: float) -> None:
    end = min(len(dst), start + len(mono))
    if end <= start:
        return
    m = mono[:end - start] * gain
    angle = (float(np.clip(pan, -1, 1)) + 1.) * math.pi / 4.
    dst[start:end, 0] += m * math.cos(angle)
    dst[start:end, 1] += m * math.sin(angle)


def save_png(path: Path, title: str, lines: list[str], data: np.ndarray | None = None, sr: int = SR) -> None:
    im = Image.new("RGB", (1500, 840), "#101419")
    d = ImageDraw.Draw(im)
    font_path = Path(r"C:\Windows\Fonts\segoeui.ttf")
    title_font = ImageFont.truetype(str(font_path), 34) if font_path.exists() else ImageFont.load_default()
    body_font = ImageFont.truetype(str(font_path), 21) if font_path.exists() else ImageFont.load_default()
    small_font = ImageFont.truetype(str(font_path), 17) if font_path.exists() else ImageFont.load_default()
    d.text((55, 42), title, fill="#e5e1d6", font=title_font)
    y = 105
    for line in lines:
        d.text((58, y), line, fill="#9eb7ae", font=body_font)
        y += 37
    if data is not None and len(data):
        mono = data.mean(axis=1) if data.ndim == 2 else data
        width, height, top = 1360, 400, 360
        d.rectangle((55, top, 55 + width, top + height), outline="#46504d")
        stride = max(1, len(mono) // width)
        env = np.max(np.abs(mono[:stride * width].reshape(-1, stride)), axis=1)
        peak = max(.0001, float(np.max(env)))
        pts = []
        for i, v in enumerate(env):
            x = 56 + i
            yy = top + height / 2 - float(v / peak) * (height * .44)
            pts.append((x, yy))
        d.line(pts, fill="#d39a5c", width=2)
        d.line((55, top + height / 2, 55 + width, top + height / 2), fill="#343b3d")
        d.text((58, top + height + 15), f"envolvente normalizada · pico de esta etapa {peak:.5f}", fill="#9eb7ae", font=small_font)
    im.save(path)


def save_timeline(path: Path, title: str, events: dict, start: float, end: float, rows: list[str] | None = None) -> None:
    """Actual event windows, rendered as a compact, readable lane map."""
    im = Image.new("RGB", (1500, 840), "#101419")
    d = ImageDraw.Draw(im)
    font_path = Path(r"C:\Windows\Fonts\segoeui.ttf")
    title_font = ImageFont.truetype(str(font_path), 34) if font_path.exists() else ImageFont.load_default()
    label_font = ImageFont.truetype(str(font_path), 15) if font_path.exists() else ImageFont.load_default()
    d.text((55, 35), title, fill="#e5e1d6", font=title_font)
    ids = rows or list(events)
    x0, x1, y0, step = 190, 1450, 113, min(18, 660 / max(1, len(ids)))
    for j, pid in enumerate(ids):
        y = int(y0 + j * step)
        d.text((52, y - 7), pid, fill="#a7b8b1", font=label_font)
        d.line((x0, y, x1, y), fill="#252d30", width=1)
        for ev in events.get(pid, []):
            for a, b in ev.get("salidas", [[ev["t"], ev["t"] + ev["dur"]]]):
                a, b = max(start, float(a)), min(end, float(b))
                if b <= a:
                    continue
                xa = x0 + round((a - start) / (end - start) * (x1 - x0))
                xb = max(xa + 1, x0 + round((b - start) / (end - start) * (x1 - x0)))
                tint = (211, 154, 92) if "voz" in pid or "coro" in pid or pid in {"duo", "boca"} else (104, 172, 160)
                d.line((xa, y, min(xb, x1), y), fill=tint, width=4)
    d.line((x0, 785, x1, 785), fill="#52605c")
    for tick in range(5):
        t = start + (end - start) * tick / 4
        x = x0 + round((x1 - x0) * tick / 4)
        d.line((x, 780, x, 792), fill="#8c9893")
        d.text((x - 22, 800), f"{t:.0f}s", fill="#a7b8b1", font=label_font)
    im.save(path)


def save_transport(path: Path, score: dict) -> None:
    data = json.loads((SCORE_DIR / "datos" / "transportes-memoria-v8.json").read_text(encoding="utf-8"))
    plans = data.get("planes", []) if isinstance(data, dict) else data
    im = Image.new("RGB", (1500, 840), "#101419")
    d = ImageDraw.Draw(im)
    font_path = Path(r"C:\Windows\Fonts\segoeui.ttf")
    title_font = ImageFont.truetype(str(font_path), 34) if font_path.exists() else ImageFont.load_default()
    label_font = ImageFont.truetype(str(font_path), 18) if font_path.exists() else ImageFont.load_default()
    d.text((55, 35), "Memoria · planes de transporte heredados", fill="#e5e1d6", font=title_font)
    if isinstance(plans, dict):
        plans = plans.get("planes", [])
    if not plans:
        d.text((58, 110), "24 planes registrados; consulta la receta y el JSON para las matrices completas.", fill="#9eb7ae", font=label_font)
    for i, plan in enumerate(plans[:24]):
        y = 110 + i * 27
        name = str(plan.get("id", plan.get("nombre", plan.get("plan", f"plan {i+1}"))))
        phases = plan.get("fases_origen", [])
        phase = float(phases[0][0] if phases and isinstance(phases[0], list) else (phases[0] if phases else 0.))
        masses = plan.get("a", plan.get("masa_entrada", []))
        amount = float(sum(masses)) if isinstance(masses, list) else float(plan.get("masa_total", 1.))
        d.text((58, y), f"{i+1:02d}  {name}", fill="#a7b8b1", font=label_font)
        d.rectangle((380, y + 3, 1370, y + 19), outline="#394440")
        width = round(990 * max(0., min(1., amount)))
        d.rectangle((381, y + 4, min(1370, 381 + width), y + 18), fill="#6aab9d")
        d.text((1390, y), f"φ {phase:.2f}", fill="#d39a5c", font=label_font)
    im.save(path)


def main() -> None:
    score_bytes = SCORE_PATH.read_bytes()
    score = json.loads(score_bytes.decode("utf-8"))
    image_bytes = IMAGE_PATH.read_bytes()
    source_sha = sha(score_bytes)
    image_sha = sha(image_bytes)
    nonce = secrets.token_hex(16)
    identity = sha((VERSION + nonce + source_sha + image_sha).encode())
    out = OUT_BASE / f"luciernagas-escucha-s{score['semilla']}-{identity[:12]}"
    out.mkdir(exist_ok=False)
    process = out / "proceso"
    process.mkdir(exist_ok=False)
    partitura_copy = out / "partitura.json"
    partitura_copy.write_bytes(score_bytes)
    duration = float(score["duracion"])
    nframes = round(duration * SR)
    mix = np.zeros((nframes, 2), np.float32)
    stem_voice = np.zeros_like(mix)
    center = np.zeros_like(mix)
    wall = np.zeros_like(mix)
    master_hash = hashlib.sha256()
    event_counts = {k: len(v) for k, v in score["eventos"].items()}
    save_png(process / f"01-partes-y-eventos-s{score['semilla']}-{identity[:12]}.png",
             "Luciérnagas · partitura v8", [f"{len(score['partes'])} partes · {sum(event_counts.values()):,} eventos internos · {duration:.3f} s",
              "Mapa de síntesis armado desde los eventos y sus ventanas audibles."], None)
    save_timeline(process / f"02-lineas-completas-s{score['semilla']}-{identity[:12]}.png",
                  "Treinta y seis partes · ventanas audibles", score["eventos"], 0., duration)

    part_lookup = {p["id"]: p for p in score["partes"]}
    for part, events in score["eventos"].items():
        family = FAMILY[part]
        gain = GAIN[family]
        for idx, ev in enumerate(events):
            for a, b in ev.get("salidas", [[ev["t"], ev["t"] + ev["dur"]]]):
                a, b = max(0., float(a)), min(duration, float(b))
                if b - a < 0.004:
                    continue
                start = round(a * SR)
                count = min(nframes - start, round((b - a) * SR))
                if count < 2:
                    continue
                # A stable event seed makes percussion/noise repeatable from the score identity.
                rng = np.random.default_rng((int(score["semilla"]) * 1000003 + idx * 9176 + sum(map(ord, part))) & 0xFFFFFFFF)
                y = event_signal(part, ev, count, SR, rng)
                pan = float(ev.get("pan", part_lookup[part].get("pan", 0.)))
                # Score velocities set local intensity; this fixed gain is an orchestration scale, not mastering.
                mono_to_stereo(mix, y, start, pan, gain)
                if part in {"voz", "duo", "corocuerda", "corojunco", "boca"}:
                    mono_to_stereo(stem_voice, y, start, pan, gain)
                if 93.33333333 <= a < 153.33333334:
                    mono_to_stereo(center, y, start, pan, gain)
                if a >= 206.66666666:
                    mono_to_stereo(wall, y, start, pan, gain)
        if part in {"voz", "duo", "corocuerda", "corojunco", "boca"}:
            save_png(process / f"03-voz-renderizada-s{score['semilla']}-{identity[:12]}.png",
                     "Voz, dúo y coros", ["Alturas, sílabas, acentos, pausas y ventanas leídas de la partitura.",
                     "Síntesis de formantes para esta maqueta; la voz final se hará en producción."], stem_voice)
    save_png(process / f"04-centro-silencioso-s{score['semilla']}-{identity[:12]}.png",
             "Centro · 93.333–153.333 s", ["Treinta y ocho segundos aproximados de salida cerrada dentro del centro.",
             "El cálculo y la mezcla siguen el reloj; el mute cierra la salida según salidas."], center)
    save_transport(process / f"05-transportes-s{score['semilla']}-{identity[:12]}.png", score)
    save_timeline(process / f"06-pared-capas-s{score['semilla']}-{identity[:12]}.png",
                  "Pared · activación de las partes", score["eventos"], 206.66666666, 246.66666667)
    save_png(process / f"07-pared-s{score['semilla']}-{identity[:12]}.png",
             "Pared · tres olas", ["La envolvente viene del render de la mezcla de eventos desde 206.667 s.",
             "Los cortes y las reaperturas siguen las ventanas audibles escritas."], wall)

    # A restrained static gain only prevents numeric overflow. No limiter, EQ, compression,
    # loudness target, or peak normalization is applied in this listening render.
    peak_before = float(np.max(np.abs(mix)))
    safety_gain = min(1., .94 / peak_before) if peak_before > .94 else 1.
    mix *= safety_gain
    peak_after = float(np.max(np.abs(mix)))
    save_png(process / f"08-mezcla-final-s{score['semilla']}-{identity[:12]}.png",
             "Mezcla completa · sin máster", ["36 partes · ganancias fijas por familia · paneo de la partitura.",
              f"Pico previo {peak_before:.5f}; escala de seguridad {safety_gain:.6f}; pico {peak_after:.5f}.",
              "Sin limitador, ecualización, compresión ni normalización de sonoridad."], mix)

    wav_path = out / f"luciernagas-primera-escucha-s{score['semilla']}-{identity[:12]}.wav"
    with wave.open(str(wav_path), "wb") as f:
        f.setnchannels(2); f.setsampwidth(3); f.setframerate(SR)
        block = 1_000_000
        for start in range(0, len(mix), block):
            x = np.clip(mix[start:start + block].astype(np.float64), -1., 1.)
            q = np.round(x * 8388607).astype(np.int32)
            packed = np.empty((len(q), 2, 3), np.uint8)
            packed[:, :, 0] = q & 255
            packed[:, :, 1] = (q >> 8) & 255
            packed[:, :, 2] = (q >> 16) & 255
            f.writeframes(packed.tobytes())
    wav_sha = sha(wav_path.read_bytes())
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("No se encontró ffmpeg para crear el archivo de escucha AAC.")
    m4a_path = out / f"luciernagas-primera-escucha-s{score['semilla']}-{identity[:12]}.m4a"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_path),
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(m4a_path)], check=True)
    m4a_sha = sha(m4a_path.read_bytes())

    # Build an honest process GIF from the actual stage plots captured above.
    pngs = sorted(process.glob("*.png"))
    frames = [Image.open(p).convert("P", palette=Image.Palette.ADAPTIVE, colors=128) for p in pngs]
    gif_path = out / f"luciernagas-proceso-render-s{score['semilla']}-{identity[:12]}.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=1050, loop=0, optimize=True)
    gif_bytes = gif_path.read_bytes()
    gif_sha = sha(gif_bytes)

    recipe = {
        "pieza": score["titulo"], "version_render": VERSION, "semilla": score["semilla"],
        "identificador_ejecucion_sha256": identity, "nonce": nonce,
        "duracion_s": duration, "frecuencia_muestreo_hz": SR, "canales": 2,
        "profundidad_wav_bits": 24, "eventos_internos": sum(event_counts.values()),
        "partes": len(score["partes"]), "conteo_por_parte": event_counts,
        "hash_fuentes": {"partitura_v8.json": source_sha, "imagen_partitura.png": image_sha},
        "hashes_entrega": {wav_path.name: wav_sha, m4a_path.name: m4a_sha,
                           gif_path.name: gif_sha,
                           partitura_copy.name: sha(partitura_copy.read_bytes()),
                           **{p.name: sha(p.read_bytes()) for p in process.glob("*.png")}},
        "pico_lineal_antes_de_escala_seguridad": peak_before,
        "escala_seguridad_fija": safety_gain, "pico_lineal_final": peak_after,
        "procesamiento": "sin limitador, EQ, compresion, normalizacion de sonoridad ni master",
        "alcance": "maqueta sonora; la voz usa formantes; articulaciones y ventanas derivadas de la partitura; motores exactos y mezcla final pendientes",
        "familias_sintesis": FAMILY,
    }
    recipe_path = out / "receta.json"
    recipe_path.write_text(json.dumps(recipe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "README.md").write_text(
        "# Luciérnagas · primera escucha\n\n"
        "Maqueta estéreo de la partitura v8, 4:18.667, 36 partes. Conserva los tiempos, alturas, paneos y ventanas audibles escritos.\n\n"
        "La voz usa síntesis de formantes y los instrumentos se agrupan en familias de síntesis para poder escuchar toda la forma. Esta salida sirve para revisar proporciones, silencios, relevo central y pared; no es el sonido final de los instrumentos ni un máster.\n\n"
        f"- Escucha AAC: `{m4a_path.name}`\n- WAV estéreo PCM 24 bit: `{wav_path.name}`\n- Partitura fuente: `partitura.json`\n- GIF de proceso: `{gif_path.name}`\n- Receta y huellas: `receta.json`\n- Etapas: `proceso/`\n\n"
        "No se aplicó limitador, ecualización, compresión, normalización de sonoridad ni máster.\n", encoding="utf-8")
    (process / "README.md").write_text(
        "# Etapas del render\n\n"
        "Las láminas registran estados tomados de esta ejecución: el mapa antes de sintetizar, la suma de voces después de procesarlas, el centro y la pared como salen de los eventos con sus ventanas, y la mezcla completa. El GIF reúne las cinco láminas en orden; no reconstruye una evolución interna del sintetizador.\n\n"
        "Versión: `" + VERSION + "`; semilla de composición: `" + str(score["semilla"]) + "`; identificador: `" + identity + "`.\n", encoding="utf-8")
    print(json.dumps({"out": str(out), "wav": str(wav_path), "m4a": str(m4a_path), "gif": str(gif_path),
                      "wav_bytes": wav_path.stat().st_size, "m4a_bytes": m4a_path.stat().st_size,
                      "gif_bytes": len(gif_bytes), "png_count": len(list(process.glob("*.png"))),
                      "peak": peak_after, "duration": duration, "sha256": identity}, ensure_ascii=False))


if __name__ == "__main__":
    main()
