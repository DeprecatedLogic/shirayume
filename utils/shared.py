from enum import Enum

class Table(Enum):
    """ Database table names. """
    user = "user"
    guild = "guild"
    user_guild_settings = "user_guild_settings"
    moderation_log = "moderation_log"

class Action(Enum):
    """ Actions that the discord bot can take. """
    warn = "warn"
    mute = "timeout"
    kick = "kick"
    ban = "ban"
    unmute = "untimeout"
    unban = "unban"
    purge = "purge"

class RPS(Enum):
    """ Rock-paper-scissors options. """
    rock = "rock"
    paper = "paper"
    scissors = "scissors"

class CoinFlip(Enum):
    """ The only results possible for a coin flip! """
    heads = "heads"
    tails = "tails"

class Rank(Enum):
    """ All available rank titles. """
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
    rank_11 = ""
    rank_12 = ""
    rank_13 = ""
    rank_14 = ""

class SupportedWebsites(Enum):
    """ Websites supported for scraping. """
    my_anime_list = "MyAnimeList"
    brainy_quote = "BrainyQuote"