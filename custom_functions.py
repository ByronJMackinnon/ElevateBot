import aiosqlite

import typing

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
    info = await dbselect("data.db", "SELECT * FROM players WHERE ID=?", (member.id,))
    player = PlayerObject(info)
    if player.team is None:
        pass
    else:
        team_id = player.team
        player.team = await Team(int(team_id))
    return player


async def Team(ctx, *, id: typing.Union[int, str]):
    if isinstance(id, int):
        results = await dbselect("data.db", "SELECT * FROM teams WHERE ID=?", (id,))
    else:
        results = await dbselect('data.db', 'SELECT * FROM teams WHERE Name=?', (id,))
    team = TeamObject(results)
    return team
    # Potential Roster? Member objects?
