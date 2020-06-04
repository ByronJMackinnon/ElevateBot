import discord
from discord.ext import commands

from custom_functions import dbselect, dbupdate
from custom_objects import DBInsert

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='test')
    async def _test(self, ctx, team1, team2):
        pass

def setup(bot):
    bot.add_cog(Test(bot))
