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
    shared.Table.global_shop_items: models.GlobalShopItem,
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
    shared.Table.global_shop_items: ["item_id"],
}

# Pre-defined mapping of tables that require in-memory auto-increment IDs to their column name
AUTO_INCREMENT_FIELDS = {
    shared.Table.moderation_logs: "mlog_id",
    shared.Table.polls: "poll_id",
    shared.Table.shop_items: "item_id",
    shared.Table.global_shop_items: "item_id",
}

class DatabaseManager:

    def __init__(self, DB_HOST: str, DB_USER: str, DB_PASSWORD: str, DATABASE: str) -> None:
        """
        Initializes the DatabaseManager, establishing the connection and creating in-memory lists.

        Args:
            DB_HOST (str): Host address for the database.
            DB_USER (str): Database username.
            DB_PASSWORD (str): Database password.
            DATABASE (str): Name of the database.
        """
        self.users = []
        self.guilds = []
        self.user_guild_settings = []
        self.moderation_logs = []
        self.polls = []
        self.user_economies = []
        self.shop_items = []
        self.global_shop_items = []

        # O(1) lookup indices
        self._index = {
            table: {}
            for table in TABLE_MAP
        }

        # Dirty tracking
        self._dirty = {
            table:set()
            for table in TABLE_MAP
        }

        # Schema cache
        self._schema_cache = {}

        # SQL cache
        self._sql_cache = {}

        # Last IDs cache
        self._last_id_cache = {}

        try:
            self.db_connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DATABASE,
                use_pure=True
            )

            self.db_shirayume = self.db_connection.cursor(
                dictionary=True
            )

            self._initialize_schema()

        except mysql.connector.Error as e:

            helpers.custom_print(
                level=shared.LogLevel.CRITICAL,
                function_name="database.DatabaseManager.__init__",
                description=f"Failed to connect: {e}"
            )

            raise

    def _key(self, table, obj):
        """
        _summary_

        Args:
            table (_type_): _description_
            obj (_type_): _description_

        Returns:
            _type_: _description_
        """
        pkeys = PRIMARY_KEYS[table]

        if len(pkeys) == 1:
            return getattr(obj, pkeys[0])

        return tuple(getattr(obj,pk) for pk in pkeys)

    def mark_dirty(self, table, obj) -> None:
        """
        _summary_

        Args:
            table (_type_): _description_
            obj (_type_): _description_
        """
        obj.is_dirty = True
        self._dirty[table].add(obj)

    def _add(self, table, items, set_dirty: bool = True) -> None:
        """
        Adds item(s) to the in-memory cache, replacing existing items 
        with the same primary key if they exist.
        """
        if not isinstance(items, list):
            items = [items]

        storage = getattr(self, table.name)
        index = self._index[table]

        for item in items:
            key = self._key(table, item)

            if key in index:
                old_item = index[key]
                
                # If same memory reference (un-delete / update if needed)
                if old_item is item:
                    old_item.is_deleted = False
                    if set_dirty:
                        self.mark_dirty(table, old_item)
                    continue

                # If new object reference replacing an old one
                if old_item in storage:
                    storage.remove(old_item)
                
                # Safely discard the old object from dirty tracking 
                # (the new object will overwrite it in the DB on commit)
                self._dirty[table].discard(old_item)

            # Insert the new item into active storage and the index
            item.is_deleted = False
            storage.append(item)
            index[key] = item

            if set_dirty:
                self.mark_dirty(table, item)

    def _remove(self, table, key) -> None:
        """_summary_

        Args:
            table (_type_): _description_
            key (_type_): _description_
        """
        obj = self._index[table].get(key)

        if obj:
            obj.is_deleted = True
            self.mark_dirty(table, obj)

    def _initialize_schema(self) -> None:
        """ _summary_ """
        for table in TABLE_MAP:

            table_name = table.name
            self.db_shirayume.execute(f"DESCRIBE {table_name}")
            
            rows = self.db_shirayume.fetchall()
            columns = [r["Field"] for r in rows]

            required = [
                r["Field"]
                for r in rows
                if (
                    r["Null"]=="NO"
                    and r["Default"] is None
                    and "auto_increment"
                    not in r["Extra"]
                )
            ]

            self._schema_cache[table_name]={
                "columns":columns,
                "required":required
            }

            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                function_name="database.database_manager.DatabaseManager._initialize_schema",
                description=f"Required fields for table {table_name}: {'/'.join(required)}"
            )

            pkeys = PRIMARY_KEYS[table]

            placeholders = ", ".join(["%s"]*len(columns))
            col_str = ", ".join(columns)

            update_str = ", ".join(
                f"{c}=VALUES({c})"
                for c in columns
                if c not in pkeys
            )

            delete_where = " AND ".join(f"{pk}=%s" for pk in pkeys)

            self._sql_cache[table_name]={
                "delete":
                f"""
                DELETE FROM {table_name}
                WHERE {delete_where}
                """,

                "upsert":
                f"""
                INSERT INTO {table_name}
                ({col_str})

                VALUES ({placeholders})

                ON DUPLICATE KEY UPDATE
                {update_str}
                """
            }


    def get_next_id(self, table: shared.Table) -> int:
        """
        Gets and increments the next available ID for an auto-increment table.
        """
        if table not in self._last_id_cache:
            self._last_id_cache[table] = 0
        self._last_id_cache[table] += 1
        return self._last_id_cache[table]


    def add_users(self, users: Union[List[models.User], models.User]) -> None:
        """
        Adds new users to the in-memory list efficiently.

        Args:
            users (Union[List[models.User], models.User]): A single user or a list of users to add.
        """
        self._add(shared.Table.users, users)

    def remove_users(self, user_ids: Union[List[int], int]) -> None:
        """
        Marks users as deleted in memory.

        Args:
            user_ids (Union[List[int], int]): A single user ID or list of user IDs to remove.
        """
        if isinstance(user_ids, int):
            user_ids = [user_ids]

        for user_id in user_ids:
            self._remove(shared.Table.users, user_id)


    def add_guilds(self, guilds: Union[List[models.Guild], models.Guild]) -> None:
        """
        Adds new guilds to the in-memory list efficiently.

        Args:
            guilds (Union[List[models.Guild], models.Guild]): A single guild or list of guilds.
        """
        self._add(shared.Table.guilds, guilds)

    def remove_guilds(self, guild_ids: Union[List[int], int]) -> None:
        """
        Marks guilds as deleted in memory.

        Args:
            guild_ids (Union[List[int], int]): Target guild ID(s) to remove.
        """
        if isinstance(guild_ids, int):
            guild_ids = [guild_ids]
        
        for guild_id in guild_ids:
            self._remove(shared.Table.guilds, guild_id)


    def add_user_guild_settings(self, user_guild_settings: Union[List[models.UserGuildSettings], models.UserGuildSettings]) -> None:
        """
        Adds user-guild settings to memory.

        Args:
            user_guild_settings (Union[List[models.UserGuildSettings], models.UserGuildSettings]): Settings to add.
        """
        self._add(shared.Table.user_guild_settings, user_guild_settings)

    def remove_user_guild_settings(self, user_id: int, guild_id: int) -> None:
        """
        Marks a specific user-guild setting as deleted.

        Args:
            user_id (int): ID of the user.
            guild_id (int): ID of the guild.
        """
        self._remove(shared.Table.user_guild_settings, (user_id, guild_id))

    def link_user_to_guild(self, user_id: int, guild_id: int) -> None:
        """
        Updates membership status or initializes a new link between user and guild.

        Args:
            user_id (int): ID of the user.
            guild_id (int): ID of the guild.
        """
        ugs = self._index[shared.Table.user_guild_settings].get((user_id, guild_id))

        if ugs:
            ugs.is_member = True
            ugs.is_deleted = False # just in case (normally we do NOT delete links between users and guilds to keep their old data intact)
            self.mark_dirty(shared.Table.user_guild_settings, ugs)
            return
        
        self.add_user_guild_settings(
            models.UserGuildSettings(
                user_id = user_id, guild_id = guild_id, joined_at = datetime.now(),
                last_interaction = datetime.now(), experience = 0, level = 0, custom_title = "",
                last_xp_message = datetime.now(), created_at = datetime.now(), updated_at = datetime.now(),
                is_member = True, is_dirty = True, is_deleted = False
            )
        )

    def unlink_user_from_guild(self, user_id: int, guild_id: int) -> None:
        """
        Sets a user's membership status in a guild to False.

        Args:
            user_id (int): ID of the user.
            guild_id (int): ID of the guild.
        """
        ugs = self._index[shared.Table.user_guild_settings].get((user_id, guild_id))

        if ugs and ugs.is_member:
            ugs.is_member = False
            self.mark_dirty(shared.Table.user_guild_settings, ugs)


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
        self._add(shared.Table.moderation_logs, moderation_logs)

    def remove_moderation_logs(self, mlog_ids: Union[List[int], int]) -> None:
        """
        Marks moderation logs as deleted.

        Args:
            mlog_ids (Union[List[int], int]): Target log ID(s).
        """
        if isinstance(mlog_ids, int):
            mlog_ids = [mlog_ids]

        for mlog_id in mlog_ids:
            self._remove(shared.Table.moderation_logs, mlog_id)


    def add_polls(self, polls: Union[List[models.Poll], models.Poll]) -> None:
        """
        Adds polls to memory.

        Args:
            polls (Union[List[models.Poll], models.Poll]): Polls to add.
        """
        self._add(shared.Table.polls, polls)

    def remove_polls(self, poll_ids: Union[List[int], int]) -> None:
        """
        Marks polls as deleted.

        Args:
            poll_ids (Union[List[int], int]): Target poll ID(s).
        """
        if isinstance(poll_ids, int):
            poll_ids = [poll_ids]

        for poll_id in poll_ids:
            self._remove(shared.Table.polls, poll_id)


    def add_user_economies(self, economies: Union[List[models.UserEconomy], models.UserEconomy]) -> None:
        """
        Adds user economy records to memory.

        Args:
            economies (Union[List[models.UserEconomy], models.UserEconomy]): Economy records to add.
        """
        self._add(shared.Table.user_economies, economies)

    def remove_user_economies(self, guild_id: int, user_id: int) -> None:
        """
        Marks an economy record as deleted.

        Args:
            guild_id (int): Target guild ID.
            user_id (int): Target user ID.
        """
        self._remove(shared.Table.user_economies, (guild_id, user_id))


    def add_shop_items(self, items: Union[List[models.ShopItem], models.ShopItem]) -> None:
        """
        Adds shop items to memory.

        Args:
            items (Union[List[models.ShopItem], models.ShopItem]): Shop items to add.
        """
        self._add(shared.Table.shop_items, items)

    def remove_shop_items(self, item_ids: Union[List[int], int]) -> None:
        """
        Marks shop items as deleted.

        Args:
            item_ids (Union[List[int], int]): Target item ID(s).
        """
        if isinstance(item_ids, int):
            item_ids = [item_ids]

        for item_id in item_ids:
            self._remove(shared.Table.shop_items, item_id)


    def add_global_shop_items(self, items: Union[List[models.GlobalShopItem], models.GlobalShopItem]) -> None:
        """
        _summary_

        Args:
            items (Union[List[models.GlobalShopItem], models.GlobalShopItem]): _description_
        """
        self._add(shared.Table.global_shop_items, items)

    def remove_global_shop_items(self, item_ids: Union[List[int], int]) -> None:
        """
        _summary_

        Args:
            item_ids (Union[List[int], int]): _description_

        Returns:
            _type_: _description_
        """
        if isinstance(item_ids, int): item_ids = [item_ids]
        for item_id in item_ids:
            self._remove(shared.Table.global_shop_items, item_id)


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
                
                required_fields = self._schema_cache[table_name]["required"]
                
                if all(field in kwargs for field in required_fields):
                    return model_class.from_dict(kwargs)
                    
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "database.DatabaseManager.initialize_database_model",
                description = f"Missing required fields for {table.name}"
            )

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
        for table in TABLE_MAP:
            for item in getattr(self, table.name):
                item.is_dirty = False
                item.is_deleted = False

            self._dirty[table].clear()

    async def database_commit(self)->None:
        """
        Efficiently executes all pending dirty state changes into the database.
        """
        try:
            pending_cleanup = []

            for table in TABLE_MAP:
                dirty_items = list(self._dirty[table])
                
                if not dirty_items:
                    continue

                delete_items=[]
                upsert_items=[]
                
                for item in dirty_items:

                    if item.is_deleted:
                        delete_items.append(item)
                    else:
                        upsert_items.append(item)

                if delete_items:
                    delete_data = [
                        tuple(getattr(item, pk) for pk in PRIMARY_KEYS[table])
                        for item in delete_items
                    ]

                    self.db_shirayume.executemany(
                        self._sql_cache[table.name]["delete"],
                        delete_data
                    )
                
                    # Remember for later cleanup
                    pending_cleanup.extend(
                        (table, obj)
                        for obj in delete_items
                    )

                if upsert_items:
                    columns = self._schema_cache[table.name]["columns"]
                    data = []

                    for item in upsert_items:
                        row = []

                        for col in columns:
                            val = getattr(item, col)

                            if isinstance(val, (shared.Action, shared.GlobalItemType)):
                                val = val.name
                            elif isinstance(val, (list, dict)):
                                val = json.dumps(val)

                            row.append(val)

                        data.append(tuple(row))

                    self.db_shirayume.executemany(
                        self._sql_cache[table.name]["upsert"],
                        data
                    )
                    
            self.db_connection.commit()

            # Execute after commit succeeded
            tables_to_rebuild = set()

            for table, obj in pending_cleanup:
                obj.is_dirty = False
                obj.is_deleted = False
                
                key = self._key(table, obj)
                self._index[table].pop(key, None)
                tables_to_rebuild.add(table)

            # Rebuild lists in a single O(n) pass for each affected table
            for table in tables_to_rebuild:
                table_name = table.name
                current_list = getattr(self, table_name)
                # Keep objects that are still in the index (not deleted)
                setattr(self, table_name, [x for x in current_list if self._key(table, x) in self._index[table]])

            for table in TABLE_MAP:
                for obj in self._dirty[table]:
                    obj.is_dirty = False

                self._dirty[table].clear()
            
        except mysql.connector.Error:
            self.db_connection.rollback()
            raise

    async def database_close(self) -> None:
        """
        Commits pending changes and gracefully closes the database connection.
        """
        try:
            await self.database_commit()  
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
        for table in TABLE_MAP:
            table_name = table.name
            helpers.custom_print(
                level = shared.LogLevel.DEBUG,
                function_name = "database.DatabaseManager.setup",
                description = f"Importing {table_name} from DB..."
            )
            
            DB_MANAGER.db_shirayume.execute(f"SELECT * FROM {table_name}")
            rows = DB_MANAGER.db_shirayume.fetchall()
            
            models_list = []
            for row in rows:
                model = DB_MANAGER.initialize_database_model(table, **row)
                if model:
                    models_list.append(model)
            
            DB_MANAGER._add(table, models_list, set_dirty=False)
            
            # Determine and cache the maximum ID for tables designated for auto-incrementing
            if table in AUTO_INCREMENT_FIELDS:
                auto_inc_col = AUTO_INCREMENT_FIELDS[table]
                max_id = max((getattr(model, auto_inc_col) for model in models_list), default=0)
                DB_MANAGER._last_id_cache[table] = max_id

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