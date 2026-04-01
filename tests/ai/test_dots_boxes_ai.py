"""Tests for ai.dots_boxes_ai module."""

import pytest
from ai.dots_boxes_ai import DotsBoxesAI


@pytest.fixture
def ai():
    return DotsBoxesAI()


def make_empty_lines(grid_rows, grid_cols):
    """Create empty h_lines and v_lines for a grid."""
    h_lines = [[False] * grid_cols for _ in range(grid_rows + 1)]
    v_lines = [[False] * (grid_cols + 1) for _ in range(grid_rows)]
    return h_lines, v_lines


class TestMoveValidity:
    def test_returns_valid_move(self, ai):
        grid_rows, grid_cols = 3, 3
        h_lines, v_lines = make_empty_lines(grid_rows, grid_cols)
        move = ai.get_move(h_lines, v_lines, grid_rows, grid_cols)
        assert move is not None
        ori, r, c = move
        assert ori in ('h', 'v')
        if ori == 'h':
            assert 0 <= r <= grid_rows
            assert 0 <= c < grid_cols
            assert not h_lines[r][c]
        else:
            assert 0 <= r < grid_rows
            assert 0 <= c <= grid_cols
            assert not v_lines[r][c]

    def test_returns_none_when_no_moves(self, ai):
        grid_rows, grid_cols = 1, 1
        h_lines = [[True], [True]]
        v_lines = [[True, True]]
        move = ai.get_move(h_lines, v_lines, grid_rows, grid_cols)
        assert move is None

    def test_does_not_pick_drawn_line(self, ai):
        grid_rows, grid_cols = 2, 2
        h_lines, v_lines = make_empty_lines(grid_rows, grid_cols)
        # Draw some lines
        h_lines[0][0] = True
        v_lines[0][0] = True
        move = ai.get_move(h_lines, v_lines, grid_rows, grid_cols)
        ori, r, c = move
        if ori == 'h':
            assert not h_lines[r][c] or (r == 0 and c == 0 and False)
        else:
            assert not v_lines[r][c] or (r == 0 and c == 0 and False)


class TestCompletesBox:
    def test_completes_box_with_three_sides(self, ai):
        """If a box has 3 sides drawn, AI should draw the 4th."""
        grid_rows, grid_cols = 1, 1
        h_lines, v_lines = make_empty_lines(grid_rows, grid_cols)
        # Draw 3 sides of the single box (top, bottom, left)
        h_lines[0][0] = True  # top
        h_lines[1][0] = True  # bottom
        v_lines[0][0] = True  # left
        # v_lines[0][1] is the right side - should be the AI's move
        move = ai.get_move(h_lines, v_lines, grid_rows, grid_cols)
        assert move == ('v', 0, 1)

    def test_completes_one_of_multiple_boxes(self, ai):
        """AI should complete a box when possible, even with other options."""
        grid_rows, grid_cols = 2, 2
        h_lines, v_lines = make_empty_lines(grid_rows, grid_cols)
        # Set up box (0,0) with 3 sides
        h_lines[0][0] = True
        h_lines[1][0] = True
        v_lines[0][0] = True
        move = ai.get_move(h_lines, v_lines, grid_rows, grid_cols)
        ori, r, c = move
        # Check that this move completes a box
        completed = DotsBoxesAI._boxes_completed_by_move(
            h_lines, v_lines, grid_rows, grid_cols, ori, r, c
        )
        assert completed > 0


class TestAvoidsGivingBox:
    def test_avoids_creating_three_sided_box(self, ai):
        """AI should avoid moves that give the opponent a 3-sided box when possible."""
        grid_rows, grid_cols = 2, 2
        h_lines, v_lines = make_empty_lines(grid_rows, grid_cols)
        # Box (0,0) has 2 sides drawn
        h_lines[0][0] = True  # top
        v_lines[0][0] = True  # left
        # Many moves are available; AI should avoid creating a 3rd side for (0,0)
        move = ai.get_move(h_lines, v_lines, grid_rows, grid_cols)
        ori, r, c = move
        danger = DotsBoxesAI._boxes_with_three_sides_created(
            h_lines, v_lines, grid_rows, grid_cols, ori, r, c
        )
        # If safe moves exist, AI should pick one with danger == 0
        # Count total safe moves to see if one was available
        all_moves = DotsBoxesAI._get_all_available_moves(
            h_lines, v_lines, grid_rows, grid_cols
        )
        safe_exists = any(
            DotsBoxesAI._boxes_with_three_sides_created(
                h_lines, v_lines, grid_rows, grid_cols, o, rr, cc
            ) == 0
            for o, rr, cc in all_moves
        )
        if safe_exists:
            assert danger == 0
