from utils import shared, helpers
from database import database_manager, models
from typing import Optional

def add_moderation_logs(**kwargs) -> Optional[models.ModerationLog]:
    """
    Generates a tracking ID and records an audit log entry for moderation actions (warns, mutes, kicks, bans).

    Args:
        **kwargs: Expected to provide parameters required by the `ModerationLog` model initialization schema:  
                  - guild_id (int): Server where the action took place.  
                  - moderator_id (int): User ID executing the action.  
                  - user_id (int): Targeted member facing the moderation action.  
                  - action (shared.Action): Type enum representing the enforcement measure.  
                  - reason (str): Background context justifying the moderation choice.

    Returns:
        Optional[models.ModerationLog]: The generated log model row tracking state data.
    """
    # Fetch next safe primary key identifier sequence
    next_id = database_manager.DB_MANAGER.get_next_id(shared.Table.moderation_logs)

    model = database_manager.DB_MANAGER.initialize_database_model(
        shared.Table.moderation_logs,
        mlog_id=next_id,
        **kwargs
    )
    database_manager.DB_MANAGER.add_moderation_logs(model)
    
    helpers.custom_print(
        level=shared.LogLevel.INFO,
        description=f"Moderation log entry with ID {next_id} added successfully for user ID {kwargs.get('user_id', 'Unknown')}."
    )
    return model