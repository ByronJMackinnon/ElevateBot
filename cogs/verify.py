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


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verify", usage="<RocketID> Ex. BMan#6086")
    async def _verify(self, ctx, *, rocketID):
        # API Call
        player_mmr = await get_player_mmr(rocketID)

        # Database update
        await dbupdate('data.db', "UPDATE players SET MMR=? WHERE ID=?", (player_mmr, ctx.author.id,))

        # Emoji / Message handling
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction(config.checkmark_emoji)

        await dbupdate("data.db", "UPDATE stats SET Players=Players+1", ())

        thank_you_embed = discord.Embed(title="Thank you for verifying.", color=0x00ffff, description=f"Your 3's MMR was calculated at **{player_mmr}**\n\nPlease, don't forget you can edit your personal logo by using the `updatelogo` command")
        thank_you_embed.set_footer(text="Powered by rocket-planet.gg", icon_url=config.rp_gg_logo)
        await ctx.author.send(embed=thank_you_embed)

    @_verify.error
    async def _verify_error(self, ctx, error):
        if isinstance(error, IndexError):
            await alert(ctx, "RocketID returned no results. Please ensure that is the correct RocketID and try again.")
            await mod_log(ctx, error)
        elif isinstance(error, ValueError):
            await alert(ctx, "It appears as though that wasn't the full RocketID. Please enter it with name and tag. (Ex. BMan#6086)")
            await mod_log(ctx, error)
        else:
            await mod_log(ctx, f"**This error was unhandled.**\n{error}")


async def get_player_mmr(rocketID):
    tag, code = rocketID.split('#')
    headers = {'Authorization': rp_gg_token}
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{rp_gg_base}/psy-tag/search?PsyTagName={tag}&PsyTagCode={code}', headers=headers) as resp:
            js = await resp.json()
            player_id = js['Result']['MatchedPlayers'][0]['PlayerID']
            async with session.get(f'{rp_gg_base}/skills/get-player-skill?PlayerID={player_id}', headers=headers) as mmr_resp:
                mmr_js = await mmr_resp.json()
                player_mmr_raw = mmr_js['Result']['Skills'][3]['MMR']
                player_mmr = round((float(player_mmr_raw) * 20) + 100)
                return player_mmr


def setup(bot):
    bot.add_cog(Verify(bot))
