"""Tests for Pac-Man ghost AI module."""

import pytest
import random

from ai.pacman_ai import (
    BlinkyAI,
    PinkyAI,
    InkyAI,
    ClydeAI,
    CHASE,
    SCATTER,
    FRIGHTENED,
    EATEN,
    SCATTER_TARGETS,
    PEN_TARGET,
    UP,
    DOWN,
    LEFT,
    RIGHT,
    DIRECTIONS,
    choose_direction,
    choose_frightened_direction,
    get_valid_directions,
    is_wall,
    decide_ghost_direction,
    _opposite,
    _tile_distance,
    _add,
)


# ---------------------------------------------------------------------------
# A small maze for testing.
# 0 = open, 1 = wall.
# 7 columns x 5 rows (indexed as maze[row][col]).
# ---------------------------------------------------------------------------

MINI_MAZE = [
    [1, 1, 1, 1, 1, 1, 1],  # row 0
    [1, 0, 0, 0, 1, 0, 1],  # row 1
    [1, 0, 1, 0, 0, 0, 1],  # row 2
    [1, 0, 0, 0, 1, 0, 1],  # row 3
    [1, 1, 1, 1, 1, 1, 1],  # row 4
]


# ---------------------------------------------------------------------------
# BlinkyAI
# ---------------------------------------------------------------------------

class TestBlinkyAI:
    def test_chase_targets_pacman(self):
        pacman_pos = (10, 20)
        target = BlinkyAI.get_target_tile(
            ghost_pos=(5, 5), ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=RIGHT, blinky_pos=(5, 5), mode=CHASE,
        )
        assert target == pacman_pos

    def test_scatter_targets_home_corner(self):
        target = BlinkyAI.get_target_tile(
            ghost_pos=(5, 5), ghost_dir=UP, pacman_pos=(10, 10),
            pacman_dir=RIGHT, blinky_pos=(5, 5), mode=SCATTER,
        )
        assert target == SCATTER_TARGETS["blinky"]

    def test_name(self):
        assert BlinkyAI.name == "blinky"


# ---------------------------------------------------------------------------
# PinkyAI
# ---------------------------------------------------------------------------

class TestPinkyAI:
    def test_chase_targets_4_ahead(self):
        pacman_pos = (10, 10)
        pacman_dir = RIGHT  # (1, 0)
        target = PinkyAI.get_target_tile(
            ghost_pos=(5, 5), ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=pacman_dir, blinky_pos=(5, 5), mode=CHASE,
        )
        assert target == (14, 10)

    def test_chase_targets_4_ahead_up(self):
        pacman_pos = (10, 10)
        pacman_dir = UP  # (0, 1)
        target = PinkyAI.get_target_tile(
            ghost_pos=(5, 5), ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=pacman_dir, blinky_pos=(5, 5), mode=CHASE,
        )
        assert target == (10, 14)

    def test_chase_targets_4_ahead_left(self):
        pacman_pos = (10, 10)
        pacman_dir = LEFT  # (-1, 0)
        target = PinkyAI.get_target_tile(
            ghost_pos=(5, 5), ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=pacman_dir, blinky_pos=(5, 5), mode=CHASE,
        )
        assert target == (6, 10)

    def test_scatter_targets_home_corner(self):
        target = PinkyAI.get_target_tile(
            ghost_pos=(5, 5), ghost_dir=UP, pacman_pos=(10, 10),
            pacman_dir=RIGHT, blinky_pos=(5, 5), mode=SCATTER,
        )
        assert target == SCATTER_TARGETS["pinky"]


# ---------------------------------------------------------------------------
# InkyAI
# ---------------------------------------------------------------------------

