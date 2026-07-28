import os
import dotenv
from utils import shared, helpers
from cogs import agent, moderation, polls, statistics
from cogs.economy import local as local_economy, global_eco as global_economy
from cogs.admin import utilities as admin_utilities, database as admin_database, economy as admin_economy
from cogs.minigames import basic as basic_minigames
#from cogs.matchmaking import cog as matchmaking
import discord
from discord.ext import commands
import json
from database import database_manager, models
from datetime import datetime
from typing import List
from time import sleep
import asyncio

async def setup_bot() -> None:
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level=shared.LogLevel.CRITICAL,
            description=f"DB_MANAGER ({DB_MANAGER}) has not been initialized."
        )
        raise RuntimeError("DB_MANAGER not initialized")
    
    helpers.custom_print(
        level=shared.LogLevel.INFO,
        description="Starting initial in-memory guild and user model initialization sync..."
    )
    
    guilds: List[models.Guild] = []
    users_per_guild: List[List[models.User]] = []
    for guild in shared.SHIRAYUME.guilds:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Bot connected to guild: {guild.name} (ID: {guild.id})."
        )
        model = DB_MANAGER.initialize_database_model(
            shared.Table.guilds,
            guild_id=guild.id,
            owner_id=guild.owner_id,
            name=guild.name,
            icon_url=str(guild.icon.url) if guild.icon else "",
            member_count=guild.member_count,
            bot_count=sum(1 for m in guild.members if m.bot),
            is_available=True, # If the guild is available, the bot is a member of it
            # this avoids deleting and re-adding guilds after bot is kicked and re-invited
            welcome_channel=-1,
            leave_channel=-1,
            joined_at=guild.me.joined_at,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_dirty=False,
            is_deleted=False
        )
        guilds.append(model)
        users: List[models.User] = []
        
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Processing {len(guild.members)} members for guild ID: {guild.id}."
        )
        
        for member in guild.members:
            user_model = DB_MANAGER.initialize_database_model(
                shared.Table.users,
                user_id=member.id,
                username=member.name,
                discriminator=member.discriminator,
                avatar_url=str(member.avatar.url) if member.avatar else "",
                is_bot=member.bot,
                currency=0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_dirty=False,
                is_deleted=False
            )
            users.append(user_model)
        users_per_guild.append(users)
    
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description="Committing synchronized users and guilds into database tracking cache state."
    )
    for users in users_per_guild:
        DB_MANAGER.add_users(users)
    
    DB_MANAGER.add_guilds(guilds)
    
    helpers.custom_print(
        level=shared.LogLevel.INFO,
        description="Bot database setup sync routine successfully completed."
    )

class ShirayumeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()

        super().__init__(
            command_prefix="!>",
            intents=intents,
            help_command=None
        )

        self.token = ""

    async def setup_hook(self):
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Executing initialization setup hooks for extensions and cogs..."
        )
        await admin_utilities.setup()
        await admin_database.setup()
        await admin_economy.setup()

        await agent.setup()
        await moderation.setup()
        await local_economy.setup()
        await global_economy.setup()
        await polls.setup()
        await statistics.setup()
        await basic_minigames.setup()
        #await matchmaking.setup()

        await helpers.update_default_color()
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="All extension setup subroutines hooked successfully."
        )

    async def on_ready(self):
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Connected as {self.user} (ID: {self.user.id})"
        )

        await setup_bot()

async def launch() -> None:

    def get_new_year() -> datetime:
        """
        Get new year's datetime.
        """

        # Set New Year date
        year = datetime.today().year + 1

        # Only if New Year set date to today
        if datetime.today().day == datetime.today().month == 1:
            year -= 1

        return datetime(year=year, month=1, day=1)
    
    if not dotenv.load_dotenv(dotenv_path = dotenv.find_dotenv(filename = ".env")):
        helpers.custom_print(
            level=shared.LogLevel.CRITICAL,
            description="No .env file found or failed to load."
        )
        return

    DB_HOST = os.environ["DB_HOST"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DATABASE = os.environ["DATABASE"]
    DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description=f"""
        DB Host: {DB_HOST}
        DB User: {DB_USER}
        DB Password: {DB_PASSWORD}
        Database: {DATABASE}
        Token: {DISCORD_TOKEN}
        """
    )
    database_manager.setup(DB_HOST, DB_USER, DB_PASSWORD, DATABASE)
    
    try:
        config_file = open("config.json", "r")
        config: dict = json.load(config_file)
        config_file.close()
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Config loaded."
        )
    except OSError:
        helpers.custom_print(
            level=shared.LogLevel.CRITICAL,
            description="Failed to open config.json file in read mode."
        )
        return
    
    shared.GLOBAL_CONFIG = config
    shared.GLOBAL_CONFIG["new_year"] = get_new_year()

    shared.SHIRAYUME = ShirayumeBot()
    shared.SHIRAYUME.command_prefix = config["bot_prefix"]
    helpers.custom_print(
        level=shared.LogLevel.INFO,
        description=f"Bot prefix set to: {shared.SHIRAYUME.command_prefix}"
    )
    shared.SHIRAYUME.token = DISCORD_TOKEN
    
    try:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Starting connection sequence to Discord Gateway API..."
        )
        await shared.SHIRAYUME.start(DISCORD_TOKEN, reconnect=True)
    except KeyboardInterrupt:
        pass
    finally:
        print("")
        if not shared.SHIRAYUME.is_closed():
            await shared.SHIRAYUME.close()
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Shirayume shutdown successfully."
        )

        if database_manager.DB_MANAGER:
            await database_manager.DB_MANAGER.database_close()
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Database connection closed gracefully."
            )
        else:
            helpers.custom_print(
                level=shared.LogLevel.WARNING,
                description=f"Database connection has already been closed."
            )

if __name__ == "__main__":
    try:
        asyncio.run(launch())
    except KeyboardInterrupt:
        pass