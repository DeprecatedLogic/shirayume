import discord
from typing import Dict, Tuple
from services.matchmaking.match import Match
from services.matchmaking.shared import MatchStatus
from cogs.matchmaking import embeds, views, renderers
from utils import helpers, shared
from utils.shared import RenderMode

RENDER_MODE = RenderMode.ASCII

ACTIVE_MATCH_THREADS: Dict[str, Dict[int, Tuple[discord.Thread, int]]] = {}

async def setup_match_threads(bot: discord.Client, match: Match):
    """Creates dedicated match threads in both participating guilds using recorded channel IDs."""
    ACTIVE_MATCH_THREADS[match.match_id] = {}
    state = match.game.get_state()
    view = views.MatchView(match.match_id)

    guild_configs = [
        (match.guild1_id, match.guild1_channel_id, match.guild2_id),
        (match.guild2_id, match.guild2_channel_id, match.guild1_id),
    ]

    for guild_id, channel_id, opponent_guild_id in guild_configs:
        try:
            channel = bot.get_channel(channel_id)
            if not channel:
                channel = await bot.fetch_channel(channel_id)

            thread = await channel.create_thread(
                name=f"⚔️-gvg-chess-vs-guild-{opponent_guild_id}",
                type=discord.ChannelType.public_thread
            )

            if RENDER_MODE == RenderMode.IMAGE:
                image_board = await renderers.render_image_board(state["board_fen"])
                embed = embeds.match_status_embed(match, state, use_image=True)
                msg = await thread.send(embed=embed, file=image_board, view=view)
            else:
                embed = embeds.match_status_embed(match, state, use_image=False)
                msg = await thread.send(embed=embed, view=view)

            ACTIVE_MATCH_THREADS[match.match_id][guild_id] = (thread, msg.id)
        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description=f"Failed to create match thread for Guild {guild_id} in Channel {channel_id}: {e}"
            )

    helpers.custom_print(
        level=shared.LogLevel.INFO,
        description=f"GvG Match threads created for Match {match.match_id}"
    )

async def update_match_threads(bot: discord.Client, match: Match, last_move_user: int, last_move_uci: str | None = None):
    """Edits the active board embed in all participating guild threads."""
    if match.match_id not in ACTIVE_MATCH_THREADS:
        return

    state = match.game.get_state()
    
    for guild_id, (thread, msg_id) in ACTIVE_MATCH_THREADS[match.match_id].items():
        try:
            msg = await thread.fetch_message(msg_id)
            if match.status == MatchStatus.FINISHED:
                res_embed = embeds.match_result_embed(match, match.winner_guild_id)
                await msg.edit(embed=res_embed, view=None, attachments=[])
                await thread.send("🏆 Match concluded!")
                await thread.edit(archived=True, locked=True)
            else:
                if RENDER_MODE == RenderMode.IMAGE:
                    image_board = await renderers.render_image_board(state["board_fen"], last_move_uci)
                    new_embed = embeds.match_status_embed(match, state, last_move_user, use_image=True)
                    await msg.edit(embed=new_embed, attachments=[image_board])
                else:
                    new_embed = embeds.match_status_embed(match, state, last_move_user, use_image=False)
                    await msg.edit(embed=new_embed)
                    
        except Exception as e:
            helpers.custom_print(
                level=shared.LogLevel.ERROR,
                description=f"Failed to update GvG thread for Guild {guild_id}: {e}"
            )

    if match.status == MatchStatus.FINISHED:
        ACTIVE_MATCH_THREADS.pop(match.match_id, None)