import asyncio
import logging
import time
from typing import Optional, Literal

import discord
from discord.ext import commands
from discord.ext.commands import Context, Greedy

from util.data.data_backup import DataBackups
from util.features import get_extensions

# from datetime import timezone

start_time = time.time()
log = logging.getLogger("smiles")


class Owner(commands.Cog, name="Owner"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="createbackup")
    @commands.is_owner()
    async def create_backup(self, ctx):
        """Create a backup of bot data"""

        await ctx.send("Creating backup...")
        DataBackups().backup_databases()
        await ctx.send("Backup created")

    @commands.command(name="reloadall")
    @commands.is_owner()
    async def reload_all(self, ctx, create_backup=False):
        """Reload all cogs"""

        if create_backup:
            cmd = self.bot.get_command("createbackup")
            await ctx.invoke(cmd)

        await ctx.send("Reload beginning...")

        for extension in get_extensions():
            try:
                self.bot.reload_extension(extension)
                log.debug(f"Reloaded {extension}")
            except commands.ExtensionError:
                try:
                    self.bot.load_extension(extension)
                except commands.ExtensionError as e:
                    log.fatal(f"Error reloading : \n\t{e}")
                    await ctx.send(f"Error reloading : `{e}`")
                else:
                    await ctx.send(f"**{extension}** loaded.")
                    log.info(f"{extension} loaded.")

        await ctx.send("Reloaded all cogs.")
        log.info(f"{ctx.author} reloaded all cogs")

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx, create_backup=False):
        """Shut the bot down."""

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        async def abort():
            return await ctx.send("Bot shutdown aborted.")

        await ctx.reply("**Are you sure you wish to initiate bot shutdown?**\n\tType *yes* to confirm.")

        try:
            entry = await self.bot.wait_for('message', check=check, timeout=10)
        except asyncio.TimeoutError:
            return await abort()

        cleaned = entry.clean_content.lower()
        if not cleaned.startswith("yes") or not cleaned.startswith("y"):
            return await abort()

        if create_backup:
            cmd = self.bot.get_command("createbackup")
            await ctx.invoke(cmd)

        await ctx.send("Shutting down bot...")

        log.info(f"{ctx.author} shutdown the bot")

        await self.bot.close()

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
            self, ctx: Context, guilds: Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
        """
        Sync application commands

        sync        : Global sync
        sync ~      : Current guild sync
        sync *      : Copies all global app commands to current guild and syncs
        sync ^      : Clears all commands from the current guild target and syncs (removes guild commands)
        sync 1 2    : Syncs guilds with ID 1 and 2
        """

        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    # @sync.autocomplete('spec')
    # async def sync_autocomplete(self, interaction: discord.Interaction, current: str,
    #                             ) -> List[app_commands.Choice[str]]:
    #     specs = ['~', '*', '^']
    #     return [
    #         app_commands.Choice(name=spec, value=spec)
    #         for spec in specs if current.lower() in spec.lower()
    #     ]


async def setup(bot):
    await bot.add_cog(Owner(bot))
