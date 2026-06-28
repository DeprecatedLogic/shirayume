import os
import json
import mysql.connector
from typing import Union, List, Dict
from database import models
from datetime import datetime
from utils import shared, helpers

DB_MANAGER = None 

class DatabaseManager():

    def __init__(self, DB_HOST, DB_USER, DB_PASSWORD, DATABASE) -> None:
        self.guilds: List[models.Guild] = []
        self.users: List[models.User] = []
        self.user_guild_settings: List[models.UserGuildSettings] = []
        self.moderation_logs: List[models.ModerationLog] = []
        self.polls: List[models.Poll] = []

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

    def add_users(self, users: Union[List[models.User], models.User]):
        if isinstance(users, models.User):
            users = [users]
        for user in users:
            if not any(u.user_id == user.user_id for u in self.users):
                user.is_dirty = True
                user.is_deleted = False
                self.users.append(user)

    def remove_users(self, user_ids: Union[List[int], int]):
        if isinstance(user_ids, int):
            user_ids = [user_ids]
        for user_id in user_ids:
            user = next((u for u in self.users if u.user_id == user_id), None)
            if user:
                user.is_dirty = True
                user.is_deleted = True

    def get_users_mod_logs(self, user_ids: Union[List[int], int]) -> List[models.ModerationLog]:
        if isinstance(user_ids, int):
            user_ids = [user_ids]
        return [mlog for mlog in self.moderation_logs if mlog.user_id in user_ids]

    def add_guilds(self, guilds: Union[List[models.Guild], models.Guild]) -> None:
        if isinstance(guilds, models.Guild):
            guilds = [guilds]
        for guild in guilds:
            if not any(g.guild_id == guild.guild_id for g in self.guilds):
                guild.is_dirty = True
                guild.is_deleted = False
                self.guilds.append(guild)

    def remove_guilds(self, guild_ids: Union[List[int], int]) -> None:
        if isinstance(guild_ids, int):
            guild_ids = [guild_ids]
        for guild_id in guild_ids:
            guild = next((g for g in self.guilds if g.guild_id == guild_id), None)
            if guild:
                guild.is_dirty = True
                guild.is_deleted = True

    def add_user_guild_settings(self, user_guild_settings: Union[List[models.UserGuildSettings], models.UserGuildSettings]) -> None:
        if isinstance(user_guild_settings, models.UserGuildSettings):
            user_guild_settings = [user_guild_settings]
        for ug_settings in user_guild_settings:
            if not any(ugs.user_id == ug_settings.user_id and ugs.guild_id == ug_settings.guild_id for ugs in self.user_guild_settings):
                ug_settings.is_dirty = True
                ug_settings.is_deleted = False
                self.user_guild_settings.append(ug_settings)

    def remove_user_guild_settings(self, user_id: int, guild_id: int) -> None:
        user_guild_settings = next((ugs for ugs in self.user_guild_settings if ugs.user_id == user_id and ugs.guild_id == guild_id), None)
        if user_guild_settings:
            user_guild_settings.is_dirty = True
            user_guild_settings.is_deleted = True

    def link_user_to_guild(self, user_id: int, guild_id: int) -> None:

        for user_guild_settings in self.user_guild_settings:
            if user_guild_settings.user_id == user_id and user_guild_settings.guild_id == guild_id:
                user_guild_settings.is_member = True
                user_guild_settings.is_dirty = True
                user_guild_settings.is_deleted = False # in case it was set to True
                return

        # In case user_id-guild_id pair doesn't exist yet, initialize a new one
        user_guild_settings = models.UserGuildSettings(
            user_id = user_id,
            guild_id = guild_id,
            joined_at = datetime.now(),
            last_interaction = datetime.now(),
            experience = 0,
            level = 0,
            custom_title = "",
            last_xp_message = datetime.now(),
            created_at = datetime.now(),
            updated_at = datetime.now(),
            is_member = True,
            is_dirty = True,
            is_deleted = False
        )
        self.add_user_guild_settings(user_guild_settings)

    def unlink_user_from_guild(self, user_id: int, guild_id: int) -> None:
        for user_guild_settings in self.user_guild_settings:
            if (
                user_guild_settings.user_id == user_id and 
                user_guild_settings.guild_id == guild_id and 
                user_guild_settings.is_member
            ):
                user_guild_settings.is_member = False # Set the member flag to False but keep user's settings in case of recovery
                user_guild_settings.is_dirty = True
                break # user_id-guild_id is a unique pair

    def add_moderation_logs(self, moderation_logs: Union[List[models.ModerationLog], models.ModerationLog]) -> None:
        if isinstance(moderation_logs, models.ModerationLog):
            moderation_logs = [moderation_logs]
        for mlog in moderation_logs:
            if not any(l.mlog_id == mlog.mlog_id for l in self.moderation_logs):
                mlog.is_dirty = True
                mlog.is_deleted = False
                self.moderation_logs.append(mlog)

    def remove_moderation_logs(self, mlog_ids: Union[List[int], int]) -> None:
        if isinstance(mlog_ids, int):
            mlog_ids = [mlog_ids]
        for mlog_id in mlog_ids:
            mlog = next((l for l in self.moderation_logs if l.mlog_id == mlog_id), None)
            if mlog:
                self.moderation_logs.remove(mlog)
                mlog.is_dirty = True
                mlog.is_deleted = True

    def add_polls(self, polls: Union[List[models.Poll], models.Poll]) -> None:
        if isinstance(polls, models.Poll):
            polls = [polls]
        for poll in polls:
            if poll not in self.polls:
                poll.is_dirty = True
                poll.is_deleted = False
                self.polls.append(poll)

    def remove_polls(self, poll_ids: Union[List[int], int]) -> None:
        if isinstance(poll_ids, int):
            poll_ids = [poll_ids]
        for poll_id in poll_ids:
            poll = next((p for p in self.polls if p.poll_id == poll_id), None)
            if poll:
                poll.is_dirty = True
                poll.is_deleted = True

    def initialize_database_model(self, table: shared.Table, **kwargs) -> Union[models.User, models.Guild, models.UserGuildSettings, models.ModerationLog, None]:
        try:
            if table == shared.Table.users:
                if all(key in kwargs for key in [
                    "user_id",
                    "username",
                    "discriminator",
                    "avatar_url",
                    "is_bot",
                    "currency",
                    "created_at"
                ]):
                    return models.User.from_dict(kwargs)
            elif table == shared.Table.guilds:
                if all(key in kwargs for key in [
                    "guild_id",
                    "owner_id",
                    "name",
                    "icon_url",
                    "member_count",
                    "bot_count",
                    "is_available",
                    "welcome_channel",
                    "leave_channel",
                    "joined_at",
                    "created_at"
                ]):
                    return models.Guild.from_dict(kwargs)
            elif table == shared.Table.user_guild_settings:
                if all(key in kwargs for key in [
                    "user_id",
                    "guild_id",
                    "joined_at",
                    "last_interaction",
                    "experience",
                    "level",
                    "custom_title",
                    "last_xp_message",
                    "created_at",
                    "is_member"
                ]):
                    return models.UserGuildSettings.from_dict(kwargs)
            elif table == shared.Table.moderation_logs:
                if all(key in kwargs for key in [
                    "mlog_id",
                    "guild_id",
                    "user_id",
                    "moderator_id",
                    "action_type",
                    "reason",
                    "action_timestamp",
                    "duration_minutes",
                    "is_active",
                    "pardoned"
                ]):
                    return models.ModerationLog.from_dict(kwargs)
            elif table == shared.Table.polls:
                if all(k in kwargs for k in [
                    "poll_id",
                    "guild_id",
                    "creator_id",
                    "question",
                    "votes",
                    "is_active",
                    "created_at",
                    "updated_at",
                    "ends_at"
                ]):
                    return models.Poll.from_dict(kwargs)
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "database.DatabaseManager.initialize_database_model",
                description = f"Missing required fields for {table}"
            )
            return None
        except Exception as e:
            helpers.custom_print(
                level = shared.LogLevel.ERROR,
                function_name = "database.DatabaseManager.initialize_database_model",
                description = f"Error creating model for {table}: {e}"
            )
            return None

    def clean_flags(self) -> None:
        for user in self.users:
            user.is_dirty = False
            user.is_deleted = False
        for guild in self.guilds:
            guild.is_dirty = False
            guild.is_deleted = False
        for user_guild_settings in self.user_guild_settings:
            user_guild_settings.is_dirty = False
            user_guild_settings.is_deleted = False
        for mlog in self.moderation_logs:
            mlog.is_dirty = False
            mlog.is_deleted = False

    def database_commit(self) -> None:
        try:
            # Commit users
            for user in [u for u in self.users if u.is_dirty]:
                if user.is_deleted:
                    self.db_shirayume.execute("DELETE FROM users WHERE user_id=%s", (user.user_id,))
                else:
                    self.db_shirayume.execute(
                        """
                        INSERT INTO users (user_id, username, discriminator, avatar_url, is_bot, currency, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        username=%s, discriminator=%s, avatar_url=%s, is_bot=%s, currency=%s, updated_at=%s
                        """,
                        (
                            user.user_id, user.username, user.discriminator, user.avatar_url, user.is_bot, user.currency,
                            user.created_at, user.updated_at, user.username, user.discriminator, user.avatar_url, user.is_bot,
                            user.currency, user.updated_at
                        )
                    )

            # Commit guilds
            for guild in [g for g in self.guilds if g.is_dirty]:
                if guild.is_deleted:
                    self.db_shirayume.execute("DELETE FROM guilds WHERE guild_id=%s", (guild.guild_id,))
                else:
                    self.db_shirayume.execute(
                        """
                        INSERT INTO guilds (guild_id, owner_id, name, icon_url, member_count, bot_count, is_available, welcome_channel, leave_channel, joined_at, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        owner_id=%s, name=%s, icon_url=%s, member_count=%s, bot_count=%s, is_available=%s, welcome_channel=%s, leave_channel=%s, joined_at=%s, updated_at=%s
                        """,
                        (
                            guild.guild_id, guild.owner_id, guild.name, guild.icon_url, guild.member_count, guild.bot_count,
                            guild.is_available, guild.welcome_channel, guild.leave_channel, guild.joined_at, guild.created_at, guild.updated_at,
                            guild.owner_id, guild.name, guild.icon_url, guild.member_count, guild.bot_count, guild.is_available,
                            guild.welcome_channel, guild.joined_at, guild.updated_at
                        )
                    )

            # Commit user_guild_settings
            for user_guild_settings in [ugs for ugs in self.user_guild_settings if ugs.is_dirty]:
                if user_guild_settings.is_deleted:
                    self.db_shirayume.execute(
                        "DELETE FROM user_guild_settings WHERE user_id=%s AND guild_id=%s",
                        (user_guild_settings.user_id, user_guild_settings.guild_id)
                    )
                else:
                    self.db_shirayume.execute(
                        """
                        INSERT INTO user_guild_settings (user_id, guild_id, joined_at, last_interaction, experience, level, custom_title, last_xp_message, created_at, updated_at, is_member)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        joined_at=%s, last_interaction=%s, experience=%s, level=%s, custom_title=%s, last_xp_message=%s, updated_at=%s, is_member=%s
                        """,
                        (
                            user_guild_settings.user_id, user_guild_settings.guild_id, user_guild_settings.joined_at, user_guild_settings.last_interaction, user_guild_settings.experience,
                            user_guild_settings.level, user_guild_settings.custom_title, user_guild_settings.last_xp_message, user_guild_settings.created_at, user_guild_settings.updated_at,
                            user_guild_settings.is_member, user_guild_settings.joined_at, user_guild_settings.last_interaction, user_guild_settings.experience, user_guild_settings.level,
                            user_guild_settings.custom_title, user_guild_settings.last_xp_message, user_guild_settings.updated_at, user_guild_settings.is_member
                        )
                    )

            # Commit moderation_logs
            for mlog in [l for l in self.moderation_logs if l.is_dirty]:
                if mlog.is_deleted:
                    self.db_shirayume.execute("DELETE FROM moderation_logs WHERE mlog_id=%s", (mlog.mlog_id,))
                else:
                    self.db_shirayume.execute(
                        """
                        INSERT INTO moderation_logs (mlog_id, guild_id, user_id, moderator_id, action_type, reason, action_timestamp, duration_minutes, is_active, pardoned)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        guild_id=%s, user_id=%s, moderator_id=%s, action_type=%s, reason=%s, action_timestamp=%s, duration_minutes=%s, is_active=%s, pardoned=%s
                        """,
                        (
                            mlog.mlog_id, mlog.guild_id, mlog.user_id, mlog.moderator_id, mlog.action_type.name, mlog.reason,
                            mlog.action_timestamp, mlog.duration_minutes, mlog.is_active, mlog.pardoned,
                            mlog.guild_id, mlog.user_id, mlog.moderator_id, mlog.action_type.name, mlog.reason,
                            mlog.action_timestamp, mlog.duration_minutes, mlog.is_active, mlog.pardoned
                        )
                    )

            for poll in [p for p in self.polls if p.is_dirty]:
                if poll.is_deleted:
                    self.db_shirayume.execute("DELETE FROM polls WHERE poll_id=%s", (poll.poll_id,))
                else:
                    self.db_shirayume.execute(
                        """
                        INSERT INTO polls (poll_id, guild_id, creator_id, question, votes, is_active, created_at, updated_at, ends_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        guild_id=%s, creator_id=%s, question=%s, votes=%s, is_active=%s, updated_at=%s
                        """,
                        (
                            poll.poll_id, poll.guild_id, poll.creator_id, poll.question, json.dumps(poll.votes),
                            poll.is_active, poll.created_at, poll.updated_at, poll.ends_at, poll.guild_id, poll.creator_id,
                            poll.question, json.dumps(poll.votes), poll.is_active, poll.updated_at
                        )
                    )

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
        try:
            self.database_commit()  # Commit any remaining dirty objects
            self.db_shirayume.close()
            self.db_connection.close()
        except mysql.connector.Error as e:
            helpers.custom_print(
                level = shared.LogLevel.CRITICAL,
                function_name = "database.DatabaseManager.database_close",
                description = f"Failed to close database connection: {e}"
            )
            raise

