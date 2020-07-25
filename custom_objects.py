from datetime import datetime, timedelta
import typing
import asyncio

import gspread_asyncio
import discord
from discord.utils import get

import config
from custom_functions import dbselect, dbupdate, is_in_database, calc_mmr_match_value, raw_color, get_creds, gspread_update
from errors import TeamError, CodeError, InappropriateError

#INFO ----------------------------------------------------------------------------

class Player(object):
    """Represents a Database object for individual players.
    
    Attributes
    ------------
    ctx: :class:`discord.Context`
        Context object for simplicity
    member: :class:`discord.Member`
        Member object for player being referenced.
    mmr: :class:`int`
        MMR for players RL 3's rank
    team: :class:`<Custom class Team>` = None
        Team object for player if there is a team. Defaults to None
    logo: :class:`str`
        Website link to a picture for use as a player logo.
    api_id: :class:`str`
        String for API calls for specific player (Grabs 3's rank)
    color: :class:`discord.Color`
        discord.Color object. This is for embeds.
    """
    async def __new__(cls, ctx, identifier: typing.Union[discord.Member, int] = None):
        if isinstance(identifier, int):
             identifier = get(ctx.guild.members, id=identifier)
        elif isinstance(identifier, discord.Member):
            pass
        else:
            raise CodeError(f"Couldn't create a class instance for {identifier}")

        mmr, team, logo, api_id, color = await dbselect('data.db', "SELECT MMR, Team, Logo, API_ID, Color FROM players WHERE ID=?", (identifier.id,))

        if team is None:
            team = None
        elif type(team) is int:
            team = await Team(ctx, team)

        if color is None:
            color = discord.Color().default
        elif type(color) is int:
            color = discord.Color(color)
        elif type(color) is str:
            try:
                color = int(color, 16)
            except Exception as e:
                raise CodeError(f"Color object in Player is not the desired result.\nType: {type(color)} / Value: {color}")
        
        obj = object().__new__(cls)
        object.__setattr__(obj, 'ctx', ctx)
        object.__setattr__(obj, 'member', identifier)
        object.__setattr__(obj, 'mmr', mmr)
        object.__setattr__(obj, 'team', team)
        object.__setattr__(obj, 'logo', logo)
        object.__setattr__(obj, 'api_id', api_id)
        object.__setattr__(obj, 'color', color)
        return obj

    async def save(self):
        self.color = await raw_color(self.color)

        await dbupdate('data.db', "UPDATE players SET MMR=?, Team=?, Logo=?, Color=? WHERE ID=?", (self.mmr, self.team, self.logo, self.color, self.member.id,))

    async def set_logo(self, link):
        self.logo = link
        
        await self.save()

    async def set_color(self, color):
        self.color = await raw_color(color)

        await self.save()

    async def set_team(self, team):
        if isinstance(team, Team):
            self.team = team.id
        elif isinstance(team, int):
            self.team = team
        
        if team is None:
            self.team = None

        await self.save()

    async def set_mmr(self, mmr):
        self.mmr = mmr
        
        await self.save()

#INFO ------------------------------------------------------------------------------------------------------

