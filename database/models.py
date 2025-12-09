from typing import List, Dict
from datetime import datetime
from utils.shared import Action

class User():
    instance_counter = 0

    def __init__(self,
        user_id: int,
        username: str,
        discriminator: str,
        avatar_url: str,
        is_bot: bool,
        currency: int,
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
        self.currency = currency
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
                discriminator = data["discriminator"],
                avatar_url = data["avatar_url"],
                is_bot = data["is_bot"],
                currency = data["currency"],
                created_at = data["created_at"],
                updated_at = data.get("updated_at", data["created_at"]),
                is_dirty = data.get("is_dirty", False),
                is_deleted = data.get("is_deleted", False)
            )

    def compare(self, model: "User") -> bool:
        return type(model) == User and self.user_id == model.user_id

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        if type(value) == int:
            self._user_id = value
        else:
            raise TypeError("Incorrect type for user_id")

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value: str):
        if type(value) == str:
            self._username = value
        else:
            raise TypeError("Incorrect type for username")

    @property
    def discriminator(self):
        return self._discriminator

    @discriminator.setter
    def discriminator(self, value: str):
        if type(value) == str:
            self._discriminator = value
        else:
            raise TypeError("Incorrect type for discriminator")
                    
    @property
    def avatar_url(self):
        return self._avatar_url

    @avatar_url.setter
    def avatar_url(self, value: str):
        if type(value) == str:
            self._avatar_url = value
        else:
            raise TypeError("Incorrect type for avatar_url")

    @property
    def is_bot(self):
        return self._is_bot

    @is_bot.setter
    def is_bot(self, value: bool):
        if type(value) == bool:
            self._is_bot = value
        else:
            raise TypeError("Incorrect type for is_bot")

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, value: int):
        if type(value) == int:
            self._currency = value
        else:
            raise TypeError("Incorrect type for currency")

    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        if type(value) == datetime:
            self._created_at = value
        else:
            raise TypeError("Incorrect type for created_at")

    @property
    def updated_at(self):
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime):
        if type(value) == datetime:
            self._updated_at = value
        else:
            raise TypeError("Incorrect type for updated_at")

    @property
    def is_dirty(self):
        return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool:
            self._is_dirty = value
        else:
            raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self):
        return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool:
            self._is_deleted = value
        else:
            raise TypeError("Incorrect type for is_deleted")

class Guild():
    instance_counter = 0

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
        is_deleted: bool
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
        Guild.instance_counter += 1

    @classmethod
    def from_dict(cls, data: dict):
        if type(data) is dict:
            return cls(
                guild_id = data["guild_id"],
                owner_id = data["owner_id"],
                name = data["name"],
                icon_url = data["icon_url"],
                member_count = data["member_count"],
                bot_count = data["bot_count"],
                is_available = data["is_available"],
                welcome_channel = data["welcome_channel"],
                leave_channel = data["leave_channel"],
                joined_at = data["joined_at"],
                created_at = data["created_at"],
                updated_at = data.get("updated_at", data["created_at"]),
                is_dirty = data.get("is_dirty", False),
                is_deleted = data.get("is_deleted", False)
            )

    def compare(self, model: "Guild") -> bool:
        return type(model) == Guild and self.guild_id == model.guild_id

    @property
    def guild_id(self):
        return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int:
            self._guild_id = value
        else:
            raise TypeError("Incorrect type for guild_id")

    @property
    def owner_id(self):
        return self._owner_id

    @owner_id.setter
    def owner_id(self, value: int):
        if type(value) == int:
            self._owner_id = value
        else:
            raise TypeError("Incorrect type for owner_id")

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        if type(value) == str:
            self._name = value
        else:
            raise TypeError("Incorrect type for name")

    @property
    def icon_url(self):
        return self._icon_url

    @icon_url.setter
    def icon_url(self, value: str):
        if type(value) == str:
            self._icon_url = value
        else:
            raise TypeError("Incorrect type for icon_url")

    @property
    def member_count(self):
        return self._member_count

    @member_count.setter
    def member_count(self, value: int):
        if type(value) == int:
            self._member_count = value
        else:
            raise TypeError("Incorrect type for member_count")

    @property
    def bot_count(self):
        return self._bot_count

    @bot_count.setter
    def bot_count(self, value: int):
        if type(value) == int:
            self._bot_count = value
        else:
            raise TypeError("Incorrect type for bot_count")

    @property
    def is_available(self):
        return self._is_available

    @is_available.setter
    def is_available(self, value: bool):
        if type(value) == bool:
            self._is_available = value
        else:
            raise TypeError("Incorrect type for is_available")

    @property
    def welcome_channel(self):
        return self._welcome_channel

    @welcome_channel.setter
    def welcome_channel(self, value: int):
        if type(value) == int:
            self._welcome_channel = value
        else:
            raise TypeError("Incorrect type for welcome_channel")
        
    @property
    def leave_channel(self):
        return self._leave_channel
    
    @leave_channel.setter
    def leave_channel(self, value: int):
        if type(value) == int:
            self._leave_channel = value
        else:
            raise TypeError("Incorrect type for leave_channel")

    @property
    def joined_at(self):
        return self._joined_at

    @joined_at.setter
    def joined_at(self, value: datetime):
        if type(value) == datetime:
            self._joined_at = value
        else:
            raise TypeError("Incorrect type for joined_at")

    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        if type(value) == datetime:
            self._created_at = value
        else:
            raise TypeError("Incorrect type for created_at")

    @property
    def updated_at(self):
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime):
        if type(value) == datetime:
            self._updated_at = value
        else:
            raise TypeError("Incorrect type for updated_at")

    @property
    def is_dirty(self):
        return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool:
            self._is_dirty = value
        else:
            raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self):
        return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool:
            self._is_deleted = value
        else:
            raise TypeError("Incorrect type for is_deleted")

