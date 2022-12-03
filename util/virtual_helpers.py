from typing import Union

from discord import Color, Embed, Message, User


class VirtualHelpers:
    @staticmethod
    def prepare_id(uuid: str):
        return uuid.lower().replace(" ", "_")

    @staticmethod
    def default_embed(title="Virtual Roles", color=Color.blurple(), author: User = None):
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

    @staticmethod
    def gen_msg_link(message_id: Union[str, int], channel_id: Union[str, int], guild_id: Union[str, int]):
        return f"<https://discord.com/channels/{guild_id}/{channel_id}/{message_id}>"

