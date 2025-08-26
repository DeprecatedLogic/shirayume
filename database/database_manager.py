import os
import mysql.connector
import mysql.connector.cursor
import mysql.connector.cursor_cext
import dotenv
import models
from utils import shared

if not dotenv.load_dotenv(dotenv_path = dotenv.find_dotenv(filename = ".env")):
    print("[ERROR] No environment variables set...")
    exit()

# Debugging output
print(
    os.environ["DB_HOST"],
    os.environ["DB_USER"],
    os.environ["DB_PASSWORD"],
    os.environ["DB_DATABASE"]
)

class ChangeData():
    def __init__(self, function_name: str, **params_values):
        self.name = function_name
        self.parameters_values = params_values

class Database_manager():

    def __init__(self,
        guilds: list[models.Guild],
        users: list[models.User],
        user_guild_settings: list[models.User_guild_settings],
        moderation_logs: list[models.Moderation_log]
    ) -> None:
        self.changes: list[ChangeData] = [] # commit only these changes to the database
        self.guilds = guilds
        self.users = users
        self.user_guild_settings = user_guild_settings
        self.moderation_logs = moderation_logs

        self.db_connection = mysql.connector.connect(
            host = os.environ["DB_HOST"],
            user = os.environ["DB_USER"],
            password = os.environ["DB_PASSWORD"],
            database = os.environ["DB_DATABASE"]
        )

        self.db_shirayume = self.db_connection.cursor(
            cursor_class = mysql.connector.cursor_cext.CMySQLCursorDict
        )

def add_users(self, users: list[models.User]):
    pass

def remove_users(self, user_ids: list[int]):
    pass

def get_users_mod_logs(self, user_ids: list[int]):
    pass

def add_guilds(self, guilds: list[models.Guild]):
    pass

def remove_guild(self, guild_ids: list[int]):
    pass

def link_user_to_guild(self, user_id: int, guild_id: int):
    pass

def unlink_user_from_guild(self, user_id: int, guild_id: int):
    pass

def add_moderation_logs(self, moderation_logs: list[models.ModerationLog] | models.ModerationLog):
    pass

def remove_moderation_logs(self, mlog_id: int):
    pass

def initialize_database_model(table: shared.Table, **kwargs):
    pass

def clean_changes(self) -> bool:
    """ Cleans the changes list. """
    return False # temporary value

def database_commit(self):
    pass

def database_close(self):
    pass
