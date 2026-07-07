from typing import Dict, List, Any, Optional
from database import database_manager, models
from utils import shared, helpers

class GlobalEconomyService:
    """
    Handles all business logic for the global economy, including Yume Coins and Guild Taxes.
    """

    def __init__(self) -> None:
        pass

    def _get_user(self, user_id: int) -> Optional[models.User]:
        DB_MANAGER = database_manager.DB_MANAGER
        if not DB_MANAGER:
            helpers.custom_print(
                level = shared.LogLevel.CRITICAL,
                function_name = "services.GlobalEconomyService._get_user",
                description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
            )
            raise RuntimeError("DB_MANAGER not initialized")

        return next((user for user in DB_MANAGER.users if user.user_id == user_id), None)

    def _get_guild(self, guild_id: int) -> Any:
        DB_MANAGER = database_manager.DB_MANAGER
        if not DB_MANAGER:
            helpers.custom_print(
                level = shared.LogLevel.CRITICAL,
                function_name = "services.GlobalEconomyService._get_guild",
                description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
            )
            raise RuntimeError("DB_MANAGER not initialized")
        return next((g for g in DB_MANAGER.guilds if g.guild_id == guild_id), None)

    def process_game_win(self, user_id: int, guild_id: int, base_reward: int) -> Dict[str, int]:
        """
        Distributes winnings, applying guild tax to convert global coins to Guild Yume Points.
        Returns a breakdown of the transaction.

        Args:
            user_id (int): _description_
            guild_id (int): _description_
            base_reward (int): _description_

        Returns:
            Dict[str, int]: _description_
        """
        user = self._get_user(user_id)
        if not user: return {"success": 0, "taxed": 0, "net": 0}

        guild = self._get_guild(guild_id)
        tax_rate = getattr(guild, 'tax_rate', 0.0) if guild else 0.0
        
        tax_amount = int(base_reward * tax_rate)
        net_reward = base_reward - tax_amount

        user.balance += net_reward
        user.is_dirty = True

        if guild and tax_amount > 0:
            guild.yume_points += tax_amount
            guild.is_dirty = True

        return {"success": 1, "taxed": tax_amount, "net": net_reward}

    def set_guild_tax(self, guild_id: int, rate: float) -> bool:
        """
        Enforces constraints (0% to 30%) and sets the tax rate.

        Args:
            guild_id (int): _description_
            rate (float): _description_

        Returns:
            bool: _description_
        """
        if not (0.0 <= rate <= 0.30):
            return False
            
        guild = self._get_guild(guild_id)
        if guild:
            guild.tax_rate = rate
            guild.is_dirty = True
            return True
        return False

    def get_global_shop_items(self) -> List[Dict[str, Any]]:
        """
        _summary_

        Returns:
            List[Dict[str, Any]]: _description_
        """
        db = database_manager.DB_MANAGER
        if not db: return []
        
        items = [item for item in getattr(db, "global_shop_items", []) if not item.is_deleted]
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
        Atomically handles global coin deduction and instantly equips the payload to User.active_items.

        Args:
            user_id (int): _description_
            item_id (int): _description_

        Returns:
            Dict[str, Any]: _description_
        """
        user = self._get_user(user_id)
        if not user: return {"success": False, "reason": "User profile not found."}

        db = database_manager.DB_MANAGER
        item = next((i for i in getattr(db, "global_shop_items", []) if i.item_id == item_id and not i.is_deleted), None)

        if not item:
            return {"success": False, "reason": "Item not found in the global shop."}

        if user.balance < item.price:
            return {"success": False, "reason": f"Insufficient Yume Coins. You need {item.price}."}

        user.balance -= item.price
        
        # Equip the item dynamically using Polymorphic mapping
        payload_key = item.item_type.name
        payload_value = item.metadata.get("value")

        if payload_value:
            user.active_items[payload_key] = payload_value

        user.is_dirty = True
        return {"success": True, "item": item}