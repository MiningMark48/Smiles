import asyncio
import copy
import json
import logging
import time
from enum import Enum
from typing import Optional

from discord import Member, Message
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

    async def wait_for_response(self, ctx: Context, timeout=30):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) <= 100

        try:
            return await self.bot.wait_for('message', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            await ctx.send("Timed out.", delete_after=7)
            return None

    async def wait_for_response_dm(self, user: Member, timeout=30):
        def check(m):
            return m.author == user and m.channel == user.dm_channel and len(m.content) <= 100

        try:
            return await self.bot.wait_for('message', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            await user.send("Timed out.", delete_after=7)
            return None

    @staticmethod
    async def send_cancel_message(ctx: Context):
        embed = CollectibleHelpers.Embeds.default_embed()
        embed.description = "Ok! No worries. :smile:"
        await ctx.send(embed=embed, delete_after=7)

    @commands.group(name="collectibles", aliases=["collectible", "collect", "col", "c"])
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
    async def collectible_set(self, ctx: Context, collect_id: Optional[str], emoji: Optional[str],
                              *, display_name: Optional[str]) -> None:
        """
        Set collectibles for the server

        If a collectible's unique identifier already exists, this will overwrite it.
        """

        messages = []

        if not collect_id:
            messages.append(await ctx.send("What would you like the **unique ID** of the collectible to be? "
                                           "This is different than the display name."))

            response: Message = await self.wait_for_response(ctx)
            messages.append(response)

            if not response:
                await self.send_cancel_message(ctx)
                await ctx.channel.delete_messages(messages)
                return

            collect_id = response.content

        if not emoji:
            messages.append(await ctx.send("What would you like the **emoji** of the collectible to be?"))

            response: Message = await self.wait_for_response(ctx)
            messages.append(response)

            if not response:
                await self.send_cancel_message(ctx)
                await ctx.channel.delete_messages(messages)
                return

            emoji = response.content

        if not display_name:
            messages.append(await ctx.send("What would you like the **display name** of the collectible to be?"))

            response: Message = await self.wait_for_response(ctx)
            messages.append(response)

            if not response:
                await self.send_cancel_message(ctx)
                await ctx.channel.delete_messages(messages)
                return

            display_name = response.content

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

    @collectibles.command(name="trade")
    @commands.guild_only()
    async def collectibles_trade(self, ctx: Context, user: Member, collectible_give: str, collectible_receive: str):
        """
        Trade a collectible with another user.

        User: The user to trade with
        Collectible_Give: The ID of the collectible to give.
        Collectible_Receive: The ID of the collectible to receive.
        """

        if not user or not await ctx.guild.fetch_member(user.id):
            await ctx.send("That user could not be found!", delete_after=7)
            return

        if collectible_give == collectible_receive:
            await ctx.send("Those are the same collectibles!")
            return

        author_has = CollectibleHelpers.Management.Users.has_collectible(
            str(ctx.guild.id), str(ctx.author.id), collectible_give)
        if not author_has:
            await ctx.send("You do not have that collectible!", delete_after=7)
            return

        user_has = CollectibleHelpers.Management.Users.has_collectible(
            str(ctx.guild.id), str(user.id), collectible_receive)
        if not user_has:
            await ctx.send("That user does not have that collectible!", delete_after=7)
            return

        author_has_want = CollectibleHelpers.Management.Users.has_collectible(
            str(ctx.guild.id), str(ctx.author.id), collectible_receive)
        if author_has_want:
            await ctx.send("You already have that collectible!", delete_after=7)
            return

        user_has_get = CollectibleHelpers.Management.Users.has_collectible(
            str(ctx.guild.id), str(user.id), collectible_give)
        if user_has_get:
            await ctx.send("That user already has that collectible!", delete_after=7)
            return

        await ctx.send(f"Asking {user.mention} if they want to trade...", delete_after=7)

        await user.send(f"{ctx.author.mention} wants to trade his `{collectible_give}` collectible for your "
                        f"`{collectible_receive}` collectible! \n\nWould you like to accept this trade? "
                        f"`(Yes (Y)/ No (N))`")

        response = await self.wait_for_response_dm(user, timeout=60)

        if not response:
            return

        if response.content.lower() not in ["yes", "y"]:
            await user.send("Ok!")
            await ctx.send(f"{ctx.author.mention}, {user.mention} did not want to trade.")
            return

        # Add receiving collectible
        CollectibleHelpers.Management.Users.add_collectible(ctx.author, ctx.guild.id, collectible_receive)

        # Add giving collectible
        CollectibleHelpers.Management.Users.add_collectible(user, ctx.guild.id, collectible_give)

        # Take giving collectible
        CollectibleHelpers.Management.Users.remove_collectible(ctx.author, ctx.guild.id, collectible_give)

        # Take receiving collectible
        CollectibleHelpers.Management.Users.remove_collectible(user, ctx.guild.id, collectible_receive)

        await ctx.send("Trade successful!")
        await user.send("Trade successful!")

        # TODO: Upon successful trade, invoke the profile view command so they see their updated profile


async def setup(bot):
    await bot.add_cog(Collectibles(bot))
