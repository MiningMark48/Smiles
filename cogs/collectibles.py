import copy
import logging
import time

import discord
# from emoji import EMOJI_DATA
import emoji as emo
from discord import Member
from discord.ext import commands
from discord.ext.commands import Context
from discord.utils import escape_markdown

from util.data.guild_data import GuildData
from util.decorators import delete_original
from util.virtual_helpers import VirtualHelpers

# from discord.types.emoji import Emoji

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

        embed = VirtualHelpers.default_embed()
        embed.description = "Setting..."

        msg = await ctx.send(embed=embed)

        collect_id = VirtualHelpers.prepare_id(collect_id)
        display_name = display_name[:25]        # Limit display name to 25 chars

        check_emoji = discord.PartialEmoji.from_str(emoji)

        if check_emoji.is_custom_emoji():
            if await ctx.guild.fetch_emoji(check_emoji.id) is None:
                await VirtualHelpers.edit_and_send_embed(
                    msg, embed, "That emoji could not be found. Please try a different one.")
                return
        elif not emo.is_emoji(emoji):
            await VirtualHelpers.edit_and_send_embed(
                msg, embed, "That is not a valid emoji. Please try again!")

        name = GuildData(str(ctx.guild.id)).collectibles.set(collect_id, display_name)
        e = GuildData(str(ctx.guild.id)).collectible_emojis.set(collect_id, emoji)

        await VirtualHelpers.edit_and_send_embed(
            msg, embed, f"Set **{collect_id}** as *{name}* with {e} as the emoji.")

    @collectibles.command(name="delete", aliases=["remove"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def collectible_delete(self, ctx: Context, collect_id: str) -> None:
        """
        Delete a collectible from the server
        """

        collect_id = VirtualHelpers.prepare_id(collect_id)

        res_collectibles = GuildData(str(ctx.guild.id)).collectibles.delete(collect_id)
        res_emojis = GuildData(str(ctx.guild.id)).collectible_emojis.delete(collect_id)
        res_collection = GuildData(str(ctx.guild.id)).collectible_collection.delete_where_collect_id(collect_id)
        res_react = GuildData(str(ctx.guild.id)).collectible_reactions.delete_where_collect_id(collect_id)

        final_result = res_collectibles and res_emojis and res_collection and res_react

        embed = VirtualHelpers.default_embed()

        if final_result:
            embed.description = f"Removed **{collect_id}** from the server."
            await ctx.send(embed=embed)
        else:
            error_code = []
            if not res_collectibles:
                error_code.append("1001")
            if not res_emojis:
                error_code.append("1002")
            if not res_collection:
                error_code.append("1003")
            if not res_react:
                error_code.append("1004")

            joined = 'x'.join(error_code)
            embed.description = f"Unable to remove **{collect_id}** from the server.\n\n ```Error: {joined}```"
            await ctx.send(embed=embed)

    @collectibles.command(name="list", aliases=["collectibles", "show", "view"])
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

        embed = VirtualHelpers.default_embed()

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

        if not user:
            await ctx.send("That user could not be found!", delete_after=7)
            return

        check_exists = GuildData(ctx.guild.id).collectibles.fetch_by_id(collect_id)
        if not check_exists:
            await ctx.send("That collectible does not exist yet!")
            return

        check_already_has = GuildData(ctx.guild.id).collectible_collection.fetch_by_user_id_where(
            str(user.id), collect_id)
        if check_already_has:
            await ctx.send("That user already has that collectible!")
            return

        GuildData(ctx.guild.id).collectible_collection.insert(str(user.id), collect_id)

        await ctx.send(f"*{user.name}* was given the `{collect_id}` collectible!", delete_after=7)

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

        if not user:
            await ctx.send("That user could not be found!", delete_after=7)
            return

        check_exists = GuildData(ctx.guild.id).collectibles.fetch_by_id(collect_id)
        if not check_exists:
            await ctx.send("That collectible does not exist yet!")
            return

        check_has = GuildData(ctx.guild.id).collectible_collection.fetch_by_user_id_where(
            str(user.id), collect_id)
        if not check_has:
            await ctx.send("That user does not have that collectible!")
            return

        GuildData(ctx.guild.id).collectible_collection.delete_where(str(user.id), collect_id)

        await ctx.send(f"Removed the `{collect_id}` collectible from *{user.name}*.")


async def setup(bot):
    await bot.add_cog(Collectibles(bot))
