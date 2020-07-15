import os
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
        pass

def setup(bot):
    bot.add_cog(TestCog(bot))