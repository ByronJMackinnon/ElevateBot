import sys
import traceback

import discord
from discord.ext import commands

import config
from errors import TeamError, CodeError, PlayerError, InappropriateError
from custom_objects import Elevate

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.message.add_reaction(config.cross_emoji)

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        error = getattr(error, 'original', error)

        if isinstance(error, CodeError):
            error_channel = self.bot.get_channel(config.error_channel)
            
            embed = discord.Embed(title='Code Error', color=0xff0000, description=str(error))
            embed.add_field(name='Traceback', value=f'```\n{error.format_exc()}\n```')
            await error_channel.send(embed=embed)

        elif isinstance(error, TeamError):
            embed = discord.Embed(title="Team Error", color=0xff0000, description=str(error))
            await ctx.send(embed=embed)

        elif isinstance(error, PlayerError):
            print("Player Error Triggered?")
            embed = discord.Embed(title="Player Error", color=0xff0000, description=str(error))
            await ctx.send(embed=embed)

        elif isinstance(error, InappropriateError):
            embed = discord.Embed(color=0xff0000, description=str(error))
            await ctx.send(embed=embed)

            mod_channel = self.bot.get_channel(config.mod_channel)

            mod_embed = discord.Embed(title="Something inappropriate was triggered.", color=0xff0000, description=str(error))
            mod_embed.add_field(name='Additional Info', value=f'Member: {ctx.author.mention}\nChannel: {ctx.channel.mention}\nCommand: {ctx.command.qualified_name}\n[Jump!]({ctx.message.jump_url})')
            mod_embed.set_footer(text=f'{ctx.author.name}#{ctx.author.discriminator} | ID: {ctx.author.id}', icon_url=self.bot.user.avatar_url)

            await mod_channel.send(embed=mod_embed)

        else:
            embed = discord.Embed(title="Unhandled Error", color=0xff0000, description='```\n' + f'{str(error)}' + '\n```')
            embed.add_field(name='Additional Info', value=f'Member: {ctx.author.mention}\nCommand: {ctx.command.qualified_name}\nChannel: {ctx.channel.mention}\n[Jump Link]({ctx.message.jump_url})')
            server = Elevate(ctx)
            await server.channels.error.send(embed=embed)

def setup(bot):
    bot.add_cog(ErrorHandler(bot))