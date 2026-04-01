"""Tests for Ludo AI module."""

import random
import pytest

from ai.ludo_ai import LudoAI


def _make_piece(state="home", track_pos=-1, finish_pos=-1, steps_from_entry=0):
    return {
        "state": state,
        "track_pos": track_pos,
        "finish_pos": finish_pos,
        "steps_from_entry": steps_from_entry,
    }


def _default_board_state(**overrides):
    state = {
        "opponent_positions": [],
        "safe_squares": set(),
        "finish_lane_length": 6,
        "track_length": 52,
        "player_entry": 0,
        "steps_to_finish_entry": 50,
    }
    state.update(overrides)
    return state


class TestChoosePieceBasic:
    def test_returns_valid_index_or_negative_one(self):
        random.seed(42)
        ai = LudoAI()
        pieces = [_make_piece("track", track_pos=10, steps_from_entry=10) for _ in range(4)]
        board = _default_board_state()
        result = ai.choose_piece(pieces, 3, board)
        assert result in [0, 1, 2, 3, -1]

    def test_returns_negative_one_when_no_valid_moves(self):
        random.seed(42)
        ai = LudoAI()
        # All pieces at home and dice is not 6
        pieces = [_make_piece("home") for _ in range(4)]
        board = _default_board_state()
        result = ai.choose_piece(pieces, 3, board)
        assert result == -1

    def test_all_finished_returns_negative_one(self):
        random.seed(42)
        ai = LudoAI()
        pieces = [_make_piece("finished") for _ in range(4)]
        board = _default_board_state()
        result = ai.choose_piece(pieces, 6, board)
        assert result == -1


class TestChoosePiecePreferences:
    def test_prefers_entering_piece_on_six(self):
        """With a roll of 6, AI should prefer entering a home piece."""
        random.seed(42)
        ai = LudoAI()
        pieces = [
            _make_piece("home"),
            _make_piece("track", track_pos=10, steps_from_entry=10),
            _make_piece("home"),
            _make_piece("finished"),
        ]
        board = _default_board_state()
        result = ai.choose_piece(pieces, 6, board)
        # Should pick a home piece (index 0 or 2) to enter the track
        assert result in [0, 2]

    def test_prefers_capture_over_normal_move(self):
        """AI should prefer a move that lands on an opponent."""
        random.seed(42)
        ai = LudoAI()
        # Piece 0 is 3 steps away from an opponent
        # Piece 1 is in the middle of nowhere
        pieces = [
            _make_piece("track", track_pos=7, steps_from_entry=7),
            _make_piece("track", track_pos=20, steps_from_entry=20),
            _make_piece("home"),
            _make_piece("finished"),
        ]
        # Opponent at position 10 (piece 0 + dice 3 = 10)
        board = _default_board_state(opponent_positions=[10])
        result = ai.choose_piece(pieces, 3, board)
        # Piece 0 can capture at position 10
        assert result == 0

    def test_prefers_finishing_piece(self):
        """AI should prefer finishing a piece over other moves."""
        random.seed(42)
        ai = LudoAI()
        pieces = [
            _make_piece("finish_lane", finish_pos=4),  # needs 2 to finish (pos 6)
            _make_piece("track", track_pos=10, steps_from_entry=10),
            _make_piece("home"),
            _make_piece("finished"),
        ]
        board = _default_board_state()
        result = ai.choose_piece(pieces, 2, board)
        assert result == 0

    def test_handles_mixed_states(self):
        """AI handles pieces in various states without crashing."""
        random.seed(42)
        ai = LudoAI()
        pieces = [
            _make_piece("home"),
            _make_piece("track", track_pos=30, steps_from_entry=30),
            _make_piece("finish_lane", finish_pos=3),
            _make_piece("finished"),
        ]
        board = _default_board_state()
        result = ai.choose_piece(pieces, 4, board)
        assert result in [0, 1, 2, 3, -1]


class TestChoosePieceEdgeCases:
    def test_single_piece_on_track(self):
        random.seed(42)
        ai = LudoAI()
        pieces = [
            _make_piece("finished"),
            _make_piece("track", track_pos=5, steps_from_entry=5),
            _make_piece("finished"),
            _make_piece("finished"),
        ]
        board = _default_board_state()
        result = ai.choose_piece(pieces, 4, board)
        assert result == 1

    def test_piece_cant_overshoot_finish_lane(self):
        """Piece in finish lane can't move past the end."""
        random.seed(42)
        ai = LudoAI()
        pieces = [
            _make_piece("finish_lane", finish_pos=5),  # needs exactly 1 to finish
            _make_piece("finished"),
            _make_piece("finished"),
            _make_piece("finished"),
        ]
        board = _default_board_state()
        # Dice 3 would overshoot (5 + 3 = 8 > 6)
        result = ai.choose_piece(pieces, 3, board)
        assert result == -1

    def test_piece_exact_finish(self):
        """Piece at finish_pos=5 with dice=1 finishes exactly."""
        random.seed(42)
        ai = LudoAI()
        pieces = [
            _make_piece("finish_lane", finish_pos=5),
            _make_piece("finished"),
            _make_piece("finished"),
            _make_piece("finished"),
        ]
        board = _default_board_state()
        result = ai.choose_piece(pieces, 1, board)
        assert result == 0
