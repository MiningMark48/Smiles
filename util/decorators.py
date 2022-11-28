import logging
import discord
from discord.ext import commands

# from util.logger import Logger


log = logging.getLogger("tidalbot")

def delete_original():
    """
    Decorator that deletes the original
    Discord message upon command execution.

    :return: boolean
    """

    async def predicate(ctx):
        if ctx.invoked_with != "help":  # Don't try to delete if help command
            if isinstance(ctx.message.channel, discord.TextChannel):
                try:
                    await ctx.message.delete()
                except discord.errors.NotFound as e:
                    log.fatal(f"Unable to delete message.\n\t{e}")
        return True

    return commands.check(predicate)
