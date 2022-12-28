import logging

from discord.ext import commands, tasks

from util.data.data_backup import DataBackups

log = logging.getLogger("smiles")


class AutoBackup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_loop.start()

    def cog_unload(self) -> None:
        self.update_loop.cancel()

    @tasks.loop(hours=1)
    async def update_loop(self):
        log.info("Auto backup starting...")
        DataBackups().backup_databases()
        log.info("Auto backup complete.")

    @update_loop.before_loop
    async def before_updater(self):
        log.info("Waiting for bot before auto backups begin...")
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(AutoBackup(bot))
