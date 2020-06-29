import sys
import traceback

import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import is_in_database, error_log

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Checks if the members is already in the database, if not, create a new entry for them."""
        if is_in_database(f'SELECT ID FROM players WHERE ID={member.id}'):
            return
        if not member.bot:
            await DBInsert.member(member)

        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

    @commands.Cog.listener()
    async def on_member_remove(self, member):  # When a member leaves the server
        """Update member count in the database 'stats' table."""
        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await ctx.message.add_reaction(config.checkmark_emoji)
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        await ctx.message.add_reaction(config.cross_emoji)
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound, )

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'{ctx.command} has been disabled.')

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')
            except discord.HTTPException:
                pass

        elif isinstance(error, commands.errors.CheckFailure):
            # INFO: Each command will have to be specified as only one check can exist.
            # ? Check_any() only throws an error if ALL params are false.
            if ctx.command.qualified_name == 'player':
                await ctx.send(f"You'll have to verify in the <#{config.verify_channel}> channel, before you can use this command.")
            else:
                await error_log(ctx, error)

        else:
            await error_log(ctx, error)

def setup(bot):
    bot.add_cog(Events(bot))