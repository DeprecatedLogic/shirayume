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
    db_manager = database_manager.DB_MANAGER
    if not db_manager:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "add_moderation_logs",
            description = f"DB_MANAGER ({db_manager}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")

    next_id = db_manager.get_next_id(shared.Table.moderation_logs)

    model = db_manager.initialize_database_model(
        shared.Table.moderation_logs,
        mlog_id=next_id,
        **kwargs
    )
    db_manager.add_moderation_logs(model)
    
    return model
