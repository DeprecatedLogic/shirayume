import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.matchmaking.shared import GameType, MatchStatus, QueueEntry
from services.matchmaking.games.chess import ChessGame
from services.matchmaking.queue import MatchmakingQueue
from services.matchmaking.match import Match
from services.matchmaking.manager import MatchmakingManager

class TestChessGame(unittest.TestCase):
    def setUp(self):
        self.guild1 = 111
        self.guild2 = 222
        self.game = ChessGame(self.guild1, self.guild2)

    def test_initialization(self):
        """Test if the game initializes correctly with correct guild assignments."""
        self.assertEqual(self.game.white_guild_id, self.guild1)
        self.assertEqual(self.game.black_guild_id, self.guild2)
        self.assertFalse(self.game.is_over)
        self.assertEqual(self.game.current_turn_guild_id, self.guild1)

    def test_valid_uci_move(self):
        """Test a valid UCI move (e2e4)."""
        result = self.game.process_turn(self.guild1, 1, {"move": "e2e4"})
        self.assertTrue(result["success"])
        self.assertEqual(result["next_turn_guild_id"], self.guild2)
        self.assertEqual(self.game.current_turn_guild_id, self.guild2)

    def test_valid_san_move(self):
        """Test a valid Standard Algebraic Notation move (Nf3)."""
        result = self.game.process_turn(self.guild1, 1, {"move": "Nf3"})
        self.assertTrue(result["success"])

    def test_legacy_from_to_notation(self):
        """Test the legacy from/to dictionary payload."""
        result = self.game.process_turn(self.guild1, 1, {"from": "e2", "to": "e4"})
        self.assertTrue(result["success"])
        self.assertEqual(result["move"], "e2e4")

    def test_invalid_turn(self):
        """Test that a guild cannot move when it is not their turn."""
        self.game.process_turn(self.guild1, 1, {"move": "e2e4"})
        result = self.game.process_turn(self.guild1, 1, {"move": "d2d4"}) # guild1 tries again
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "Not your guild's turn.")

    def test_illegal_move(self):
        """Test that illegal moves are rejected."""
        result = self.game.process_turn(self.guild1, 1, {"move": "e2e5"}) # Invalid pawn move
        self.assertFalse(result["success"])
        self.assertIn("Illegal move", result["reason"])

    def test_checkmate_fools_mate(self):
        """Test game over condition using Fool's Mate."""
        # Guild 1 (White) moves
        self.game.process_turn(self.guild1, 1, {"move": "f2f3"})
        # Guild 2 (Black) moves
        self.game.process_turn(self.guild2, 2, {"move": "e7e5"})
        # Guild 1 (White) moves
        self.game.process_turn(self.guild1, 1, {"move": "g2g4"})
        # Guild 2 (Black) delivers checkmate
        result = self.game.process_turn(self.guild2, 2, {"move": "d8h4"})

        self.assertTrue(result["success"])
        self.assertTrue(self.game.is_over)
        self.assertEqual(self.game.winner_guild_id, self.guild2)
        
        state = self.game.get_state()
        self.assertTrue(state["is_checkmate"])


class TestMatchmakingQueue(unittest.TestCase):
    def setUp(self):
        # Patch the custom logger to avoid console spam during tests
        self.patcher = patch('services.matchmaking.queue.helpers.custom_print')
        self.mock_print = self.patcher.start()
        self.queue = MatchmakingQueue()

    def tearDown(self):
        self.patcher.stop()

    def test_add_to_queue(self):
        """Test adding a team to the queue successfully."""
        success, msg, match = self.queue.add_to_queue(100, [1, 2], GameType.CHESS)
        self.assertTrue(success)
        self.assertIsNone(match)
        self.assertTrue(self.queue.is_user_queued(1))
        self.assertTrue(self.queue.is_user_queued(2))

    def test_user_already_queued(self):
        """Test that a user cannot queue twice."""
        self.queue.add_to_queue(100, [1], GameType.CHESS)
        success, msg, match = self.queue.add_to_queue(100, [1, 2], GameType.CHESS)
        self.assertFalse(success)
        self.assertEqual(msg, "User 1 is already in a queue.")

    def test_match_creation(self):
        """Test that two teams from different guilds trigger a match."""
        # Guild 1 queues
        self.queue.add_to_queue(100, [1], GameType.CHESS)
        # Guild 2 queues, should match with Guild 1
        success, msg, match_tuple = self.queue.add_to_queue(200, [2], GameType.CHESS)
        
        self.assertTrue(success)
        self.assertIsNotNone(match_tuple)
        
        entry1, entry2 = match_tuple
        self.assertEqual(entry1.guild_id, 100)
        self.assertEqual(entry2.guild_id, 200)

        # Users should be removed from queue index upon match creation
        self.assertFalse(self.queue.is_user_queued(1))
        self.assertFalse(self.queue.is_user_queued(2))

    def test_remove_from_queue(self):
        """Test removing a queued team by a single user's ID."""
        self.queue.add_to_queue(100, [1, 2, 3], GameType.TYPING)
        self.assertTrue(self.queue.is_user_queued(3))
        
        removed = self.queue.remove_from_queue(2)
        self.assertTrue(removed)
        
        # Verify the entire team is dequeued
        self.assertFalse(self.queue.is_user_queued(1))
        self.assertFalse(self.queue.is_user_queued(2))
        self.assertFalse(self.queue.is_user_queued(3))


