from datetime import datetime

from discord.ext import commands, tasks
from discord.utils import get

from custom_functions import dbupdate, dbselect, dbselect_all
from custom_objects import Team, DBInsert

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timeout_scan.start()

    def cog_unload(self):
        self.timeout_scan.cancel()

    @tasks.loop(seconds=60.0)
    async def timeout_scan(self):
        timeouts = dbselect_all('data.db', "SELECT Timeout FROM matches", ())
        timeouts = [datetime.strptime(dt, "%Y-%m-%d %H:%M") for dt in timeouts]
        for id, timeout in enumerate(timeouts, 1):
            if timeout <= datetime.now():
                match = Match(id)
                await match.timeout(ctx)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        check = await dbselect('data.db', "SELECT * FROM invites WHERE MessageID=?", (payload.message_id,))
        if check is None:
            return
        print(check)
        channel, msgID, challenger, challenged, inviter = check
        challenger = Team(challenger)
        await challenger.get_stats()

        challenged = Team(challenged)
        await challenged.get_stats()

        if payload.user_id not in challenged.players:
            return

        await DBInsert.match(challenger.id, challenged.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):  # When a member joins the server
        """Checks if the members is already in the database, if not, create a new entry for them."""
        check = await dbselect('data.db' 'SELECT ID FROM players WHERE ID=?', (member.id,))

        if check is None:
            await DBInsert.member(member)

        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

    @commands.Cog.listener()
    async def on_member_remove(self, member):  # When a member leaves the server
        """Update member count in the database 'stats' table."""
        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """If a member updates their name or discriminator, I reflect that change in the database."""
        if before.name != after.name or before.discriminator != after.discriminator:
            await dbupdate("data.db", "UPDATE players SET Name=? WHERE ID=?", (f'{after.name}#{after.discriminator}', after.id,))

def setup(bot):
    bot.add_cog(Events(bot))
