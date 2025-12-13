import os
import dotenv
from database import database_manager
from cogs import moderation, economy, polls, rankings, utilities, web_scraping
from cogs.minigames import basic
import discord
from discord.ext import commands
import json
#import asyncio
from utils import shared, helpers
from database import database_manager, models
import datetime
from typing import List

bot = commands.Bot("EXE>", intents = discord.Intents.all())

async def setup_bot() -> None:
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "launch.setup_bot",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")
    #bot.remove_command("help")
    #bot.help_command = None
    guilds: List[models.Guild] = []
    users_per_guild: List[List[models.User]] = []
    for guild in bot.guilds:
        helpers.custom_print(
            level = shared.LogLevel.INFO,
            function_name = "launch.setup_bot",
            description = f"Bot connected to guild: {guild.name} (ID: {guild.id})"
        )
        model = DB_MANAGER.initialize_database_model(shared.Table.guilds,
            guild_id = guild.id,
            owner_id = guild.owner_id,
            name = guild.name,
            icon_url = str(guild.icon.url) if guild.icon else None,
            member_count = guild.member_count,
            bot_count = sum(1 for m in guild.members if m.bot),
            is_available = True, # If the guild is available, the bot is a member of it
            # this avoids deleting and re-adding guilds after bot is kicked and re-invited
            welcome_channel = -1,
            leave_channel = -1,
            joined_at = guild.me.joined_at,
            created_at = datetime.datetime.now(),
            updated_at = datetime.datetime.now(),
            is_dirty = False,
            is_deleted = False
        )
        guilds.append(model)
        users: List[models.User] = []
        for member in guild.members:
            user_model = DB_MANAGER.initialize_database_model(shared.Table.users,
                user_id = member.id,
                username = member.name,
                discriminator = member.discriminator,
                avatar_url = str(member.avatar.url) if member.avatar else "",
                is_bot = member.bot,
                currency = 0,
                created_at = datetime.datetime.now(),
                updated_at = datetime.datetime.now(),
                is_dirty = False,
                is_deleted = False
            )
            users.append(user_model)
        users_per_guild.append(users)
    
    for users in users_per_guild:
        DB_MANAGER.add_users(users)
    
    DB_MANAGER.add_guilds(guilds)

@bot.event
async def on_ready() -> None:
    helpers.custom_print(
        level = shared.LogLevel.INFO,
        function_name = "launch.on_ready",
        description = f"Bot connected as {bot.user} (ID: {bot.user.id})"
    )
    
    await moderation.setup(bot)
    #economy.setup(bot, config)
    await polls.setup(bot)
    #rankings.setup(bot)
    #utilities_commands.setup(bot, config)
    #web_scraping_commands.setup(bot, config)
    await basic.setup(bot)

    helpers.custom_print(
        level = shared.LogLevel.INFO,
        function_name = "launch.on_ready",
        description = "All cogs have been set up."
    )
    helpers.custom_print(
        level = shared.LogLevel.INFO,
        function_name = "launch.on_ready",
        description = "Starting command sync..."
    )
    try:
        #GUILD_ID = 1183463468020531343
        #synced_guild = await bot.tree.sync(guild = bot.get_guild(GUILD_ID))
        #print(f"Synced {len(synced_guild)} commands to guild {bot.get_guild(GUILD_ID).name}")
        synced_globally = await bot.tree.sync()
        helpers.custom_print(
            level = shared.LogLevel.INFO,
            function_name = "launch.on_ready",
            description = f"Synced {len(synced_globally)} commands globally."
        )
    except Exception as e:
        helpers.custom_print(
            level = shared.LogLevel.ERROR,
            function_name = "launch.on_ready",
            description = f"Failed to sync commands: {e}"
        )
    
    await setup_bot()

def launch() -> None:
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
        #config_string = json.dumps(config, indent = 4)
        helpers.custom_print(
            level = shared.LogLevel.INFO,
            function_name = "launch",
            description = f"Loaded config"
        )
    
    if not dotenv.load_dotenv(dotenv_path = dotenv.find_dotenv(filename = ".env")):
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "launch",
            description = "No .env file found or failed to load."
        )
        exit()

    DB_HOST = os.environ["DB_HOST"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DATABASE = os.environ["DATABASE"]
    DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

    # Debugging output
    helpers.custom_print(
        level = shared.LogLevel.DEBUG,
        function_name = "launch",
        description = f"""
        DB Host: {DB_HOST}
        DB User: {DB_USER}
        DB Password: {DB_PASSWORD}
        Database: {DATABASE}
        Token: {DISCORD_TOKEN}

        """
    )
    database_manager.setup(DB_HOST, DB_USER, DB_PASSWORD, DATABASE)
    bot.run(DISCORD_TOKEN, reconnect = True)

if __name__ == "__main__":
    launch()
