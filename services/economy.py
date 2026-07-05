import datetime
from typing import Dict, List, Optional, Any
from database import database_manager
from utils import shared, helpers

class EconomyService:
    """
    Handles all business logic for the local server economy.
    Strictly isolated from the Discord API.
    """

    def __init__(self) -> None:
        """
        Initializes the EconomyService.
        """
        pass

    def _get_db_guild(self, guild_id: int) -> Optional[Any]:
        """
        Fetches the guild object from the in-memory database manager.

        Args:
            guild_id (int): The ID of the target guild.

        Returns:
            Optional[Any]: The Guild model object, or None if not found.
        """
        db_manager = database_manager.DB_MANAGER
        if not db_manager:
            return None
        return next((g for g in db_manager.guilds if g.guild_id == guild_id), None)

    def _get_user_record(self, guild_id: int, user_id: int) -> Optional[Any]:
        """
        Fetches the economy record for a user in a specific guild, initializing a new one if necessary.

        Args:
            guild_id (int): The ID of the guild.
            user_id (int): The ID of the user.

        Returns:
            Optional[Any]: The UserEconomy model object, or None if the DB is unavailable.
        """
        db_manager = database_manager.DB_MANAGER
        if not db_manager:
            return None
        
        record = next((ue for ue in getattr(db_manager, "user_economies", []) if ue.guild_id == guild_id and ue.user_id == user_id), None)
        
        if not record:
            # Use safe default for MySQL to avoid out-of-range datetime errors
            safe_min_time = datetime.datetime(2000, 1, 1)
            record = db_manager.initialize_database_model(
                shared.Table.user_economies,
                guild_id=guild_id,
                user_id=user_id,
                local_balance=0,
                last_message_reward_time=safe_min_time,
                is_dirty=True,
                is_deleted=False
            )
            if hasattr(db_manager, "add_user_economies") and record:
                db_manager.add_user_economies(record)
            
        return record

    def get_balance(self, guild_id: int, user_id: int) -> int:
        """
        Retrieves the current local balance of a user in a specific guild.

        Args:
            guild_id (int): The ID of the guild.
            user_id (int): The ID of the user.

        Returns:
            int: The user's current balance, or 0 if no record exists.
        """
        record = self._get_user_record(guild_id, user_id)
        if not record:
            return 0
        return getattr(record, "local_balance", 0)

    def add_balance(self, guild_id: int, user_id: int, amount: int) -> int:
        """
        Mints or adds new local currency to a user's wallet.

        Args:
            guild_id (int): The ID of the guild.
            user_id (int): The ID of the user receiving funds.
            amount (int): The positive amount of currency to add.

        Returns:
            int: The updated balance. Returns the current balance if the amount is invalid.
        """
        if amount <= 0:
            return self.get_balance(guild_id, user_id)
            
        record = self._get_user_record(guild_id, user_id)
        if not record:
            return 0
            
        record.local_balance += amount
        record.is_dirty = True
        return record.local_balance

    def remove_balance(self, guild_id: int, user_id: int, amount: int) -> bool:
        """
        Removes local currency from a user's wallet (e.g., for purchases or penalties).

        Args:
            guild_id (int): The ID of the guild.
            user_id (int): The ID of the user losing funds.
            amount (int): The positive amount of currency to remove.

        Returns:
            bool: True if the deduction was successful, False if insufficient funds.
        """
        if amount <= 0:
            return False
            
        record = self._get_user_record(guild_id, user_id)
        if not record or record.local_balance < amount:
            return False
            
        record.local_balance -= amount
        record.is_dirty = True
        return True

    def transfer_funds(self, guild_id: int, sender_id: int, receiver_id: int, amount: int) -> bool:
        """
        Handles user-to-user currency transfers atomically.

        Args:
            guild_id (int): The ID of the guild where the transaction occurs.
            sender_id (int): The ID of the user sending funds.
            receiver_id (int): The ID of the user receiving funds.
            amount (int): The positive amount to transfer.

        Returns:
            bool: True if the transaction succeeded, False if the sender lacked funds.
        """
        if amount <= 0 or sender_id == receiver_id:
            return False
            
        if self.remove_balance(guild_id, sender_id, amount):
            self.add_balance(guild_id, receiver_id, amount)
            return True
            
        return False

    def process_message_reward(self, guild_id: int, user_id: int) -> int:
        """
        Calculates and applies a currency reward for chatting, utilizing a 60-second cooldown.

        Args:
            guild_id (int): The ID of the guild where the message was sent.
            user_id (int): The ID of the author.

        Returns:
            int: The amount of currency rewarded. Returns 0 if rate-limited or disabled.
        """
        db_guild = self._get_db_guild(guild_id)
        if not db_guild or not getattr(db_guild, "economy_enabled", True):
            return 0
            
        reward = getattr(db_guild, "base_message_reward", 0)
        if reward <= 0:
            return 0
            
        record = self._get_user_record(guild_id, user_id)
        if not record:
            return 0
            
        now = datetime.datetime.now()
        last_time = getattr(record, "last_message_reward_time", datetime.datetime.min)
        
        # 60 seconds cooldown to prevent chat spamming
        if (now - last_time).total_seconds() < 60:
            return 0
            
        record.last_message_reward_time = now
        record.is_dirty = True
        self.add_balance(guild_id, user_id, reward)
        
        return reward

    def get_shop_items(self, guild_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves the catalog of items available in the Guild's local shop.

        Args:
            guild_id (int): The ID of the guild's shop.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the shop inventory.
        """
        db_manager = database_manager.DB_MANAGER
        if not db_manager:
            return []
            
        items = [item for item in getattr(db_manager, "shop_items", []) if item.guild_id == guild_id and not item.is_deleted]
        
        return [
            {
                "item_id": item.item_id,
                "name": item.name,
                "description": item.description,
                "price": item.price,
                "role_id": getattr(item, "role_id", None)
            }
            for item in items
        ]

    def get_guild_currency(self, guild_id: int) -> str:
        """
        Retrieves the custom currency name for the specified guild.

        Args:
            guild_id (int): The ID of the guild.

        Returns:
            str: The name of the currency, defaulting to "Credits".
        """
        db_guild = self._get_db_guild(guild_id)
        if db_guild and getattr(db_guild, "currency_name", None):
            return db_guild.currency_name
        return "Credits"

    def purchase_item(self, guild_id: int, user_id: int, item_name: str) -> Dict[str, Any]:
        """
        Processes a shop purchase for a user, validating balance and deducting funds atomically.

        Args:
            guild_id (int): The ID of the guild where the shop is located.
            user_id (int): The ID of the purchasing user.
            item_name (str): The name of the item to buy.

        Returns:
            Dict[str, Any]: A dictionary containing a 'success' boolean and either an 'item' payload or a 'reason' string.
        """
        items = self.get_shop_items(guild_id)
        item = next((i for i in items if i["name"].lower() == item_name.lower()), None)
        
        if not item:
            return {"success": False, "reason": "Item not found in the shop."}
            
        price = item["price"]
        
        if self.remove_balance(guild_id, user_id, price):
            return {"success": True, "item": item}
        else:
            return {"success": False, "reason": "Insufficient funds."}