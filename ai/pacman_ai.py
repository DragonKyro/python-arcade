"""
Pac-Man ghost AI module.
Pure Python logic -- no arcade imports.

Four distinct ghost personalities:
  Blinky (red)   - direct chase
  Pinky (pink)   - ambush 4 tiles ahead
  Inky (cyan)    - flanking via Blinky reflection
  Clyde (orange) - shy, scatters when close
"""

import random
import math

# ---------------------------------------------------------------------------
# Directions as (dx, dy) offsets in tile coords
# ---------------------------------------------------------------------------
UP = (0, 1)
DOWN = (0, -1)
LEFT = (-1, 0)
RIGHT = (1, 0)
DIRECTIONS = [UP, DOWN, LEFT, RIGHT]

# ---------------------------------------------------------------------------
# Ghost modes
# ---------------------------------------------------------------------------
CHASE = "chase"
SCATTER = "scatter"
FRIGHTENED = "frightened"
EATEN = "eaten"

# Scatter corners (tile coords) for each ghost
SCATTER_TARGETS = {
    "blinky": (25, 30),  # top-right
    "pinky":  (2, 30),   # top-left
    "inky":   (27, 0),   # bottom-right
    "clyde":  (0, 0),    # bottom-left
}

# Ghost pen target (center top of pen)
PEN_TARGET = (13, 17)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _opposite(direction):
    """Return the opposite direction."""
    return (-direction[0], -direction[1])


