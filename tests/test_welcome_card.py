import io

import pytest
from PIL import Image

from src.pixel.welcome_card import (
    DEFAULT_NAME,
    HEART_HEIGHT,
    TEXT_START,
    WelcomeCard,
    clean_name,
)

DISCORD_LIMIT = 10 * 1024 * 1024  # 10 MiB: servidores sin boosts


def test_clean_name_keeps_accents():
    assert clean_name("Ángel Ñandú") == "Ángel Ñandú"


def test_clean_name_removes_emojis_and_other_alphabets():
    assert clean_name("Pixel 😀 ミク") == "Pixel"


def test_clean_name_uses_default_when_nothing_is_left():
    assert clean_name("😀😀") == DEFAULT_NAME


def test_clean_name_limits_length_to_32():
    assert len(clean_name("a" * 50)) == 32


@pytest.fixture(scope="module")
def card():
    return WelcomeCard()  # se carga una vez y se reutiliza en las pruebas


def test_render_makes_an_animated_gif_that_fits_in_discord(card):
    data = card.render("Angel")
    assert data.startswith(b"GIF")
    assert len(data) < DISCORD_LIMIT

    image = Image.open(io.BytesIO(data))
    assert image.size == (card.width, card.height)
    assert image.n_frames > 1


def test_text_is_centered(card):
    layout = card.layout("Angel")
    for line in (*layout.titles, layout.name):
        assert abs((line.start + line.end) / 2 - card.width / 2) <= 1


@pytest.mark.parametrize("name", ["a", "W" * 32, "Ángel Ñandú"])
def test_text_stays_inside_the_image(card, name):
    layout = card.layout(clean_name(name))
    for line in (*layout.titles, layout.name):
        assert line.start >= 0
        assert line.end <= card.width


def test_long_names_use_a_smaller_font(card):
    short = card.layout("Ana")
    long = card.layout("W" * 32)
    assert long.name.size < short.name.size


def test_text_starts_at_the_configured_height(card):
    first_line = card.layout("Angel").titles[0]
    visible_top = first_line.y + first_line.font.getbbox("H")[1]
    assert visible_top == round(card.height * TEXT_START)


def test_text_has_three_lines_in_order(card):
    layout = card.layout("Angel")
    assert [line.text for line in layout.titles] == ["Bienvenido a", "Pixel Station"]
    assert layout.name.text == "Angel"

    # cada línea queda más abajo que la anterior
    tops = [line.y for line in (*layout.titles, layout.name)]
    assert tops == sorted(tops)
    assert len(set(tops)) == 3


def test_text_block_ends_above_the_bottom_edge(card):
    layout = card.layout("W" * 32)
    heart_bottom = layout.heart_y + HEART_HEIGHT * layout.name.unit
    assert heart_bottom < card.height