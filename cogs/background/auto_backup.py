import logging

from discord.ext import commands, tasks


log = logging.getLogger("smiles")


class MyCog(commands.Cog):
    def __init__(self, bot):
        self.index = 0
        self.bot = bot
        self.update_loop.start()

    def cog_unload(self) -> None:
        self.update_loop.cancel()

    @tasks.loop(seconds=30)
    async def update_loop(self):
        print(self.index)
        self.index += 1

    @update_loop.before_loop
    async def before_printer(self):
        log.info("Waiting for bot before auto backups begin...")
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(MyCog(bot))
