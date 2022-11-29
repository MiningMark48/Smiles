import logging
import time
from typing import Optional, Literal, List

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context, Greedy

# from datetime import timezone

start_time = time.time()
log = logging.getLogger("smiles")


class Owner(commands.Cog, name="Owner"):
    def __init__(self, bot):
        self.bot = bot

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
