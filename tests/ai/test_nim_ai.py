"""Tests for ai.nim_ai module."""

import pytest
from ai.nim_ai import NimAI


@pytest.fixture
def ai():
    return NimAI()


class TestGetMoveValidity:
    """AI must return a valid (row_index, count) pair."""

    @pytest.mark.parametrize("rows", [
        [1, 3, 5, 7],
        [1, 1, 1],
        [0, 0, 1],
        [3],
        [4, 4],
        [0, 5, 0, 2],
    ])
    def test_move_is_valid(self, ai, rows):
        row_idx, count = ai.get_move(rows)
        assert 0 <= row_idx < len(rows), "row_index out of range"
        assert count > 0, "must remove at least 1 stone"
        assert count <= rows[row_idx], "cannot remove more stones than available"

    def test_single_stone_remaining(self, ai):
        row_idx, count = ai.get_move([0, 0, 1])
        assert row_idx == 2
        assert count == 1

    def test_single_row(self, ai):
        row_idx, count = ai.get_move([3])
        assert row_idx == 0
        assert 1 <= count <= 3


class TestOptimalPlay:
    """From a winning position the AI should leave nim-sum == 0 (with misere adjustments)."""

    def test_classic_board_1357(self, ai):
        # [1,3,5,7] has nim-sum 0, so AI is in a losing position.
        # It should still return a valid move (takes 1 from largest row).
        row_idx, count = ai.get_move([1, 3, 5, 7])
        assert count >= 1

    def test_winning_position_leaves_xor_zero(self, ai):
        # [1, 3, 5, 6] has nim-sum = 1^3^5^6 = 1, a winning position.
        rows = [1, 3, 5, 6]
        row_idx, count = ai.get_move(rows)
        new_rows = list(rows)
        new_rows[row_idx] -= count
        # With multiple rows >1, AI should leave nim-sum 0
        rows_gt_one = sum(1 for c in new_rows if c > 1)
        if rows_gt_one >= 2:
            nim_sum = 0
            for c in new_rows:
                nim_sum ^= c
            assert nim_sum == 0

    def test_misere_endgame_leaves_odd_ones(self, ai):
        # All rows 0 or 1: [1, 1, 0, 1] -> 3 ones (odd). AI takes one to leave even?
        # Actually 3 ones is odd -> AI is in losing endgame, but still returns valid move.
        rows = [1, 1, 0, 1]
        row_idx, count = ai.get_move(rows)
        assert count == 1
        assert rows[row_idx] == 1

    def test_misere_endgame_even_ones(self, ai):
        # [1, 1, 0, 0] has 2 ones (even). AI should take 1 to leave 1 one (odd).
        rows = [1, 1, 0, 0]
        row_idx, count = ai.get_move(rows)
        new_rows = list(rows)
        new_rows[row_idx] -= count
        remaining_ones = sum(1 for c in new_rows if c == 1)
        assert remaining_ones % 2 == 1

    def test_transition_move(self, ai):
        # [0, 4, 1] -> one row >1 (row 1), one row ==1. ones=1 (odd).
        # AI should reduce big row to 0 to keep ones odd.
        rows = [0, 4, 1]
        row_idx, count = ai.get_move(rows)
        new_rows = list(rows)
        new_rows[row_idx] -= count
        remaining_ones = sum(1 for c in new_rows if c == 1)
        assert remaining_ones % 2 == 1
