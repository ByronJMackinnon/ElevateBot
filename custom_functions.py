# Standard Imports
import typing

# 3rd Party Imports
import aiosqlite
from discord.utils import get

async def dbselect(db, sql, variables):
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


async def dbupdate(db, sql, variables):
    db = await aiosqlite.connect(db)
    cursor = await db.execute(sql, variables)
    await db.commit()
    await cursor.close()
    await db.close()


async def Player(member):
    mmr, team, logo, url = await dbselect("data.db", "SELECT MMR, Team, Logo, URL FROM players WHERE ID=?", (member.id,))
    Player.member = member
    Player.name = f"{member.name}#{member.discriminator}"
    Player.mmr = mmr
    Player.team = team
    Player.logo = logo
    Player.url = url
    if player.team is None:
        pass
    else:
        team_id = Player.team
        Player.team = await Team(int(team_id))
    return player


async def Team(id: int):
    id, name, abbrev, p1, p2, p3, p4, p5, mmr, wins, losses, logo = await dbselect("data.db", "SELECT * FROM teams WHERE ID=?", (id,))

    Team.id = id
    Team.name = name
    Team.abbrev = abbrev
    Team.p1 = p1
    Team.p2 = p2
    Team.p3 = p3
    Team.p4 = p4
    Team.p5 = p5
    Team.mmr = mmr
    Team.wins = wins
    Team.losses = losses
    Team.logo = logo

    ids = [Team.p1, Team.p2, Team.p3, Team.p4, Team.p5]
    ids = list(filter(None, ids))  # Removes any "None" values.

    Team.roster = ids

    return Team
