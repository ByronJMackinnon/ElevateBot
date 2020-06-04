from custom_functions import dbupdate, dbselect

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await dbupdate('data.db', 'INSERT INTO players (ID, Name, MMR, Team, Logo) VALUES (?, ?, ?, ?, ?)', (member.id, f"{member.name}#{member.discriminator}", None, None, member.avatar_url,))

        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await dbupdate('data.db', 'UPDATE stats SET Members=?', (member.guild.member_count,))

def setup(bot):
    bot.add_cog(Events(bot))
