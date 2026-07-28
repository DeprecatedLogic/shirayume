import discord
from typing import List, Optional
from services.matchmaking.shared import GameType
from services.matchmaking.match import Match
from cogs.matchmaking import renderers
from utils import helpers

def lobby_embed(game_type: GameType, leader: discord.User, team_members: List[discord.User]) -> discord.Embed:
    members_str = "\n".join([f"• {user.mention}" for user in team_members])
    embed = helpers.embed_generator(
        title=f"⚔️ GvG Matchmaking Lobby ({game_type.name})",
        description=f"**Lobby Leader:** {leader.mention}\n\n**Current Team Members:**\n{members_str}\n\nClick **Join Team** to join, or **Find Match** when ready!"
    )
    return embed

def match_status_embed(match: Match, state: dict, last_move_user: Optional[int] = None, use_image: bool = False) -> discord.Embed:
    if state.get("is_over"):
        turn_indicator = "🏁 **Game Over**"
    else:
        is_turn_g1 = state["current_turn"] == match.guild1_id
        turn_indicator = f"🟢 **Guild {match.guild1_id}'s Turn**" if is_turn_g1 else f"🔴 **Guild {match.guild2_id}'s Turn**"
    
    status_text = f"**Status:** {turn_indicator}\n"
    if state.get("in_check") and not state.get("is_checkmate"):
        status_text += "**CHECK!**\n"

    if use_image:
        description = status_text
    else:
        board_display = renderers.render_ascii_board(state["board_fen"])
        description = f"{board_display}\n{status_text}"
    
    embed = helpers.embed_generator(
        title=f"♟️ GvG Chess: Guild {match.guild1_id} vs Guild {match.guild2_id}",
        description=description
    )
    
    if use_image:
        embed.set_image(url="attachment://chessboard.png")

    if last_move_user:
        embed.set_footer(text=f"Last move made by User <@{last_move_user}>")
        
    return embed

def match_result_embed(match: Match, winner_guild_id: Optional[int]) -> discord.Embed:
    if winner_guild_id is None:
        title = "Match Ended. It's a Draw!"
        desc = "The game concluded in a draw or stalemate."
    else:
        title = f"🏆 Match Over. Guild {winner_guild_id} Victorious!"
        desc = f"Congratulations to Guild {winner_guild_id} for winning the match!"

    embed = helpers.embed_generator(
        title=title,
        description=desc
    )
    return embed