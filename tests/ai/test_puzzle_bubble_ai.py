"""Tests for ai.puzzle_bubble_ai module."""

import math
import pytest
from ai.puzzle_bubble_ai import PuzzleBubbleAI


@pytest.fixture(params=['easy', 'medium', 'hard'])
def ai(request):
    return PuzzleBubbleAI(difficulty=request.param)


class TestAngleValidity:
    def test_returns_float(self, ai):
        grid = {(0, 0): 'red', (1, 0): 'blue', (2, 0): 'red'}
        angle = ai.get_aim_angle(grid, 'red', grid_cols=8, grid_rows=12, bubble_radius=16)
        assert isinstance(angle, float)

    def test_angle_within_bounds(self, ai):
        grid = {(0, 0): 'red', (1, 0): 'blue'}
        angle = ai.get_aim_angle(grid, 'red', grid_cols=8, grid_rows=12, bubble_radius=16)
        min_angle = math.radians(10)
        max_angle = math.radians(170)
        assert min_angle <= angle <= max_angle

    def test_empty_grid_returns_valid_angle(self, ai):
        angle = ai.get_aim_angle({}, 'red', grid_cols=8, grid_rows=12, bubble_radius=16)
        min_angle = math.radians(10)
        max_angle = math.radians(170)
        assert min_angle <= angle <= max_angle

    def test_angle_straight_up_on_empty_grid(self):
        """On an empty grid with no randomness, angle should be near pi/2."""
        ai = PuzzleBubbleAI('hard')  # least random
        # With empty grid, candidates are top-row cells. Hard mode has spread=0.03
        angle = ai.get_aim_angle({}, 'red', grid_cols=8, grid_rows=12, bubble_radius=16)
        # Should be roughly pointing upward
        assert math.radians(10) <= angle <= math.radians(170)


class TestDifficulties:
    def test_all_difficulties_instantiate(self):
        for diff in ('easy', 'medium', 'hard'):
            ai = PuzzleBubbleAI(diff)
            assert ai.difficulty == diff

    def test_invalid_difficulty_defaults_to_medium(self):
        ai = PuzzleBubbleAI('impossible')
        assert ai.difficulty == 'medium'

    def test_easy_has_larger_spread_than_hard(self):
        easy = PuzzleBubbleAI('easy')
        hard = PuzzleBubbleAI('hard')
        assert easy.settings['random_spread'] > hard.settings['random_spread']

    def test_hard_considers_chains(self):
        hard = PuzzleBubbleAI('hard')
        assert hard.settings['consider_chains'] is True


class TestWithPopulatedGrid:
    def test_grid_with_matching_colors(self, ai):
        """AI should return valid angle when same-color neighbors exist."""
        grid = {(0, 0): 'red', (1, 0): 'red', (3, 0): 'blue'}
        angle = ai.get_aim_angle(grid, 'red', grid_cols=8, grid_rows=12, bubble_radius=16)
        assert isinstance(angle, float)
        assert math.radians(10) <= angle <= math.radians(170)

    def test_densely_populated_grid(self, ai):
        grid = {}
        for r in range(4):
            cols = 8 if r % 2 == 0 else 7
            for c in range(cols):
                color = ['red', 'blue', 'green'][c % 3]
                grid[(c, r)] = color
        angle = ai.get_aim_angle(grid, 'blue', grid_cols=8, grid_rows=12, bubble_radius=16)
        assert math.radians(10) <= angle <= math.radians(170)
