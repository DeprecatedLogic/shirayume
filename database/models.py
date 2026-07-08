from typing import List, Dict, Union, Optional
from datetime import datetime
import json
from utils.shared import Action, GlobalItemType

class User():
    instance_counter = 0

    __slots__ = (
        "_user_id",
        "_username",
        "_discriminator",
        "_avatar_url",
        "_is_bot",
        "_balance",
        "_active_items",
        "_created_at",
        "_updated_at",
        "_is_dirty",
        "_is_deleted"
    )

    def __init__(self,
        user_id: int,
        username: str,
        discriminator: str,
        avatar_url: str,
        is_bot: bool,
        balance: int,
        active_items: dict,
        created_at: datetime,
        updated_at: datetime,
        is_dirty: bool,
        is_deleted: bool
    ) -> None:
        self.user_id = user_id
        self.username = username
        self.discriminator = discriminator
        self.avatar_url = avatar_url
        self.is_bot = is_bot
        self.balance = balance
        self.active_items = active_items if active_items is not None else {} # todo: don't check
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_dirty = is_dirty
        self.is_deleted = is_deleted

        User.instance_counter += 1

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is dict:
            return cls(
                user_id = data["user_id"],
                username = data["username"],
                discriminator = data.get("discriminator", ""),
                avatar_url = data.get("avatar_url", ""),
                is_bot = bool(data["is_bot"]),
                balance = data.get("balance", 0),
                active_items = data.get("active_items", {}),
                created_at = data["created_at"],
                updated_at = data.get("updated_at", data["created_at"]),
                is_dirty = bool(data.get("is_dirty", False)),
                is_deleted = bool(data.get("is_deleted", False))
            )

    def compare(self, model: "User") -> bool:
        return type(model) == User and self.user_id == model.user_id

    @property
    def user_id(self): return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        if type(value) == int: self._user_id = value
        else: raise TypeError("Incorrect type for user_id")

    @property
    def username(self): return self._username

    @username.setter
    def username(self, value: str):
        if type(value) == str: self._username = value
        else: raise TypeError("Incorrect type for username")

    @property
    def discriminator(self): return self._discriminator

    @discriminator.setter
    def discriminator(self, value: str):
        if type(value) == str: self._discriminator = value
        else: raise TypeError("Incorrect type for discriminator")
                    
    @property
    def avatar_url(self): return self._avatar_url

    @avatar_url.setter
    def avatar_url(self, value: str):
        if type(value) == str: self._avatar_url = value
        else: raise TypeError("Incorrect type for avatar_url")

    @property
    def is_bot(self): return self._is_bot

    @is_bot.setter
    def is_bot(self, value: bool):
        if type(value) == bool: self._is_bot = value
        else: raise TypeError("Incorrect type for is_bot")

    @property
    def balance(self): return self._balance

    @balance.setter
    def balance(self, value: int):
        if type(value) == int: self._balance = value
        else: raise TypeError("Incorrect type for balance")

    @property
    def created_at(self): return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        if type(value) == datetime: self._created_at = value
        else: raise TypeError("Incorrect type for created_at")

    @property
    def updated_at(self): return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime):
        if type(value) == datetime: self._updated_at = value
        else: raise TypeError("Incorrect type for updated_at")

    @property
    def is_dirty(self): return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool: self._is_dirty = value
        else: raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self): return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool: self._is_deleted = value
        else: raise TypeError("Incorrect type for is_deleted")

    @property
    def active_items(self): return self._active_items

    @active_items.setter
    def active_items(self, value: dict):
        if type(value) == dict: self._active_items = value
        else: raise TypeError("Incorrect type for active_items")

