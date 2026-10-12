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

        if bot.settings.auto_role_id == 0:
            log.warning("AUTO_ROLE_ID no está configurado: no se asignará rol")

    async def _assign_role(self, member: discord.Member):
        """Da el rol automático al entrar. Si falla, avisa y la bienvenida sigue."""
        role_id = self.bot.settings.auto_role_id
        if role_id == 0 or member.bot:
            return

        role = member.guild.get_role(role_id)
        if role is None:
            await self.bot.report_error(
                "rol automático",
                RuntimeError(
                    f"No existe un rol con ID {role_id}. Revisa AUTO_ROLE_ID."
                ),
            )
            return

        try:
            await member.add_roles(role, reason="Rol automático de bienvenida")
        except discord.Forbidden as error:
            explanation = RuntimeError(
                f"Discord no dejó dar el rol '{role.name}'. Revisa que el bot tenga "
                "el permiso Gestionar roles y que su rol esté ARRIBA de ese rol."
            )
            explanation.__cause__ = error
            await self.bot.report_error("rol automático", explanation)
        except discord.HTTPException as error:
            await self.bot.report_error("rol automático", error)

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
        # El rol va primero: no depende de que exista el canal de bienvenida
        await self._assign_role(member)

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