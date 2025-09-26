import discord

def embed_generator(title: str, description:str, colour: tuple[int, int, int] = (255,255,255)) -> discord.Embed:
    r,g,b = colour
    
    embed = discord.Embed(
        title = title, 
        description = description, 
        colour = discord.Colour.from_rgb(r,g,b)
    )

    return embed