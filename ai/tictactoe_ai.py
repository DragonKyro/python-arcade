"""
Tic-Tac-Toe AI using minimax algorithm.
Pure game logic — no arcade imports.
"""

import copy
from typing import List, Optional, Tuple

Board = List[List[Optional[str]]]


def check_winner(board: Board) -> Optional[str]:
    """
    Check the board state and return:
      'X'   — if X has won
      'O'   — if O has won
      'draw' — if all cells filled with no winner
      None  — if the game is still in progress
    Also returns the winning line coordinates as a second value when there is a winner.
    """
    lines = []
    # Rows
    for r in range(3):
        lines.append([(r, 0), (r, 1), (r, 2)])
    # Columns
    for c in range(3):
        lines.append([(0, c), (1, c), (2, c)])
    # Diagonals
    lines.append([(0, 0), (1, 1), (2, 2)])
    lines.append([(0, 2), (1, 1), (2, 0)])

    for line in lines:
        vals = [board[r][c] for r, c in line]
        if vals[0] is not None and vals[0] == vals[1] == vals[2]:
            return vals[0]

    # Check for draw (no empty cells)
    for r in range(3):
        for c in range(3):
            if board[r][c] is None:
                return None

    return "draw"


def get_winning_line(board: Board) -> Optional[List[Tuple[int, int]]]:
    """Return the list of (row, col) cells forming the winning line, or None."""
    lines = []
    for r in range(3):
        lines.append([(r, 0), (r, 1), (r, 2)])
    for c in range(3):
        lines.append([(0, c), (1, c), (2, c)])
    lines.append([(0, 0), (1, 1), (2, 2)])
    lines.append([(0, 2), (1, 1), (2, 0)])

    for line in lines:
        vals = [board[r][c] for r, c in line]
        if vals[0] is not None and vals[0] == vals[1] == vals[2]:
            return line
    return None


class TicTacToeAI:
    """Minimax-based AI that plays as 'O'."""

    def __init__(self):
        self.ai_marker = "O"
        self.human_marker = "X"

    def get_move(self, board: Board) -> Optional[Tuple[int, int]]:
        """
        Given the current board state, return the best (row, col) for 'O'.
        Returns None if no moves are available.
        """
        best_score = -float("inf")
        best_move = None

        for r in range(3):
            for c in range(3):
                if board[r][c] is None:
                    board_copy = copy.deepcopy(board)
                    board_copy[r][c] = self.ai_marker
                    score = self._minimax(board_copy, is_maximizing=False)
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)

        return best_move

    def _minimax(self, board: Board, is_maximizing: bool) -> int:
        result = check_winner(board)
        if result == self.ai_marker:
            return 1
        elif result == self.human_marker:
            return -1
        elif result == "draw":
            return 0

        if is_maximizing:
            best = -float("inf")
            for r in range(3):
                for c in range(3):
                    if board[r][c] is None:
                        board[r][c] = self.ai_marker
                        best = max(best, self._minimax(board, False))
                        board[r][c] = None
            return best
        else:
            best = float("inf")
            for r in range(3):
                for c in range(3):
                    if board[r][c] is None:
                        board[r][c] = self.human_marker
                        best = min(best, self._minimax(board, True))
                        board[r][c] = None
            return best
