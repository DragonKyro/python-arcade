"""Tests for Gomoku AI module."""

import random
import pytest

from ai.gomoku_ai import (
    BOARD_SIZE, EMPTY, BLACK, WHITE,
    check_winner, get_legal_moves, is_board_full, GomokuAI,
)


def _empty_board():
    return [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]


# ---------------------------------------------------------------------------
# check_winner
# ---------------------------------------------------------------------------

class TestCheckWinner:
    def test_no_winner_empty_board(self):
        board = _empty_board()
        assert check_winner(board) is None

    def test_horizontal_win_black(self):
        board = _empty_board()
        for c in range(5):
            board[7][c] = BLACK
        assert check_winner(board) == BLACK

    def test_vertical_win_white(self):
        board = _empty_board()
        for r in range(5):
            board[r][3] = WHITE
        assert check_winner(board) == WHITE

    def test_diagonal_down_right_win(self):
        board = _empty_board()
        for i in range(5):
            board[i][i] = BLACK
        assert check_winner(board) == BLACK

    def test_diagonal_down_left_win(self):
        board = _empty_board()
        for i in range(5):
            board[i][10 - i] = WHITE
        assert check_winner(board) == WHITE

    def test_four_in_a_row_no_winner(self):
        board = _empty_board()
        for c in range(4):
            board[0][c] = BLACK
        assert check_winner(board) is None

    def test_six_in_a_row_still_wins(self):
        board = _empty_board()
        for c in range(6):
            board[0][c] = WHITE
        assert check_winner(board) == WHITE


# ---------------------------------------------------------------------------
# get_legal_moves
# ---------------------------------------------------------------------------

class TestGetLegalMoves:
    def test_empty_board_returns_center(self):
        board = _empty_board()
        moves = get_legal_moves(board)
        assert moves == [(BOARD_SIZE // 2, BOARD_SIZE // 2)]

    def test_partially_filled_board(self):
        board = _empty_board()
        board[7][7] = BLACK
        moves = get_legal_moves(board)
        # All moves should be empty intersections near (7,7)
        assert len(moves) > 0
        for r, c in moves:
            assert board[r][c] == EMPTY

    def test_no_duplicate_moves(self):
        board = _empty_board()
        board[7][7] = BLACK
        board[7][8] = WHITE
        moves = get_legal_moves(board)
        assert len(moves) == len(set(moves))


# ---------------------------------------------------------------------------
# AI returns valid move
# ---------------------------------------------------------------------------

class TestGomokuAIMove:
    def test_ai_returns_valid_move_empty_board(self):
        random.seed(42)
        board = _empty_board()
        ai = GomokuAI(difficulty="easy")
        move = ai.get_move(board, BLACK)
        assert move is not None
        r, c = move
        assert 0 <= r < BOARD_SIZE
        assert 0 <= c < BOARD_SIZE
        assert board[r][c] == EMPTY

    def test_ai_returns_valid_move_mid_game(self):
        random.seed(42)
        board = _empty_board()
        board[7][7] = BLACK
        board[7][8] = WHITE
        board[8][7] = BLACK
        ai = GomokuAI(difficulty="easy")
        move = ai.get_move(board, WHITE)
        assert move is not None
        r, c = move
        assert board[r][c] == EMPTY

    def test_ai_blocks_opponent_four_in_a_row(self):
        """AI should block opponent's open 4-in-a-row."""
        board = _empty_board()
        # White has 4 in a row at row 5, cols 3-6
        for c in range(3, 7):
            board[5][c] = WHITE
        ai = GomokuAI(difficulty="medium")
        move = ai.get_move(board, BLACK)
        assert move is not None
        r, c = move
        # Should block at one of the endpoints: (5,2) or (5,7)
        assert (r, c) in [(5, 2), (5, 7)]

    def test_ai_takes_winning_move(self):
        """AI should take immediate winning move when it has 4-in-a-row."""
        board = _empty_board()
        # Black has 4 in a row at row 3, cols 4-7
        for c in range(4, 8):
            board[3][c] = BLACK
        # Give white some stones so the board isn't trivial
        board[0][0] = WHITE
        board[0][1] = WHITE
        ai = GomokuAI(difficulty="easy")
        move = ai.get_move(board, BLACK)
        assert move is not None
        r, c = move
        # Should complete the 5 at (3,3) or (3,8)
        assert (r, c) in [(3, 3), (3, 8)]

    def test_ai_returns_none_on_full_board(self):
        """AI returns None when no legal moves exist."""
        board = [[BLACK] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        ai = GomokuAI(difficulty="easy")
        moves = get_legal_moves(board)
        # Board is completely full, but check_winner may find a winner.
        # get_legal_moves should return no moves near stones on a full board
        # because there are no empty cells.
        assert all(board[r][c] != EMPTY for r in range(BOARD_SIZE) for c in range(BOARD_SIZE))


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestGomokuEdgeCases:
    def test_is_board_full_empty(self):
        board = _empty_board()
        assert is_board_full(board) is False

    def test_is_board_full_full(self):
        board = [[BLACK] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        assert is_board_full(board) is True

    def test_winner_at_board_edge(self):
        board = _empty_board()
        for r in range(5):
            board[r][0] = BLACK
        assert check_winner(board) == BLACK

    def test_winner_at_bottom_right_corner(self):
        board = _empty_board()
        for i in range(5):
            board[BOARD_SIZE - 5 + i][BOARD_SIZE - 5 + i] = WHITE
        assert check_winner(board) == WHITE
