from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseGame(ABC):
    """Abstract base class for all Guild vs Guild mini-games."""
    
    def __init__(self, guild1_id: int, guild2_id: int):
        self.guild1_id = guild1_id
        self.guild2_id = guild2_id
        self.current_turn_guild_id: Optional[int] = guild1_id
        self.is_over: bool = False
        self.winner_guild_id: Optional[int] = None

    @abstractmethod
    def process_turn(self, guild_id: int, user_id: int, move_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processes a turn or input from a guild/user and updates game state."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Returns the current state payload for rendering."""
        pass