# Standard Imports
import typing

# 3rd Party Imports
import aiosqlite
from discord.utils import get

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