class Team(object):
    """Represents a Database object for Teams.
    
    Attributes
    ------------
    ctx: :class:`discord.Context`
        Context object for simplicity
    slots: :class:`list`
        List object of all 5 players (or None)
    ID: :class:`int`
        Integer that represents the Team's Unique Identifier
    name: :class:`str`
        String that represents the Teams Name
    Abbreviation: :class:`str`
        String that represents the Teams Abbreviation (Max letters = 4) ex. [APEX]
    player1: class:`discord.Member`
        Player object that represents the captain of the team.
    player2: class:`discord.Member`
        Player object that represents the 2nd player of the team.
    player3: class:`discord.Member`
        Player object that represents the 3rd player of the team.
    player4: class:`discord.Member`
        Player object that represents the 4th player of the team
    player5: class:`discord.Member`
        Player object that represents the 5th player of the team.
    last_game: class:`datetime`
        Datetime object of when the last match was played/reported.
    mmr: :class:`int`
        MMR for team. This is only changes from league matches.
    average: :class:`int`
        Average MMR for Team. THIS IS RANKED BASED. This value is changed daily.
    tier: :class:`int`
        Integer specifying which tier this Team belongs in. (Also based on Ranked 3's)
    wins: :class:`int`
        Integer representing the amount of wins the team has.
    losses: :class:`int`
        Integer representing the amount of wins the team has.
    logo: :class:`str`
        Website link to a picture for use as a player logo.
    color: :class:`discord.Color`
        discord.Color object. This is for embeds.
    """
    async def __new__(cls, ctx, team_id):
        team_id, abbrev, name, p1, p2, p3, p4, p5, last_game, mmr, average, tier, wins, losses, logo, color = await dbselect('data.db', "SELECT * FROM teams WHERE ID=?", (team_id,))

        slots = [p1, p2, p3, p4, p5]

        ids = list(filter(None, [p1, p2, p3, p4, p5]))  # Removes any None values.

        ids = [get(ctx.guild.members, id=member) for member in ids]  # Converts any IDs pulled into Member Objects.

        if last_game is not None:
            last_game = datetime.strptime(last_game, "%m/%d/%Y %I:%M%p")  # Returns a Datetime object from String (pulled from database.)

        obj = object().__new__(cls)

        object.__setattr__(obj, 'player1', p1)
        object.__setattr__(obj, 'player2', p2)
        object.__setattr__(obj, 'player3', p3)  # This creates all of the players (even none values.)
        object.__setattr__(obj, 'player4', p4)
        object.__setattr__(obj, 'player5', p5)

        for i in range(len(ids)):
            object.__setattr__(obj, f'player{i+1}', ids[i])  # Overwrites any Non-None values. Leave None as such

        if color is None:
            color = discord.Color().default
        elif type(color) is int:
            color = discord.Color(color)
        elif type(color) is str:
            try:
                color = int(color, 16)
            except Exception as e:
                raise CodeError(f"Color object in Team is not the desired result.\nType: {type(color)} / Value: {color} / Error: {type(error)} - {str(error)}")

        eligible = False

        if len(ids) >= 3:
            eligible = True

        object.__setattr__(obj, 'slots', slots)
        object.__setattr__(obj, 'ctx', ctx)
        object.__setattr__(obj, 'id', team_id)
        object.__setattr__(obj, 'abbreviation', abbrev)
        object.__setattr__(obj, 'name', name)
        object.__setattr__(obj, 'members', ids)
        object.__setattr__(obj, 'last_game', last_game)
        object.__setattr__(obj, 'mmr', mmr)
        object.__setattr__(obj, 'average', average)
        object.__setattr__(obj, 'tier', tier)
        object.__setattr__(obj, 'wins', wins)
        object.__setattr__(obj, 'losses', losses)
        object.__setattr__(obj, 'logo', logo)
        object.__setattr__(obj, 'color', color)
        object.__setattr__(obj, 'eligible', eligible)
        return obj

    def __str__(self):
        return f"**[{self.abbreviation}]** | {self.name}"

    async def add(self, amount):
        if isinstance(amount, int):
            self.wins += 1
            self.mmr += amount
            
            await self.save()

        elif isinstance(amount, Player):
            print(self.slots)
            players = list(filter(None, self.slots))
            print(players)

            if amount.member in self.members:
                raise TeamError(f"That player is already on this team. Unable to add them again.\nPlayer: {amount.member.mention}\nTeam: {str(self)}")

            if amount.team is not None:
                raise TeamError(f'That player is already on a team. They would have to leave that team before joining another.')

            if len(players) < 5:
                players.append(amount.member.id)
            elif len(players) == 5:
                raise TeamError("This team has already reached the maximum players allowed. (5)")

            else:
                raise CodeError(f"Critical Error. Team: {str(self)} has more than 5 players. Currently set to {len(self.slots)}. Please reference database immediately.\nTeam ID: {self.id}")

            while len(players) < 5:
                players.append(None)

            self.slots = players
            await amount.set_team(self.id)
            await self.save()
        
        else:
            raise CodeError(f"Unsupported addition with a Team object.\nType: {type(amount)} Value: {amount}")

    async def sub(self, amount):
        if isinstance(amount, int):
            self.losses += 1
            self.mmr -= amount

            await self.save()

        elif isinstance(amount, Player):
            if amount.member.id in self.slots:
                self.slots.remove(amount.member.id)
                self.slots.append(None)
                
                await amount.set_team(None)
                await self.save()

            else:
                raise TeamError(f"This player did not show up on this team. Could not remove them.\nPlayer: {amount.member.mention}\nTeam: {str(self)}")

        else:
            raise CodeError(f"Unsupported subtraction with a Team object.\nType: {type(amount)} Value: {amount}")


    async def save(self):  # This saves the current state of the object to the database.
        agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        sheet = await gspread_update(agcm)

        sheet_members = [member.name for member in self.members]
        while len(sheet_members) < 5:
            sheet_members.append(None)

        team_values = [str(self.abbreviation), str(self.name), str(sheet_members[0]), str(sheet_members[1]), str(sheet_members[2]), str(sheet_members[3]), str(sheet_members[4]), str(self.mmr)]

        try:
            team_id_cell = sheet.find(str(self.id))
            team_cell = team_id_cell.row
            team_range = f'B{team_cell}:I{team_cell}' #B2:I2

            data = [{
                "range": f"{team_range}", 
                "values": [team_values]
                }]

            sheet.batch_update(data)
        except Exception as e:
            team_values = [self.id] + team_values
            sheet.append_row(team_values)

        self.color = await raw_color(self.color)
        
        await dbupdate('data.db', "UPDATE teams SET Abbreviation=?, Name=?, Player1=?, Player2=?, Player3=?, Player4=?, Player5=?, LastGame=?, MMR=?, Average=?, Tier=?, Wins=?, Losses=?, Logo=?, Color=? WHERE ID=?", (self.abbreviation, self.name, *self.slots, self.last_game, self.mmr, self.average, self.tier, self.wins, self.losses, self.logo, self.color, self.id,))


    async def set_abbreviation(self, abbreviation):
        if len(abbreviation) > 4:
            raise TeamError("That abbreviation is too long.")
        elif len(abbreviation) == 0:
            raise TeamError("That abbreviation is too short.")

        for swear in config.swears:  # Profanity Check
            if swear in abbreviation:
                raise InappropriateError("That abbreviation is inappropriate. Please try again.")

        self.abbreviation = abbreviation.upper()

        await self.save()

    async def set_name(self, name):
        if len(name) < config.shortest_team_name:
            raise TeamError(f"That team name is too short. (Less than {config.shortest_team_name} letters.)")
        elif len(name) > config.longest_team_name:
            raise TeamError(f"That team name is too long. (More than {config.longest_team_name} letters.)")

        for swear in config.swears:  # Profanity Check
            if swear in name:
                raise InappropriateError("That abbreviation is inappropriate. Please try again.")

        self.name = name.title()

        await self.save()

    async def set_logo(self, link = None):
        if link is None:
            if len(self.ctx.message.attachments) == 0:
                link = config.elevate_logo
            else:
                link = self.ctx.message.attachments[0].url

        if '.' not in link:
            raise TeamError("This is not a link that directs to an image.")
        else:
            file_format = link.split('.')[-1]
            accepted_formats = ['jpg', 'png', 'webp', 'gif']
            if file_format in accepted_formats:
                pass
            else:
                raise TeamError("This is not an accepted file format. (jpg, png, gif, webp)")

        self.logo = link

        await self.save()

    async def set_color(self, color):
        self.color = await raw_color(color)

        await self.save()

