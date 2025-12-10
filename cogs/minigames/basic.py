import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from collections import defaultdict
from random import randint, choice
from utils import shared, helpers
from cogs.minigames.NumberGuessingLogic import NumberGame

class Minigames(commands.Cog):
    class GuessModal(discord.ui.Modal, title = "Enter your guess"):
        guess = discord.ui.TextInput(
            label = "Your guess",
            placeholder = "Type a number and submit",
            required = True,
            max_length = 10
        )

        def __init__(self, game: NumberGame, view: "Minigames.GuessView"):
            super().__init__()
            self.game = game
            self.view = view

        async def on_submit(self, interaction: discord.Interaction) -> None:
            await interaction.response.defer(ephemeral = True)

            try:
                guess_val = int(self.guess.value.strip())
            except ValueError:
                await interaction.followup.send("Please enter a valid integer.", ephemeral = True)
                return
            
            if not (self.game.from_number <= guess_val <= self.game.to_number):
                await interaction.followup.send(
                    f"Guess must be between {self.game.from_number} and {self.game.to_number}.",
                    ephemeral = True
                )
                return

            await self.view.process_guess_via_modal(interaction, guess_val)
    
    class GuessView(discord.ui.View):
        def __init__(self, game: "NumberGame", cog: "Minigames", *, timeout: float = 60.0):
            super().__init__(timeout = timeout)
            self.game = game
            self.cog = cog
            self.message: discord.Message | None = None

        @discord.ui.button(label = "Guess", style = discord.ButtonStyle.primary)
        async def open_modal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.game.user_id:
                return await interaction.response.send_message("This is not your game.", ephemeral = True)

            modal = Minigames.GuessModal(self.game, self)
            await interaction.response.send_modal(modal)

        @discord.ui.button(label = "End game", style = discord.ButtonStyle.danger)
        async def end_game_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.game.user_id:
                return await interaction.response.send_message("This is not your game.", ephemeral = True)

            await self._end_game(interaction, ended_by_user = True)

        async def process_guess_via_modal(self, interaction: discord.Interaction, guess_val: int):
            result = self.game.make_guess(guess_val)

            if result == "win":
                embed = helpers.embed_generator(
                    title = "Guess the number",
                    description = f"🎉 Congrats {interaction.user.mention}! You guessed the number: **{self.game.answer}**.\n\n{self.game.summary()}",
                    color = (0, 191, 255)
                )

                if self.message:
                    await self.message.edit(embed = embed, view = None)
                await interaction.followup.send("You won! 🎉", ephemeral = True)
                self.cog.remove_game("guess", self.game.user_id)
                return

            if result == "bigger":
                hint = "⬆️ The number is bigger than your guess."
            else:
                hint = "⬇️ The number is smaller than your guess."

            if self.game.out_of_attempts():
                embed = helpers.embed_generator(
                    title = "Guess the number",
                    description = f"❌ Game over, no attempts left. The number was **{self.game.answer}**.\n\n{self.game.summary()}",
                    color = (0, 191, 255)
                )
                if self.message:
                    await self.message.edit(embed = embed, view = None)
                await interaction.followup.send("Out of attempts — game has concluded.", ephemeral = True)
                self.cog.remove_game("guess", self.game.user_id)
                return

            embed = helpers.embed_generator(
                title = "Guess the number",
                description = f"{hint}\n\n{self.game.summary()}",
                color = (0, 191, 255)
            )
            if self.message:
                await self.message.edit(embed = embed, view = self)

        async def _end_game(self, interaction: discord.Interaction, ended_by_user: bool = False):
            embed = helpers.embed_generator(
                title = "Guess the number",
                description = f"⛔ Game forcefully ended by player." if ended_by_user else "Game concluded due to timeout.",
                color = (0, 191, 255)
            )
            if self.message:
                await self.message.edit(embed = embed, view = None)
            if ended_by_user:
                await interaction.response.send_message("Number guessing game ended.", ephemeral = True)
            self.cog.remove_game("guess", self.game.user_id)

        async def on_timeout(self):
            embed = helpers.embed_generator(
                title = "Guess the number",
                description = f"⌛ {self.game.user_id}, game timed out.",
                color = (0, 191, 255)
            )
            try:
                if self.message:
                    await self.message.edit(embed = embed, view = None)
            except Exception:
                pass
            self.cog.remove_game("guess", self.game.user_id)

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_games: dict[str, dict[int, NumberGame]] = defaultdict(dict)

    def remove_game(self, game_name: str, user_id: int):
        if user_id in self.active_games.get(game_name, {}):
            try:
                del self.active_games[game_name][user_id]
            except KeyError:
                pass


    @app_commands.command(name = "yumecoinflip", description = "Flip a coin!")
    async def coin_flip(self, interaction: discord.Interaction):
        try:   
            embed = helpers.embed_generator(
                    title = "Coinflip",
                    description = f"{interaction.user.mention} got {choice(list(shared.CoinFlip)).name.capitalize()}!",
                    color = (0, 191, 255)
                )
            await interaction.response.send_message(embed = embed)

        except Exception as e:
            embed = helpers.embed_generator(
                title = "Coinflip",
                description = "[ERROR] Instead of flipping a coin, how about i flip you instead?",
            )
            await interaction.response.send_message(embed = embed, ephemeral=True)


    @app_commands.command(name = "yumerolldice", description = "Roll a custom sized dice!")
    async def roll_dice(self, interaction: discord.Interaction, sides: int = 6):
        try:   
            embed = helpers.embed_generator(
                    title = "Dice roll",
                    description = f"{interaction.user.mention} rolled {randint(0, sides)} from a {sides} sided dice!",
                    color = (0, 191, 255)
                )
            await interaction.response.send_message(embed = embed)

        except Exception as e:
            embed = helpers.embed_generator(
                title = "Dice roll",
                description = "[ERROR] You don't have dices at home?",
            )
            await interaction.response.send_message(embed = embed, ephemeral=True)


    @app_commands.command(name = "yumeguessnumber", description = "Guess the number!")
    async def guess_the_number(self, interaction: discord.Interaction, from_number: int = 0, to_number: int = 100, attempts: int = 10):
        if from_number >= to_number:
            return await interaction.response.send_message("`from_number` must be less than `to_number`.", ephemeral = True)
        if attempts < 1:
            return await interaction.response.send_message("Attempts must be >= 1.", ephemeral = True)

        user_id = interaction.user.id

        if user_id in self.active_games["guess"]:
            return await interaction.response.send_message("You already have a Guess game running. Finish or end it first.", ephemeral = True)
        
        game = NumberGame(user_id, from_number, to_number, attempts)
        view = Minigames.GuessView(game, self, timeout = 60.0)

        self.active_games["guess"][user_id] = game

        initial_embed = helpers.embed_generator(
            title = "Guess The Number",
            description = f"Guess a number between **{from_number}** and **{to_number}**.\nAttempts: **{attempts}**\n\nClick **Guess** to open the input modal.",
            color = (0, 191, 255)
        )

        modal = Minigames.GuessModal(game, view)
        await interaction.response.send_modal(modal)

        sent = await interaction.followup.send(embed = initial_embed, view = view, ephemeral = False)
        view.message = sent


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