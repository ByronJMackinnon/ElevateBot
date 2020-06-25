import traceback

from discord.ext import commands

from custom_objects import Player, Invite

class WrongValueMotherfucker(Exception):
    pass

class TestCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test")
    async def _test(self, ctx):
        value = 'test'
        value = int(value)

    @_test.error
    async def _test_error(self, ctx, error):
        await ctx.send(f"`{dir(error)}`")
        await ctx.send(error.with_traceback)

def setup(bot):
    bot.add_cog(TestCog(bot))