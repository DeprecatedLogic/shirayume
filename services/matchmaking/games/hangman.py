from services.matchmaking.games.base import BaseGame
from typing import Dict, Any

class HangmanGame(BaseGame):
    def __init__(self, guild1_id: int, guild2_id: int, word: str = "DISCORD"):
        super().__init__(guild1_id, guild2_id)
        self.word = word.upper()
        self.guessed_letters = set()
        self.max_attempts = 6
        self.wrong_attempts = 0

    def process_turn(self, guild_id: int, user_id: int, move_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_over:
            return {"success": False, "reason": "Game is already over."}
        if self.current_turn_guild_id != guild_id:
            return {"success": False, "reason": "Not your guild's turn."}

        letter = str(move_data.get("letter", "")).upper()
        if not letter or len(letter) != 1 or not letter.isalpha():
            return {"success": False, "reason": "Invalid character."}

        if letter in self.guessed_letters:
            return {"success": False, "reason": "Letter already guessed."}

        self.guessed_letters.add(letter)

        if letter not in self.word:
            self.wrong_attempts += 1
            if self.wrong_attempts >= self.max_attempts:
                self.is_over = True
                self.winner_guild_id = self.guild2_id if guild_id == self.guild1_id else self.guild1_id
        else:
            if all(c in self.guessed_letters for c in self.word):
                self.is_over = True
                self.winner_guild_id = guild_id

        if not self.is_over:
            self.current_turn_guild_id = self.guild2_id if guild_id == self.guild1_id else self.guild1_id

        return {
            "success": True,
            "guessed_letter": letter,
            "current_display": "".join([c if c in self.guessed_letters else "_" for c in self.word]),
            "wrong_attempts": self.wrong_attempts,
            "is_over": self.is_over,
            "winner_guild_id": self.winner_guild_id,
            "next_turn_guild_id": self.current_turn_guild_id
        }

    def get_state(self) -> Dict[str, Any]:
        return {
            "display": "".join([c if c in self.guessed_letters else "_" for c in self.word]),
            "guessed_letters": list(self.guessed_letters),
            "wrong_attempts": self.wrong_attempts,
            "max_attempts": self.max_attempts,
            "is_over": self.is_over,
            "winner_guild_id": self.winner_guild_id
        }