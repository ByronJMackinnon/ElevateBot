import typing

import discord
from discord.ext import commands
from discord.utils import get

import config
from custom_functions import dbupdate, dbselect
from custom_objects import Player, Match

class Challenges(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='challenge', usage='<Team ID | @Member | Team Name>')
    async def _challenge(self, ctx, *, id: typing.Union[discord.Member, int, str]):
        """
        This command is used to challenge another team
        
        It takes 3 different arguments. Member, Team ID, or Team Name.
        """

        if type(id) is discord.Member:  # Player/Member passed
            member = id

        elif type(id) is int:  # Team ID Passed
            id = await dbselect('data.db', "SELECT Player1 FROM teams WHERE ID=?", (id,))
            member = get(ctx.guild.members, id=id)
            print("Member Object:", member)

        elif type(id) is str:  # Team Name Passed
            id = await dbselect('data.db', "SELECT Player1 FROM teams WHERE Name=?", (id.title(),))
            member = get(ctx.guild.members, id=id)

        challenger = Player(ctx.author)
        await challenger.get_stats()

        challenged = Player(member)
        await challenged.get_stats()


        challenger_players = [f'<@{player_id}>' for player_id in challenger.team.players]

        challenged_players = [f'<@{player_id}>' for player_id in challenged.team.players]

        if len(challenger_players) < 3:
            return await ctx.author.send("Your team has less than 3 players. Therefore you cannot challenge another team.")
        if len(challenged_players) < 3:
            return await ctx.author.send("The team you challenged does not currently have enough players to complete a match.")

        embed = discord.Embed(color=0x00ffff, description=f"{challenged.team.name} has been challenged by {challenger.team.name}. Are you interested?")
        embed.add_field(name="Roster:", value=', '.join(challenger_players))
        embed.add_field(name="Team Stats:", value=f'Wins: {challenger.team.wins}\nLosses: {challenger.team.losses}\nTotal Games: {challenger.team.wins + challenger.team.losses}', inline=False)
        embed.set_thumbnail(url=challenger.team.logo)
        embed.set_footer(text="You will have 4 days (96 hours) to report a match if accepted.", icon_url=config.elevate_logo)

        msg = await ctx.send(embed=embed)
        channel = msg.channel.id

        await msg.add_reaction(config.checkmark_emoji)
        await msg.add_reaction(config.cross_emoji)

        await dbupdate('data.db', "INSERT INTO invites (Channel, MessageID, Challenger, Challenged, Inviter) VALUES (?, ?, ?, ?, ?)", (channel, msg.id, challenger.team.id, challenged.team.id, ctx.author.id,))

        reaction, user = await self.bot.wait_for('reaction_add')

        player = Player(user)
        await player.get_stats()

        if player.team == challenged.team:
            if str(reaction) == config.checkmark_emoji:
                await ctx.send("Okay, match is a go!")
                return await DBInsert.match(player.team.id, challenged.team)

            elif str(reaction) == config.cross_emoji:
                return await ctx.send("Okay, no match.")
        
        else:
            pass


class Reports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="report", usage="<Match ID> <Won/Loss>")
    async def _report(self, ctx, matchID, winorloss):
        """
        This command is used to report scores for matches played.

        This command takes 2 arguments. The ID for the match, and whether you won or loss.
        """

        check = await dbselect('data.db', "SELECT Complete FROM matches WHERE ID=?", (matchID,))

        if winorloss.lower() in ['w', 'win', 'won']:
            wl_mine = 'W'
            wl_other = 'L'

        elif winorloss.lower() in ['l', 'loss', 'lost']:
            wl_mine = 'L'
            wl_other = 'W'

        if check is None:
            await ctx.send("There is not match in the database with this ID. Please check the ID again.")
            return

        elif check is True:
            await ctx.send("This match has already been reported. Please reach out to a staff member if there is an issue.")
            return

        match = Match(matchID)

        if ctx.author.id in match.team1.players:
            my_team = match.team1
            other_team = match.team2
            pass
        elif ctx.author.id in match.team2.players:
            my_team = match.team2
            other_team = match.team1
        else:
            await ctx.send("You aren't able to report a match you weren't a part of.")
            return

        if winorloss.lower() in ['w', 'win', 'won']:  # Reporter Won
            if my_team.mmr > other_team.mmr:
                for player in my_team.players:
                    player = get(ctx.guild.members, id=player)
                    player = Player(player)
                    player.mmr_change(match.loss)

                for player in other_team.players:
                    player = get(ctx.guild.members, id=player)
                    player = Player(player)
                    player.mmr_change(match.loss * -1)

            elif my_team.mmr < other_team.mmr:
                for player in my_team.players:
                    player = get(ctx.guild.members, id=player)
                    player = Player(player)
                    player.mmr_change(match.gain)

                for player in other_team.players:
                    player = get(ctx.guild.members, id=player)
                    player = Player(player)
                    player.mmr_change(match.gain * -1)

        elif winorloss.lower() in ['l', 'loss', 'lost']:  # Reporter Lost
            if my_team.mmr > other_team.mmr:
                for player in my_team.players:
                    player = get(ctx.guild.members, id=player)
                    player = Player(player)
                    player.mmr_change(match.gain * -1)

                for player in other_team.mmr:
                    player = get(ctx.guild.members, id=player)
                    player = Player(player)
                    player.mmr_change(match.gain)

            elif my_team.mmr < other_team.mmr:
                for player in my_team.players:
                    player = get(ctx.guild.members, id=player)
                    player = Player(player)
                    player.mmr_change(match.loss * -1)

                for player in other_team.players:
                    player = get(ctx.guild.members, id=player)
                    player = Player(player)
                    player.mmr_change(match.loss)

        reporter = Player(ctx.author)
        await reporter.get_stats()

        if reporter.team.id == match.team1.id:
            await dbupdate('data.db', "UPDATE matches SET WL1=?, WL2=?, Complete=? WHERE ID=?", (wl_mine, wl_other, True, matchID,))

        elif reporter.team.id == match.team2.id:
            await dbupdate('data.db', "UPDATE matches SET WL1=?, WL2=?, Complete=? WHERE ID=?", (wl_other, wl_mine, True, matchID,))



def setup(bot):
    bot.add_cog(Challenges(bot))
    bot.add_cog(Reports(bot))
