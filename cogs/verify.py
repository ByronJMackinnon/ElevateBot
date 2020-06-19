import traceback
import requests

from bs4 import BeautifulSoup
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
        player_mmr = await get_player_mmr(rocketID)
        await ctx.send(player_mmr)
        return

        # Database update
        await dbupdate('data.db', "UPDATE players SET MMR=? WHERE ID=?", (mmr, ctx.author.id,))

        # Emoji / Message handling
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction(config.checkmark_emoji)

        await dbupdate("data.db", "UPDATE stats SET Players=Players+1", ())

        thank_you_embed = discord.Embed(title="Thank you for verifying.", color=0x00ffff, description=f"Your 3's MMR was calculated at **{mmr}**\n\nPlease, don't forget you can edit your personal logo by using the `updatelogo` command")
        thank_you_embed.set_footer(text="Powered by rocket-planet.gg", icon_url=config.rp_gg_logo)
        await ctx.author.send(embed=thank_you_embed)

    @_verify.error
    async def _verify_error(self, ctx, error):
        """A local handler for verification errors."""
        mod_channel = self.bot.get_channel(config.mod_channel)

        print(error)

        if isinstance(error, AttributeError):
            await alert(ctx, "Profile criteria isn't able to be parsed.")
        elif isinstance(error, IndexError):
            await alert(ctx, "Unable to scrape rank information from your profile.")
        elif isinstance(error, commands.errors.CommandInvokeError):
            await alert(ctx, "No information came back with the RocketID given. Please try again")
        else:
            embed = discord.Embed(title="New Error", color=0xff00ff, description=str(error))
            await mod_channel.send(embed=embed)


async def get_player_mmr(rocketID):
    tag, code = rocketID.split('#')
    headers = {'Authorization': rp_gg_token}
    player_id_response = requests.get(f'{rp_gg_base}/psy-tag/search?PsyTagName={tag}&PsyTagCode={code}', headers=headers)
    player_id_json = player_id_response.json()
    player_id = player_id_json['Result']['MatchedPlayers'][0]['PlayerID']

    player_mmr_response = requests.get(f'{rp_gg_base}/skills/get-player-skill?PlayerID={player_id}', headers=headers)
    player_mmr_skills = player_mmr_response.json()['Result']['Skills']
    player_mmr_raw = player_mmr_skills[3]['MMR']
    player_mmr = round((float(player_mmr_raw) * 20) + 100)
    return player_mmr


def setup(bot):
    bot.add_cog(Verify(bot))