class Guild():
    instance_counter = 0

    __slots__ = (
        "_guild_id",
        "_owner_id",
        "_name",
        "_icon_url",
        "_member_count",
        "_bot_count",
        "_is_available",
        "_welcome_channel",
        "_leave_channel",
        "_joined_at",
        "_created_at",
        "_updated_at",
        "_is_dirty",
        "_is_deleted",
        "_stats_enabled",
        "_stats_category_id",
        "_stats_channel_ids",
        "_economy_enabled",
        "_base_message_reward",
        "_currency",
        "_yume_points",
        "_tax_rate"
    )

    def __init__(self,
        guild_id: int,
        owner_id: int,
        name: str,
        icon_url: str,
        member_count: int,
        bot_count: int,
        is_available: bool,
        welcome_channel: int,
        leave_channel: int,
        joined_at: datetime,
        created_at: datetime,
        updated_at: datetime,
        is_dirty: bool,
        is_deleted: bool,
        stats_enabled: bool = False,
        stats_category_id: Optional[int] = None,
        stats_channel_ids: dict = {},
        economy_enabled: bool = False,
        base_message_reward: int = 0,
        currency: str = "Credits",
        yume_points: int = 0,
        tax_rate: float = 0.05
    ) -> None:
        self.guild_id = guild_id
        self.owner_id = owner_id
        self.name = name
        self.icon_url = icon_url
        self.member_count = member_count
        self.bot_count = bot_count
        self.is_available = is_available
        self.welcome_channel = welcome_channel
        self.leave_channel = leave_channel
        self.joined_at = joined_at
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_dirty = is_dirty
        self.is_deleted = is_deleted

        self.stats_enabled = stats_enabled
        self.stats_category_id = stats_category_id
        self.stats_channel_ids = stats_channel_ids
        
        self.economy_enabled = economy_enabled
        self.base_message_reward = base_message_reward
        self.currency = currency
        self.yume_points = yume_points
        self.tax_rate = tax_rate
        
        Guild.instance_counter += 1

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is dict:
            return cls(
                guild_id = data["guild_id"],
                owner_id = data["owner_id"],
                name = data["name"],
                icon_url = data.get("icon_url", ""),
                member_count = data["member_count"],
                bot_count = data["bot_count"],
                is_available = bool(data["is_available"]),
                welcome_channel = data.get("welcome_channel", None),
                leave_channel = data.get("leave_channel", None),
                joined_at = data["joined_at"],
                created_at = data["created_at"],
                updated_at = data.get("updated_at", data["created_at"]),
                stats_enabled = bool(data.get("stats_enabled", False)),
                stats_category_id = data.get("stats_category_id", None),
                stats_channel_ids = json.loads(data["stats_channel_ids"]) if isinstance(data.get("stats_channel_ids"), str) else data.get("stats_channel_ids", {}),
                economy_enabled = bool(data.get("economy_enabled", False)),
                base_message_reward = data.get("base_message_reward", 0),
                currency = data.get("currency", "Credits"),
                yume_points = data.get("yume_points", 0),
                tax_rate = data.get("tax_rate", 0.05),
                is_dirty = bool(data.get("is_dirty", False)),
                is_deleted = bool(data.get("is_deleted", False)),
            )

    def compare(self, model: "Guild") -> bool:
        return type(model) == Guild and self.guild_id == model.guild_id

    @property
    def guild_id(self): return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int: self._guild_id = value
        else: raise TypeError("Incorrect type for guild_id")

    @property
    def owner_id(self): return self._owner_id

    @owner_id.setter
    def owner_id(self, value: int):
        if type(value) == int: self._owner_id = value
        else: raise TypeError("Incorrect type for owner_id")

    @property
    def name(self): return self._name

    @name.setter
    def name(self, value: str):
        if type(value) == str: self._name = value
        else: raise TypeError("Incorrect type for name")

    @property
    def icon_url(self): return self._icon_url

    @icon_url.setter
    def icon_url(self, value: str):
        if type(value) == str: self._icon_url = value
        else: raise TypeError("Incorrect type for icon_url")

    @property
    def member_count(self): return self._member_count

    @member_count.setter
    def member_count(self, value: int):
        if type(value) == int: self._member_count = value
        else: raise TypeError("Incorrect type for member_count")

    @property
    def bot_count(self): return self._bot_count

    @bot_count.setter
    def bot_count(self, value: int):
        if type(value) == int: self._bot_count = value
        else: raise TypeError("Incorrect type for bot_count")

    @property
    def is_available(self): return self._is_available

    @is_available.setter
    def is_available(self, value: bool):
        if type(value) == bool: self._is_available = value
        else: raise TypeError("Incorrect type for is_available")

    @property
    def welcome_channel(self): return self._welcome_channel

    @welcome_channel.setter
    def welcome_channel(self, value: int):
        if type(value) == int: self._welcome_channel = value
        else: raise TypeError("Incorrect type for welcome_channel")
        
    @property
    def leave_channel(self): return self._leave_channel
    
    @leave_channel.setter
    def leave_channel(self, value: int):
        if type(value) == int: self._leave_channel = value
        else: raise TypeError("Incorrect type for leave_channel")

    @property
    def joined_at(self): return self._joined_at

    @joined_at.setter
    def joined_at(self, value: datetime):
        if type(value) == datetime: self._joined_at = value
        else: raise TypeError("Incorrect type for joined_at")

    @property
    def created_at(self): return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        if type(value) == datetime: self._created_at = value
        else: raise TypeError("Incorrect type for created_at")

    @property
    def updated_at(self): return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime):
        if type(value) == datetime: self._updated_at = value
        else: raise TypeError("Incorrect type for updated_at")

    @property
    def is_dirty(self): return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool: self._is_dirty = value
        else: raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self): return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool: self._is_deleted = value
        else: raise TypeError("Incorrect type for is_deleted")

    @property
    def stats_enabled(self): return self._stats_enabled
    
    @stats_enabled.setter
    def stats_enabled(self, value: bool):
        if type(value) == bool: self._stats_enabled = value
        else: raise TypeError("Incorrect type for stats_enabled")
    
    @property
    def stats_category_id(self): return self._stats_category_id
    
    @stats_category_id.setter
    def stats_category_id(self, value: Union[int, None]):
        if value is None or type(value) == int: self._stats_category_id = value
        else: raise TypeError("Incorrect type for stats_category_id")

    @property
    def stats_channel_ids(self): return self._stats_channel_ids
    
    @stats_channel_ids.setter
    def stats_channel_ids(self, value: dict):
        if type(value) == dict: self._stats_channel_ids = value
        else: raise TypeError("Incorrect type for stats_channel_ids")

    @property
    def economy_enabled(self): return self._economy_enabled

    @economy_enabled.setter
    def economy_enabled(self, value: bool):
        if type(value) == bool: self._economy_enabled = value
        else: raise TypeError("Incorrect type for economy_enabled")

    @property
    def base_message_reward(self): return self._base_message_reward

    @base_message_reward.setter
    def base_message_reward(self, value: int):
        if type(value) == int: self._base_message_reward = value
        else: raise TypeError("Incorrect type for base_message_reward")

    @property
    def currency(self): return self._currency

    @currency.setter
    def currency(self, value: str):
        if type(value) == str: self._currency = value
        else: raise TypeError("Incorrect type for currency")

    @property
    def yume_points(self): return self._yume_points

    @yume_points.setter
    def yume_points(self, value: int):
        if type(value) == int: self._yume_points = value
        else: raise TypeError("Incorrect type for yume_points")

    @property
    def tax_rate(self): return self._tax_rate

    @tax_rate.setter
    def tax_rate(self, value: float):
        if type(value) == float: self._tax_rate = value
        else: raise TypeError("Incorrect type for tax_rate")

