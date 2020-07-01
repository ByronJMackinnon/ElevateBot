import traceback

import discord
from discord.ext import commands, tasks

from custom_objects import Player
from custom_functions import dbselect, mod_log

async def get_delay():
    return await dbselect('data.db', 'SELECT Delay FROM stats', ())

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test")
    async def _test(self, ctx, *, message):
        embed = discord.Embed(title='test', color=0x00ffff)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(TestCog(bot))