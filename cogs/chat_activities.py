import copy
import copy
import logging
import time
from typing import Optional

from discord import TextChannel
from discord.ext import commands
from discord.ext.commands import Context

from util.data.guild_data import GuildData
from util.decorators import delete_original

start_time = time.time()
log = logging.getLogger("smiles")


class ChatActivities(commands.Cog, name="Activity Management"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="activitymanagement", aliases=["actmng", "am"])
    @commands.cooldown(1, 2)
    @commands.guild_only()
    async def activity_management(self, ctx):
        """
        Manage chat activities for the server.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(f"Invalid subcommand! ")

            msg = copy.copy(ctx.message)
            msg.content = f"{ctx.prefix}help {ctx.command}"
            new_ctx = await self.bot.get_context(msg, cls=type(ctx))
            await self.bot.invoke(new_ctx)

    @activity_management.command(name="channelset", aliases=["chanset", "cs", "setchannel", "setchan"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def activity_channel_set(self, ctx: Context, channel: TextChannel = None) -> None:
        """
        Set the channel where activities are sent.

        If channel is None, channel will be removed from the config and not set.
        """

        if channel:
            if await ctx.guild.fetch_channel(channel.id):
                GuildData(str(ctx.guild.id)).strings.set("activity_channel", str(channel.id))
                await ctx.send(f"Activity channel **set** to `{channel}`.", delete_after=7)
                return

        if GuildData(str(ctx.guild.id)).strings.fetch_by_name("activity_channel"):
            GuildData(str(ctx.guild.id)).strings.delete("activity_channel")
            await ctx.send(f"Activity channel **cleared**.", delete_after=7)
            return

        await ctx.send("No activity channel is set.", delete_after=7)


async def setup(bot):
    await bot.add_cog(ChatActivities(bot))