class UserGuildSettings():
    instance_counter = 0

    __slots__ = (
        "_user_id",
        "_guild_id",
        "_joined_at",
        "_last_interaction",
        "_experience",
        "_level",
        "_custom_title",
        "_last_xp_message",
        "_created_at",
        "_updated_at",
        "_is_member",
        "_is_dirty",
        "_is_deleted"
    )

    def __init__(self,
        user_id: int,
        guild_id: int,
        joined_at: datetime,
        last_interaction: datetime,
        experience: int,
        level: int,
        custom_title: str,
        last_xp_message: datetime,
        created_at: datetime,
        updated_at: datetime,
        is_member: bool,
        is_dirty: bool,
        is_deleted: bool
    ) -> None:
        self.user_id = user_id
        self.guild_id = guild_id
        self.joined_at = joined_at
        self.last_interaction = last_interaction
        self.experience = experience
        self.level = level
        self.custom_title = custom_title
        self.last_xp_message = last_xp_message
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_member = is_member
        self.is_dirty = is_dirty
        self.is_deleted = is_deleted
        
        UserGuildSettings.instance_counter += 1

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is dict:
            return cls(
                user_id = data["user_id"],
                guild_id = data["guild_id"],
                joined_at = data["joined_at"],
                last_interaction = data["last_interaction"],
                experience = data["experience"],
                level = data["level"],
                custom_title = data.get("custom_title", ""),
                last_xp_message = data.get("last_xp_message", None),
                created_at = data["created_at"],
                updated_at = data.get("updated_at", data["created_at"]),
                is_member = bool(data["is_member"]),
                is_dirty = bool(data.get("is_dirty", False)),
                is_deleted = bool(data.get("is_deleted", False))
            )

    def compare(self, model: "UserGuildSettings") -> bool:
        return type(model) == UserGuildSettings and self.user_id == model.user_id and self.guild_id == model.guild_id

    @property
    def user_id(self): return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        if type(value) == int: self._user_id = value
        else: raise TypeError("Incorrect type for user_id")

    @property
    def guild_id(self): return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int: self._guild_id = value
        else: raise TypeError("Incorrect type for guild_id")

    @property
    def joined_at(self): return self._joined_at

    @joined_at.setter
    def joined_at(self, value: datetime):
        if type(value) == datetime: self._joined_at = value
        else: raise TypeError("Incorrect type for joined_at")

    @property
    def last_interaction(self): return self._last_interaction

    @last_interaction.setter
    def last_interaction(self, value: datetime):
        if type(value) == datetime: self._last_interaction = value
        else: raise TypeError("Incorrect type for last_interaction")

    @property
    def experience(self): return self._experience

    @experience.setter
    def experience(self, value: int):
        if type(value) == int: self._experience = value
        else: raise TypeError("Incorrect type for experience")

    @property
    def level(self): return self._level

    @level.setter
    def level(self, value: int):
        if type(value) == int: self._level = value
        else: raise TypeError("Incorrect type for level")

    @property
    def custom_title(self): return self._custom_title

    @custom_title.setter
    def custom_title(self, value: str):
        if type(value) == str: self._custom_title = value
        else: raise TypeError("Incorrect type for custom_title")

    @property
    def last_xp_message(self): return self._last_xp_message

    @last_xp_message.setter
    def last_xp_message(self, value: datetime):
        if type(value) == datetime: self._last_xp_message = value
        else: raise TypeError("Incorrect type for last_xp_message")

    @property
    def created_at(self): return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        if type(value) == datetime: self._created_at = value
        else: raise TypeError("Incorrect type for created_at")

    @property
    def updated_at(self): return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime):
        if type(value) == datetime: self._updated_at = value
        else: raise TypeError("Incorrect type for updated_at")

    @property
    def is_member(self): return self._is_member

    @is_member.setter
    def is_member(self, value: bool):
        if type(value) == bool: self._is_member = value
        else: raise TypeError("Incorrect type for is_member")

    @property
    def is_dirty(self): return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool: self._is_dirty = value
        else: raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self): return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool: self._is_deleted = value
        else: raise TypeError("Incorrect type for is_deleted")