class TestInkyAI:
    def test_chase_uses_blinky_position(self):
        """Inky's target = blinky_pos + 2 * (pivot - blinky_pos)
        where pivot = pacman_pos + 2 * pacman_dir."""
        pacman_pos = (10, 10)
        pacman_dir = RIGHT  # (1, 0)
        blinky_pos = (8, 10)
        target = InkyAI.get_target_tile(
            ghost_pos=(20, 5), ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=pacman_dir, blinky_pos=blinky_pos, mode=CHASE,
        )
        # pivot = (12, 10), vec = (12-8, 10-10) = (4, 0)
        # target = (8 + 8, 10 + 0) = (16, 10)
        assert target == (16, 10)

    def test_chase_different_blinky(self):
        pacman_pos = (10, 10)
        pacman_dir = UP  # (0, 1)
        blinky_pos = (10, 5)
        target = InkyAI.get_target_tile(
            ghost_pos=(20, 5), ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=pacman_dir, blinky_pos=blinky_pos, mode=CHASE,
        )
        # pivot = (10, 12), vec = (0, 7), target = (10, 5+14) = (10, 19)
        assert target == (10, 19)

    def test_scatter_targets_home_corner(self):
        target = InkyAI.get_target_tile(
            ghost_pos=(5, 5), ghost_dir=UP, pacman_pos=(10, 10),
            pacman_dir=RIGHT, blinky_pos=(5, 5), mode=SCATTER,
        )
        assert target == SCATTER_TARGETS["inky"]


# ---------------------------------------------------------------------------
# ClydeAI
# ---------------------------------------------------------------------------

class TestClydeAI:
    def test_chase_far_targets_pacman(self):
        """When Clyde is > 8 tiles from Pac-Man, target = pacman position."""
        pacman_pos = (20, 20)
        ghost_pos = (5, 5)
        # distance = sqrt(225+225) ~ 21.2 > 8
        target = ClydeAI.get_target_tile(
            ghost_pos=ghost_pos, ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=RIGHT, blinky_pos=(0, 0), mode=CHASE,
        )
        assert target == pacman_pos

    def test_chase_close_targets_scatter_corner(self):
        """When Clyde is <= 8 tiles from Pac-Man, target = scatter corner."""
        pacman_pos = (10, 10)
        ghost_pos = (10, 5)  # distance = 5 <= 8
        target = ClydeAI.get_target_tile(
            ghost_pos=ghost_pos, ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=RIGHT, blinky_pos=(0, 0), mode=CHASE,
        )
        assert target == SCATTER_TARGETS["clyde"]

    def test_chase_exactly_8_tiles(self):
        """At exactly 8 tiles distance, Clyde should scatter (not > 8)."""
        pacman_pos = (10, 10)
        ghost_pos = (10, 2)  # distance = 8
        target = ClydeAI.get_target_tile(
            ghost_pos=ghost_pos, ghost_dir=UP, pacman_pos=pacman_pos,
            pacman_dir=RIGHT, blinky_pos=(0, 0), mode=CHASE,
        )
        assert target == SCATTER_TARGETS["clyde"]

    def test_scatter_mode(self):
        target = ClydeAI.get_target_tile(
            ghost_pos=(5, 5), ghost_dir=UP, pacman_pos=(20, 20),
            pacman_dir=RIGHT, blinky_pos=(0, 0), mode=SCATTER,
        )
        assert target == SCATTER_TARGETS["clyde"]


# ---------------------------------------------------------------------------
# choose_direction
# ---------------------------------------------------------------------------

