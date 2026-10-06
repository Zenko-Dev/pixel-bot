import discord
from discord.ext import commands

class PixelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Pixel conectado como {self.user}")