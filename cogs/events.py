import sys
import traceback
import asyncio

import discord
from discord.ext import commands, tasks
from discord.utils import get

import config
from custom_functions import is_in_database, error_log, dbselect
from custom_objects import Player

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mmr_check.start()

    def cog_unload(self):
        self.mmr_check.cancel()

    @tasks.loop(hours=24)
    async def mmr_check(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(config.server_id)
        for member in guild.members:
            player = await Player(member)

            before = player.mmr

            await player.verify_mmr()

            after = player.mmr
            if before != after:
                await mod_log(f"{member.mention}'s MMR was updated.")
            await asyncio.sleep(86400 / guild.member_count)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Checks if the members is already in the database, if not, create a new entry for them."""
        if is_in_database(f'SELECT ID FROM players WHERE ID={member.id}'):
            return
        if not member.bot:
            await DBInsert.member(member)

        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

    @commands.Cog.listener()
    async def on_member_remove(self, member):  # When a member leaves the server
        """Update member count in the database 'stats' table."""
        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await ctx.message.add_reaction(config.checkmark_emoji)

def setup(bot):
    bot.add_cog(Events(bot))