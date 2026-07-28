import uuid
from collections import OrderedDict
from datetime import datetime
from typing import Optional
from services.matchmaking.shared import GameType, QueueEntry
from utils import helpers, shared

class MatchmakingQueue:
    """
    Manages matchmaking queues per game mode. Checks users strictly in O(1).
    Matches guilds iteratively from the front of the queue to ensure cross-guild pairs.
    """
    def __init__(self):
        self._queues: dict[GameType, OrderedDict[str, QueueEntry]] = {
            game_type: OrderedDict() for game_type in GameType
        }
        self._user_to_entry: dict[int, str] = {}

    def is_user_queued(self, user_id: int) -> bool:
        """O(1) lookup to check if a specific user is in any queue."""
        return user_id in self._user_to_entry

    def is_guild_queued(self, guild_id: int) -> bool:
        """Checks if a guild is already queued in any game mode."""
        for queue in self._queues.values():
            for entry in queue.values():
                if entry.guild_id == guild_id:
                    return True
        return False

    def add_to_queue(
        self,
        guild_id: int,
        channel_id: int,
        user_ids: list[int],
        game_type: GameType,
        credits_bet: int = 0
    ) -> tuple[bool, str, tuple[QueueEntry, QueueEntry] | None]:
        """
        Enqueues a team of users. If an opponent from a different guild exists, pairs them.
        """
        for user_id in user_ids:
            if self.is_user_queued(user_id):
                return False, f"User <@{user_id}> is already in a queue.", None

        if self.is_guild_queued(guild_id):
            return False, "Your guild is already in the matchmaking queue.", None

        queue = self._queues[game_type]
        match_entry = None

        # O(1) amortized search for opponent from a different guild
        for entry_id, entry in queue.items():
            if entry.guild_id != guild_id and entry.credits_bet == credits_bet:
                match_entry = entry
                break

        current_entry_id = str(uuid.uuid4())
        current_entry = QueueEntry(
            entry_id=current_entry_id,
            guild_id=guild_id,
            channel_id=channel_id,
            user_ids=user_ids,
            game_type=game_type,
            joined_at=datetime.now(),
            credits_bet=credits_bet
        )

        if match_entry:
            del queue[match_entry.entry_id]
            for uid in match_entry.user_ids:
                del self._user_to_entry[uid]

            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Match found between Guild {match_entry.guild_id} and Guild {guild_id} for {game_type.name}."
            )
            return True, "Match found!", (match_entry, current_entry)

        queue[current_entry_id] = current_entry
        for user_id in user_ids:
            self._user_to_entry[user_id] = current_entry_id

        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Guild {guild_id} team joined queue for {game_type.name}."
        )
        return True, "Joined queue.", None

    def remove_from_queue(self, user_id: int) -> bool:
        """Removes the entire team's queue entry using a single user's ID in O(1)."""
        entry_id = self._user_to_entry.get(user_id)
        if not entry_id:
            return False

        for game_type, queue in self._queues.items():
            if entry_id in queue:
                entry = queue.pop(entry_id)
                for uid in entry.user_ids:
                    del self._user_to_entry[uid]
                helpers.custom_print(
                    level=shared.LogLevel.INFO,
                    description=f"Queue entry {entry_id} removed by User {user_id}."
                )
                return True
        return False
