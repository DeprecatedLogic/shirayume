from services import rankings
import discord
from discord.ext import commands
from utils import shared

class Rankings(commands.Cog):
    
    def __init__(self):
        self.users = []

async def setup():
    await shared.SHIRAYUME.add_cog(Rankings(), override=True)