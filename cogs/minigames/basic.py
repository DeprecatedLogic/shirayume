# minigames.py
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from collections import defaultdict
from random import randint, choice
from utils import shared, helpers
from services.minigames.number_guessing import NumberGame

class Minigames(commands.Cog):
    """Cog responsible for managing interactive minigames like number guessing, coin flips, and dice rolls."""

    class GuessModal(discord.ui.Modal, title="Enter your guess"):
        """Modal interface for users to submit their numeric guess."""

        guess = discord.ui.TextInput(
            label="Your guess",
            placeholder="Type a number and submit",
            required=True,
            max_length=10
        )

        def __init__(self, game: NumberGame, view: "Minigames.GuessView") -> None:
            """Initializes the guess modal with the current game state and parent view.

            Args:
                game (NumberGame): The active number guessing game instance.
                view (Minigames.GuessView): The parent view coordinating the interactive elements.
            """
            super().__init__()
            self.game = game
            self.view = view

        async def on_submit(self, interaction: discord.Interaction) -> None:
            """Validates the user's guess and processes it through the game logic.

            Args:
                interaction (discord.Interaction): The interaction payload from the modal submission.
            """
            await interaction.response.defer(ephemeral=True)

            try:
                guess_val = int(self.guess.value.strip())
            except ValueError:
                helpers.custom_print(
                    level=shared.LogLevel.WARNING,
                    description=f"User {interaction.user.id} submitted an invalid integer: {self.guess.value}"
                )
                await interaction.followup.send("Please enter a valid integer.", ephemeral=True)
                return
            
            if not (self.game.from_number <= guess_val <= self.game.to_number):
                await interaction.followup.send(
                    f"Guess must be between {self.game.from_number} and {self.game.to_number}.",
                    ephemeral=True
                )
                return

            await self.view.process_guess_via_modal(interaction, guess_val)
    
    class GuessView(discord.ui.View):
        """Interactive view containing buttons for guessing and ending the game."""
        def __init__(self, game: "NumberGame", cog: "Minigames", *, timeout: float = 60.0) -> None:
            """
            Initializes the guessing game view.

            Args:
                game (NumberGame): The active number guessing game instance.
                cog (Minigames): The parent cog instance managing active games.
                timeout (float): The duration in seconds before the view expires.
            """
            super().__init__(timeout=timeout)
            self.game = game
            self.cog = cog
            self.message: discord.Message | None = None

        @discord.ui.button(label="Guess", style=discord.ButtonStyle.primary)
        async def open_modal_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """
            Opens the guessing modal when the Guess button is clicked.

            Args:
                interaction (discord.Interaction): The button interaction payload.
                button (discord.ui.Button): The button component pressed.
            """
            if interaction.user.id != self.game.user_id:
                return await interaction.response.send_message("This is not your game.", ephemeral=True)

            modal = Minigames.GuessModal(self.game, self)
            await interaction.response.send_modal(modal)

        @discord.ui.button(label="End game", style=discord.ButtonStyle.danger)
        async def end_game_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
            """
            Forces the game to end immediately when the End Game button is clicked.

            Args:
                interaction (discord.Interaction): The button interaction payload.
                button (discord.ui.Button): The button component pressed.
            """
            if interaction.user.id != self.game.user_id:
                return await interaction.response.send_message("This is not your game.", ephemeral=True)

            await self._end_game(interaction, ended_by_user=True)

        async def process_guess_via_modal(self, interaction: discord.Interaction, guess_val: int) -> None:
            """
            Evaluates the guess, updates the embed, and handles win/loss conditions.

            Args:
                interaction (discord.Interaction): The modal submission interaction payload.
                guess_val (int): The validated integer guessed by the user.
            """
            result = self.game.make_guess(guess_val)

            if result == "win":
                helpers.custom_print(
                    level=shared.LogLevel.INFO,
                    description=f"User {interaction.user.id} won the number guessing game."
                )
                embed = helpers.embed_generator(
                    title="Guess the number",
                    description=f"Congrats {interaction.user.mention}! You guessed the number: **{self.game.answer}**.\n\n{self.game.summary()}",
                )

                if self.message:
                    await self.message.edit(embed=embed, view=None)
                await interaction.followup.send("You won! 🎉", ephemeral=True)
                self.cog.remove_game("guess", self.game.user_id)
                return

            if result == "bigger":
                hint = "⬆️ The number is **bigger** than your guess."
            else:
                hint = "⬇️ The number is **smaller** than your guess."

            if self.game.out_of_attempts():
                helpers.custom_print(
                    level=shared.LogLevel.INFO,
                    description=f"User {interaction.user.id} ran out of attempts in number guessing game."
                )
                embed = helpers.embed_generator(
                    title="Guess the number",
                    description=f"**Game over**, no attempts left. The number was **{self.game.answer}**.\n\n{self.game.summary()}",
                )
                if self.message:
                    await self.message.edit(embed=embed, view=None)
                await interaction.followup.send("Out of attempts — game has concluded.", ephemeral=True)
                self.cog.remove_game("guess", self.game.user_id)
                return

            embed = helpers.embed_generator(
                title="Guess the number",
                description=f"{hint}\n\n{self.game.summary()}",
            )
            if self.message:
                await self.message.edit(embed=embed, view=self)

        async def _end_game(self, interaction: discord.Interaction, ended_by_user: bool = False) -> None:
            """
            Helper function to end the game and remove it from active tracking.

            Args:
                interaction (discord.Interaction): The user interaction triggering the game end.
                ended_by_user (bool): Indicates if the termination was user-initiated.
            """
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Guessing game for {interaction.user.id} ended (by user: {ended_by_user})."
            )
            embed = helpers.embed_generator(
                title="Guess the number",
                description="Game forcefully ended by player." if ended_by_user else "Game concluded due to timeout.",
            )
            if self.message:
                await self.message.edit(embed=embed, view=None)
            if ended_by_user:
                await interaction.response.send_message("Number guessing game ended.", ephemeral=True)
            self.cog.remove_game("guess", self.game.user_id)

        async def on_timeout(self) -> None:
            """Automatically ends the game when the view times out."""
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Guessing game for {self.game.user_id} timed out."
            )
            embed = helpers.embed_generator(
                title="Guess the number",
                description=f"⌛ {shared.SHIRAYUME.get_user(self.game.user_id).mention}, game timed out.",
            )
            try:
                if self.message:
                    await self.message.edit(embed=embed, view=None)
            except Exception as e:
                helpers.custom_print(
                    level=shared.LogLevel.ERROR,
                    description=f"Error editing message on timeout: {e}"
                )
            self.cog.remove_game("guess", self.game.user_id)

    def __init__(self) -> None:
        """Initializes the Minigames cog and the active games dictionary."""
        self.active_games: dict[str, dict[int, NumberGame]] = defaultdict(dict)

    def remove_game(self, game_name: str, user_id: int) -> None:
        """Removes a user's active game from the tracking dictionary.

        Args:
            game_name (str): The identifier string of the minigame category.
            user_id (int): The unique Discord ID of the user.
        """
        if user_id in self.active_games.get(game_name, {}):
            try:
                del self.active_games[game_name][user_id]
                helpers.custom_print(
                    level=shared.LogLevel.DEBUG,
                    description=f"Removed active {game_name} game for user {user_id}."
                )
            except KeyError:
                pass

    @app_commands.command(name="coinflip", description="Flip a coin!")
    async def coin_flip(self, interaction: discord.Interaction) -> None:
        """Simulates flipping a coin and sends the result.

        Args:
            interaction (discord.Interaction): The slash command interaction payload.
        """
        try:   
            result = choice(list(shared.CoinFlip)).name.capitalize()
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"User {interaction.user.id} flipped a coin and got {result}."
            )
            embed = helpers.embed_generator(
                title="Coinflip",
                description=f"{interaction.user.mention} got {result}!",
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description=f"Coinflip command error: {e}"
            )
            embed = helpers.embed_generator(
                title="Coinflip",
                description="[ERROR] Instead of flipping a coin, how about i flip you instead?",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="rolldice", description="Roll a custom sized dice!")
    async def roll_dice(self, interaction: discord.Interaction, sides: int = 6) -> None:
        """Rolls a dice with a custom number of sides.

        Args:
            interaction (discord.Interaction): The slash command interaction payload.
            sides (int): The total number of faces on the simulated die.
        """
        try:
            result = randint(1, sides) # Assuming 1 to sides makes more sense for a dice
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"User {interaction.user.id} rolled a {sides}-sided dice and got {result}."
            )
            embed = helpers.embed_generator(
                title="Dice roll",
                description=f"{interaction.user.mention} rolled {result} from a {sides} sided dice!",
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description=f"Dice roll command error: {e}"
            )
            embed = helpers.embed_generator(
                title="Dice roll",
                description="[ERROR] You don't have dices at home?",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="guessnumber", description="Guess the number!")
    async def guess_the_number(self, interaction: discord.Interaction, from_number: int = 0, to_number: int = 100, attempts: int = 10) -> None:
        """Starts a new number guessing game for the user.

        Args:
            interaction (discord.Interaction): The slash command interaction payload.
            from_number (int): The lower bound of the guessing range.
            to_number (int): The upper bound of the guessing range.
            attempts (int): The maximum number of allowed guesses.
        """
        if from_number >= to_number:
            return await interaction.response.send_message("`from_number` must be less than `to_number`.", ephemeral=True)
        if attempts < 1:
            return await interaction.response.send_message("Attempts must be >= 1.", ephemeral=True)

        user_id = interaction.user.id

        if user_id in self.active_games["guess"]:
            return await interaction.response.send_message("You already have a Guess game running. Finish or end it first.", ephemeral=True)
        
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Starting number guessing game for {user_id}."
        )
        
        game = NumberGame(user_id, from_number, to_number, attempts)
        view = Minigames.GuessView(game, self, timeout=60.0)

        self.active_games["guess"][user_id] = game

        initial_embed = helpers.embed_generator(
            title="Guess The Number",
            description=f"Guess a number between **{from_number}** and **{to_number}**.\nAttempts: **{attempts}**\n\nClick **Guess** to open the input modal.",
        )

        modal = Minigames.GuessModal(game, view)
        await interaction.response.send_modal(modal)

        sent = await interaction.followup.send(embed=initial_embed, view=view, ephemeral=False)
        view.message = sent

    def rock_paper_scissors(self, first_pick: shared.RPS, second_pick: shared.RPS) -> None:
        """Placeholder for Rock, Paper, Scissors game logic.

        Args:
            first_pick (shared.RPS): The choice made by the first player.
            second_pick (shared.RPS): The choice made by the second player.
        """
        pass

    def word_scramble(self, language: str) -> None:
        """Placeholder for Word Scramble game logic.

        Args:
            language (str): The identifier string of the selected language.
        """
        pass

    def hangman(self) -> None:
        """Placeholder for Hangman game logic."""
        pass

    def typing_race(self) -> None:
        """Placeholder for Typing Race game logic."""
        pass

    def lucky_seven(self) -> None:
        """Placeholder for Lucky Seven game logic."""
        pass

    def event(self) -> None:
        """Placeholder for general event logic."""
        pass

async def setup() -> None:
    """
    Adds the Minigames cog to the bot instance.
    """
    if shared.GLOBAL_CONFIG["features"]["minigames"].get("is_enabled", False):
        await shared.SHIRAYUME.add_cog(Minigames(), override=True)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description="Basic minigames setup completed successfully"
        )
    else:
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description="Minigames feature is disabled, setup skipped."
        )