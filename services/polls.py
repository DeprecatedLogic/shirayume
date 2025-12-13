from utils import shared, helpers
from database import database_manager, models
import datetime
from typing import Union, List
import asyncio

async def create_poll(**kwargs) -> Union[models.Poll, None]:
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "services.polls.create_poll",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")
    
    opts = kwargs.get("votes", None).keys()
    if not opts or len(opts) < 2:
        helpers.custom_print(
            level = shared.LogLevel.ERROR,
            function_name = "services.polls.create_poll",
            description = f"Invalid options provided: {opts}"
        )
        return None
    
    model: models.Poll = DB_MANAGER.initialize_database_model(shared.Table.polls, **kwargs)
    
    if not model:
        helpers.custom_print(
            level = shared.LogLevel.ERROR,
            function_name = "services.polls.create_poll",
            description = f"Failed to initialize model ({model})."
        )
        raise RuntimeError("Database model not initialized")
        
    DB_MANAGER.add_polls(model)
    return model

async def vote_poll(poll_id: int, guild_id: int, user_id: int, option: str) -> bool:
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "services.polls.vote_poll",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")
    
    poll = next((
        p for p in DB_MANAGER.polls
        if p.poll_id == poll_id and p.guild_id == guild_id and
        p.is_active and not p.is_deleted
    ), None)
    
    if not poll:
        return False
    
    found_voter = False
    for opt, voters in poll.votes.items():
        for voter in voters:
            if voter == user_id:
                poll.votes[opt].remove(user_id)
                found_voter = True
                break
        if found_voter:
            break

    # If user passed numeric, treat it as 1-based index
    if option.isdigit():
        idx = int(option) - 1
        if idx < 0 or idx >= len(poll.votes.keys()):
            return False
        option = tuple(poll.votes.keys())[idx]

    poll.votes[option].append(user_id)
    poll.updated_at = datetime.datetime.now()
    poll.is_dirty = True
    return True

async def cancel_vote_poll(poll_id: int, guild_id: int, user_id: int) -> bool:
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "services.polls.cancel_vote_poll",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")
    
    poll = next((
        p for p in DB_MANAGER.polls
        if p.poll_id == poll_id and p.guild_id == guild_id and
        p.is_active and not p.is_deleted
    ), None)
    
    if not poll:
        return False
    
    found_voter = False
    for opt, voters in poll.votes.items():
        for voter in voters:
            if voter == user_id:
                poll.votes[opt].remove(user_id)
                found_voter = True
                break
        if found_voter:
            poll.updated_at = datetime.datetime.now()
            poll.is_dirty = True
            break
        
    return found_voter

async def end_poll(poll_id: int, creator_id: int, guild_id: int) -> bool:
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "services.polls.end_poll",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")
    
    poll = next((
        p for p in DB_MANAGER.polls
        if p.poll_id == poll_id and p.guild_id == guild_id and
        p.creator_id == creator_id and
        p.is_active and not p.is_deleted
    ), None)
    
    if not poll:
        poll = DB_MANAGER.polls[0]
        helpers.custom_print(
            level = shared.LogLevel.DEBUG,
            function_name = "services.polls.end_poll",
            description = f"First poll peek:\nPoll ID: {poll.poll_id}\nCreator ID: {poll.creator_id}\nGuild ID: {poll.guild_id}\nIs Deleted: {poll.is_deleted}"
        )
        return False
    
    poll.is_active = False
    poll.updated_at = datetime.datetime.now()
    poll.is_dirty = True
    return True

async def get_active_polls(user_id: int, guild_id: int) -> Union[List[models.Poll], None]:
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "services.polls.get_active_polls",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")
    
    active_polls = [
        p for p in DB_MANAGER.polls
        if p.is_active and not p.is_deleted and
        p.creator_id == user_id and p.guild_id == guild_id
    ]
    if not active_polls:
        return None
    
    return active_polls

async def _sleep_and_finish_poll(poll_id: int, guild_id: int, ends_at: datetime.datetime):
    DB_MANAGER = database_manager.DB_MANAGER
    if not DB_MANAGER:
        helpers.custom_print(
            level = shared.LogLevel.CRITICAL,
            function_name = "services.polls.get_active_polls",
            description = f"DB_MANAGER ({DB_MANAGER}) has not been initialized"
        )
        raise RuntimeError("DB_MANAGER not initialized")
    
    poll = next((
        p for p in DB_MANAGER.polls
        if p.poll_id == poll_id and guild_id == guild_id and
        p.is_active and not p.is_deleted
    ), None)

    if not poll:
        return
    
    now = datetime.datetime.now()
    delay = (ends_at - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    
    await end_poll(poll_id = poll_id, creator_id = poll.creator_id, guild_id = guild_id)

    user = next((
        u for u in DB_MANAGER.users
        if u.user_id == poll.creator_id
    ), None)
    helpers.custom_print(
        level = shared.LogLevel.DEBUG,
        function_name = "services.polls._sleep_and_finish_poll",
        description = f"User {user.username if user else poll.creator_id}'s poll ({poll_id}) in Guild ID {guild_id} has ended automatically"
    )