from discord.ext import commands

from custom_functions import dbupdate, dbselect

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
