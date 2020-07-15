# Standard Imports
import string
from datetime import datetime, timedelta

# 3rd Party Imports
import discord
from discord.utils import get

# Custom Imports
import config
from custom_functions import dbupdate, dbselect, team_average, calc_mmr_match_value

class Player(object):  # Helper Object for Player Database Management
    def __init__(self, member):
        self.member = member

    async def get_stats(self):  # Makes database call to add attributes to class
        name, mmr, team, logo = await dbselect('data.db', 'SELECT Name, MMR, Team, Logo FROM players WHERE ID=?', (self.member.id,))
        self.name = name
        self.mmr = mmr
        self.team = team
        self.logo = logo

        if self.team is None:
            pass
        else:
            team_class = Team(self.team)
            await team_class.get_stats()
            self.team = team_class

    async def mmr_change(self, amount):  # Updates individuals MMR. Important when cycling through players.
        await dbupdate("data.db", "UPDATE players SET MMR=MMR+?, WHERE ID=?", (amount, self.member.id,))

    async def edit_logo(self, link):  # Updates players profile image.
        await dbupdate('data.db', 'UPDATE players SET Logo=? WHERE ID=?', (str(link), self.member.id,))

class Team(object):  # Helper Object for Team Database Management
    def __init__(self, teamID):
        self.id = teamID

    async def get_stats(self):  # Makes database call to add attributes to class
        name, abbrev, p1, p2, p3, p4, p5, mmr, wins, losses, logo = await dbselect("data.db", "SELECT Name, Abbreviation, Player1, Player2, Player3, Player4, Player5, MMR, Wins, Losses, Logo FROM teams WHERE ID=?", (self.id,))
        self.name = name
        self.abbrev = abbrev
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.p4 = p4
        self.p5 = p5
        self.mmr = mmr
        self.wins = wins
        self.losses = losses
        self.logo = logo
        players = [self.p1, self.p2, self.p3, self.p4, self.p5]
        self.players = list(filter(None, players))

    async def add_player(self, member):  # Adds player to team in database and gives player proper discord roles.
        captain = get(member.guild.members, id=self.p1)
        new_player = Player(member)
        await new_player.get_stats()

        if member.id in self.players:  # Is on the same team they are trying to add
            await captain.send("This player is already on your team.")
            return

        elif config.team_member_role_id in [role.id for role in member.roles]:  # Has Team Member Role
            await captain.send("I'm sorry, this player seems to already be a part of a team.")
            return

        elif new_player.mmr is None:
            await captain.send("I'm sorry, this player has not yet been verified and they are unable to be added to the team.")
            return

        else:  # All checks are cleared and the player gets added.
            players = list(filter(None, self.players))  # Removes "None" values from roster

            if len(players) == 5:  # If team is currently full
                await captain.send("Your team already has 5 players. Which is the max allowed.")
                return

            # Player id gets added to the list, and if the roster isn't full, fill the rest with None values.
            players.append(member.id)
            while len(players) < 5:
                players.append(None)

            # Give player the Team ID in the players table when being added to a team.
            await dbupdate('data.db', "UPDATE players SET Team=? WHERE ID=?", (self.id, member.id,))

            await dbupdate('data.db', "UPDATE teams SET Player1=?, Player2=?, Player3=?, Player4=?, Player5=? WHERE ID=?", (*players, self.id,))  # Adds player list to the roster in the database

            await team_average(self.id)  # Calculates new average MMR for roster.

            await member.edit(nick=f"{self.abbrev.upper()} | {member.name}")

            # Gives the new member the "Team Member" role.
            team_member_role = get(member.guild.roles, id=config.team_member_role_id)
            await member.add_roles(team_member_role)

            await member.send(f"You have been added to {self.name}")  # Alerts the player they were added to the team.

            await captain.send(f"{member.mention} has been added to {self.name}")

    async def remove_player(self, member):  # Removes player to team in database and removes discord roles.
        captain = get(member.guild.members, id=self.p1)
        players = list(filter(None, self.players))
        team_member_role = get(member.guild.roles, id=config.team_member_role_id)
        team_captain_role = get(member.guild.roles, id=config.team_captain_role_id)

        await dbupdate('data.db', "UPDATE players SET Team=? WHERE ID=?", (None, member.id,))

        if member.id == captain.id:  # If the captain is the one leaving.
            await member.remove_roles(team_member_role, team_captain_role)  # Takes away discord roles

            if len(players) == 1:  # If captain was the only player on the team, it deletes it from database
                await dbupdate("data.db", "DELETE FROM teams WHERE ID=?", (self.id,))
                await member.send(f"You were removed from {self.name}. Which resulted in the team being deleted since you were the only player.")
                await member.edit(nick=None)
                return

            player.remove(member.id)  # Remove captain from the players list.
            while len(players) < 5:
                players.append(None)  # Fills the rest with None values if roster is not full.

            new_captain = get(member.guild.members, id=players[0])
            await new_captain.add_roles(team_captain_role)  # Gives captain role to new captain

            await dbupdate('data.db', "UPDATE teams SET Player1=?, Player2=?, Player3=?, Player4=?, Player5=? WHERE ID=?", (*players, self.id,))  # Updates roster in the database

            await team_average(self.id)  # Calculates new average MMR for roster.

            # Alert both the old captain and new captain about their change in postion.
            await new_captain.send(f"You are now the captain of {self.name}")
            await member.send(f"You have been removed from {self.name}")

        else:
            players.remove(member.id)
            while len(players) < 5:
                players.append(None)

            await dbupdate('data.db', "UPDATE teams SET Player1=?, Player2=?, Player3=?, Player4=?, Player5=? WHERE ID=?", (*players, self.id,))  # Updates roster in the database

            await team_average(self.id)  # Calculates new average MMR for roster.

            await member.remove_roles(team_member_role)

            await member.send(f"You have been removed from {self.name}")
            await captain.send(f"{member.mention} has been removed from {self.name}")

        await member.edit(nick=None)


    async def edit_abbrev(self, ctx, abbrev):  # Edit teams abbreviation in the database and messages the captain
        captain = get(ctx.guild.members, id=self.p1)

        if len(abbrev) > 4:  # Abbreviations can only be 4 characters long.
            await captain.send("I'm sorry, the max length for abbreviations are capped at 4 characters.")
            return

        for character in abbrev:  # Iterates through to ensure no special characters are used.
            if character.isdigit():  # Character is a number
                pass
            elif character in string.ascii_letters:  # Character is a letter
                pass
            else:  # Character is a special character
                await captain.send("There was a special character used. We can only accept Alpha-Numeric characters.")
                return

        # Updates abbreviation and alerts the captain that the change was successful.
        await dbupdate('data.db', "UPDATE teams SET Abbreviation=? WHERE ID=?", (abbrev.upper(), self.id,))
        await captain.send(f"{self.name}'s Abbreviation has been changed to [{abbrev.upper()}]")

        for player in self.players:
            member = get(ctx.guild.members, id=player)
            await member.edit(nick=f"{abbrev.upper()} | {member.name}")

    async def edit_owner(self, ctx, member: discord.Member):
        player = Player(ctx.author)
        await player.get_stats()

        if member.id not in player.team.players:
            await ctx.author.send("You are only able to transfer ownership to someone on your team.")
            return

        players = player.team.players
        players.remove(member.id)

        new_captain = [member.id]

        players = new_captain + players

        while len(players) < 5:
            players.append(None)

        await dbupdate('data.db', "UPDATE teams SET Player1=?, Player2=?, Player3=?, Player4=?, Player5=? WHERE ID=?", (*players, player.team.id,))

        captain_role = get(ctx.guild.roles, id=config.team_captain_role_id)

        await ctx.author.remove_roles(captain_role)
        await member.add_roles(captain_role)

    async def edit_name(self, ctx, name):    # Edit teams name in the database and messages the captain

        if len(name) > config.longest_team_name:
            return await ctx.author.send("The team name was too large. No changes were made.")

        elif len(name) < config.shortest_team_name:
            return await ctx.author.send("The team name is too short. No changes were made.")
            
        check = await dbselect('data.db', "SELECT * FROM players WHERE Name=?", (name.title(),))
        if check is None:
            pass
        else:
            await ctx.author.send("I'm sorry, there is already a team by that name. Please pick another name.")
            return

        captain = get(ctx.guild.members, id=self.p1)

        for character in name:  # Iterates through to ensure no special characters are being used.
            if character.isdigit():
                pass
            elif character in string.ascii_letters:
                pass
            elif character == ' ':
                pass
            else:
                await captain.send("There was a special character used. We can only accept Alpha-Numeric characters.")
                return

        check = await dbselect('data.db', "SELECT Name FROM teams WHERE Name=?", (name.title(),))
        if check is not None:
            await ctx.author.send("It appears that another team by the same name has already registered their name. Please choose another team name.")
            return

        # Updates the name and alerts the captain that they change was successful.
        await dbupdate('data.db', "UPDATE teams SET Name=? WHERE ID=?", (name.title(), self.id,))
        await captain.send(f"Team name has been changed to **{name.title()}**")

    async def edit_logo(self, ctx, link=None):  # Edit teams logo in the database and messages the captain
        captain = get(ctx.guild.members, id=self.p1)

        if link is None:
            link = ctx.message.attachments[0].url

        await dbupdate('data.db', "UPDATE teams SET logo=? WHERE ID=?", (link, self.id,))
        await captain.send("Your team logo has been updated successfully.")

    async def mmr_change(amount):    # Changes team MMR. Useful for after a series win.
        await dbupdate('data.db', 'UPDATE teams SET MMR=MMR+? WHERE ID=?', (amount, self.id,))

