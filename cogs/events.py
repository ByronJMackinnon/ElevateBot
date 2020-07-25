import asyncio

import aiohttp
import discord
from discord.ext import commands, tasks

import config
from botToken import rp_gg_base, rp_gg_token
from custom_functions import dbselect, dbupdate
from custom_objects import DBInsert, Invite

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mmr_cycle.start()

    def cog_unload(self):
        self.mmr_cycle.cancel()

    @tasks.loop(minutes=1)
    async def timeout_scan(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=1)
    async def mmr_cycle(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(config.server_id)
        bman = guild.get_member(config.bman_id)
        for member in guild.members:
            if member.bot:
                pass
            else:
                error_occured = False
                current_mmr, api_id = await dbselect('data.db', "SELECT MMR, API_ID FROM players WHERE ID=?", (member.id,))
                if api_id == None:
                    pass
                else:
                    headers = {'Authorization': rp_gg_token}
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f'{rp_gg_base}/skills/get-player-skill?PlayerID={api_id}', headers=headers) as mmr_resp:
                            mmr_js = await mmr_resp.json()
                            player_mmr_list = mmr_js['Result']['Skills']
                            my_item = next((item for item in player_mmr_list if item["Playlist"] == 13), None)
                            player_mmr_raw = my_item["MMR"]
                            player_mmr = round((float(player_mmr_raw) * 20) + 100)
                            print(f'{member.name}#{member.discriminator} - MMR Now: {type(player_mmr)} MMR Before: {type(current_mmr)}')
                            await dbupdate('data.db', "UPDATE players SET MMR=? WHERE ID=?", (player_mmr, member.id,))
                            delay = 3600 // guild.member_count
                            await asyncio.sleep(delay)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        ctx = await self.bot.get_context(message)

        invite_id = await dbselect('data.db', "SELECT ID FROM invites WHERE Message=?", (message.id,))

        invite = await Invite(ctx, invite_id)

        if payload.user_id in [member.id for member in invite.challenged.members]:
            if str(payload.emoji) == config.checkmark_emoji:
                await DBInsert.match(ctx, invite.challenger, invite.challenged)
                await invite.message.clear_reactions()
                await dbupdate('data.db', "DELETE FROM invites WHERE ID=?", (invite.id,))

            elif str(payload.emoji) == config.cross_emoji:
                await invite.message.clear_reactions()
                await dbupdate('data.db', "DELETE FROM invites WHERE ID=?", (invite.id,))

                embed = discord.Embed(color=0xff0000, description=f"{str(invite.challenged)} denied your request for a series.")

                await ctx.send(embed=embed)
        else:
            return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await DBInsert.player(member)



def setup(bot):
    bot.add_cog(Events(bot))