#INFO ----------------------------------------------------------------------------------------------

class Invite(object):
    """Represents a Database object for Invites to challenges between teams.
    
    Attributes
    ------------
    ctx: :class:`discord.Context`
        Context object for simplicity
    ID: :class:`int`
        Integer that represents the Invite's Unique Identifier
    channel: :class:`discord.TextChannel`
        Channel the invite was sent in.
    message_id: :class:`discord.Message`
        Message object the invite was sent through.
    challenger: :class:`Team`
        Team object for the team that sent the challenge invite
    challenged: :class:`Team`
        Team object for the team that was sent the challenge invite.
    Invite: :class:`Player`
        Player object for the player that sent the invite on behalf of the team.
    Timeout: :class:`datetime`
        Datetime object for when the invite expires.)
    """

    async def __new__(cls, ctx, invite_id):
        invite_id, channel_id, message_id, challenger, challenged, inviter, timeout = await dbselect('data.db', "SELECT * FROM invites WHERE ID=?", (invite_id,))

        channel = ctx.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
        challenger = await Team(ctx, challenger)
        challenged = await Team(ctx, challenged)
        inviter = await Player(ctx, inviter)
        timeout = datetime.strptime(timeout, "%m/%d/%Y %I:%M%p")

        obj = object().__new__(cls)
        object.__setattr__(obj, 'ctx', ctx)
        object.__setattr__(obj, 'id', invite_id)
        object.__setattr__(obj, 'channel', channel)
        object.__setattr__(obj, 'message', message)
        object.__setattr__(obj, 'challenger', challenger)
        object.__setattr__(obj, 'challenged', challenged)
        object.__setattr__(obj, 'timeout', timeout)
        return obj

    async def cancel(self):
        await self.message.delete()
        await dbupdate('data.db', "DELETE FROM invites WHERE ID=?", (self.id,))

