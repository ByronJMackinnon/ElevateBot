import discord
from discord.ext import commands

from custom_functions import dbselect, dbupdate

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

def setup(bot):
    bot.add_cog(Test(bot))
