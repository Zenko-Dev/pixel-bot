import logging
import sys
import traceback

import discord
from discord.ext import commands

from .config import Settings

log = logging.getLogger(__name__)

class PixelBot(commands.Bot):
    def __init__(self, settings: Settings):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings

    async def setup_hook(self):
        await self.load_extension(f"{__package__}.cogs.welcome")

    async def on_ready(self):
        log.info("Pixel conectado como %s [%s]", self.user, self.settings.env)

    def target_channel(self, prod_channel_id: int):
        """Devuelve el canal correcto segun el entorno"""
        if self.settings.is_prod:
            return self.get_channel(prod_channel_id)
        return self.get_channel(self.settings.staging_channel_id)
    
    async def report_error(self, where: str, error: BaseException):
        log.error("Error en %s", where, exc_info=error)

        channel = self.get_channel(self.settings.error_channel_id)
        if channel is None:
            log.warning(
                "No encuentro el canal de errores (ERROR_CHANNEL:ID=%s)",
                self.settings.error_channel_id,
            )
            return

        trace = "".join(traceback.format_exception(error))
        message = (
            f"⚠️ **[{self.settings.env}] Error en `{where}`**\n"
            f"```py\n{trace[-1800:]}\n```"
        )
        await channel.send(message)

    async def on_error(self, event_method: str, *args, **kwargs):
        error = sys.exc_info()[1]
        if error is not None:
            await self.report_error(f"Evento {event_method}", error)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        await self.report_error("commando {ctx.command}". error)