class TestMatch(unittest.TestCase):
    def setUp(self):
        self.patcher_print = patch('services.matchmaking.match.helpers.custom_print')
        self.mock_print = self.patcher_print.start()
        
        # Mock the DB_MANAGER to test if record_guild_match_result is called
        self.patcher_db = patch('services.matchmaking.match.database_manager')
        self.mock_db = self.patcher_db.start()
        self.mock_db.DB_MANAGER.record_guild_match_result = MagicMock()

        self.match = Match(100, [1], 200, [2], GameType.CHESS)

    def tearDown(self):
        self.patcher_print.stop()
        self.patcher_db.stop()

    def test_is_user_in_match(self):
        self.assertTrue(self.match.is_user_in_match(1))
        self.assertTrue(self.match.is_user_in_match(2))
        self.assertFalse(self.match.is_user_in_match(99))

    def test_make_valid_move(self):
        """Test move delegation to the underlying game."""
        result = self.match.make_move(100, 1, {"move": "e2e4"})
        self.assertTrue(result["success"])
        self.assertEqual(self.match.status, MatchStatus.IN_PROGRESS)

    def test_make_move_unauthorized_user(self):
        """Test that an external user cannot interfere with the match."""
        result = self.match.make_move(100, 99, {"move": "e2e4"})
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "You are not a participant in this match.")

    def test_forfeit(self):
        """Test the forfeit mechanism assigns the correct winner."""
        result = self.match.forfeit(100) # Guild 100 forfeits
        self.assertTrue(result["success"])
        self.assertEqual(result["winner_guild_id"], 200)
        self.assertEqual(self.match.status, MatchStatus.FINISHED)
        self.assertIsNotNone(self.match.ended_at)


class TestMatchmakingManager(unittest.TestCase):
    def setUp(self):
        self.patcher_print = patch('services.matchmaking.manager.helpers.custom_print')
        self.patcher_db = patch('services.matchmaking.match.database_manager')
        self.mock_print = self.patcher_print.start()
        self.mock_db = self.patcher_db.start()
        
        self.manager = MatchmakingManager()

    def tearDown(self):
        self.patcher_print.stop()
        self.patcher_db.stop()

    def test_join_queue_and_match(self):
        """Test full flow: queuing, matching, and active match registration."""
        # Guild 1 queues
        success, msg, match = self.manager.join_queue(100, [1, 2], GameType.CHESS)
        self.assertTrue(success)
        self.assertIsNone(match)

        # Guild 2 queues and matches
        success, msg, match = self.manager.join_queue(200, [3, 4], GameType.CHESS)
        self.assertTrue(success)
        self.assertIsNotNone(match)
        self.assertEqual(match.guild1_id, 100)
        self.assertEqual(match.guild2_id, 200)

        # Verify active dictionaries are updated
        self.assertEqual(self.manager.user_active_match[1], match.match_id)
        self.assertEqual(self.manager.user_active_match[4], match.match_id)
        self.assertIn(match.match_id, self.manager.active_matches)

    def test_prevent_dual_queuing(self):
        """Test that a user in an active match cannot join another queue."""
        self.manager.join_queue(100, [1], GameType.CHESS)
        self.manager.join_queue(200, [2], GameType.CHESS) # Match created!
        
        # User 1 tries to queue for Hangman while in a Chess match
        success, msg, match = self.manager.join_queue(100, [1], GameType.HANGMAN)
        self.assertFalse(success)
        self.assertIn("already in an active match", msg)

    def test_cleanup_after_forfeit(self):
        """Test that matches are cleaned up properly when they end."""
        self.manager.join_queue(100, [1], GameType.CHESS)
        _, _, match = self.manager.join_queue(200, [2], GameType.CHESS)

        self.assertIn(1, self.manager.user_active_match)

        # User 1 forfeits
        success, result = self.manager.forfeit_match(100, 1)
        self.assertTrue(success)
        self.assertEqual(result["winner_guild_id"], 200)

        # Verify O(1) maps are cleaned
        self.assertNotIn(1, self.manager.user_active_match)
        self.assertNotIn(2, self.manager.user_active_match)
        self.assertNotIn(match.match_id, self.manager.active_matches)

if __name__ == '__main__':
    unittest.main()