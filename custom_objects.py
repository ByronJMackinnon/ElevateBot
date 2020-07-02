# Standard Imports
import string
from datetime import datetime, timedelta

# 3rd Party Imports
import aiohttp
import discord
from discord.utils import get

# Custom Imports
import config
from custom_functions import dbupdate, dbselect, team_average, calc_mmr_match_value, is_in_database
from botToken import rp_gg_base, rp_gg_token
from cogs.verify import Verify


class Player(object):
    """Represents a Database object for players/members.
    
    Attributes
    ------------
    member: :class:`discord.Member`
        Players' Member object based off their ID
    name: :class:`str`
        Players' Name | Default: Discord Name and Discriminator. (BMan#6972)
    mmr: :class:`int`
        Players' MMR value.
    team: :class:`int`
        Team player is currently playing for.
    logo: :class:`str`
        Player Logo link
    api_id: :class:`str`
        Player's ID for API Call
    """


    async def __new__(cls, ctx, member):
        id_lost, name, mmr, team, logo, api_id, color= await dbselect('data.db', 'SELECT * FROM players WHERE ID=?', (member.id,))
        if team is None:
            pass
        else:
            team = await Team(ctx, team)
        obj = object().__new__(cls)
        object.__setattr__(obj, 'color', color)
        object.__setattr__(obj, 'member', member)
        object.__setattr__(obj, 'name', name)
        object.__setattr__(obj, 'mmr', mmr)
        object.__setattr__(obj, 'logo', logo)
        object.__setattr__(obj, 'api_id', api_id)
        object.__setattr__(obj, 'team', team)
        return obj

    async def verify_mmr(self):
        headers = {'Authorization': rp_gg_token}
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{rp_gg_base}/skills/get-player-skill?PlayerID={self.api_id}', headers=headers) as mmr_resp:
                mmr_js = await mmr_resp.json()
                player_mmr_raw = mmr_js['Result']['Skills'][3]['MMR']
                player_mmr = round((float(player_mmr_raw) * 20) + 100)
                self.mmr = player_mmr
                await dbupdate('data.db', "UPDATE players SET MMR=? WHERE ID=?", (self.mmr, self.member.id,))

    async def save_changes(self):
        await self.verify_mmr()
        if isinstance(self.team, Team):
            self.team = self.team.id
        db_changes = [self.name, self.team, self.logo, self.color]
        await dbupdate('data.db', "UPDATE players SET Name=?, Team=?, Logo=?, Color=? WHERE ID=?", (*db_changes, self.member.id,))
        return "Changes commited to database."

    async def change_mmr(self, amount):
        self.mmr = self.mmr + amount
        await self.save_changes()

    async def set_color(self, color):
        self.color = color
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
    """Represents a Database object for Teams.
    
    Attributes
    ------------
    guild: :class:`discord.Guild`
        Guild object for elevate. (Used for grabbing member objects from IDs.)
    players: :class:`list`
        Players for team. list of member objects
    id: :class:`int`
        Team Identifier.
    name: :class:`str`
        Team Name.
    abbrev: :class:`str`
        Team abbreviation/club tag.
    mmr: :class:`int`
        Teams Average MMR
    wins: :class:`int`
        Teams Wins reported
    losses: :class:`int`
        Teams Losses reported
    logo: :class:`str`
        Teams Logo link.
    color: :class:`int`
        Number representation base 16 of color
    """

    async def __new__(cls, ctx, TeamID):
        id_lost, name, abbrev, p1, p2, p3, p4, p5, mmr, tier, wins, losses, logo, color = await dbselect('data.db', "SELECT * FROM teams WHERE ID=?", (TeamID,))
        
        raw_players = [p1, p2, p3, p4, p5]  # All player slots
        raw_players = list(filter(None, raw_players))  # All players currently on team. (Remove NoneTypes)

        roster = [p1, p2, p3, p4, p5]
        
        players = []
        for player in raw_players:
            member = get(ctx.guild.members, id=player)  # Get the Member object
            players.append(member)

        if color is not None:
            color = int(color, 16)
        
        obj = object().__new__(cls)
        object.__setattr__(obj, 'ctx', ctx)
        object.__setattr__(obj, 'roster', roster)
        object.__setattr__(obj, 'color', color)
        object.__setattr__(obj, 'players', players)
        object.__setattr__(obj, 'id', TeamID)
        object.__setattr__(obj, 'name', name)
        object.__setattr__(obj, 'abbrev', abbrev)
        object.__setattr__(obj, 'mmr', mmr)
        object.__setattr__(obj, 'wins', wins)
        object.__setattr__(obj, 'losses', losses)
        object.__setattr__(obj, 'logo', logo)
        object.__setattr__(obj, 'tier', tier)
        return obj

    async def promote(self):
        embed = discord.Embed(color=0x00ff00, description="Your team has been promoted to Tier 1! Congratulations.")
        for member in self.players:
            await member.send(embed=embed)

    async def demote(self):
        embed = discord.Embed(color=0xff0000, description="Your team has been demoted to Tier 2. The average 3's MMR across your team is less than 1500.")
        for member in self.players:
            await member.send(embed=embed)

    async def verify_tier(self, mmr):
        if self.tier == 1 and average_mmr < 1500:
            self.tier = 2
            await self.demote()
        elif self.tier == 2 and average_mmr > 1800:
            self.tier = 1
            await self.promote()

    async def average_mmr(self):
        # Average the MMR and commit it to new attribute and save_changes()
        mmrs = []
        for element in self.roster:
            if element is None:
                return
            member = get(self.ctx.guild.members, id=element)
            player = await Player(self.ctx, member)
            mmrs.append(player.mmr)
            average_mmr = round(sum(mmrs) / len(mmrs))
            await self.verify_tier(average_mmr)

    async def save_changes(self):
        await self.average_mmr()
        db_changes = [self.name, self.abbrev, self.mmr, self.tier, self.wins, self.losses, self.logo, str(self.color)]
        await dbupdate('data.db', "UPDATE teams SET Name=?, Abbreviation=?, MMR=?, Tier=?, Wins=?, Losses=?, Logo=?, Color=? WHERE ID=?", (*db_changes, self.id,))
        await dbupdate('data.db', "UPDATE teams SET Player1=?, Player2=?, Player3=?, Player4=?, Player5=? WHERE ID=?", (*self.roster, self.id,))
        return "Changes commited to database."

    async def change_mmr(self, amount):
        if amount > 0:
            self.wins += 1
        elif amount < 0:
            self.losses += 1
        self.mmr += amount
        await self.save_changes()

    async def add_player(self, member):
        if len(self.players) >= 5: # If Team is full.
            return #raise TeamFullError

        await dbupdate('data.db', "UPDATE players SET Team=? WHERE ID=?", (self.id, member.id,))

        self.players.append(member)

        self.roster = [member.id for member in self.players]

        while len(self.roster) < 5:
            self.roster.append(None)

        await self.save_changes()

    async def remove_player(self, ctx, member):
        if len(self.players) == 1:
            player = await Player(ctx, member)
            await dbupdate('data.db', "DELETE FROM teams WHERE ID=?", (player.team.id,))
            return await member.send(f'You have been removed from **{player.team.name}**. Since you were the last person, the team has been deleted in our database.')  #! DELETE TEAM FROM DB

        await dbupdate('data.db', "UPDATE players SET Team=? WHERE ID=?", (None, member.id,))

        self.players.remove(member)

        self.roster = [member.id for member in self.players]

        while len(self.roster) < 5:
            self.roster.append(None)

        await self.save_changes()

    async def set_logo(self, link):
        self.logo = link
        await self.save_changes()

    async def set_name(self, team_name):
        self.name = team_name.title()
        await self.save_changes()

    async def set_abbreviation(self, abbrev):
        self.abbrev = abbrev.upper()
        await self.save_changes()

    async def set_color(self, color):
        self.color = color
        await self.save_changes()

