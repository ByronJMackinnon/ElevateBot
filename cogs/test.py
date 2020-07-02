import traceback
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

import config
from custom_objects import Player
from custom_functions import dbselect, mod_log, dbupdate

async def get_delay():
    return await dbselect('data.db', 'SELECT Delay FROM stats', ())

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test")
    async def _test(self, ctx):
        #await dbupdate('data.db', "UPDATE test SET ti=?", (datetime.now()+timedelta(hours=config.series_timeout),))
        dtobj = await dbselect('data.db', "SELECT ti FROM test", ())
        dtobj = datetime.strptime(dtobj, '%Y-%m-%d %H:%M:%S.%f')
        if dtobj > datetime.now():
            return await ctx.send("Database is more than now")
        elif dtobj < datetime.now():
            return await ctx.send("Database is less than now.")
        else:
            return await ctx.send("I have no fucking clue.")

def setup(bot):
    bot.add_cog(TestCog(bot))