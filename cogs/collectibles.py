import copy
import json
import logging
import time
from enum import Enum

from discord import Member
from discord.ext import commands
from discord.ext.commands import Context
from discord.utils import escape_markdown

from util.collectible_helpers import CollectibleHelpers, DataResults
from util.data.guild_data import GuildData
from util.decorators import delete_original

start_time = time.time()
log = logging.getLogger("smiles")


class Collectibles(commands.Cog, name="Collectibles"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="collectibles", aliases=["collect", "col", "c"])
    @commands.cooldown(1, 2)
    @commands.guild_only()
    async def collectibles(self, ctx):
        """
        Manage collectibles for the server.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(f"Invalid subcommand! ")

            msg = copy.copy(ctx.message)
            msg.content = f"{ctx.prefix}help {ctx.command}"
            new_ctx = await self.bot.get_context(msg, cls=type(ctx))
            await self.bot.invoke(new_ctx)

    @collectibles.command(name="set", aliases=["add", "s", "a"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def collectible_set(self, ctx: Context, collect_id: str, emoji: str, *, display_name: str) -> None:
        """
        Set collectibles for the server

        If a collectible's unique identifier already exists, this will overwrite it.
        """

        embed = CollectibleHelpers.Embeds.default_embed()
        embed.description = "Setting..."

        msg = await ctx.send(embed=embed)

        result: Enum = await CollectibleHelpers.Management.Collectibles.create_collectible(
            ctx.guild, collect_id, display_name, emoji)
        result_value: str = str(result.value)

        if result == DataResults.SUCCESS_SET:
            await CollectibleHelpers.Embeds.edit_and_send_embed(
                msg, embed, result_value.format(collect_id, display_name, emoji))
        else:
            await CollectibleHelpers.Embeds.edit_and_send_embed(msg, embed, result_value)

    @collectibles.command(name="delete", aliases=["remove"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def collectible_delete(self, ctx: Context, collect_id: str) -> None:
        """
        Delete a collectible from the server
        """

        embed = CollectibleHelpers.Embeds.default_embed()

        result: Enum = CollectibleHelpers.Management.Collectibles.delete_collectible(ctx.guild, collect_id)
        result_value: str = str(result.value)

        if result == DataResults.SUCCESS_DELETE:
            embed.description = result_value.format(collect_id)
        elif result in [DataResults.ERROR_DELETE_COLLECTIBLES, DataResults.ERROR_DELETE_COLLECTION,
                        DataResults.ERROR_DELETE_EMOJI, DataResults.ERROR_DELETE_REACT]:
            embed.description = f"Unable to remove **{collect_id}** from the server.\n\n " \
                                f"```Error: {result_value}```"
        else:
            embed.description = result_value

        await ctx.send(embed=embed)

    @collectibles.command(name="list", aliases=["collectibles"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def collectibles_list(self, ctx: Context) -> None:
        """
        List collectibles on the server
        """

        guild_collectibles = GuildData(str(ctx.guild.id)).collectibles.fetch_all()
        guild_collectible_emojis = GuildData(str(ctx.guild.id)).collectible_emojis.fetch_all()

        sorted_emojis = sorted(guild_collectible_emojis)

        embed = CollectibleHelpers.Embeds.default_embed()

        if not len(guild_collectibles) > 0:
            embed.description = "There are no available collectibles!"
            await ctx.send(embed=embed, delete_after=7)
            return

        embed.title += ": List"
        i = 0
        for t in sorted(guild_collectibles):
            value = t[2]
            embed.add_field(
                name=f"{sorted_emojis[i][2]} {escape_markdown(value[:100])}{'...' if len(value) > 100 else ''}",
                value=t[1],
                inline=True
            )
            i += 1

        await ctx.send(embed=embed)

    @collectibles.command(name="give", aliases=["giveuser"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def collectibles_give(self, ctx: Context, user: Member, collect_id: str) -> None:
        """
        Give a user a collectible.

        User: The user to give the collectible to.
        Collect_ID: The ID of the collectible to give.
        """

        result: Enum = CollectibleHelpers.Management.Users.add_collectible(user, ctx.guild.id, collect_id)
        result_value: str = str(result.value)
        if result == DataResults.SUCCESS_GIVE:
            await ctx.send(result_value.format(user.name, collect_id))
        else:
            await ctx.send(result_value)

    @collectibles.command(name="take", aliases=["takeuser"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def collectibles_take(self, ctx: Context, user: Member, collect_id: str) -> None:
        """
        Take a collectible from a user.

        User: The user to take the collectible from.
        Collect_ID: The ID of the collectible to take.
        """

        result: Enum = CollectibleHelpers.Management.Users.remove_collectible(user, ctx.guild.id, collect_id)
        result_value: str = str(result.value)
        if result == DataResults.SUCCESS_TAKE:
            await ctx.send(result_value.format(user.name, collect_id))
        else:
            await ctx.send(result_value)

    @collectibles.command(name="view")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def collectibles_view(self, ctx: Context, collect_ids: str, show_reactions=True, show_collections=False):
        """
        View data on collectibles

        Enclosing a space-separated list of collectible ids in quotes does multiple at once
        """

        collect_ids_split = collect_ids.split(" ")

        final_data = {}
        for collect_id in collect_ids_split:
            data = CollectibleHelpers.Management.Collectibles.join_data(str(ctx.guild.id), collect_id,
                                                                        not show_reactions, not show_collections)

            final_data.update(data)

        formatted = json.dumps(final_data, indent=2)
        await ctx.send(f"```json\n{formatted[:2000]}\n```")


async def setup(bot):
    await bot.add_cog(Collectibles(bot))
