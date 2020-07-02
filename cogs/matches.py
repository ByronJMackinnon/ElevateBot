import typing

import discord
from discord.ext import commands

from custom_functions import dbselect, is_in_database

class Matches(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def match_eligible(ctx):
        player = await Player(ctx.author)
        if player.team is not None and len(player.team.players) >= 3:
            return True
        return False

    @commands.command(name='challenge')
    @commands.check(match_eligible)
    async def _challenge(self, ctx, identifier: typing.Union[discord.Member, str, int]):
        member_id = None
        if identifier is int:
            if await is_in_database(sql=f'SELECT ID FROM teams WHERE ID={identifier}'):
                member_id = await dbselect('data.db', 'SELECT Player1 FROM teams WHERE ID=?', (identifier,))
            else:
                return await ctx.send("That team did not come up in the database. Please check the identifier again.\nYou can challenge another team using their TeamID, their Team Name, or by mentioning any player on the team!")
        elif identifier is str:
            if await is_in_database(sql=f'SELECT Name FROM teams WHERE Name={identifier.title()}'):
                member_id = await dbselect('data.db', 'SELECT Player1 FROM teams WHERE Name=?', (identifier.title(),))
            else:
                return await ctx.send("That team did not come up in the database. Please check the identifier again.\nYou can challenge another team using their TeamID, their Team Name, or by mentioning any player on the team!")
        elif identifier is discord.Member:
            pass
        
        if member_id is not None:
            identifier = get(ctx.guild.members, id=member_id)
        
        challenged_team = await Player(identifier).team
        if challenged_team is None:
            return await ctx.send('The challenged team is not eligible to play a match.')
        elif len(challenged_team.players) < 3:
            return await ctx.send(f'The challenged team do not have enough players for a match. ({len(challenged_team.players)} registered players)')

        challenger_team = await Player(ctx.author).team
        
        await DBInsert.invite(ctx, challenger_team, challenged_team)

        roster_mention = ', '.join([member.mention for member in challenger_team.players])

        embed = discord.Embed(title='You have been challenged!', color=challenger_team.color, description=f'{challenger_team.name} has sent you a challenge. Do you accept?')
        embed.add_field(name="Roster:", value=roster_mention, inline=False)
        embed.add_field(name="MMR", value=challenger_team.mmr, inline=False)
        embed.set_thumbnail(url=challenger_team.logo)
        
        challenge_channel = ctx.guild.get_channel(config.challenge_channel)

        await challenge_channel.send(content=roster_mention, embed=embed)

    @commands.command(name='report')
    async def _report(self, ctx, matchID, winorloss):
        possible_wins = ['win', 'w', 'won']
        possible_loss = ['loss', 'lose', 'l']
        if winorloss.lower() in possible_wins:
            pass
        elif winorloss.lower() in possible_loss:
            pass

def setup(bot):
    bot.add_cog(Matches(bot))