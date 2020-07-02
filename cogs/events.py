import sys
import traceback
import asyncio
from datetime import datetime

import discord
from discord.ext import commands, tasks
from discord.utils import get

import config
from custom_functions import is_in_database, error_log, dbselect, chunks
from custom_objects import Player

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mmr_check.start()
        self.database_backup.start()

    def cog_unload(self):
        self.mmr_check.cancel()
        self.database_backup.cancel()

    @tasks.loop(minutes=1)
    async def match_scan(self):
        matches = await dbselect_all('data.db', 'SELECT ID, Timeout FROM matches WHERE Complete=?', (0,))
        print(matches)
        matches = chunks(matches, 2)
        for match in matches:
            dtobj = match[1]
            dtobj = datetime.strptime(dtobj, '%Y-%m-%d %H:%M:%S.%f')
            if dtobj > datetime.now():
                return
            elif dtobj < datetime.now():
                game = await Match(match[0])
                match.expired()

    @tasks.loop(seconds=1)
    async def mmr_check(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(config.server_id)
        for member in guild.members:
            player = await Player(member)

            before = player.mmr

            await player.verify_mmr()

            after = player.mmr
            if before != after:
                await mod_log(f"{member.mention}'s MMR was updated. {before} --> {after}")
            await asyncio.sleep(86400 / guild.member_count)

    @tasks.loop(minutes=1)
    async def database_backup(self):
        if datetime.now().strftime('%M') == '00':
            filename = datetime.now().strftime('%b-%d %I-%M%p.db')
            file = discord.File('data.db', filename=filename)
            await self.bot.wait_until_ready()
            guild = self.bot.get_guild(config.server_id)
            db_backup_channel = guild.get_channel(config.db_backup_channel)
            await db_backup_channel.send(file=file)

    @commands.group(name='tasks')
    @commands.is_owner()
    async def _task(self, ctx):
        if ctx.invoked_subcommand is None:
            pass

    @_task.command(name='stop')
    async def _task_stop(self, ctx, task):
        if task.lower() == 'mmr_check':
            if self.mmr_check.is_running():
                self.mmr_check.stop()
            else:
                return await ctx.send("That task is not currently running")
        elif task.lower() == 'database_backup':
            if self.database_backup.is_running():
                self.database_backup.stop()
            else:
                return await ctx.send("That task is not currently running")
    
    @_task.command(name='start')
    async def _task_start(self, ctx, task):
        if task.lower() == 'mmr_check':
            self.mmr_check.start()
        elif task.lower() == 'database_backup':
            self.database_backup.start()

    @_task.command(name='status')
    async def _task_status(self, ctx, task):
        if task.lower() == 'mmr_check':
            if self.mmr_check.is_running():
                await ctx.send(f"`mmr_check` is currently running. It has looped {self.mmr_check.current_loop} times.")
            else:
                return await ctx.send("That task is not currently running")
        elif task.lower() == 'database_backup':
            if self.database_backup.is_running():
                await ctx.send(f"`database_backup` is currently running. It has looped {self.database_backup.current_loop} times.")
            else:
                return await ctx.send("That task is not currently running")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if await is_in_database(sql=f'SELECT ID FROM invites WHERE MessageID={payload.message_id}'):
            identifier = await dbselect('data.db', "SELECT ID FROM invites WHERE MessageID=?", (payload.message_id,))
            invite = await Invite(identifier)
            if payload.user_id not in [member.id for member in invite.challenged.players]:
                return
            if emoji == config.checkmark_emoji:
                return await DBInsert.match(ctx, invite)
            elif emoji == config.cross_emoji:
                for member in invite.challenger.players:
                    await member.send(f"Your challenge to {challenged.name} was denied.")
            else:
                return

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

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await ctx.message.add_reaction(config.checkmark_emoji)

def setup(bot):
    bot.add_cog(Events(bot))