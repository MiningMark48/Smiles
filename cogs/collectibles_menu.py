import logging

import discord
from discord import Interaction
from discord.ext import commands
from discord.ext.commands import Context

from util.collectible_helpers import CollectibleHelpers
from util.data.guild_data import GuildData
from util.decorators import delete_original

log = logging.getLogger("smiles")


class CollectiblesDropdown(discord.ui.Select):
    def __init__(self, options: list):
        super().__init__(placeholder="Choose collectibles to delete...", min_values=1, max_values=5, options=options)

    async def callback(self, interaction: Interaction):
        deleted = []
        for col in self.values:
            col_id = [o.description for o in self.options if o.label == col][0].replace("ID: ", "")
            log.debug(f"{col}: {col_id}")
            deleted.append(col_id)
            CollectibleHelpers.Management.Collectibles.delete_collectible(interaction.guild, col_id)

        # TODO: See why this isn't completing correctly

        await interaction.response.send_message(f"Deleted the following roles: {', '.join(deleted)}", ephemeral=True)


class CollectiblesDropdownView(discord.ui.View):
    def __init__(self, options: list):
        super().__init__(timeout=60)

        # self.message = None

        self.add_item(CollectiblesDropdown(options))

    # noinspection PyUnresolvedReferences
    # async def on_timeout(self) -> None:
    #     await self.message.delete()


class CollectiblesMenuView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)

        self.user = author

        self.message = None
        self.value = None

    # noinspection PyUnresolvedReferences
    async def on_timeout(self) -> None:
        # self.collectibles_list.disabled = True
        # self.collectibles_set.disabled = True
        # await self.message.edit(view=self)

        await self.message.delete()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user == interaction.user:
            return True

        await interaction.response.send_message(f'Only {self.user.name} can use this menu.', ephemeral=True)
        return False

    @discord.ui.button(label="List Collectibles", style=discord.ButtonStyle.blurple)
    async def collectibles_list(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = "list"

        # await interaction.response.send_message("Listing collectibles...", ephemeral=True)
        await interaction.response.pong()
        self.stop()
        await self.message.delete()

    @discord.ui.button(label="List Reactions", style=discord.ButtonStyle.blurple)
    async def collectibles_reaction_list(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = "listreactions"

        # await interaction.response.send_message("Listing collectibles...", ephemeral=True)
        await interaction.response.pong()
        self.stop()
        await self.message.delete()

    @discord.ui.button(label="Add Collectible", style=discord.ButtonStyle.green)
    async def collectibles_set(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = "set"

        # await interaction.response.send_message("Add collectibles...", ephemeral=True)
        await interaction.response.pong()
        self.stop()
        await self.message.delete()

    @discord.ui.button(label="Add to Message", style=discord.ButtonStyle.green)
    async def collectibles_add_to_msg(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = "addtomsg"

        # await interaction.response.send_message("Setup beginning...", ephemeral=True)
        await interaction.response.pong()
        self.stop()
        await self.message.delete()

    @discord.ui.button(label="Delete Collectibles", style=discord.ButtonStyle.red)
    async def collectibles_delete(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.value = "delete"

        # await interaction.response.send_message("Select the collectible to delete from the dropdown.", ephemeral=True)
        await interaction.response.pong()
        self.stop()
        await self.message.delete()

    async def do_wait(self, message) -> bool:
        self.message = message
        return await self.wait()


class CollectiblesMenu(commands.Cog, name="Collectibles Menu"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="collectiblesmanager", aliases=["cm", "collectibleshelper", "ch"])
    @commands.has_permissions(manage_guild=True)
    @delete_original()
    async def collectibles_helper(self, ctx: Context):
        """
        Open a menu to help with managing collectibles.
        """

        view = CollectiblesMenuView(author=ctx.author)

        embed = CollectibleHelpers.Embeds.default_embed()
        embed.title = "Collectibles Manager"

        embed.description = "Click the buttons below to manage collectibles!"

        message = await ctx.channel.send(embed=embed, view=view)

        await view.do_wait(message)
        if view.value is None:
            await ctx.send("Time out.", delete_after=7)
        elif view.value == "list":
            await ctx.invoke(self.bot.get_command("c list"))
        elif view.value == "listreactions":
            await ctx.invoke(self.bot.get_command("cr list"))
        elif view.value == "set":
            await ctx.invoke(self.bot.get_command("c set"), collect_id=None, emoji=None, display_name=None)
        elif view.value == "addtomsg":
            await ctx.invoke(self.bot.get_command("cr set"), collect_id=None, msg_uuid=None, channel=None)
        elif view.value == "delete":
            collectibles = CollectibleHelpers.Management.Collectibles.fetch_collectibles(str(ctx.guild.id))

            ops = []
            for c in collectibles:
                emoji = GuildData(ctx.guild.id).collectible_emojis.fetch_by_id(c[1])
                ops.append(discord.SelectOption(label=c[2], description=f"ID: {c[1]}", emoji=emoji))

            ops = sorted(ops, key=lambda col: col.label)
            await ctx.channel.send(content="Select the collectibles to delete.",
                                   view=CollectiblesDropdownView(options=ops))
        else:
            log.error("Button response not found...")

        # await CollectiblesMenuView.start(ctx)


async def setup(bot):
    await bot.add_cog(CollectiblesMenu(bot))
