import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import is_in_database
from custom_objects import Player, DBInsert

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

    async def is_verified(ctx):
        if await is_in_database(sql=f'SELECT MMR FROM players WHERE ID={ctx.author.id}'):
            return True
        return False

    @commands.group(name='player')
    @commands.check(is_verified)
    async def _player(self, ctx):
        player = await Player(ctx, ctx.author)
        footer = None
        if player.color is None:
            color = discord.Color.default()
            footer = "You can set a color value for yourself. using !player edit color <hex>"
        else:
            color = discord.Color(value=int(player.color, 16))

        embed = discord.Embed(color=color, description=player.member.mention)
        if footer is not None:
            embed.set_footer(text=footer)
        embed.add_field(name="MMR:", value=player.mmr)
        embed.set_author(name=player.name, icon_url=player.member.avatar_url)
        embed.set_thumbnail(url=player.logo)
        if player.team is None:
            embed.add_field(name="Team:", value="**__Free Agent__**", inline=False)
        else:
            embed.add_field(name="Team:", value=f'**[{player.team.abbrev}]** | {player.team.name}', inline=False)
        await ctx.send(embed=embed)


    @commands.group(name='team')
    async def _team(self, ctx):
        if ctx.invoked_subcommand is None:
            player = await Player(ctx, ctx.author)
            if player.team is None:
                footer = None
                if player.color is None:
                    color = discord.Color.default()
                    footer = "You can set a color value for yourself. using !player edit color <hex>"
                else:
                    color = discord.Color(value=int(player.color, 16))

                embed = discord.Embed(title="Free Agent", color=color)
                embed.add_field(name="MMR:", value=player.mmr)
                embed.set_thumbnail(url=player.logo)
                if footer is not None:
                    embed.set_footer(text=footer)
            else:

                footer = None
                if player.team.color is None:
                    color = discord.Color.default()
                    footer = "You can set a color value for your team. !team edit color <hex> (ex: 00ffff)"
                else:
                    if int(player.team.color, 16) > 16777215:
                        color = discord.Color.default()
                        footer = "Your color value is not set properly. Only the 6 hex values please."
                    else:
                        color = discord.Color(value=int(player.team.color, 16))

                roster = list(filter(None, player.team.players))
                roster = [member.mention for member in roster]

                embed = discord.Embed(color=color, description=f'**[{player.team.abbrev}]** | {player.team.name}')
                embed.add_field(name="Roster:", value=', '.join(roster))
                embed.add_field(name="MMR:", value=player.team.mmr, inline=False)
                embed.add_field(name="Stats:", value=f'Wins: {player.team.wins}\nLosses: {player.team.losses}\nTotal Games: {player.team.wins + player.team.losses}', inline=False)
                embed.set_thumbnail(url=player.team.logo)
                if footer is not None:
                    embed.set_footer(text=footer)
            embed.set_author(name=player.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

    @_team.command(name='create')
    async def _team_create(self, ctx, *, team_name):
        await DBInsert.team(self, ctx, team_name)
        team_member_role = get(ctx.guild.roles, id=config.team_member_role_id)
        team_capt_role = get(ctx.guild.roles, id=config.team_captain_role_id)
        await ctx.author.add_roles(team_member_role, team_capt_role)
        player = await Player(ctx, ctx.author)
        await ctx.author.edit(nick=f'{player.team.abbrev} | {player.name}')

    @_team.command(name='add')
    async def _team_add(self, ctx, member: discord.Member):
        player = await Player(ctx, ctx.author)
        await player.team.add_player(member)

    @_team.command(name='remove')
    async def _team_remove(self, ctx, member: discord.Member):
        player = await Player(ctx, ctx.author)
        await player.team.remove_player(ctx, member)

    @_team.command(name="leave")
    async def _team_leave(self, ctx):
        # INFO Database Stuff
        player = await Player(ctx, ctx.author)
        await player.team.remove_player(ctx, ctx.author)
        
        # INFO: Discord Stuff
            # INFO: Gather Roles
        team_member = get(ctx.guild.roles, id=config.team_member_role_id)
        team_capt = get(ctx.guild.roles, id=config.team_captain_role_id)
            # INFO: Remove Necessary Roles.
        if config.team_captain_role_id in [role.id for role in ctx.author.roles]:
            await ctx.author.remove_roles(team_member, team_capt)
        else:
            await ctx.author.remove_roles(team_member)
        await ctx.author.edit(nick=None)  # INFO: Remove Nickname
        await ctx.send(f"You have left {player.team.name}")

    @_team.group(name='edit')
    async def _team_edit(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @_team_edit.command(name='color')
    async def _team_edit_color(self, ctx, color):
        if int(color, 16) > 16777215 or int(color, 16) < 0:
            return await ctx.send("That is not a valid hex value. (Ex: 000000, ffffff, or ff00a1")
        player = await Player(ctx, ctx.author)
        await player.team.set_color(color)

    @_team_edit.command(name='name')
    async def _team_edit_name(self, ctx, *, name):
        player = await Player(ctx, ctx.author)
        await player.team.set_name(name)

    @_team_edit.command(name='abbreviation', aliases=['abbrev'])
    async def _team_edit_abbrev(self, ctx, abbrev):
        if len(abbrev) > 4 or len(abbrev) < 0:
            return await ctx.send("That is not a valid length for abbreviations. Please enter 1-4 characters.", delete_after=5)
        for swear in config.swears:
            if swear in abbrev.lower():
                return await ctx.send("Please don't use any profanity in your team abbreviation.", delete_after=5)
        player = await Player(ctx, ctx.author)
        await player.team.set_abbreviation(abbrev)
    
    @_team_edit.command(name='logo')
    async def _team_edit_logo(self, ctx, link = None):
        if link is None:
            try:
                link = ctx.message.attachments[0].url
            except:
                return await ctx.send("We were unable to find the picture you would like to use. Please use a file or a link with the command.", delete_after=10)
        player = await Player(ctx, ctx.author)
        await player.team.set_logo(link)

def setup(bot):
    bot.add_cog(Teams(bot))