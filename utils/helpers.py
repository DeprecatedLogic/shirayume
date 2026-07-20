import discord
from datetime import datetime
import asyncio
from utils import shared
from io import BytesIO
from colorthief import ColorThief
import inspect
from database import database_manager

DEFAULT_COLOR = (255, 255, 255)


def embed_generator(title: str, description:str, color: tuple[int, int, int] | discord.Color = None) -> discord.Embed:
    """
    _summary_

    Args:
        title (str): _description_
        description (str): _description_
        color (tuple[int, int, int] | discord.Color, optional): _description_. Defaults to DEFAULT_COLOR.

    Returns:
        discord.Embed: _description_
    """
    if color is None:
        color = discord.Color.from_rgb(*DEFAULT_COLOR)
    elif isinstance(color, tuple):
        r,g,b = color
        color = discord.Color.from_rgb(r,g,b)
    
    embed = discord.Embed(
        title=title, 
        description=description, 
        color=color
    )

    return embed

def remove_characters(string: str, chars_to_remove: str) -> str:
    """
    _summary_

    Args:
        string (str): _description_
        chars_to_remove (str): _description_

    Returns:
        str: _description_
    """
    # Create a translation table directly without using str.maketrans
    translation_table = {ord(char): None for char in chars_to_remove}

    # Use translate to remove specified characters and return the string
    return string.translate(translation_table)

def custom_print(level: shared.LogLevel, description: str):
    """
    _summary_

    Args:
        level (shared.LogLevel): _description_
        description (str): _description_
    """
    terminal = shared.GLOBAL_TERMINAL
    default_fg = terminal.color_rgb(255, 255, 255)

    datetime_fg = terminal.color_rgb(101, 101, 185)
    function_fg = terminal.color_rgb(116, 137, 93)

    r, g, b = level.color_rgb
    description_color = terminal.color_rgb(r, g, b)

    # Get caller information
    frame = inspect.currentframe()
    while frame:
        frame = frame.f_back
        if frame and frame.f_globals.get("__name__") != __name__:
            break

    module = inspect.getmodule(frame)
    module_name = module.__name__ if module else "<unknown>"

    function_name = frame.f_code.co_name

    # Get class name if called from a method
    class_name = ""
    if "self" in frame.f_locals:
        class_name = f"{frame.f_locals['self'].__class__.__name__}."

    function_path = f"{module_name}.{class_name}{function_name}"

    print(
        f"{description_color}{level}{' ' * (shared.LogLevel.max_length() - len(level.name))}",
        f"{datetime_fg}{datetime.strftime(datetime.now(), '[%Y-%m-%d %H:%M:%S]')}",
        f"{function_fg}[{function_path}]",
        f"{description_color}{description}",
        default_fg,
        flush=True
    )

async def update_default_color():
    """
    _summary_
    """
    asset = shared.SHIRAYUME.user.display_avatar
    avatar_bytes = await asset.read()
    global DEFAULT_COLOR
    DEFAULT_COLOR = ColorThief(BytesIO(avatar_bytes)).get_color(quality=1)
    custom_print(
        level=shared.LogLevel.INFO,
        description=f"Shirayume's default color set to: {DEFAULT_COLOR}"
    )