class ModerationLog():
    instance_counter = 0

    __slots__ = (
        "_mlog_id",
        "_guild_id",
        "_user_id",
        "_moderator_id",
        "_action_type",
        "_reason",
        "_action_timestamp",
        "_duration_minutes",
        "_is_active",
        "_pardoned",
        "_is_dirty",
        "_is_deleted"
    )

    def __init__(self,
        mlog_id: int,
        guild_id: int,
        user_id: int,
        moderator_id: int,
        action_type: Action,
        reason: str,
        action_timestamp: datetime,
        duration_minutes: int,
        is_active: bool,
        pardoned: bool,
        is_dirty: bool,
        is_deleted: bool
    ) -> None:
        self.mlog_id = mlog_id
        self.guild_id = guild_id
        self.user_id = user_id
        self.moderator_id = moderator_id
        self.action_type = action_type
        self.reason = reason
        self.action_timestamp = action_timestamp
        self.duration_minutes = duration_minutes
        self.is_active = is_active
        self.pardoned = pardoned
        self.is_dirty = is_dirty
        self.is_deleted = is_deleted
        ModerationLog.instance_counter += 1

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is dict:

            action_value = data["action_type"]
            if isinstance(action_value, str):
                try:
                    action_value = Action[action_value]
                except KeyError:
                    action_value = Action(action_value)

            return cls(
                mlog_id = data["mlog_id"],
                guild_id = data["guild_id"],
                user_id = data["user_id"],
                moderator_id = data["moderator_id"],
                action_type = action_value,
                reason = data["reason"],
                action_timestamp = data["action_timestamp"],
                duration_minutes = data.get("duration_minutes", None), # maybe 0 instead of None ?
                is_active = bool(data["is_active"]),
                pardoned = bool(data["pardoned"]),
                is_dirty = bool(data.get("is_dirty", False)),
                is_deleted = bool(data.get("is_deleted", False))
            )

    def compare(self, model: "ModerationLog") -> bool:
        return type(model) == ModerationLog and self.mlog_id == model.mlog_id

    @property
    def mlog_id(self): return self._mlog_id

    @mlog_id.setter
    def mlog_id(self, value: int):
        if type(value) == int:
            if value == -1: value = ModerationLog.instance_counter
            self._mlog_id = value
        else: raise TypeError("Incorrect type for mlog_id")

    @property
    def guild_id(self): return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int: self._guild_id = value
        else: raise TypeError("Incorrect type for guild_id")

    @property
    def user_id(self): return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        if type(value) == int: self._user_id = value
        else: raise TypeError("Incorrect type for user_id")

    @property
    def moderator_id(self): return self._moderator_id

    @moderator_id.setter
    def moderator_id(self, value: int):
        if type(value) == int: self._moderator_id = value
        else: raise TypeError("Incorrect type for moderator_id")

    @property
    def action_type(self): return self._action_type

    @action_type.setter
    def action_type(self, value: Action):
        if type(value) == Action: self._action_type = value
        else: raise TypeError("Incorrect type for action_type")

    @property
    def reason(self): return self._reason

    @reason.setter
    def reason(self, value: str):
        if type(value) == str: self._reason = value
        else: raise TypeError("Incorrect type for reason")

    @property
    def action_timestamp(self): return self._action_timestamp

    @action_timestamp.setter
    def action_timestamp(self, value: datetime):
        if type(value) == datetime: self._action_timestamp = value
        else: raise TypeError("Incorrect type for action_timestamp")

    @property
    def duration_minutes(self): return self._duration_minutes

    @duration_minutes.setter
    def duration_minutes(self, value: int):
        if type(value) == int: self._duration_minutes = value
        else: raise TypeError("Incorrect type for duration_minutes")

    @property
    def is_active(self): return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        if type(value) == bool: self._is_active = value
        else: raise TypeError("Incorrect type for is_active")

    @property
    def pardoned(self): return self._pardoned

    @pardoned.setter
    def pardoned(self, value: bool):
        if type(value) == bool: self._pardoned = value
        else: raise TypeError("Incorrect type for pardoned")

    @property
    def is_dirty(self): return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool: self._is_dirty = value
        else: raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self): return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool: self._is_deleted = value
        else: raise TypeError("Incorrect type for is_deleted")

