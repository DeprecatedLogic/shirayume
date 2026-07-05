import mysql.connector
import json
from typing import Union, List, Dict, Any, Set
from database import models
from datetime import datetime
from utils import shared, helpers

DB_MANAGER = None 

# Dynamic mapping linking Table enums directly to their model classes
TABLE_MAP = {
    shared.Table.users: models.User,
    shared.Table.guilds: models.Guild,
    shared.Table.user_guild_settings: models.UserGuildSettings,
    shared.Table.moderation_logs: models.ModerationLog,
    shared.Table.polls: models.Poll,
    shared.Table.user_economies: models.UserEconomy,
    shared.Table.shop_items: models.ShopItem,
}

# Explicit definition of primary keys to correctly handle deletions and upsert updates
PRIMARY_KEYS = {
    shared.Table.users: ["user_id"],
    shared.Table.guilds: ["guild_id"],
    shared.Table.user_guild_settings: ["user_id", "guild_id"],
    shared.Table.moderation_logs: ["mlog_id"],
    shared.Table.polls: ["poll_id"],
    shared.Table.user_economies: ["guild_id", "user_id"],
    shared.Table.shop_items: ["item_id"],
}

class DatabaseManager():

    def __init__(self, DB_HOST: str, DB_USER: str, DB_PASSWORD: str, DATABASE: str) -> None:
        """
        Initializes the DatabaseManager, establishing the connection and creating in-memory lists.

        Args:
            DB_HOST (str): Host address for the database.
            DB_USER (str): Database username.
            DB_PASSWORD (str): Database password.
            DATABASE (str): Name of the database.
        """
        self.guilds: List[models.Guild] = []
        self.users: List[models.User] = []
        self.user_guild_settings: List[models.UserGuildSettings] = []
        self.moderation_logs: List[models.ModerationLog] = []
        self.polls: List[models.Poll] = []
        self.user_economies: List[models.UserEconomy] = []
        self.shop_items: List[models.ShopItem] = []
        
        # Cache for database schemas to prevent N+1 query bottlenecks during model initialization
        self._schema_cache: Dict[str, List[str]] = {}

        try:
            self.db_connection = mysql.connector.connect(
                host = DB_HOST,
                user = DB_USER,
                password = DB_PASSWORD,
                database = DATABASE,
                use_pure = True
            )
            self.db_shirayume = self.db_connection.cursor(dictionary=True)

        except mysql.connector.Error as e:
            helpers.custom_print(
                level = shared.LogLevel.CRITICAL,
                function_name = "database.DatabaseManager.__init__",
                description = f"Failed to connect to the database: {e}"
            )
            raise

    # --- Users ---
    def add_users(self, users: Union[List[models.User], models.User]) -> None:
        """
        Adds new users to the in-memory list efficiently.

        Args:
            users (Union[List[models.User], models.User]): A single user or a list of users to add.
        """
        if isinstance(users, models.User): users = [users]
        existing_ids: Set[int] = {u.user_id for u in self.users}
        for user in users:
            if user.user_id not in existing_ids:
                user.is_dirty = True
                user.is_deleted = False
                self.users.append(user)
                existing_ids.add(user.user_id)

    def remove_users(self, user_ids: Union[List[int], int]) -> None:
        """
        Marks users as deleted in memory.

        Args:
            user_ids (Union[List[int], int]): A single user ID or list of user IDs to remove.
        """
        if isinstance(user_ids, int): user_ids = [user_ids]
        id_set = set(user_ids)
        for user in self.users:
            if user.user_id in id_set:
                user.is_dirty = True
                user.is_deleted = True

    # --- Guilds ---
    def add_guilds(self, guilds: Union[List[models.Guild], models.Guild]) -> None:
        """
        Adds new guilds to the in-memory list efficiently.

        Args:
            guilds (Union[List[models.Guild], models.Guild]): A single guild or list of guilds.
        """
        if isinstance(guilds, models.Guild): guilds = [guilds]
        existing_ids: Set[int] = {g.guild_id for g in self.guilds}
        for guild in guilds:
            if guild.guild_id not in existing_ids:
                guild.is_dirty = True
                guild.is_deleted = False
                self.guilds.append(guild)
                existing_ids.add(guild.guild_id)

    def remove_guilds(self, guild_ids: Union[List[int], int]) -> None:
        """
        Marks guilds as deleted in memory.

        Args:
            guild_ids (Union[List[int], int]): Target guild ID(s) to remove.
        """
        if isinstance(guild_ids, int): guild_ids = [guild_ids]
        id_set = set(guild_ids)
        for guild in self.guilds:
            if guild.guild_id in id_set:
                guild.is_dirty = True
                guild.is_deleted = True

    # --- User Guild Settings ---
    def add_user_guild_settings(self, user_guild_settings: Union[List[models.UserGuildSettings], models.UserGuildSettings]) -> None:
        """
        Adds user-guild settings to memory.

        Args:
            user_guild_settings (Union[List[models.UserGuildSettings], models.UserGuildSettings]): Settings to add.
        """
        if isinstance(user_guild_settings, models.UserGuildSettings): user_guild_settings = [user_guild_settings]
        existing_pairs = {(ugs.user_id, ugs.guild_id) for ugs in self.user_guild_settings}
        for ug_settings in user_guild_settings:
            if (ug_settings.user_id, ug_settings.guild_id) not in existing_pairs:
                ug_settings.is_dirty = True
                ug_settings.is_deleted = False
                self.user_guild_settings.append(ug_settings)
                existing_pairs.add((ug_settings.user_id, ug_settings.guild_id))

    def remove_user_guild_settings(self, user_id: int, guild_id: int) -> None:
        """
        Marks a specific user-guild setting as deleted.

        Args:
            user_id (int): ID of the user.
            guild_id (int): ID of the guild.
        """
        for ugs in self.user_guild_settings:
            if ugs.user_id == user_id and ugs.guild_id == guild_id:
                ugs.is_dirty = True
                ugs.is_deleted = True
                break

    def link_user_to_guild(self, user_id: int, guild_id: int) -> None:
        """
        Updates membership status or initializes a new link between user and guild.

        Args:
            user_id (int): ID of the user.
            guild_id (int): ID of the guild.
        """
        for user_guild_settings in self.user_guild_settings:
            if user_guild_settings.user_id == user_id and user_guild_settings.guild_id == guild_id:
                user_guild_settings.is_member = True
                user_guild_settings.is_dirty = True
                user_guild_settings.is_deleted = False 
                return

        user_guild_settings = models.UserGuildSettings(
            user_id = user_id, guild_id = guild_id, joined_at = datetime.now(),
            last_interaction = datetime.now(), experience = 0, level = 0, custom_title = "",
            last_xp_message = datetime.now(), created_at = datetime.now(), updated_at = datetime.now(),
            is_member = True, is_dirty = True, is_deleted = False
        )
        self.add_user_guild_settings(user_guild_settings)

    def unlink_user_from_guild(self, user_id: int, guild_id: int) -> None:
        """
        Sets a user's membership status in a guild to False.

        Args:
            user_id (int): ID of the user.
            guild_id (int): ID of the guild.
        """
        for user_guild_settings in self.user_guild_settings:
            if user_guild_settings.user_id == user_id and user_guild_settings.guild_id == guild_id and user_guild_settings.is_member:
                user_guild_settings.is_member = False 
                user_guild_settings.is_dirty = True
                break 

    # --- Moderation Logs ---
    def get_users_mod_logs(self, user_ids: Union[List[int], int]) -> List[models.ModerationLog]:
        """
        Retrieves all moderation logs associated with specific user(s).

        Args:
            user_ids (Union[List[int], int]): Target user ID(s).

        Returns:
            List[models.ModerationLog]: A list of matching moderation logs.
        """
        if isinstance(user_ids, int): user_ids = [user_ids]
        id_set = set(user_ids)
        return [mlog for mlog in self.moderation_logs if mlog.user_id in id_set]

    def add_moderation_logs(self, moderation_logs: Union[List[models.ModerationLog], models.ModerationLog]) -> None:
        """
        Adds moderation logs to memory.

        Args:
            moderation_logs (Union[List[models.ModerationLog], models.ModerationLog]): Logs to add.
        """
        if isinstance(moderation_logs, models.ModerationLog): moderation_logs = [moderation_logs]
        existing_ids = {l.mlog_id for l in self.moderation_logs}
        for mlog in moderation_logs:
            if mlog.mlog_id not in existing_ids:
                mlog.is_dirty = True
                mlog.is_deleted = False
                self.moderation_logs.append(mlog)
                existing_ids.add(mlog.mlog_id)

    def remove_moderation_logs(self, mlog_ids: Union[List[int], int]) -> None:
        """
        Marks moderation logs as deleted.

        Args:
            mlog_ids (Union[List[int], int]): Target log ID(s).
        """
        if isinstance(mlog_ids, int): mlog_ids = [mlog_ids]
        id_set = set(mlog_ids)
        for mlog in self.moderation_logs:
            if mlog.mlog_id in id_set:
                mlog.is_dirty = True
                mlog.is_deleted = True

    # --- Polls ---
    def add_polls(self, polls: Union[List[models.Poll], models.Poll]) -> None:
        """
        Adds polls to memory.

        Args:
            polls (Union[List[models.Poll], models.Poll]): Polls to add.
        """
        if isinstance(polls, models.Poll): polls = [polls]
        existing_ids = {p.poll_id for p in self.polls}
        for poll in polls:
            if poll.poll_id not in existing_ids:
                poll.is_dirty = True
                poll.is_deleted = False
                self.polls.append(poll)
                existing_ids.add(poll.poll_id)

    def remove_polls(self, poll_ids: Union[List[int], int]) -> None:
        """
        Marks polls as deleted.

        Args:
            poll_ids (Union[List[int], int]): Target poll ID(s).
        """
        if isinstance(poll_ids, int): poll_ids = [poll_ids]
        id_set = set(poll_ids)
        for poll in self.polls:
            if poll.poll_id in id_set:
                poll.is_dirty = True
                poll.is_deleted = True

    # --- User Economies ---
    def add_user_economies(self, economies: Union[List[models.UserEconomy], models.UserEconomy]) -> None:
        """
        Adds user economy records to memory.

        Args:
            economies (Union[List[models.UserEconomy], models.UserEconomy]): Economy records to add.
        """
        if isinstance(economies, models.UserEconomy): economies = [economies]
        existing_pairs = {(e.guild_id, e.user_id) for e in self.user_economies}
        for eco in economies:
            if (eco.guild_id, eco.user_id) not in existing_pairs:
                eco.is_dirty = True
                eco.is_deleted = False
                self.user_economies.append(eco)
                existing_pairs.add((eco.guild_id, eco.user_id))

    def remove_user_economies(self, guild_id: int, user_id: int) -> None:
        """
        Marks an economy record as deleted.

        Args:
            guild_id (int): Target guild ID.
            user_id (int): Target user ID.
        """
        for eco in self.user_economies:
            if eco.guild_id == guild_id and eco.user_id == user_id:
                eco.is_dirty = True
                eco.is_deleted = True
                break

    # --- Shop Items ---
    def add_shop_items(self, items: Union[List[models.ShopItem], models.ShopItem]) -> None:
        """
        Adds shop items to memory.

        Args:
            items (Union[List[models.ShopItem], models.ShopItem]): Shop items to add.
        """
        if isinstance(items, models.ShopItem): items = [items]
        existing_ids = {i.item_id for i in self.shop_items}
        for item in items:
            if item.item_id not in existing_ids:
                item.is_dirty = True
                item.is_deleted = False
                self.shop_items.append(item)
                existing_ids.add(item.item_id)

    def remove_shop_items(self, item_ids: Union[List[int], int]) -> None:
        """
        Marks shop items as deleted.

        Args:
            item_ids (Union[List[int], int]): Target item ID(s).
        """
        if isinstance(item_ids, int): item_ids = [item_ids]
        id_set = set(item_ids)
        for item in self.shop_items:
            if item.item_id in id_set:
                item.is_dirty = True
                item.is_deleted = True

    # --- Core Logic ---
    def initialize_database_model(self, table: shared.Table, **kwargs) -> Any:
        """
        Dynamically initializes a database model based on the target table.

        Args:
            table (shared.Table): The table enum mapping to the model.
            **kwargs: Database row kwargs.

        Returns:
            Any: The initialized model object, or None if validation fails.
        """
        try:
            if table in TABLE_MAP:
                model_class = TABLE_MAP[table]
                table_name = table.name
                
                # Cache the schema to prevent hammering the DB on every single fetch
                if table_name not in self._schema_cache:
                    self.db_shirayume.execute(f"DESCRIBE {table_name}")
                    # We only strictly require fields that cannot be null, have no default, and aren't auto-incremented
                    self._schema_cache[table_name] = [
                        row['Field'] for row in self.db_shirayume.fetchall() 
                        if row['Null'] == 'NO' and row['Default'] is None and 'auto_increment' not in row['Extra']
                    ]
                
                required_fields = self._schema_cache[table_name]
                
                if all(field in kwargs for field in required_fields):
                    return model_class.from_dict(kwargs)
                    
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "database.DatabaseManager.initialize_database_model",
                description = f"Missing required fields for {table.name}"
            )
            return None
        except Exception as e:
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "database.DatabaseManager.initialize_database_model",
                description = f"Error creating model for {table.name}: {e}"
            )
            return None

    def clean_flags(self) -> None:
        """
        Resets all is_dirty and is_deleted flags across all tracked models dynamically.
        """
        for table_enum in TABLE_MAP:
            for item in getattr(self, table_enum.name):
                item.is_dirty = False
                item.is_deleted = False

    def database_commit(self) -> None:
        """
        Efficiently batches and executes all pending dirty state changes into the database using reflection.
        """
        try:
            for table_enum, model_class in TABLE_MAP.items():
                table_name = table_enum.name
                items = getattr(self, table_name)
                dirty_items = [item for item in items if item.is_dirty]
                
                if not dirty_items:
                    continue

                pkeys = PRIMARY_KEYS[table_enum]

                # Batch Deletions
                deleted_items = [item for item in dirty_items if item.is_deleted]
                if deleted_items:
                    where_clause = " AND ".join([f"{pk}=%s" for pk in pkeys])
                    delete_sql = f"DELETE FROM {table_name} WHERE {where_clause}"
                    delete_data = [tuple(getattr(item, pk) for pk in pkeys) for item in deleted_items]
                    self.db_shirayume.executemany(delete_sql, delete_data)

                # Batch Insertions/Updates (Upsert)
                upsert_items = [item for item in dirty_items if not item.is_deleted]
                if upsert_items:
                    # Introspect actual DB columns dynamically just once per table commit
                    self.db_shirayume.execute(f"DESCRIBE {table_name}")
                    columns = [row['Field'] for row in self.db_shirayume.fetchall()]

                    placeholders = ", ".join(["%s"] * len(columns))
                    col_str = ", ".join(columns)
                    
                    # Uses VALUES() which safely updates duplicate keys efficiently in standard MySQL connectors
                    update_str = ", ".join([f"{col}=VALUES({col})" for col in columns if col not in pkeys])

                    upsert_sql = f"""
                        INSERT INTO {table_name} ({col_str})
                        VALUES ({placeholders})
                        ON DUPLICATE KEY UPDATE {update_str}
                    """

                    upsert_data = []
                    for item in upsert_items:
                        row_values = []
                        for col in columns:
                            val = getattr(item, col)
                            # Handle serialization variations smoothly via reflection
                            if isinstance(val, shared.Action):
                                val = val.name
                            elif isinstance(val, (dict, list)):
                                val = json.dumps(val)
                            row_values.append(val)
                        upsert_data.append(tuple(row_values))

                    self.db_shirayume.executemany(upsert_sql, upsert_data)

            self.db_connection.commit()
            self.clean_flags()
            
        except mysql.connector.Error as e:
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "database.DatabaseManager.database_commit",
                description = f"Failed to commit to database: {e}"
            )
            raise

    def database_close(self) -> None:
        """
        Commits pending changes and gracefully closes the database connection.
        """
        try:
            self.database_commit()  
            self.db_shirayume.close()
            self.db_connection.close()
        except mysql.connector.Error as e:
            helpers.custom_print(
                level = shared.LogLevel.CRITICAL,
                function_name = "database.DatabaseManager.database_close",
                description = f"Failed to close database connection: {e}"
            )
            raise

