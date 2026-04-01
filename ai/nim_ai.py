"""
Nim AI using optimal strategy (misere variant).
Pure game logic — no arcade imports.

Misere Nim: the player who takes the LAST stone loses.
"""

from typing import List, Tuple


class NimAI:
    """AI that plays optimal Nim strategy (misere variant)."""

    def get_move(self, rows: List[int]) -> Tuple[int, int]:
        """
        Given the current rows (list of ints representing stones per row),
        return (row_index, count_to_remove).

        Uses optimal Nim strategy with misere adjustment:
        - Compute the nim-sum (XOR of all rows).
        - If nim-sum != 0, find a move that makes it 0 (with misere endgame handling).
        - If nim-sum == 0 (losing position), remove 1 from the largest row.
        """
        nim_sum = 0
        for count in rows:
            nim_sum ^= count

        # Count rows with more than one stone
        rows_gt_one = sum(1 for c in rows if c > 1)

        # Misere endgame: if all rows have 0 or 1 stones, we want to leave
        # an ODD number of rows with 1 stone (so the opponent takes the last).
        if rows_gt_one == 0:
            return self._misere_endgame_move(rows)

        # If exactly one row has >1 stones, we're entering the endgame.
        # We need to reduce that row so that an odd number of 1-rows remain.
        if rows_gt_one == 1:
            return self._misere_transition_move(rows)

        # Normal play: try to make nim-sum 0
        if nim_sum != 0:
            for i, count in enumerate(rows):
                target = count ^ nim_sum
                if target < count:
                    return (i, count - target)

        # Losing position (nim_sum == 0): remove 1 from the largest row
        largest_row = max(range(len(rows)), key=lambda i: rows[i])
        return (largest_row, 1)

    def _misere_endgame_move(self, rows: List[int]) -> Tuple[int, int]:
        """All rows have 0 or 1 stones. Leave an odd number of 1-rows."""
        ones = sum(1 for c in rows if c == 1)
        if ones % 2 == 0:
            # Even number of 1-rows: take one to make it odd
            for i, count in enumerate(rows):
                if count == 1:
                    return (i, 1)
        # Odd number of 1-rows: we're in a losing spot, just take from any
        for i, count in enumerate(rows):
            if count == 1:
                return (i, 1)
        # Should not reach here if the game is still ongoing
        return (0, 1)

    def _misere_transition_move(self, rows: List[int]) -> Tuple[int, int]:
        """Exactly one row has >1 stones. Reduce it for optimal misere play."""
        ones = sum(1 for c in rows if c == 1)
        big_row = next(i for i, c in enumerate(rows) if c > 1)
        big_count = rows[big_row]

        # After removing from the big row, we want an odd number of 1-rows total.
        # Currently there are `ones` rows with 1 stone.
        # If we leave the big row at 1, total ones = ones + 1
        # If we leave the big row at 0, total ones = ones
        if ones % 2 == 0:
            # Leave big row at 1 -> ones+1 is odd. Good.
            return (big_row, big_count - 1)
        else:
            # Leave big row at 0 -> ones is odd. Good.
            return (big_row, big_count)
