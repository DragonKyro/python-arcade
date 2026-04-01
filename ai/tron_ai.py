"""
Tron Light Cycles AI module.
Pure logic -- no arcade imports.
"""

import random
from collections import deque

DIRECTIONS = {
    'up': (0, 1),
    'down': (0, -1),
    'left': (-1, 0),
    'right': (1, 0),
}

OPPOSITE = {
    'up': 'down',
    'down': 'up',
    'left': 'right',
    'right': 'left',
}


def _move(head, direction):
    dx, dy = DIRECTIONS[direction]
    return (head[0] + dx, head[1] + dy)


def _is_safe(pos, grid, grid_w, grid_h):
    x, y = pos
    if x < 0 or x >= grid_w or y < 0 or y >= grid_h:
        return False
    return grid[y][x] == 0


def _flood_fill_count(start, grid, grid_w, grid_h, limit=None):
    """Count reachable empty cells from *start* using BFS.
    If *limit* is set, stop early once that many cells are found.
    """
    if not _is_safe(start, grid, grid_w, grid_h):
        return 0
    visited = set()
    visited.add(start)
    queue = deque([start])
    count = 0
    while queue:
        cx, cy = queue.popleft()
        count += 1
        if limit is not None and count >= limit:
            return count
        for dx, dy in DIRECTIONS.values():
            nx, ny = cx + dx, cy + dy
            if (nx, ny) not in visited and _is_safe((nx, ny), grid, grid_w, grid_h):
                visited.add((nx, ny))
                queue.append((nx, ny))
    return count


class TronAI:
    """AI controller for a Tron light-cycle."""

    def __init__(self, difficulty='medium'):
        self.difficulty = difficulty  # 'easy', 'medium', 'hard'

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_direction(self, head, direction, grid, grid_w, grid_h, other_heads):
        """Return the direction to move next.

        Parameters
        ----------
        head : (int, int)
            Current grid position of this AI's cycle.
        direction : str
            Current direction ('up', 'down', 'left', 'right').
        grid : list[list[int]]
            2-D grid where 0 = empty and any other int = a player trail.
        grid_w, grid_h : int
            Width and height of the grid.
        other_heads : list[(int, int)]
            Positions of all other living players' heads.

        Returns
        -------
        str  – one of 'up', 'down', 'left', 'right'
        """
        if self.difficulty == 'easy':
            return self._easy(head, direction, grid, grid_w, grid_h)
        elif self.difficulty == 'medium':
            return self._medium(head, direction, grid, grid_w, grid_h)
        else:
            return self._hard(head, direction, grid, grid_w, grid_h, other_heads)

    # ------------------------------------------------------------------
    # Easy – avoid immediate death, otherwise random
    # ------------------------------------------------------------------

    def _easy(self, head, direction, grid, grid_w, grid_h):
        safe = self._safe_directions(head, direction, grid, grid_w, grid_h)
        if not safe:
            return direction  # doomed
        return random.choice(safe)

    # ------------------------------------------------------------------
    # Medium – look a few steps ahead, prefer open space
    # ------------------------------------------------------------------

    def _medium(self, head, direction, grid, grid_w, grid_h):
        safe = self._safe_directions(head, direction, grid, grid_w, grid_h)
        if not safe:
            return direction

        best_dir = None
        best_score = -1
        for d in safe:
            pos = _move(head, d)
            score = _flood_fill_count(pos, grid, grid_w, grid_h, limit=150)
            if score > best_score:
                best_score = score
                best_dir = d
        return best_dir

    # ------------------------------------------------------------------
    # Hard – maximise own reachable area, try to cut off opponents
    # ------------------------------------------------------------------

    def _hard(self, head, direction, grid, grid_w, grid_h, other_heads):
        safe = self._safe_directions(head, direction, grid, grid_w, grid_h)
        if not safe:
            return direction

        best_dir = None
        best_score = -float('inf')

        for d in safe:
            pos = _move(head, d)
            my_reach = _flood_fill_count(pos, grid, grid_w, grid_h, limit=500)

            # Evaluate how much space opponents would have after we move
            opponent_reach_total = 0
            for oh in other_heads:
                opponent_reach_total += _flood_fill_count(oh, grid, grid_w, grid_h, limit=300)

            # Score: maximise own space, minimise opponent space
            score = my_reach - 0.5 * opponent_reach_total

            # Tie-break: slightly prefer continuing straight
            if d == direction:
                score += 0.1

            if score > best_score:
                best_score = score
                best_dir = d

        return best_dir

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_directions(head, direction, grid, grid_w, grid_h):
        """Return list of directions that don't lead to immediate death."""
        opposite = OPPOSITE[direction]
        safe = []
        for d in DIRECTIONS:
            if d == opposite:
                continue
            pos = _move(head, d)
            if _is_safe(pos, grid, grid_w, grid_h):
                safe.append(d)
        return safe
