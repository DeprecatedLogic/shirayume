from utils import shared, helpers
from database import database_manager, models
import datetime
from typing import Any, Optional, List
import asyncio

ACTIVE_POLLS: dict[int, list[models.Poll]] = {}

def _find_poll(
    poll_id: int,
    guild_id: Optional[int] = None,
    creator_id: Optional[int] = None,
    active_only: bool = False,
) -> Optional[models.Poll]:
    """
    Retrieves a poll matching the supplied filtering criteria.

    Args:
        poll_id (int): The unique identifier of the poll.
        guild_id (Optional[int]): Restricts the search to a specific guild if provided.
        creator_id (Optional[int]): Restricts the search to polls created by a specific user if provided.
        active_only (bool): Whether inactive or deleted polls should be excluded. Default is False.

    Returns:
        Optional[models.Poll]: The matching poll if found, otherwise None.
    """
    return next(
        (
            poll
            for poll in database_manager.DB_MANAGER.polls
            if poll.poll_id == poll_id
            and (guild_id is None or poll.guild_id == guild_id)
            and (creator_id is None or poll.creator_id == creator_id)
            and (not active_only or (poll.is_active and not poll.is_deleted))
        ),
        None,
    )

def is_limit_reached(user_id: int) -> bool:
    """
    Checks whether a user has reached the configured limit of simultaneously active polls.

    Args:
        user_id (int): The unique Discord snowflake ID of the poll creator.

    Returns:
        bool: True if the user cannot create another active poll, otherwise False.
    """
    global ACTIVE_POLLS
    active_polls = ACTIVE_POLLS.get(user_id, [])
    max_active = shared.GLOBAL_CONFIG["features"]["polls"]["max_active_per_user"]
    
    if len(active_polls) < max_active:
        return False

    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description=f"Active polls limit reached for user (ID: {user_id})."
    )
    return True

def poll_modified(poll: models.Poll) -> None:
    """
    Creates a new poll, stores it in the database manager, and registers it in
    the active in-memory cache.

    Args:
        guild_id (int): The unique Discord snowflake ID of the guild.
        creator_id (int): The unique Discord snowflake ID of the poll creator.
        question (str): The poll question shown to users.
        votes (dict[str, list[int]]): Mapping of option names to voter ID lists.
        ends_at (datetime.datetime): Timestamp at which the poll automatically ends.
        message_id (int): Discord message ID associated with the poll.
        channel_id (int): Discord channel ID containing the poll.
        is_active (bool): Whether the poll is immediately active.
        created_at (datetime.datetime): Poll creation timestamp.
        updated_at (datetime.datetime): Last modification timestamp.
        is_dirty (bool): Whether the poll should immediately be persisted.

    Returns:
        Optional[models.Poll]: The newly created poll model if successful,
        otherwise None.
    """
    database_manager.DB_MANAGER.mark_dirty(shared.Table.polls, poll)

async def create_poll(**kwargs) -> Optional[models.Poll]:
    """
    Builds, registers, and commits a structured ballot object into active tracking memory.
    """
    opts = kwargs.get("votes", {}).keys()
    if not opts or len(opts) < 2:
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=(
                f"Poll creation rejected: expected at least 2 options, "
                f"received {len(opts)}."
            )
        )
        return None
    
    # Allocate the next persistent poll ID before constructing the database model
    next_id: int = database_manager.DB_MANAGER.get_next_id(shared.Table.polls)
    
    guild_id: int = kwargs.get("guild_id")
    creator_id: int = kwargs.get("creator_id")
    message_id: int = kwargs.get("message_id", -1)
    channel_id: int = kwargs.get("channel_id", -1)
    question: str = kwargs.get("question")
    votes: dict[str, list[int]] = kwargs.get("votes")
    is_active: bool = kwargs.get("is_active", True)
    is_anonymous: bool = kwargs.get("is_anonymous", True) 
    created_at: datetime.datetime = kwargs.get("created_at", datetime.datetime.now())
    updated_at: datetime.datetime = kwargs.get("updated_at", datetime.datetime.now())
    ends_at: datetime.datetime = kwargs.get("ends_at")
    is_dirty: bool = kwargs.get("is_dirty", True)

    model: models.Poll = database_manager.DB_MANAGER.initialize_database_model(
        shared.Table.polls,
        poll_id=next_id,
        guild_id=guild_id,
        creator_id=creator_id,
        message_id=message_id,
        channel_id=channel_id,
        question=question,
        votes=votes,
        is_active=is_active,
        is_anonymous=is_anonymous,
        created_at=created_at,
        updated_at=updated_at,
        ends_at=ends_at,
        is_dirty=is_dirty
    )
    
    if not model:
        helpers.custom_print(
            level=shared.LogLevel.ERROR,
            description="Failed to initialize poll model."
        )
        return
        
    database_manager.DB_MANAGER.add_polls(model)
    
    # Keep an in-memory index of active polls for quick per-user lookups
    ACTIVE_POLLS.setdefault(creator_id, [])
    ACTIVE_POLLS[creator_id].append(model)
    
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description=(
            f"Created poll ID {next_id} "
            f"(guild={guild_id}, creator={creator_id})."
        )
    )
    return model

