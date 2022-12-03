import copy
import logging
import time

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import Context

from util.data.guild_data import GuildData
from util.decorators import delete_original
from util.virtual_helpers import VirtualHelpers

start_time = time.time()
log = logging.getLogger("smiles")


# TODO:
#   [ ] Add pagination for collectibles viewing
#   [ ] Add way to view other users' profiles
#   [ ] Leaderboard of most owned collectibles


class VirtualProfile(commands.Cog, name="Virtual Profile"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="virtualprofile", aliases=["vprofile", "vp", "profile"])
    @commands.cooldown(1, 2)
    @commands.guild_only()
    async def virtual_profile(self, ctx):
        """
        Manage and view your virtual profile!
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(f"Invalid subcommand! ")

            msg = copy.copy(ctx.message)
            msg.content = f"{ctx.prefix}help {ctx.command}"
            new_ctx = await self.bot.get_context(msg, cls=type(ctx))
            await self.bot.invoke(new_ctx)

    @virtual_profile.command(name="view", aliases=["see", "v"])
    @commands.guild_only()
    @delete_original()
    async def virtual_view(self, ctx: Context) -> None:
        """
        View your virtual profile
        """

        embed = VirtualHelpers.default_embed(title="Profile")

        collectibles = GuildData(ctx.guild.id).collectible_collection.fetch_all_by_user_id(ctx.author.id)
        # log.debug(collectibles)

        collect_desc = "**Collectibles:**\n\n"

        if not collectibles:
            collect_desc = "You have no collectibles!"
        else:
            for _, _, collect_id in collectibles:
                collect_display_name = GuildData(ctx.guild.id).collectibles.fetch_all_by_id(collect_id)[0][2]
                collect_emoji = GuildData(ctx.guild.id).collectible_emojis.fetch_all_by_id(collect_id)[0][2]

                # log.debug(f"{collect_id}: {collect_emoji} {collect_display_name}")

                collect_desc += f"{collect_emoji} {collect_display_name}\n"

        embed.description = collect_desc
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(VirtualProfile(bot))