class Match(object):
    def __init__(self, id):
        self.id = id

    async def get_stats(self):
        id, team1, team2, wl1, wl2, gain, loss, timeoutdate, complete = await dbselect('data.db', "SELECT * FROM matches WHERE ID=?", (self.id,))
        self.team1 = Team(team1)
        self.team2 = Team(team2)

        await self.team1.get_stats()
        await self.team2.get_stats()

        self.wl1 = wl1
        self.wl2 = wl2
        self.gain = gain
        self.loss = loss
        self.timeoutdate = timeoutdate
        self.complete = complete

    async def timeout(self, guild):
        team1, team2 = await dbselect('data.db', "SELECT Team1, Team2 FROM matches WHERE ID=?", (self.id,))
        team1 = Team(team1)
        team2 = Team(team2)

        embed = discord.Embed(title=f"Your match has timed out. (Over {config.series_timeout} hours)", color=0xff0000, description=f"[team1.abbrev] {team1.name}\nVS.\n[{team2.abbrev}] {team2.name}")

        players = team1.players + team2.players
        for player in players:
            member = get(guild.members, id=player)
            await member.send(embed=embed)

class DBInsert(object):  # Helper Object for Modular addition of database fields.

    async def member(self, member):  # Inserts new entry into the 'players' table in the database.
        if member.bot:
            return
        await dbupdate('data.db', 'INSERT INTO players (ID, Name, MMR, Team, Logo) VALUES (?, ?, ?, ?, ?)', (member.id, f"{member.name}#{member.discriminator}", None, None, str(member.avatar_url),))

    async def team(self, ctx, name):  # Inserts new entry into the 'teams' table in the database.

        async def team_in_database(name):  # Local function for checking existing teams.
            check = await dbselect('data.db', "SELECT * FROM players WHERE Name=?", (name.title(),))
            if check is None:
                return False
            return True

        if await team_in_database(name):
            await ctx.author.send("I'm sorry, there is already a team by that name. Please pick another name.")
            return

        await dbupdate('data.db', "UPDATE stats SET TeamsRegistered=TeamsRegistered+1", ())  # Creates ID for Team

        id = await dbselect('data.db', "SELECT TeamsRegistered FROM stats", ())  # Grabs ID for team

        abbrev = name.upper()[:4]  # Creates abbreviation. All capitals, first 4 letters of team name

        mmr = await dbselect('data.db', "SELECT MMR FROM players WHERE ID=?", (ctx.author.id,))
        if mmr is None:
            await ctx.author.send("I'm sorry, you have to verify your rank before you can create a team! Please head over to the <#{config.verify_channel}> to do so.")
            return

        await dbupdate('data.db', "INSERT INTO teams (ID, Name, Abbreviation, Player1, Player2, Player3, Player4, Player5, MMR, Wins, Losses, Logo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (id, name.title(), abbrev, ctx.author.id, None, None, None, None, mmr, 0, 0, config.elevate_logo,))

        await dbupdate('data.db', "UPDATE players SET Team=? WHERE ID=?", (id, ctx.author.id,))

        team_member_role = get(ctx.guild.roles, id=config.team_member_role_id)
        team_captain_role = get(ctx.guild.roles, id=config.team_captain_role_id)
        await ctx.author.add_roles(team_member_role, team_captain_role)
        await ctx.author.edit(nick=f"{abbrev.upper()} | {ctx.author.name}")
        await ctx.author.send(f"Your team has been successfully registered. **[{abbrev}]** | {name.title()}")

    async def match(self, team1, team2):  # Inserts new entry into the 'matches' table in the database.
        id = await dbselect('data.db', "SELECT count(*) FROM matches", ())
        id += 1

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        timeout = now + timedelta(hours=config.series_timeout)

        team1 = Team(team1)
        await team1.get_stats()

        team2 = Team(team2)
        await team2.get_stats()

        mmr_diff = abs(int(team1.mmr) - int(team2.mmr))

        gain, loss = await calc_mmr_match_value(mmr_diff)

        await dbupdate('data.db', 'INSERT INTO matches (ID, Team1, Team2, WL1, WL2, Gain, Loss, Timeout, Complete) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (id, team1.id, team2.id, None, None, gain, loss, timeout, False))