#INFO ----------------------------------------------------------------------------------

class Match(object):
    """Represents a Database object for matches between teams.
    
    Attributes
    ------------
    ctx: :class:`discord.Context`
        Context object for simplicity
    ID: :class:`int`
        Match's Unique Identifier
    Challenger: :class:`Team`
        Team object for the team that challenged
    Challenged: :class:`Team`
        Team object for the team that was challenged
    WL1: :class:`str`
        String to represent whether Team 1, won or lost. Will return 'W' or 'L'
    WL2: :class:`str`
        String to represent whether Team 2, won or lost. Will return 'W' or 'L'
    High: :class:`int`
        Integer to represent the highest possible MMR change from the match.
    Low: :class:`int`
        Integer to represent the lowest possible MMR change from the match.
    Timeout: :class:`datetime`
        Datetime object to represent when the series expires and cancels.
    Completed: :class:`int`
        Integer to represent whether the match was reported. 0 for no, 1 for yes.
    """

    async def __new__(cls, ctx, match_id: int):
        match_id, challenger, challenged, wl1, wl2, high, low, timeout, completed = await dbselect('data.db', "SELECT * FROM matches WHERE ID=?", (match_id,))

        challenger = await Team(ctx, challenger)
        challenged = await Team(ctx, challenged)

        timeout = datetime.strptime(timeout, "%m/%d/%Y %I:%M%p")

        if completed == 0:
            completed = False
        elif completed == 1:
            completed = True
        else:
            raise CodeError("Match Attribute `Completed` Not working correctly. Did not come back as 0, or 1.")

        obj = object().__new__(cls)
        object.__setattr__(obj, 'ctx', ctx)
        object.__setattr__(obj, 'id', match_id)
        object.__setattr__(obj, 'challenger', challenger)
        object.__setattr__(obj, 'challenged', challenged)
        object.__setattr__(obj, 'wl1', wl1)
        object.__setattr__(obj, 'wl2', wl2)
        object.__setattr__(obj, 'high', high)
        object.__setattr__(obj, 'low', low)
        object.__setattr__(obj, 'timeout', timeout)
        object.__setattr__(obj, 'completed', completed)
        return obj

    async def cancel(self):
        await dbupdate('data.db', "DELETE FROM matches WHERE ID=?", (self.id,))

    async def save(self):
        await dbupdate('data.db', "UPDATE matches SET WL1=?, WL2=?, Complete=? WHERE ID=?", (self.wl1, self.wl2, self.completed, self.id,))

    async def won(self, team):
        self.completed = 1
        diff = abs(self.challenger.mmr - self.challenged.mmr)
        high, low = await calc_mmr_match_value(diff)
        if team.id == self.challenger.id:
            self.wl1 = 'W'
            self.wl2 = 'L'

            if self.challenger.mmr >= self.challenged.mmr:
                await self.challenger.add(low)
                await self.challenged.sub(low)

            elif self.challenged.mmr >= self.challenger.mmr:
                await self.challenger.add(high)
                await self.challenged.sub(high)

            
        elif team.id == self.challenged.id:
            self.wl1 = 'L'
            self.wl2 = 'W'

            if self.challenger.mmr >= self.challenged.mmr:
                await self.challenger.sub(low)
                await self.challenged.add(low)

            elif self.challenged.mmr >= self.challenger.mmr:
                await self.challenger.sub(high)
                await self.challenged.add(high)

        else:
            raise PlayerError("You were not involved in this match, and cannot report the score.")

        await self.save()

#INFO -------------------------------------------------------------------------------------------------------------------

