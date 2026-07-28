from services.matchmaking.games.base import BaseGame
from typing import Dict, Any

class SudokuGame(BaseGame):
    def __init__(self, guild1_id: int, guild2_id: int):
        super().__init__(guild1_id, guild2_id)
        self.board = [[0] * 9 for _ in range(9)]
        self.scores = {guild1_id: 0, guild2_id: 0}

    def process_turn(self, guild_id: int, user_id: int, move_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_over:
            return {"success": False, "reason": "Game is already over."}

        row = move_data.get("row")
        col = move_data.get("col")
        val = move_data.get("val")

        if row is None or col is None or val is None:
            return {"success": False, "reason": "Missing placement coordinates."}

        self.board[row][col] = val
        self.scores[guild_id] += 1

        if all(all(cell != 0 for cell in r) for r in self.board):
            self.is_over = True
            self.winner_guild_id = max(self.scores, key=self.scores.get)

        return {
            "success": True,
            "placed": (row, col, val),
            "scores": self.scores,
            "is_over": self.is_over,
            "winner_guild_id": self.winner_guild_id
        }

    def get_state(self) -> Dict[str, Any]:
        return {
            "board": self.board,
            "scores": self.scores,
            "is_over": self.is_over,
            "winner_guild_id": self.winner_guild_id
        }