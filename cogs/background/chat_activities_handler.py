import logging
import os.path as osp
import random

import discord
import yaml
from discord import Guild, TextChannel, Color
from discord.ext import commands, tasks

from util.data.guild_data import GuildData

log = logging.getLogger("smiles")


class ChatActivitiesHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.activity_loop.start()

        self.quotes = None

    def cog_unload(self) -> None:
        self.activity_loop.cancel()

    def load_motivation(self):
        file_path = "assets/motivation.yml"
        if osp.isfile(file_path):
            with open(file_path, 'r') as file:

                data = yaml.full_load(file)

                log.debug(data)

                self.quotes = data["quotes"]

                log.info(f"Loaded {len(self.quotes)} quotes.")

    async def motivate(self, channel: TextChannel):
        embed = discord.Embed(title="Motivational Quote", color=Color.blurple())

        random.shuffle(self.quotes)
        rand_quote = random.choice(self.quotes)
        share_credit = f"<@{rand_quote['share_credit']}>" if "share_credit" in rand_quote else "`N/A`"

        embed.description = f"> {rand_quote['quote']}\n\nShared by: {share_credit}"

        await channel.send(embed=embed)

    @tasks.loop(minutes=30)
    async def activity_loop(self):
        log.info("Chat activity loop begin...")

        rand_chance = 6     # TODO: Make config

        for guild in self.bot.guilds:
            log.debug(guild)

            rand_draw = random.randint(1, rand_chance)
            if rand_draw == 1:

                act_chan = GuildData(str(guild.id)).strings.fetch_by_name("activity_channel")

                if act_chan:
                    channel = await guild.fetch_channel(act_chan)

                    # TODO: Random activity (once there are more than one to handle)

                    await self.motivate(channel)

    @activity_loop.before_loop
    async def before_activity(self):
        log.info("Waiting for bot before chat activities begin...")
        await self.bot.wait_until_ready()

        log.info("Preparing activity information...")

        self.load_motivation()  # Loads quotes for motivation

        log.info("Chat activities are starting now.")


async def setup(bot):
    await bot.add_cog(ChatActivitiesHandler(bot))
