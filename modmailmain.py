from configparser import ConfigParser

import discord
from discord.ext import commands
import asyncpg
import asyncio
import sys
import os


class Bot(commands.Bot):
    def __init__(self, database_conn, conf, event_loop):
        super().__init__(command_prefix='!', description="Official Floor-Gang modmail bot", loop=event_loop,
                         case_insensitive=True, intents=discord.Intents.default())
        self.db_conn = database_conn
        self.conf = conf

        for cog in os.listdir('./cogs'):
            if cog.endswith('.py') and not cog.startswith('_'):
                try:
                    self.load_extension(f"cogs.{cog.replace('.py', '')}")
                except Exception as err:
                    print(f"{cog} can't be loaded")
                    raise err

        for task in os.listdir('./tasks'):
            if task.endswith('.py') and not task.startswith('_'):
                try:
                    self.load_extension(f"tasks.{task.replace('.py', '')}")
                except Exception as err:
                    print(f"{task} can't be loaded")
                    raise err

        print("Loaded all extensions")

    @staticmethod
    async def on_ready():
        print('We have logged in!')

    def run(self):
        super().run(Config.conf.get('global', 'discord_id'))


class Database:
    db_conn = None

    @staticmethod
    async def initiate_database():
        try:
            Database.db_conn = await asyncpg.create_pool(user=Config.conf.get('database_creds', 'username'),
                                                         password=Config.conf.get('database_creds', 'password'),
                                                         host=Config.conf.get('database_creds', 'host'),
                                                         port=Config.conf.get('database_creds', 'port'),
                                                         database=Config.conf.get('database_creds', 'database'))
            return True

        except Exception as e:
            print('Failed to connect to database', e)
            return False


class Config:
    conf = None

    @staticmethod
    def initiate_config():
        try:
            Config.conf = ConfigParser()
            os.chdir(sys.path[0])
            if os.path.exists('conf.ini'):
                Config.conf.read('conf.ini')
                return True
            else:
                print('Config file, conf.ini, was not found.')
                return False

        except Exception as e:
            print("Could not initiate conf.", e)
            return False


def main():
    if not Config.initiate_config():
        sys.exit()

    event_loop = asyncio.get_event_loop()
    if not event_loop.run_until_complete(Database.initiate_database()):
        sys.exit()

    bot = Bot(database_conn=Database.db_conn, conf=Config.conf, event_loop=event_loop)
    bot.run()


if __name__ == '__main__':
    main()
