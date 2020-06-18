import traceback

from bs4 import BeautifulSoup
import requests_async as requests
import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import dbselect, dbupdate, get_player_mmr, get_player_id


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verify", usage="<RocketID> Ex. BMan#6086")
    async def _verify(self, ctx, *, rocketID):
        # API Call
        player_id = await get_player_id(rocketID)

        mmr = await get_player_mmr(player_id)

        # Database update
        await dbupdate('data.db', "UPDATE players SET MMR=? WHERE ID=?", (mmr, ctx.author.id,))

        # Emoji / Message handling
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction(config.checkmark_emoji)

        await dbupdate("data.db", "UPDATE stats SET Players=Players+1", ())

    @_verify.error
    async def _verify_error(self, ctx, error):
        """A local handler for verification errors."""
        mod_channel = get(ctx.guild.text_channels, id=config.mod_channel)

        if isinstance(error, AttributeError):
            await alert("Profile criteria isn't able to be parsed.")
        elif isinstance(error, IndexError):
            await alert("Unable to scrape rank information from your profile.")
        else:
            embed = discord.Embed(title="New Error", color=0xff00fff, description=error)
            embed.add_field(name="Type:", value=type(error))
            await mod_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Verify(bot))
