import traceback
import requests
import aiohttp

from bs4 import BeautifulSoup
import discord
from discord.ext import commands
from discord.utils import get

import config
from botToken import rp_gg_base, rp_gg_token
from custom_functions import dbselect, dbupdate, alert, mod_log
from errors import PlayerError


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verify", help=f"<RocketID> Ex. BMan#6086")
    async def _verify(self, ctx, *, rocketID = None):
        if rocketID is None:
            await ctx.message.delete()
            raise PlayerError("Please enter your RocketID with your command. (Ex. `!verify BMan#6086`)")
        # API Call
        api_id, player_mmr = await get_player_mmr(rocketID)

        # Database update
        await dbupdate('data.db', "UPDATE players SET MMR=?, API_ID=? WHERE ID=?", (player_mmr, api_id, ctx.author.id,))

        # Emoji / Message handling
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction(config.checkmark_emoji)

        thank_you_embed = discord.Embed(title="Thank you for verifying.", color=0x00ffff, description=f"Your 3's MMR was calculated at **{player_mmr}**\n\nPlease, don't forget you can edit your personal logo by using the `player edit logo` command")
        thank_you_embed.set_footer(text="Powered by rocket-planet.gg", icon_url=config.rp_gg_logo)
        await ctx.send(embed=thank_you_embed)

    @_verify.error
    async def _verify_error(self, ctx, error):
        if isinstance(error, IndexError):
            await mod_log(ctx, error)
            raise PlayerError("RocketID returned no results. Please ensure that is the correct RocketID and try again.")
        elif isinstance(error, ValueError):
            await mod_log(ctx, error)
            raise PlayerError("It appears as though that wasn't the full RocketID. Please enter it with name and tag. (Ex. BMan#6086)")
        else:
            await mod_log(ctx, f"**This error was unhandled.**\n{error}")
            # raise PlayerError("Your RocketID did not return expected results. Please make sure it is the correct RocketID and try again.")


async def get_player_mmr(rocketID):
    tag, code = rocketID.split('#')
    headers = {'Authorization': rp_gg_token}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{rp_gg_base}/psy-tag/search?PsyTagName={tag}&PsyTagCode={code}', headers=headers) as resp:
            js = await resp.json()
            api_id = js['Result']['MatchedPlayers'][0]['PlayerID']
            async with session.get(f'{rp_gg_base}/skills/get-player-skill?PlayerID={api_id}', headers=headers) as mmr_resp:
                mmr_js = await mmr_resp.json()
                player_mmr_list = mmr_js['Result']['Skills']
                my_item = next((item for item in player_mmr_list if item["Playlist"] == 13), None)
                player_mmr_raw = my_item["MMR"]
                player_mmr = round((float(player_mmr_raw) * 20) + 100)
                return api_id, player_mmr


def setup(bot):
    bot.add_cog(Verify(bot))