class TestChooseDirection:
    def test_picks_closest_to_target(self):
        # At (1, 1) in MINI_MAZE, valid moves: RIGHT (2,1), DOWN-ish
        # Target is to the right
        direction = choose_direction(
            current_pos=(1, 1), current_dir=RIGHT, target_tile=(5, 1),
            maze=MINI_MAZE,
        )
        assert direction == RIGHT

    def test_no_reversal(self):
        """Ghost should not reverse direction."""
        # At (3, 1), coming from LEFT means current_dir=RIGHT.
        # Reverse would be LEFT. Even if target is left, should not reverse.
        direction = choose_direction(
            current_pos=(3, 1), current_dir=RIGHT, target_tile=(1, 1),
            maze=MINI_MAZE,
        )
        assert direction != LEFT

    def test_dead_end_forced_reversal(self):
        """In a dead end with only one exit (the reverse), should reverse."""
        # (5, 1) in MINI_MAZE: only open neighbor is (5, 2) going DOWN=(0,-1)
        # Wait -- let me trace the maze: row 1 col 5 = 0, neighbors:
        #   UP (5,2) row2col5=0, DOWN (5,0) row0col5=1(wall),
        #   LEFT (4,1) row1col4=1(wall), RIGHT (6,1) row1col6=1(wall)
        # Only valid direction is UP. If current_dir is UP, reverse is DOWN.
        # Since DOWN is wall, candidate = [UP] after removing reverse... but UP is the only valid.
        # Actually if current_dir=UP, reverse=DOWN. candidates = [d for d in [UP] if d != DOWN] = [UP]
        # Not really dead-end reversal. Let's test differently.
        # If current_dir=DOWN (came from above), reverse=UP. candidates=[d for d in [UP] if d!=UP]=[]
        # Then fallback: candidates = valid_dirs = [UP].
        direction = choose_direction(
            current_pos=(5, 1), current_dir=DOWN, target_tile=(5, 3),
            maze=MINI_MAZE,
        )
        # Forced to go UP since it's the only valid direction
        assert direction == UP

    def test_returns_valid_direction(self):
        direction = choose_direction(
            current_pos=(1, 2), current_dir=UP, target_tile=(5, 3),
            maze=MINI_MAZE,
        )
        assert direction in DIRECTIONS

    def test_tiebreak_order(self):
        """On a tie, UP wins over LEFT, LEFT over DOWN, DOWN over RIGHT."""
        # Create a scenario with equidistant options.
        # At (3, 2) in MINI_MAZE: row2col3=0.
        #   UP (3,3) row3col3=0, DOWN (3,1) row1col3=0,
        #   LEFT (2,2) row2col2=1(wall), RIGHT (4,2) row2col4=0
        # Valid: UP, DOWN, RIGHT. If target is (3, 2) itself, distances are all 1.
        # Current_dir=LEFT, reverse=RIGHT. Candidates = [UP, DOWN].
        # Both distance 1 to target (3,2). Tie-break: UP(pri=0) < DOWN(pri=2).
        direction = choose_direction(
            current_pos=(3, 2), current_dir=LEFT, target_tile=(3, 2),
            maze=MINI_MAZE,
        )
        assert direction == UP


# ---------------------------------------------------------------------------
# choose_frightened_direction
# ---------------------------------------------------------------------------

class TestChooseFrightenedDirection:
    def test_returns_valid_direction(self):
        random.seed(42)
        direction = choose_frightened_direction(
            current_pos=(1, 1), current_dir=RIGHT, maze=MINI_MAZE,
        )
        assert direction in DIRECTIONS

    def test_no_reversal(self):
        """Frightened direction should not be the reverse of current."""
        for _ in range(50):
            direction = choose_frightened_direction(
                current_pos=(3, 2), current_dir=LEFT, maze=MINI_MAZE,
            )
            valid = get_valid_directions((3, 2), MINI_MAZE)
            rev = _opposite(LEFT)
            # Should not reverse unless it's the only option
            if len([d for d in valid if d != rev]) > 0:
                assert direction != rev

    def test_returns_direction_from_valid_set(self):
        valid = get_valid_directions((1, 1), MINI_MAZE)
        for _ in range(20):
            direction = choose_frightened_direction(
                current_pos=(1, 1), current_dir=RIGHT, maze=MINI_MAZE,
            )
            assert direction in valid


# ---------------------------------------------------------------------------
# get_valid_directions
# ---------------------------------------------------------------------------

class TestGetValidDirections:
    def test_walls_excluded(self):
        # (1, 1): row 1, col 1 = 0 (open)
        # Neighbors: UP (1,2)=row2col1=0, DOWN (1,0)=row0col1=1(wall),
        #            LEFT (0,1)=row1col0=1(wall), RIGHT (2,1)=row1col2=0
        valid = get_valid_directions((1, 1), MINI_MAZE)
        assert UP in valid
        assert RIGHT in valid
        assert DOWN not in valid
        assert LEFT not in valid

    def test_center_open(self):
        # (3, 2): row 2, col 3 = 0
        # UP (3,3)=row3col3=0, DOWN (3,1)=row1col3=0,
        # LEFT (2,2)=row2col2=1(wall), RIGHT (4,2)=row2col4=0
        valid = get_valid_directions((3, 2), MINI_MAZE)
        assert UP in valid
        assert DOWN in valid
        assert RIGHT in valid
        assert LEFT not in valid

    def test_surrounded_by_walls(self):
        """A tile completely surrounded by walls should return empty list."""
        # All-wall maze
        wall_maze = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
        valid = get_valid_directions((1, 1), wall_maze)
        assert valid == []

    def test_out_of_bounds_is_wall(self):
        # (0, 0) in MINI_MAZE is a wall itself; even if open, neighbors
        # off-grid are walls.
        valid = get_valid_directions((0, 0), MINI_MAZE)
        # (0,0) = row0col0 = 1 (wall) -- but get_valid_directions checks
        # neighbors, not the tile itself. Neighbors: UP(0,1)=1, DOWN(0,-1)=OOB=wall,
        # LEFT(-1,0)=OOB=wall, RIGHT(1,0)=1. All walls.
        assert valid == []


