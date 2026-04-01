"""Tests for Snakes and Ladders AI module."""

import random
import pytest

from ai.snakes_and_ladders_ai import SnakesAndLaddersAI


class TestSnakesAndLaddersAI:
    def test_roll_returns_int(self):
        random.seed(42)
        ai = SnakesAndLaddersAI()
        result = ai.roll_dice()
        assert isinstance(result, int)

    def test_roll_in_range(self):
        random.seed(42)
        ai = SnakesAndLaddersAI()
        for _ in range(100):
            result = ai.roll_dice()
            assert 1 <= result <= 6

    def test_roll_distribution_covers_all_values(self):
        """Over many rolls, all values 1-6 should appear."""
        random.seed(42)
        ai = SnakesAndLaddersAI()
        results = {ai.roll_dice() for _ in range(200)}
        assert results == {1, 2, 3, 4, 5, 6}

    def test_deterministic_with_seed(self):
        random.seed(42)
        ai = SnakesAndLaddersAI()
        rolls1 = [ai.roll_dice() for _ in range(10)]
        random.seed(42)
        rolls2 = [ai.roll_dice() for _ in range(10)]
        assert rolls1 == rolls2
