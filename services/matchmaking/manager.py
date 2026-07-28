from typing import Dict, Optional, Tuple, Any, List
from services.matchmaking.shared import GameType
from services.matchmaking.queue import MatchmakingQueue
from services.matchmaking.match import Match
from utils import helpers, shared

class MatchmakingManager:
    """
    Main entry point managing queues and active matches, tracking limits per user/guild.
    """
    def __init__(self):
        self.queue = MatchmakingQueue()
        self.active_matches: Dict[str, Match] = {}
        self.user_active_match: Dict[int, str] = {}

    def is_guild_busy(self, guild_id: int) -> bool:
        """Checks if a guild already has an active queue entry or in-progress match."""
        if self.queue.is_guild_queued(guild_id):
            return True
        for match in self.active_matches.values():
            if guild_id in (match.guild1_id, match.guild2_id):
                return True
        return False

    def join_queue(
        self,
        guild_id: int,
        channel_id: int,
        user_ids: List[int],
        game_type: GameType,
        credits_bet: int = 0
    ) -> Tuple[bool, str, Optional[Match]]:
        """
        Enqueues a team or matches them immediately with a waiting team from another guild.
        """
        if self.is_guild_busy(guild_id):
            return False, "Your guild already has an active queue or match in progress.", None

        for user_id in user_ids:
            if user_id in self.user_active_match:
                return False, f"User <@{user_id}> is already in an active match.", None

        success, msg, match_pair = self.queue.add_to_queue(guild_id, channel_id, user_ids, game_type, credits_bet)
        if not success:
            return False, msg, None

        if match_pair:
            entry1, entry2 = match_pair
            match = Match(
                guild1_id=entry1.guild_id,
                guild1_channel_id=entry1.channel_id,
                guild1_users=entry1.user_ids,
                guild2_id=entry2.guild_id,
                guild2_channel_id=entry2.channel_id,
                guild2_users=entry2.user_ids,
                game_type=game_type,
                credits_bet=credits_bet
            )
            self.active_matches[match.match_id] = match
            
            for uid in entry1.user_ids + entry2.user_ids:
                self.user_active_match[uid] = match.match_id

            opponent_id = entry1.guild_id if entry2.guild_id == guild_id else entry2.guild_id
            return True, f"Match found against Guild {opponent_id}!", match

        return True, f"Queued for {game_type.name}. Searching for opponent...", None

    def leave_queue(self, user_id: int) -> Tuple[bool, str]:
        """Removes a team's entry based on one participating user."""
        removed = self.queue.remove_from_queue(user_id)
        if removed:
            return True, "Left the matchmaking queue."
        return False, "You are not currently queued."

    def get_user_match(self, user_id: int) -> Optional[Match]:
        """O(1) active match lookup by user_id."""
        match_id = self.user_active_match.get(user_id)
        if match_id:
            return self.active_matches.get(match_id)
        return None

    def process_move(self, guild_id: int, user_id: int, move_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Executes a move in the active match and cleans up if game ends."""
        match = self.get_user_match(user_id)
        if not match:
            return False, {"reason": "You are not currently in an active match."}

        result = match.make_move(guild_id, user_id, move_data)

        if match.status == match.status.FINISHED:
            self._cleanup_match(match)

        return True, result

    def forfeit_match(self, guild_id: int, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        """Forfeits an active match via an authorized user."""
        match = self.get_user_match(user_id)
        if not match:
            return False, {"reason": "You are not in an active match."}

        result = match.forfeit(guild_id)
        self._cleanup_match(match)

        return True, result

    def _cleanup_match(self, match: Match) -> None:
        """O(1) match removal from active state across all participants."""
        for uid in match.guild1_users + match.guild2_users:
            self.user_active_match.pop(uid, None)
            
        self.active_matches.pop(match.match_id, None)
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Cleaned up active match {match.match_id} for Guilds {match.guild1_id} & {match.guild2_id}."
        )

# Global Manager Instance
MATCHMAKING_MANAGER = MatchmakingManager()