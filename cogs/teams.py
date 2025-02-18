import traceback
from datetime import datetime

import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_objects import Player, DBInsert
from custom_functions import dbselect, dbupdate, send_confirm

class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_team_captain(ctx):
        if config.team_captain_role_id in [role.id for role in ctx.author.roles]:
            return True
        return False

    async def is_team_member(ctx):
        if config.team_member_role_id in [role.id for role in ctx.author.roles]:
            return True
        return False

    @commands.group(name='player')
    async def _player(self, ctx):
        if ctx.invoked_subcommand is None:
            player = Player(ctx.author)
            await player.get_stats()

            embed = discord.Embed(color=0x00ffff, description=f"MMR: {player.mmr}")
            embed.set_thumbnail(url=player.logo)
            embed.set_author(name=f'{ctx.author.name}#{ctx.author.discriminator}', icon_url=ctx.author.avatar_url)
            if player.team is None:
                await ctx.send(embed=embed)
            else:
                team_players = ', '.join([f'<@{mem_id}>' for mem_id in player.team.players])
                embed.add_field(name=f'[{player.team.abbrev}] | {player.team.name}', value=f"MMR: {player.team.mmr}\nWins: {player.team.wins}\nLosses: {player.team.losses}\n Total Games: {player.team.wins + player.team.losses}\nRoster: {team_players}")
                embed.set_image(url=player.team.logo)
                await ctx.send(embed=embed)

    @_player.group(name='edit')
    async def _player_edit(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @_player_edit.command(name='logo')
    async def _player_edit_logo(self, ctx, link = None):
        player = Player(ctx.author)
        await player.get_stats()

        if link is None:
            if len(ctx.message.attachments) == 0:
                await player.edit_logo(ctx.author.avatar_url)
            else:
                await player.edit_logo(ctx.message.attachments[0].url)
        else:
            await player.edit_logo(link)

    
    @commands.command(name="updatemylogo", usage="<Link/File>")
    async def _updatemylogo(self, ctx, link = None):
        """Edits your own logo
        
        You can give a link, upload a file, or if you give nothing, it will update to your current discord profile picture.
        """

        if link is None:
            try:
                link = ctx.message.attachments[0].url
            except IndexError:
                link = ctx.author.avatar_url

        player = Player(ctx.author)
        await player.get_stats()

        await player.edit_logo(link)

        await send_confirm(ctx, "Your logo has been updated!")

    @commands.group(name='team')
    async def _team(self, ctx):
        """Shows your current teams information."""

        if ctx.invoked_subcommand is None:
            player = Player(ctx.author)
            await player.get_stats()
            if player.team is None:
                embed = discord.Embed(title="Free Agent", color=0x00ffff)
                embed.add_field(name="MMR:", value=player.mmr)
                embed.set_thumbnail(url=player.logo)
            else:
                roster = list(filter(None, player.team.players))
                roster = [f'<@{member}>' for member in roster]

                embed = discord.Embed(title=f'[{player.team.abbrev}] | {player.team.name}', color=0x00ffff, description=', '.join(roster))
                embed.add_field(name="MMR:", value=player.team.mmr)
                embed.add_field(name="Stats:", value=f'Wins: {player.team.wins}\nLosses: {player.team.losses}\nTotal Games: {player.team.wins + player.team.losses}', inline=False)
                embed.set_thumbnail(url=player.team.logo)
            embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @_team.command(name='create', usage="<Team Name>")
    async def _team_create(self, ctx, *, team_name):
        """Used to create a team."""

        if config.team_member_role_id in [role.id for role in ctx.author.roles]:
            return await ctx.send("I'm sorry, you are already in a team. Please leave your current team before creating a new one.")
        elif len(team_name) < config.shortest_team_name:
            return await ctx.send(f"The team name you choose is too short. (Less than {config.shortest_team_name} characters.")
        elif len(team_name) > config.longest_team_name:
            return await ctx.send(f"The team name you choose is too long. (More than {config.longest_team_name} characters.)")
        elif any(swear in team_name.lower() for swear in config.swears):
            return await ctx.send("Please use an appropriate name for your team.")

        await DBInsert().team(ctx, team_name)

    @_team.command(name='add', usage="@Player")
    @commands.check(is_team_captain)
    async def _team_add(self, ctx, member: discord.Member):
        """Add a player to your team"""

        player = Player(ctx.author)
        await player.get_stats()

        await player.team.add_player(member)

    @_team.command(name='remove', usage="@Player")
    @commands.check(is_team_captain)
    async def _team_remove(self, ctx, member: discord.Member):
        """Removes player from team"""

        player = Player(ctx.author)
        await player.get_stats()

        if member == ctx.author:
            command = self.bot.get_command('team leave')
            await ctx.invoke(command)
            return

        await player.team.remove_player(member)

    @_team.command(name='leave')
    @commands.check(is_team_member)
    async def _team_leave(self, ctx):
        """Removes yourself from the team."""

        player = Player(ctx.author)
        await player.get_stats()

        await player.team.remove_player(ctx.author)

    @_team.group(name='edit')
    @commands.check(is_team_captain)
    async def _team_edit(self, ctx):
        """Used to edit team information."""

        if ctx.invoked_subcommand is None:
            pass

    @_team_edit.command(name='abbrev', aliases=['abbreviation'], usage="<New Abbreviation>")
    async def _team_edit_abbrev(self, ctx, abbrev):
        """Edit your teams abbreviation"""

        player = Player(ctx.author)
        await player.get_stats()

        await player.team.edit_abbrev(ctx, abbrev)

    @_team_edit.command(name='name', usage="<New Team Name>")
    async def _team_edit_name(self, ctx, *, name):
        """Edits your teams name"""

        player = Player(ctx.author)
        await player.get_stats()

        await player.team.edit_name(ctx, name)

    @_team_edit.command(name='logo', usage="<Link/File>")
    async def _team_edit_logo(self, ctx, link = None):
        """Edits your team logo
        
        You can give a link, upload a file"""

        if link is None:
            if len(ctx.message.attachments) == 0:
                await ctx.author.send("I'm sorry, please send a photo with the command or paste a link to the photo.")
                return
            link = ctx.message.attachments[0].url

        player = Player(ctx.author)
        await player.get_stats()

        await player.team.edit_logo(ctx, link)

    @_team_edit.command(name='owner', usage="@Player")
    async def _team_edit_owner(self, ctx, member: discord.Member):
        """Transfer Ownership of Team to a new player"""

        player = Player(ctx.author)
        await player.get_stats()

        if member.id not in player.team.players:
            await ctx.author.send("You are only able to transfer ownership to someone on your team.")
            return

        players = player.team.players
        players.remove(member.id)

        new_captain = [member.id]

        players = new_captain + players

        await dbupdate('data.db', "UPDATE teams SET Player1, Player2, Player3, Player4, Player5 WHERE ID=?", (player.team.id,))

        captain_role = get(ctx.guild.roles, id=config.team_captain_role_id)

        await ctx.author.remove_roles(captain_role)
        await member.add_roles(captain_role)


def setup(bot):
    bot.add_cog(Teams(bot))
