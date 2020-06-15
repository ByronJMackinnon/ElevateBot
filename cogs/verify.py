import traceback

from bs4 import BeautifulSoup
import requests
import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import dbselect, dbupdate, get_player_mmr


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verify", usage="<profile> [platform] (Defaults to Steam)")
    async def _verify(self, ctx, profile, platform=None):
        """
        This command is to be used to get a players rank information

        When using your profile, you should be able to use your vanity name, Steam 64 ID, or the entire steam link.
        DO NOT use your screen name, or whatever you changed your display name too.

        Ex: My display name is BMan.Py, however 'BMan.py" wouldn't work. My URL is https://steamcommunity.com/id/BManRL.
        Please send the entire URL, or just the "BManRL" part at the end. OTHERWISE your url might look something like this.
        https://steamcommunity.com/profiles/6561198175677370 which is also just my profile, without the Vanity. 
        So send the entire link, or just the numbers
        """
        await ctx.message.add_reaction(config.waiting_emoji) # Hourglass Emoji

        # Platform handling
        ps_platforms = ['playstation', 'playstation4', 'ps4', 'ps']
        xbox_platforms = ['xbox', 'xbone', 'xboxone', 'xbox1']
        if platform is None:
            platform = "Steam"
        elif platform.lower() in ps_platforms:
            platform = "PS4"
        elif platform.lower() in xbox_platforms:
            platform = "XboxOne"
        else:
            platform = "Steam"

        # Profile Handling
        if platform == 'Steam' and "steamcommunity.com" in profile:
            profile = profile.split('/')[4]
        
        profile_url = f"https://steamidfinder.com/lookup/{profile}/"
        profile_source = requests.get(profile_url)
        profile_soup = BeautifulSoup(profile_source.text, "html.parser")
        profile_main = profile_soup.find('div', attrs={'class': 'panel-body'})
        codes = profile_main.find_all('code')
        codes = [code.text for code in codes]
        profile = codes[2]

        # API Call
        mmr = await get_player_mmr(platform, profile)

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
