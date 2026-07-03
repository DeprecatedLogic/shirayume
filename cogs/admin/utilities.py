import discord
from discord import app_commands
from discord.ext import commands
from utils import shared, helpers
from typing import Literal, Optional
from pathlib import Path

@commands.is_owner()
@commands.command("shutdown")
async def shutdown(ctx: commands.Context) -> None:
    """ Disconnects bot by closing the client."""

    embed = helpers.embed_generator(
            title = "Shutting Down",
            description = "Vanishing into the void... If I don't return, delete my browser history. :saluting_face:",
            color = (205, 85, 0)
        )
    ctx.send(embed=embed)
    await shared.SHIRAYUME.close()

    helpers.custom_print(
        level = shared.LogLevel.INFO,
        function_name = "on_guild_join",
        description = f"Bot was shutdown by {ctx.message.author.name}"
    )

@commands.guild_only()
@commands.is_owner()
@commands.command("sync")
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object],
            spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    """ Syncs commands based on spec.
    
    ~: sync
    *: copy global & sync
    ^: clear & sync
    
    If spec is left None, syncs commands globally.
    """
    embed = helpers.embed_generator(
        title="Syncing",
        description="This might take a while. Syncing..."
    )
    temp_msg = ctx.send(embed=embed)

    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild = ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild = ctx.guild)
            synced = await ctx.bot.tree.sync(guild = ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild = ctx.guild)
            await ctx.bot.tree.sync(guild = ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await temp_msg.message.delete()
        embed = helpers.embed_generator(
            title="Syncing",
            description=f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        await ctx.send(embed=embed)
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild = guild)
        except discord.HTTPException as e:
            helpers.custom_print(
                level = shared.LogLevel.INFO,
                function_name = "sync",
                description = f"An HTTP exception has occured: {e}"
            )
        else:
            ret += 1

    try:
        await temp_msg.message.delete()
        await temp_msg.delete()
    except:
        pass

    embed = helpers.embed_generator(
        title="Syncing",
        description=f"Synced the tree to {ret}/{len(guilds)}."
    )
    await ctx.send(embed=embed)

@commands.command("help")
async def help(ctx: commands.Context, args: str = None) -> None:
    """ Help Command.
    
    Parameters
    ----------
    - `ctx`: `commands.Context`
        - The context in which a command is being invoked under.
    - `args`: `str`
        - The command's name to get help for.
    
    """

    embed = helpers.embed_generator(
        title="===== List of supported commands =====",
        description="",
        color=(255, 48, 72)
    )

    slash_comm_names = [comm.name for comm in shared.SHIRAYUME.commands]
    prefix_comm_names = shared.SHIRAYUME.all_commands.keys()

    # No arguments?
    if not args:

        prefix_commands = [str(i + 1) + ". " + x for i, x in enumerate(prefix_comm_names, start = 0)]
        slash_commands = [str(i + 1) + ". " + x for i, x in enumerate(slash_comm_names, start = 0)]

        name = "Prefix Commands"
        embed.add_field(
            name = name,
            value = '-' * len(name) + '\n' + "\n".join(prefix_commands),
            inline = False
        )

        name = "Slash Commands"
        embed.add_field(
            name = name,
            value = '-' * len(name) + '\n' + "\n".join(slash_commands),
            inline = False
        )

        name = "Details"
        embed.add_field(
            name = name,
            value = '-' * len(
                name) + '\n' + f"Type `{shared.SHIRAYUME.command_prefix}help <command_name>` for more details about a command.",
            inline = False
        )

    elif args in slash_comm_names:
        embed.add_field(
            name = args,
            value = shared.SHIRAYUME.get_command(args).help
        )
    else:
        embed.add_field(
            name = "Couldn't find that command!",
            value = "Do you think I'm wikipedia or what...?"
        )
    
    await ctx.send(embed = embed)

@commands.is_owner()
@commands.command("upload_pfp")
async def upload_pfp(ctx: commands.Context, image_path: str = None) -> None:
    """ Uploads a profile picture for the bot.
    
    Parameters
    ----------
    - ctx (commands.Context): The context in which a command is being invoked under.
    - image_path (str): The path of the image to upload as a profile picture.
    
    """
    user = ctx.message.author.global_name

    if not image_path:
        helpers.custom_print(
            level = shared.LogLevel.INFO,
            function_name = "upload_pfp",
            description = "Image path is empty."
        )
        embed = helpers.embed_generator(
            title="Empty image path",
            description=f"You forgot the image path, {user}. Focus pocus please! >w<",
            color = (204, 166, 0)
        )
        return


    msg = await util.send_text(
        channel = ctx.channel,
        title = 'Uploading profile picture...',
        description = f'This may take a while, {user}. Please be patient... :sweat_smile:',
        color = (53, 68, 84)
    )

    try:
        # Remove quotes and leading/trailing whitespaces from the image path
        image_path = image_path.replace('"', "").replace("'", "").strip()
        image_path = Path(image_path)
        
        if not image_path.is_file():
            raise Exception("Path provided is not a file")
        elif image_path.suffix not in ("jpeg", "jpg", "png", "gif"):
            raise Exception("File suffix is invalid")

        with image_path.open("rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        headers = {
            "Authorization": f"Bot {os.getenv('TOKEN')}",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0",
            "Content-Type": "application/json"
        }

        data = {
            "avatar": f"data:image/png;base64,{encoded_image}"
        }

        url = "https://discord.com/api/v9/users/@me"

        response = requests.patch(url, headers = headers, json = data)

        if response.status_code != 200:
            embed = helpers.embed_generator(
                title = "Failed to upload the profile picture.",
                description = f"It seems like an error has occured! Please try again later... :disappointed:",
                color = discord.Color.from_rgb(204, 166, 0)
            )
            await msg.edit(embed = embed)

            helpers.custom_print(
                level = shared.LogLevel.INFO,
                function_name = "upload_pfp",
                description = f"HTML Request Error: Response status code is {response.status_code} instead of 200"
            )
            helpers.custom_print(
                level = shared.LogLevel.INFO,
                function_name = "upload_pfp",
                description = f"Response json: {response.json()}"
            )
            return

        await msg.edit(embed = discord.Embed(
            title = 'Profile picture uploaded succesfully.',
            description = f'Thank you {user} for keeping my profile picture up to date! :smiling_face:',
            color = discord.Color.from_rgb(79, 213, 128)
        )
        )
        helpers.custom_print(
            level = shared.LogLevel.INFO,
            function_name = "upload_pfp",
            description = "Profile picture uploaded!"
        )

    except Exception as e:
        embed = helpers.embed_generator(
            title = 'Failed to upload the profile picture.',
            description = f'It seems like an error has occured! Please try again later... :disappointed:',
            color = discord.Color.from_rgb(204, 166, 0)
        )
        await msg.edit(embed=embed)
        helpers.custom_print(
            level = shared.LogLevel.INFO,
            function_name = "upload_pfp",
            description = f"Failed to upload the profile picture, exception: {e}"
        )

@commands.is_owner()
@commands.command(name="upload_banner")
async def upload_banner(ctx: commands.Context, image_path: str = None) -> None:
    """ Uploads a banner for the bot.
    
    Parameters
    ----------
    - `ctx`: `commands.Context`
        - The context in which a command is being invoked under.
    - `image_path`: `str`
        - The path of the image to upload as a banner.
    
    """
    user = ctx.message.author.global_name
    
    if not image_path:
        helpers.custom_print(
            function_name = "upload_pfp",
            level = shared.LogLevel.INFO,
            description = [
                "Image path is empty."
            ],
            rgb_values = [
                (206, 136, 108)
            ],
            add_datetime = True,
            sep = '',
            begin = f'{term.color_rgb(255, 30, 30)}FAILED',
            end = '\n'
        )
        embed = helpers.embed_generator(
            title="Empty Image Path...",
            description = f"You forgot the image path {user}. Focus pocus please! >w<",
            color = (204, 166, 0)
        )
        ctx.send(embed=embed)
        return

    embed = helpers.embed_generator(
        title = "Uploading banner...",
        description = f"This may take a while {user}, please be patient... 😅",
        color = (53, 68, 84)
    )
    msg = ctx.send(embed=embed)

    try:
        # Remove quotes and leading/trailing whitespaces from the image path
        image_path = image_path.replace('"', "").replace("'", "").strip()

        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        headers = {
            "Authorization": f"Bot {os.getenv('TOKEN')}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
            "Content-Type": "application/json"
        }

        data = {
            "banner": f"data:image/png;base64,{encoded_image}"
        }

        url = "https://discord.com/api/v9/users/@me"

        response = requests.patch(url, headers = headers, json = data)

        if response.status_code != 200:
            await msg.edit(embed = discord.Embed(
                title = 'Failed to upload the banner.',
                description = f'It seems like an error has occured! Please try again later... 😞',
                color = discord.Color.from_rgb(204, 166, 0)
            )
            )
            helpers.custom_print(
                function_name = "upload_banner",
                level = shared.LogLevel.INFO,
                description = [
                    "HTML Request Error: Response status code is",
                    f"{response.status_code}",
                    "instead of 200"
                ],
                rgb_values = [
                    (206, 136, 108),
                    (140, 217, 225),
                    (206, 136, 108)
                ],
                add_datetime = True,
                sep = ' ',
                begin = f'{term.color_rgb(255, 30, 30)}ERROR',
                end = '\n'
            )
            helpers.custom_print(
                function_name = "upload_banner",
                level = shared.LogLevel.INFO,
                description = [
                    "Response json:",
                    f"{response.json()}"
                ],
                rgb_values = [
                    (206, 136, 108),
                    (140, 217, 225)
                ],
                add_datetime = True,
                sep = '\n\n',
                begin = f'{term.color_rgb(255, 30, 30)}ERROR',
                end = '\n'
            )
            return

        await msg.edit(embed = discord.Embed(
            title = 'Banner uploaded succesfully.',
            description = f'Thank you {user} for keeping my banner up to date! 😊',
            color = discord.Color.from_rgb(79, 213, 128)
        )
        )
        helpers.custom_print(
            function_name = "upload_banner",
            level = shared.LogLevel.INFO,
            description = [
                "Banner uploaded!"
            ],
            rgb_values = [
                (206, 136, 108)
            ],
            add_datetime = True,
            sep = '',
            begin = f'{term.color_rgb(30, 255, 30)}SUCCEEDED',
            end = '\n'
        )

    except Exception as e:
        await msg.edit(embed = discord.Embed(
            title = 'Failed to upload the banner.',
            description = f'It seems like an error has occured! Please try again later... 😞',
            color = discord.Color.from_rgb(204, 166, 0)
        )
        )
        helpers.custom_print(
            function_name = "upload_banner",
            level = shared.LogLevel.INFO,
            description = [
                "Failed to upload the banner, exception:",
                f"{e}"
            ],
            rgb_values = [
                (206, 136, 108),
                (140, 217, 225)
            ],
            add_datetime = True,
            sep = '\n\n',
            begin = f'{term.color_rgb(255, 30, 30)}ERROR',
            end = '\n'
        )

def setup():
    functions = (
        shutdown,
        sync,
        help,
        upload_pfp,
        upload_banner
    )

    for func in functions:
        try:
            shared.SHIRAYUME.add_command(func)
        except:
            pass