"""Genera la imagen de bienvenida: la plantilla GIF con el texto encima.

Prueba rápida sin Discord (desde la raíz del proyecto):
    python -m src.pixel.welcome_card "Angel"
Crea un archivo preview.gif para que veas el resultado.
"""

import io
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = ROOT / "assets" / "welcome_template.gif"
FONT_PATH = ROOT / "assets" / "fonts" / "PressStart2P-Regular.ttf"

# Colores reservados en la paleta de la plantilla (posiciones 253, 254 y 255).
# tools/prepare_template.py los crea usando estos mismos valores.
SHADOW, TEXT, HEART = 253, 254, 255
RESERVED_COLORS = [(6, 10, 60), (255, 255, 255), (255, 92, 138)]

# Cada elemento es una línea; el nombre y el corazón van debajo, en una tercera.
TITLE_LINES = ("Bienvenido a", "Pixel Station")
DEFAULT_NAME = "Nuevo jugador"

# La fuente está dibujada en una cuadrícula de 8 px, por eso solo usamos
# múltiplos de 8: así los "píxeles" del texto salen nítidos.
FONT_SIZES = (64, 32, 24, 16, 8)
# Dónde empieza el texto, como fracción de la altura de la imagen:
# 0 = pegado arriba, 1/3 = donde empieza el tercio de en medio.
# (A 2/3 el texto taparía la antena de la mascota Pixel.)
TEXT_START = 1 / 4
LINE_GAP = 18

# Corazón de 7x6 "píxeles" (# = pintado)
HEART_PIXELS = (
    ".##.##.",
    "#######",
    "#######",
    ".#####.",
    "..###..",
    "...#...",
)
HEART_WIDTH = 7
HEART_HEIGHT = 6


def _can_draw(char: str) -> bool:
    """La fuente tiene ASCII y letras latinas (á, ñ, ü...), pero no emojis."""
    code = ord(char)
    return 0x20 <= code <= 0x7E or (code <= 0xFF and char.isalpha())


def clean_name(name: str) -> str:
    """Quita lo que la fuente no puede dibujar (saldría como cuadritos)."""
    kept = "".join(c for c in name if _can_draw(c))
    return " ".join(kept.split())[:32] or DEFAULT_NAME


@dataclass(frozen=True)
class Line:
    """Un texto ya medido: con qué fuente se dibuja y en qué posición."""

    text: str
    font: ImageFont.FreeTypeFont
    size: int
    x: int  # dónde se dibuja
    y: int
    start: int  # dónde empieza lo que se ve (incluye el corazón, si hay)
    end: int
    text_width: int

    @property
    def unit(self) -> int:
        """Tamaño de 1 "píxel" de la fuente."""
        return self.size // 8


@dataclass(frozen=True)
class Layout:
    titles: tuple[Line, ...]
    name: Line
    heart_x: int
    heart_y: int


