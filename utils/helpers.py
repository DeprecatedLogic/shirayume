import discord

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