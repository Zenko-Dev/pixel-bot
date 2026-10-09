"""Convierte el GIF original en la plantilla ligera que usa el bot.

Uso (desde la raíz del proyecto):
    python -m tools.prepare_template assets/source/original.gif

Qué hace:
1. Reduce el tamaño (ancho 768 px) para que pese pocos MB.
2. Crea UNA paleta común de 253 colores para todos los cuadros.
3. Reserva los 3 últimos colores (253, 254, 255) para el texto.
"""

import sys
from pathlib import Path

from PIL import Image, ImageSequence

from src.pixel.welcome_card import RESERVED_COLORS

WIDTH = 768
OUTPUT = Path("assets/welcome_template.gif")


def prepare(source: Path, destination: Path) -> None:
    original = Image.open(source)
    height = round(original.height * WIDTH / original.width)

    durations = []
    rgb_frames = []
    for frame in ImageSequence.Iterator(original):
        durations.append(frame.info.get("duration", 160))
        small = frame.convert("RGB").resize((WIDTH, height), Image.Resampling.LANCZOS)
        rgb_frames.append(small)

    # Paleta de 253 colores calculada con el primer cuadro (sin estrella fugaz)
    base = rgb_frames[0].quantize(
        colors=253, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE
    )
    colors = base.getpalette()[: 253 * 3]
    colors += [0] * (253 * 3 - len(colors))
    for rgb in RESERVED_COLORS:
        colors += list(rgb)

    palette = Image.new("P", (1, 1))
    palette.putpalette(colors)

    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in rgb_frames]
    frames[0].save(
        destination,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    size_mb = destination.stat().st_size / 1_000_000
    print(
        f"Listo: {destination} ({WIDTH}x{height}, "
        f"{len(frames)} cuadros, {size_mb:.2f} MB)"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python -m tools.prepare_template ruta/al/original.gif")
    prepare(Path(sys.argv[1]), OUTPUT)