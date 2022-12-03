import asyncio
import copy
import logging
import time

from discord import Message, TextChannel
from discord.ext import commands
from discord.ext.commands import Context

from util.data.guild_data import GuildData
from util.decorators import delete_original
from util.virtual_helpers import VirtualHelpers

start_time = time.time()
log = logging.getLogger("smiles")


# TODO: Add cmd to edit message content

class CollectibleReactions(commands.Cog, name="Collectible Reactions"):
    def __init__(self, bot):
        self.bot = bot

    async def wait_for_response(self, ctx: Context):
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) <= 100

        try:
            return await self.bot.wait_for('message', check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send("Timed out.", delete_after=7)
            return None

    @staticmethod
    async def send_cancel_message(ctx: Context):
        embed = VirtualHelpers.default_embed()
        embed.description = "Ok! No worries. :smile:"
        await ctx.send(embed=embed, delete_after=7)

    @commands.group(name="collectreact", aliases=["creact", "creaction", "cr"])
    @commands.cooldown(1, 2)
    @commands.guild_only()
    async def collectibles_reaction(self, ctx):
        """
        Manage collectible reactions for the server.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(f"Invalid subcommand! ")

            msg = copy.copy(ctx.message)
            msg.content = f"{ctx.prefix}help {ctx.command}"
            new_ctx = await self.bot.get_context(msg, cls=type(ctx))
            await self.bot.invoke(new_ctx)

    @collectibles_reaction.command(name="addtomessage", aliases=["addtomsg", "add", "set", "a"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def collectibles_add_to_msg(self, ctx: Context, collect_id: str, msg_uuid: str, channel: TextChannel) -> None:
        """
        Add a collectible reaction to a message.

        If the message does not exist yet, it will ask to create one.

        Collect_ID: The unique identifier of the collectible you want to add to the message.
        Msg_UUID: The unique identifier of the message you want to add to.
        Channel: The channel the message is located.
        """

        collect_id = VirtualHelpers.prepare_id(collect_id)
        msg_uuid = VirtualHelpers.prepare_id(msg_uuid)

        combined_id = GuildData(str(ctx.guild.id)).collectible_messages.fetch_by_msg_uuid(msg_uuid)

        embed = VirtualHelpers.default_embed()

        if combined_id:
            message_id = combined_id.split("_")[0]

            embed.description = "Adding reactions to existing message..."
            msg_creating = await ctx.send(embed=embed)

            reaction_message = await channel.fetch_message(message_id)

            reaction_emoji = GuildData(str(ctx.guild.id)).collectible_emojis.fetch_by_id(collect_id)
            if not reaction_emoji:
                await VirtualHelpers.edit_and_send_embed(msg_creating, embed,
                                                         "Error! Reaction emoji could not be retrieved.",
                                                         delete_after=7)
                return

            # log.debug(reaction_message.reactions)

            for reaction in reaction_message.reactions:
                if reaction_emoji == reaction.emoji:
                    await VirtualHelpers.edit_and_send_embed(msg_creating, embed,
                                                             "Error! Unable to add collectible as the emoji associated "
                                                             "with that collectible is already on that message with a "
                                                             "reaction.",
                                                             delete_after=7)
                    return

            if reaction_emoji in reaction_message.reactions:
                await VirtualHelpers.edit_and_send_embed(msg_creating, embed,
                                                         "Error! Message already has that emoji as a reaction.",
                                                         delete_after=7)
                return

            if reaction_message.reactions == 20:
                await VirtualHelpers.edit_and_send_embed(msg_creating, embed,
                                                         "Error! Message has max amount of reactions!",
                                                         delete_after=7)
                return

            await reaction_message.add_reaction(reaction_emoji)

            combined_id = f"{reaction_message.id}_{channel.id}"
            GuildData(str(ctx.guild.id)).collectible_messages.set(msg_uuid, combined_id)
            GuildData(str(ctx.guild.id)).collectible_reactions.insert(msg_uuid, collect_id)

            msg_link = VirtualHelpers.gen_msg_link(reaction_message.id, channel.id, ctx.guild.id)
            await VirtualHelpers.edit_and_send_embed(msg_creating, embed,
                                                     f"Reactions were added to your [message]({msg_link}).",
                                                     delete_after=7)

            return

        # noinspection PyListCreation
        messages = [ctx.message]  # Messages that are deleted after message creation.

        messages.append(await ctx.send(
            "It looks like that message doesn't exist yet, would you like to create it? `Yes (Y) / No (N)`"))

        response = await self.wait_for_response(ctx)
        messages.append(response)

        if not response:
            embed.description = "Error! No response."
            await ctx.send(embed=embed, delete_after=7)
            return

        if response.content.lower() not in ["yes", "y"]:
            await self.send_cancel_message(ctx)
            return

        messages.append(await ctx.send("What would you like the message to say?"))
        response: Message = await self.wait_for_response(ctx)
        messages.append(response)
        if not response:
            await self.send_cancel_message(ctx)
            return

        message_content = response.content[:2000]

        embed.description = "Creating message..."
        msg_creating = await ctx.send(embed=embed)

        reaction_message = await channel.send(message_content)

        reaction_emoji = GuildData(str(ctx.guild.id)).collectible_emojis.fetch_by_id(collect_id)
        if not reaction_emoji:
            embed.description = "Error! Reaction emoji could not be retrieved."
            await ctx.send(embed=embed, delete_after=7)
            return

        await reaction_message.add_reaction(reaction_emoji)

        combined_id = f"{reaction_message.id}_{channel.id}"
        GuildData(str(ctx.guild.id)).collectible_messages.set(msg_uuid, combined_id)
        GuildData(str(ctx.guild.id)).collectible_reactions.insert(msg_uuid, collect_id)

        msg_link = VirtualHelpers.gen_msg_link(reaction_message.id, channel.id, ctx.guild.id)
        await VirtualHelpers.edit_and_send_embed(msg_creating, embed, f"[Message]({msg_link}) created.", delete_after=7)

        await ctx.channel.delete_messages(messages)

    @collectibles_reaction.command(name="removefrommsg", aliases=["deletecollect", "removecollect", "dc"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def collectible_remove_from_msg(self, ctx: Context, collect_id: str,
                                          msg_uuid: str, channel: TextChannel) -> None:
        """
        Remove a collectible reaction from a message.

        Collect_ID: The unique identifier of the collectible you want to remove from a message.
        Msg_UUID: The unique identifier of the message you want to remove from.
        Channel: The channel where the message is located.
        """

        collect_id = VirtualHelpers.prepare_id(collect_id)
        msg_uuid = VirtualHelpers.prepare_id(msg_uuid)

        combined_id = GuildData(str(ctx.guild.id)).collectible_messages.fetch_by_msg_uuid(msg_uuid)

        embed = VirtualHelpers.default_embed()

        if combined_id:
            message_id = combined_id.split("_")[0]
            embed.description = "Removing reactions from existing message..."
            msg_removing = await ctx.send(embed=embed)

            reaction_message = await channel.fetch_message(message_id)

            reaction_emoji = GuildData(str(ctx.guild.id)).collectible_emojis.fetch_by_id(collect_id)
            if not reaction_emoji:
                await VirtualHelpers.edit_and_send_embed(msg_removing, embed, "Error! Reaction emoji could not be "
                                                                              "retrieved.", delete_after=7)
                return

            await reaction_message.clear_reaction(reaction_emoji)

            GuildData(str(ctx.guild.id)).collectible_reactions.delete_where(msg_uuid, collect_id)

            await VirtualHelpers.edit_and_send_embed(
                msg_removing, embed, f"Removed **{collect_id}** collectible from **{msg_uuid}** message.", delete_after=7)

            messages = []
            log.debug(len(reaction_message.reactions))
            # Subtracts one for the previously deleted message as the list hasn't updated yet
            if (len(reaction_message.reactions) - 1) <= 0:
                messages.append(await ctx.send("I noticed that the message has no reactions now, would you like me to "
                                               "delete the message now? `Yes (Y) / No (No)`"))
                response: Message = await self.wait_for_response(ctx)
                messages.append(response)
                if not response:
                    await self.send_cancel_message(ctx)
                    return

                if response.content.lower() not in ["yes", "y"]:
                    await self.send_cancel_message(ctx)
                    await ctx.channel.delete_messages(messages)
                    return

                deleting_msg = await ctx.send("Ok, I'm deleting it now!")

                GuildData(str(ctx.guild.id)).collectible_messages.delete(msg_uuid)
                await reaction_message.delete()

                await deleting_msg.edit(content="The message was deleted!", delete_after=7)
                await ctx.channel.delete_messages(messages)

    @collectibles_reaction.command(name="deletemessage", aliases=["removemessage", "delmsg", "remmsg", "dm", "rm"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def collectible_delete_message(self, ctx: Context, msg_uuid: str, channel: TextChannel) -> None:
        """
        Remove a collectible's reaction message.

        Msg_UUID: The unique identifier of the message you want to remove.
        Channel: The channel where the message is located.
        """

        msg_uuid = VirtualHelpers.prepare_id(msg_uuid)

        combined_id = GuildData(str(ctx.guild.id)).collectible_messages.fetch_by_msg_uuid(msg_uuid)

        embed = VirtualHelpers.default_embed()

        if combined_id:
            message_id = combined_id.split("_")[0]
            embed.description = "Removing message..."
            msg_removing = await ctx.send(embed=embed)

            GuildData(str(ctx.guild.id)).collectible_messages.delete(msg_uuid)

            # noinspection PyBroadException
            try:
                reaction_message = await channel.fetch_message(message_id)
                if reaction_message:
                    await reaction_message.delete()
            except Exception:
                await VirtualHelpers.edit_and_send_embed(
                    msg_removing, embed, f"**{msg_uuid}** message has already been deleted.", delete_after=7)
                return

            await VirtualHelpers.edit_and_send_embed(msg_removing, embed, f"Removed the **{msg_uuid}** message.",
                                                     delete_after=7)

    @collectibles_reaction.command(name="listmessages", aliases=["messages", "list"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def collectibles_list(self, ctx: Context) -> None:
        """
        List collectible reactions on the server
        """

        guild_collect_msgs = GuildData(str(ctx.guild.id)).collectible_messages.fetch_all()

        embed = VirtualHelpers.default_embed()
        embed.title += ": Reaction Message List"

        if not len(guild_collect_msgs) > 0:
            embed.description = "No reaction messages available!"
            await ctx.send(embed=embed)
            return

        i = 0
        for t in sorted(guild_collect_msgs):
            ids = t[2].split("_")

            embed.add_field(name=t[1],
                            value=f"[Jump!]({VirtualHelpers.gen_msg_link(ids[0], ids[1], ctx.guild.id)})", inline=True)

            i += 1

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(CollectibleReactions(bot))