class Poll():
    instance_counter = 0

    __slots__ = (
        "_poll_id",
        "_guild_id",
        "_creator_id",
        "_question",
        "_votes",
        "_is_active",
        "_created_at",
        "_updated_at",
        "_ends_at",
        "_is_dirty",
        "_is_deleted"
    )

    def __init__(self,
        poll_id: int,
        guild_id: int,
        creator_id: int,
        question: str,
        votes: Dict[str, List[int]],
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
        ends_at: datetime,
        is_dirty: bool,
        is_deleted: bool
    ) -> None:
        self.poll_id = poll_id
        self.guild_id = guild_id
        self.creator_id = creator_id
        self.question = question
        self.votes = votes
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at
        self.is_dirty = is_dirty
        self.is_deleted = is_deleted
        self.ends_at = ends_at
        Poll.instance_counter += 1

    @classmethod
    def from_dict(cls, data: Dict):
        if type(data) is dict:
            raw_votes = data.get("votes", {})
            parsed_votes = json.loads(raw_votes) if isinstance(raw_votes, str) else raw_votes
            
            return cls(
                poll_id = data["poll_id"],
                guild_id = data["guild_id"],
                creator_id = data["creator_id"],
                question = data["question"],
                votes = parsed_votes,
                is_active = bool(data["is_active"]),
                created_at = data["created_at"],
                updated_at = data.get("updated_at", data["created_at"]),
                ends_at = data.get("ends_at", data["created_at"]),
                is_dirty = bool(data.get("is_dirty", False)),
                is_deleted = bool(data.get("is_deleted", False))
            )

    def to_dict(self) -> dict:
        return {
            "poll_id": self.poll_id,
            "guild_id": self.guild_id,
            "creator_id": self.creator_id,
            "question": self.question,
            "votes": self.votes,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_dirty": self.is_dirty,
            "is_deleted": self.is_deleted
        }

    def compare(self, model: "Poll") -> bool:
        return type(model) == Poll and self.poll_id == model.poll_id

    @property
    def poll_id(self): return self._poll_id

    @poll_id.setter
    def poll_id(self, value: int):
        if type(value) == int:
            if value == -1: value = Poll.instance_counter
            self._poll_id = value
        else: raise TypeError("Incorrect type for poll_id")

    @property
    def guild_id(self): return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int: self._guild_id = value
        else: raise TypeError("Incorrect type for guild_id")

    @property
    def creator_id(self): return self._creator_id

    @creator_id.setter
    def creator_id(self, value: int):
        if type(value) == int: self._creator_id = value
        else: raise TypeError("Incorrect type for creator_id")

    @property
    def question(self): return self._question

    @question.setter
    def question(self, value: str):
        if type(value) == str: self._question = value
        else: raise TypeError("Incorrect type for question")

    @property
    def votes(self): return self._votes

    @votes.setter
    def votes(self, value: Dict[str, List[int]]):
        if type(value) == dict and all(type(k) == str and type(v) == list for k, v in value.items()): self._votes = value
        else: raise TypeError("Incorrect type for votes")

    @property
    def is_active(self): return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        if type(value) == bool: self._is_active = value
        else: raise TypeError("Incorrect type for is_active")
    
    @property
    def created_at(self): return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        if type(value) == datetime: self._created_at = value
        else: raise TypeError("Incorrect type for created_at")

    @property
    def updated_at(self): return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime):
        if type(value) == datetime: self._updated_at = value
        else: raise TypeError("Incorrect type for updated_at")

    @property
    def ends_at(self): return self._ends_at
    
    @ends_at.setter
    def ends_at(self, value: datetime):
        if type(value) == datetime: self._ends_at = value
        else: raise TypeError("Incorrect type for ends_at")

    @property
    def is_dirty(self): return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool: self._is_dirty = value
        else: raise TypeError("Incorrect type for is_dirty")
    
    @property
    def is_deleted(self): return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool: self._is_deleted = value
        else: raise TypeError("Incorrect type for is_deleted")

