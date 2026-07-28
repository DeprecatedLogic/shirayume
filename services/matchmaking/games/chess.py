import chess
from typing import Dict, Any
from services.matchmaking.games.base import BaseGame

class ChessGame(BaseGame):
    def __init__(self, guild1_id: int, guild2_id: int):
        super().__init__(guild1_id, guild2_id)
        
        # Initialize the optimized chess board
        self.board = chess.Board()
        
        # Assign colors to guilds
        self.white_guild_id = guild1_id
        self.black_guild_id = guild2_id
        
        # Track if the game is over and the winner
        self.is_over = False
        self.winner_guild_id = None
        
        # Ensure white starts
        self.current_turn_guild_id = guild1_id

    def process_turn(self, guild_id: int, user_id: int, move_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates and processes a chess move. Accepts UCI (e.g., 'e2e4') or SAN (e.g., 'Nf3').
        Always guarantees a UCI string output for correct visual rendering.
        """
        if self.is_over:
            return {"success": False, "reason": "Game is already over."}
            
        if self.current_turn_guild_id != guild_id:
            return {"success": False, "reason": "Not your guild's turn."}

        # Extract move notation
        move_str = move_data.get("move")
        if not move_str:
            from_pos = move_data.get("from")
            to_pos = move_data.get("to")
            if from_pos and to_pos:
                move_str = f"{from_pos}{to_pos}"
            else:
                return {"success": False, "reason": "Invalid move notation."}

        move_applied = False
        uci_str = ""

        # Try UCI first
        try:
            move_obj = chess.Move.from_uci(move_str)
            if move_obj in self.board.legal_moves:
                self.board.push(move_obj)
                move_applied = True
                uci_str = move_obj.uci()
        except (ValueError, chess.InvalidMoveError):
            pass

        # Fallback to Standard Algebraic Notation (SAN)
        if not move_applied:
            try:
                move_obj = self.board.push_san(move_str)
                move_applied = True
                uci_str = move_obj.uci()
            except (ValueError, chess.InvalidMoveError, chess.IllegalMoveError):
                return {"success": False, "reason": f"Illegal move: {move_str}. Use valid UCI or SAN format."}

        # Check for game-ending conditions
        outcome = self.board.outcome()
        if outcome:
            self.is_over = True
            if outcome.winner is True: 
                self.winner_guild_id = self.white_guild_id
            elif outcome.winner is False: 
                self.winner_guild_id = self.black_guild_id
            else: 
                self.winner_guild_id = None

        # Switch turn
        self.current_turn_guild_id = self.guild2_id if self.current_turn_guild_id == self.guild1_id else self.guild1_id

        return {
            "success": True,
            "move": uci_str,
            "is_over": self.is_over,
            "winner_guild_id": self.winner_guild_id,
            "next_turn_guild_id": self.current_turn_guild_id
        }

    def get_state(self) -> Dict[str, Any]:
        """Returns the current state of the game in a serializable dictionary."""
        return {
            "board_fen": self.board.fen(),
            "current_turn": self.current_turn_guild_id,
            "is_over": self.is_over,
            "winner_guild_id": self.winner_guild_id,
            "in_check": self.board.is_check(),
            "is_checkmate": self.board.is_checkmate(),
            "is_stalemate": self.board.is_stalemate()
        }