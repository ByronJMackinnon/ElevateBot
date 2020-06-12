from discord.ext import commands

from custom_functions import alert

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return

        ignored = (commands.CommandNotFound)

        error = getattr(error, 'original', error)

        if isinstance(error, ignored):
            return

        await alert(ctx, str(error))

def setup(bot):
    bot.add_cog(ErrorHandler(bot))