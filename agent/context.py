from dataclasses import dataclass
import discord

@dataclass
class DiscordToolContext:
    bot: discord.Client