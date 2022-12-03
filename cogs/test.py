import discord
from discord.ext import commands


class TestView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)

        self.user = author

    async def on_timeout(self) -> None:
        self.button1.disabled = True
        self.button2.disabled = True
        self.button3.disabled = True
        await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user == interaction.user:
            return True

        await interaction.response.send_message(f'Only {self.user.name} can react. Start new if you want to.',
                                                ephemeral=True)
        return False

    @discord.ui.button(label="Green", style=discord.ButtonStyle.green)
    async def button1(self, _, interaction: discord.Interaction) -> None:
        # await interaction.response.send_message(f"Hello {self.user.name}!", ephemeral=True)

        await interaction.response.edit_message(content='Message for Label 1 here')

    @discord.ui.button(label="Red", style=discord.ButtonStyle.red)
    async def button2(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content='Message for Label 2 here')

    @discord.ui.button(label="Blurple w/ Emoji", style=discord.ButtonStyle.blurple, emoji="😄")
    async def button3(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(content='Message for Label 3 here')

    @discord.ui.select(placeholder="Select", options=[discord.SelectOption(label="One", value="1", emoji="1️⃣"),
                                                      discord.SelectOption(label="Two", value="2", emoji="2️⃣"),
                                                      discord.SelectOption(label="Three", value="3", emoji="3️⃣")],
                       max_values=3)
    async def dropdown(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f"Dropdown! `{', '.join(x for x in select.values)}`")

    @classmethod
    async def start(cls, ctx):
        self = cls(ctx.author)
        self.add_item(item=discord.ui.Button(label="Grey, w/link", style=discord.ButtonStyle.blurple,
                                             url="https://twitter.com/miningmark48"))
        self.message = await ctx.channel.send('Components! ', view=self)
        return self


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def components(self, ctx):
        await TestView.start(ctx)


async def setup(bot):
    await bot.add_cog(Test(bot))
