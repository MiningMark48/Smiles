import copy
import logging
import time
from typing import Optional

from discord import Color, Member
from discord.ext import commands
from discord.ext.commands import Context

from util.collectible_helpers import CollectibleHelpers
from util.data.guild_data import GuildData
from util.decorators import delete_original

start_time = time.time()
log = logging.getLogger("smiles")


# TODO:
#   [ ] Add pagination for collectibles viewing
#   [X] Add way to view other users' profiles
#   [ ] Leaderboard of most owned collectibles?


class VirtualProfile(commands.Cog, name="Virtual Profile"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="profile", aliases=["p"])
    @commands.cooldown(1, 2)
    @commands.guild_only()
    async def profile(self, ctx):
        """
        Manage and view your profile!
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(f"Invalid subcommand! ")

            msg = copy.copy(ctx.message)
            msg.content = f"{ctx.prefix}help {ctx.command}"
            new_ctx = await self.bot.get_context(msg, cls=type(ctx))
            await self.bot.invoke(new_ctx)

    @profile.command(name="view", aliases=["see", "v"])
    @commands.guild_only()
    @delete_original()
    async def profile_view(self, ctx: Context, user: Optional[Member] = None) -> None:
        """
        View your profile to see your collectibles and other information!
        """

        profile_user = user if user else ctx.author

        color = profile_user.color if profile_user.color else Color.blurple()
        embed = CollectibleHelpers.Embeds.default_embed(title=f"{profile_user.display_name}'s Profile", color=color)
        if profile_user.avatar and profile_user.avatar.url:
            embed.set_thumbnail(url=profile_user.avatar.url)

        embed.set_footer(text="Sent")
        embed.timestamp = ctx.message.created_at

        embed.add_field(name="Joined Discord", value=profile_user.created_at.date(), inline=True)
        embed.add_field(name="Joined Server", value=profile_user.joined_at.date(), inline=True)

        collectibles = GuildData(ctx.guild.id).collectible_collection.fetch_all_by_user_id(profile_user.id)

        collect_list = []

        if not collectibles:
            collect_list.append("You have no collectibles!")
        else:
            for _, _, collect_id in collectibles:
                collect_display_name = GuildData(ctx.guild.id).collectibles.fetch_all_by_id(collect_id)[0][2]
                collect_emoji = GuildData(ctx.guild.id).collectible_emojis.fetch_all_by_id(collect_id)[0][2]

                collect_list.append(f"{collect_emoji} {collect_display_name}")

        embed.add_field(name="Collectibles", value=' • '.join(collect_list), inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(VirtualProfile(bot))
