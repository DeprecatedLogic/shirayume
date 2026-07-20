import time
from utils import shared, helpers
from typing import Dict, List, Optional
from database import database_manager, models

class StatisticsService:
    """
    Manages active guild member statistics, keeping track of caching,  
    rate-limiting counters, and channel visibility states.
    """

    def __init__(self) -> None:
        self.cache = {} # Map guild_id -> last stats dict to prevent redundant updates
        self.last_update = {} # Map guild_id -> timestamp for rate limit pacing

    def _get_db_guild(self, guild_id: int) -> Optional[models.Guild]:
        """
        Internal helper to look up a guild tracking model within the active database cache.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.

        Returns:
            Optional[models.Guild]: The matching guild database record or None if missing.
        """
        return next((guild for guild in database_manager.DB_MANAGER.guilds if guild.guild_id == guild_id), None)

    def is_stats_enabled(self, guild_id: int) -> bool:
        """
        Checks if the voice/text statistics system is globally functional  
        and explicitly toggled on for the specified guild.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.

        Returns:
            bool: True if statistics tracking is enabled locally and globally, otherwise False.
        """
        # Guard clause against the global feature config toggle
        if not shared.GLOBAL_CONFIG["features"]["statistics"]["is_enabled"]:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description="Statistics are disabled globally."
            )
            return False
        
        db_guild = self._get_db_guild(guild_id)
        return db_guild and db_guild.stats_enabled

    def enable_stats(self, guild_id: int) -> bool:
        """
        Enables statistics tracking flags for a guild and sets up the internal channel mapping structure.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.

        Returns:
            bool: True if the toggle state successfully flipped to enabled, False if it was already active.
        """

        db_guild = self._get_db_guild(guild_id)
        if not db_guild or db_guild.stats_enabled:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Failed to enable statistics for guild ID {guild_id} (already enabled or guild not found)."
            )
            return False

        # Flip the tracking bit and ensure the ID mapping dict exists
        db_guild.stats_enabled = True
        if not db_guild.stats_channel_ids:
            db_guild.stats_channel_ids = {}

        database_manager.DB_MANAGER.mark_dirty(shared.Table.guilds, db_guild)
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Statistics feature enabled for guild ID {guild_id}."
        )
        return True

    def disable_stats(self, guild_id: int) -> dict:
        """
        Turns off tracking flags for a guild, flushes its active cache, and aggregates  
        its existing tracking channel resources to clear out leftovers.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.
        
        Returns:
            dict: A payload containing the tracked 'category_id' and a list of 'channel_ids' slated for deletion.
        """

        db_guild = self._get_db_guild(guild_id)
        if not db_guild or not db_guild.stats_enabled:
            return {}

        # Collect old IDs before wiping them so the calling cog knows what channels to remove from Discord
        to_delete = {
            "category_id": db_guild.stats_category_id,
            "channel_ids": list(db_guild.stats_channel_ids.values())
        }

        # Clear state structures completely
        db_guild.stats_enabled = False
        db_guild.stats_category_id = None
        db_guild.stats_channel_ids = {}

        database_manager.DB_MANAGER.mark_dirty(shared.Table.guilds, db_guild)
        self.cache.pop(guild_id, None)
        
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Statistics feature disabled for guild ID {guild_id}."
        )
        return to_delete

    def get_tracked_ids(self, guild_id: int) -> dict:
        """
        Retrieves the category and channel snowflakes allocated to statistics display for the target guild.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.

        Returns:
            dict: Dictionary structure containing 'category_id' and the 'channel_ids' sub-dictionary.
        """
        db_guild = self._get_db_guild(guild_id)
        if not db_guild:
            return {"category_id": None, "channel_ids": {}}
            
        return {
            "category_id": db_guild.stats_category_id,
            "channel_ids": db_guild.stats_channel_ids
        }

    def update_tracked_ids(self, guild_id: int, category_id: int, channel_ids: dict) -> None:
        """
        Updates and commits the active category and channel display snowflakes mapped to the guild's statistics block.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.
            category_id (int): The new Discord CategoryChannel snowflake ID.
            channel_ids (dict): Dictionary mapping metrics (e.g., 'all', 'bots') to text/voice channel snowflakes.
        """

        db_guild = self._get_db_guild(guild_id)
        if db_guild:
            db_guild.stats_category_id = category_id
            db_guild.stats_channel_ids = channel_ids

            database_manager.DB_MANAGER.mark_dirty(shared.Table.guilds, db_guild)
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Updated tracking IDs for guild ID {guild_id}."
            )

    def calculate_stats(self, guild_id: int, total_members: int, member_data: List[Dict[str, bool]]) -> Optional[Dict[str, int]]:
        """
        Parses and computes real-time counts across visibility groups, skipping execution  
        if the metrics match the last known state cache.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.
            total_members (int): The absolute count of all members in the guild.
            member_data (List[Dict[str, bool]]): A list of status profiles containing keys "is_bot" and "is_online".

        Returns:
            Optional[Dict[str, int]]: A dictionary detailing numerical segments if numbers changed, otherwise None.
        """
        if not self.is_stats_enabled(guild_id):
            return None

        # Count groups based on application rules
        bots = sum(1 for member in member_data if member["is_bot"])
        active = sum(1 for member in member_data if not member["is_bot"] and member["is_online"])
        inactive = total_members - active - bots

        stats = {
            "all": total_members,
            "active": active,
            "inactive": inactive,
            "bots": bots,
        }

        # Cache optimization step: avoid making redundant Discord API edits if data hasn't changed
        if self.cache.get(guild_id) == stats:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Statistics fetched from cache."
            )
            return None

        self.cache[guild_id] = stats
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Recalculated stats for guild ID {guild_id}: {stats}"
        )
        return stats

    def get_expected_names(self, stats: Dict[str, int]) -> Dict[str, str]:
        """
        Formats standard channel string templates extracted from configuration with raw calculated integers.

        Args:
            stats (Dict[str, int]): Computed tracking dictionary from `calculate_stats`.

        Returns:
            Dict[str, str]: Map of metric target keys to their fully stylized, end-user channel titles.
        """
        CHANNELS = shared.GLOBAL_CONFIG["features"]["statistics"]["channels"]
        return {key: CHANNELS[key].format(count) for key, count in stats.items()}