def setup(DB_HOST, DB_USER, DB_PASSWORD, DATABASE):
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
        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"Importing users from DB..."
        )
        DB_MANAGER.db_shirayume.execute(f"SELECT * FROM {shared.Table.users.name}")
        users = []
        while True:
            user = DB_MANAGER.db_shirayume.fetchone()
            if not user:
                break
            model = DB_MANAGER.initialize_database_model(shared.Table.users, **user)
            if model:
                users.append(model)
        DB_MANAGER.add_users(users)
        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"DB users imported"
        )

        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"Importing guilds from DB..."
        )
        DB_MANAGER.db_shirayume.execute(f"SELECT * FROM {shared.Table.guilds.name}")
        guilds = []
        while True:
            guild = DB_MANAGER.db_shirayume.fetchone()
            if not guild:
                break
            model = DB_MANAGER.initialize_database_model(shared.Table.guilds, **guild)
            guilds.append(model)
        DB_MANAGER.add_guilds(guilds)
        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"DB guilds imported"
        )

        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"Importing user-guild settings from DB..."
        )
        DB_MANAGER.db_shirayume.execute(f"SELECT * FROM {shared.Table.user_guild_settings.name}")
        user_guild_settings = []
        while True:
            ug_settings = DB_MANAGER.db_shirayume.fetchone()
            if not ug_settings:
                break
            model = DB_MANAGER.initialize_database_model(shared.Table.user_guild_settings, **ug_settings)
            user_guild_settings.append(model)
        DB_MANAGER.add_user_guild_settings(user_guild_settings)
        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"DB user-guild settings imported"
        )

        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"Importing moderation logs from DB..."
        )
        DB_MANAGER.db_shirayume.execute(f"SELECT * FROM {shared.Table.moderation_logs.name}")
        moderation_logs = []
        while True:
            moderation_log = DB_MANAGER.db_shirayume.fetchone()
            if not moderation_log:
                break
            model = DB_MANAGER.initialize_database_model(shared.Table.moderation_logs, **moderation_log)
            moderation_logs.append(model)
        DB_MANAGER.add_moderation_logs(moderation_logs)
        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"DB moderation logs imported"
        )

        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"Importing polls from DB..."
        )
        DB_MANAGER.db_shirayume.execute(f"SELECT * FROM {shared.Table.polls.name}")
        polls = []
        while True:
            poll = DB_MANAGER.db_shirayume.fetchone()
            if not poll:
                break
            model = DB_MANAGER.initialize_database_model(shared.Table.polls, **poll)
            polls.append(model)
        DB_MANAGER.add_polls(polls)
        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "database.DatabaseManager.setup",
            description = f"DB polls imported"
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