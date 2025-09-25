import os
import dotenv
from cogs import moderation, economy, polls, rankings, utilities_commands, web_scraping_commands
from database import database_manager
import discord
from discord.ext import commands
import json

def launch():
    if not dotenv.load_dotenv(dotenv_path = dotenv.find_dotenv(filename = ".env")):
        print("[ERROR] No environment variables set...")
        exit()

    DB_HOST = {os.environ["DB_HOST"]},
    DB_USER = {os.environ["DB_USER"]},
    DB_PASSWORD = {os.environ["DB_PASSWORD"]},
    DATABASE = {os.environ["DATABASE"]},
    DISCORD_BOT_TOKEN = {os.environ["DISCORD_BOT_TOKEN"]}

    # Debugging output
    print(
        f"DB Host: {DB_HOST}",
        f"DB User: {DB_USER}",
        f"DB Password: {DB_PASSWORD}",
        f"Database: {DATABASE}",
        f"Token: {DISCORD_BOT_TOKEN}"
    )

    bot = commands.Bot("EXE>", intents = discord.Intents.all())

    database_manager.setup()

    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    #moderation.setup(bot, config)
    #economy.setup(bot, config)
    #polls.setup(bot, config)
    #rankings.setup(bot, config)
    #utilities_commands.setup(bot, config)
    #web_scraping_commands.setup(bot, config)    

    bot.run(DISCORD_BOT_TOKEN, reconnect = True)

if __name__ == "__main__":
    launch()
