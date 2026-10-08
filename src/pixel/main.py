import logging

from dotenv import load_dotenv

from .bot import PixelBot
from .config import load_settings


def main():
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = load_settings()
    bot = PixelBot(settings)
    bot.run(settings.token, log_handler=None)

if __name__ == "__main__":
    main()