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
    rank_0 = "Wet Sock"
    rank_1 = "Microwave Enjoyer"
    rank_2 = "Left Toe Collector"
    rank_3 = "Certified Simp"
    rank_4 = "Hotdog Without Bun"
    rank_5 = "69% Charged Phone"
    rank_6 = "Accidental Incognito Tab"
    rank_7 = "OnlyFans Intern"
    rank_8 = "Half-Eaten Burrito"
    rank_9 = "Big Spoon (no cereal)"
    rank_10 = "Banana Peeler Supreme"
    rank_11 = "Mom's Credit Card"
    rank_12 = "Horny Jail Inmate"
    rank_13 = "Professional Stepbro"
    rank_14 = "CEO of Bad Decisions"
