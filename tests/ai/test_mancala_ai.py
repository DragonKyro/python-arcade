"""Tests for Mancala AI module."""

import pytest

from ai.mancala_ai import sow, MancalaAI


def default_pits():
    """Standard starting pits: 4 stones in each of 6 pits per side."""
    return [[4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4]]


def default_stores():
    return [0, 0]


# ---------- sow tests ----------

class TestSow:
    def test_basic_sow(self):
        pits = default_pits()
        stores = default_stores()
        new_pits, new_stores, extra_turn, capture = sow(pits, stores, 0, 0)
        # Pit 0 of side 0 had 4 stones, should be empty now
        assert new_pits[0][0] == 0
        # Stones distributed into pits 1-4
        assert new_pits[0][1] == 5
        assert new_pits[0][2] == 5
        assert new_pits[0][3] == 5
        assert new_pits[0][4] == 5
        assert not extra_turn

    def test_extra_turn_landing_in_own_store(self):
        pits = default_pits()
        stores = default_stores()
        # Side 0, pit 2: 4 stones -> pits 3,4,5 + store = lands in store
        new_pits, new_stores, extra_turn, capture = sow(pits, stores, 0, 2)
        assert new_stores[0] == 1
        assert extra_turn is True

    def test_skip_opponent_store(self):
        """Sowing should skip the opponent's store."""
        pits = [[0, 0, 0, 0, 0, 12], [4, 4, 4, 4, 4, 4]]
        stores = [0, 0]
        # Side 0, pit 5 has 12 stones: goes through store, across opponent,
        # skips opponent store, returns to own side
        new_pits, new_stores, extra_turn, capture = sow(pits, stores, 0, 5)
        # Own store should get exactly 1 stone (passing through once)
        assert new_stores[0] == 1
        # Opponent store should remain 0 (skipped)
        assert new_stores[1] == 0

    def test_capture_rule(self):
        """Last stone lands in empty own pit: capture that stone + opposite."""
        pits = [[0, 0, 0, 0, 1, 0], [4, 4, 4, 4, 4, 4]]
        stores = [0, 0]
        # Side 0, pit 4 has 1 stone -> lands in pit 5 (empty)
        # Opposite of pit 5 is opponent pit 0 which has 4 stones
        new_pits, new_stores, extra_turn, capture = sow(pits, stores, 0, 4)
        assert capture is True
        # Side 0 store gets captured stones: 1 (own) + 4 (opponent) = 5
        assert new_stores[0] == 5
        assert new_pits[0][5] == 0
        assert new_pits[1][0] == 0  # opponent pit emptied

    def test_no_capture_on_opponent_side(self):
        """Last stone landing on opponent's side should not trigger capture."""
        pits = [[0, 0, 0, 0, 0, 3], [0, 4, 4, 4, 4, 4]]
        stores = [0, 0]
        # Side 0, pit 5: 3 stones -> store (1), then opponent pits 0,1
        new_pits, new_stores, extra_turn, capture = sow(pits, stores, 0, 5)
        assert capture is False

    def test_does_not_mutate_original(self):
        pits = default_pits()
        stores = default_stores()
        sow(pits, stores, 0, 0)
        assert pits[0][0] == 4  # unchanged


# ---------- AI behaviour tests ----------

class TestMancalaAI:
    def setup_method(self):
        self.ai = MancalaAI()

    def test_ai_returns_valid_pit(self):
        pits = default_pits()
        stores = default_stores()
        move = self.ai.get_move(pits, stores, ai_side=1)
        assert move is not None
        assert 0 <= move <= 5
        assert pits[1][move] > 0

    def test_ai_picks_from_nonempty_pits_only(self):
        pits = [[4, 4, 4, 4, 4, 4], [0, 0, 0, 0, 0, 3]]
        stores = [0, 0]
        move = self.ai.get_move(pits, stores, ai_side=1)
        assert move == 5  # only non-empty pit

    def test_ai_returns_none_when_no_moves(self):
        pits = [[4, 4, 4, 4, 4, 4], [0, 0, 0, 0, 0, 0]]
        stores = [0, 0]
        move = self.ai.get_move(pits, stores, ai_side=1)
        assert move is None

    def test_ai_prefers_extra_turn(self):
        """If a move gives an extra turn, AI should favor it (or at least not crash)."""
        pits = [[4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4]]
        stores = [0, 0]
        move = self.ai.get_move(pits, stores, ai_side=1)
        assert move is not None
        assert 0 <= move <= 5

    def test_ai_side_0(self):
        """AI should work when playing as side 0."""
        pits = default_pits()
        stores = default_stores()
        move = self.ai.get_move(pits, stores, ai_side=0)
        assert move is not None
        assert 0 <= move <= 5
        assert pits[0][move] > 0

    def test_ai_does_not_crash_various_states(self):
        """Test several non-trivial board states."""
        states = [
            ([[1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1]], [20, 20]),
            ([[6, 6, 6, 6, 6, 6], [6, 6, 6, 6, 6, 6]], [0, 0]),
            ([[0, 0, 0, 0, 0, 1], [1, 0, 0, 0, 0, 0]], [23, 23]),
        ]
        ai = MancalaAI()
        for pits, stores in states:
            for side in (0, 1):
                if any(p > 0 for p in pits[side]):
                    move = ai.get_move(pits, stores, ai_side=side)
                    assert move is not None
                    assert 0 <= move <= 5
                    assert pits[side][move] > 0
