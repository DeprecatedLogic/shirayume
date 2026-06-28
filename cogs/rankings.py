from services import rankings
import discord
from discord.ext import commands
from utils import shared

class Rankings(commands.Cog):
    
    def __init__(self):
        self.users = []

def setup(config: dict):
    bot.add_cog()