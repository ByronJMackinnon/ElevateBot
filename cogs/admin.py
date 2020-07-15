import typing

import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import dbselect_all, dbselect, dbupdate, chunks
from custom_objects import Player, Match

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
    async def _nonick(self, ctx, member: typing.Union[discord.Member, str]):
        if isinstance(member, discord.Member):
            await member.edit(nick=None)
        else:
            if member.lower() == "all":
                for member in ctx.guild.members:
                    if 715899669544173660 in [role.id for role in member.roles]:
                        return
                    await member.edit(nick=None)

    @commands.command(name="echo")
    async def _echo(self, ctx, destination: typing.Union[discord.Member, discord.TextChannel], *, message):
        await destination.send(message)

    @commands.group(name='search')
    async def _search(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @_search.command(name='player')
    async def _search_player(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        player = await Player(ctx, member)
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

    @_search.command(name='team')
    async def _search_team(self, ctx, identifier: typing.Union[discord.Member, int, str]):
        if isinstance(identifier, discord.Member):
            print('Identifier was a Discord Member Object')
            pass
        elif isinstance(identifier, int):
            print('Identifier was an Integer Object')
            capt = await dbselect('data.db', "SELECT Player1 FROM teams WHERE ID=?", (identifier,))
            identifier = get(ctx.guild.members, id=capt)
        elif isinstance(identifier, str):
            print('Identifier was a String Object')
            capt = await dbselect('data.db', "SELECT Player1 FROM teams WHERE Name=?", (identifier.title(),))
            identifier = get(ctx.guild.members, id=capt)
        print(type(identifier))
        player = await Player(ctx, identifier)
        footer = None
        if player.team.color is None:
            color = discord.Color.default()
            footer = "You can set a color value for your team. !team edit color <hex> (ex: 00ffff)"
        else:
            if player.team.color > 16777215:
                color = discord.Color.default()
                footer = "Your color value is not set properly. Only the 6 hex values please."
            else:
                color = discord.Color(value=player.team.color)

        roster = list(filter(None, player.team.players))
        roster = [member.mention for member in roster]

        embed = discord.Embed(color=color, description=f'**[{player.team.abbrev}]** | {player.team.name}')
        embed.add_field(name="Roster:", value=', '.join(roster))
        embed.add_field(name="MMR:", value=player.team.mmr, inline=False)
        embed.add_field(name="Stats:", value=f'Wins: {player.team.wins}\nLosses: {player.team.losses}\nTotal Games: {player.team.wins + player.team.losses}', inline=False)
        embed.set_thumbnail(url=player.team.logo)
        await ctx.send(embed=embed)

    @_search.command(name='match')
    async def _search_match(self, ctx, MatchID):
        match = await Match(ctx, MatchID)
        embed = discord.Embed(title="Match Info", color=0x00ffff)
        embed.add_field(name=f'[{match.t1.abbrev}] | {match.t1.name} - {match.wl1}', value=f'MMR: {match.t1.mmr}\n' + ', '.join([member.mention for member in match.t1.players]), inline=False)
        embed.add_field(name=f'[{match.t2.abbrev}] | {match.t2.name} - {match.wl2}', value=f'MMR: {match.t2.mmr}\n' + ', '.join([member.mention for member in match.t2.players]), inline=False)
        await ctx.send(embed=embed)

    @commands.group(name='db', aliases=['database'])
    async def _db(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @_db.command(name='backup')
    async def _db_backup(self, ctx):
        file = discord.File('data.db', filename='manual_backup.db')
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(config.server_id)
        db_backup_channel = guild.get_channel(config.db_backup_channel)
        await db_backup_channel.send(file=file)

    @_db.command(name='view')
    async def _db_view(self, ctx, columns, table, conditional = None):
        if conditional is None:
            results = await dbselect_all('data.db', f"SELECT {columns} FROM {table}", ())
        else:
            results = await dbselect_all('data.db', f"SELECT {columns} FROM {table} WHERE {conditional}", ())
        
        columns = columns.strip().split(',')

        results = await chunks(results, len(columns))

        layout = ''

        for row in results:
            temp_hold = []
            for element in row:
                temp_hold.append(str(element))
            layout += ', '.join(temp_hold)
            layout += '\n'

        embed = discord.Embed(title="Database Query", color=0xff0000)
        embed.add_field(name=', '.join(columns), value=layout)
        await ctx.send(embed=embed)

    @_db.command(name='edit')
    @commands.is_owner()
    async def _db_edit(self, ctx, table, column, new_value, conditional = None):
        #* UPDATE players SET team=1 <WHERE {conditional}>
        if conditional is None:
            if new_value.title() == "None":
                await dbupdate('data.db', f'UPDATE {table} SET {column}=?', (None,))
            else:
                await dbupdate('data.db', f"UPDATE {table} SET {column}={new_value}", ())
            await ctx.send(f"Database has been updated. Every entry in the **{column}** column, has been updated to `{new_value}`")
        else:
            before = await dbselect('data.db', f"SELECT * FROM {table} WHERE {conditional}", ())
            if new_value.title() == "None":
                await dbupdate('data.db', f'UPDATE {table} SET {column}=? WHERE {conditional}', (None,))
            else:
                await dbupdate('data.db', f"UPDATE {table} SET {column}={new_value} WHERE {conditional}", ())
            after = await dbselect('data.db', f"SELECT * FROM {table} WHERE {conditional}", ())
            await ctx.send(f'Database updated.\nBefore: {before}\n\nAfter: {after}')

def setup(bot):
    bot.add_cog(Admin(bot))