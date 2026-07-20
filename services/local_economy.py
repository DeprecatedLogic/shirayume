import datetime
from typing import Dict, List, Optional, Any
from database import database_manager, models
from utils import shared, helpers

class EconomyService:
    """
    Manages all local economy configuration logic, item shop transactions, 
    and balance records isolated from direct API calls.
    """

    def __init__(self) -> None:
        pass

    def _get_db_guild(self, guild_id: int) -> Optional[Any]:
        """
        Fetches the guild object from the in-memory database manager.

        Args:
            guild_id (int): The ID of the target guild.

        Returns:
            Optional[Any]: The Guild model object, or None if not found.
        """
        return next((g for g in database_manager.DB_MANAGER.guilds if g.guild_id == guild_id), None)

    def _get_user_record(self, guild_id: int, user_id: int) -> Optional[Any]:
        """
        Fetches the economy record for a user in a specific guild, initializing a new one if necessary.

        Args:
            guild_id (int): The ID of the guild.
            user_id (int): The ID of the user.

        Returns:
            Optional[Any]: The UserEconomy model object.
        """
        record = next((ue for ue in getattr(database_manager.DB_MANAGER, "user_economies", []) if ue.guild_id == guild_id and ue.user_id == user_id), None)
        
        if not record:
            # Use safe default for MySQL to avoid out-of-range datetime errors
            safe_min_time = datetime.datetime(2000, 1, 1)
            record = database_manager.DB_MANAGER.initialize_database_model(
                shared.Table.user_economies,
                guild_id=guild_id,
                user_id=user_id,
                local_balance=0,
                last_message_reward_time=safe_min_time,
                is_dirty=True,
                is_deleted=False
            )
            if hasattr(database_manager.DB_MANAGER, "add_user_economies") and record:
                database_manager.DB_MANAGER.add_user_economies(record)
                helpers.custom_print(
                    level=shared.LogLevel.DEBUG,
                    description=f"Initialized new local economy tracking profile for user ID {user_id} in guild ID {guild_id}."
                )
            
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
        database_manager.DB_MANAGER.mark_dirty(shared.Table.user_economies, record)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Added {amount} local currency to user ID {user_id} in guild ID {guild_id}."
        )
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
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=f"Failed balance removal: User ID {user_id} lacks {amount} credits in guild ID {guild_id}."
            )
            return False
            
        record.local_balance -= amount
        database_manager.DB_MANAGER.mark_dirty(shared.Table.user_economies, record)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"Removed {amount} local currency from user ID {user_id} in guild ID {guild_id}."
        )
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
            
        # Execute atomic withdrawal before verifying drop points
        if self.remove_balance(guild_id, sender_id, amount):
            self.add_balance(guild_id, receiver_id, amount)
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Transferred {amount} local credits from user ID {sender_id} to user ID {receiver_id} in guild ID {guild_id}."
            )
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
        database_manager.DB_MANAGER.mark_dirty(shared.Table.user_economies, record)
        self.add_balance(guild_id, user_id, reward)
        
        return reward

    def get_shop_item(self, guild_id: int, item_id: int) -> Dict[str, Any]:
        """
        Retrieves the specific item if it's still available in the Guild's local shop.

        Args:
            guild_id (int): The ID of the guild's shop.
            item_id (int): The internal database ID of the item.

        Returns:
            Dict[str, Any]: A dictionary representing the item.
        """
            
        item = next((
            item
            for item in getattr(database_manager.DB_MANAGER, "shop_items", [])
            if item.guild_id == guild_id and item.item_id == item_id and not getattr(item, "is_deleted", False)
        ), None)
        
        if not item:
            return {}

        return {
            "item_id": item.item_id,
            "name": item.name,
            "description": item.description,
            "price": item.price,
            "role_id": getattr(item, "role_id", None)
        }

    def get_shop_items(self, guild_id: int) -> List[Dict[str, Any]]:
        """
        Retrieves the catalog of items available in the Guild's local shop.

        Args:
            guild_id (int): The ID of the guild's shop.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the shop inventory.
        """
            
        items = [item for item in getattr(database_manager.DB_MANAGER, "shop_items", []) if item.guild_id == guild_id and not item.is_deleted]
        
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

    def add_shop_item(self, guild_id: int, name: str, price: int, description: str, role_id: Optional[int] = None) -> bool:
        """
        Adds a new item to the guild's local shop.

        Args:
            guild_id (int): The ID of the guild.
            name (str): The name of the item.
            price (int): The cost of the item.
            description (str): The description of the item.
            role_id (Optional[int]): The ID of the role to grant upon purchase, if any.

        Returns:
            bool: True if added successfully, False otherwise.
        """
            
        next_id = database_manager.DB_MANAGER.get_next_id(shared.Table.shop_items, guild_id)

        record = database_manager.DB_MANAGER.initialize_database_model(
            shared.Table.shop_items,
            item_id=next_id,
            guild_id=guild_id,
            name=name,
            description=description,
            price=price,
            role_id=role_id,
            is_dirty=True,
            is_deleted=False
        )
        
        if hasattr(database_manager.DB_MANAGER, "add_shop_items") and record:
            database_manager.DB_MANAGER.add_shop_items(record)
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"Created new local shop item ID {next_id} (Name: {name}) for guild ID {guild_id}."
            )
            return True

        return False

    def remove_shop_item(self, guild_id: int, item_id: int) -> bool:
        """
        Soft-deletes an item from the guild's local shop.

        Args:
            guild_id (int): The ID of the guild.
            item_id (int): The internal database ID of the item to remove.

        Returns:
            bool: True if the item was found and deleted, False otherwise.
        """
            
        item = next((
            item for item in getattr(database_manager.DB_MANAGER, "shop_items", []) 
            if item.guild_id == guild_id and item.item_id == item_id and not getattr(item, "is_deleted", False)
        ), None)
        
        if not item:
            return False

        database_manager.DB_MANAGER.remove_shop_items(item_id)
        helpers.custom_print(
            level=shared.LogLevel.INFO,
            description=f"Soft-deleted local shop item ID {item_id} from guild ID {guild_id}."
        )
        return True

    def get_guild_currency(self, guild_id: int) -> str:
        """
        Retrieves the custom currency name for the specified guild.

        Args:
            guild_id (int): The ID of the guild.

        Returns:
            str: The name of the currency, defaulting to "Credits".
        """
        db_guild = self._get_db_guild(guild_id)
        if db_guild:
            return getattr(db_guild, "currency", "Credits")
        return "Credits"

    def purchase_item(self, guild_id: int, user_id: int, item_id: int) -> Dict[str, Any]:
        """
        Processes a shop purchase for a user, validating balance and deducting funds atomically.

        Args:
            guild_id (int): The ID of the guild where the shop is located.
            user_id (int): The ID of the purchasing user.
            item_id (int): The ID of the item to buy.

        Returns:
            Dict[str, Any]: A dictionary containing a 'success' boolean and either an 'item' payload or a 'reason' string.
        """
        items = self.get_shop_items(guild_id)
        item = next((i for i in items if i["item_id"] == item_id), None)
        
        if not item:
            return {"success": False, "reason": "Item not found in the shop."}
            
        price = item["price"]
        
        # Atomically remove balance to settle transaction safely
        if self.remove_balance(guild_id, user_id, price):
            helpers.custom_print(
                level=shared.LogLevel.INFO,
                description=f"User ID {user_id} successfully bought item ID {item_id} in local shop of guild ID {guild_id}."
            )
            return {"success": True, "item": item}
        else:
            return {"success": False, "reason": "Insufficient funds."}