class UserGuildSettings():
    instance_counter = 0

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
                custom_title = data["custom_title"],
                last_xp_message = data["last_xp_message"],
                created_at = data["created_at"],
                updated_at = data.get("updated_at", data["created_at"]),
                is_member = data["is_member"],
                is_dirty = data.get("is_dirty", False),
                is_deleted = data.get("is_deleted", False)
            )

    def compare(self, model: "UserGuildSettings") -> bool:
        return type(model) == UserGuildSettings and self.user_id == model.user_id and self.guild_id == model.guild_id

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value: int):
        if type(value) == int:
            self._user_id = value
        else:
            raise TypeError("Incorrect type for user_id")

    @property
    def guild_id(self):
        return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int:
            self._guild_id = value
        else:
            raise TypeError("Incorrect type for guild_id")

    @property
    def joined_at(self):
        return self._joined_at

    @joined_at.setter
    def joined_at(self, value: datetime):
        if type(value) == datetime:
            self._joined_at = value
        else:
            raise TypeError("Incorrect type for joined_at")

    @property
    def last_interaction(self):
        return self._last_interaction

    @last_interaction.setter
    def last_interaction(self, value: datetime):
        if type(value) == datetime:
            self._last_interaction = value
        else:
            raise TypeError("Incorrect type for last_interaction")

    @property
    def experience(self):
        return self._experience

    @experience.setter
    def experience(self, value: int):
        if type(value) == int:
            self._experience = value
        else:
            raise TypeError("Incorrect type for experience")

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value: int):
        if type(value) == int:
            self._level = value
        else:
            raise TypeError("Incorrect type for level")

    @property
    def custom_title(self):
        return self._custom_title

    @custom_title.setter
    def custom_title(self, value: str):
        if type(value) == str:
            self._custom_title = value
        else:
            raise TypeError("Incorrect type for custom_title")

    @property
    def last_xp_message(self):
        return self._last_xp_message

    @last_xp_message.setter
    def last_xp_message(self, value: datetime):
        if type(value) == datetime:
            self._last_xp_message = value
        else:
            raise TypeError("Incorrect type for last_xp_message")

    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        if type(value) == datetime:
            self._created_at = value
        else:
            raise TypeError("Incorrect type for created_at")

    @property
    def updated_at(self):
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime):
        if type(value) == datetime:
            self._updated_at = value
        else:
            raise TypeError("Incorrect type for updated_at")

    @property
    def is_member(self):
        return self._is_member

    @is_member.setter
    def is_member(self, value: bool):
        if type(value) == bool:
            self._is_member = value
        else:
            raise TypeError("Incorrect type for is_member")

    @property
    def is_dirty(self):
        return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool:
            self._is_dirty = value
        else:
            raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self):
        return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool:
            self._is_deleted = value
        else:
            raise TypeError("Incorrect type for is_deleted")

