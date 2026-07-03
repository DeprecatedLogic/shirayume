import time
from utils import shared, helpers
from typing import Dict, List, Optional
import database
from database import database_manager

class StatisticsService:
    def __init__(self) -> None:
        """_summary_"""
        self.cache = {} # guild_id: last stats dict
        self.last_update = {} # guild_id: timestamp

    def _get_db_guild(self, guild_id: int) -> database.models.Guild:
        """
        _summary_

        Args:
            guild_id (int): _description_

        Raises:
            RuntimeError: _description_

        Returns:
            database.models.Guild: _description_
        """
        DB_MANAGER = database_manager.DB_MANAGER
        if not DB_MANAGER:
            helpers.custom_print(
                level = shared.LogLevel.CRITICAL,
                function_name = "services.StatisticsService.add_moderation_logs",
                description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
            )
            raise RuntimeError("DB_MANAGER not initialized")

        return next((guild for guild in DB_MANAGER.guilds if guild.guild_id == guild_id), None)

    def is_stats_enabled(self, guild_id: int) -> bool:
        """
        _summary_

        Args:
            guild_id (int): _description_

        Returns:
            bool: _description_
        """
        if not shared.GLOBAL_CONFIG["features"]["statistics"]["is_enabled"]:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                function_name="services.StatisticsService.is_stats_enabled",
                description="Statistics are disabled globally"
            )
            return False
        
        db_guild = self._get_db_guild(guild_id)
        return db_guild and db_guild.stats_enabled

    def enable_stats(self, guild_id: int) -> bool:
        """
        _summary_

        Args:
            guild_id (int): _description_

        Returns:
            bool: _description_
        """
        db_guild = self._get_db_guild(guild_id)
        if not db_guild or db_guild.stats_enabled:
            return False

        db_guild.stats_enabled = True
        
        if not db_guild.stats_channel_ids:
            db_guild.stats_channel_ids = {}

        db_guild.is_dirty = True
        return True

    def disable_stats(self, guild_id: int) -> dict:
        """
        Marks stats as disabled in DB and returns the IDs of channels/categories 
        that need to be deleted by the Cog.

        Args:
            guild_id (int): _description_
        
        Returns:
            dict: _description_
        """
        db_guild = self._get_db_guild(guild_id)
        if not db_guild or not db_guild.stats_enabled:
            return {}

        to_delete = {
            "category_id": db_guild.stats_category_id,
            "channel_ids": list(db_guild.stats_channel_ids.values())
        }

        db_guild.stats_enabled = False
        db_guild.stats_category_id = None
        db_guild.stats_channel_ids = {}
        db_guild.is_dirty = True

        self.cache.pop(guild_id, None)
        self.last_update.pop(guild_id, None)
        
        return to_delete

    def get_tracked_ids(self, guild_id: int) -> dict:
        db_guild = self._get_db_guild(guild_id)
        if not db_guild:
            return {"category_id": None, "channel_ids": {}}
            
        return {
            "category_id": db_guild.stats_category_id,
            "channel_ids": db_guild.stats_channel_ids
        }

    def update_tracked_ids(self, guild_id: int, category_id: int, channel_ids: dict) -> None:
        """
        _summary_

        Args:
            guild_id (int): _description_
            category_id (int): _description_
            channel_ids (dict): _description_
        """
        db_guild = self._get_db_guild(guild_id)
        if db_guild:
            db_guild.stats_category_id = category_id
            db_guild.stats_channel_ids = channel_ids
            db_guild.is_dirty = True

    def calculate_stats(self, guild_id: int, total_members: int, member_data: List[Dict[str, bool]]) -> Optional[Dict[str, int]]:
        """
        Calculates stats if not rate limited and if stats changed.
        Returns the stats dict if an update is needed, else None.
        member_data should be a list of dicts: {"is_bot": bool, "is_online": bool}

        Args:
            guild_id (int): _description_
            total_members (int): _description_
            member_data (List[Dict[str, bool]]): _description_

        Returns:
            Optional[Dict[str, int]]: _description_
        """
        if not self.is_stats_enabled(guild_id):
            return None

        time_delta = time.time() - self.last_update.get(guild_id, 0)
        if time_delta < 45:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                function_name="services.StatisticsService.calculate_stats",
                description=f"Statistics are being rate limited ({time_delta} seconds)"
            )
            return None

        bots = sum(1 for member in member_data if member["is_bot"])
        active = sum(1 for member in member_data if not member["is_bot"] and member["is_online"])
        inactive = total_members - active - bots

        stats = {
            "all": total_members,
            "active": active,
            "inactive": inactive,
            "bots": bots,
        }

        if self.cache.get(guild_id) == stats:
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                function_name="services.StatisticsService.calculate_stats",
                description=f"Statistics fetched from cache"
            )
            return None

        self.cache[guild_id] = stats
        self.last_update[guild_id] = time.time()
        return stats

    def get_expected_names(self, stats: Dict[str, int]) -> Dict[str, str]:
        """
        Returns a mapping of channel keys to their formatted names.

        Args:
            stats (Dict[str, int]): _description_

        Returns:
            Dict[str, str]: _description_
        """
        CHANNELS = shared.GLOBAL_CONFIG["features"]["statistics"]["channels"]
        return {key: CHANNELS[key].format(count) for key, count in stats.items()}