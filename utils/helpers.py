import discord
from datetime import datetime
import asyncio
from utils import shared

def embed_generator(title: str, description:str, color: tuple[int, int, int] = (255,255,255)) -> discord.Embed:
    r,g,b = color
    
    embed = discord.Embed(
        title = title, 
        description = description, 
        color = discord.Color.from_rgb(r,g,b)
    )

    return embed

def remove_characters(string: str, chars_to_remove: str) -> str:
    # Create a translation table directly without using str.maketrans
    translation_table = {ord(char): None for char in chars_to_remove}

    # Use translate to remove specified characters and return the string
    return string.translate(translation_table)

def custom_print(
    level: shared.LogLevel,
    function_name: str,
    description: str
):
    terminal = shared.GLOBAL_TERMINAL
    default_fg = terminal.color_rgb(255, 255, 255)

    datetime_fg = terminal.color_rgb(101, 101, 185)
    function_fg = terminal.color_rgb(116, 137, 93)

    r, g, b = level.color_rgb
    description_color = terminal.color_rgb(r, g, b)

    print(
        f"{description_color}{level}{' ' * (shared.LogLevel.max_length() - len(level.name))}",
        f"{datetime_fg}{datetime.strftime(datetime.now(), '[%d-%m-%Y %H:%M:%S]')}",
        f"{function_fg}[{function_name}]",
        f"{description_color}{description}",
        default_fg,
        flush = True
    )

async def exec_in_thread(thread_pool, func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, func, *args, **kwargs)
