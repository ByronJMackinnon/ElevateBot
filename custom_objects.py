# Standard Imports
from datetime import datetime, timedelta

# 3rd Party Imports
from discord.utils import get

# Custom Imports
import config
from custom_functions import dbupdate, dbselect, Team

class DBInsert(object):  # Helper Object for Modular addition of database fields.

    async def member(member):
        await dbupdate('data.db', 'INSERT INTO players (ID, Name, MMR, Team, Logo, URL) VALUES (?, ?, ?, ?, ?, ?)', (member.id, f"{member.name}#{member.discriminator}", None, None, str(member.avatar_url), None))

    async def team(ctx, name):
        await dbupdate('data.db', "UPDATE stats SET TeamsRegistered=TeamsRegistered+1", ())  # Creates ID for Team

        id = await dbselect('data.db', "SELECT TeamsRegistered FROM stats", ())  # Grabs ID for team

        abbrev = name.upper()[:4]  # Creates abbreviation. All capitals, first 4 letters of team name

        mmr = await dbselect('data.db', "SELECT MMR FROM players WHERE ID=?", (ctx.author.id,))

        await dbupdate('data.db', "INSERT INTO teams (ID, Name, Abbreviation, Player1, Player2, Player3, Player4, Player5, MMR, Wins, Losses, Logo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (id, name.title(), abbrev, ctx.author.id, None, None, None, None, mmr, 0, 0, config.elevate_logo,))

    async def match(team1, team2):
        id = await dbselect('data.db', "SELECT count(*) FROM matches", ())
        id += 1

        now = datetime.now()
        timeout = now + timedelta(hours=config.series_timeout)

        await dbupdate('data.db', 'INSERT INTO matches (ID, Team1, Team2, WL1, WL2, MMR, Timeout, Complete) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (id, team1, team2, None, None, None, timeout, False))