class DBInsert(object):
    async def player(member):
        if await is_in_database(sql=f"SELECT ID FROM players WHERE ID={member.id}"):
            return
        await dbupdate('data.db', "INSERT INTO players (ID, MMR, Team, Logo, API_ID, Color) VALUES (?, ?, ?, ?, ?, ?)", (member.id, None, None, str(member.avatar_url), None, member.color.value,))

    async def team(ctx, name):
        if await is_in_database(sql=f"SELECT ID FROM teams WHERE Name='{name.title()}'"):
            raise TeamError("There appears to be a team under that name already.")

        for swear in config.swears:
            if swear in name:
                raise InappropriateError(f"No swear words allowed. Attempted Team Name Change: {name.title()}")

        player = await Player(ctx, ctx.author)

        if player.mmr is None:
            raise PlayerError(f"I'm sorry, you'll have to verify before you can create a team. You can verify here: <#{config.verify_channel}>")

        team_id = await dbselect('data.db', "SELECT teams FROM stats", ())
        team_id += 1
        await dbupdate('data.db', "UPDATE stats SET teams=?", (team_id,))

        player.team = team_id
        await player.save()

        tier = 0

        if player.mmr >= 1600:
            tier = 1
        elif player.mmr < 1600:
            tier = 2

        await dbupdate('data.db', "INSERT INTO teams (ID, Abbreviation, Name, Player1, Player2, Player3, Player4, Player5, LastGame, MMR, Average, Tier, Wins, Losses, Logo, Color) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (team_id, name.upper()[:4], name.title(), ctx.author.id, None, None, None, None, None, 2000, player.mmr, tier, 0, 0, config.elevate_logo, discord.Color.default().value,))

    async def invite(ctx, challenged):
        invite_id = await dbselect('data.db', "SELECT count(*) FROM invites", ())
        invite_id += 1

        inviter = await Player(ctx, ctx.author)
        challenger = inviter.team

        if isinstance(challenged, int):
            challenged = Team(ctx, challenged)
        elif isinstance(challenged, Team):
            pass
        else:
            raise CodeError("Unexpected Challenge parameter for DBInsert.invite (was NOT int or Team object.)")

        timeout = datetime.now() + timedelta(hours=config.invite_timeout)
        timeout = timeout.strftime("%m/%d/%Y %I:%M%p")

        msg = await ctx.send(f"Invite sent to {str(challenged)}")
        await msg.add_reaction(config.checkmark_emoji)
        await msg.add_reaction(config.cross_emoji)

        await dbupdate('data.db', "INSERT INTO invites (ID, Channel, Message, Challenger, Challenged, Inviter, Timeout) VALUES (?, ?, ?, ?, ?, ?, ?)", (invite_id, ctx.channel.id, msg.id, challenger.id, challenged.id, inviter.member.id, timeout,))

    async def match(ctx, team1, team2):
        match_id = await dbselect('data.db', "SELECT count(*) FROM matches", ())
        match_id += 1

        diff = abs(team1.mmr - team2.mmr)

        high, low = await calc_mmr_match_value(diff)

        timeout = datetime.now() + timedelta(hours=config.series_timeout)
        timeout = timeout.strftime("%m/%d/%Y %I:%M%p")

        embed = discord.Embed(title=f"Match Confirmed. ID: #{match_id}", color=0x00ff00, description=f"You have {config.series_timeout} hours to play and report your series, before it is cancelled.")
        embed.add_field(name=str(team1), value=', '.join([member.mention for member in team1.members]), inline=False)
        embed.add_field(name=str(team2), value=', '.join([member.mention for member in team2.members]), inline=False)
        await ctx.send(embed=embed)

        await dbupdate('data.db', "INSERT INTO matches (ID, Challenger, Challenged, WL1, WL2, High, Low, Timeout, Complete) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (match_id, team1.id, team2.id, None, None, high, low, timeout, 0,))

#INFO --------------------------------------------------------------------------------------------------------------------------

class Role_Objects(object):
    def __init__(self, ctx):
        self.team_member = get(ctx.guild.roles, id=config.team_member_role_id)
        self.team_captain = get(ctx.guild.roles, id=config.team_captain_role_id)
        self.admin = get(ctx.guild.roles, id=config.admin_role_id)

class Channel_Objects(object):
    def __init__(self, ctx):
        self.verify = get(ctx.guild.text_channels, id=config.verify_channel)
        self.error = get(ctx.guild.text_channels, id=config.error_channel)
        self.db_backup = get(ctx.guild.text_channels, id=config.db_backup_channel)
        self.challenge = get(ctx.guild.text_channels, id=config.challenge_channel)
        
class Elevate(object):
    def __init__(self, ctx):
        self.roles = Role_Objects(ctx)
        self.channels = Channel_Objects(ctx)