from services import rankings
import discord
from discord.ext import commands
from utils import shared

class Rankings(commands.Cog):
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.users = []

    

def setup(bot: commands.Bot, config: dict):
    bot.add_cog()