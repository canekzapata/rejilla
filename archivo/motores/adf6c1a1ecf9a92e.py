from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).parent
OUT = ROOT / "proceso"
HASH = "d5b2b63514a7"
DATA = json.loads((OUT / "datos-render.json").read_text(encoding="utf-8"))
BG = "#101712"
PANEL = "#17231a"
INK = "#e4e8d9"
MUTED = "#a8b7a0"
WATER = "#8ac8bf"
BIRD = "#e7c986"
FONT_PATH = Path("C:/Windows/Fonts/consola.ttf")
FONT_BOLD_PATH = Path("C:/Windows/Fonts/consolab.ttf")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD_PATH if bold and FONT_BOLD_PATH.exists() else FONT_PATH
    return ImageFont.truetype(str(path), size=size)


def base(title: str, number: str) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (1200, 630), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((46, 42, 1154, 588), radius=16, fill=PANEL, outline="#50644f", width=2)
    draw.text((82, 72), "SIRINGUA   /   ENSAYO DE CANAL", font=font(18, True), fill=WATER)
    draw.text((82, 115), title, font=font(32, True), fill=INK)
    draw.text((82, 560), f"{number}   ·   PRUEBA LOCAL; CANAL TEIA AÚN SIN CONECTAR", font=font(15), fill=MUTED)
    return image, draw


def message_stage() -> Image.Image:
    image, draw = base("Una frase llega", "01")
    draw.text((105, 215), "todavía estoy aquí", font=font(42), fill=INK)
    draw.line((106, 302, 1092, 302), fill="#4c6354", width=2)
    draw.text((110, 346), "mensaje de prueba", font=font(21), fill=BIRD)
    draw.text((110, 390), "18 caracteres · español mexicano", font=font(19), fill=MUTED)
    draw.text((110, 456), "el texto entra como dato; no ejecuta código", font=font(18), fill=WATER)
    draw.text((990, 434), "< 300", font=font(24, True), fill=BIRD)
    return image


def phoneme_stage() -> Image.Image:
    image, draw = base("La frase se vuelve sonidos", "02")
    y = 205
    for word in DATA["words"]:
        draw.text((106, y), word["text"], font=font(26, True), fill=BIRD)
        draw.text((330, y + 2), "  ·  ".join(word["phones"]), font=font(22), fill=INK)
        draw.text((330, y + 36), "  ".join(word["ipa"]), font=font(16), fill=MUTED)
        y += 102
    draw.text((106, 485), f"Difonos es-MX  →  {DATA['events']['water']} frases de agua  +  {DATA['events']['bird']} respuestas de ave", font=font(18), fill=WATER)
    return image


def render_stage() -> Image.Image:
    image, draw = base("Agua cantada; pájaro responde", "03")
    x0, x1, ymid, amp = 100, 1100, 340, 118
    draw.line((x0, ymid, x1, ymid), fill="#516151", width=1)
    samples = DATA["samples"]
    steps = 1000
    points = []
    for i in range(steps):
        start = int(i * len(samples) / steps)
        stop = max(start + 1, int((i + 1) * len(samples) / steps))
        value = max(samples[start:stop], key=abs)
        x = x0 + (x1 - x0) * i / (steps - 1)
        y = ymid - value * amp
        points.append((x, y))
    draw.line(points, fill=WATER, width=2)
    for i, word in enumerate(DATA["words"]):
        start = 110 + i * 328
        draw.rounded_rectangle((start, 473, start + 210, 512), radius=16, outline="#718263", width=1)
        draw.text((start + 15, 481), word["text"], font=font(17), fill=BIRD)
        draw.text((start + 236, 480), "··  ♪", font=font(19), fill=BIRD)
    draw.text((100, 185), f"{DATA['duration']:.2f} s  ·  24 kHz  ·  pico {DATA['peak']:.2f}  ·  RMS {DATA['rms']:.3f}", font=font(17), fill=MUTED)
    draw.text((100, 521), "El pájaro contesta después de cada palabra.", font=font(18), fill=WATER)
    return image


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    images = [
        message_stage(),
        phoneme_stage(),
        render_stage(),
    ]
    names = [
        f"01-mensaje-siringua-prueba-teia-{HASH}.png",
        f"02-fonemas-siringua-prueba-teia-{HASH}.png",
        f"03-agua-y-ave-siringua-prueba-teia-{HASH}.png",
    ]
    for image, name in zip(images, names):
        image.save(OUT / name, optimize=True)
    images[-1].save(ROOT / "og.png", optimize=True)
    images[-1].save(ROOT / f"siringua-prueba-teia-{HASH}-resultado.png", optimize=True)
    images[-1].resize((32, 32)).save(ROOT / "favicon.png", optimize=True)
    images[0].save(
        ROOT / f"proceso-siringua-prueba-teia-{HASH}.gif",
        save_all=True,
        append_images=images[1:],
        duration=[1800, 1800, 1800],
        loop=0,
        optimize=True,
    )
    print("\n".join(str(ROOT / name) for name in names))


if __name__ == "__main__":
    main()

