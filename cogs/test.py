import discord
from discord.ext import commands

from custom_functions import dbselect, dbupdate

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="test")
    async def _test(self, ctx):
        for member in ctx.guild.members:
            check = await dbselect('data.db', "SELECT ID FROM players WHERE ID=?", (member.id,))
            if check is None:
                await dbupdate('data.db', 'INSERT INTO players (ID, Name, MMR, Team, Logo) VALUES (?, ?, ?, ?, ?)', (member.id, f'{member.name}#{member.discriminator}', None, None, str(member.avatar_url),))
            else:
                await ctx.send("It appears you are already in the database.")

def setup(bot):
    bot.add_cog(Test(bot))
