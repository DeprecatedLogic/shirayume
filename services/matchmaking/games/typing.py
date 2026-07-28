from services.matchmaking.games.base import BaseGame
import time
from typing import Dict, Any

class TypingGame(BaseGame):
    def __init__(self, guild1_id: int, guild2_id: int, prompt: str = "The quick brown fox jumps over the lazy dog."):
        super().__init__(guild1_id, guild2_id)
        self.prompt = prompt
        self.start_time = time.time()
        self.completions: Dict[int, float] = {}

    def process_turn(self, guild_id: int, user_id: int, move_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_over:
            return {"success": False, "reason": "Game is already over."}

        submission = move_data.get("text", "")
        if submission.strip() == self.prompt:
            elapsed = round(time.time() - self.start_time, 2)
            self.completions[guild_id] = elapsed
            self.is_over = True
            self.winner_guild_id = guild_id
            
            words = len(self.prompt.split())
            wpm = round((words / (elapsed / 60)), 1) if elapsed > 0 else 0

            return {
                "success": True,
                "elapsed_seconds": elapsed,
                "wpm": wpm,
                "is_over": True,
                "winner_guild_id": guild_id
            }

        return {"success": False, "reason": "Text did not match prompt."}

    def get_state(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "start_time": self.start_time,
            "is_over": self.is_over,
            "winner_guild_id": self.winner_guild_id
        }