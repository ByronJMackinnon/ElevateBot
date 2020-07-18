import traceback
import sys

import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import alert

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        The event triggered when an error is raised while invoking a command.
        ctx   : Context
        error : Exception
        """

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        if hasattr(ctx.command, 'on_error'):
            return
        
        ignored = (commands.CommandNotFound, commands.UserInputError)
        error = getattr(error, 'original', error)
        
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except:
                pass

        embed = discord.Embed(title="Error Needs Handling.", color=0xff00ff, description=f"Member: {ctx.author.mention}\nChannel: {ctx.channel.mention}")
        if len(ctx.message.content) < 500:
            embed.add_field(name="Content:", value=f"[{ctx.message.content}]({ctx.message.jump_url})", inline=False)
        else:
            embed.add_field(name="Jump Link:", value=f"[Jump!]({ctx.message.jump_url})", inline=False)
        embed.add_field(name="Traceback:", value=f"```{error}```", inline=False)

        mod_channel = get(ctx.guild.text_channels, id=config.mod_channel)
        
        await mod_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(ErrorHandler(bot))