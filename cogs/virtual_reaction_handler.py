import logging
import time

import discord
from discord import Color, Guild, TextChannel, Message
from discord.ext import commands

from util.data.guild_data import GuildData

start_time = time.time()
log = logging.getLogger("smiles")


def prepare_id(uuid: str):  # TODO: Make common method
    return uuid.lower().replace(" ", "_")


class VirtualReactionRoleHandler(commands.Cog, name="Virtual Reaction Role Handler"):
    def __init__(self, bot):
        self.bot = bot

        self.reaction_embed = discord.Embed(title="Virtual Reaction Role", color=Color.og_blurple())

    @commands.Cog.listener("on_raw_reaction_add")
    async def on_raw_reaction_add(self, payload):
        await self.reaction_handle(payload, add_mode=True)

    @commands.Cog.listener("on_raw_reaction_remove")
    async def on_raw_reaction_remove(self, payload):
        await self.reaction_handle(payload, add_mode=False)

    async def reaction_handle(self, payload, add_mode: bool):

        reaction_guild_id = str(payload.guild_id)
        reaction_channel_id = str(payload.channel_id)
        reaction_msg_id = str(payload.message_id)
        reaction_emoji = str(payload.emoji)
        reaction_user_id = str(payload.user_id)

        guild: Guild = self.bot.get_guild(payload.guild_id)

        if not guild:
            return

        user = payload.member if payload.member else await guild.fetch_member(int(reaction_user_id))

        if user == self.bot.user:
            return

        # log.debug(payload)

        reaction_channel: TextChannel = await guild.fetch_channel(int(reaction_channel_id))
        reaction_message: Message = await reaction_channel.fetch_message(int(reaction_msg_id))
        if reaction_message.author != self.bot.user:
            # log.debug("DIFFERENT MESSAGE")
            return

        combined_id = f"{reaction_msg_id}_{reaction_channel_id}"

        reaction_roles_emojis = GuildData(reaction_guild_id).virtual_role_emojis.fetch_all()
        # log.debug(reaction_roles_emojis)

        emojis_filtered = filter(lambda r: reaction_emoji == r[2], reaction_roles_emojis)
        list_emojis = list(emojis_filtered)
        # log.debug(list_emojis)

        reaction_roles_messages = GuildData(reaction_guild_id).virtual_reaction_messages.fetch_all()
        # log.debug(reaction_roles_messages)

        msgs_filtered = filter(lambda r: combined_id == r[2], reaction_roles_messages)
        list_msgs = list(msgs_filtered)
        react_msg = list_msgs[0]
        # log.debug(react_msg)

        reaction_roles = GuildData(reaction_guild_id).virtual_reaction_roles.fetch_all()
        roles_filtered = filter(lambda r: str(react_msg[1]) == r[1], reaction_roles)
        list_roles = list(roles_filtered)

        reaction_role_uuid = None
        for emoji in list_emojis:
            for role in list_roles:
                if emoji[1] == role[2]:
                    reaction_role_uuid = role[2]
                    break

        # log.debug(reaction_role_uuid)

        role_names = GuildData(reaction_guild_id).virtual_roles.fetch_all_by_role_id(reaction_role_uuid)
        role_name = role_names[0][2]

        # await reaction_channel.send(f"You clicked the `{role_name}` role!", delete_after=3)

        if add_mode:
            # log.debug("Add role")

            check_for = GuildData(reaction_guild_id).virtual_role_collection.fetch_by_user_id_where(
                str(reaction_user_id), reaction_role_uuid)
            if check_for:
                return

            GuildData(reaction_guild_id).virtual_role_collection.insert(str(reaction_user_id), reaction_role_uuid)

            await user.send(f"Added the `{role_name}` role!")
        else:
            # log.debug("Remove role")

            # GuildData(reaction_guild_id).virtual_role_collection.delete_all()

            result = GuildData(reaction_guild_id).virtual_role_collection.delete_where(
                str(reaction_user_id), reaction_role_uuid)
            if result:
                await user.send(f"Removed the `{role_name}` role!")

        # log.debug(GuildData(reaction_guild_id).virtual_role_collection.fetch_all())

        # await reaction_channel.send(f"Your roles: `{', '.join(x for _, _, x in GuildData(
        # reaction_guild_id).virtual_role_collection.fetch_all())}`", delete_after=3)

    @commands.Cog.listener("on_raw_message_delete")
    async def on_raw_message_delete(self, payload):

        if payload.cached_message is not None:
            if payload.cached_message.author.id != self.bot.user.id:
                return

        combined_id = f"{payload.message_id}_{payload.channel_id}"

        reaction_message = GuildData(str(payload.guild_id)).virtual_reaction_messages.fetch_all_by_msg_id(combined_id)

        if len(reaction_message) <= 0:
            return

        rm_uuid = reaction_message[0][1]

        GuildData(str(payload.guild_id)).virtual_reaction_messages.delete(rm_uuid)
        GuildData(str(payload.guild_id)).virtual_reaction_roles.delete(rm_uuid)


async def setup(bot):
    await bot.add_cog(VirtualReactionRoleHandler(bot))
