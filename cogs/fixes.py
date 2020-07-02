import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import dbselect, dbupdate

class Fixes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        if payload.channel_id == config.to_fix_channel_id:
            if payload.user_id == 144051124272365569:
                if str(payload.emoji) == "<:check:723985365362278471>":
                    msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                    embed = msg.embeds[0]
                    fixed_channel = self.bot.get_channel(config.fixed_channel_id)
                    fix_msg = await fixed_channel.send(embed=embed)
                    await msg.delete()
                    return

    @commands.command(name="bugs")
    async def _search_bugs(self, ctx, member: discord.Member):
        results = await dbselect_all('data.db', "SELECT * FROM Fixes ORDER BY fixes DESC", ())
        if member.id not in results:
            await ctx.send("That player hasn't found any bugs yet.", delete_after=5)
            return
        total = await dbselect('data.db', "SELECT count(*) FROM Fixes", ())
        index = results.index(member.id)
        bugs = results[index+1]
        if index == 0:
            position = 1
        else:
            position = (index/2) + 1
        await ctx.send(f"Player is ranked **#{int(position)}** out of {total} people in bug testing. with a total of {bugs} found.")

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