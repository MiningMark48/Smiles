import typing
from enum import Enum
from typing import Union

from discord import Color, Embed, Message, User, Member

from util.data.guild_data import GuildData


class DataResults(Enum):
    """
    Enum class for Data Management results
    """

    SUCCESS_GIVE = "*{0}* was given the `{1}` collectible!"
    SUCCESS_TAKE = "Removed the `{1}` collectible from *{0}*."
    NO_USER = "That user could not be found!"
    NO_COLLECTIBLE = "That collectible does not exist yet!"
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
    def prepare_id(uuid: str):
        return uuid.lower().replace(" ", "_")

    @staticmethod
    def gen_msg_link(message_id: Union[str, int], channel_id: Union[str, int], guild_id: Union[str, int]):
        return f"<https://discord.com/channels/{guild_id}/{channel_id}/{message_id}>"

