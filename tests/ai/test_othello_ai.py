"""Tests for Othello AI module."""

import pytest

from ai.othello_ai import (
    EMPTY, BLACK, WHITE,
    get_valid_moves, apply_move, check_game_over, OthelloAI,
)


def initial_board():
    """Standard Othello starting position."""
    board = [[EMPTY] * 8 for _ in range(8)]
    board[3][3] = WHITE
    board[3][4] = BLACK
    board[4][3] = BLACK
    board[4][4] = WHITE
    return board


# ---------- get_valid_moves tests ----------

class TestGetValidMoves:
    def test_initial_board_black_has_4_moves(self):
        board = initial_board()
        moves = get_valid_moves(board, BLACK)
        assert len(moves) == 4
        expected = {(2, 3), (3, 2), (4, 5), (5, 4)}
        assert set(moves) == expected

    def test_initial_board_white_has_4_moves(self):
        board = initial_board()
        moves = get_valid_moves(board, WHITE)
        assert len(moves) == 4

    def test_no_moves_on_empty_board(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        assert get_valid_moves(board, BLACK) == []

    def test_no_moves_when_no_opponent(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        board[0][0] = BLACK
        # No white pieces to flip, so no valid moves for black
        assert get_valid_moves(board, BLACK) == []


# ---------- apply_move tests ----------

class TestApplyMove:
    def test_flips_correct_pieces(self):
        board = initial_board()
        # Black plays (2,3) — should flip white piece at (3,3)
        new_board = apply_move(board, 2, 3, BLACK)
        assert new_board[2][3] == BLACK
        assert new_board[3][3] == BLACK  # flipped from WHITE
        assert new_board[3][4] == BLACK  # unchanged
        assert new_board[4][4] == WHITE  # unchanged

    def test_does_not_mutate_original(self):
        board = initial_board()
        apply_move(board, 2, 3, BLACK)
        assert board[3][3] == WHITE  # original unchanged

    def test_flips_multiple_directions(self):
        """Set up a board where a move flips in two directions."""
        board = [[EMPTY] * 8 for _ in range(8)]
        board[0][0] = BLACK
        board[1][1] = WHITE
        board[2][0] = BLACK
        board[1][0] = WHITE
        # Playing at (2,2) should flip (1,1) diagonally
        new_board = apply_move(board, 2, 2, BLACK)
        assert new_board[2][2] == BLACK
        assert new_board[1][1] == BLACK  # flipped


# ---------- check_game_over tests ----------

class TestCheckGameOver:
    def test_not_over_at_start(self):
        board = initial_board()
        assert check_game_over(board) is False

    def test_over_when_no_moves_for_both(self):
        # All one color — neither side can move
        board = [[BLACK] * 8 for _ in range(8)]
        assert check_game_over(board) is True

    def test_over_on_empty_board(self):
        board = [[EMPTY] * 8 for _ in range(8)]
        assert check_game_over(board) is True


# ---------- AI behaviour tests ----------

class TestOthelloAI:
    def setup_method(self):
        self.ai = OthelloAI(depth=3)

    def test_ai_returns_valid_move_for_black(self):
        board = initial_board()
        move = self.ai.get_move(board, BLACK)
        assert move is not None
        valid = get_valid_moves(board, BLACK)
        assert move in valid

    def test_ai_returns_valid_move_for_white(self):
        board = initial_board()
        # After black plays, white should have valid moves
        board = apply_move(board, 2, 3, BLACK)
        move = self.ai.get_move(board, WHITE)
        assert move is not None
        valid = get_valid_moves(board, WHITE)
        assert move in valid

    def test_ai_returns_none_when_no_moves(self):
        # Board where one side has no moves
        board = [[EMPTY] * 8 for _ in range(8)]
        board[0][0] = BLACK
        # No white pieces, so black has no valid moves (nothing to flip)
        move = self.ai.get_move(board, BLACK)
        assert move is None

    def test_ai_handles_pass(self):
        """When AI has no moves it should return None (pass)."""
        board = [[WHITE] * 8 for _ in range(8)]
        # Black cannot play anywhere on an all-white board
        move = self.ai.get_move(board, BLACK)
        assert move is None

    def test_ai_does_not_crash_mid_game(self):
        """Play several moves and verify AI keeps returning valid moves."""
        board = initial_board()
        colors = [BLACK, WHITE]
        for i in range(10):
            color = colors[i % 2]
            moves = get_valid_moves(board, color)
            if not moves:
                continue
            move = self.ai.get_move(board, color)
            assert move in moves
            board = apply_move(board, move[0], move[1], color)
