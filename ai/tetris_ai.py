"""
Tetris AI controller.
Pure game logic - no arcade imports.
Evaluates all possible placements for a given piece and board state.
"""

import random
import copy

# Tetromino definitions: each piece has 4 rotation states.
# Each state is a list of (row, col) offsets from the piece origin.
TETROMINOES = {
    "I": [
        [(0, 0), (0, 1), (0, 2), (0, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 1), (1, 1), (2, 1), (3, 1)],
    ],
    "O": [
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
        [(0, 0), (0, 1), (1, 0), (1, 1)],
    ],
    "T": [
        [(0, 1), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 1)],
        [(0, 1), (1, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(0, 1), (0, 2), (1, 0), (1, 1)],
        [(0, 0), (1, 0), (1, 1), (2, 1)],
    ],
    "Z": [
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
        [(0, 1), (1, 0), (1, 1), (2, 0)],
    ],
    "J": [
        [(0, 0), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (0, 2), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 0), (2, 1)],
    ],
    "L": [
        [(0, 2), (1, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (1, 2), (2, 0)],
        [(0, 0), (0, 1), (1, 1), (2, 1)],
    ],
}

BOARD_COLS = 10
BOARD_ROWS = 20

# Difficulty settings: weights for evaluation and tick speed
DIFFICULTY_SETTINGS = {
    'easy': {
        'tick_rate': 0.8,
        'noise': 0.35,       # random noise added to evaluation scores
        'lines_weight': 1.0,
        'holes_weight': -3.0,
        'height_weight': -0.5,
        'bumpiness_weight': -0.3,
        'well_weight': 0.0,
    },
    'medium': {
        'tick_rate': 0.4,
        'noise': 0.08,
        'lines_weight': 1.5,
        'holes_weight': -4.5,
        'height_weight': -0.7,
        'bumpiness_weight': -0.4,
        'well_weight': 0.2,
    },
    'hard': {
        'tick_rate': 0.2,
        'noise': 0.0,
        'lines_weight': 2.0,
        'holes_weight': -6.0,
        'height_weight': -0.8,
        'bumpiness_weight': -0.5,
        'well_weight': 0.4,
    },
}


def _get_piece_cells(piece_type, rotation, col, row):
    """Return list of (board_col, board_row) for a piece at given position.
    row is the spawn row (top of piece), dr offsets go downward in the shape
    but we place with row - dr so higher dr = lower board row.
    """
    shape = TETROMINOES[piece_type][rotation]
    cells = []
    for dr, dc in shape:
        cells.append((col + dc, row - dr))
    return cells


def _valid_position(board, piece_type, rotation, col, row):
    """Check if piece at given position is valid."""
    for bc, br in _get_piece_cells(piece_type, rotation, col, row):
        if bc < 0 or bc >= BOARD_COLS:
            return False
        if br < 0 or br >= BOARD_ROWS:
            return False
        if board[br][bc] is not None:
            return False
    return True


def _drop_piece(board, piece_type, rotation, col):
    """Drop a piece from the top of the board and return the landing row, or None if invalid."""
    # Start from the top
    shape = TETROMINOES[piece_type][rotation]
    max_r = max(r for r, c in shape)
    start_row = BOARD_ROWS - 1 - max_r + 1

    if not _valid_position(board, piece_type, rotation, col, start_row):
        return None

    row = start_row
    while _valid_position(board, piece_type, rotation, col, row - 1):
        row -= 1
    return row


def _place_piece(board, piece_type, rotation, col, row):
    """Place piece on a copy of board and return (new_board, lines_cleared)."""
    new_board = [r[:] for r in board]
    # Use a generic color marker for AI evaluation
    color = (200, 200, 200)
    for bc, br in _get_piece_cells(piece_type, rotation, col, row):
        if 0 <= br < BOARD_ROWS and 0 <= bc < BOARD_COLS:
            new_board[br][bc] = color

    # Clear lines
    lines_cleared = 0
    new_rows = []
    for r in range(BOARD_ROWS):
        if all(new_board[r][c] is not None for c in range(BOARD_COLS)):
            lines_cleared += 1
        else:
            new_rows.append(new_board[r])
    while len(new_rows) < BOARD_ROWS:
        new_rows.append([None] * BOARD_COLS)
    return new_rows, lines_cleared