class UserEconomy():
    instance_counter = 0

    __slots__ = (
        "_guild_id",
        "_user_id",
        "_local_balance",
        "_last_message_reward_time",
        "_is_dirty",
        "_is_deleted"
    )

    def __init__(self,
        guild_id: int,
        user_id: int,
        local_balance: int,
        last_message_reward_time: datetime,
        is_dirty: bool,
        is_deleted: bool
    ) -> None:
        self.guild_id = guild_id
        self.user_id = user_id
        self.local_balance = local_balance
        self.last_message_reward_time = last_message_reward_time
        self.is_dirty = is_dirty
        self.is_deleted = is_deleted
        UserEconomy.instance_counter += 1

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is dict:
            return cls(
                guild_id = data["guild_id"],
                user_id = data["user_id"],
                local_balance = data["local_balance"],
                last_message_reward_time = data["last_message_reward_time"],
                is_dirty = bool(data.get("is_dirty", False)),
                is_deleted = bool(data.get("is_deleted", False))
            )

    def compare(self, model: "UserEconomy") -> bool:
        return type(model) == UserEconomy and self.guild_id == model.guild_id and self.user_id == model.user_id

    @property
    def guild_id(self): return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int: self._guild_id = value
        else: raise TypeError("Incorrect type for guild_id")

    @property
    def user_id(self): return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        if type(value) == int: self._user_id = value
        else: raise TypeError("Incorrect type for user_id")

    @property
    def local_balance(self): return self._local_balance

    @local_balance.setter
    def local_balance(self, value: int):
        if type(value) == int: self._local_balance = value
        else: raise TypeError("Incorrect type for local_balance")

    @property
    def last_message_reward_time(self): return self._last_message_reward_time

    @last_message_reward_time.setter
    def last_message_reward_time(self, value: datetime):
        if type(value) == datetime: self._last_message_reward_time = value
        else: raise TypeError("Incorrect type for last_message_reward_time")

    @property
    def is_dirty(self): return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool: self._is_dirty = value
        else: raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self): return self._is_deleted

    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool: self._is_deleted = value
        else: raise TypeError("Incorrect type for is_deleted")