class ModerationLog():
    instance_counter = 0

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
            return cls(
                mlog_id = data["mlog_id"],
                guild_id = data["guild_id"],
                user_id = data["user_id"],
                moderator_id = data["moderator_id"],
                action_type = data["action_type"],
                reason = data["reason"],
                action_timestamp = data["action_timestamp"],
                duration_minutes = data["duration_minutes"],
                is_active = data["is_active"],
                pardoned = data["pardoned"],
                is_dirty = data.get("is_dirty", False),
                is_deleted = data.get("is_deleted", False)
            )

    def compare(self, model: "ModerationLog") -> bool:
        return type(model) == ModerationLog and self.mlog_id == model.mlog_id

    @property
    def mlog_id(self):
        return self._mlog_id

    @mlog_id.setter
    def mlog_id(self, value):
        if type(value) == int:
            if value == -1:
                value = ModerationLog.instance_counter
            self._mlog_id = value
        else:
            raise TypeError("Incorrect type for mlog_id")

    @property
    def guild_id(self):
        return self._guild_id

    @guild_id.setter
    def guild_id(self, value):
        if type(value) == int:
            self._guild_id = value
        else:
            raise TypeError("Incorrect type for guild_id")

    @property
    def user_id(self):
        return self._user_id

    @user_id.setter
    def user_id(self, value):
        if type(value) == int:
            self._user_id = value
        else:
            raise TypeError("Incorrect type for user_id")

    @property
    def moderator_id(self):
        return self._moderator_id

    @moderator_id.setter
    def moderator_id(self, value):
        if type(value) == int:
            self._moderator_id = value
        else:
            raise TypeError("Incorrect type for moderator_id")

    @property
    def action_type(self):
        return self._action_type

    @action_type.setter
    def action_type(self, value):
        if type(value) == Action:
            self._action_type = value
        else:
            raise TypeError("Incorrect type for action_type")

    @property
    def reason(self):
        return self._reason

    @reason.setter
    def reason(self, value: str):
        if type(value) == str:
            self._reason = value
        else:
            raise TypeError("Incorrect type for reason")

    @property
    def action_timestamp(self):
        return self._action_timestamp

    @action_timestamp.setter
    def action_timestamp(self, value: datetime):
        if type(value) == datetime:
            self._action_timestamp = value
        else:
            raise TypeError("Incorrect type for action_timestamp")

    @property
    def duration_minutes(self):
        return self._duration_minutes

    @duration_minutes.setter
    def duration_minutes(self, value: int):
        if type(value) == int:
            self._duration_minutes = value
        else:
            raise TypeError("Incorrect type for duration_minutes")

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        if type(value) == bool:
            self._is_active = value
        else:
            raise TypeError("Incorrect type for is_active")

    @property
    def pardoned(self):
        return self._pardoned

    @pardoned.setter
    def pardoned(self, value: bool):
        if type(value) == bool:
            self._pardoned = value
        else:
            raise TypeError("Incorrect type for pardoned")

    @property
    def is_dirty(self):
        return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool:
            self._is_dirty = value
        else:
            raise TypeError("Incorrect type for is_dirty")

    @property
    def is_deleted(self):
        return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool:
            self._is_deleted = value
        else:
            raise TypeError("Incorrect type for is_deleted")

class Poll():
    instance_counter = 0

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
            return cls(
                poll_id = data["poll_id"],
                guild_id = data["guild_id"],
                creator_id = data["creator_id"],
                question = data["question"],
                votes = data["votes"],
                is_active = data["is_active"],
                created_at = data["created_at"],
                updated_at = data.get("updated_at", data["created_at"]),
                ends_at = data.get("ends_at", data["created_at"]),
                is_dirty = data.get("is_dirty", False),
                is_deleted = data.get("is_deleted", False)
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
    def poll_id(self):
        return self._poll_id

    @poll_id.setter
    def poll_id(self, value: int):
        if type(value) == int:
            if value == -1:
                value = Poll.instance_counter
            self._poll_id = value
        else:
            raise TypeError("Incorrect type for poll_id")

    @property
    def guild_id(self):
        return self._guild_id

    @guild_id.setter
    def guild_id(self, value: int):
        if type(value) == int:
            self._guild_id = value
        else:
            raise TypeError("Incorrect type for guild_id")

    @property
    def creator_id(self):
        return self._creator_id

    @creator_id.setter
    def creator_id(self, value: int):
        if type(value) == int:
            self._creator_id = value
        else:
            raise TypeError("Incorrect type for creator_id")

    @property
    def question(self):
        return self._question

    @question.setter
    def question(self, value: str):
        if type(value) == str:
            self._question = value
        else:
            raise TypeError("Incorrect type for question")

    @property
    def votes(self):
        return self._votes

    @votes.setter
    def votes(self, value: Dict[str, List[int]]):
        if type(value) == dict and all(type(k) == str and type(v) == list for k, v in value.items()):
            self._votes = value
        else:
            raise TypeError("Incorrect type for votes")

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool):
        if type(value) == bool:
            self._is_active = value
        else:
            raise TypeError("Incorrect type for is_active")
    
    @property
    def created_at(self):
        return self._created_at

    @created_at.setter
    def created_at(self, value: datetime):
        if type(value) == datetime:
            self._created_at = value
        else:
            raise TypeError("Incorrect type for created_at")

    @property
    def updated_at(self):
        return self._updated_at

    @updated_at.setter
    def updated_at(self, value: datetime):
        if type(value) == datetime:
            self._updated_at = value
        else:
            raise TypeError("Incorrect type for updated_at")

    @property
    def ends_at(self):
        return self._ends_at
    
    @ends_at.setter
    def ends_at(self, value: datetime):
        if type(value) == datetime:
            self._ends_at = value
        else:
            raise TypeError("Incorrect type for ends_at")

    @property
    def is_dirty(self):
        return self._is_dirty
    
    @is_dirty.setter
    def is_dirty(self, value: bool):
        if type(value) == bool:
            self._is_dirty = value
        else:
            raise TypeError("Incorrect type for is_dirty")
    
    @property
    def is_deleted(self):
        return self._is_deleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool):
        if type(value) == bool:
            self._is_deleted = value
        else:
            raise TypeError("Incorrect type for is_deleted")