def _tile_distance(a, b):
    """Euclidean distance between two tile positions."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _direction_offset(direction, steps):
    """Return the tile that is *steps* tiles in *direction* from origin (0,0)."""
    return (direction[0] * steps, direction[1] * steps)


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def is_wall(pos, maze):
    """Check if a tile position is a wall (1) in the maze grid.
    Tiles outside maze bounds count as walls (except tunnel row)."""
    col, row = int(pos[0]), int(pos[1])
    rows = len(maze)
    cols = len(maze[0]) if rows > 0 else 0
    # Tunnel wrap: row 14 allows off-grid movement
    if row == 14 and (col < 0 or col >= cols):
        return False
    if row < 0 or row >= rows or col < 0 or col >= cols:
        return True
    return maze[row][col] == 1


def get_valid_directions(pos, maze):
    """Return list of directions that lead to a walkable tile from *pos*."""
    valid = []
    for d in DIRECTIONS:
        next_pos = _add(pos, d)
        if not is_wall(next_pos, maze):
            valid.append(d)
    return valid


# ---------------------------------------------------------------------------
# Direction chooser (shared by all ghosts in chase / scatter mode)
# ---------------------------------------------------------------------------

def choose_direction(current_pos, current_dir, target_tile, maze, valid_dirs=None):
    """Pick the direction from *current_pos* that minimises distance to
    *target_tile*.  Ghosts cannot reverse (except on mode change, handled
    externally).  Tie-break order: UP, LEFT, DOWN, RIGHT (matches original).

    *valid_dirs* may be pre-computed; if None we compute them here.
    """
    if valid_dirs is None:
        valid_dirs = get_valid_directions(current_pos, maze)

    # Remove the reverse of current direction (no reversals)
    rev = _opposite(current_dir)
    candidates = [d for d in valid_dirs if d != rev]

    if not candidates:
        # Dead-end: forced to reverse
        candidates = valid_dirs if valid_dirs else [current_dir]

    # Tie-break priority: UP, LEFT, DOWN, RIGHT
    priority = {UP: 0, LEFT: 1, DOWN: 2, RIGHT: 3}

    best_dir = None
    best_dist = float("inf")
    best_pri = 99
    for d in candidates:
        next_tile = _add(current_pos, d)
        dist = _tile_distance(next_tile, target_tile)
        pri = priority.get(d, 99)
        if dist < best_dist or (dist == best_dist and pri < best_pri):
            best_dist = dist
            best_dir = d
            best_pri = pri

    return best_dir if best_dir else current_dir


def choose_frightened_direction(current_pos, current_dir, maze, valid_dirs=None):
    """In frightened mode, pick a random valid direction (no reversal)."""
    if valid_dirs is None:
        valid_dirs = get_valid_directions(current_pos, maze)
    rev = _opposite(current_dir)
    candidates = [d for d in valid_dirs if d != rev]
    if not candidates:
        candidates = valid_dirs if valid_dirs else [current_dir]
    return random.choice(candidates)


# ---------------------------------------------------------------------------
# Per-ghost target tile strategies
# ---------------------------------------------------------------------------

class BlinkyAI:
    """Red ghost - targets Pac-Man directly."""
    name = "blinky"

    @staticmethod
    def get_target_tile(ghost_pos, ghost_dir, pacman_pos, pacman_dir,
                        blinky_pos, mode):
        if mode == SCATTER:
            return SCATTER_TARGETS["blinky"]
        # Chase: target is Pac-Man's current tile
        return pacman_pos


class PinkyAI:
    """Pink ghost - targets 4 tiles ahead of Pac-Man."""
    name = "pinky"

    @staticmethod
    def get_target_tile(ghost_pos, ghost_dir, pacman_pos, pacman_dir,
                        blinky_pos, mode):
        if mode == SCATTER:
            return SCATTER_TARGETS["pinky"]
        # Chase: 4 tiles ahead of Pac-Man's direction
        offset = _direction_offset(pacman_dir, 4)
        return _add(pacman_pos, offset)


class InkyAI:
    """Cyan ghost - uses vector from Blinky to 2 tiles ahead of Pac-Man,
    then doubles it.  Creates unpredictable flanking behaviour."""
    name = "inky"

    @staticmethod
    def get_target_tile(ghost_pos, ghost_dir, pacman_pos, pacman_dir,
                        blinky_pos, mode):
        if mode == SCATTER:
            return SCATTER_TARGETS["inky"]
        # 2 tiles ahead of Pac-Man
        offset = _direction_offset(pacman_dir, 2)
        pivot = _add(pacman_pos, offset)
        # Vector from Blinky to pivot, doubled
        vec = _sub(pivot, blinky_pos)
        target = _add(blinky_pos, (vec[0] * 2, vec[1] * 2))
        return target


class ClydeAI:
    """Orange ghost - targets Pac-Man when far (>8 tiles), scatters when close."""
    name = "clyde"

    @staticmethod
    def get_target_tile(ghost_pos, ghost_dir, pacman_pos, pacman_dir,
                        blinky_pos, mode):
        if mode == SCATTER:
            return SCATTER_TARGETS["clyde"]
        dist = _tile_distance(ghost_pos, pacman_pos)
        if dist > 8:
            return pacman_pos
        return SCATTER_TARGETS["clyde"]


# Convenience list in order
GHOST_AIS = [BlinkyAI, PinkyAI, InkyAI, ClydeAI]
GHOST_NAMES = ["blinky", "pinky", "inky", "clyde"]


# ---------------------------------------------------------------------------
# High-level helper: decide a ghost's next direction at an intersection
# ---------------------------------------------------------------------------

def decide_ghost_direction(ghost_index, ghost_pos, ghost_dir, pacman_pos,
                           pacman_dir, blinky_pos, mode, maze):
    """Return the direction a ghost should move given the current game state.

    Parameters
    ----------
    ghost_index : int  (0=blinky, 1=pinky, 2=inky, 3=clyde)
    ghost_pos   : (col, row) current tile
    ghost_dir   : (dx, dy) current direction
    pacman_pos  : (col, row) Pac-Man's tile
    pacman_dir  : (dx, dy) Pac-Man's direction
    blinky_pos  : (col, row) Blinky's tile (needed by Inky)
    mode        : CHASE | SCATTER | FRIGHTENED | EATEN
    maze        : 2-D list of the maze
    """
    valid = get_valid_directions(ghost_pos, maze)

    if mode == FRIGHTENED:
        return choose_frightened_direction(ghost_pos, ghost_dir, maze, valid)

    if mode == EATEN:
        # Head straight back to pen
        return choose_direction(ghost_pos, ghost_dir, PEN_TARGET, maze, valid)

    ai = GHOST_AIS[ghost_index]
    target = ai.get_target_tile(ghost_pos, ghost_dir, pacman_pos, pacman_dir,
                                blinky_pos, mode)
    return choose_direction(ghost_pos, ghost_dir, target, maze, valid)
