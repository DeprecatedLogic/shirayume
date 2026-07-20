from random import randint
from utils import shared, helpers

class NumberGame:
    """Handles the state and logic for a number guessing game session."""

    def __init__(self, user_id: int, from_number: int, to_number: int, attempts: int) -> None:
        """
        Initializes a new NumberGame instance with specific boundaries and allowed attempts.

        Args:
            user_id (int): The unique Discord ID of the user playing the game.
            from_number (int): The lower bound of the guessing range.
            to_number (int): The upper bound of the guessing range.
            attempts (int): The maximum number of allowed guesses.
        """
        self.user_id = user_id
        self.from_number = from_number
        self.to_number = to_number
        self.attempts_left = attempts
        self.answer = randint(from_number, to_number)
        self.guesses: list[int] = []
        
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"NumberGame initialized for user {user_id} ({from_number}-{to_number}, {attempts} attempts)"
        )

    def make_guess(self, value: int) -> str:
        """
        Processes a numeric guess and returns the relational outcome ('win', 'bigger', or 'smaller').

        Args:
            value (int): The numeric guess provided by the user.

        Returns:
            str: 'win' if the guess is correct, 'bigger' if the answer is larger, or 'smaller' if the answer is smaller.
        """
        self.guesses.append(value)
        self.attempts_left -= 1
        
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"User {self.user_id} guessed {value}. Attempts left: {self.attempts_left}"
        )
        
        if value == self.answer:
            return "win"
        if value < self.answer:
            return "bigger"
        return "smaller"

    def out_of_attempts(self) -> bool:
        """
        Checks if the user has exhausted all their allowed attempts.

        Returns:
            bool: True if zero or fewer attempts remain, otherwise False.
        """
        return self.attempts_left <= 0

    def summary(self) -> str:
        """
        Generates a summary string containing remaining attempts and the last 10 guesses.

        Returns:
            str: A formatted string detailing the game state.
        """
        g = ", ".join(str(x) for x in self.guesses[-10:]) if self.guesses else "—"
        return f"Attempts left: {self.attempts_left}\nRecent guesses: {g}"