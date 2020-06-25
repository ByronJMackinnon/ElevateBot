from discord.ext import commands

import config
from custom_functions import is_in_database

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Checks if the members is already in the database, if not, create a new entry for them."""
        if is_in_database(f'SELECT ID FROM players WHERE ID={member.id}'):
            return
        if not member.bot:
            await DBInsert.member(member)

        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

    @commands.Cog.listener()
    async def on_member_remove(self, member):  # When a member leaves the server
        """Update member count in the database 'stats' table."""
        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

def setup(bot):
    bot.add_cog(Events(bot))