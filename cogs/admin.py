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



def setup(bot):
    bot.add_cog(Admin(bot))