class Match(object):
    async def __new__(cls, ctx, MatchID):
        id_lost, t1, t2, wl1, wl2, gain, loss, timeout, complete = await dbselect('data.db', "SELECT * FROM matches WHERE ID=?", (MatchID,))
        team1 = await Team(ctx, t1)
        team2 = await Team(ctx, t2)
        obj = object().__new__(cls)
        object.__setattr__(obj, 'id', MatchID)
        object.__setattr__(obj, 't1', team1)
        object.__setattr__(obj, 't2', team2)
        object.__setattr__(obj, 'wl1', wl1)
        object.__setattr__(obj, 'wl2', wl2)
        object.__setattr__(obj, 'gain', gain)
        object.__setattr__(obj, 'loss', loss)
        object.__setattr__(obj, 'timeout', timeout)
        object.__setattr__(obj, 'complete', complete)
        return obj

    async def expired(self):
        self.complete = 1
        for member in self.t1.players:
            await member.send(f"Your match with **{self.t2.name}** has been cancelled. (Over 92 hours since the challenge was accepted.)")
        for member in self.t2.players:
            await member.send(f"Your match with **{self.t1.name}** has been cancelled. (Over 92 hours since the challenge was accepted.)")
        await mod_log(self.ctx, f"{self.t2.name} let their match against {self.t1.name} expire. ({config.series_timeout} hours.)")

    async def save_changes(self):
        db_changes = [self.wl1, self.wl2, self.complete]
        await dbupdate('data.db', "UPDATE matches SET WL1=?, WL=2, Complete=? WHERE ID=?", (*db_changes, self.id,))

    async def won(self, member):
        if member.id in self.team1.players:
            self.wl1 = "W"
            self.wl2 = "L"
            self.complete = 1
            if self.team1.mmr > self.team2.mmr:
                await self.team1.change_mmr(self.loss)
                await self.team2.change_mmr(self.loss * -1)
            elif self.team1.mmr < self.team2.mmr:
                await self.team1.change_mmr(self.gain)
                await self.team2.change_mmr(self.gain * -1)

        elif member.id in self.team2.players:
            self.wl1 = "L"
            self.wl2 = "W"
            self.complete = 1
            if self.team1.mmr > self.team2.mmr:
                await self.team2.change_mmr(self.gain)
                await self.team1.change_mmr(self.gain * -1)
            elif self.team1.mmr < self.team2.mmr:
                await self.team2.change_mmr(self.loss)
                await self.team1.change_mmr(self.loss * -1)

        else:
            return "You can't report this match since you didn't play in it."
        await self.save_changes()

    async def loss(self, member):
        if member.id in self.team1.players:
            self.wl1 = "L"
            self.wl2 = "W"
            self.complete = 1
            if self.team1.mmr > self.team2.mmr:
                await self.team2.change_mmr(self.gain)
                await self.team1.change_mmr(self.gain * -1)
            elif self.team1.mmr < self.team2.mmr:
                await self.team2.change_mmr(self.loss)
                await self.team1.change_mmr(self.loss * -1)

        elif member.id in self.team2.players:
            self.wl1 = "W"
            self.wl2 = "L"
            self.complete = 1
            if self.team1.mmr > self.team2.mmr:
                await self.team1.change_mmr(self.loss)
                await self.team2.change_mmr(self.loss * -1)
            elif self.team1.mmr < self.team2.mmr:
                await self.team1.change_mmr(self.gain)
                await self.team2.change_mmr(self.gain * -1)

        else:
            return "You can't report this match since you didn't play in it."
        await self.save_changes()


