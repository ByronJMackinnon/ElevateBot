import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import dbselect, dbupdate

class Fixes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tofix")
    @commands.is_owner()
    async def _tofix(self, ctx, member: discord.Member, *, bug):
        await ctx.message.delete()
        check = await dbselect('data.db', 'SELECT ID FROM fixes WHERE ID=?', (member.id,))
        if check is None:
            await dbupdate('data.db', 'INSERT INTO fixes (ID, Fixes) VALUES (?, ?)', (member.id, 1))
        else:
            await dbupdate('data.db', "UPDATE fixes SET Fixes=Fixes+1 WHERE ID=?", (member.id,))
        bugs = await dbselect('data.db', "SELECT Fixes FROM fixes WHERE ID=?", (member.id,))        
        thank_you = discord.Embed(title="Thank you!", color=0x00ffff, description=f"Thank you for your contribution to bug testing. You are currently at {bugs} found")
        await member.send(embed=thank_you)

        to_fix_channel = get(ctx.guild.text_channels, id=config.to_fix_channel_id)
        bug_embed = discord.Embed(title="Bug Found", color=0xff5500, description=bug)
        bug_embed.add_field(name="Found by:", value=member.mention)
        msg = await to_fix_channel.send(embed=bug_embed)
        await msg.add_reaction(get(ctx.guild.emojis, name='check'))

def setup(bot):
    bot.add_cog(Fixes(bot))