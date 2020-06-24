# Standard Imports
import typing

# 3rd Party Imports
import requests_async as requests
import asyncio

import aiosqlite
import discord
from discord.utils import get

# Custom Imports
import config
from botToken import rp_gg_token, rp_gg_base

async def dbselect_all(db, sql, variables):
    db = await aiosqlite.connect(db)
    cursor = await db.execute(sql, variables)
    rows = await cursor.fetchall()
    await cursor.close()
    await db.close()

    values = [item for t in rows for item in t]

    return values

async def dbselect(db, sql, variables):  # Helper function for grabbing information from database asynchronously.
    db = await aiosqlite.connect(db)
    cursor = await db.execute(sql, variables)
    row = await cursor.fetchone()
    await cursor.close()
    await db.close()

    # If nothing is returned - Nothing happens
    if row is None:
        pass

    # If only a single result returned. It gets turned to it's proper Data Type
    elif len(row) == 1:
        try:
            row = int(row[0])
        except TypeError:
            row = str(row[0])
        except ValueError:
            row = str(row[0])

    # Otherwise it is returned as a list.
    else:
        row = list(row)

    return row


async def dbupdate(db, sql, variables):  # Helper function for updating information from database asynchronously.
    db = await aiosqlite.connect(db)
    cursor = await db.execute(sql, variables)
    await db.commit()
    await cursor.close()
    await db.close()


async def team_average(teamID):
    players = await dbselect('data.db', "SELECT Player1, Player2, Player3, Player4, Player5 FROM teams WHERE ID=?", (teamID,))

    players = list(filter(None, players))

    mmrs = []

    for player in players:
        mmr = await dbselect('data.db', "SELECT MMR FROM players WHERE ID=?", (player,))
        mmrs.append(int(mmr))

    average = round(sum(mmrs) / len(mmrs))

    await dbupdate('data.db', "UPDATE teams SET MMR=? WHERE ID=?", (average, teamID,))
    return average

async def calc_mmr_match_value(diff):
    if diff >= 0 and diff < 25:
        value = 9, 9
    elif diff >= 25 and diff < 50:
        value = 10, 8
    elif diff >= 50 and diff < 75:
        value = 11, 7
    elif diff >= 75 and diff < 100:
        value = 12, 6
    else:
        value = 13, 5
    return value

async def alert(ctx, message):
    embed = discord.Embed(title="Error.", color=0xff0000, description=message)
    embed.set_footer(text="Powered by rocket-planet.gg", icon_url=config.rp_gg_logo)
    await ctx.send(embed=embed, delete_after=5)

async def mod_log(ctx, message):
    embed = discord.Embed(title="Error.", color=0xff0000, description=message)
    embed.add_field(name="Details:", value=f"Person: {ctx.author.mention}\nChannel: {ctx.channel.mention}\nMessage Content: **{ctx.message.content}**")
    mod_channel = get(ctx.guild.text_channels, id=config.mod_channel)
    await mod_channel.send(embed=embed)
    return

async def send_confirm(ctx, message):
    embed = discord.Embed(title="Success.", color=0x00ff00, description=message)
    embed.set_footer(text="Powered by rocket-planet.gg", icon_url=config.rp_gg_logo)
    await ctx.send(embed=embed, delete_after=5)

async def is_in_database(*, sql):
    check = await dbselect('data.db', sql, ()):
    if check is None:
        return False
    return True