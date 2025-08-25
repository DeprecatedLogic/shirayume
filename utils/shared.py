from enum import Enum

class Action(Enum):
    warn = "warn"
    mute = "mute"
    kick = "kick"
    ban = "ban"
    unmute = "unmute"
    unban = "unban"
