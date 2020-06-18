import traceback

from bs4 import BeautifulSoup
import requests_async as requests
import discord
from discord.ext import commands
from discord.utils import get

import config
from botToken import rp_gg_base, rp_gg_token
from custom_functions import dbselect, dbupdate, alert


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verify", usage="<RocketID> Ex. BMan#6086")
    async def _verify(self, ctx, *, rocketID):
        # API Call
        if "#" not in rocketID:
            await ctx.send("Please send your entire RocketID. Tag and Code. (Ex: BMan#6086)")
            return

        player_id = await get_player_id(rocketID)

        if "|" not in player_id:
            await ctx.send("We were unable to find any information with that RocketID. Please ensure you typed it in correctly and try again.")
            return

        mmr = await get_player_mmr(player_id)

        # Database update
        await dbupdate('data.db', "UPDATE players SET MMR=? WHERE ID=?", (mmr, ctx.author.id,))

        # Emoji / Message handling
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction(config.checkmark_emoji)

        await dbupdate("data.db", "UPDATE stats SET Players=Players+1", ())

        thank_you_embed = discord.Embed(title="Thank you for verifying.", color=0x00ffff, description=f"Your 3's MMR was calculated at **{mmr}**\n\nPlease, don't forget you can edit your personal logo by using the `updatelogo` command")

    @_verify.error
    async def _verify_error(self, ctx, error):
        """A local handler for verification errors."""
        mod_channel = self.bot.get_channel(config.mod_channel)

        print(type(error))

        if isinstance(error, AttributeError):
            await alert(ctx, "Profile criteria isn't able to be parsed.")
        elif isinstance(error, IndexError):
            await alert(ctx, "Unable to scrape rank information from your profile.")
        elif isinstance(error, commands.errors.CommandInvokeError):
            await alert(ctx, "No information came back with the RocketID given. Please try again")
        else:
            embed = discord.Embed(title="New Error", color=0xff00ff, description=str(error))
            await mod_channel.send(embed=embed)


async def get_player_id(rocketID):
    try:
        tag, code = rocketID.split('#')
    except Exception as e:
        raise ValueError
        return
    if tag is not None and code is not None:
        async with requests.Session() as session:
            headers = {'Authorization': rp_gg_token}
            response = await session.get(f'{rp_gg_base}/psy-tag/search?PsyTagName={tag}&PsyTagCode={code}', headers=headers)
            json = response.json()
            return json['Result']['MatchedPlayers'][0]['PlayerID']

async def get_player_mmr(playerID):
    async with requests.Session() as session:
        headers = {'Authorization': rp_gg_token}
        print(f'{rp_gg_base}/skills/get-player-skill?PlayerID={playerID}')
        response = await session.get(f'{rp_gg_base}/skills/get-player-skill?PlayerID={playerID}', headers=headers)
        json = response.json()
        print(json)
        stats = json['Result']['Skills']
        stats3s = [item for item in stats if item["Playlist"] == 13][0]
        mmr = stats3s['MMR']
        return round((mmr * 20) + 100)


def setup(bot):
    bot.add_cog(Verify(bot))
