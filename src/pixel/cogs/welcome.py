import asyncio
import io
import logging

import discord
from discord.ext import commands

from ..bot import PixelBot
from ..welcome_card import WelcomeCard

log = logging.getLogger(__name__)


class Welcome(commands.Cog):
    def __init__(self, bot: PixelBot):
        self.bot = bot
        try:
            self.card = WelcomeCard()
        except Exception:
            # Si falta la fuente o la plantilla, el bot arranca igual y saluda con texto
            log.exception("No se pudo cargar la tarjeta de bienvenida")
            self.card = None

    async def _make_image(self, member: discord.Member) -> discord.File | None:
        """Crea la imagen; si algo falla, avisa al canal de errores y devuelve None."""
        if self.card is None:
            return None
        try:
            # render() es trabajo pesado y no es async: va en otro hilo para no
            # congelar al bot mientras dibuja
            data = await asyncio.to_thread(self.card.render, member.display_name)
            limit = member.guild.filesize_limit
            if len(data) > limit:
                raise RuntimeError(
                    f"La imagen pesa {len(data) / 1e6:.1f} MB y el servidor "
                    f"admite {limit / 1e6:.1f} MB"
                )
        except Exception as error:  # noqa: BLE001 - cualquier fallo debe degradar a texto
            await self.bot.report_error("bienvenida (imagen)", error)
            return None
        return discord.File(io.BytesIO(data), filename="bienvenida.gif")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.target_channel(self.bot.settings.welcome_channel_id)
        if channel is None:
            return

        tag = "" if self.bot.settings.is_prod else "[STAGING] "
        image = await self._make_image(member)
        if image is None:
            await channel.send(f"{tag}¡Bienvenido a Pixel Station, {member.mention}!")
        else:
            await channel.send(f"{tag}{member.mention}", file=image)


async def setup(bot: PixelBot):
    await bot.add_cog(Welcome(bot))