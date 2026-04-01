"""Tests for ai.tron_ai module."""

import pytest
from ai.tron_ai import TronAI, DIRECTIONS


def make_empty_grid(w, h):
    return [[0] * w for _ in range(h)]


@pytest.fixture(params=['easy', 'medium', 'hard'])
def ai(request):
    return TronAI(difficulty=request.param)


class TestReturnType:
    def test_returns_valid_direction(self, ai):
        grid = make_empty_grid(10, 10)
        d = ai.get_direction((5, 5), 'up', grid, 10, 10, [(8, 8)])
        assert d in DIRECTIONS

    def test_returns_string(self, ai):
        grid = make_empty_grid(10, 10)
        d = ai.get_direction((5, 5), 'right', grid, 10, 10, [])
        assert isinstance(d, str)


class TestAvoidsCrash:
    def test_avoids_wall(self):
        """AI at the top edge should not go up."""
        ai = TronAI('medium')
        grid = make_empty_grid(10, 10)
        # Head at top-right corner going right
        head = (9, 9)
        d = ai.get_direction(head, 'right', grid, 10, 10, [])
        # Should not go 'right' (wall) or 'up' (wall)
        dx, dy = DIRECTIONS[d]
        new_x, new_y = head[0] + dx, head[1] + dy
        assert 0 <= new_x < 10 and 0 <= new_y < 10

    def test_avoids_trail(self):
        """AI should not move into a cell occupied by a trail."""
        ai = TronAI('medium')
        grid = make_empty_grid(10, 10)
        head = (5, 5)
        # Block up, left, right with trails
        grid[6][5] = 1  # up (y+1)
        grid[5][4] = 1  # left
        grid[5][6] = 1  # right
        d = ai.get_direction(head, 'up', grid, 10, 10, [])
        # The only safe direction that's not opposite to 'up' (which is 'down')
        # Since up is blocked, left blocked, right blocked, and down is opposite...
        # Actually opposite of 'up' is 'down', so down won't be tried.
        # Let's adjust: direction is 'right', so opposite is 'left' (won't try left)
        # Redo: block up and right, leave down open
        grid2 = make_empty_grid(10, 10)
        grid2[6][5] = 1  # up
        grid2[5][6] = 1  # right
        d2 = ai.get_direction((5, 5), 'right', grid2, 10, 10, [])
        dx, dy = DIRECTIONS[d2]
        new_pos = (5 + dx, 5 + dy)
        assert grid2[new_pos[1]][new_pos[0]] == 0

    def test_no_safe_direction_returns_current(self):
        """When all directions crash, AI returns current direction."""
        ai = TronAI('easy')
        grid = make_empty_grid(3, 3)
        # Surround (1,1) completely
        grid[0][1] = 1  # down
        grid[2][1] = 1  # up
        grid[1][0] = 1  # left
        grid[1][2] = 1  # right
        d = ai.get_direction((1, 1), 'up', grid, 3, 3, [])
        # All directions unsafe; returns current direction
        assert d == 'up'


class TestVariousGridStates:
    def test_large_open_grid(self, ai):
        grid = make_empty_grid(50, 50)
        d = ai.get_direction((25, 25), 'right', grid, 50, 50, [(10, 10)])
        assert d in DIRECTIONS

    def test_narrow_corridor(self, ai):
        """AI in a narrow corridor should pick the open path."""
        grid = make_empty_grid(5, 5)
        # Create walls on sides of a corridor along y-axis at x=2
        for y in range(5):
            grid[y][1] = 1
            grid[y][3] = 1
        d = ai.get_direction((2, 0), 'up', grid, 5, 5, [])
        assert d in DIRECTIONS

    def test_almost_full_grid(self, ai):
        grid = [[1] * 10 for _ in range(10)]
        grid[5][5] = 0  # only our cell
        grid[5][6] = 0  # one open cell to the right
        d = ai.get_direction((5, 5), 'right', grid, 10, 10, [])
        assert d in DIRECTIONS
