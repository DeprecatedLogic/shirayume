from enum import Enum, auto
from dataclasses import dataclass
from datetime import datetime

class GameType(Enum):
    CHESS = auto()
    HANGMAN = auto()
    SUDOKU = auto()
    TYPING = auto()

class MatchStatus(Enum):
    WAITING = auto()
    IN_PROGRESS = auto()
    FINISHED = auto()
    CANCELLED = auto()

@dataclass
class QueueEntry:
    entry_id: str
    guild_id: int
    channel_id: int
    user_ids: list[int]
    game_type: GameType
    joined_at: datetime
    credits_bet: int = 0
