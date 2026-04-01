"""Tests for Peg Solitaire game logic.

We test jump validation, peg removal, game-over detection, and board validity
without instantiating PegSolitaireView.  We build a minimal stand-in that has
the board dict and bind the real methods.
"""

import types

from renderers.peg_solitaire_renderer import PLAYING, WON, LOST


def _make_game(board=None):
    """Return a lightweight object with peg solitaire state + bound logic methods."""

    class _Stub:
        pass

    g = _Stub()

    from games.peg_solitaire import VALID_POSITIONS

    if board is not None:
        g.board = dict(board)
    else:
        # Default initial board
        g.board = {}
        for pos in VALID_POSITIONS:
            g.board[pos] = True
        g.board[(3, 3)] = False

    g.selected = None
    g.valid_jumps = []
    g.move_count = 0
    g.move_history = []
    g.game_state = PLAYING

    from games.peg_solitaire import PegSolitaireView
    for name in (
        "_get_jumps_for", "_any_jumps_available", "_peg_count",
        "_check_game_over", "_do_jump", "_undo",
    ):
        method = getattr(PegSolitaireView, name)
        setattr(g, name, types.MethodType(method, g))

    return g


# ===================================================================
# Valid board positions (cross / plus shape)
# ===================================================================

def test_valid_positions_count():
    from games.peg_solitaire import VALID_POSITIONS
    # English peg solitaire has 33 positions
    assert len(VALID_POSITIONS) == 33


def test_corners_not_valid():
    from games.peg_solitaire import VALID_POSITIONS
    for pos in [(0, 0), (0, 1), (1, 0), (1, 1),
                (0, 5), (0, 6), (1, 5), (1, 6),
                (5, 0), (5, 1), (6, 0), (6, 1),
                (5, 5), (5, 6), (6, 5), (6, 6)]:
        assert pos not in VALID_POSITIONS, f"{pos} should not be valid"


def test_center_is_valid():
    from games.peg_solitaire import VALID_POSITIONS
    assert (3, 3) in VALID_POSITIONS


# ===================================================================
# Initial board setup
# ===================================================================

def test_initial_peg_count():
    g = _make_game()
    assert g._peg_count() == 32  # 33 positions - 1 empty center


def test_initial_center_empty():
    g = _make_game()
    assert g.board[(3, 3)] is False


# ===================================================================
# Valid jump detection
# ===================================================================

def test_valid_jump_into_center():
    """A peg two away from the empty center with a peg in between can jump."""
    g = _make_game()
    # Peg at (1,3) can jump over (2,3) into (3,3)
    jumps = g._get_jumps_for(1, 3)
    destinations = [(j[0], j[1]) for j in jumps]
    assert (3, 3) in destinations


def test_valid_jump_horizontal():
    g = _make_game()
    # Peg at (3,1) can jump over (3,2) into (3,3)
    jumps = g._get_jumps_for(3, 1)
    destinations = [(j[0], j[1]) for j in jumps]
    assert (3, 3) in destinations


def test_no_jump_from_empty():
    """An empty hole has no jumps."""
    g = _make_game()
    jumps = g._get_jumps_for(3, 3)  # center is empty
    assert jumps == []


def test_no_jump_when_blocked():
    """A peg with no adjacent peg to jump over, or no empty landing, has no jumps."""
    from games.peg_solitaire import VALID_POSITIONS

    # Build a board with only one peg at (3,3)
    board = {pos: False for pos in VALID_POSITIONS}
    board[(3, 3)] = True
    g = _make_game(board)
    jumps = g._get_jumps_for(3, 3)
    assert jumps == []


# ===================================================================
# Invalid jump rejection
# ===================================================================

def test_cannot_jump_to_occupied():
    """Cannot jump if the destination is already occupied."""
    g = _make_game()
    # All positions except (3,3) are occupied, so (1,3) can jump to (3,3)
    # but (5,3) would land on (3,3) too — both should appear.
    # Now fill (3,3): no jumps should land there.
    g.board[(3, 3)] = True
    jumps = g._get_jumps_for(1, 3)
    destinations = [(j[0], j[1]) for j in jumps]
    assert (3, 3) not in destinations


def test_cannot_jump_without_middle_peg():
    """Cannot jump if there is no peg in between."""
    from games.peg_solitaire import VALID_POSITIONS
    board = {pos: False for pos in VALID_POSITIONS}
    board[(1, 3)] = True
    # (2,3) is empty (no middle peg), (3,3) is empty (valid landing)
    g = _make_game(board)
    jumps = g._get_jumps_for(1, 3)
    assert jumps == []


# ===================================================================
# Peg removal after jump
# ===================================================================

def test_jump_removes_jumped_peg():
    g = _make_game()
    # Jump from (1,3) over (2,3) into (3,3)
    g._do_jump((1, 3), (3, 3), (2, 3))
    assert g.board[(1, 3)] is False   # source cleared
    assert g.board[(2, 3)] is False   # jumped peg removed
    assert g.board[(3, 3)] is True    # destination filled
    assert g.move_count == 1


def test_jump_updates_move_history():
    g = _make_game()
    g._do_jump((1, 3), (3, 3), (2, 3))
    assert len(g.move_history) == 1
    assert g.move_history[0] == ((1, 3), (2, 3), (3, 3))


# ===================================================================
# Undo
# ===================================================================

def test_undo_restores_board():
    g = _make_game()
    g._do_jump((1, 3), (3, 3), (2, 3))
    g._undo()
    assert g.board[(1, 3)] is True
    assert g.board[(2, 3)] is True
    assert g.board[(3, 3)] is False
    assert g.move_count == 0


# ===================================================================
# Game over detection
# ===================================================================

def test_game_over_no_jumps_multiple_pegs():
    """When no jumps are available and more than 1 peg remains -> LOST."""
    from games.peg_solitaire import VALID_POSITIONS
    # Place pegs at (0,2) and (6,4) — far apart, no jumps possible
    board = {pos: False for pos in VALID_POSITIONS}
    board[(0, 2)] = True
    board[(6, 4)] = True
    g = _make_game(board)
    g._check_game_over()
    assert g.game_state == LOST


def test_game_over_one_peg_wins():
    """When only 1 peg remains and no jumps -> WON."""
    from games.peg_solitaire import VALID_POSITIONS
    board = {pos: False for pos in VALID_POSITIONS}
    board[(3, 3)] = True
    g = _make_game(board)
    g._check_game_over()
    assert g.game_state == WON


def test_not_game_over_when_jumps_exist():
    g = _make_game()  # initial board has many jumps
    g._check_game_over()
    assert g.game_state == PLAYING


def test_any_jumps_available_initial():
    g = _make_game()
    assert g._any_jumps_available() is True


def test_any_jumps_not_available_isolated_pegs():
    from games.peg_solitaire import VALID_POSITIONS
    board = {pos: False for pos in VALID_POSITIONS}
    board[(0, 3)] = True  # isolated on top arm
    g = _make_game(board)
    assert g._any_jumps_available() is False
