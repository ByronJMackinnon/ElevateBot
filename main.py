import os
import importlib
import inspect

import discord
from discord.ext import commands

import config
from botToken import token
from custom_functions import dbselect
from custom_objects import DBInsert


bot = commands.Bot(command_prefix="!", owner_id=144051124272365569, case_insensitive=True)

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

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over the League."))

    guild = bot.get_guild(config.server_id)
    new_players = []
    for member in guild.members:
        check = await dbselect('data.db', "SELECT Name FROM players WHERE ID=?", (member.id,))
        if member.bot:
            return
        await DBInsert().player(member)
        new_players.append(member.mention)
    if len(added_players) > 0:
        await bot.wait_until_ready()
        bman = bot.get_user(144051124272365569)
        added_players = '\n'.join(new_players)
        await bman.send(f'{len(new_players)} added to the database.\n```{added_players}```')

@bot.command(name='lines')
@commands.is_owner()
async def _lines(ctx):
    paths = []
    main_files = os.listdir()
    for extension in main_files:
        if extension.endswith('.py'):
            paths.append(extension)
    for extension in os.listdir('./cogs'):
        if extension.endswith('.py'):
            paths.append(f'cogs/{extension}')
    lines_of_code = 0
    for file in paths:
        with open(file, 'r') as f:
            for line in f:
                lines_of_code += 1
    await ctx.send(f"It took <@{144051124272365569}> {format(lines_of_code, ',')} lines of code to create ElevateBot.", allowed_mentions=discord.AllowedMentions(users=False))

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
