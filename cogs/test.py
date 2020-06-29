import traceback

import discord
from discord.ext import commands

from custom_objects import Player

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test")
    async def _test(self, ctx):
        await ctx.send(int("000000", 16))
        #await ctx.send("This is a placeholder cog for any tests needed to be ran.")

def setup(bot):
    bot.add_cog(TestCog(bot))