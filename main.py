import os

import discord
from discord.ext import commands

import config
from botToken import token
from custom_functions import dbselect, is_in_database
from custom_objects import DBInsert
from embed_help_command import EmbedHelpCommand


bot = commands.Bot(command_prefix="!", owner_id=144051124272365569, case_insensitive=True, help_command=EmbedHelpCommand(), description="Elevate your Experience.")

for extension in os.listdir('./cogs'):
    if extension.endswith('.py'):
        try:
            bot.load_extension(f'cogs.{extension[:-3]}')
        except Exception as e:
            exc = f"{type(e).__name__}: {e}"
            print(f"Failed to load extension {extension}\n{exc}")


@bot.event
async def on_ready():
    print("Username: {0.name}#{0.discriminator}\nID: {0.id}".format(bot.user))
    print(f"Using discord.py v{discord.__version__}")

    guild = bot.get_guild(config.server_id)
    for member in guild.members:
        if member.bot:
            return
        if await is_in_database(sql=f"SELECT ID FROM players WHERE ID={member.id}"):
            pass
        else:
            await DBInsert().player(member)

@bot.command(name="restart")
@commands.is_owner()
async def _restart(ctx):
    """Restarts the entire bot.
    
    This is mostly useful for Class editing within a production environment."""
    await ctx.author.send("Restarting now...")
    FILEPATH = os.path.abspath(__file__)
    os.system('python3 %s' % (FILEPATH))
    exit()

@bot.command(name='lines')
@commands.is_owner()
async def _lines(ctx):
    paths = []
    files = 0
    main_files = os.listdir()
    for extension in main_files:
        if extension.endswith('.py'):
            paths.append(extension)
    for extension in os.listdir('./cogs'):
        if extension.endswith('.py'):
            paths.append(f'cogs/{extension}')
    lines_of_code = 0
    for file in paths:
        files += 1
        with open(file, 'r') as f:
            for line in f:
                lines_of_code += 1
    await ctx.send(f'{lines_of_code} lines of code make up Elevate Bot.')


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
