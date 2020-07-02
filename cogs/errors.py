import discord
from discord.ext import commands

import config
from custom_functions import error_log

class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            # ? Check_any() only throws an error if ALL params are false Doesn't work here.
            if ctx.command.qualified_name == 'player':
                await ctx.send(f"You'll have to verify in the <#{config.verify_channel}> channel, before you can use this command.")
            elif ctx.command.qualified_name == 'team leave':
                player = await Player(ctx.author)
                if player.team is None:
                    await ctx.send('You are not on a team to leave.')
                else:
                    await player.team.remove_player(ctx, ctx.author)
            elif ctx.command.qualified_name == 'challenge':
                await ctx.send("Your team is either, not coming up in the database, or the team has less than 3 players.")
            else:
                await error_log(ctx, error)

        else:
            await error_log(ctx, error)

def setup(bot):
    bot.add_cog(Errors(bot))