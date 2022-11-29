import copy
import logging
import time

from discord.ext import commands
from discord.ext.commands import Context

# from datetime import timezone
from discord.utils import escape_markdown

from util.data.guild_data import GuildData

start_time = time.time()
log = logging.getLogger("smiles")


def prepare_role_id(role_id: str):
    return role_id.lower().replace(" ", "_")


class VirtualRoles(commands.Cog, name="Virtual Roles"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="virtualroles", aliases=["virtualrole", "virtrole"])
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
    async def virtual_set(self, ctx: Context, role_id: str, *, display_name: str) -> None:
        """
        Set virtual role to the server

        If a role's unique identifier already exists, this will overwrite it.
        """

        msg = await ctx.send("Setting...")

        role_id = prepare_role_id(role_id)
        display_name = display_name[:25]        # Limit display name to 25 chars

        # log.debug(f"{role_id} {display_name}")

        name = GuildData(str(ctx.guild.id)).virtual_roles.set(role_id, display_name)

        # await ctx.send(f"Set **{role_id}** as *{display_name}*.")
        await msg.edit(content=f"Set **{role_id}** as *{name}*.")

    @virtual_roles.command(name="delete", aliases=["remove"])
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def virtual_delete(self, ctx: Context, role_id: str) -> None:
        """
        Delete virtual role from the server
        """

        role_id = prepare_role_id(role_id)

        result = GuildData(str(ctx.guild.id)).virtual_roles.delete(role_id)

        if result:
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
    await bot.add_cog(VirtualRoles(bot))
