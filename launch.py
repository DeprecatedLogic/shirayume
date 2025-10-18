import os
import dotenv
from cogs import moderation, economy, polls, rankings, utilities_commands, web_scraping_commands
from database import database_manager
import discord
from discord.ext import commands
import json
import asyncio

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
    if not dotenv.load_dotenv(dotenv_path = dotenv.find_dotenv(filename = ".env")):
        print("[ERROR] No environment variables set...")
        exit()

    DB_HOST = os.environ["DB_HOST"]
    DB_USER = os.environ["DB_USER"]
    DB_PASSWORD = os.environ["DB_PASSWORD"]
    DATABASE = os.environ["DATABASE"]
    DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]

    # Debugging output
    print(
        f"DB Host: {DB_HOST}",
        f"DB User: {DB_USER}",
        f"DB Password: {DB_PASSWORD}",
        f"Database: {DATABASE}",
        f"Token: {DISCORD_TOKEN}",
        sep="\n"
    )

    #asyncio.run(database_manager.setup())

    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    asyncio.run(moderation.setup(bot))
    #asyncio.run(economy.setup(bot, config))
    #asyncio.run(polls.setup(bot, config))
    #asyncio.run(rankings.setup(bot, config))
    #asyncio.run(utilities_commands.setup(bot, config))
    #asyncio.run(web_scraping_commands.setup(bot, config)    )

    bot.run(DISCORD_TOKEN, reconnect = True)

if __name__ == "__main__":
    launch()
