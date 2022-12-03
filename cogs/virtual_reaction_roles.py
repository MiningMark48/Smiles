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


class VirtualReactionRoles(commands.Cog, name="Virtual Reaction Roles"):
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
        await ctx.send("Ok, no worries!", delete_after=7)

    @commands.group(name="virtualreaction", aliases=["virtreact", "vreaction", "vreact"])
    @commands.cooldown(1, 2)
    @commands.guild_only()
    async def virtual_reaction(self, ctx):
        """
        Manage virtual reaction roles for the server.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(f"Invalid subcommand! ")

            msg = copy.copy(ctx.message)
            msg.content = f"{ctx.prefix}help {ctx.command}"
            new_ctx = await self.bot.get_context(msg, cls=type(ctx))
            await self.bot.invoke(new_ctx)

    @virtual_reaction.command(name="addtomessage", aliases=["addtomsg", "addrole", "setrole", "add", "set"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_add_to_msg(self, ctx: Context, role_uuid: str, msg_uuid: str, channel: TextChannel) -> None:
        """
        Add a virtual role to a message.

        If the message does not exist yet, it will ask to create one.

        Role_UUID: The unique identifier of the role you want to add to the message.
        Msg_UUID: The unique identifier of the message you want to add to.
        Channel: The channel the message is located.
        """

        role_uuid = VirtualHelpers.prepare_id(role_uuid)
        msg_uuid = VirtualHelpers.prepare_id(msg_uuid)

        combined_id = GuildData(str(ctx.guild.id)).virtual_reaction_messages.fetch_by_msg_uuid(msg_uuid)

        if combined_id:
            message_id = combined_id.split("_")[0]

            msg_creating = await ctx.send("Adding reactions to existing message...")

            reaction_message = await channel.fetch_message(message_id)

            reaction_emoji = GuildData(str(ctx.guild.id)).virtual_role_emojis.fetch_by_role_id(role_uuid)
            if not reaction_emoji:
                await ctx.send("Error! Reaction emoji could not be retrieved.")
                return

            # log.debug(reaction_message.reactions)

            for reaction in reaction_message.reactions:
                if reaction_emoji == reaction.emoji:
                    await msg_creating.edit(content="Error! Unable to add role as the emoji associated with that role "
                                                    "is already on that message with a reaction.", delete_after=7)
                    return

            if reaction_emoji in reaction_message.reactions:
                await ctx.send("Error! Message already has that emoji as a reaction.")
                return

            if reaction_message.reactions == 20:
                await ctx.send("Error! Message has max amount of reactions!")
                return

            await reaction_message.add_reaction(reaction_emoji)

            combined_id = f"{reaction_message.id}_{channel.id}"
            GuildData(str(ctx.guild.id)).virtual_reaction_messages.set(msg_uuid, combined_id)
            GuildData(str(ctx.guild.id)).virtual_reaction_roles.insert(msg_uuid, role_uuid)

            await msg_creating.edit(content="Reactions added.", delete_after=7)

            return

        # noinspection PyListCreation
        messages = [ctx.message]  # Messages that are deleted after message creation.

        messages.append(await ctx.send(
            "It looks like that message doesn't exist yet, would you like to create it? `Yes (Y) / No (N)`"))

        response = await self.wait_for_response(ctx)
        messages.append(response)

        if not response:
            await ctx.send("Error!", delete_after=7)
            return

        if response.content.lower() not in ["yes", "y"]:
            await self.send_cancel_message(ctx)
            return

        # messages.append(await ctx.send("What channel would you like to send your message in? Please mention the "
        #                                "channel."))
        # response: Message = await wait_for_response()
        # messages.append(response)
        # if not response:
        #     await send_cancel_message()
        #     return
        #
        # if not response.channel_mentions:
        #     await ctx.send("No channels were found. Please try setup again.", delete_after=7)
        #     return
        #
        # channel = response.channel_mentions[0]
        # if not isinstance(channel, TextChannel):
        #     await ctx.send("Invalid channel. Please be sure it's a text channel!", delete_after=7)
        #     return
        #
        # channel: TextChannel = channel
        #
        # log.debug(channel)

        messages.append(await ctx.send("What would you like the message to say?"))
        response: Message = await self.wait_for_response(ctx)
        messages.append(response)
        if not response:
            await self.send_cancel_message(ctx)
            return

        message_content = response.content[:2000]

        msg_creating = await ctx.send("Creating message...")

        reaction_message = await channel.send(message_content)

        reaction_emoji = GuildData(str(ctx.guild.id)).virtual_role_emojis.fetch_by_role_id(role_uuid)
        if not reaction_emoji:
            await ctx.send("Error! Reaction emoji could not be retrieved.")
            return

        await reaction_message.add_reaction(reaction_emoji)

        combined_id = f"{reaction_message.id}_{channel.id}"
        GuildData(str(ctx.guild.id)).virtual_reaction_messages.set(msg_uuid, combined_id)
        GuildData(str(ctx.guild.id)).virtual_reaction_roles.insert(msg_uuid, role_uuid)

        await msg_creating.edit(content="Message created.", delete_after=7)
        await ctx.channel.delete_messages(messages)

    @virtual_reaction.command(name="removerolefrommsg", aliases=["deleterole", "removerole", "remrole", "delrole"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_remove_from_message(self, ctx: Context, role_uuid: str,
                                          msg_uuid: str, channel: TextChannel) -> None:
        """
        Remove a virtual role from a message.

        Role_UUID: The unique identifier of the role you want to remove from a message.
        Msg_UUID: The unique identifier of the message you want to remove from.
        Channel: The channel where the message is located.
        """

        role_uuid = VirtualHelpers.prepare_id(role_uuid)
        msg_uuid = VirtualHelpers.prepare_id(msg_uuid)

        combined_id = GuildData(str(ctx.guild.id)).virtual_reaction_messages.fetch_by_msg_uuid(msg_uuid)

        if combined_id:
            message_id = combined_id.split("_")[0]
            msg_removing = await ctx.send("Removing reactions from existing message...")

            reaction_message = await channel.fetch_message(message_id)

            reaction_emoji = GuildData(str(ctx.guild.id)).virtual_role_emojis.fetch_by_role_id(role_uuid)
            if not reaction_emoji:
                await ctx.send("Error! Reaction emoji could not be retrieved.")
                return

            await reaction_message.clear_reaction(reaction_emoji)

            GuildData(str(ctx.guild.id)).virtual_reaction_roles.delete_where(msg_uuid, role_uuid)

            await msg_removing.edit(content=f"Removed **{role_uuid}** role from **{msg_uuid}** message.",
                                    delete_after=7)

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

                deleting_msg = await ctx.send("Ok, deleting now!")

                GuildData(str(ctx.guild.id)).virtual_reaction_messages.delete(msg_uuid)
                await reaction_message.delete()

                await deleting_msg.edit(content="Message deleted!", delete_after=7)
                await ctx.channel.delete_messages(messages)

    @virtual_reaction.command(name="deletemessage", aliases=["removemessage", "delmsg", "remmsg"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def virtual_delete_message(self, ctx: Context, msg_uuid: str, channel: TextChannel) -> None:
        """
        Remove a virtual role message.

        Msg_UUID: The unique identifier of the message you want to remove.
        Channel: The channel where the message is located.
        """

        msg_uuid = VirtualHelpers.prepare_id(msg_uuid)

        combined_id = GuildData(str(ctx.guild.id)).virtual_reaction_messages.fetch_by_msg_uuid(msg_uuid)

        if combined_id:
            message_id = combined_id.split("_")[0]
            msg_removing = await ctx.send("Removing message...")

            GuildData(str(ctx.guild.id)).virtual_reaction_messages.delete(msg_uuid)

            # noinspection PyBroadException
            try:
                reaction_message = await channel.fetch_message(message_id)
                if reaction_message:
                    await reaction_message.delete()
            except Exception:
                await msg_removing.edit(content=f"**{msg_uuid}** message has already been deleted.", delete_after=7)
                return

            await msg_removing.edit(content=f"Removed the **{msg_uuid}** message.",  delete_after=7)

    @virtual_reaction.command(name="listmessages", aliases=["messages", "list"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_list(self, ctx: Context) -> None:
        """
        List virtual reaction roles on the server
        """

        def make_msg_link(message_id, channel_id, guild_id):
            return f"<https://discord.com/channels/{guild_id}/{channel_id}/{message_id}>"

        guild_virtual_msgs = GuildData(str(ctx.guild.id)).virtual_reaction_messages.fetch_all()

        if not len(guild_virtual_msgs) > 0:
            await ctx.send("No messages available!")
            return

        tags = f"**{ctx.guild.name} Virtual Reaction Role Messages**\n\n"
        i = 0
        for t in sorted(guild_virtual_msgs):
            ids = t[2].split("_")
            tags += f"`{t[1]}` {make_msg_link(ids[0], ids[1], ctx.guild.id)}\n"
            i += 1

        parts = [(tags[i:i + 750]) for i in range(0, len(tags), 750)]
        for part in parts:
            part = part.replace("```", "")
            await ctx.send(f"{part}")

    # TODO: Make messages use embeds
    # TODO: Delete all links to a role when a role is delete from the virtual roles list


async def setup(bot):
    await bot.add_cog(VirtualReactionRoles(bot))
