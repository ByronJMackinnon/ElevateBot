import os

import discord
from discord.ext import commands
from botToken import token


bot = commands.Bot(command_prefix="!", owner_id=144051124272365569, case_insensitive=True)
initial_extensions = ["cogs.verify", "cogs.teams", "cogs.events", "cogs.matches", "cogs.admin", "cogs.errors"]

for extension in initial_extensions:
    try:
        bot.load_extension(extension)
    except Exception as e:
        exc = f"{type(e).__name__}: {e}"
        print(f"Failed to load extension {extension}\n{exc}")


@bot.event
async def on_ready():
    print("Username: {0.name}#{0.discriminator}\nID: {0.id}".format(bot.user))
    print(f"Using discord.py v{discord.__version__}")

@bot.event
async def on_connect():
    bman = bot.get_user(144051124272365569)
    await bman.send("I have connected again!")

@bot.command(name="restart")
@commands.is_owner()
async def _restart(ctx):
    """Restarts the entire bot.
    
    This is mostly useful for Class editing within a production environment."""
    await ctx.author.send("Restarting now...")
    FILEPATH = os.path.abspath(__file__)
    os.system('python3 %s' % (FILEPATH))
    exit()


@bot.command(name="load")
@commands.is_owner()
async def _load(ctx, extension_name: str):
    """Loads an extension."""
    try:
        bot.load_extension(extension_name)
    except (AttributeError, ImportError) as e:
        await ctx.send(f"```py\n{type(e).__name__}: {str(e)}\n```")
        return
    await ctx.send(f"`{extension_name}` loaded.", delete_after=3)
    await ctx.message.delete()


@bot.command(name="unload")
@commands.is_owner()
async def _unload(ctx, extension_name: str):
    """Unloads an extension."""
    bot.unload_extension(extension_name)
    await ctx.send(f"`{extension_name}` unloaded.", delete_after=3)
    await ctx.message.delete()


@bot.command(name="reload")
@commands.is_owner()
async def _reload(ctx, extension_name: str):
    """Reloads an extension."""
    bot.reload_extension(extension_name)
    await ctx.send(f"`{extension_name}` reloaded.", delete_after=3)
    await ctx.message.delete()

bot.run(token)
