import copy
import logging
import time

import discord
from discord import Color
from discord.ext import commands
from discord.ext.commands import Context

from util.data.guild_data import GuildData
from util.decorators import delete_original

start_time = time.time()
log = logging.getLogger("smiles")


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

        embed = discord.Embed(title="Profile", color=Color.og_blurple())

        roles = GuildData(ctx.guild.id).virtual_role_collection.fetch_all_by_user_id(ctx.author.id)
        # log.debug(roles)

        role_desc = "**Roles:**\n\n"

        if not roles:
            role_desc = "You have no roles!"
        else:
            for _, _, role_uuid in roles:
                role_display_name = GuildData(ctx.guild.id).virtual_roles.fetch_all_by_role_id(role_uuid)[0][2]
                role_emoji = GuildData(ctx.guild.id).virtual_role_emojis.fetch_all_by_role_id(role_uuid)[0][2]

                # log.debug(f"{role_uuid}: {role_emoji} {role_display_name}")

                role_desc += f"{role_emoji} {role_display_name}\n"

        embed.description = role_desc
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(VirtualProfile(bot))
