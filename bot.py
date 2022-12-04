import asyncio
import datetime
import logging
import time
from logging.handlers import RotatingFileHandler

import discord
from discord.ext import commands

import util.gen_list as GenList
from util.config import BotConfig
from util.data.data_backup import DataBackups
from util.data.data_delete import delete_database_guild
from util.data.guild_data import GuildData
from util.features import get_extensions, get_commands_blacklist
from util.help_command import HelpCommand
from util.logging import ConsoleColorFormatter, CustomLogLevels

log = logging.getLogger("smiles")
start_time = time.time()

# TODO: Global exception handling (make sure errors are spit out to the console)


def get_log_level(name: str):
    valid = ["debug", "info", "warning", "error", "critical"]

    log_cfg = name

    if log_cfg.lower() in valid:
        return getattr(logging, log_cfg.upper())

    if log_cfg.lower() in CustomLogLevels.LOG_LEVELS:
        return CustomLogLevels.LOG_LEVELS[log_cfg.lower()]

    return logging.INFO


# noinspection PyUnresolvedReferences
class Smiles(commands.Bot):
    def __init__(self):

        self.resources_path = "./resources/"

        self.load_config()

        try:
            self.setup_logging()
        except Exception as e:
            log.error(f"Logging error!\n{e}")
            raise Exception(f"Logging error!\n{e}")

        self.logger = log

        log.info("Starting bot...")

        intents = discord.Intents(
            guilds=True,
            members=True,
            messages=True,
            reactions=True,
            presences=True,
            voice_states=True,
            message_content=True
        )

        activity = discord.Activity(name=f"Do {self.bot_key}help", type=discord.ActivityType.playing)
        super().__init__(command_prefix=self.prefix, help_command=HelpCommand(), intents=intents, activity=activity)

        self.extns = get_extensions()

    # noinspection PyAttributeOutsideInit
    def load_config(self):
        self.bot_token = None
        # self.load_music = None
        try:
            log.info("Loading config...")
            self.config = BotConfig()
            self.config_data = self.config.data
            self.bot_data = self.config_data["bot"]
            self.bot_token = self.bot_data["token"]
            self.bot_key = self.bot_data["key"]
            self.bot_owners = self.bot_data["owners"]
            # self.load_music = self.config_data["music"]["enabled"]
            self.create_commands_list = self.config_data["misc"]["create_commands_list"]
            self.logging_data = self.config_data["logging"]

            self.do_run = self.config.do_run
        except KeyError as e:
            log.fatal(f"Config error.\n\tKey Not Loaded: {e}")
            self.do_run = False

    def setup_logging(self):
        log_file = self.logging_data["file"]
        log_console = self.logging_data["console"]

        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.WARNING)
        # logging.getLogger("discord.state").setLevel(logging.INFO)

        current_time = datetime.datetime.now()
        filename = f'{log_file["file_location"]}/{current_time.strftime("%m%y")}.log'

        log.setLevel(get_log_level(log_file["level"]))

        max_bytes = log_file["max_mebibytes"] * 1024 * 1024  # Bytes -> MiB conversion
        handler = RotatingFileHandler(filename=filename, encoding=log_file["encoding"],
                                      mode=log_file["write_mode"], backupCount=log_file["backup_count"],
                                      maxBytes=max_bytes)
        fmt = logging.Formatter(log_file["format"], log_file["date_time_format"], style=log_file["style"])
        handler.setFormatter(fmt)
        log.addHandler(handler)

        console = logging.StreamHandler()
        # console_fmt = logging.Formatter(log_console["format"], log_console["date_time_format"], style=log_console[
        # "style"])
        console_fmt = ConsoleColorFormatter(log_console["format"], log_console["date_time_format"],
                                            style=log_console["style"], colored=log_console["colored"])
        console.setFormatter(console_fmt)
        console.setLevel(get_log_level(log_console["level"]))
        log.addHandler(console)

        CustomLogLevels.add_log_levels()

        log.info(f"Logging initialized. Logging to console and `{filename}`.")
        log.lnbrk("Logging complete")

    def prefix(self, bot, message):
        pfx = self.bot_key
        if message.guild:
            data = GuildData(str(message.guild.id)).strings.fetch_by_name("prefix")
            if data:
                pfx = commands.when_mentioned_or(data)(bot, message)
            else:
                pfx = commands.when_mentioned_or(self.bot_key)(bot, message)
        return pfx if pfx else self.bot_key

    async def load_extensions(self):

        if not self.do_run:
            return

        # Other extensions
        count = 0
        for extension in self.extns:
            try:
                await self.load_extension(extension)
                log.info(f"Cog Loaded | {extension}")
                count += 1
            except Exception as error:
                log.error(f"{extension} cannot be loaded. \n\t[{error}]")
        log.success(f"Loaded {count}/{len(self.extns)} cogs")

    def unload_commands(self):
        bl_cmds = get_commands_blacklist()

        if len(bl_cmds) == 0:
            log.debug("No commands to blacklist")
            return

        count = 0
        for cmd in bl_cmds:
            self.remove_command(cmd)
            log.info(f"Removed {cmd}")
            count += 1

        log.success(f"Removed {count}/{len(bl_cmds)} commands")

    # async def setup_hook(self):
        # log.info("Syncing command tree...")
        # self.tree.copy_global_to(guild=DEV_GUILD)
        # await self.tree.sync(guild=DEV_GUILD)
        # log.info("Synced command tree.")

    async def start_bot(self):
        if self.do_run:
            await super().start(self.bot_token)
        else:
            log.fatal("Startup aborted.")

    def generate_commands_lists(self):
        if self.create_commands_list:
            generator = GenList.Generator(self)
            generator.gen_md_list()
            # generator.gen_list()
            # generator.gen_img_list()

    async def on_ready(self):
        log.success(f"We have logged in as {self.user}")
        log.lnbrk()

        log.success("Bot started in {} seconds".format(str(time.time() - start_time)[:4]))
        log.lnbrk()

        log.debug(f"Bot key: {self.bot_key}")

    async def on_message(self, message):

        if message.author == self.user:
            return

        ctx = await self.get_context(message)
        if ctx:
            if ctx.command and ctx.guild:
                if len(GuildData(str(ctx.guild.id)).disabled_commands
                       .fetch_all_by_name(ctx.command.name)) > 0:
                    await ctx.send(f'`{ctx.command.name}` has been disabled.')
                    return

            # await bot.invoke(ctx) # Uses this so webhooks/bots can use the bot

        # if message.webhook_id:
        #     await bot.invoke(ctx)
        # else:

        await self.process_commands(message)

    @staticmethod
    async def on_guild_join(guild):
        log.info(f"Guild Joined | {guild.id} : {guild.name}")

    @staticmethod
    async def on_guild_remove(guild):
        delete_database_guild(str(guild.id))

        log.info(f"Guild Left | {guild.id} : {guild.name}")


# noinspection PyUnresolvedReferences
async def main():
    log.info("Starting...")

    async with Smiles() as bot:
        await bot.load_extensions()
        log.lnbrk()

        bot.unload_commands()

        DataBackups().backup_databases()
        log.lnbrk()

        bot.generate_commands_lists()
        log.lnbrk()

        await bot.start_bot()

asyncio.run(main())
