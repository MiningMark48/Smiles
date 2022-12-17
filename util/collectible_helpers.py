import logging
import typing
from enum import Enum
from typing import Union

import discord
import emoji as emo
from discord import Color, Embed, Message, User, Member, Guild

from util.data.guild_data import GuildData

log = logging.getLogger("smiles")


class DataResults(Enum):
    """
    Enum class for Data Management results
    """

    SUCCESS_GIVE = "*{0}* was given the `{1}` collectible!"
    SUCCESS_TAKE = "Removed the `{1}` collectible from *{0}*."
    SUCCESS_SET = "Set **{0}** as *{1}* with {2} as the emoji."
    SUCCESS_DELETE = "Deleted the **{0}** collectible from the server."
    ERROR_DELETE_COLLECTIBLES = "Could not delete the collectible."
    ERROR_DELETE_EMOJI = "Could not delete the emoji."
    ERROR_DELETE_COLLECTION = "Could not remove from collection."
    ERROR_DELETE_REACT = "Could not remove from reactions."
    ERROR_DELETE = "There was an issue deleting that collectible."
    NO_USER = "That user could not be found!"
    NO_COLLECTIBLE = "That collectible does not exist yet!"
    NO_EMOJI = "That emoji could not be found!"
    INVALID_EMOJI = "That emoji is invalid."
    ALREADY_HAS = "That user already has that collectible!"
    DOES_NOT_HAVE = "That user does not have that collectible."


