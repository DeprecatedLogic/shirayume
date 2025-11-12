from utils import shared, helpers
from database import database_manager, models
from datetime import datetime

DB_MANAGER = database_manager.DB_MANAGER

async def create_poll(**kwargs):
    if not DB_MANAGER:
        helpers.custom_print(
            level=shared.LogLevel.CRITICAL,
            function_name="add_poll",
            description=f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")
    model = DB_MANAGER.initialize_database_model(shared.Table.polls, **kwargs)
    DB_MANAGER.add_polls(model)
    return model

async def vote_poll(poll_id: int, guild_id: int, user_id: int, option: str) -> bool:
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "vote_poll",
            description = "DB_MANAGER not initialized"
        )
        return False
    poll = next((
        p for p in DB_MANAGER.polls
        if p.poll_id == poll_id and
        p.guild_id == guild_id and
        p.creator_id == user_id and
        p.is_active and not
        p.is_deleted
        ), None)
    if not poll or option not in poll.options:
        return False
    poll.votes[option] = poll.votes.get(option, 0) + 1
    poll.updated_at = datetime.now()
    poll.is_dirty = True
    return True

async def close_poll(poll_id: int, guild_id: int, creator_id: int) -> bool:
    if not DB_MANAGER:
        helpers.custom_print(
            level =shared.LogLevel.CRITICAL,
            function_name ="close_poll",
            description ="DB_MANAGER not initialized"
        )
        return False
    poll = next((
        p for p in DB_MANAGER.polls
        if p.poll_id == poll_id and
        p.guild_id == guild_id and
        p.creator_id == creator_id and not
        p.is_deleted
        ), None)
    if not poll:
        return False
    poll.is_active = False
    poll.updated_at = datetime.now()
    poll.is_dirty = True
    return True