class ShopItem():
    instance_counter = 0

    __slots__ = (
        "_item_id",
        "_guild_id",
        "_name",
        "_description",
        "_price",
        "_role_id",
        "_is_dirty",
        "_is_deleted"
    )

    def __init__(self,
        item_id: int,
        guild_id: int,
        name: str,
        description: str,
        price: int,
        role_id: Union[int, None],
        is_dirty: bool,
        is_deleted: bool
    ) -> None:
        self.item_id = item_id
        self.guild_id = guild_id
        self.name = name
        self.description = description
        self.price = price
        self.role_id = role_id
        self.is_dirty = is_dirty
        self.is_deleted = is_deleted
        ShopItem.instance_counter += 1

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is dict:
            return cls(
                item_id = data["item_id"],
                guild_id = data["guild_id"],
                name = data["name"],
                description = data["description"],
                price = data["price"],
                role_id = data.get("role_id", None),
                is_dirty = bool(data.get("is_dirty", False)),
                is_deleted = bool(data.get("is_deleted", False))
            )

    def compare(self, model: "ShopItem") -> bool:
        return type(model) == ShopItem and self.item_id == model.item_id

    @property
    def item_id(self): return self._item_id

    @item_id.setter
    def item_id(self, value: int):
        if type(value) == int:
            if value == -1: value = ShopItem.instance_counter
            self._item_id = value
        else: raise TypeError("Incorrect type for item_id")

    @property
    def guild_id(self): return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int: self._guild_id = value
        else: raise TypeError("Incorrect type for guild_id")

    @property
    def name(self): return self._name

    @name.setter
    def name(self, value: str):
        if type(value) == str: self._name = value
        else: raise TypeError("Incorrect type for name")

    @property
    def description(self): return self._description

    @description.setter
    def description(self, value: str):
        if type(value) == str: self._description = value
        else: raise TypeError("Incorrect type for description")

    @property
    def price(self): return self._price

    @price.setter
    def price(self, value: int):
        if type(value) == int: self._price = value
        else: raise TypeError("Incorrect type for price")

    @property
    def role_id(self): return self._role_id

    @role_id.setter
    def role_id(self, value: Union[int, None]):
        if type(value) == int or value is None: self._role_id = value
        else: raise TypeError("Incorrect type for role_id")

    @property
    def is_dirty(self): return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool: self._is_dirty = value
        else: raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self): return self._is_deleted

    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool: self._is_deleted = value
        else: raise TypeError("Incorrect type for is_deleted")