class CollectibleHelpers:
    class Embeds:
        @staticmethod
        def default_embed(title="Collectibles", color=Color.blurple(), author: User = None):
            embed = Embed(title=title, color=color)

            if author:
                embed.set_author(name=author.display_name, icon_url=author.avatar.url)

            return embed

        @staticmethod
        async def edit_and_send_embed(message: Message, embed: Embed, new_desc: str, delete_after=None):
            embed.description = new_desc
            if delete_after:
                await message.edit(embed=embed, delete_after=delete_after)
                return
            await message.edit(embed=embed)

    class Management:

        class Collectibles:

            @staticmethod
            async def create_collectible(guild: Guild, collect_id: str, display_name: str, emoji: str) -> DataResults:
                """
                Create a collectible on a server.

                :param Guild guild: The server to create the collectible for.
                :param str collect_id: The id of the collectible to create. Must be unique.
                :param str display_name: The display name of the collectible to create.
                :param str emoji: The emoji the collectible will use.
                :return DataResults: Returns result of the attempted request
                """

                guild_id = str(guild.id)

                collect_id = CollectibleHelpers.prepare_id(collect_id)
                display_name = display_name[:25]  # Limit display name to 25 chars

                check_emoji = discord.PartialEmoji.from_str(emoji)

                if check_emoji.is_custom_emoji():
                    if await guild.fetch_emoji(check_emoji.id) is None:
                        return DataResults.NO_EMOJI
                elif not emo.is_emoji(emoji):
                    return DataResults.INVALID_EMOJI

                GuildData(guild_id).collectibles.set(collect_id, display_name)
                GuildData(guild_id).collectible_emojis.set(collect_id, emoji)

                return DataResults.SUCCESS_SET

            @staticmethod
            def delete_collectible(guild: Guild, collect_id: str) -> DataResults:
                """
                Delete a collectible from a server.

                :param Guild guild: The server to create the collectible for.
                :param str collect_id: The id of the collectible to create. Must be unique.
                :return DataResults: Returns result of the attempted request
                """

                guild_id = str(guild.id)

                collect_id = CollectibleHelpers.prepare_id(collect_id)

                # noinspection PyBroadException
                try:
                    res_collectibles = GuildData(guild_id).collectibles.delete(collect_id)
                    res_emojis = GuildData(guild_id).collectible_emojis.delete(collect_id)

                    final_result = res_collectibles and res_emojis
                except Exception:
                    final_result = False

                if len(GuildData(guild_id).collectible_collection.fetch_all_by_collect_id(collect_id)) > 0:
                    # noinspection PyBroadException
                    try:
                        GuildData(guild_id).collectible_collection.delete_where_uuid(collect_id)
                    except Exception:
                        log.error("Error deleting from collection.")

                if len(GuildData(guild.id).collectible_reactions.fetch_all_by_collect_id(collect_id)) > 0:
                    # noinspection PyBroadException
                    try:
                        GuildData(guild_id).collectible_reactions.delete_where_collect_id(collect_id)
                    except Exception:
                        log.error("Error deleting from reactions.")

                return DataResults.SUCCESS_DELETE if final_result else DataResults.ERROR_DELETE

            @staticmethod
            def collectible_exists(guild_id: str, collect_id: str) -> bool:
                """
                Check if a collectible exists.

                :param str guild_id: The ID of the guild.
                :param str collect_id: The ID of the collectible to check for.
                :return bool: Returns True if the collectible exists.
                """

                collectible_name = GuildData(guild_id).collectibles.fetch_by_id(collect_id)
                collectible_emoji = GuildData(guild_id).collectible_emojis.fetch_by_id(collect_id)

                return collectible_name and collectible_emoji

            @staticmethod
            def fetch_collectibles(guild_id: str):
                return GuildData(guild_id).collectibles.fetch_all()

            @staticmethod
            def join_data(guild_id: str, collect_id: str, hide_reactions=False, hide_collections=False) -> dict:
                """
                Join collectible data into a dictionary


                :param str guild_id: The guild id to pull data from.
                :param str collect_id: The unique ID of the collectible
                :param bool hide_reactions: If True, reaction data is not shown
                :param bool hide_collections: If True, collection data is not shown
                :return dict: Returns dictionary of all the data joined.
                """

                collect_display_name = GuildData(guild_id).collectibles.fetch_by_id(collect_id)
                collect_emoji = GuildData(guild_id).collectible_emojis.fetch_by_id(collect_id)

                collect_reactions_raw = GuildData(guild_id).collectible_reactions.fetch_all_by_collect_id(collect_id)
                collect_reactions = [c_id for _, c_id, _ in collect_reactions_raw]

                collect_collection_raw = GuildData(guild_id).collectible_collection.fetch_all_by_collect_id(collect_id)
                collect_collection = [c_id for _, c_id, _ in collect_collection_raw]

                # GuildData(guild_id).collectible_messages.

                data = {
                    collect_id: {
                        "display_name": collect_display_name,
                        "emoji": collect_emoji,
                    }
                }

                if not hide_reactions:
                    data[collect_id].update({"reaction_messages": collect_reactions})

                if not hide_collections:
                    data[collect_id].update({"user_collections": collect_collection})

                return data

        class Users:

            @staticmethod
            def add_collectible(user: Member, guild_id: typing.Union[str, int], collect_id: str) -> DataResults:
                """
                Add a collectible to a user

                Checks if both the collectible and user exists

                :param discord.Member user: User to add the collectible to
                :param str guild_id: ID of the server to manage collectibles for
                :param str collect_id: ID of the collectible to add to the user
                :return DataResults: Returns result of the attempted request

                """

                if isinstance(guild_id, int):
                    guild_id = str(guild_id)

                if not user:
                    return DataResults.NO_USER

                check_exists = GuildData(guild_id).collectibles.fetch_by_id(collect_id)
                if not check_exists:
                    return DataResults.NO_COLLECTIBLE

                check_already_has = GuildData(guild_id).collectible_collection.fetch_by_user_id_where(
                    str(user.id), collect_id)
                if check_already_has:
                    return DataResults.ALREADY_HAS

                GuildData(guild_id).collectible_collection.insert(str(user.id), collect_id)

                return DataResults.SUCCESS_GIVE

            @staticmethod
            def remove_collectible(user: Member, guild_id: typing.Union[str, int], collect_id: str) -> DataResults:
                """
                Remove a collectible from a user

                Checks if both the collectible and user exists

                :param discord.Member user: User to remove the collectible from
                :param str guild_id: ID of the server to manage collectibles for
                :param str collect_id: ID of the collectible to remove from the user
                :return DataResults: Returns result of the attempted request

                """

                if isinstance(guild_id, int):
                    guild_id = str(guild_id)

                if not user:
                    return DataResults.NO_USER

                check_exists = GuildData(guild_id).collectibles.fetch_by_id(collect_id)
                if not check_exists:
                    return DataResults.NO_COLLECTIBLE

                check_has = GuildData(guild_id).collectible_collection.fetch_by_user_id_where(
                    str(user.id), collect_id)
                if not check_has:
                    return DataResults.DOES_NOT_HAVE

                GuildData(guild_id).collectible_collection.delete_where(str(user.id), collect_id)

                return DataResults.SUCCESS_TAKE

            @staticmethod
            def has_collectible(guild_id: str, user_id: str, collect_id: str):
                """
                Check if a user has a collectible.

                :param str guild_id: The ID of the guild.
                :param str user_id: The ID of the user to check.
                :param str collect_id: The ID of the collectible to check for.
                :return bool: Returns True if the user has the collectible.
                """

                collectibles = GuildData(guild_id).collectible_collection.fetch_by_user_id_where(user_id, collect_id)
                return True if collectibles else False

    @staticmethod
    def prepare_id(uuid: str):
        return uuid.lower().replace(" ", "_")

    @staticmethod
    def gen_msg_link(message_id: Union[str, int], channel_id: Union[str, int], guild_id: Union[str, int]):
        return f"<https://discord.com/channels/{guild_id}/{channel_id}/{message_id}>"
