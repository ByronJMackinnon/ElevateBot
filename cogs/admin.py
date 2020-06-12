from datetime import datetime
import typing

import discord
from discord.ext import commands

import config
from custom_functions import dbselect
from custom_objects import Player, Team, Match

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="search")
    async def _search(self, ctx):
        if ctx.invoked_subcommand:
            pass

    @_search.command(name="player")
    async def _search_player(self, ctx, member: discord.Member = None):
        if member is None:
            command = self.bot.get_command('team')
            await ctx.invoke(command)
            return

        player = Player(member)
        await player.get_stats()

        embed = discord.Embed(color=0x00ffff)
        embed.set_author(name=player.name, icon_url=player.logo)
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
            Roster: {', '.join(['<@{player_id}>' for player_id in player.team.roster])}""")
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