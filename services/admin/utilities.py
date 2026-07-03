from utils import shared, helpers
from database import database_manager

def add_admin_log(**kwargs):
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "add_admin_log",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
    
    model = None #DB_MANAGER.initialize_database_model(shared.Table.admin_log, **kwargs)
    #DB_MANAGER.add_admin_log(model)
    return model
