"""Tests for Mastermind game logic.

We test _calculate_feedback without instantiating MastermindView.
The method only reads self.secret_code, so we build a minimal stand-in.
"""

import types

from renderers.mastermind_renderer import NUM_SLOTS


def _make_game(secret_code):
    """Return a lightweight object with Mastermind feedback logic."""

    class _Stub:
        pass

    g = _Stub()
    g.secret_code = list(secret_code)

    from games.mastermind import MastermindView
    method = getattr(MastermindView, "_calculate_feedback")
    g._calculate_feedback = types.MethodType(method, g)

    return g


# ===================================================================
# All correct
# ===================================================================

def test_all_correct():
    g = _make_game([0, 1, 2, 3])
    black, white = g._calculate_feedback([0, 1, 2, 3])
    assert black == 4
    assert white == 0


# ===================================================================
# All wrong (no color match at all)
# ===================================================================

def test_all_wrong():
    g = _make_game([0, 1, 2, 3])
    black, white = g._calculate_feedback([4, 5, 4, 5])
    assert black == 0
    assert white == 0


# ===================================================================
# Mixed: some exact, some partial, some miss
# ===================================================================

def test_one_black_one_white():
    g = _make_game([0, 1, 2, 3])
    # pos 0: 0 == 0 -> black
    # pos 1: 2 != 1, but 2 is in secret (pos 2) -> white
    # pos 2: 4 not in remaining secret
    # pos 3: 5 not in remaining secret
    black, white = g._calculate_feedback([0, 2, 4, 5])
    assert black == 1
    assert white == 1


def test_two_black_two_white():
    g = _make_game([0, 1, 2, 3])
    # pos 0: 0 == 0 -> black
    # pos 1: 1 == 1 -> black
    # pos 2: 3 != 2, 3 in secret (pos 3) -> white
    # pos 3: 2 != 3, 2 in secret (pos 2) -> white
    black, white = g._calculate_feedback([0, 1, 3, 2])
    assert black == 2
    assert white == 2


def test_all_white():
    g = _make_game([0, 1, 2, 3])
    black, white = g._calculate_feedback([3, 2, 1, 0])
    assert black == 0
    assert white == 4


def test_some_miss():
    g = _make_game([0, 1, 2, 3])
    # pos 0: 5 miss
    # pos 1: 0 wrong pos, 0 in secret -> white
    # pos 2: 2 exact -> black
    # pos 3: 5 miss
    black, white = g._calculate_feedback([5, 0, 2, 5])
    assert black == 1
    assert white == 1


# ===================================================================
# Duplicate color handling
# ===================================================================

def test_duplicate_in_guess_one_in_secret():
    """Guess has two 0's, secret has one 0. Only one white peg."""
    g = _make_game([0, 1, 2, 3])
    # pos 0: 5 miss
    # pos 1: 0 wrong pos -> white (0 is at pos 0 in secret)
    # pos 2: 0 wrong pos -> but 0 already consumed, so miss
    # pos 3: 5 miss
    black, white = g._calculate_feedback([5, 0, 0, 5])
    assert black == 0
    assert white == 1


def test_duplicate_in_guess_exact_plus_extra():
    """Guess has two 0's, secret has one 0 at position 0. One black, zero white."""
    g = _make_game([0, 1, 2, 3])
    # pos 0: 0 exact -> black (consumes the 0)
    # pos 1: 0 wrong pos, but no more 0 in secret remaining
    # pos 2: 5 miss
    # pos 3: 5 miss
    black, white = g._calculate_feedback([0, 0, 5, 5])
    assert black == 1
    assert white == 0


def test_duplicate_in_secret_and_guess():
    """Both secret and guess have duplicate colors."""
    g = _make_game([0, 0, 1, 2])
    # pos 0: 0 exact -> black
    # pos 1: 0 exact -> black
    # pos 2: 5 miss
    # pos 3: 5 miss
    black, white = g._calculate_feedback([0, 0, 5, 5])
    assert black == 2
    assert white == 0


def test_duplicate_in_secret_partial_match():
    """Secret has two 0's; guess has 0 in wrong positions."""
    g = _make_game([0, 0, 1, 2])
    # pos 0: 5 miss
    # pos 1: 5 miss
    # pos 2: 0 wrong pos -> white (secret has 0 at pos 0)
    # pos 3: 0 wrong pos -> white (secret has 0 at pos 1)
    black, white = g._calculate_feedback([5, 5, 0, 0])
    assert black == 0
    assert white == 2


# ===================================================================
# Edge cases
# ===================================================================

def test_all_same_color_secret():
    g = _make_game([3, 3, 3, 3])
    black, white = g._calculate_feedback([3, 3, 3, 3])
    assert black == 4
    assert white == 0


def test_all_same_guess_one_match():
    g = _make_game([3, 0, 1, 2])
    # Guess all 3's: pos 0 exact -> black, rest miss (no more 3 in secret)
    black, white = g._calculate_feedback([3, 3, 3, 3])
    assert black == 1
    assert white == 0
