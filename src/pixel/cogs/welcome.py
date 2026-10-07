import discord
from discord.ext import commands

from ..bot import PixelBot

class Welcome(commands.Cog):
    def __init__(self, bot:PixelBot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.target_channel(self.bot.settings.welcome_channel_id)
        if channel is None:
            return
        
        tag = "" if self.bot.settings.is_prod else "[STAGING] "
        await channel.send(f"{tag}¡Bienvenido al servidor, {member.metion}!")

async def setup(bot: PixelBot):
    await bot.add_cog(Welcome(bot))