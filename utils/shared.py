from enum import Enum

class Table(Enum):
    users = "users"
    guilds = "guilds"
    user_guild_settings = "user_guild_settings"
    moderation_logs = "moderation_logs"

class Action(Enum):
    warn = "warn"
    mute = "mute"
    kick = "kick"
    ban = "ban"
    unmute = "unmute"
    unban = "unban"

class RPS(Enum):
    rock = "rock"
    paper = "paper"
    scissors = "scissors"

class CoinFlip(Enum):
    heads = "heads"
    tails = "tails"
