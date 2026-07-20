from typing import Dict, List, Any, Optional
from database import database_manager, models
from utils import shared, helpers
import heapq

class GlobalEconomyService:
    """
    Manages all core business logic for the global economy cross-server system,  
    including Yume Coin transactions, shop processing, and tax collection points.
    """

    def __init__(self) -> None:
        pass

    def _get_user(self, user_id: int) -> Optional[models.User]:
        """
        Internal lookup utility to locate a user profile from the database manager's cache.

        Args:
            user_id (int): The unique Discord snowflake ID of the user.

        Returns:
            Optional[models.User]: The matching user model record, or None if missing.
        """
        return next((user for user in database_manager.DB_MANAGER.users if user.user_id == user_id), None)

    def _get_guild(self, guild_id: int) -> Any:
        """
        Internal lookup utility to locate a guild record from the database manager's cache.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.

        Returns:
            Any: The matching guild model record, or None if missing.
        """
        return next((guild for guild in database_manager.DB_MANAGER.guilds if guild.guild_id == guild_id), None)

    def process_game_win(self, user_id: int, guild_id: int, base_reward: int) -> Dict[str, int]:
        """
        Distributes currency winnings to a user while applying the local guild's tax 
        rate to allocate points to the guild pool.

        Args:
            user_id (int): The unique Discord snowflake ID of the user.
            guild_id (int): The server context boundary where the mini-game was won.
            base_reward (int): The absolute starting currency pool prior to tax deductions.

        Returns:
            Dict[str, int]: Transaction mapping summary containing execution metrics.
        """
        user = self._get_user(user_id)
        if not user: 
            return {"success": 0, "taxed": 0, "net": 0}

        guild = self._get_guild(guild_id)
        tax_rate = getattr(guild, 'tax_rate', 0.0) if guild else 0.0
        
        # Calculate split between user net reward and guild tax allocation
        tax_amount = int(base_reward * tax_rate)
        net_reward = base_reward - tax_amount

        user.balance += net_reward
        database_manager.DB_MANAGER.mark_dirty(shared.Table.users, user)

        # Apply calculated tax slices directly to the guild storage record
        if guild and tax_amount > 0:
            guild.yume_points += tax_amount
            database_manager.DB_MANAGER.mark_dirty(shared.Table.guilds, guild)

        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=(
                f"Processed game win for user ID {user_id} in guild ID {guild_id}: "
                f"base {base_reward}, net {net_reward}, taxed {tax_amount}."
            )
        )
        return {"success": 1, "taxed": tax_amount, "net": net_reward}

    def set_guild_tax(self, guild_id: int, rate: float) -> bool:
        """
        Sets and limits a server's global economy tax rate configuration within boundaries.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.
            rate (float): The target percentage value represented as a float factor between 0.0 and 0.30.

        Returns:
            bool: True if the verification succeeded and the rate was saved, otherwise False.
        """
        # Hard constraint ceiling checks (0% minimum to 30% maximum allowed)
        if not (0.0 <= rate <= 0.30):
            helpers.custom_print(
                level=shared.LogLevel.WARNING,
                description=f"Rejected out of bounds tax rate configuration attempt of {rate} for guild ID {guild_id}."
            )
            return False
            
        guild = self._get_guild(guild_id)
        if guild:
            guild.tax_rate = rate
            database_manager.DB_MANAGER.mark_dirty(shared.Table.guilds, guild)
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Updated tax rate configuration for guild ID {guild_id} to {rate}."
            )
            return True
        return False

    def get_guild_tax(self, guild_id: int) -> float:
        """
        Retrieves the active global economy tax rate configured for the target server.

        Args:
            guild_id (int): The unique Discord snowflake ID of the guild.

        Returns:
            float: The saved tax float value, or -1 if the server record cannot be resolved.
        """ 
        guild = self._get_guild(guild_id)
        if guild:
            return guild.tax_rate
            
        return -1

    def get_global_shop_items(self) -> List[Dict[str, Any]]:
        """
        Extracts the entire collection of active items currently sold within the cross-server shop catalog.

        Returns:
            List[Dict[str, Any]]: Array of dictionary items tracking standard product fields.
        """
        # Filter down the tracking catalog array to remove soft-deleted models
        items = [item for item in getattr(database_manager.DB_MANAGER, "global_shop_items", []) if not item.is_deleted]
        return [
            {
                "item_id": i.item_id,
                "name": i.name,
                "description": i.description,
                "price": i.price,
                "item_type": i.item_type,
                "metadata": i.metadata
            }
            for i in items
        ]

    def purchase_global_item(self, user_id: int, item_id: int) -> Dict[str, Any]:
        """
        Validates balances, performs atomic balance deductions, and maps item privileges 
        directly to a user's active inventory profile slot.

        Args:
            user_id (int): The unique Discord snowflake ID of the purchasing user.
            item_id (int): The internal tracking key configuration assigned to the item.

        Returns:
            Dict[str, Any]: Dictionary payload verifying transaction status parameters.
        """
        user = self._get_user(user_id)
        if not user: 
            return {"success": False, "reason": "User profile not found."}

        item = next((i for i in getattr(database_manager.DB_MANAGER, "global_shop_items", []) if i.item_id == item_id and not i.is_deleted), None)

        if not item:
            return {"success": False, "reason": "Item not found in the global shop."}

        # Verify wallet limits before approving item processing
        if user.balance < item.price:
            return {"success": False, "reason": f"Insufficient Yume Coins. You need {item.price}."}

        user.balance -= item.price
        
        # Equip the purchased payload target into the polymorphic mapping container
        payload_key = item.item_type.name
        payload_value = item.metadata.get("value")

        if payload_value:
            user.active_items[payload_key] = payload_value

        database_manager.DB_MANAGER.mark_dirty(shared.Table.users, user)
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"User ID {user_id} successfully bought item ID {item_id} for {item.price} coins."
        )
        return {"success": True, "item": item}

    def get_top_guilds(self, guild_id: int, number_of_guilds: int) -> list[models.Guild]:
        """
        Compiles a sorted leaderboard array containing high-ranking guild models based on aggregated tax points.

        Args:
            guild_id (int): Server boundary tracking reference context.
            number_of_guilds (int): Cap configuration restricting total results returned.

        Raises:
            RuntimeError: If the central database tracking manager is uninitialized.

        Returns:
            list[models.Guild]: Highest matching guild data rows extracted from storage.
        """
        # Keep number_of_guilds bound safely within [1, 100] scale constraints
        if number_of_guilds > 100:
            number_of_guilds = 100
        elif number_of_guilds < 1:
            number_of_guilds = 1
        
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Querying top {number_of_guilds} guilds for leaderboard display request."
        )
        return heapq.nlargest(
            number_of_guilds,
            database_manager.DB_MANAGER.guilds,
            key=lambda g: getattr(g, 'yume_points', 0)
        )

    def add_global_shop_item(self, name: str, price: int, item_type_name: str, metadata: dict, description: str) -> Dict[str, Any]:
        """
        Creates a completely new global shop item configuration model and registers it inside storage tracked arrays.

        Args:
            name (str): Label applied to display fields.
            price (int): Numerical value coin requirement.
            item_type_name (str): String identifier key tracking enum classifications.
            metadata (dict): Structural configuration fields assigned to functional commands.
            description (str): Detail context information strings.

        Returns:
            Dict[str, Any]: Status confirmation verification structures.
        """
        # Dynamically evaluate the string target against core Enum components
        try:
            item_type = shared.GlobalItemType[item_type_name.lower()]
        except KeyError:
            valid_types = ", ".join(set(e.name for e in shared.GlobalItemType))
            return {"success": False, "reason": f"Invalid item type. Allowed types: {valid_types}"}

        next_id = database_manager.DB_MANAGER.get_next_id(shared.Table.global_shop_items)

        record = database_manager.DB_MANAGER.initialize_database_model(
            shared.Table.global_shop_items,
            item_id=next_id,
            name=name,
            description=description,
            price=price,
            item_type=item_type,
            metadata=metadata,
            is_dirty=True,
            is_deleted=False
        )

        if hasattr(database_manager.DB_MANAGER, "add_global_shop_items") and record:
            database_manager.DB_MANAGER.add_global_shop_items(record)
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Successfully created global shop item ID {next_id} (Name: {name})."
            )
            return {"success": True, "item": record}

        return {"success": False, "reason": "Failed to add the item to the database."}