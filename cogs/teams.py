import typing
import asyncio

import discord
from discord.ext import commands

import config
from custom_objects import Player, DBInsert, Elevate, Team, Match
from custom_functions import dbupdate, dbselect
from errors import PlayerError, TeamError, InappropriateError

class Teams(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_captain(ctx):
        if config.team_captain_role_id in [role.id for role in ctx.author.roles]:
            return True
        return False

    async def is_member(ctx):
        if config.team_member_role_id in [role.id for role in ctx.author.roles]:
            return True
        return False

    @commands.command(name='leaderboard', aliases=['lb'])
    async def _leaderboard(self, ctx):
        embed = discord.Embed(color=0x00ffff, description=f'For the time being, the leaderboard can be found on [this](http://159.65.35.63:5000/) website. However it will be migrated shortly.')
        await ctx.send(embed=embed)

    @commands.group(name='player')
    async def _player(self, ctx):
        if ctx.invoked_subcommand is None:
            player = await Player(ctx, ctx.author)
            
            embed = discord.Embed(color=player.color, description=player.member.mention)
            embed.set_author(name=player.member, icon_url=player.member.avatar_url)
            embed.set_thumbnail(url=player.logo)
            if player.mmr is None:
                embed.add_field(name='MMR:', value="Not verified.")
            else:
                embed.add_field(name='MMR:', value=player.mmr)
            
            if player.team is None:
                embed.add_field(name='Team:', value="Free Agent.", inline=False)
            else:
                embed.add_field(name="Team:", value=str(player.team), inline=False)
                embed.set_footer(text=f'Team ID: {player.team.id}')

            await ctx.send(embed=embed)

    @_player.group(name='edit')
    async def _player_edit(self, ctx):
        if ctx.invoked_subcommand is None:
            prefix = await self.bot.get_prefix(ctx.message)
            
            embed = discord.Embed(title="Player Edit", color=0x00ffff, description=f'{prefix}player edit color <hex value> | Changes your player color for embeds.\n{prefix}player edit logo <link> | If link is not provided. Logo will be updated to your discord profile picture.')

            await ctx.send(embed=embed)

    @_player_edit.command(name='logo')
    async def _player_edit_logo(self, ctx, link=None):
        if link is None:
            if len(ctx.message.attachments) > 0:
                link = ctx.message.attachments[0].url  # If image was sent as a file
            else:
                link = str(ctx.author.avatar_url)  # If no new image was offered.

        else:  # If there was a link supplied. Checks to make sure it is a supported format.
            passed = 0
            picture_files = ['.webp', '.jpg', '.png', '.gif']
            for filetype in picture_files:
                if link.endswith(filetype):
                    passed += 1
                else:
                    pass
            if passed == 0:
                raise PlayerError("The link given does not appear to be a supported image format. (.webp, .jpg, .png, .gif)")
                    
        
        player = await Player(ctx, ctx.author)
        await player.set_logo(link)

        embed = discord.Embed(color=player.color, description="Your logo has been updated!")
        embed.set_image(url=player.logo)
        
        await ctx.send(embed=embed)

    @_player_edit.command(name='color')
    async def _player_edit_color(self, ctx, *, color):
        try:
            color = int(color, 16)
        except ValueError as e:
            raise PlayerError("Invalid Color. Only hex values allowed. `00ffff`, `1abc9c`, `2ecc71`, etc...")
        
        player = await Player(ctx, ctx.author)
        await player.set_color(color)

        embed = discord.Embed(color=player.color, description="Your color has been updated.")

        await ctx.send(embed=embed)


    @commands.group(name='team')
    async def _team(self, ctx):
        if ctx.invoked_subcommand is None:
            player = await Player(ctx, ctx.author)
            if player.team is None:
                raise TeamError("You do not appear to have a team at the moment. Please create one by using `!team create <Team Name>`")
            else:
                embed = discord.Embed(color=player.team.color)
                embed.set_author(name=f'[{player.team.abbreviation}] | {player.team.name}')
                embed.set_thumbnail(url=player.team.logo)
                embed.add_field(name='MMR:', value=player.team.mmr, inline=False)
                embed.add_field(name='Tier:', value=player.team.tier, inline=False)
                embed.add_field(name='Game Stats:', value=f'Wins: {player.team.wins}\nLosses: {player.team.losses}\nTotal Games: {player.team.wins + player.team.losses}', inline=False)
                embed.add_field(name=f'Roster: ({len(player.team.members)}/5)', value=', '.join([member.mention for member in player.team.members]))

                await ctx.send(embed=embed)

    @_team.command(name='create')
    async def _team_create(self, ctx, *, team_name):
        async with ctx.channel.typing():
            if config.team_member_role_id in [role.id for role in ctx.author.roles]:
                raise PlayerError("You already belong to a team.")
            
            await DBInsert.team(ctx, team_name)

            elevate = Elevate(ctx)

            player = await Player(ctx, ctx.author)
            team = player.team

            await team.save()

            await player.member.add_roles(elevate.roles.team_captain, elevate.roles.team_member)

            embed = discord.Embed(color=team.color, description=f"Your team was registered.\n{str(team)}")

            await player.member.edit(nick=f'{team.abbreviation} | {player.member.name}')

            await ctx.send(embed=embed)

    @_team.command(name='add')
    @commands.check(is_captain)
    async def _team_add(self, ctx, member: discord.Member):
        async with ctx.channel.typing():
            if isinstance(member, discord.Member):
                player = await Player(ctx, ctx.author)
                member = await Player(ctx, member)

                await player.team.add(member)

                elevate = Elevate(ctx)

                await member.member.add_roles(elevate.roles.team_member)
                await member.member.edit(nick=f'{player.team.abbreviation} | {member.member.name}')

                embed = discord.Embed(color=player.team.color, description=f"{member.member.mention} has been added to {str(player.team)}")
                await ctx.send(embed=embed)

    @_team.command(name='remove')
    @commands.check(is_captain)
    async def _team_remove(self, ctx, member: discord.Member):
        async with ctx.channel.typing():
            if isinstance(member, discord.Member):
                player = await Player(ctx, ctx.author)
                member = await Player(ctx, member)

                await member.member.edit(nick=None)

                await player.team.remove(member)

                elevate = Elevate(ctx)

                await member.member.remove_roles(elevate.roles.team_member)

                embed = discord.Embed(color=player.team.color, description=f"{member.member.mention} has been removed from {str(player.team)}")
                await ctx.send(embed=embed)

    @_team.command(name='leave')
    @commands.check(is_member)
    async def _team_leave(self, ctx):
        async with ctx.channel.typing():
            player = await Player(ctx, ctx.author)
            elevate = Elevate(ctx)
            if elevate.roles.team_captain in player.member.roles:
                await player.member.remove_roles(elevate.roles.team_captain, elevate.roles.team_member)
                await player.member.edit(nick=None)

                if len(player.team.members) == 1:
                    embed = discord.Embed(color=player.team.color, description=f"You have been removed from {str(player.team)}\nYou were the only player on the team. So it was deleted.")

                    await dbupdate('data.db', "DELETE FROM teams WHERE ID=?", (player.team.id,))
                    await player.set_team(None)

                    await ctx.send(embed=embed)
                
                else:
                    embed = discord.Embed(color=player.team.color, description=f"You have been removed from {str(player.team)}")

                    await player.team.members[1].add_roles(elevate.roles.team_captain)
                    await player.team.sub(player)
                    await player.set_team(None)
                    await player.member.edit(nick=None)

                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(color=player.team.color, description=f"You have been removed from {str(player.team)}")

                await player.member.remove_roles(elevate.roles.team_member)
                await player.member.edit(nick=None)

                await player.team.sub(player)
                await player.set_team(None)

                await ctx.send(embed=embed)

    @_team.group(name='edit')
    @commands.check(is_captain)
    async def _team_edit(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @_team_edit.command(name='name')
    async def _team_edit_name(self, ctx, *, name):
        player = await Player(ctx, ctx.author)
        await player.team.set_name(name)

        embed = discord.Embed(color=player.team.color, description=f'Your team name is now {str(player.team)}')
        await ctx.send(embed=embed)

    @_team_edit.command(name='abbreviation', aliases=['abbrev'])
    async def _team_edit_abbreviation(self, ctx, *, abbreviation):
        player = await Player(ctx, ctx.author)
        await player.team.set_abbreviation(abbreviation)

        embed = discord.Embed(color=player.team.color, description=f'Your team abbreviation is now {str(player.team)}')
        await ctx.send(embed=embed)

    @_team_edit.command(name='logo')
    async def _team_edit_logo(self, ctx, link=None):
        player = await Player(ctx, ctx.author)
        await player.team.set_logo(link)

        embed = discord.Embed(color=player.team.color, description=f'Here is your team logo now.')
        embed.set_image(url=player.team.logo)
        await ctx.send(embed=embed)

    @_team_edit.command(name='color')
    async def _team_edit_color(self, ctx, *, color):
        player = await Player(ctx, ctx.author)
        await player.team.set_color(color)

        embed = discord.Embed(color=player.team.color, description=f'Your team color was edited successfully!')
        await ctx.send(embed=embed)

    @commands.command(name="challenge")
    async def _challenge(self, ctx, *, team: typing.Union[discord.Member, int, str]):
        if isinstance(team, discord.Member):
            player = await Player(ctx, team)
            team = player.team

            if team is None:
                raise TeamError("This member is not currently on a team.")


        elif isinstance(team, int):
            team = await Team(ctx, team)

        elif isinstance(team, str):
            team_id = await dbselect('data.db', "SELECT ID FROM teams WHERE Name=?", (team.title(),))
            team = await Team(ctx, team_id)

        else:
            raise CodeError(f"I'm not sure why this failed. It was in the challenge command. Expected type for team was not Member, Int, String.\nType: {type(team)} Value: {team}")

        player = await Player(ctx, ctx.author)

        if player.team.id == team.id:
            raise TeamError("You cannot send a challenge to your own team.")

        if player.team.eligible and team.eligible:
            await DBInsert.invite(ctx, team)
        else:
            if not player.team.eligible:
                raise TeamError(f"Your team is ineligible to play matches. They need a minimum of 3 players. (Currently at {len(player.team.members)})")
            elif not team.eligible:
                raise TeamError(f'The team you challenged is ineligible to play matches. They need a minimum of 3 players. (Currently at {len(team.members)})')

    @commands.command(name='report')
    async def _report(self, ctx, match_id, winorloss):
        match = await Match(ctx, match_id)
        player = await Player(ctx, ctx.author)

        if match.challenger.id == player.team.id:
            my_team = match.challenger
            other_team = match.challenged
        
        elif match.challenged.id == player.team.id:
            my_team = match.challenged
            other_team = match.challenger

        possible_wins = ['w', 'win', 'won']
        possible_loss = ['l', 'loss', 'lost']

        if winorloss.lower() in possible_wins:
            await match.won(my_team)
        elif winorloss.lower() in possible_loss:
            await match.won(other_team)
        else:
            raise PlayerError("Invalid value. !report <match_id> <w/l>")

        await ctx.send("Done.")

def setup(bot):
    bot.add_cog(Teams(bot))