def _column_heights(board):
    """Return list of column heights (0-based, 0 = empty column)."""
    heights = []
    for c in range(BOARD_COLS):
        h = 0
        for r in range(BOARD_ROWS - 1, -1, -1):
            if board[r][c] is not None:
                h = r + 1
                break
        heights.append(h)
    return heights


def _count_holes(board):
    """Count number of empty cells that have a filled cell above them."""
    holes = 0
    for c in range(BOARD_COLS):
        found_block = False
        for r in range(BOARD_ROWS - 1, -1, -1):
            if board[r][c] is not None:
                found_block = True
            elif found_block:
                holes += 1
    return holes


def _bumpiness(heights):
    """Sum of absolute differences between adjacent column heights."""
    total = 0
    for i in range(len(heights) - 1):
        total += abs(heights[i] - heights[i + 1])
    return total


def get_all_placements(board, piece_type):
    """Return list of (col, rotation, resulting_board, lines_cleared) for all valid placements."""
    placements = []
    num_rotations = 4
    # O piece has only 1 unique rotation
    if piece_type == 'O':
        num_rotations = 1

    for rotation in range(num_rotations):
        shape = TETROMINOES[piece_type][rotation]
        min_dc = min(dc for _, dc in shape)
        max_dc = max(dc for _, dc in shape)

        for col in range(-min_dc, BOARD_COLS - max_dc):
            row = _drop_piece(board, piece_type, rotation, col)
            if row is not None:
                new_board, lines = _place_piece(board, piece_type, rotation, col, row)
                placements.append((col, rotation, new_board, lines))

    return placements


class TetrisAI:
    """AI opponent for Tetris with configurable difficulty."""

    def __init__(self, difficulty='medium'):
        if difficulty not in DIFFICULTY_SETTINGS:
            difficulty = 'medium'
        self.difficulty = difficulty
        self.settings = DIFFICULTY_SETTINGS[difficulty]

    @property
    def tick_rate(self):
        return self.settings['tick_rate']

    def _evaluate(self, board, lines_cleared):
        """Evaluate a board state. Higher is better."""
        s = self.settings
        heights = _column_heights(board)
        max_height = max(heights) if heights else 0
        avg_height = sum(heights) / len(heights) if heights else 0
        holes = _count_holes(board)
        bump = _bumpiness(heights)

        score = 0.0
        score += s['lines_weight'] * (lines_cleared ** 2)  # quadratic reward for more lines
        score += s['holes_weight'] * holes
        score += s['height_weight'] * avg_height
        score += s['bumpiness_weight'] * bump

        # Bonus for keeping a well (column significantly lower for Tetris clears)
        if s['well_weight'] > 0:
            min_h = min(heights)
            well_count = sum(1 for h in heights if h == min_h)
            if well_count == 1:
                # Exactly one column is the lowest - good for I-piece
                well_depth = sorted(heights)[1] - min_h
                score += s['well_weight'] * min(well_depth, 4)

        # Penalty for very high stacks
        if max_height > 15:
            score -= (max_height - 15) * 2.0

        # Add noise for easier difficulties
        if s['noise'] > 0:
            score += random.gauss(0, s['noise'] * 10)

        return score

    def get_placement(self, board, piece, next_piece=None):
        """Determine the best placement for the given piece.

        Parameters
        ----------
        board : list[list]
            10x20 grid, None=empty, color tuple=filled.
        piece : str
            Current piece type ('I','O','T','S','Z','J','L').
        next_piece : str or None
            Next piece type (used for lookahead on hard difficulty).

        Returns
        -------
        tuple (column, rotation) for the best placement,
        or None if no valid placement exists.
        """
        placements = get_all_placements(board, piece)
        if not placements:
            return None

        best_score = float('-inf')
        best_placement = None

        for col, rotation, new_board, lines in placements:
            score = self._evaluate(new_board, lines)

            # Hard difficulty does 1-ply lookahead with next piece
            if self.difficulty == 'hard' and next_piece is not None:
                next_placements = get_all_placements(new_board, next_piece)
                if next_placements:
                    best_next = max(
                        self._evaluate(nb, nl)
                        for _, _, nb, nl in next_placements
                    )
                    score += best_next * 0.3  # weight future state less

            if score > best_score:
                best_score = score
                best_placement = (col, rotation)

        return best_placement
