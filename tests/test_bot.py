from src.pixel.bot import PixelBot
from src.pixel.config import Settings


def crear_bot(env):
    settings = Settings(
        env=env,
        token="token-falso",
        staging_channel_id=111,
        error_channel_id=222,
        welcome_channel_id=333,
    )
    bot = PixelBot(settings)
    bot.get_channel = lambda canal_id: canal_id  # devuelve el ID que le pidan
    return bot


def test_staging_manda_todo_al_canal_privado():
    bot = crear_bot("staging")
    assert bot.target_channel(333) == 111


def test_prod_usa_el_canal_real():
    bot = crear_bot("prod")
    assert bot.target_channel(333) == 333