class GlobalShopItem():
    instance_counter = 0

    __slots__ = (
        "_item_id",
        "_name",
        "_description",
        "_price",
        "_item_type",
        "_metadata",
        "_is_dirty",
        "_is_deleted"
    )

    def __init__(self,
        item_id: int,
        name: str,
        description: str,
        price: int,
        item_type: GlobalItemType,
        metadata: dict,
        is_dirty: bool,
        is_deleted: bool
    ) -> None:
        self.item_id = item_id
        self.name = name
        self.description = description
        self.price = price
        self.item_type = item_type
        self.metadata = metadata if metadata is not None else {}
        self.is_dirty = is_dirty
        self.is_deleted = is_deleted
        GlobalShopItem.instance_counter += 1

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is dict:
            i_type = data["item_type"]
            if isinstance(i_type, str):
                try: i_type = GlobalItemType[i_type]
                except KeyError: i_type = GlobalItemType(i_type)

            return cls(
                item_id = data["item_id"],
                name = data["name"],
                description = data.get("description", ""),
                price = data.get("price", 0),
                item_type = i_type,
                metadata = json.loads(data["metadata"]) if isinstance(data.get("metadata"), str) else data.get("metadata", {}),
                is_dirty = bool(data.get("is_dirty", False)),
                is_deleted = bool(data.get("is_deleted", False))
            )

    def compare(self, model: "GlobalShopItem") -> bool:
        return type(model) == GlobalShopItem and self.item_id == model.item_id

    @property
    def item_id(self): return self._item_id

    @item_id.setter
    def item_id(self, value: int):
        if type(value) == int: self._item_id = value
        else: raise TypeError("Incorrect type for item_id")

    @property
    def name(self): return self._name

    @name.setter
    def name(self, value: str):
        if type(value) == str: self._name = value
        else: raise TypeError("Incorrect type for name")

    @property
    def description(self): return self._description

    @description.setter
    def description(self, value: str):
        if type(value) == str: self._description = value
        else: raise TypeError("Incorrect type for description")

    @property
    def price(self): return self._price

    @price.setter
    def price(self, value: int):
        if type(value) == int: self._price = value
        else: raise TypeError("Incorrect type for price")

    @property
    def item_type(self): return self._item_type

    @item_type.setter
    def item_type(self, value: GlobalItemType):
        if type(value) == GlobalItemType: self._item_type = value
        else: raise TypeError("Incorrect type for item_type")

    @property
    def metadata(self): return self._metadata

    @metadata.setter
    def metadata(self, value: dict):
        if type(value) == dict: self._metadata = value
        else: raise TypeError("Incorrect type for metadata")

    @property
    def is_dirty(self): return self._is_dirty

    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool: self._is_dirty = value
        else: raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self): return self._is_deleted

    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool: self._is_deleted = value
        else: raise TypeError("Incorrect type for is_deleted")