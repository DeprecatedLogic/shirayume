from utils import shared, helpers
from database import database_manager

def add_moderation_logs(**kwargs):
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "add_moderation_logs",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
    model = DB_MANAGER.initialize_database_model(shared.Table.moderation_logs, **kwargs)
    DB_MANAGER.add_moderation_logs(model)
    return model
