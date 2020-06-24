# Standard Imports
import string
from datetime import datetime, timedelta

# 3rd Party Imports
import discord
from discord.utils import get

# Custom Imports
import config
from custom_functions import dbupdate, dbselect, team_average, calc_mmr_match_value

class Player(object):
    """Represents a Database object for players/members.
    
    Attributes
    ------------
    member: :class:`discord.Member`
        Players' Member object based off their ID
    name: :class:`str`
        Players' Name | Default: Discord Name and Discriminator. (BMan#6972)
    mmr: :class:`int`
        Indicates if the user is currently muted by their own accord.
    team: :class:`int`
        Indicates if the user is currently deafened by their own accord.
    logo: :class:`str`
        Indicates if the user is currently streaming via 'Go Live' feature.
    """


    async def __new__(cls, member):
        name, mmr, team, logo = await dbselect('data.db', 'SELECT Name, MMR, Team, Logo FROM players WHERE ID=?', (member.id,))
        obj = object().__new__(cls)
        object.__setattr__(obj, 'member', member)
        object.__setattr__(obj, 'name', name)
        object.__setattr__(obj, 'mmr', mmr)
        object.__setattr__(obj, 'logo', logo)
        if team is None:
            object.__setattr__(obj, 'team', team)
        elif team.isdigit():
            object.__setattr__(obj, 'team', Team(self.member.guild, team))
        return obj

    async def save_changes(self):
        db_changes = [self.name, self.mmr, self.team, self.logo]
        await dbupdate('data.db', "UPDATE players SET Name=?, MMR=?, Team=?, Logo=? WHERE ID=?", (*db_changes, self.member.id,))
        return "Changes commited to database."

    async def change_mmr(self, amount):
        self.mmr = self.mmr + amount
        await self.save_changes()

    async def set_logo(self, link):
        self.logo = link
        await self.save_changes()

    async def set_mmr(self, new_mmr):
        self.mmr = new_mmr
        await self.save_changes()

    async def set_name(self, new_name):
        self.name = new_name
        await self.save_changes()

    async def set_team(self, new_team = None):
        if new_team is None:
            pass
        elif new_team.isdigit():
            pass
        else:
            return "No changes made."
        self.team = new_team
        await self.save_changes()

    def __repr__(self):
        return '<Player name={0.name} mmr={0.mmr} logo={0.logo} team={0.team} member={0.member}>'.format(self)

    def __str__(self):
        return f"<@{self.member.id}>"


class Team(object):
    async def __new__(cls, guild, TeamID):
        id_lost, name, abbrev, p1, p2, p3, p4, p5, mmr, wins, losses, logo = await dbselect('data.db', "SELECT * FROM teams WHERE ID=?", (TeamID,))
        raw_players = [p1, p2, p3, p4, p5]
        players = []
        for player in raw_players:
            if player is None:
                pass
            else:
                member = get(guild.members, id=player)
                players.append(member)

        obj = object().__new__(cls)
        object.__setattr__(obj, 'guild', guild)
        object.__setattr__(obj, 'players', players)
        object.__setattr__(obj, 'id', TeamID)
        object.__setattr__(obj, 'name', name)
        object.__setattr__(obj, 'abbrev', abbrev)
        # object.__setattr__(obj, 'p1', p1)
        # object.__setattr__(obj, 'p2', p2)
        # object.__setattr__(obj, 'p3', p3)
        # object.__setattr__(obj, 'p4', p4)
        # object.__setattr__(obj, 'p5', p5)
        object.__setattr__(obj, 'mmr', mmr)
        object.__setattr__(obj, 'wins', wins)
        object.__setattr__(obj, 'losses', losses)
        object.__setattr__(obj, 'logo', logo)
        return obj

    async def verify_mmr(self):
        pass # Average the MMR and commit it to new attribute and save_changes()
        for element in self.players:
            player = Player(element)

    async def save_changes(self):
        db_changes = [self.name, self.abbrev, self.mmr, self.wins, self.losses, self.logo]
        await dbupdate('data.db', "UPDATE teams SET Name=? Abbreviation=?, MMR=?, Wins=?, Losses=?, Logo=? WHERE ID=?", (*db_changes, self.id,))
        await dbupdate('data.db', "UPDATE teams SET Player1=?, Player2=?, Player3=?, Player4=?, Player5=? WHERE ID=?", (*self.players, self.id,))
        return "Changes commited to database."

    async def add_player(self, member):
        if len(self.players) => 5: # If Team is full.
            return #raise TeamFullError

        self.players.append(member.id)

        while len(self.players) < 5:
            self.players.append(None)

        await save_changes()

    async def remove_player(self, member):
        if len(self.players) == 1:
            return # DELETE TEAM FROM DB

        self.players.remove(member.id)
        self.players.append(None)

        await self.save_changes()

    async def set_logo(self, link):
        pass

class Match(object):
    async def __new__(cls, MatchID):
        id_lost, t1, t2, wl1, wl2, gain, loss, timeout, complete = await dbselect('data.db', "SELECT * FROM matches WHERE ID=?", (MatchID,))
        obj = object().__new__(cls)
        object.__setattr__(obj, 'id', MatchID)
        object.__setattr__(obj, 't1', t1)
        object.__setattr__(obj, 't2', t2)
        object.__setattr__(obj, 'wl1', wl1)
        object.__setattr__(obj, 'wl2', wl2)
        object.__setattr__(obj, 'gain', gain)
        object.__setattr__(obj, 'loss', loss)
        object.__setattr__(obj, 'timeout', timeout)
        object.__setattr__(obj, 'complete', complete)
        return obj
