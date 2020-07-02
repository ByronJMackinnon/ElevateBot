import discord
from discord.ext import commands

import config
from custom_functions import dbselect_all, dbselect, dbupdate, chunks

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(ctx):
        if config.admin_role_id in [role.id for role in ctx.author.roles]:
            return True
        return False

    @commands.group(name='db', aliases=['database'])
    @commands.check(is_admin)
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

        results = chunks(results, len(columns))

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