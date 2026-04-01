"""Tests for Tic-Tac-Toe AI module."""

import random
import pytest

from ai.tictactoe_ai import check_winner, get_winning_line, TicTacToeAI


def empty_board():
    return [[None, None, None] for _ in range(3)]


# ---------- check_winner tests ----------

class TestCheckWinner:
    def test_x_wins_row(self):
        board = [
            ["X", "X", "X"],
            [None, "O", None],
            ["O", None, None],
        ]
        assert check_winner(board) == "X"

    def test_x_wins_column(self):
        board = [
            ["X", "O", None],
            ["X", "O", None],
            ["X", None, None],
        ]
        assert check_winner(board) == "X"

    def test_x_wins_diagonal(self):
        board = [
            ["X", "O", None],
            [None, "X", "O"],
            [None, None, "X"],
        ]
        assert check_winner(board) == "X"

    def test_o_wins_row(self):
        board = [
            ["X", None, "X"],
            ["O", "O", "O"],
            [None, "X", None],
        ]
        assert check_winner(board) == "O"

    def test_o_wins_anti_diagonal(self):
        board = [
            [None, None, "O"],
            ["X", "O", "X"],
            ["O", None, None],
        ]
        assert check_winner(board) == "O"

    def test_draw(self):
        board = [
            ["X", "O", "X"],
            ["X", "X", "O"],
            ["O", "X", "O"],
        ]
        assert check_winner(board) == "draw"

    def test_in_progress_empty(self):
        assert check_winner(empty_board()) is None

    def test_in_progress_partial(self):
        board = [
            ["X", None, None],
            [None, "O", None],
            [None, None, None],
        ]
        assert check_winner(board) is None


# ---------- get_winning_line tests ----------

class TestGetWinningLine:
    def test_returns_row_cells(self):
        board = [
            [None, None, None],
            ["O", "O", "O"],
            ["X", "X", None],
        ]
        line = get_winning_line(board)
        assert line == [(1, 0), (1, 1), (1, 2)]

    def test_returns_diagonal_cells(self):
        board = [
            ["X", "O", None],
            [None, "X", "O"],
            [None, None, "X"],
        ]
        line = get_winning_line(board)
        assert line == [(0, 0), (1, 1), (2, 2)]

    def test_returns_none_when_no_winner(self):
        assert get_winning_line(empty_board()) is None


# ---------- AI behaviour tests ----------

class TestTicTacToeAI:
    def setup_method(self):
        self.ai = TicTacToeAI()

    def test_ai_returns_valid_move(self):
        board = [
            ["X", None, None],
            [None, "O", None],
            [None, None, None],
        ]
        move = self.ai.get_move(board)
        assert move is not None
        r, c = move
        assert board[r][c] is None

    def test_ai_returns_none_on_full_board(self):
        board = [
            ["X", "O", "X"],
            ["X", "X", "O"],
            ["O", "X", "O"],
        ]
        assert self.ai.get_move(board) is None

    def test_ai_takes_winning_move(self):
        # O has two in a row, can win at (0,2)
        board = [
            ["O", "O", None],
            ["X", "X", None],
            [None, None, None],
        ]
        move = self.ai.get_move(board)
        assert move == (0, 2)

    def test_ai_blocks_opponent_winning_move(self):
        # X has two in a row at (0,0) and (0,1); AI must block (0,2)
        board = [
            ["X", "X", None],
            [None, "O", None],
            [None, None, None],
        ]
        move = self.ai.get_move(board)
        assert move == (0, 2)

    def test_ai_never_loses_against_random(self):
        """Play 50 games with random X vs minimax O. AI should never lose."""
        random.seed(42)
        for _ in range(50):
            board = empty_board()
            turn = "X"
            while True:
                if turn == "X":
                    empties = [
                        (r, c)
                        for r in range(3)
                        for c in range(3)
                        if board[r][c] is None
                    ]
                    if not empties:
                        break
                    r, c = random.choice(empties)
                    board[r][c] = "X"
                else:
                    move = self.ai.get_move(board)
                    if move is None:
                        break
                    board[move[0]][move[1]] = "O"

                result = check_winner(board)
                if result is not None:
                    assert result != "X", "AI (O) lost a game!"
                    break
                turn = "O" if turn == "X" else "X"
