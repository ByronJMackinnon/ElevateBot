from datetime import datetime
import typing

import discord
from discord.ext import commands

import config
from custom_functions import dbselect, dbupdate, dbselect_all
from custom_objects import Player, Team, Match

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        if config.admin_role_id in [role.id for role in ctx.author.roles]:
            return True
        return False

    @commands.command(name="purge")
    async def _purge(self, ctx, amount: int):
       await ctx.channel.purge(limit=amount) 

    @commands.command(name="nonick")
    async def _nonick(self, ctx, member: discord.Member):
        if type(member) is discord.Member:
            await member.edit(nick=None)
        else:
            if member.lower() == "all":
                for member in ctx.guild.members:
                    await member.edit(nick=None)

    @commands.command(name="echo")
    async def _echo(self, ctx, destination: typing.Union[discord.Member, discord.TextChannel], *, msg):
        await destination.send(msg)

    @commands.group(name='db')
    async def _db(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @_db.command(name="backup")
    async def _db_backup(self, ctx):
        with open('data.db', 'rb') as file:
            await ctx.send(file=discord.File(file, "Backup Database.db"))

    @_db.command(name="view")
    async def _db_view(self, ctx, table: str, identifier: int = None):
        if table.lower() == "players":
            columns = ["ID", "Name", "MMR", "Team", "Logo"]
        elif table.lower() == "matches":
            columns = ["ID", "Team1", "Team2", "WL1", "WL2", "Gain", "Loss", "Timeout", "Complete"]
        elif table.lower() == "teams":
            columns = ["ID", "Name", "Abbreviation", "Player1", "Player2", "Player3", "Player4", "Player5", "MMR", "Wins", "Losses", "Logo"]
        if identifier is None:
            await ctx.send(columns)
            return
        else:
            query = await dbselect('data.db', f"SELECT * FROM {table.lower()} WHERE ID=?", (identifier,))
        if query is None:
            await ctx.send("That ID wasn't able to be found in that table. Please check the command and try again.")
            return
        layout = ""
        for column, value in zip(columns, query):
            layout = layout + f"{column}: {value}\n"
        embed = discord.Embed(title="Database View", color=0x010101, description=layout)
        embed.set_footer(text="These commands are extremely powerful. Use them with caution.", icon_url=config.elevate_logo)
        await ctx.send(embed=embed)

    @_db.command(name="edit")
    async def _db_edit(self, ctx, table: str, id: int, column, new_value = None):
        await dbupdate("data.db", f"UPDATE {table.lower()} SET {column.title()}=? WHERE ID=?", (new_value, id,))

    @commands.group(name="search")
    async def _search(self, ctx):
        if ctx.invoked_subcommand:
            pass

    @_search.command(name="bugs")
    async def _search_bugs(self, ctx, member: discord.Member):
        results = await dbselect_all('data.db', "SELECT * FROM Fixes ORDER BY fixes DESC", ())
        if member.id not in results:
            await ctx.send("That player hasn't found any bugs yet.", delete_after=5)
            return
        total = await dbselect('data.db', "SELECT count(*) FROM Fixes", ())
        index = results.index(member.id)
        bugs = results[index+1]
        if index == 0:
            position = 1
        else:
            position = (index/2) + 1
        await ctx.send(f"Player is ranked **#{int(position)}** out of {total} people in bug testing. with a total of {bugs} found.")

    @_search.command(name="player")
    async def _search_player(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
            return

        player = Player(member)
        await player.get_stats()

        embed = discord.Embed(color=0x00ffff)
        embed.set_author(name=player.name, icon_url=player.logo)
        if player.mmr is None:
            embed.add_field(name="MMR:", value="Not yet verified.")
        else:
            embed.add_field(name="MMR:", value=player.mmr)
        if player.team is None:
            embed.add_field(name="Team:", value="Free Agent")
            embed.set_footer(text=f"Player ID: {player.member.id}", icon_url=config.elevate_logo)
        else:
            embed.add_field(name="Team:", value=f"""**[{player.team.abbrev}]** | {player.team.name}
            MMR: {player.team.mmr}
            Wins: {player.team.wins}
            Losses: {player.team.losses}
            Total Games: {player.team.wins + player.team.losses}
            Roster: {', '.join([f'<@{player_id}>' for player_id in player.team.players])}""", inline=False)
            embed.set_footer(text=f"Player ID: {player.member.id} | Team ID: {player.team.id}")
            embed.set_thumbnail(url=player.team.logo)

        await ctx.send(embed=embed)

    @_search.command(name="team")
    async def _search_team(self, ctx, *, id: typing.Union[int, str]):
        if type(id) is int:
            pass
        elif type(id) is str:
            id = await dbselect("data.db", "SELECT id FROM teams WHERE Name=?", (id.title(),))

        team = Team(id)
        await team.get_stats()

        embed = discord.Embed(title="Team Search", color=0x00ffff, description=f'**{team.abbrev}** | {team.name}')
        embed.add_field(name="MMR:", value=team.mmr)
        embed.add_field(name="Stats:", value=f'Wins: {team.wins}\nLosses: {team.losses}\nTotal Games: {team.wins + team.losses}', inline=False)
        embed.set_thumbnail(url=team.logo)
        embed.set_footer(text=f"Team ID: {team.id}")
        embed.add_field(name="Roster:", value=', '.join([f'<@{player_id}>' for player_id in team.players]), inline=False)

        await ctx.send(embed=embed)

    @_search.command(name="match")
    async def _search_match(self, ctx, matchID):
        match = Match(matchID)
        await match.get_stats()

        embed = discord.Embed(title="Match Search", color=0x00ffff)
        embed.add_field(name=f"**[{match.team1.abbrev}]** | {match.team1.name} | {match.wl1}", value=', '.join([f'<@{player_id}>' for player_id in match.team1.players]))
        embed.add_field(name=f"**[{match.team2.abbrev}]** | {match.team2.name} | {match.wl2}", value=', '.join([f'<@{player_id}>' for player_id in match.team2.players]), inline=False)

        await ctx.send(embed=embed)

    @_search.command(name="member")
    async def _search_member(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        roles = [role.mention for role in member.roles]
        clean_roles = roles[1:]
        if clean_roles == []:
            clean_roles = ["None"]

        activity_list = [activity.name for activity in member.activities]
        if activity_list == []:
            activity_list = ["None"]
        
        embed = discord.Embed(color=member.top_role.color, description=f"Member information for {member.mention}\nID: {member.id}")
        embed.add_field(name="Status:", value=member.status)
        embed.add_field(name="Bot:", value=member.bot)
        embed.add_field(name="Activity:", value='\n'.join(activity_list), inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="Created At:", value=getDuration(member.created_at), inline=False)
        embed.add_field(name="Joined At:", value=getDuration(member.joined_at), inline=False)
        embed.add_field(name="Roles:", value=', '.join(clean_roles), inline=False)

        await ctx.send(embed=embed)

def clean_time(dtobject):
    return dtobject.strftime("%B %d, %Y - %I:%M%p")

def getDuration(then, now = datetime.now(), interval = 'default'):

    # Returns a duration as specified by variable interval
    # Functions, except totalDuration, returns [quotient, remainder]

    duration = now - then # For build-in functions
    duration_in_s = duration.total_seconds() 

    def years():
      return divmod(duration_in_s, 31536000) # Seconds in a year=31536000.

    def days(seconds = None):
      return divmod(seconds if seconds != None else duration_in_s, 86400) # Seconds in a day = 86400

    def hours(seconds = None):
      return divmod(seconds if seconds != None else duration_in_s, 3600) # Seconds in an hour = 3600

    def totalDuration():
        y = years()
        d = days(y[1]) # Use remainder to calculate next variable
        h = hours(d[1])

        return "{} years, {} days, {} hours".format(int(y[0]), int(d[0]), int(h[0]))
    
    return {
        'years': int(years()[0]),
        'days': int(days()[0]),
        'hours': int(hours()[0]),
        'default': totalDuration()
    }[interval]


def setup(bot):
    bot.add_cog(Admin(bot))