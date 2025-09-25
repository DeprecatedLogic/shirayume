import os
import mysql.connector
import mysql.connector.cursor_cext
import models
from utils import shared

DB_MANAGER: "DatabaseManager" | None = None

class DatabaseManager():

    def __init__(self) -> None:
        self.guilds: list[models.Guild] = []
        self.users: list[models.User] = []
        self.user_guild_settings: list[models.UserGuildSettings] = []
        self.moderation_logs: list[models.ModerationLog] = []

        self.db_connection = mysql.connector.connect(
            host = os.environ["DB_HOST"],
            user = os.environ["DB_USER"],
            password = os.environ["DB_PASSWORD"],
            database = os.environ["DATABASE"]
        )

        self.db_shirayume = self.db_connection.cursor(
            cursor_class = mysql.connector.cursor_cext.CMySQLCursorDict
        )

    def add_users(self, users: list[models.User] | models.User):
        if type(users) == models.User:
            self.users.append
        else:
            self.users.extend(users)

    def remove_users(self, user_ids: list[int] | int):
        if type(user_ids) == int:
            for user in self.users:
                if user.user_id == user_ids:
                    self.users.remove(user)
        else:
            for user_id in user_ids:
                for user in self.users:
                    if user.user_id == user_id:
                        self.users.remove(user)

    def get_users_mod_logs(self, user_ids: list[int] | int):
        pass

    def add_guilds(self, guilds: list[models.Guild] | models.Guild):
        pass

    def remove_guilds(self, guild_ids: list[int] | int):
        pass

    def import_user_guild_settings(self, user_guild_settings: list[models.UserGuildSettings] | models.UserGuildSettings):
        pass

    def remove_user_guild_settings(self, user_id: int, guild_id: int):
        pass

    def link_user_to_guild(self, user_id: int, guild_id: int):
        pass

    def unlink_user_from_guild(self, user_id: int, guild_id: int):
        pass

    def add_moderation_logs(self, moderation_logs: list[models.ModerationLog] | models.ModerationLog):
        pass

    def remove_moderation_logs(self, mlog_ids: list[int] | int):
        pass

    def initialize_database_model(table: shared.Table, **kwargs):
        #todo: maybe make some params optional (default values)
        if table == shared.Table.user:
            if (
                kwargs.get("user_id", False)
                and kwargs.get("username", False)
                and kwargs.get("discriminator", False)
                and kwargs.get("avatar_url", False)
                and kwargs.get("is_bot", False)
                and kwargs.get("currency", False)
                and kwargs.get("created_at", False)
                and kwargs.get("updated_at", False)
                and kwargs.get("is_dirty", False)
            ):
                models.User.from_dict(kwargs)
            else:
                # print error ?
                pass
        elif table == shared.Table.guild:
            if (
                kwargs.get("guild_id", False)
                and kwargs.get("owner_id", False)
                and kwargs.get("name", False)
                and kwargs.get("icon_url", False)
                and kwargs.get("member_count", False)
                and kwargs.get("bot_count", False)
                and kwargs.get("is_available", False)
                and kwargs.get("welcome_channel", False)
                and kwargs.get("joined_at", False)
                and kwargs.get("created_at", False)
                and kwargs.get("updated_at", False)
                and kwargs.get("is_dirty", False)
            ):
                models.Guild.from_dict(kwargs)
            else:
                # print error ?
                pass
        elif table == shared.Table.user_guild_settings:
            if (
                kwargs.get("user_id", False)
                and kwargs.get("guild_id", False)
                and kwargs.get("joined_at", False)
                and kwargs.get("last_interaction", False)
                and kwargs.get("experience", False)
                and kwargs.get("level", False)
                and kwargs.get("custom_title", False)
                and kwargs.get("last_xp_message", False)
                and kwargs.get("created_at", False)
                and kwargs.get("updated_at", False)
                and kwargs.get("is_member", False)
                and kwargs.get("is_dirty", False)
            ):
                models.UserGuildSettings.from_dict(kwargs)
            else:
                # print error ?
                pass
        elif table == shared.Table.moderation_log:
            if (
                kwargs.get("mlog_id", False)
                and kwargs.get("guild_id", False)
                and kwargs.get("user_id", False)
                and kwargs.get("moderator_id", False)
                and kwargs.get("action_type", False)
                and kwargs.get("reason", False)
                and kwargs.get("action_timestamp", False)
                and kwargs.get("duration_minutes", False)
                and kwargs.get("is_active", False)
                and kwargs.get("pardoned", False)
                and kwargs.get("is_dirty", False)
            ):
                models.UserGuildSettings.from_dict(kwargs)
            else:
                # print error ?
                pass

    def clean_flags(self):
        pass

    def database_commit(self):
        pass

    def database_close(self):
        pass

def setup():
    DB_MANAGER = DatabaseManager()

    DB_MANAGER.db_shirayume.execute("SELECT * FROM user")
    users = []
    while True:
        user = DB_MANAGER.db_shirayume.fetchone()
        if not user: break
        users.append(DB_MANAGER.initialize_database_model(shared.Table.user))
    DB_MANAGER.add_users(users)

    DB_MANAGER.db_shirayume.execute("SELECT * FROM guild")
    guilds = []
    while True:
        guild = DB_MANAGER.db_shirayume.fetchone()
        if not guild: break
        guilds.append(DB_MANAGER.initialize_database_model(shared.Table.guild))
    DB_MANAGER.add_guilds(guilds)

    DB_MANAGER.db_shirayume.execute("SELECT * FROM user_guild_settings")
    user_guild_settings = []
    while True:
        ug_settings = DB_MANAGER.db_shirayume.fetchone()
        if not ug_settings: break
        user_guild_settings.append(DB_MANAGER.initialize_database_model(shared.Table.user_guild_settings))
    DB_MANAGER.import_user_guild_settings(user_guild_settings)

    DB_MANAGER.db_shirayume.execute("SELECT * FROM moderation_logs")
    moderation_logs = []
    while True:
        moderation_log = DB_MANAGER.db_shirayume.fetchone()
        if not moderation_log: break
        moderation_logs.append(DB_MANAGER.initialize_database_model(shared.Table.moderation_log))
    DB_MANAGER.add_moderation_logs(moderation_logs)