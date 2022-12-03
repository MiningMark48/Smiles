import calendar
import datetime
import logging
import time
# from datetime import timezone
from io import BytesIO

import discord
from PIL import Image, ImageDraw, ImageFont
from discord import Color
from discord.ext import commands
from fuzzywuzzy import process as fwp

from util.decorators import delete_original

start_time = time.time()
log = logging.getLogger("smiles")


# class TimezoneDropdown(discord.ui.Select['Utility']):
#     def __init__(self, callback, options: list):
#         super().__init__(placeholder="Select Timezone", options=options)
#
#         self.cb = callback
#
#     async def callback(self, interaction: discord.Interaction):
#         await self.cb(interaction.user.id, self.values[0])
#
#
# class TimezoneView(discord.ui.View):
#     def __init__(self, author):
#         super().__init__(timeout=60)
#
#         self.user = author
#
#         self.avail_tzs = dict()
#         self.common_tzs = list()
#         # self.misc_avail_tzs = list()
#
#         for tz in pytz.common_timezones:
#             if "/" not in tz:
#                 # self.misc_avail_tzs.append(tz)
#                 continue
#             self.common_tzs.append(tuple(tz.split("/")))
#
#         for tz in self.common_tzs:
#             country_zones = self.avail_tzs.get(tz[0])
#             if country_zones:
#                 if tz[1] not in country_zones:
#                     country_zones.append(tz[1])
#                     self.avail_tzs.update({tz[0]: country_zones})
#                     continue
#             self.avail_tzs.update({tz[0]: [tz[1]]})
#
#     async def on_timeout(self) -> None:
#         await self.message.delete()
#
#     async def interaction_check(self, interaction: discord.Interaction) -> bool:
#         if self.user == interaction.user:
#             return True
#
#         await interaction.response.send_message(f'Only {self.user.name} can interact. You can try it though!',
#                                                 ephemeral=True)
#         return False
#
#     @discord.ui.select(placeholder="Select Region")
#     async def dropdown_region(self, select: discord.ui.Select, interaction: discord.Interaction):
#
#         async def cb(user_id: str, selection: str):
#             final_timezone = f"{select.values[0]}/{selection}"
#
#             UserData(user_id).strings.set("timezone", final_timezone)
#
# self.clear_items() await interaction.followup.edit_message(message_id=self.message.id, content=f"{
# interaction.user.mention}, timezone set to **{final_timezone}**!", view=self)
#
#         self.clear_items()
#         options = self.avail_tzs.get(select.values[0])
#         chunk_amt = 25
#         chunked_options = [options[i:i + chunk_amt]
#                            for i in range(0, len(options), chunk_amt)]
#         for chunk in chunked_options:
#             self.add_item(item=TimezoneDropdown(
#                 cb, [discord.SelectOption(label=c, value=c) for c in chunk]))
#
#         await interaction.response.edit_message(content="Select a Timezone", view=self)
#
#     @classmethod
#     async def start(cls, ctx):
#         self = cls(ctx.author)
#
#         for country in self.avail_tzs:
#             self.dropdown_region.options.append(
#                 discord.SelectOption(label=country, value=country))
#
#         self.message = await ctx.channel.send("Select a Timezone Region", view=self)
#         return self


