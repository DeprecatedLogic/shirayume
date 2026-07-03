from utils import shared, helpers
from database import models
from database import database_manager
from typing import Optional

def add_moderation_logs(**kwargs) -> Optional[models.ModerationLog]:
    """
    _summary_

    Raises:
        RuntimeError: _description_

    Returns:
        Optional[models.ModerationLog]: _description_
    """
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "add_moderation_logs",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")

    model = DB_MANAGER.initialize_database_model(shared.Table.moderation_logs, **kwargs)
    DB_MANAGER.add_moderation_logs(model)
    
    return model
