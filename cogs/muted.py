from utils.checks import *
from utils.is_muted import *
from utils.common_embed import *
from discord.ext import tasks
import datetime
import discord
import typing
import pytz


class Time:
    # convert_to_hours takes time str
    #  translates time to hours
    #  returns hours int
    @staticmethod
    def convert_to_hours(time: str) -> int:
        hours_per_unit = {"h": 1, "d": 24, "w": 168, "m": 730, "y": 8766}
        return int(time[:-1]) * hours_per_unit[time[-1]]

    # add_text_to_time takes text str, time datetime.datetime
    #  parses and adds time
    #  returns time datetime.datetime
    def add_text_to_time(self, text: str, time: datetime.datetime) -> datetime.datetime:
        params = text.split()
        hours = 0
        for i in params:
            hours += self.convert_to_hours(i)

        time += datetime.timedelta(hours=hours)
        return time


class MutedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_conn = self.bot.db_conn

    # Mute takes user and time.
    #  mutes discord user from modmail
    #  sends confirmation on success, error on failure
    @commands.command()
    @has_access()
    @commands.guild_only()
    async def mute(self, ctx, user: typing.Union[discord.Member, str], end_time: typing.Optional[str] = None) -> None:
        if isinstance(user, str):
            try:
                user = await self.bot.fetch_user(int(user))
            except (discord.ext.commands.CommandInvokeError, ValueError):
                await ctx.send(embed=common_embed("Mute", "Unable to locate user, please check if the id is correct"))
                return

        if await is_muted(user.id, self.db_conn):
            await ctx.send(embed=common_embed("Mute", 'User already muted'))
            return

        msg = await ctx.send(embed=common_embed("Mute", f"Muting user {user.name}..."))
        db_user = await self.db_conn.fetch("SELECT * \
                                            FROM modmail.muted \
                                            WHERE \
                                                user_id = $1", user.id)

        if end_time:
            time_class = Time()
            time = time_class.add_text_to_time(end_time, datetime.datetime.now(pytz.utc))
            if db_user:
                await self.db_conn.execute("UPDATE modmail.muted \
                                            SET active = true, muted_by = $1, muted_until = $2 \
                                            WHERE \
                                               user_id = $3",
                                           ctx.author.id, time, user.id)
            else:
                await self.db_conn.execute("INSERT INTO modmail.muted (user_id, muted_by, muted_until, active) \
                                            VALUES ($1, $2, $3, true)",
                                           user.id, ctx.author.id, time)
        else:
            if db_user:
                await self.db_conn.execute("UPDATE modmail.muted \
                                            SET active = true, muted_by = $1 \
                                            WHERE \
                                               user_id = $2",
                                           ctx.author.id, user.id)
            else:
                await self.db_conn.execute("INSERT INTO modmail.muted (user_id, muted_by, active) \
                                            VALUES ($1, $2, true)",
                                           user.id, ctx.author.id)
        await msg.edit(embed=common_embed("Mute", f"Muted user {user}({user.id})"))
        await user.send(embed=common_embed("Muted", f"Due to misuse of our modmail bot, you were muted "
                                                    f"for {end_time}. Any messages you send here will not be "
                                                    f"received by the moderator team."))

    # Unmute takes user.
    #  unmutes discord user from modmail
    #  sends confirmation on success, error on failure
    @commands.command()
    @has_access()
    @commands.guild_only()
    async def unmute(self, ctx, user: typing.Union[discord.Member, str]) -> None:
        if isinstance(user, str):
            try:
                user = await self.bot.fetch_user(int(user))
            except (discord.ext.commands.CommandInvokeError, ValueError):
                await ctx.send(embed=common_embed("Unmute", "Unable to locate user, please check if the id is correct"))
                return

        if not await is_muted(user.id, self.db_conn):
            await ctx.send(embed=common_embed("Unmute", 'User is not muted'))
            return
        else:
            msg = await ctx.send(embed=common_embed("Unmute", f"Unmuting user {user}..."))
            await self.db_conn.execute("UPDATE modmail.muted \
                                        SET active = false \
                                        WHERE \
                                           user_id = $1",
                                       user.id)
            await msg.edit(embed=common_embed("Unmute", f'Unmuted user {user.id}'))

    # Muted takes no parameters
    #  Gets all active muted users from modmail
    #  Sends results on success, error on failure
    @commands.group(invoke_without_command=True)
    @is_admin()
    @commands.guild_only()
    async def muted(self, ctx) -> None:
        msg = await ctx.send(embed=common_embed("Muted", "Getting all active users..."))

        results = await self.db_conn.fetch("SELECT user_id, muted_by, muted_at, muted_until \
                                            FROM modmail.muted \
                                            WHERE \
                                               active = true")
        paginator = discord.ext.commands.Paginator()

        for row in results:
            user = await self.bot.fetch_user(row[0])
            muted_by = await self.bot.fetch_user(row[1])
            paginator.add_line(f"{user}({user.id})\n\n"
                               f"Muted by: {muted_by}({row[1]})\n"
                               f"Muted at: {row[2].strftime('%d/%m/%Y, %H:%M')}\n"
                               f"Muted until: {row[3].strftime('%d/%m/%Y, %H:%M')}\n"
                               f"--------------------------------\n")

        await msg.delete()
        for page in paginator.pages:
            await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=page))

    # Muted takes no parameters
    #  Gets all muted users from modmail
    #  Sends results on success, error on failure
    @muted.command()
    @is_admin()
    @commands.guild_only()
    async def all(self, ctx):
        msg = await ctx.send(embed=common_embed("Muted all", "Getting all users..."))

        results = await self.db_conn.fetch("SELECT user_id, muted_by, muted_at, muted_until, active \
                                            FROM modmail.muted")
        paginator = commands.Paginator()

        for row in results:
            user = await self.bot.fetch_user(row[0])
            muted_by = await self.bot.fetch_user(row[1])
            paginator.add_line(f"{user}({user.id})\n\n"
                               f"Muted: {'???' if bool(row[4]) else '???'}\n"
                               f"Muted by: {muted_by}({row[1]})\n"
                               f"Muted at: {row[2].strftime('%d/%m/%Y, %H:%M')}\n"
                               f"Muted until: {row[3].strftime('%d/%m/%Y, %H:%M')}\n"
                               f"--------------------------------\n")

        await msg.delete()
        for page in paginator.pages:
            await ctx.send(embed=discord.Embed(color=discord.Color.red(), description=page))

    # Muted takes a user id or discord.Member
    #  Checks if user is muted
    #  Returns results on success, error on failure
    @commands.command()
    @has_access()
    @commands.guild_only()
    async def is_muted(self, ctx, user: typing.Union[discord.Member, str]) -> None:
        if isinstance(user, str):
            try:
                user = await self.bot.fetch_user(int(user))
            except (commands.CommandInvokeError, ValueError):
                await ctx.send(embed=common_embed("Is muted",
                                                  "Unable to locate user, please check if the id is correct"))
                return

        result = await self.db_conn.fetchrow("SELECT active, muted_by, muted_at, muted_until \
                                              FROM modmail.muted \
                                              WHERE \
                                                user_id = $1", user.id)

        if result:
            muted_by = await self.bot.fetch_user(result[1])
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.red(),
                    description=f"```{user}({user.id})\n\n"
                                f"Muted: {'???' if is_muted else '???'}\n"
                                f"Muted by: {muted_by}({result[1]})\n"
                                f"Muted at: {result[2].strftime('%d/%m/%Y, %H:%M')}\n"
                                f"Muted until: {result[3].strftime('%d/%m/%Y, %H:%M')}\n```"))
        else:
            await ctx.send(embed=common_embed("Is muted", "User is not muted and is not in database"))


def setup(bot):
    bot.add_cog(MutedCog(bot))