class WelcomeCard:
    def __init__(self, template: Path = TEMPLATE_PATH, font: Path = FONT_PATH):
        self.fonts = {size: ImageFont.truetype(str(font), size) for size in FONT_SIZES}

        with Image.open(template) as gif:
            self.width, self.height = gif.size
            colors = gif.getpalette()
            self._check_palette(colors)
            palette = Image.new("P", (1, 1))
            palette.putpalette(colors)

            # Se decodifica UNA vez al arrancar; después solo se copia y se dibuja.
            self.frames = []
            self.durations = []
            for frame in ImageSequence.Iterator(gif):
                self.durations.append(frame.info.get("duration", 160))
                rgb = frame.convert("RGB")
                self.frames.append(
                    rgb.quantize(palette=palette, dither=Image.Dither.NONE)
                )

    @staticmethod
    def _check_palette(colors: list[int]) -> None:
        reserved = zip((SHADOW, TEXT, HEART), RESERVED_COLORS, strict=True)
        for index, expected in reserved:
            actual = tuple(colors[index * 3 : index * 3 + 3])
            if actual != expected:
                raise ValueError(
                    "La plantilla no tiene los colores reservados para el texto. "
                    "Generala con: python -m tools.prepare_template"
                )

    # ---- medir y colocar -------------------------------------------------

    def _visible_width(self, text: str, size: int) -> int:
        left, _, right, _ = self.fonts[size].getbbox(text)
        return right - left

    def _fit(self, text: str, with_heart: bool) -> tuple[int, int, int]:
        """Elige el tamaño más grande que quepa.

        Devuelve (tamaño, ancho del texto, ancho total con el corazón).
        """
        max_width = self.width - 2 * (self.width // 16)
        for size in FONT_SIZES:
            text_width = self._visible_width(text, size)
            total = text_width
            if with_heart:
                total += size + HEART_WIDTH * (size // 8)  # hueco + corazón
            if total <= max_width:
                break
        return size, text_width, total

    def _place(self, text: str, with_heart: bool, top: int) -> Line:
        """Mide el texto y lo centra horizontalmente."""
        size, text_width, total = self._fit(text, with_heart)
        font = self.fonts[size]
        start = self.width // 2 - total // 2
        return Line(
            text=text,
            font=font,
            size=size,
            x=start - font.getbbox(text)[0],
            y=top - font.getbbox("H")[1],
            start=start,
            end=start + total,
            text_width=text_width,
        )

    @staticmethod
    def _cap_height(font: ImageFont.FreeTypeFont) -> int:
        _, top, _, bottom = font.getbbox("H")
        return bottom - top

    def layout(self, name: str) -> Layout:
        """Calcula tamaños y posiciones de todo. No dibuja nada."""
        top = round(self.height * TEXT_START)

        # Las líneas del título, una debajo de otra
        titles = []
        for text in TITLE_LINES:
            line = self._place(text, with_heart=False, top=top)
            titles.append(line)
            top += self._cap_height(line.font) + LINE_GAP

        # Última línea: el nombre. "top" ya quedó justo debajo del título.
        name_line = self._place(name, with_heart=True, top=top)

        # El corazón va después del nombre, centrado en vertical con las mayúsculas
        spare = self._cap_height(name_line.font) - HEART_HEIGHT * name_line.unit
        return Layout(
            titles=tuple(titles),
            name=name_line,
            heart_x=name_line.start + name_line.text_width + name_line.size,
            heart_y=top + spare // 2,
        )

    # ---- dibujar ---------------------------------------------------------

    @staticmethod
    def _draw(frame: Image.Image, layout: Layout) -> None:
        pen = ImageDraw.Draw(frame)
        pen.fontmode = "1"  # sin suavizado: bordes de píxel nítidos

        # Cada texto: primero su sombra (desplazada) y encima el texto
        for line in (*layout.titles, layout.name):
            u = line.unit
            pen.text((line.x + u, line.y + u), line.text, font=line.font, fill=SHADOW)
            pen.text((line.x, line.y), line.text, font=line.font, fill=TEXT)

        # El corazón se pinta "píxel" por "píxel": primero sombra, luego rosa
        u = layout.name.unit
        for color, offset in ((SHADOW, u), (HEART, 0)):
            for row, pattern in enumerate(HEART_PIXELS):
                for col, cell in enumerate(pattern):
                    if cell == "#":
                        x = layout.heart_x + col * u + offset
                        y = layout.heart_y + row * u + offset
                        pen.rectangle((x, y, x + u - 1, y + u - 1), fill=color)

    def render(self, name: str) -> bytes:
        """Devuelve el GIF terminado (en bytes) para este nombre."""
        layout = self.layout(clean_name(name))

        frames = []
        for original in self.frames:
            frame = original.copy()  # nunca se modifica el original
            self._draw(frame, layout)
            frames.append(frame)

        output = io.BytesIO()
        frames[0].save(
            output,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=self.durations,
            loop=0,
            optimize=False,
        )
        return output.getvalue()


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Angel"
    Path("preview.gif").write_bytes(WelcomeCard().render(name))
    print("Listo: preview.gif")