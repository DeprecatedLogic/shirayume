import discord
from discord import app_commands
from discord.ext import commands
from random import randint, choice
from utils import shared, helpers


class Minigames(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name = "coinflip", description = "Flip a coin!")
    async def coin_flip(self, interaction: discord.Interaction):
        try:   
            embed = helpers.embed_generator(
                    title = "Coinflip",
                    description = f"{interaction.user.name} got {choice(list(shared.CoinFlip)).name.capitalize()}!",
                    color = (0, 191, 255)
                )
            await interaction.response.send_message(embed = embed)

        except Exception as e:
            embed = helpers.embed_generator(
                title = "Coinflip",
                description = "I am not getting paid enough for this...",
            )
            await interaction.response.send_message(embed = embed, ephemeral=True)


    @app_commands.command(name = "roll_dice", description = "Roll a custom sized dice!")
    async def roll_dice(self, interaction: discord.Interaction, sides: int = 6):
        try:   
            embed = helpers.embed_generator(
                    title = "Dice roll",
                    description = f"{interaction.user.name} rolled {randint(0, sides)} from a {sides} sided dice!",
                    color = (0, 191, 255)
                )
            await interaction.response.send_message(embed = embed)

        except Exception as e:
            embed = helpers.embed_generator(
                title = "Dice roll",
                description = "I am not getting paid enough for this...",
            )
            await interaction.response.send_message(embed = embed, ephemeral=True)


    @app_commands.command(name = "guess_the_number", description = "Guess the number!")
    async def guess_the_number(self, interaction: discord.Interaction, from_number: int | None, to_number: int | None):
        #IN PROGRESS
        try:   
            embed = helpers.embed_generator(
                    title = "Number guessing",
                    description = f"",
                    color = (0, 191, 255)
                )
            await interaction.response.send_message(embed = embed)

        except Exception as e:
            embed = helpers.embed_generator(
                title = "Number guessing",
                description = "I am not getting paid enough for this...",
            )
            await interaction.response.send_message(embed = embed, ephemeral=True)

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