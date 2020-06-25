import aiohttp
import discord
from discord.ext import commands

import config
from botToken import rp_gg_base, rp_gg_token
from custom_functions import dbselect, dbupdate

class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="verify")
    async def _verify(self, ctx, rocketID):
        # API Call
        player_mmr, player_id = await get_player_mmr(rocketID)

        # Database update
        await dbupdate('data.db', "UPDATE players SET MMR=?, API_ID=? WHERE ID=?", (player_mmr, player_id, ctx.author.id,))
        
        await dbupdate("data.db", "UPDATE stats SET Players=Players+1", ())

        # Emoji / Message handling
        await ctx.message.add_reaction(config.checkmark_emoji)

        # Embed creation
        thank_you_embed = discord.Embed(title="Thank you for verifying.", color=0x00ffff, description=f"Your 3's MMR was calculated at **{player_mmr}**\n\nPlease, don't forget you can edit your personal logo by using the `updatelogo` command")
        thank_you_embed.set_footer(text="Powered by rocket-planet.gg", icon_url=config.rp_gg_logo)
        await ctx.author.send(embed=thank_you_embed)


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
                return player_mmr, player_id

def setup(bot):
    bot.add_cog(Verify(bot))