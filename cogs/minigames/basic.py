import discord
from discord import app_commands
from discord.ext import commands
from utils import shared


class Minigames(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def coin_flip(first_pick: shared.CoinFlip, second_pick: shared.CoinFlip):
        pass

    def roll_dice(from_number: int | None, to_number: int | None):
        pass

    def guess_the_number(from_number: int | None, to_number: int | None):
        pass

    def rock_paper_scissors(first_pick: shared.RPS, second_pick: shared.RPS):
        pass

    def word_scramble(language: str):
        pass

    def hangman():
        pass

    def typing_race():
        pass

    def lucky_seven():
        pass

    def event():
        pass

async def setup(bot: commands.Bot):
    await bot.add_cog(Minigames(bot))