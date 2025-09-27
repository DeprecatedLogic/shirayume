from enum import Enum

class Table(Enum):
    user = "user"
    guild = "guild"
    user_guild_settings = "user_guild_settings"
    moderation_log = "moderation_log"

class Action(Enum):
    warn = "warn"
    mute = "timeout"
    kick = "kick"
    ban = "ban"
    unmute = "untimeout"
    unban = "unban"
    purge = "purge"

class RPS(Enum):
    rock = "rock"
    paper = "paper"
    scissors = "scissors"

class CoinFlip(Enum):
    heads = "heads"
    tails = "tails"

class Rank(Enum):
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
