from enum import Enum
import blessed
GLOBAL_TERMINAL = blessed.Terminal()

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
    user = "user"
    guild = "guild"
    user_guild_settings = "user_guild_settings"
    moderation_log = "moderation_log"

class Action(Enum):
    """ Defines actions that the discord bot can take. """
    warn = "warn"
    mute = "timeout"
    kick = "kick"
    ban = "ban"
    unmute = "untimeout"
    unban = "unban"
    purge = "purge"

class RPS(Enum):
    """ Defines rock-paper-scissors options. """
    rock = "rock"
    paper = "paper"
    scissors = "scissors"

class CoinFlip(Enum):
    """ Defines the only results possible for a coin flip! """
    heads = "heads"
    tails = "tails"

class Rank(Enum):
    """ Defines all available rank titles. """
    rank_0 = ""
    rank_1 = ""
    rank_2 = ""
    rank_3 = ""
    rank_4 = ""
    rank_5 = ""
    rank_6 = ""
    rank_7 = ""
    rank_8 = ""
    rank_9 = ""
    rank_10 = ""

class SupportedWebsites(Enum):
    """ Defines supported websites for scraping. """
    my_anime_list = "MyAnimeList"
    brainy_quote = "BrainyQuote"