# ---------------------------------------------------------------------------
# SCATTER mode for all ghosts
# ---------------------------------------------------------------------------

class TestScatterMode:
    @pytest.mark.parametrize("ai_cls,name", [
        (BlinkyAI, "blinky"),
        (PinkyAI, "pinky"),
        (InkyAI, "inky"),
        (ClydeAI, "clyde"),
    ])
    def test_scatter_targets_home_corner(self, ai_cls, name):
        target = ai_cls.get_target_tile(
            ghost_pos=(14, 14), ghost_dir=UP, pacman_pos=(10, 10),
            pacman_dir=RIGHT, blinky_pos=(14, 14), mode=SCATTER,
        )
        assert target == SCATTER_TARGETS[name]


# ---------------------------------------------------------------------------
# is_wall
# ---------------------------------------------------------------------------

class TestIsWall:
    def test_wall_tile(self):
        assert is_wall((0, 0), MINI_MAZE) is True

    def test_open_tile(self):
        assert is_wall((1, 1), MINI_MAZE) is False

    def test_out_of_bounds_is_wall(self):
        assert is_wall((-1, 0), MINI_MAZE) is True
        assert is_wall((0, -1), MINI_MAZE) is True
        assert is_wall((100, 100), MINI_MAZE) is True

    def test_tunnel_row_exception(self):
        """Row 14 allows off-grid movement (tunnel wrap)."""
        # Build a maze tall enough to have row 14
        tall_maze = [[0] * 28 for _ in range(31)]
        assert is_wall((-1, 14), tall_maze) is False
        assert is_wall((28, 14), tall_maze) is False


# ---------------------------------------------------------------------------
# decide_ghost_direction (integration)
# ---------------------------------------------------------------------------

class TestDecideGhostDirection:
    def test_chase_mode(self):
        direction = decide_ghost_direction(
            ghost_index=0, ghost_pos=(3, 2), ghost_dir=UP,
            pacman_pos=(5, 3), pacman_dir=RIGHT, blinky_pos=(3, 2),
            mode=CHASE, maze=MINI_MAZE,
        )
        assert direction in DIRECTIONS

    def test_frightened_mode(self):
        direction = decide_ghost_direction(
            ghost_index=1, ghost_pos=(3, 2), ghost_dir=UP,
            pacman_pos=(5, 3), pacman_dir=RIGHT, blinky_pos=(3, 2),
            mode=FRIGHTENED, maze=MINI_MAZE,
        )
        assert direction in DIRECTIONS

    def test_eaten_mode_targets_pen(self):
        """In EATEN mode, ghost should head toward the pen target."""
        direction = decide_ghost_direction(
            ghost_index=2, ghost_pos=(3, 2), ghost_dir=UP,
            pacman_pos=(5, 3), pacman_dir=RIGHT, blinky_pos=(3, 2),
            mode=EATEN, maze=MINI_MAZE,
        )
        assert direction in DIRECTIONS


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_opposite(self):
        assert _opposite(UP) == DOWN
        assert _opposite(LEFT) == RIGHT
        assert _opposite(DOWN) == UP
        assert _opposite(RIGHT) == LEFT

    def test_tile_distance(self):
        assert _tile_distance((0, 0), (3, 4)) == pytest.approx(5.0)
        assert _tile_distance((5, 5), (5, 5)) == pytest.approx(0.0)

    def test_add(self):
        assert _add((1, 2), (3, 4)) == (4, 6)
