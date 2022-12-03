import copy
import logging
import time

import discord
# from emoji import EMOJI_DATA
import emoji as emo
from discord.ext import commands
from discord.ext.commands import Context
from discord.utils import escape_markdown

from util.data.guild_data import GuildData
from util.virtual_helpers import VirtualHelpers

# from discord.types.emoji import Emoji

start_time = time.time()
log = logging.getLogger("smiles")


class VirtualRoles(commands.Cog, name="Virtual Roles"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="virtualroles", aliases=["virtualrole", "virtrole", "vrole"])
    @commands.cooldown(1, 2)
    @commands.guild_only()
    async def virtual_roles(self, ctx):
        """
        Manage virtual roles for the server.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(f"Invalid subcommand! ")

            msg = copy.copy(ctx.message)
            msg.content = f"{ctx.prefix}help {ctx.command}"
            new_ctx = await self.bot.get_context(msg, cls=type(ctx))
            await self.bot.invoke(new_ctx)

    @virtual_roles.command(name="set", aliases=["add"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_set(self, ctx: Context, role_id: str, emoji: str, *, display_name: str) -> None:
        """
        Set virtual role to the server

        If a role's unique identifier already exists, this will overwrite it.
        """

        embed = VirtualHelpers.default_embed()
        embed.description = "Setting..."

        msg = await ctx.send(embed=embed)

        role_id = VirtualHelpers.prepare_id(role_id)
        display_name = display_name[:25]        # Limit display name to 25 chars

        check_emoji = discord.PartialEmoji.from_str(emoji)

        if check_emoji.is_custom_emoji():
            if await ctx.guild.fetch_emoji(check_emoji.id) is None:
                await VirtualHelpers.edit_and_send_embed(
                    msg, embed, "That emoji could not be found. Please try a different emoji.")
                return
        elif not emo.is_emoji(emoji):
            await VirtualHelpers.edit_and_send_embed(
                msg, embed, "That is not a valid emoji. Please try again!")

        name = GuildData(str(ctx.guild.id)).virtual_roles.set(role_id, display_name)
        e = GuildData(str(ctx.guild.id)).virtual_role_emojis.set(role_id, emoji)

        await VirtualHelpers.edit_and_send_embed(
            msg, embed, f"Set **{role_id}** as *{name}* with {e} as the emoji.")

    @virtual_roles.command(name="delete", aliases=["remove"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_delete(self, ctx: Context, role_id: str) -> None:
        """
        Delete virtual role from the server
        """

        role_id = VirtualHelpers.prepare_id(role_id)

        res_roles = GuildData(str(ctx.guild.id)).virtual_roles.delete(role_id)
        res_emojis = GuildData(str(ctx.guild.id)).virtual_role_emojis.delete(role_id)
        res_collect = GuildData(str(ctx.guild.id)).virtual_role_collection.delete_where_role(role_id)
        res_react = GuildData(str(ctx.guild.id)).virtual_reaction_roles.delete_where_role(role_id)

        final_result = res_roles and res_emojis and res_collect and res_react

        embed = VirtualHelpers.default_embed()

        if final_result:
            embed.description = f"Removed **{role_id}** from the server."
            await ctx.send(embed=embed)
        else:
            error_code = []
            if not res_roles:
                error_code.append("1001")
            if not res_emojis:
                error_code.append("1002")
            if not res_collect:
                error_code.append("1003")
            if not res_react:
                error_code.append("1004")

            joined = 'x'.join(error_code)
            embed.description = f"Unable to remove **{role_id}** from the server.\n\n ```Error: {joined}```"
            await ctx.send(embed=embed)

    @virtual_roles.command(name="list", aliases=["roles"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_list(self, ctx: Context) -> None:
        """
        List virtual roles on the server
        """

        guild_virtual_roles = GuildData(str(ctx.guild.id)).virtual_roles.fetch_all()
        guild_virtual_role_emojis = GuildData(str(ctx.guild.id)).virtual_role_emojis.fetch_all()

        sorted_emojis = sorted(guild_virtual_role_emojis)

        embed = VirtualHelpers.default_embed()

        if not len(guild_virtual_roles) > 0:
            embed.description = "There are no available roles!"
            await ctx.send(embed=embed, delete_after=7)
            return

        embed.title += ": List"
        i = 0
        for t in sorted(guild_virtual_roles):
            value = t[2]
            embed.add_field(
                name=f"{sorted_emojis[i][2]} {escape_markdown(value[:100])}{'...' if len(value) > 100 else ''}",
                value=t[1],
                inline=True
            )
            i += 1

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(VirtualRoles(bot))
