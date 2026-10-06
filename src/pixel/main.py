import os
from dotenv import load_dotenv
from .bot import PixelBot

def main():
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Falta DISCORD_TOKEN en el archivo .env")
    
    bot = PixelBot()
    bot.run(token)

if __name__ == "__main__":
    main()