def setup(DB_HOST: str, DB_USER: str, DB_PASSWORD: str, DATABASE: str) -> None:
    """
    Initializes the global DB_MANAGER and dynamically loads all tables.

    Args:
        DB_HOST (str): Host address.
        DB_USER (str): Db user.
        DB_PASSWORD (str): Db password.
        DATABASE (str): Target database.
    """
    helpers.custom_print(
        level = shared.LogLevel.INFO,
        function_name = "database.DatabaseManager.setup",
        description = f"Starting DB setup..."
    )
    global DB_MANAGER
    DB_MANAGER = DatabaseManager(DB_HOST, DB_USER, DB_PASSWORD, DATABASE)
    helpers.custom_print(
        level = shared.LogLevel.DEBUG,
        function_name = "database.DatabaseManager.setup",
        description = f"DB_MANAGER initialized ({DB_MANAGER})"
    )
    try:
        for table_enum in TABLE_MAP:
            table_name = table_enum.name
            helpers.custom_print(
                level = shared.LogLevel.DEBUG,
                function_name = "database.DatabaseManager.setup",
                description = f"Importing {table_name} from DB..."
            )
            
            DB_MANAGER.db_shirayume.execute(f"SELECT * FROM {table_name}")
            rows = DB_MANAGER.db_shirayume.fetchall()
            
            models_list = []
            for row in rows:
                model = DB_MANAGER.initialize_database_model(table_enum, **row)
                if model:
                    models_list.append(model)
            
            # Use reflection to invoke the respective add call dynamically
            getattr(DB_MANAGER, f"add_{table_name}")(models_list)
            
            helpers.custom_print(
                level = shared.LogLevel.DEBUG,
                function_name = "database.DatabaseManager.setup",
                description = f"DB {table_name} imported"
            )

        helpers.custom_print(
            level = shared.LogLevel.INFO,
            function_name = "database.DatabaseManager.setup",
            description = f"Database setup finished"
        )

    except mysql.connector.Error as e:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "database.DatabaseManager.setup",
            description = f"Failed to load data from database: {e}"
        )
        raise