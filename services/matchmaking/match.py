from datetime import datetime
from typing import Dict, Any, Optional, Type, List
from services.matchmaking.shared import GameType, MatchStatus
from services.matchmaking.games.base import BaseGame
from services.matchmaking.games.chess import ChessGame
from services.matchmaking.games.hangman import HangmanGame
from services.matchmaking.games.sudoku import SudokuGame
from services.matchmaking.games.typing import TypingGame
from database import database_manager
from utils import helpers, shared

GAME_REGISTRY: Dict[GameType, Type[BaseGame]] = {
    GameType.CHESS: ChessGame,
    GameType.HANGMAN: HangmanGame,
    GameType.SUDOKU: SudokuGame,
    GameType.TYPING: TypingGame,
}

class Match:
    """
    Represents an active Guild vs Guild game match with multiple possible users per guild.
    """

    def __init__(
        self,
        guild1_id: int,
        guild1_channel_id: int,
        guild1_users: List[int],
        guild2_id: int,
        guild2_channel_id: int,
        guild2_users: List[int],
        game_type: GameType,
        credits_bet: int = 0
    ):
        self.match_id: int = database_manager.DB_MANAGER.get_next_id()
        self.guild1_id: int = guild1_id
        self.guild1_channel_id: int = guild1_channel_id
        self.guild1_users: List[int] = guild1_users
        self.guild2_id: int = guild2_id
        self.guild2_channel_id: int = guild2_channel_id
        self.guild2_users: List[int] = guild2_users
        self.game_type: GameType = game_type
        self.credits_bet: int = credits_bet
        self.status: MatchStatus = MatchStatus.IN_PROGRESS
        self.started_at: datetime = datetime.now()
        self.ended_at: Optional[datetime] = None
        self.winner_guild_id: Optional[int] = None

        game_cls = GAME_REGISTRY.get(game_type)
        if not game_cls:
            raise ValueError(f"No game logic registered for game type: {game_type}")

        self.game: BaseGame = game_cls(guild1_id, guild2_id)

    def is_user_in_match(self, user_id: int) -> bool:
        """Checks if a user is part of this active match."""
        return user_id in self.guild1_users or user_id in self.guild2_users

    def make_move(self, guild_id: int, user_id: int, move_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a move within the match and updates game status."""
        if self.status != MatchStatus.IN_PROGRESS:
            return {"success": False, "reason": "Match is not active."}

        if not self.is_user_in_match(user_id):
            return {"success": False, "reason": "You are not a participant in this match."}

        if guild_id not in (self.guild1_id, self.guild2_id):
            return {"success": False, "reason": "Guild is not a participant in this match."}

        result = self.game.process_turn(guild_id, user_id, move_data)

        if result.get("is_over"):
            self.finish_match(winner_guild_id=result.get("winner_guild_id"))

        return result

    def forfeit(self, forfeiting_guild_id: int) -> Dict[str, Any]:
        """Handles match forfeit."""
        if self.status != MatchStatus.IN_PROGRESS:
            return {"success": False, "reason": "Match is not active."}

        if forfeiting_guild_id not in (self.guild1_id, self.guild2_id):
            return {"success": False, "reason": "Guild is not in this match."}

        winner = self.guild2_id if forfeiting_guild_id == self.guild1_id else self.guild1_id
        self.finish_match(winner_guild_id=winner)

        return {"success": True, "winner_guild_id": winner, "forfeited_guild_id": forfeiting_guild_id}

    def finish_match(self, winner_guild_id: Optional[int]) -> None:
        """Finalizes state and triggers database log."""
        self.status = MatchStatus.FINISHED
        self.ended_at = datetime.now()
        self.winner_guild_id = winner_guild_id

        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Match {self.match_id} ({self.game_type.name}) finished. Winner Guild: {winner_guild_id}"
        )

        record = database_manager.DB_MANAGER.initialize_database_model(
            shared.Table.match_results,
            match_id=self.match_id,
            guild1_id=self.guild1_id,
            guild1_users=self.guild1_users,
            guild2_id=self.guild2_id,
            guild2_users=self.guild2_users,
            game_type=self.game_type.name,
            winner_guild_id=self.winner_guild_id,
            started_at=self.started_at,
            ended_at=self.ended_at
        )
        database_manager.DB_MANAGER.add_match_results(record)
