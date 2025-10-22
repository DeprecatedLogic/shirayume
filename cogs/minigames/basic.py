import discord
from discord import app_commands
from discord.ext import commands
import asyncio
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
                description = "[ERROR] Instead of flipping a coin, how about i flip you instead?",
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
                description = "[ERROR] You don't have dices at home?",
            )
            await interaction.response.send_message(embed = embed, ephemeral=True)


    @app_commands.command(name = "guess_the_number", description = "Guess the number!")
    async def guess_the_number(self, interaction: discord.Interaction, from_number: int = 0, to_number: int = 100, attempts: int = 10):
        number_to_guess = randint(from_number, to_number)
        max_attempts = attempts
        
        def is_correct_player_and_format(m):
            if m.author != interaction.user or m.channel != interaction.channel:
                return False
                
            if m.content.startswith('!'):
                guess_str = m.content[1:].strip()
                return guess_str.isdigit() and from_number <= int(guess_str) <= to_number
                
            return False
        
        initial_embed = helpers.embed_generator(
                        title = "Number guessing",
                        description = f"Guess the secret number between {from_number} and {to_number}! You have {attempts} attempts!",
                        color = (0, 191, 255)
                    )
        
        await interaction.response.send_message(embed = initial_embed)

        game_message = await interaction.original_response()
        
        while max_attempts > 0:
            try:
                guess_message = await self.bot.wait_for(
                    'message',
                    check = is_correct_player_and_format,
                    timeout = 60.0
                )
                guess_number = int(guess_message.content[1:].strip()) 
                max_attempts -= 1

                if guess_number == number_to_guess:
                    win_embed = helpers.embed_generator(
                        title = "Number guessing",
                        description = f"🎉 Congrats {interaction.user.name} on guessing the secret number ({number_to_guess})!",
                        color = (0, 191, 255)
                    )
                    await interaction.followup.send(embed = win_embed)
                    return

                else:
                    if guess_number < number_to_guess:
                        description_text = f"The number to guess is **bigger** than {guess_number}! You have {max_attempts} attempts remaining!" 
                    else:
                        description_text = f"The number to guess is **smaller** than {guess_number}! You have {max_attempts} attempts remaining!" 

                    situation_embed = helpers.embed_generator(
                        title = f"Number guessing",
                        description = description_text,
                        color = (0, 191, 255)
                        )
                    
                    await game_message.edit(embed = situation_embed)
                    
            except asyncio.TimeoutError:
                embed = helpers.embed_generator(
                    title = "Number guessing",
                    description = f"😴 Game timed out! Do not leave me hanging {interaction.user.name}",
                )
                await interaction.followup.send(embed=embed)
                return
            
            except Exception as e:
                embed = helpers.embed_generator(
                    title = "Number guessing",
                    description = f"[ERROR] I am not getting paid enough for this... Error {e}",
                )
                await interaction.followup.send(embed = embed, ephemeral=True)

        if max_attempts <= 0:
            try:
                lose_embed = helpers.embed_generator(
                    title = "Number guessing",
                    description = f"❌ Game Over {interaction.user.name}! You ran out of attempts. The secret number was **{number_to_guess}**.",
                    color = (0, 191, 255)
                )
                await interaction.followup.send(embed = lose_embed)
                
            except Exception as e:
                embed = helpers.embed_generator(
                    title = "Number guessing",
                    description = f"[ERROR] I am not getting paid enough for this... Error: {e}",
                )
                await interaction.followup.send(embed = embed, ephemeral=True)


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