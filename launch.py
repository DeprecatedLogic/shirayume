import os
import dotenv
from database import database_manager
from cogs import moderation, economy, polls, rankings, utilities_commands, web_scraping_commands
import discord
from discord.ext import commands
import json
import asyncio
from utils import shared, helpers

bot = commands.Bot("EXE>", intents = discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("Syncing commands...")
    try:
        GUILD_ID = 1183463468020531343
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands to guild {GUILD_ID}")
        print(f"Synced {len(synced)} commands globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

def launch():
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    
    if not dotenv.load_dotenv(dotenv_path = dotenv.find_dotenv(filename = ".env")):
        print("[ERROR] No environment variables set...")
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
    asyncio.run(moderation.setup(bot))
    #asyncio.run(economy.setup(bot, config))
    #asyncio.run(polls.setup(bot, config))
    #asyncio.run(rankings.setup(bot, config))
    #asyncio.run(utilities_commands.setup(bot, config))
    #asyncio.run(web_scraping_commands.setup(bot, config)    )

    bot.run(DISCORD_TOKEN, reconnect = True)

if __name__ == "__main__":
    launch()
