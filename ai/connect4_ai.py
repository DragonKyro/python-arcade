"""
Connect Four AI using Minimax with Alpha-Beta Pruning.
Pure game logic - no arcade imports.
"""

import math
import random

ROWS = 6
COLS = 7
EMPTY = 0
PLAYER_PIECE = 1
AI_PIECE = 2
WINDOW_LENGTH = 4
DEPTH_LIMIT = 5


def get_valid_columns(board):
    """Return list of columns that are not full (top row has an empty slot)."""
    valid = []
    for col in range(COLS):
        if board[0][col] == EMPTY:
            valid.append(col)
    return valid


def get_next_open_row(board, col):
    """Return the lowest empty row in the given column, or -1 if full."""
    for row in range(ROWS - 1, -1, -1):
        if board[row][col] == EMPTY:
            return row
    return -1


def drop_piece(board, row, col, piece):
    """Return a new board with the piece placed at (row, col)."""
    new_board = [r[:] for r in board]
    new_board[row][col] = piece
    return new_board


def check_winner(board):
    """
    Check the board state.
    Returns:
        1  - player wins
        2  - AI wins
        'draw' - board is full with no winner
        None - game still in progress
    """
    # Check horizontal
    for row in range(ROWS):
        for col in range(COLS - 3):
            window = [board[row][col + i] for i in range(4)]
            if window == [PLAYER_PIECE] * 4:
                return PLAYER_PIECE
            if window == [AI_PIECE] * 4:
                return AI_PIECE

    # Check vertical
    for row in range(ROWS - 3):
        for col in range(COLS):
            window = [board[row + i][col] for i in range(4)]
            if window == [PLAYER_PIECE] * 4:
                return PLAYER_PIECE
            if window == [AI_PIECE] * 4:
                return AI_PIECE

    # Check positive diagonal
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            window = [board[row + i][col + i] for i in range(4)]
            if window == [PLAYER_PIECE] * 4:
                return PLAYER_PIECE
            if window == [AI_PIECE] * 4:
                return AI_PIECE

    # Check negative diagonal
    for row in range(3, ROWS):
        for col in range(COLS - 3):
            window = [board[row - i][col + i] for i in range(4)]
            if window == [PLAYER_PIECE] * 4:
                return PLAYER_PIECE
            if window == [AI_PIECE] * 4:
                return AI_PIECE

    # Check for draw (no empty spaces)
    if not get_valid_columns(board):
        return "draw"

    return None


def get_winning_positions(board):
    """Return list of (row, col) tuples for the four winning cells, or empty list."""
    # Horizontal
    for row in range(ROWS):
        for col in range(COLS - 3):
            window = [board[row][col + i] for i in range(4)]
            if window == [PLAYER_PIECE] * 4 or window == [AI_PIECE] * 4:
                return [(row, col + i) for i in range(4)]

    # Vertical
    for row in range(ROWS - 3):
        for col in range(COLS):
            window = [board[row + i][col] for i in range(4)]
            if window == [PLAYER_PIECE] * 4 or window == [AI_PIECE] * 4:
                return [(row + i, col) for i in range(4)]

    # Positive diagonal
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            window = [board[row + i][col + i] for i in range(4)]
            if window == [PLAYER_PIECE] * 4 or window == [AI_PIECE] * 4:
                return [(row + i, col + i) for i in range(4)]

    # Negative diagonal
    for row in range(3, ROWS):
        for col in range(COLS - 3):
            window = [board[row - i][col + i] for i in range(4)]
            if window == [PLAYER_PIECE] * 4 or window == [AI_PIECE] * 4:
                return [(row - i, col + i) for i in range(4)]

    return []


def _evaluate_window(window, piece):
    """Score a window of 4 cells for the given piece."""
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE
    score = 0

    piece_count = window.count(piece)
    empty_count = window.count(EMPTY)
    opp_count = window.count(opp_piece)

    if piece_count == 4:
        score += 100
    elif piece_count == 3 and empty_count == 1:
        score += 5
    elif piece_count == 2 and empty_count == 2:
        score += 2

    if opp_count == 3 and empty_count == 1:
        score -= 4

    return score


def _score_position(board, piece):
    """Evaluate the entire board for the given piece."""
    score = 0

    # Center column preference
    center_col = COLS // 2
    center_array = [board[row][center_col] for row in range(ROWS)]
    center_count = center_array.count(piece)
    score += center_count * 3

    # Horizontal windows
    for row in range(ROWS):
        for col in range(COLS - 3):
            window = [board[row][col + i] for i in range(4)]
            score += _evaluate_window(window, piece)

    # Vertical windows
    for row in range(ROWS - 3):
        for col in range(COLS):
            window = [board[row + i][col] for i in range(4)]
            score += _evaluate_window(window, piece)

    # Positive diagonal windows
    for row in range(ROWS - 3):
        for col in range(COLS - 3):
            window = [board[row + i][col + i] for i in range(4)]
            score += _evaluate_window(window, piece)

    # Negative diagonal windows
    for row in range(3, ROWS):
        for col in range(COLS - 3):
            window = [board[row - i][col + i] for i in range(4)]
            score += _evaluate_window(window, piece)

    return score


def _is_terminal_node(board):
    """Check if the board is in a terminal state."""
    return check_winner(board) is not None


def _minimax(board, depth, alpha, beta, maximizing_player, ai_piece, player_piece):
    """Minimax with alpha-beta pruning."""
    valid_columns = get_valid_columns(board)
    terminal = _is_terminal_node(board)

    if depth == 0 or terminal:
        if terminal:
            winner = check_winner(board)
            if winner == ai_piece:
                return None, 100000000
            elif winner == player_piece:
                return None, -100000000
            else:
                # Draw
                return None, 0
        else:
            return None, _score_position(board, ai_piece)

    if maximizing_player:
        value = -math.inf
        best_col = random.choice(valid_columns)
        for col in valid_columns:
            row = get_next_open_row(board, col)
            new_board = drop_piece(board, row, col, ai_piece)
            _, new_score = _minimax(
                new_board, depth - 1, alpha, beta, False, ai_piece, player_piece
            )
            if new_score > value:
                value = new_score
                best_col = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return best_col, value
    else:
        value = math.inf
        best_col = random.choice(valid_columns)
        for col in valid_columns:
            row = get_next_open_row(board, col)
            new_board = drop_piece(board, row, col, player_piece)
            _, new_score = _minimax(
                new_board, depth - 1, alpha, beta, True, ai_piece, player_piece
            )
            if new_score < value:
                value = new_score
                best_col = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return best_col, value


class Connect4AI:
    """Connect Four AI player using minimax with alpha-beta pruning."""

    def get_move(self, board, ai_piece, player_piece):
        """
        Determine the best column for the AI to play.

        Args:
            board: 6x7 list of lists. Values: 0=empty, 1=player, 2=AI.
            ai_piece: The piece value for the AI (typically 2).
            player_piece: The piece value for the player (typically 1).

        Returns:
            int: Column index (0-6) for the best move.
        """
        col, _ = _minimax(
            board, DEPTH_LIMIT, -math.inf, math.inf, True, ai_piece, player_piece
        )
        return col
