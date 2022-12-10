import logging
import time

import discord
from discord import Color, Guild, TextChannel, Message
from discord.ext import commands

from util.collectible_helpers import CollectibleHelpers
from util.data.guild_data import GuildData

start_time = time.time()
log = logging.getLogger("smiles")


class CollectiblesReactionHandler(commands.Cog, name="Collectibles Reaction Handler"):
    def __init__(self, bot):
        self.bot = bot

        self.reaction_embed = discord.Embed(title="Collections", color=Color.og_blurple())

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

        reaction_channel: TextChannel = await guild.fetch_channel(int(reaction_channel_id))
        reaction_message: Message = await reaction_channel.fetch_message(int(reaction_msg_id))
        if reaction_message.author != self.bot.user:
            return

        combined_id = f"{reaction_msg_id}_{reaction_channel_id}"

        collectible_emojis = GuildData(reaction_guild_id).collectible_emojis.fetch_all()

        emojis_filtered = filter(lambda r: reaction_emoji == r[2], collectible_emojis)
        list_emojis = list(emojis_filtered)

        collectible_messages = GuildData(reaction_guild_id).collectible_messages.fetch_all()

        msgs_filtered = filter(lambda r: combined_id == r[2], collectible_messages)
        list_msgs = list(msgs_filtered)
        react_msg = list_msgs[0]

        collectible = GuildData(reaction_guild_id).collectible_reactions.fetch_all()
        collect_filtered = filter(lambda r: str(react_msg[1]) == r[1], collectible)
        list_collect = list(collect_filtered)

        collect_id = None
        for emoji in list_emojis:
            for collectible in list_collect:
                if emoji[1] == collectible[2]:
                    collect_id = collectible[2]
                    break

        collect_name = GuildData(reaction_guild_id).collectibles.fetch_by_id(collect_id)
        collect_emoji = GuildData(reaction_guild_id).collectible_emojis.fetch_by_id(collect_id)

        embed = CollectibleHelpers.Embeds.default_embed()

        embed.timestamp = reaction_message.created_at

        if add_mode:
            check_for = GuildData(reaction_guild_id).collectible_collection.fetch_by_user_id_where(
                str(reaction_user_id), collect_id)
            if check_for:
                return

            GuildData(reaction_guild_id).collectible_collection.insert(str(reaction_user_id), collect_id)

            embed.description = f"You got the {collect_emoji} **{collect_name}** collectible!"
            await user.send(embed=embed)
        else:
            result = GuildData(reaction_guild_id).collectible_collection.delete_where(
                str(reaction_user_id), collect_id)
            if result:
                embed.description = f"You removed the {collect_emoji} **{collect_name}** collectible!"
                await user.send(embed=embed)

    @commands.Cog.listener("on_raw_message_delete")
    async def on_raw_message_delete(self, payload):

        if payload.cached_message is not None:
            if payload.cached_message.author.id != self.bot.user.id:
                return

        combined_id = f"{payload.message_id}_{payload.channel_id}"

        reaction_message = GuildData(str(payload.guild_id)).collectible_messages.fetch_all_by_msg_id(combined_id)

        if len(reaction_message) <= 0:
            return

        rm_uuid = reaction_message[0][1]

        GuildData(str(payload.guild_id)).collectible_messages.delete(rm_uuid)
        GuildData(str(payload.guild_id)).collectible_reactions.delete(rm_uuid)


async def setup(bot):
    await bot.add_cog(CollectiblesReactionHandler(bot))
