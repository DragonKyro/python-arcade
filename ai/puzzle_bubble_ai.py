"""
Puzzle Bubble VS AI controller.
Pure game logic - no arcade imports.
"""

import random
import math
from collections import deque


class PuzzleBubbleAI:
    """AI opponent for Puzzle Bubble VS with configurable difficulty."""

    DIFFICULTY_SETTINGS = {
        'easy': {
            'fire_delay': 2.0,
            'random_spread': 0.35,       # radians of random deviation
            'consider_chains': False,
            'miss_chance': 0.25,          # chance to pick a suboptimal shot
        },
        'medium': {
            'fire_delay': 1.2,
            'random_spread': 0.12,
            'consider_chains': False,
            'miss_chance': 0.08,
        },
        'hard': {
            'fire_delay': 0.7,
            'random_spread': 0.03,
            'consider_chains': True,
            'miss_chance': 0.0,
        },
    }

    def __init__(self, difficulty='medium'):
        if difficulty not in self.DIFFICULTY_SETTINGS:
            difficulty = 'medium'
        self.difficulty = difficulty
        self.settings = self.DIFFICULTY_SETTINGS[difficulty]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_aim_angle(self, grid, current_color, grid_cols, grid_rows, bubble_radius):
        """Return an aim angle in radians for the AI's next shot.

        Parameters
        ----------
        grid : dict
            Mapping of (col, row) -> color_name for bubbles on the AI board.
        current_color : str
            The color of the bubble the AI is about to fire.
        grid_cols : int
            Number of columns in the grid.
        grid_rows : int
            Number of rows in the grid.
        bubble_radius : float
            Radius of a single bubble.

        Returns
        -------
        float
            Aim angle in radians (pi/2 is straight up, >pi/2 is left, <pi/2 is right).
        """
        settings = self.settings

        # Collect candidate targets: empty cells adjacent to existing bubbles
        candidates = self._find_candidate_cells(grid, grid_cols, grid_rows)

        if not candidates:
            # Board is empty or no adjacencies; aim straight up
            return math.pi / 2

        # Score each candidate
        scored = []
        for (col, row) in candidates:
            score = self._score_placement(
                grid, col, row, current_color, grid_cols, grid_rows, bubble_radius
            )
            scored.append((score, col, row))

        scored.sort(key=lambda t: t[0], reverse=True)

        # Decide which target to pick based on difficulty
        if random.random() < settings['miss_chance'] and len(scored) > 1:
            # Pick a random candidate from the top half
            pick = random.choice(scored[:max(len(scored) // 2, 2)])
        else:
            pick = scored[0]

        _, target_col, target_row = pick

        # Convert grid position to an angle from the shooter
        target_x, target_y = self._grid_to_local(
            target_col, target_row, grid_cols, bubble_radius
        )

        # Shooter is at center-bottom of the board
        board_width = grid_cols * bubble_radius * 2
        shooter_x = board_width / 2
        shooter_y = 0.0

        dx = target_x - shooter_x
        dy = target_y - shooter_y

        angle = math.atan2(dy, dx)

        # Add random spread
        angle += random.uniform(-settings['random_spread'], settings['random_spread'])

        # Clamp angle to valid range (10 to 170 degrees)
        min_angle = math.radians(10)
        max_angle = math.radians(170)
        angle = max(min_angle, min(max_angle, angle))

        return angle

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _neighbors(self, col, row, grid_cols, grid_rows):
        """Return valid hex-grid neighbors of (col, row)."""
        results = []
        results.append((col - 1, row))
        results.append((col + 1, row))

        if row % 2 == 0:
            for dr in [-1, 1]:
                nr = row + dr
                results.append((col - 1, nr))
                results.append((col, nr))
        else:
            for dr in [-1, 1]:
                nr = row + dr
                results.append((col, nr))
                results.append((col + 1, nr))

        valid = []
        for c, r in results:
            if r < 0 or r >= grid_rows:
                continue
            max_cols = grid_cols - (1 if r % 2 == 1 else 0)
            if c < 0 or c >= max_cols:
                continue
            valid.append((c, r))
        return valid

    def _find_candidate_cells(self, grid, grid_cols, grid_rows):
        """Return set of empty cells that are adjacent to at least one occupied cell,
        or top-row cells if the grid is empty."""
        if not grid:
            # Return all top-row cells
            return [(c, 0) for c in range(grid_cols)]

        candidates = set()
        for (col, row) in grid:
            for nc, nr in self._neighbors(col, row, grid_cols, grid_rows):
                if (nc, nr) not in grid:
                    candidates.add((nc, nr))
        return list(candidates)

    def _find_connected_same_color(self, grid, col, row, color, grid_cols, grid_rows):
        """BFS to find all connected bubbles of the same color starting from (col, row)."""
        visited = set()
        queue = deque()
        queue.append((col, row))
        visited.add((col, row))
        while queue:
            c, r = queue.popleft()
            for nc, nr in self._neighbors(c, r, grid_cols, grid_rows):
                if (nc, nr) not in visited and grid.get((nc, nr)) == color:
                    visited.add((nc, nr))
                    queue.append((nc, nr))
        return visited

    def _find_floating(self, grid, grid_cols, grid_rows):
        """Find all bubbles not connected to the top row."""
        connected = set()
        queue = deque()
        for (c, r) in grid:
            if r == 0:
                connected.add((c, r))
                queue.append((c, r))

        while queue:
            c, r = queue.popleft()
            for nc, nr in self._neighbors(c, r, grid_cols, grid_rows):
                if (nc, nr) not in connected and (nc, nr) in grid:
                    connected.add((nc, nr))
                    queue.append((nc, nr))

        return {pos for pos in grid if pos not in connected}

    def _score_placement(self, grid, col, row, color, grid_cols, grid_rows, bubble_radius):
        """Score a potential placement. Higher is better."""
        score = 0.0

        # Simulate placing the bubble
        test_grid = dict(grid)
        test_grid[(col, row)] = color

        # Count same-color connected group
        group = self._find_connected_same_color(
            test_grid, col, row, color, grid_cols, grid_rows
        )
        group_size = len(group)

        if group_size >= 3:
            # This creates a match -- highly desirable
            score += 100 + group_size * 20

            # Check for floaters if considering chains (hard mode)
            if self.settings['consider_chains']:
                # Remove the matched group and count floaters
                chain_grid = {k: v for k, v in test_grid.items() if k not in group}
                floaters = self._find_floating(chain_grid, grid_cols, grid_rows)
                score += len(floaters) * 30
        else:
            # No match -- prefer grouping same colors together
            same_color_neighbors = 0
            for nc, nr in self._neighbors(col, row, grid_cols, grid_rows):
                if grid.get((nc, nr)) == color:
                    same_color_neighbors += 1
            score += same_color_neighbors * 15

            # Slight preference for placing near same-color clusters
            score += group_size * 5

        # Prefer higher rows (closer to top, lower row number = safer)
        score -= row * 2

        # Small random factor to avoid perfectly predictable play
        score += random.uniform(0, 3)

        return score

    def _grid_to_local(self, col, row, grid_cols, bubble_radius):
        """Convert grid (col, row) to local coordinates relative to the board's top-left.
        Returns (x, y) where y increases upward from the shooter."""
        diameter = bubble_radius * 2
        offset = bubble_radius if row % 2 == 1 else 0
        x = bubble_radius + col * diameter + offset
        # y: row 0 is at the top of the board; shooter is at y=0
        # Approximate board height and invert
        row_height = diameter * 0.866
        # Place row 0 high and row N low
        board_height = grid_cols * diameter  # rough approximation
        y = board_height - row * row_height
        return x, y