class Invite(object):
    """Represents a Database object for Invites.
    
    Attributes
    ------------
    id: :class:`int`
        Team Identifier.
    channel: :class:`discord.TextChannel`
        Channel they invite was went to.
    message: :class:`discord.Message`
        Message the invite was sent in.
    challenger: :class:`Team`
        Team that sent the invite
    challenged: :class:`Team`
        Teams that was sent the invite
    inviter: :class:`Player`
        Player that sent the invite
    """

    async def __new__(cls, ctx, InviteID):
        id_lost, channel_id, message_id, challenger, challenged, inviter = await dbselect('data.db', "SELECT * FROM invites WHERE ID=?", (InviteID,))
        
        guild = ctx.bot.get_guild(config.server_id)  #INFO Guild Object
        channel = ctx.bot.get_channel(channel)  #INFO Channel Object
        message = await channel.fetch_message(message_id)  #INFO Message Object
        challenger = await Team(ctx, challenger)  #INFO Team Object
        challenged = await Team(ctx, challenged)  #INFO Team Object
        inviter = await Player(get(guild.members, id=inviter))  #Player Object

        obj = object().__new__(cls)
        object.__setattr__(obj, 'ctx', ctx)
        object.__setattr__(obj, 'id', InviteID)
        object.__setattr__(obj, 'channel', channel)
        object.__setattr__(obj, 'message', message)
        object.__setattr__(obj, 'challenger', challenger)
        object.__setattr__(obj, 'challenged', challenged)
        object.__setattr__(obj, 'inviter', inviter)
        return obj

    async def cancel(self):
        if self.ctx.author.id in [player.member.id for player in self.challenger.players] or config.admin_role_id in [role.id for role in self.ctx.author.roles]:
            await dbupdate('data.db', "DELETE FROM invites WHERE ID=?", (self.id,))
            await self.message.delete()
            for member in self.challenged.players:
                await member.send("Your team was challenged to an invite, however the invite has since been cancelled. (From **{self.challenger.name}**)")
            return "Invite deleted from database."


