"""Tests for ai.backgammon_ai module."""

import pytest
from ai.backgammon_ai import BackgammonAI, initial_board, apply_moves, get_all_legal_moves, AI, PLAYER


@pytest.fixture
def ai():
    return BackgammonAI()


class TestInitialBoard:
    def test_board_length(self):
        board, bar, off = initial_board()
        assert len(board) == 24

    def test_bar_and_off_start_at_zero(self):
        board, bar, off = initial_board()
        assert bar == [0, 0]
        assert off == [0, 0]

    def test_correct_checker_counts(self):
        board, bar, off = initial_board()
        player_count = sum(c for c in board if c > 0)
        ai_count = sum(abs(c) for c in board if c < 0)
        assert player_count == 15
        assert ai_count == 15

    def test_starting_positions(self):
        board, bar, off = initial_board()
        # Player checkers
        assert board[23] == 2
        assert board[12] == 5
        assert board[7] == 3
        assert board[5] == 5
        # AI checkers
        assert board[0] == -2
        assert board[11] == -5
        assert board[16] == -3
        assert board[18] == -5


class TestGetMoves:
    def test_returns_list(self, ai):
        board, bar, off = initial_board()
        moves = ai.get_moves(board, bar, off, [3, 1])
        assert isinstance(moves, list)

    def test_moves_are_tuples(self, ai):
        board, bar, off = initial_board()
        moves = ai.get_moves(board, bar, off, [6, 4])
        for move in moves:
            assert isinstance(move, tuple)
            assert len(move) == 2

    def test_opening_roll_produces_moves(self, ai):
        board, bar, off = initial_board()
        for d1 in range(1, 7):
            for d2 in range(1, 7):
                if d1 == d2:
                    dice = [d1] * 4
                else:
                    dice = [d1, d2]
                moves = ai.get_moves(board, bar, off, dice)
                assert len(moves) > 0, f"No moves for dice {dice}"

    def test_moves_are_legal(self, ai):
        board, bar, off = initial_board()
        dice = [3, 5]
        moves = ai.get_moves(board, bar, off, dice)
        # Verify we can apply the moves without error
        new_board, new_bar, new_off = apply_moves(board, bar, off, moves, AI)
        assert len(new_board) == 24


class TestDoesNotCrash:
    def test_empty_board_with_bar(self, ai):
        board = [0] * 24
        bar = [0, 2]  # AI has 2 on bar
        off = [15, 13]
        moves = ai.get_moves(board, bar, off, [3, 1])
        assert isinstance(moves, list)

    def test_bearing_off_position(self, ai):
        board = [0] * 24
        board[20] = -3
        board[22] = -2
        bar = [0, 0]
        off = [0, 10]
        moves = ai.get_moves(board, bar, off, [2, 4])
        assert isinstance(moves, list)

    def test_doubles(self, ai):
        board, bar, off = initial_board()
        moves = ai.get_moves(board, bar, off, [6, 6, 6, 6])
        assert isinstance(moves, list)

    def test_no_legal_moves(self, ai):
        """When all entry points are blocked, AI on bar has no moves."""
        board = [0] * 24
        # Block points 0-5 with player checkers (2 each)
        for i in range(6):
            board[i] = 2
        bar = [0, 1]
        off = [0, 14]
        moves = ai.get_moves(board, bar, off, [1, 2])
        assert moves == []


class TestGetAllLegalMoves:
    def test_returns_list_of_sequences(self):
        board, bar, off = initial_board()
        sequences = get_all_legal_moves(board, bar, off, [3, 1], AI)
        assert isinstance(sequences, list)
        assert len(sequences) > 0
        for seq in sequences:
            assert isinstance(seq, list)

    def test_max_dice_usage(self):
        """All returned sequences should use the maximum number of dice."""
        board, bar, off = initial_board()
        sequences = get_all_legal_moves(board, bar, off, [4, 2], AI)
        if sequences:
            max_len = max(len(s) for s in sequences)
            for seq in sequences:
                assert len(seq) == max_len
