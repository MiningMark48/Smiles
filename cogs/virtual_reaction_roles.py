import asyncio
import copy
import logging
import time

from discord import Message, TextChannel
from discord.ext import commands
from discord.ext.commands import Context
from discord.utils import escape_markdown

from util.data.guild_data import GuildData

start_time = time.time()
log = logging.getLogger("smiles")


def prepare_id(uuid: str):  # TODO: Make common method
    return uuid.lower().replace(" ", "_")


class VirtualReactionRoles(commands.Cog, name="Virtual Reaction Roles"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="virtualreaction", aliases=["virtreact"])
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

    @virtual_reaction.command(name="addtomessage", aliases=["addtomsg", "add"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_add_to_msg(self, ctx: Context, role_uuid: str, msg_uuid: str, channel: TextChannel) -> None:
        """
        Add a virtual role to a message.

        If the message does not exist yet, it will ask to create one.

        Role_UUID: The unique identifier of the role you want to add to the message.
        Msg_UUID: The unique identifier of the message you want to add to.
        """

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) <= 100

        async def wait_for_response():
            try:
                return await self.bot.wait_for('message', check=check, timeout=30)
            except asyncio.TimeoutError:
                await ctx.send("Timed out.", delete_after=7)
                return None

        async def send_cancel_message():
            await ctx.send("Ok, no worries!", delete_after=7)

        log.debug("CALLED")

        role_uuid = prepare_id(role_uuid)
        msg_uuid = prepare_id(msg_uuid)

        message_id = GuildData(str(ctx.guild.id)).virtual_reaction_messages.fetch_by_msg_uuid(msg_uuid)

        log.debug(message_id)

        if message_id:
            msg_creating = await ctx.send("Adding reactions to existing message...")

            log.debug(f"FOUND! {message_id}")

            reaction_message = await channel.fetch_message(message_id)

            log.debug(reaction_message)

            reaction_emoji = GuildData(str(ctx.guild.id)).virtual_role_emojis.fetch_by_role_id(role_uuid)
            if not reaction_emoji:
                await ctx.send("Error! Reaction emoji could not be retrieved.")
                return

            log.debug(reaction_message.reactions)

            if reaction_emoji in reaction_message.reactions:    # TODO: make this check reactions (reaction emoji
                # needs to be reaction obj)
                await ctx.send("Error! Message already has that emoji as a reaction.")
                return

            if reaction_message.reactions == 20:
                await ctx.send("Error! Message has max amount of reactions!")
                return

            # log.debug(reaction_emoji)

            await reaction_message.add_reaction(reaction_emoji)

            GuildData(str(ctx.guild.id)).virtual_reaction_messages.set(msg_uuid, reaction_message.id)

            await msg_creating.edit(content="Reactions added.", delete_after=7)

            return

        # noinspection PyListCreation
        messages = [ctx.message]  # Messages that are deleted after message creation.

        messages.append(await ctx.send(
            "It looks like that message doesn't exist yet, would you like to create it? `Yes (Y) / No (N)`"))

        response = await wait_for_response()
        messages.append(response)

        # log.debug(response)

        if not response:
            return

        if response.content.lower() not in ["yes", "y"]:
            await send_cancel_message()
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
        response: Message = await wait_for_response()
        messages.append(response)
        if not response:
            await send_cancel_message()
            return

        message_content = response.content[:2000]

        log.debug(message_content)

        msg_creating = await ctx.send("Creating message...")

        reaction_message = await channel.send(message_content)
        log.debug(reaction_message)

        reaction_emoji = GuildData(str(ctx.guild.id)).virtual_role_emojis.fetch_by_role_id(role_uuid)
        if not reaction_emoji:
            await ctx.send("Error! Reaction emoji could not be retrieved.")
            return

        await reaction_message.add_reaction(reaction_emoji)

        GuildData(str(ctx.guild.id)).virtual_reaction_messages.set(msg_uuid, reaction_message.id)

        await msg_creating.edit(content="Message created.", delete_after=7)
        await ctx.channel.delete_messages(messages)

    @virtual_reaction.command(name="delete", aliases=["remove"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_delete(self, ctx: Context, role_id: str) -> None:
        """
        Delete virtual role from the server
        """

        role_id = prepare_id(role_id)

        result = GuildData(str(ctx.guild.id)).virtual_roles.delete(role_id)

        if result:
            await ctx.send(f"Removed **{role_id}** from the server.")
        else:
            await ctx.send(f"Unable to remove **{role_id}** from the server.")

    @virtual_reaction.command(name="list", aliases=["roles"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_list(self, ctx: Context) -> None:
        """
        List virtual roles on the server
        """

        guild_virtual_roles = GuildData(str(ctx.guild.id)).virtual_roles.fetch_all()

        if not len(guild_virtual_roles) > 0:
            await ctx.send("No tags available!")
            return

        tags = f"{ctx.guild.name} Virtual Roles\n\n"
        for t in sorted(guild_virtual_roles):
            value = t[2]
            value = value.replace("\n", "")
            tags += f"[{t[1]}] {escape_markdown(value[:100])}{'...' if len(value) > 100 else ''}\n"

        parts = [(tags[i:i + 750]) for i in range(0, len(tags), 750)]
        for part in parts:
            part = part.replace("```", "")
            await ctx.send(f"```{part}```")


async def setup(bot):
    await bot.add_cog(VirtualReactionRoles(bot))