async def vote_poll(poll_id: int, guild_id: int, user_id: int, option: str) -> bool:
    """
    Registers or updates a user's vote for an active poll.

    If the user has already voted, their previous vote is removed before the
    new one is recorded, ensuring that only one active vote exists per user.

    Args:
        poll_id (int): The unique identifier of the target poll.
        guild_id (int): The unique Discord snowflake ID of the guild.
        user_id (int): The unique Discord snowflake ID of the voter.
        option (str): The option label or 1-based option index selected by the user.

    Returns:
        bool: True if the vote was successfully recorded, otherwise False.
    """
    poll: Optional[models.Poll] = _find_poll(
        poll_id=poll_id,
        guild_id=guild_id,
        active_only=True
    )
    
    if not poll:
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=(
                f"Vote rejected: poll {poll_id} is not active "
                f"or does not exist in guild {guild_id}."
            )
        )
        return False
    
    if option.isdigit():
        # Allow users to specify options using a 1-based index
        index = int(option) - 1
        options_keys = list(poll.votes.keys())
        if index < 0 or index >= len(options_keys):
            helpers.custom_print(
                level=shared.LogLevel.DEBUG,
                description=(
                    f"Vote rejected: option index '{option}' "
                    f"is outside the valid range for poll {poll_id}."
                )
            )
            return False
        option = options_keys[index]

    if option not in poll.votes:
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=(
                f"Vote rejected: '{option}' is not a valid option "
                f"for poll {poll_id}."
            )
        )
        return False

    # Remove any previous vote so each user can only vote once
    for opt in poll.votes:
        if user_id in poll.votes[opt]:
            poll.votes[opt].remove(user_id)
        
    poll.votes[option].append(user_id)
    poll.updated_at = datetime.datetime.now()
    database_manager.DB_MANAGER.mark_dirty(shared.Table.polls, poll)
    
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description=(
            f"User {user_id} voted for '{option}' "
            f"in poll {poll_id}."
        )
    )
    return True

async def cancel_vote_poll(poll: models.Poll, user_id: int) -> dict:
    """
    Removes a user's existing vote from an active poll.

    Args:
        poll_id (int): The unique identifier of the target poll.
        user_id (int): The unique Discord snowflake ID of the voter.

    Returns:
        dict: {  
            "success": bool     # if poll exists and is active
            "has_voted": bool   # if the user has voted
        }
    """
    if not poll or not poll.is_active:
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=(
                f"Vote cancellation rejected: poll {poll.poll_id} "
                f"is not active or does not exist."
            )
        )
        return {"success": False}
    
    # Search every option in case the stored vote needs to be removed
    found_voter = False
    for opt in poll.votes:
        if user_id in poll.votes[opt]:
            poll.votes[opt].remove(user_id)
            found_voter = True
        
    if found_voter:
        poll.updated_at = datetime.datetime.now()
        database_manager.DB_MANAGER.mark_dirty(shared.Table.polls, poll)
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=f"User ID {user_id} canceled their vote on poll ID {poll.poll_id}."
        )
    else:
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=(
                f"Vote cancellation ignored: user {user_id} "
                f"had not voted in poll {poll.poll_id}."
            )
        )
        
    return {"success": True, "has_voted": found_voter}