class DBInsert(object):
    async def player(self, member):
        if await is_in_database(sql=f'SELECT ID FROM players WHERE ID={member.id}'):
            return "Player is already in database."
        await dbupdate('data.db', "INSERT INTO players (ID, Name, MMR, Team, Logo) VALUES (?, ?, ?, ?, ?)", 
        (member.id, member.name, None, None, str(member.avatar_url)))

    async def team(self, ctx, team_name):
        id = await dbselect('data.db', "SELECT TeamsRegistered FROM stats", ())
        id += 1
        await dbupdate('data.db', "UPDATE stats SET TeamsRegistered=?", (id,))

        player = await Player(ctx, ctx.author)

        if player.mmr >= 1650:
            tier = 1
        elif player.mmr < 1650:
            tier = 2

        await dbupdate('data.db', "INSERT INTO teams (ID, Name, Abbreviation, Player1, Player2, Player3, Player4, Player5, \
            MMR, Tier, Wins, Losses, Logo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            (id, team_name.title(), team_name.upper()[:4], ctx.author.id, None, None, None, None, 2000, tier, 0, 0, config.elevate_logo,))
        
        player.team = id
        await player.save_changes()
    
    async def invite(self, ctx, team1, team2):
        identifier = await dbselect('data.db', "SELECT count(*) FROM invites", ())
        await dbupdate('data.db', "INSERT INTO invites (ID, Channel, Message, Challenger, Challenged, Inviter) VALUES (?, ?, ?, ?, ?, ?)", 
            (identifier, ctx.channel.id, ctx.message.id, team1.id, team2.id, ctx.author.id,))

    async def match(self, ctx, invite):
        mmr_diff = abs(invite.challenger.mmr - invite.challenged.mmr)
        gain, loss = await calc_mmr_match_value(mmr_diff)
        timeout = datetime.now()+timedelta(hours=config.series_timeout)
        identifier = await dbselect('data.db', 'SELECT count(*) FROM matches')
        identifier += 1
        await dbupdate('data.db', "INSERT INTO matches (ID, Team1, Team2, WL1, WL2, Gain, Loss, Timeout, Complete) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (identifier, invite.challenger.id, invite.challenged.id, None, None, gain, loss, timeout, 0))