from enum import Enum, auto
import blessed
from discord.ext import commands
from discord import app_commands
from typing import Any

GLOBAL_CONFIG = {}
GLOBAL_TERMINAL = blessed.Terminal()
SHIRAYUME: commands.Bot | None = None

class GroupedCog(commands.Cog):
    """Base class that automatically adds all app_commands to a group."""
    group : app_commands.Group = None # override in subclass

    def __init__(self):
        super().__init__()
        if self.group:
            try:
                for command in self.__cog_app_commands__:
                    if isinstance(command, app_commands.Command):
                        self.group.add_command(command)
            except Exception as e:
                raise Exception(f"An error occured while adding commands to this group\nException: {e}")
        else:
            raise Exception(f"Class {self.__class__} did not override the group attribute")

class LogLevel(Enum):
    """ Defines logging levels with priority. """

    DEBUG = (1, (169, 169, 169))
    INFO = (2, (30, 144, 255))
    WARNING = (3, (255, 165, 0))
    ERROR = (4, (220, 20, 60))
    CRITICAL = (5, (255, 0, 0))

    @property
    def priority(self) -> int:
        """ Returns the integer priority. """
        return self.value[0]

    @property
    def color_rgb(self) -> tuple[int, int, int]:
        """ Returns the (R, G, B) tuple. """
        return self.value[1]
    
    @classmethod
    def max_length(cls) -> int:
        return len(max(cls._member_names_))

    def __str__(self):
        """ Returns the uppercase name (e.g., 'DEBUG') when converted to string. """
        return self.name
    
    def __lt__(self, other):
        """ Compares based on priority. """
        if self.__class__ is other.__class__:
            return self.priority < other.priority
        return NotImplemented

class Table(Enum):
    """ Defines database tables. """
    users = auto()
    guilds = auto()
    user_guild_settings = auto()
    moderation_logs = auto()
    polls = auto()
    user_economies = auto()
    shop_items = auto()
    global_shop_items = auto()
    match_results = auto()

class GlobalItemType(Enum):
    title = auto()
    color = auto()
    badge = auto()
    multiplier = auto()

class Action(Enum):
    """ Defines actions that the discord bot can take. """
    warn = auto()
    mute = auto()
    kick = auto()
    ban = auto()
    unmute = auto()
    unban = auto()
    purge = auto()

class RPS(Enum):
    """ Defines rock-paper-scissors options. """
    rock = auto()
    paper = auto()
    scissors = auto()

class CoinFlip(Enum):
    """ Defines the only results possible for a coin flip! """
    heads = auto()
    tails = auto()

class Rank(Enum):
    """ Defines all available rank titles. """
    rank_0 = ""
    rank_10 = ""
    rank_20 = ""
    rank_30 = ""
    rank_40 = ""
    rank_50 = ""
    rank_60 = ""
    rank_70 = ""
    rank_80 = ""
    rank_90 = ""
    rank_100 = ""

    def __str__(self):
        return self.name.split('_', maxsplit = 1)[1]

class RenderMode(Enum):
    ASCII = auto()
    IMAGE = auto()