async def end_poll(poll_id: int, creator_id: int, guild_id: int) -> bool:
    """
    Manually closes an active poll created by the specified user.

    The poll is marked as inactive, scheduled for persistence, and removed
    from the active in-memory cache.

    Args:
        poll_id (int): The unique identifier of the poll.
        creator_id (int): The unique Discord snowflake ID of the poll creator.
        guild_id (int): The unique Discord snowflake ID of the guild.

    Returns:
        bool: True if the poll was successfully closed, otherwise False.
    """
    poll: Optional[models.Poll] = _find_poll(
        poll_id=poll_id,
        guild_id=guild_id,
        creator_id=creator_id,
        active_only=True
    )
    
    if not poll:
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=(
                f"Failed to end poll {poll_id}: "
                f"no matching active poll owned by user {creator_id}."
            )
        )
        return False
        
    poll.is_active = False
    poll.updated_at = datetime.datetime.now()
    database_manager.DB_MANAGER.mark_dirty(shared.Table.polls, poll)
    
    # Remove the poll from the active cache so future limit checks stay accurate
    active_list: list[models.Poll] = ACTIVE_POLLS.get(creator_id, [])
    for p in active_list:
        if p.poll_id == poll_id:         
            active_list.remove(p)
            break
            
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description=f"Poll {poll_id} was manually closed by creator {creator_id}."
    )
    return True

async def get_poll(poll_id: int) -> Optional[models.Poll]:
    """
    Retrieves a poll by its unique identifier.

    Args:
        poll_id (int): The unique identifier of the poll.

    Returns:
        Optional[models.Poll]: The matching poll if found, otherwise None.
    """
    return _find_poll(poll_id)

async def get_active_polls(user_id: int, guild_id: int) -> Optional[List[models.Poll]]:
    """
    Retrieves all active polls created by a specific user within a guild.

    Args:
        user_id (int): The unique Discord snowflake ID of the poll creator.
        guild_id (int): The unique Discord snowflake ID of the guild.

    Returns:
        Optional[list[models.Poll]]: A list of active polls if any exist,
        otherwise None.
    """
    active_polls: list[models.Poll] = [
        p for p in database_manager.DB_MANAGER.polls
        if p.is_active and not p.is_deleted and
        p.creator_id == user_id and p.guild_id == guild_id
    ]
    if not active_polls:
        return None
    
    return active_polls

async def sleep_and_close_poll(poll: models.Poll) -> None:
    """
    Sleeps until a poll reaches its expiration time, then automatically closes it.

    Once the timeout expires, the poll is marked as inactive, removed from the
    active cache, and persisted for database synchronization.

    Args:
        poll (models.Poll): The poll object.
    """
    # Wait until the scheduled expiration time before processing the poll
    delay: float = (poll.ends_at - datetime.datetime.now()).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)
    
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description=f"Automatic expiration reached for poll {poll.poll_id}."
    )

    if not poll.is_active:
        helpers.custom_print(
            level=shared.LogLevel.DEBUG,
            description=(
                f"Automatic closure skipped for poll {poll.poll_id}: "
                "poll no longer active."
            )
        )
        return

    poll.is_active = False
    poll.updated_at = datetime.datetime.now()
    # Mark poll for deletion
    #database_manager.DB_MANAGER.remove_polls(poll.poll_id)
    # Or use `mark_dirty` instead if keeping inactive polls is required (maybe to check who has voted even when poll has ended?)
    database_manager.DB_MANAGER.mark_dirty(poll.poll_id)
    
    # Remove the poll from the active cache now that voting has ended
    active_list: list[models.Poll] = ACTIVE_POLLS.get(poll.creator_id, [])
    for p in active_list:
        if p.poll_id == poll.poll_id:
            active_list.remove(p)
            break
    
    helpers.custom_print(
        level=shared.LogLevel.DEBUG,
        description=f"Poll ID {poll.poll_id} closed automatically upon reaching runtime boundaries."
    )

def get_all_polls(active_only: bool = False) -> List[models.Poll]:
    """
    Retrieves every active poll currently stored in the database cache.

    Args:
        active_only (bool): Whether to exclude inactive polls. Default is False.

    Returns:
        list[models.Poll]: All active, non-deleted polls.
    """
    polls: list[models.Poll] = [
        poll
        for poll in database_manager.DB_MANAGER.polls
        if (not active_only or poll.is_active)
    ]

    return polls