import copy
import logging
import time

import discord
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

        # def clean_emoji(e: str):
        #     e.replace("<", "").replace(">", "").replace

        msg = await ctx.send("Setting...")

        role_id = VirtualHelpers.prepare_id(role_id)
        display_name = display_name[:25]        # Limit display name to 25 chars

        check_emoji = discord.PartialEmoji.from_str(emoji)
        if check_emoji.is_custom_emoji():
            if await ctx.guild.fetch_emoji(check_emoji.id) is None:
                await msg.edit(content="That emoji could not be found. Please try a different emoji.")
                return

        # TODO: Make sure emoji *is* an emoji and not just text

        name = GuildData(str(ctx.guild.id)).virtual_roles.set(role_id, display_name)
        e = GuildData(str(ctx.guild.id)).virtual_role_emojis.set(role_id, emoji)

        await msg.edit(content=f"Set **{role_id}** as *{name}* with {e} as the emoji.")

    @virtual_roles.command(name="delete", aliases=["remove"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_delete(self, ctx: Context, role_id: str) -> None:
        """
        Delete virtual role from the server
        """

        role_id = VirtualHelpers.prepare_id(role_id)

        result = GuildData(str(ctx.guild.id)).virtual_roles.delete(role_id)
        result2 = GuildData(str(ctx.guild.id)).virtual_role_emojis.delete(role_id)

        final_result = result and result2

        if final_result:
            await ctx.send(f"Removed **{role_id}** from the server.")
        else:
            await ctx.send(f"Unable to remove **{role_id}** from the server.")

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

        if not len(guild_virtual_roles) > 0:
            await ctx.send("No roles available!")
            return

        tags = f"{ctx.guild.name} Virtual Roles\n\n"
        i = 0
        for t in sorted(guild_virtual_roles):
            value = t[2]
            value = value.replace("\n", "")
            tags += f"[{t[1]}] {sorted_emojis[i][2]} " \
                    f"{escape_markdown(value[:100])}{'...' if len(value) > 100 else ''}\n"
            i += 1

        parts = [(tags[i:i + 750]) for i in range(0, len(tags), 750)]
        for part in parts:
            part = part.replace("```", "")
            await ctx.send(f"```{part}```")


async def setup(bot):
    await bot.add_cog(VirtualRoles(bot))