class Utility(commands.Cog, name="Utility"):
    def __init__(self, bot):
        self.bot = bot

        # self.trans = googletrans.Translator()

        self.cmd_search_options = None

    @commands.command(aliases=["emojis"])
    @commands.guild_only()
    async def emojilist(self, ctx):
        """Get a list of all emojis for the server"""
        emoji_list = ' '.join(str(x) for x in ctx.guild.emojis)
        await ctx.send(f'**Emojis: **{emoji_list}')

    @commands.hybrid_command()
    @delete_original()
    async def ping(self, ctx):
        """Latency of the bot"""
        await ctx.send(f":ping_pong: Pong! {str(round(self.bot.latency * 1000, 0))[:2]}ms :signal_strength:")

    @commands.command(aliases=["progressbar"])
    @commands.cooldown(2, 30, commands.BucketType.user)
    @delete_original()
    async def progress(self, ctx):
        """See how far into the year we are."""

        async with ctx.typing():
            with Image.new("RGB", (800, 400), 0x202225) as im:

                dt = datetime.date.today()
                year = dt.year
                day = int(dt.strftime("%j"))
                is_leap = calendar.isleap(year)
                total_days = 365 if not is_leap else 366

                percentage = round((day / total_days) * 100)

                text = f'{year} is {percentage}% complete'

                font_size = 70
                font = ImageFont.truetype(f'./resources/fonts/arial.ttf', size=font_size)
                draw = ImageDraw.Draw(im)

                w, h = im.size
                spacing = 25
                shape_h = 75
                prog_width = w - spacing
                outline_size = 5
                shape_bg = ((spacing, (h / 2) - (shape_h / 2)), (prog_width, (h / 2) + (shape_h / 2)))
                shape_bg2 = ((spacing - outline_size, (h / 2) - (shape_h / 2) - outline_size),
                             (prog_width + outline_size, (h / 2) + (shape_h / 2) + outline_size))
                shape_fg = ((spacing, (h / 2) - (shape_h / 2)),
                            (((prog_width / 100) * percentage) + (spacing / 2), (h / 2) + (shape_h / 2)))

                draw.rectangle(shape_bg2, fill=0xffffff)
                draw.rectangle(shape_bg, fill=0x2f3136)

                if isinstance(ctx.channel, discord.TextChannel):
                    draw.rectangle(shape_fg, fill=ctx.message.author.top_role.color.to_rgb())
                else:
                    draw.rectangle(shape_fg, fill=0xb9ae92)

                tw = draw.textsize(text, font)[0]
                draw.text(((w - tw) / 2, 35), text, fill=0xffffff, font=font)

                im = im.crop((0, 0, w, (h / 2) + (shape_h / 2) + spacing))

                final_buffer = BytesIO()
                im.save(final_buffer, "png")

            final_buffer.seek(0)
            file = discord.File(filename=f"progressbar_{year}.png", fp=final_buffer)

            embed = discord.Embed(title="Year Progress", color=Color.dark_theme())
            # embed = discord.Embed(title="Year Progress", color=0xb9ae92)
            # if isinstance(ctx.channel, discord.TextChannel):
            #     embed.__setattr__("color", ctx.message.author.top_role.color)
            embed.set_image(url=f"attachment://progressbar_{year}.png")
            embed.timestamp = ctx.message.created_at

            await ctx.send(file=file, embed=embed)

    @commands.command(aliases=["purge", "nuke"])
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def prune(self, ctx, amt: int):
        """Bulk delete messages (up to 100)"""
        if not amt > 0 and amt <= 100:
            await ctx.send(f'Amount must be between **0** and **100**, you entered `{amt}`')
            return
        await ctx.message.delete()
        await ctx.channel.purge(limit=amt)
        msg = await ctx.send(f'Pruned `{amt}` messages.')
        await msg.delete(delay=3)

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def say(self, ctx, *, msg: str):
        """Make the bot say something"""
        await ctx.message.delete()
        await ctx.send(msg)

    # region Timezone

    # @commands.group(aliases=["tz", "time"])
    # @commands.cooldown(2, 5, commands.BucketType.user)
    # @delete_original()
    # async def timezone(self, ctx):
    #     """Commands that help with user timezones."""
    #
    #     if ctx.invoked_subcommand is None:
    #         await ctx.send(f"Invalid subcommand! ")
    #
    #         msg = copy.copy(ctx.message)
    #         msg.content = f"{ctx.prefix}help {ctx.command}"
    #         new_ctx = await self.bot.get_context(msg, cls=type(ctx))
    #         await self.bot.invoke(new_ctx)
    #
    # @timezone.command(name="set")
    # async def tz_set(self, ctx):
    #     """Set your timezone."""
    #
    #     await TimezoneView.start(ctx)
    #
    # @timezone.command(name="get")
    # async def tz_get(self, ctx, user: typing.Optional[discord.User]):
    #     """Get another user's timezone."""
    #
    #     if not user:
    #         user = ctx.author
    #
    #     tz = UserData(str(user.id)).strings.fetch_by_name("timezone")
    #
    #     if not tz:
    #         return await ctx.send(f"*{user.display_name}* does not have a timezone currently set!")
    #
    #     tz = str(tz)
    #     author_datetime = datetime.datetime.now(pytz.timezone(tz))
    #     author_date = author_datetime.strftime("%B %d, %Y")
    #     author_time = author_datetime.strftime("%I:%M %p")
    #
    #     embed = discord.Embed(color=Color.blurple())
    #     embed.set_author(name=f"{user.display_name} #{user.discriminator}", icon_url=user.avatar.url)
    #     embed.timestamp = ctx.message.created_at
    #
    #     embed.add_field(name="Their Timezone Set", value=tz)
    #     embed.add_field(name="Their Current Date", value=author_date)
    #     embed.add_field(name="Their Current Time", value=author_time)
    #
    #     author_tz = UserData(str(ctx.author.id)).strings.fetch_by_name("timezone")
    #     if author_tz:
    #         author_tz = str(author_tz)
    #         author_datetime = datetime.datetime.now(pytz.timezone(author_tz))
    #         author_date = author_datetime.strftime("%B %d, %Y")
    #         author_time = author_datetime.strftime("%I:%M %p")
    #
    #         embed.add_field(name="Your Timezone", value=author_tz)
    #         embed.add_field(name="Your Current Date", value=author_date)
    #         embed.add_field(name="Your Current Time", value=author_time)
    #
    #     await ctx.send(embed=embed)
    #
    # @timezone.command(name="clear")
    # async def tz_clear(self, ctx):
    #     """Clear your timezone."""
    #
    #     UserData(str(ctx.author.id)).strings.delete("timezone")
    #
    #     await ctx.send(f"{ctx.author.mention}, Your timezone has been erased!", delete_after=10)

    # endregion

    @commands.hybrid_command()
    async def uptime(self, ctx):
        """See how long the bot has been running"""
        current_time = time.time()
        difference = int(round(current_time - start_time))
        time_d = datetime.timedelta(seconds=difference)

        days = time_d.days
        hours = time_d.seconds // 3600
        minutes = (time_d.seconds // 60) % 60
        seconds = time_d.seconds % 60

        text_days = f'{days} day{"" if days == 1 else "s"}'
        text_hours = f'{hours} hour{"" if hours == 1 else "s"}'
        text_minutes = f'{minutes} minute{"" if minutes == 1 else "s"}'
        text_seconds = f'{seconds} second{"" if seconds == 1 else "s"}'
        text = f'{text_days}, {text_hours}, {text_minutes}, and {text_seconds}'

        embed = discord.Embed(title="Uptime", color=Color.dark_theme())
        embed.description = text
        try:
            await ctx.send(embed=embed)
        except discord.HTTPException:
            await ctx.send("Current uptime: " + text)

    @staticmethod
    def fetch_and_sort_members(guild: discord.Guild, reverse=False, include_bots=False):
        members = sorted(guild.members, key=lambda mem: mem.created_at, reverse=reverse)

        if not include_bots:
            members = list(filter(lambda mem: not mem.bot, members))

        return members

    @staticmethod
    def format_years_days(years: int, days: int):
        if years == 0 and days != 0:
            return f"{days} day{'s' if days != 1 else ''}"
        if years != 0 and days == 0:
            return f"{years} year{'s' if years != 1 else ''}"
        return f"{years} year{'s' if years != 1 else ''}, {days} day{'s' if days != 1 else ''}"

    # endregion

    # region Command Search

    @commands.command(name="commandsearch", aliases=["cmdsearch", "search"])
    @commands.cooldown(1, 3)
    async def command_search(self, ctx, *, query: str):
        """
        Search for a command
        """

        # Load if not already loaded
        if self.cmd_search_options is None:
            self.cmd_search_options = self.get_options(self.bot.commands, desc_search=False)

        search_results = self.handle_search(query)

        if len(search_results) <= 0:
            await ctx.send("No search results found!")
            return

        results_txt = f"Command Search Results ({query})\n\n"
        for (res, rat) in search_results:
            if rat == 100:
                res = f"[ {res} ]"
            results_txt += f"{res}\n"
            # results_txt += f"{res} ({rat})\n"

        await ctx.send(f"```{results_txt}```")

    @staticmethod
    def get_options(cmds, desc_search):
        options = []

        for cmd in cmds:
            options.append(str(cmd.name))

            if desc_search:
                options.append(f"'{cmd.name}' : {cmd.help}")  # Description searching

            for alias in cmd.aliases:
                options.append(str(alias))

            if isinstance(cmd, commands.Group):
                for c in cmd.walk_commands():
                    options.append(str(c))

        return options

    def handle_search(self, query):
        search_results = fwp.extract(query, self.search_options, limit=5)
        return search_results

    # endregion


def to_emoji(c):
    base = 0x1f1e6
    return chr(base + c)


async def setup(bot):
    await bot.add_cog(Utility(bot))
