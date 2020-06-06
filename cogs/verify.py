from bs4 import BeautifulSoup
import requests
import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import dbselect, dbupdate


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verify")
    async def _verify(self, ctx, profile, platform=None):
        await ctx.message.add_reaction(config.waiting_emoji) # Hourglass Emoji

        # Platform handling
        ps_platforms = ['playstation', 'playstation4', 'ps4', 'ps']
        xbox_platforms = ['xbox', 'xbone', 'xboxone', 'xbox1']
        if platform is None:
            platform = "steam"
        elif platform.lower() in ps_platforms:
            platform = "ps"
        elif platform.lower() in xbox_platforms:
            platform = "xbox"
        else:
            platform = "steam"

        # Profile Handling
        if platform == 'steam' and "steamcommunity.com" in profile:
            profile = profile.split('/')[4]
            profile_url = f"https://steamidfinder.com/lookup/{profile}/"
            profile_source = requests.get(profile_url)
            profile_soup = BeautifulSoup(profile_source.text, "html.parser")
            profile_main = profile_soup.find('div', attrs={'class': 'panel-body'})
            codes = profile_main.find_all('code')
            codes = [code.text for code in codes]
            profile = codes[2]

        # Scraping
        url = f"https://rocketleague.tracker.network/profile/mmr/{platform}/{profile}"
        source_code = requests.get(url)
        soup = BeautifulSoup(source_code.text, 'html.parser')
        main = soup.find("div", attrs={'class': 'card card-list'})

        try:
            spans = main.find_all('span')
        except AttributeError:
            await ctx.message.clear_reactions()
            await ctx.message.add_reaction(config.cross_emoji)

        ranks = [mmr.text for mmr in spans]

        try:
            rank = ranks[4]  # Players 3's MMR
        except IndexError:
            await ctx.message.clear_reactions()
            await ctx.message.add_reaction(config.cross_emoji)

        # Database update
        await dbupdate('data.db', "UPDATE players SET MMR=? WHERE ID=?", (rank, ctx.author.id,))

        # Emoji / Message handling
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction(config.checkmark_emoji)

        await dbupdate("data.db", "UPDATE stats SET Players=Players+1", ())

        await dbupdate("data.db", "UPDATE players SET URL=? WHERE ID=?", (url, ctx.author.id,))


def setup(bot):
    bot.add_cog(Verify(bot))
