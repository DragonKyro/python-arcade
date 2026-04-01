"""Tests for 15 Puzzle game logic.

We test _check_win, _try_move, and _shuffle without the OpenGL context by
building a minimal stand-in with the needed attributes and bound methods.
"""

import types

from renderers.fifteen_puzzle_renderer import GRID_SIZE, PLAYING, WON


def _make_game(board=None, empty_row=None, empty_col=None):
    """Return a lightweight object with 15-puzzle state + bound logic methods."""

    class _Stub:
        pass

    g = _Stub()

    if board is not None:
        g.board = [row[:] for row in board]
    else:
        # Solved board
        g.board = [
            [(r * GRID_SIZE + c + 1) % (GRID_SIZE * GRID_SIZE)
             for c in range(GRID_SIZE)]
            for r in range(GRID_SIZE)
        ]

    if empty_row is not None and empty_col is not None:
        g.empty_row = empty_row
        g.empty_col = empty_col
    else:
        # Find empty
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if g.board[r][c] == 0:
                    g.empty_row = r
                    g.empty_col = c

    g.move_count = 0
    g.timer_started = False
    g.game_state = PLAYING

    from games.fifteen_puzzle import FifteenPuzzleView
    for name in ("_check_win", "_try_move", "_shuffle"):
        method = getattr(FifteenPuzzleView, name)
        setattr(g, name, types.MethodType(method, g))

    return g


# ===================================================================
# Win detection
# ===================================================================

def test_solved_board_is_win():
    """Solved board: 1..15, then 0 in bottom-right."""
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    g._check_win()
    assert g.game_state == WON


def test_unsolved_board_is_not_win():
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 15, 14, 0],
    ]
    g = _make_game(board, 3, 3)
    g._check_win()
    assert g.game_state == PLAYING


def test_empty_not_in_corner_is_not_win():
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 0,  12],
        [13, 14, 11, 15],
    ]
    g = _make_game(board, 2, 2)
    g._check_win()
    assert g.game_state == PLAYING


# ===================================================================
# Valid slide (adjacent to empty)
# ===================================================================

def test_valid_slide_from_above():
    """Tile directly above the empty space can slide down."""
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    g.game_state = PLAYING
    # Slide tile at (2,3)=12 into empty (3,3)
    result = g._try_move(2, 3)
    assert result is True
    assert g.board[3][3] == 12
    assert g.board[2][3] == 0
    assert g.empty_row == 2
    assert g.empty_col == 3
    assert g.move_count == 1


def test_valid_slide_from_left():
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    result = g._try_move(3, 2)  # tile 15
    assert result is True
    assert g.board[3][3] == 15
    assert g.board[3][2] == 0


# ===================================================================
# Invalid slide (not adjacent)
# ===================================================================

def test_invalid_slide_diagonal():
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    result = g._try_move(2, 2)  # diagonal — invalid
    assert result is False
    assert g.move_count == 0


def test_invalid_slide_two_away():
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    result = g._try_move(1, 3)  # two rows away
    assert result is False


def test_invalid_slide_out_of_bounds():
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    result = g._try_move(4, 3)  # row 4 out of bounds
    assert result is False


def test_invalid_slide_same_position():
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    result = g._try_move(3, 3)  # the empty cell itself
    assert result is False


# ===================================================================
# Shuffle produces solvable (not solved) state
# ===================================================================

def test_shuffle_changes_board():
    """After shuffling, the board should not be in the solved state."""
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    g._shuffle(num_moves=200)
    solved = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    assert g.board != solved


def test_shuffle_keeps_valid_tiles():
    """After shuffling, the board should still contain tiles 0-15 exactly once."""
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 15, 0],
    ]
    g = _make_game(board, 3, 3)
    g._shuffle(num_moves=200)
    flat = sorted(val for row in g.board for val in row)
    assert flat == list(range(16))


# ===================================================================
# Move triggers win check
# ===================================================================

def test_move_triggers_win():
    """Sliding the last tile into place should set WON state."""
    # Board one move from solved: tile 15 is to the right of empty
    board = [
        [1,  2,  3,  4],
        [5,  6,  7,  8],
        [9,  10, 11, 12],
        [13, 14, 0,  15],
    ]
    g = _make_game(board, 3, 2)
    g._try_move(3, 3)  # slide 15 left into empty
    assert g.game_state == WON
