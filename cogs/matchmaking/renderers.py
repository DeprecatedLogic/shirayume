import io
import asyncio
import chess
import chess.svg
import cairosvg
from typing import Tuple, Optional
import discord

# ASCII Character Mapping
CHESS_EMOJIS = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙', # White
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟', # Black
    '.': '·'
}

def render_ascii_board(fen: str) -> str:
    """Converts FEN to ASCII grid."""
    position = fen.split()[0]
    rows = position.split('/')
    board_str = "```\n  a b c d e f g h\n"
    
    for rank_idx, row in enumerate(rows):
        rank_num = 8 - rank_idx
        board_str += f"{rank_num} "
        for char in row:
            if char.isdigit():
                board_str += ". " * int(char)
            else:
                board_str += f"{CHESS_EMOJIS.get(char, char)} "
        board_str += f"{rank_num}\n"
        
    board_str += "  a b c d e f g h\n```"
    return board_str

def _generate_png_sync(fen: str, last_move_uci: Optional[str] = None) -> io.BytesIO:
    """
    CPU-Bound Sync Function: Converts FEN to SVG via python-chess,
    then renders SVG to PNG using cairosvg.
    """
    board = chess.Board(fen)
    last_move = chess.Move.from_uci(last_move_uci) if last_move_uci else None
    
    # Generate high-res SVG board from python-chess engine
    svg_data = chess.svg.board(
        board=board,
        lastmove=last_move,
        size=400,
        style="""
            .square.light { fill: #f0d9b5; }
            .square.dark { fill: #b58863; }
        """
    )
    
    # Convert SVG string to PNG byte buffer
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode('utf-8'))
    buffer = io.BytesIO(png_bytes)
    buffer.seek(0)
    return buffer

async def render_image_board(fen: str, last_move_uci: Optional[str] = None) -> discord.File:
    """
    Async Wrapper: Offloads CPU image rendering to OS worker threads (Leverages No-GIL Python).
    """
    buffer = await asyncio.to_thread(_generate_png_sync, fen, last_move_uci)
    return discord.File(fp=buffer, filename="chessboard.png")