"""
Pac-Man game view for Python Arcade 3.x.
Classic Pac-Man gameplay with four ghosts, dots, power pellets, and fruit.
"""

import arcade
import random
import math

from pages.rules import RulesView
from renderers import pacman_renderer
from ai import pacman_ai

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TILE_SIZE = 18
MAZE_COLS = 28
MAZE_ROWS = 31
MAZE_OFFSET_X = (WIDTH - MAZE_COLS * TILE_SIZE) // 2
MAZE_OFFSET_Y = 30  # bottom padding for lives/score
TOP_BAR_HEIGHT = 50

# Directions
UP = (0, 1)
DOWN = (0, -1)
LEFT = (-1, 0)
RIGHT = (1, 0)
STOP = (0, 0)

# Speeds (tiles per second)
PACMAN_SPEED = 8.0
GHOST_SPEED = 7.0
GHOST_FRIGHTENED_SPEED = 4.0
GHOST_EATEN_SPEED = 14.0
GHOST_TUNNEL_SPEED = 4.0

# Timing
SCATTER_CHASE_CYCLE = [
    (7.0, "scatter"),
    (20.0, "chase"),
    (7.0, "scatter"),
    (20.0, "chase"),
    (5.0, "scatter"),
    (20.0, "chase"),
    (5.0, "scatter"),
    (None, "chase"),  # indefinite chase
]
FRIGHTENED_DURATION = 6.0
GHOST_PEN_DELAYS = [0.0, 3.0, 6.0, 9.0]  # seconds before each ghost exits

# Fruit
FRUIT_POS = (13, 14)
FRUIT_SCORES = [100, 300, 500, 700, 1000, 2000, 3000, 5000]
FRUIT_DOT_THRESHOLDS = [70, 170]

# Colors for UI
BG_COLOR = (0, 0, 0)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (255, 255, 255)
OVERLAY_COLOR = (0, 0, 0, 180)

# Ghost colors
GHOST_COLORS = {
    "blinky": (255, 0, 0),
    "pinky": (255, 184, 255),
    "inky": (0, 255, 255),
    "clyde": (255, 184, 82),
}

# ---------------------------------------------------------------------------
# Classic Pac-Man maze layout (28 x 31)
# 0 = path, 1 = wall, 2 = dot, 3 = power pellet, 4 = ghost pen wall,
# 5 = ghost pen interior, 6 = ghost pen gate, 7 = empty (no dot) path,
# 8 = tunnel
# Row 0 = bottom of maze, row 30 = top
# ---------------------------------------------------------------------------
_MAZE_TEMPLATE = [
    # Row 0 (bottom)
    "1111111111111111111111111111",
    "1222222222222112222222222221",
    "1211112111112112111121111121",
    "1311112111112112111121111131",
    "1211112111112112111121111121",
    "1222222222222222222222222221",
    "1211112112111111121121111121",
    "1211112112111111121121111121",
    "1222222112222112222122222221",
    "1111112111110110111121111111",
    "0000012111110110111121000000",
    "1111112110000000001121111111",
    "1111112110111641110121111111",
    "8888882000155555100028888888",
    "1111112110155555100121111111",
    "1111112110111111110121111111",
    "1111112110000000001121111111",
    "0000012110111111101121000000",
    "1111112110111111101121111111",
    "1222222222222112222222222221",
    "1211112111112112111121111121",
    "1211112111112112111121111121",
    "1322112222222002222222112231",
    "1112112112111111121121121121",
    "1112112112111111121121121121",
    "1222222112222112222122222221",
    "1211111111112112111111111121",
    "1211111111112112111111111121",
    "1222222222222222222222222221",
    "1111111111111111111111111111",
    "1111111111111111111111111111",
]


def _parse_maze():
    """Parse the template into a 2D list, also extract dot/pellet positions."""
    maze = []
    dots = set()
    pellets = set()
    total_dots = 0
    # Template is stored bottom-to-top (row 0 = bottom)
    for row_idx, row_str in enumerate(_MAZE_TEMPLATE):
        row = []
        for col_idx, ch in enumerate(row_str):
            val = int(ch)
            if val == 2:
                dots.add((col_idx, row_idx))
                total_dots += 1
                row.append(0)  # walkable
            elif val == 3:
                pellets.add((col_idx, row_idx))
                total_dots += 1
                row.append(0)
            elif val == 8:
                row.append(0)  # tunnel path
            elif val == 6:
                row.append(0)  # pen gate is walkable for ghosts
            elif val == 5:
                row.append(0)  # pen interior walkable for ghosts
            elif val == 7:
                row.append(0)  # empty path
            elif val == 4:
                row.append(1)  # pen wall counts as wall for pathfinding
            else:
                row.append(val)
        maze.append(row)
    return maze, dots, pellets, total_dots


# Pre-parse to get wall layout for AI (static across levels)
_BASE_MAZE, _BASE_DOTS, _BASE_PELLETS, _BASE_TOTAL_DOTS = _parse_maze()

# Also keep the raw template for the renderer to distinguish wall types
RAW_MAZE = []
for row_str in _MAZE_TEMPLATE:
    RAW_MAZE.append([int(ch) for ch in row_str])


class _Button:
    """Simple rectangular button helper."""

    def __init__(self, cx, cy, w, h, label):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.label = label
        self.txt_label = arcade.Text(
            label, cx, cy, BUTTON_TEXT_COLOR,
            font_size=14, anchor_x="center", anchor_y="center",
        )

    def contains(self, x, y):
        return (abs(x - self.cx) <= self.w / 2) and (abs(y - self.cy) <= self.h / 2)

    def draw(self, hover=False):
        color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
        arcade.draw_rect_filled(arcade.XYWH(self.cx, self.cy, self.w, self.h), color)
        arcade.draw_rect_outline(arcade.XYWH(self.cx, self.cy, self.w, self.h), LINE_COLOR, 2)
        self.txt_label.draw()


class Ghost:
    """Holds state for one ghost."""

    def __init__(self, name, index, start_col, start_row):
        self.name = name
        self.index = index
        self.start_col = start_col
        self.start_row = start_row
        self.reset()

    def reset(self):
        self.col = float(self.start_col)
        self.row = float(self.start_row)
        self.direction = UP if self.index > 0 else LEFT
        self.next_direction = self.direction
        self.mode = pacman_ai.SCATTER
        self.prev_mode = None
        self.frightened_timer = 0.0
        self.in_pen = self.index > 0  # Blinky starts outside
        self.pen_timer = 0.0
        self.eaten = False
        self.exiting_pen = False
        self.move_progress = 0.0  # fractional progress between tiles

    @property
    def tile_pos(self):
        return (int(round(self.col)), int(round(self.row)))

    @property
    def pixel_x(self):
        return MAZE_OFFSET_X + self.col * TILE_SIZE + TILE_SIZE / 2

    @property
    def pixel_y(self):
        return MAZE_OFFSET_Y + self.row * TILE_SIZE + TILE_SIZE / 2

    @property
    def color(self):
        return GHOST_COLORS[self.name]


class PacmanView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0
        self.high_score = 0

        # Buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_new = _Button(WIDTH - 80, HEIGHT - 25, 110, 34, "New Game")
        self.btn_help = _Button(WIDTH - 150, HEIGHT - 25, 40, 40, "?")

        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
        self.txt_score = arcade.Text(
            "", 10, HEIGHT - 25, SCORE_COLOR,
            font_size=14, anchor_x="left", anchor_y="center", bold=True,
        )
        self.txt_high_score = arcade.Text(
            "", WIDTH // 2, HEIGHT - 25, SCORE_COLOR,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_ready = arcade.Text(
            "READY!", WIDTH // 2, HEIGHT // 2 - 20, (255, 255, 0),
            font_size=18, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over = arcade.Text(
            "GAME OVER", WIDTH // 2, HEIGHT // 2, (255, 0, 0),
            font_size=28, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_level_clear = arcade.Text(
            "LEVEL CLEAR!", WIDTH // 2, HEIGHT // 2, (255, 255, 0),
            font_size=28, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_restart_hint = arcade.Text(
            "Press SPACE or click New Game",
            WIDTH // 2, HEIGHT // 2 - 40, LINE_COLOR,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_score_popup = arcade.Text(
            "", 0, 0, (0, 255, 255),
            font_size=12, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_lives_label = arcade.Text(
            "Lives:", 10, 12, LINE_COLOR,
            font_size=11, anchor_x="left", anchor_y="center",
        )
        self.txt_level_label = arcade.Text(
            "", WIDTH - 10, 12, LINE_COLOR,
            font_size=11, anchor_x="right", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset all game state."""
        self.level = 1
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.level_clear = False
        self.paused = False
        self.ready_timer = 2.0  # "READY!" display countdown
        self._init_level()

    def _init_level(self):
        """Set up a single level (maze, dots, entities)."""
        self.maze = [row[:] for row in _BASE_MAZE]
        self.raw_maze = [row[:] for row in RAW_MAZE]
        self.dots = set(_BASE_DOTS)
        self.pellets = set(_BASE_PELLETS)
        self.total_dots = len(self.dots) + len(self.pellets)
        self.dots_eaten = 0
        self.level_clear = False
        self.ready_timer = 2.0

        # Pac-Man start position
        self.pac_col = 13.5
        self.pac_row = 7.0
        self.pac_dir = LEFT
        self.pac_next_dir = LEFT
        self.pac_moving = False
        self.pac_mouth_angle = 0.0
        self.pac_mouth_opening = True
        self.pac_move_progress = 0.0

        # Ghosts
        self.ghosts = [
            Ghost("blinky", 0, 13, 19),
            Ghost("pinky", 1, 13, 16),
            Ghost("inky", 2, 11, 16),
            Ghost("clyde", 3, 15, 16),
        ]

        # Ghost mode cycling
        self.mode_index = 0
        self.mode_timer = 0.0
        self.global_mode = pacman_ai.SCATTER
        self.frightened_timer = 0.0
        self.frightened_active = False
        self.ghost_eaten_combo = 0  # for 200/400/800/1600 scoring

        # Fruit
        self.fruit_active = False
        self.fruit_timer = 0.0
        self.fruit_shown_count = 0

        # Score popup
        self.score_popup_timer = 0.0
        self.score_popup_value = 0
        self.score_popup_x = 0.0
        self.score_popup_y = 0.0

        # Speed adjustments by level
        speed_mult = 1.0 + (self.level - 1) * 0.05
        self.pacman_speed = PACMAN_SPEED * speed_mult
        self.ghost_speed = GHOST_SPEED * speed_mult
        self.ghost_fright_speed = GHOST_FRIGHTENED_SPEED
        self.ghost_eaten_speed = GHOST_EATEN_SPEED

        # Pellet flash timer
        self.pellet_flash_timer = 0.0

    def _reset_positions(self):
        """Reset positions after a death (keep dots)."""
        self.pac_col = 13.5
        self.pac_row = 7.0
        self.pac_dir = LEFT
        self.pac_next_dir = LEFT
        self.pac_moving = False
        self.pac_move_progress = 0.0
        self.ready_timer = 2.0

        for g in self.ghosts:
            g.reset()

        self.mode_index = 0
        self.mode_timer = 0.0
        self.global_mode = pacman_ai.SCATTER
        self.frightened_active = False
        self.frightened_timer = 0.0
        self.ghost_eaten_combo = 0

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def _tile_center(self, col, row):
        """Pixel center of a tile."""
        px = MAZE_OFFSET_X + col * TILE_SIZE + TILE_SIZE / 2
        py = MAZE_OFFSET_Y + row * TILE_SIZE + TILE_SIZE / 2
        return px, py

    def _is_wall(self, col, row):
        """Check if a tile is a wall."""
        return pacman_ai.is_wall((col, row), self.maze)

    def _can_move(self, col, row, direction):
        """Check if moving from (col, row) in direction is valid."""
        nc = col + direction[0]
        nr = row + direction[1]
        # Tunnel wrap
        if nr == 13 or nr == 14:
            if nc < 0:
                nc = MAZE_COLS - 1
            elif nc >= MAZE_COLS:
                nc = 0
        return not self._is_wall(int(round(nc)), int(round(nr)))

    def _wrap_tunnel(self, col, row):
        """Wrap column for tunnel."""
        if (int(round(row)) == 13 or int(round(row)) == 14):
            if col < -1:
                col = MAZE_COLS
            elif col > MAZE_COLS:
                col = -1
        return col

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _move_pacman(self, dt):
        """Move Pac-Man continuously in current direction."""
        if self.ready_timer > 0:
            return

        tile_col = int(round(self.pac_col))
        tile_row = int(round(self.pac_row))

        # At tile center, try buffered direction first
        at_center = (abs(self.pac_col - tile_col) < 0.05 and
                     abs(self.pac_row - tile_row) < 0.05)

        if at_center:
            # Snap to center
            self.pac_col = float(tile_col)
            self.pac_row = float(tile_row)

            # Try buffered direction
            if self.pac_next_dir != self.pac_dir:
                if self._can_move(tile_col, tile_row, self.pac_next_dir):
                    self.pac_dir = self.pac_next_dir

            # Check if can continue
            if not self._can_move(tile_col, tile_row, self.pac_dir):
                self.pac_moving = False
                return

            self.pac_moving = True

        if self.pac_moving:
            speed = self.pacman_speed
            dist = speed * dt
            self.pac_col += self.pac_dir[0] * dist
            self.pac_row += self.pac_dir[1] * dist
            self.pac_col = self._wrap_tunnel(self.pac_col, self.pac_row)

            # Animate mouth
            mouth_speed = 12.0
            if self.pac_mouth_opening:
                self.pac_mouth_angle += mouth_speed * dt
                if self.pac_mouth_angle >= 1.0:
                    self.pac_mouth_angle = 1.0
                    self.pac_mouth_opening = False
            else:
                self.pac_mouth_angle -= mouth_speed * dt
                if self.pac_mouth_angle <= 0.0:
                    self.pac_mouth_angle = 0.0
                    self.pac_mouth_opening = True

    def _move_ghost(self, ghost, dt):
        """Move a single ghost."""
        if self.ready_timer > 0:
            return

        # Handle pen exit
        if ghost.in_pen and not ghost.exiting_pen:
            ghost.pen_timer += dt
            delay = GHOST_PEN_DELAYS[ghost.index]
            if ghost.pen_timer >= delay:
                ghost.exiting_pen = True
            else:
                # Bob up and down in pen
                ghost.row = ghost.start_row + 0.3 * math.sin(ghost.pen_timer * 4)
                return

        if ghost.exiting_pen:
            # Move toward pen exit (col 13, row 19)
            target_col, target_row = 13.0, 19.0
            speed = 4.0
            # First center horizontally
            if abs(ghost.col - target_col) > 0.1:
                if ghost.col < target_col:
                    ghost.col += speed * dt
                else:
                    ghost.col -= speed * dt
            # Then move up
            elif ghost.row < target_row - 0.1:
                ghost.row += speed * dt
            else:
                ghost.col = target_col
                ghost.row = target_row
                ghost.in_pen = False
                ghost.exiting_pen = False
                ghost.direction = LEFT
                return
            return

        # Determine speed
        tile_col = int(round(ghost.col))
        tile_row = int(round(ghost.row))

        if ghost.eaten:
            speed = self.ghost_eaten_speed
        elif ghost.mode == pacman_ai.FRIGHTENED:
            speed = self.ghost_fright_speed
        elif tile_row == 13 and (tile_col < 6 or tile_col > 21):
            speed = GHOST_TUNNEL_SPEED
        else:
            speed = self.ghost_speed

        # Move in current direction
        ghost.col += ghost.direction[0] * speed * dt
        ghost.row += ghost.direction[1] * speed * dt

        # Tunnel wrap
        ghost.col = self._wrap_tunnel(ghost.col, ghost.row)

        # Check if reached new tile center
        new_tile_col = int(round(ghost.col))
        new_tile_row = int(round(ghost.row))
        at_center = (abs(ghost.col - new_tile_col) < 0.15 and
                     abs(ghost.row - new_tile_row) < 0.15)

        if at_center:
            ghost.col = float(new_tile_col)
            ghost.row = float(new_tile_row)

            # If eaten and reached pen, respawn
            if ghost.eaten:
                if new_tile_col in (13, 14) and new_tile_row in (16, 17, 18, 19):
                    ghost.eaten = False
                    ghost.mode = self.global_mode
                    ghost.in_pen = True
                    ghost.exiting_pen = True
                    ghost.col = 13.0
                    ghost.row = 16.0
                    return

            # Decide next direction at intersection
            mode = ghost.mode
            if ghost.eaten:
                mode = pacman_ai.EATEN

            pac_tile = (int(round(self.pac_col)), int(round(self.pac_row)))
            blinky_tile = self.ghosts[0].tile_pos

            new_dir = pacman_ai.decide_ghost_direction(
                ghost.index,
                (new_tile_col, new_tile_row),
                ghost.direction,
                pac_tile,
                self.pac_dir,
                blinky_tile,
                mode,
                self.maze,
            )
            ghost.direction = new_dir

    # ------------------------------------------------------------------
    # Collision detection
    # ------------------------------------------------------------------

    def _check_dot_collision(self):
        """Check if Pac-Man eats a dot or pellet."""
        tile = (int(round(self.pac_col)), int(round(self.pac_row)))

        if tile in self.dots:
            self.dots.discard(tile)
            self.score += 10
            self.dots_eaten += 1
            self._check_fruit_spawn()
            self._check_level_clear()

        elif tile in self.pellets:
            self.pellets.discard(tile)
            self.score += 50
            self.dots_eaten += 1
            self._activate_frightened()
            self._check_level_clear()

    def _check_ghost_collision(self):
        """Check if Pac-Man collides with any ghost."""
        pac_col = round(self.pac_col)
        pac_row = round(self.pac_row)

        for ghost in self.ghosts:
            if ghost.in_pen or ghost.exiting_pen:
                continue
            g_col = round(ghost.col)
            g_row = round(ghost.row)

            dist = math.sqrt((self.pac_col - ghost.col) ** 2 +
                             (self.pac_row - ghost.row) ** 2)
            if dist > 0.8:
                continue

            if ghost.eaten:
                continue

            if ghost.mode == pacman_ai.FRIGHTENED:
                # Eat the ghost
                ghost.eaten = True
                ghost.mode = self.global_mode
                self.ghost_eaten_combo += 1
                points = 200 * (2 ** (self.ghost_eaten_combo - 1))
                if points > 1600:
                    points = 1600
                self.score += points
                self.score_popup_value = points
                self.score_popup_x = ghost.pixel_x
                self.score_popup_y = ghost.pixel_y
                self.score_popup_timer = 1.0
            else:
                # Pac-Man dies
                self.lives -= 1
                if self.lives <= 0:
                    self.game_over = True
                    if self.score > self.high_score:
                        self.high_score = self.score
                else:
                    self._reset_positions()
                return

    def _check_level_clear(self):
        """Check if all dots are eaten."""
        if len(self.dots) == 0 and len(self.pellets) == 0:
            self.level_clear = True

    def _check_fruit_spawn(self):
        """Spawn fruit at certain dot counts."""
        for threshold in FRUIT_DOT_THRESHOLDS:
            if self.dots_eaten == threshold and not self.fruit_active:
                if self.fruit_shown_count < len(FRUIT_DOT_THRESHOLDS):
                    self.fruit_active = True
                    self.fruit_timer = 10.0
                    self.fruit_shown_count += 1

    def _check_fruit_collision(self):
        """Check if Pac-Man eats the fruit."""
        if not self.fruit_active:
            return
        fc, fr = FRUIT_POS
        dist = math.sqrt((self.pac_col - fc) ** 2 + (self.pac_row - fr) ** 2)
        if dist < 0.8:
            fruit_idx = min(self.level - 1, len(FRUIT_SCORES) - 1)
            points = FRUIT_SCORES[fruit_idx]
            self.score += points
            self.fruit_active = False
            self.score_popup_value = points
            px, py = self._tile_center(fc, fr)
            self.score_popup_x = px
            self.score_popup_y = py
            self.score_popup_timer = 1.5

    # ------------------------------------------------------------------
    # Ghost mode management
    # ------------------------------------------------------------------

    def _update_ghost_modes(self, dt):
        """Cycle through scatter/chase modes."""
        if self.frightened_active:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0:
                self.frightened_active = False
                self.ghost_eaten_combo = 0
                # Restore modes
                for g in self.ghosts:
                    if g.mode == pacman_ai.FRIGHTENED:
                        g.mode = self.global_mode
            return

        if self.mode_index >= len(SCATTER_CHASE_CYCLE):
            return

        duration, mode_name = SCATTER_CHASE_CYCLE[self.mode_index]
        if duration is None:
            # Indefinite
            self.global_mode = pacman_ai.CHASE
            return

        self.mode_timer += dt
        if self.mode_timer >= duration:
            self.mode_timer = 0.0
            self.mode_index += 1
            if self.mode_index < len(SCATTER_CHASE_CYCLE):
                _, new_mode = SCATTER_CHASE_CYCLE[self.mode_index]
                new_mode_const = pacman_ai.CHASE if new_mode == "chase" else pacman_ai.SCATTER
                self.global_mode = new_mode_const
                # Ghosts reverse direction on mode change
                for g in self.ghosts:
                    if not g.in_pen and not g.eaten and g.mode != pacman_ai.FRIGHTENED:
                        g.mode = new_mode_const
                        g.direction = (-g.direction[0], -g.direction[1])

    def _activate_frightened(self):
        """Activate frightened mode for all ghosts."""
        self.frightened_active = True
        self.frightened_timer = FRIGHTENED_DURATION
        self.ghost_eaten_combo = 0
        for g in self.ghosts:
            if not g.in_pen and not g.eaten:
                g.prev_mode = g.mode
                g.mode = pacman_ai.FRIGHTENED
                # Reverse direction
                g.direction = (-g.direction[0], -g.direction[1])

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.game_over:
            return

        if self.level_clear:
            self.ready_timer -= delta_time
            if self.ready_timer <= -1.5:
                self.level += 1
                self._init_level()
            return

        # Ready countdown
        if self.ready_timer > 0:
            self.ready_timer -= delta_time
            return

        # Update timers
        self.pellet_flash_timer += delta_time

        if self.score_popup_timer > 0:
            self.score_popup_timer -= delta_time

        # Fruit timer
        if self.fruit_active:
            self.fruit_timer -= delta_time
            if self.fruit_timer <= 0:
                self.fruit_active = False

        # Ghost mode cycling
        self._update_ghost_modes(delta_time)

        # Move Pac-Man
        self._move_pacman(delta_time)

        # Move ghosts
        for ghost in self.ghosts:
            self._move_ghost(ghost, delta_time)

        # Collisions
        self._check_dot_collision()
        self._check_ghost_collision()
        self._check_fruit_collision()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def on_key_press(self, key, modifiers):
        if self.game_over or self.level_clear:
            if key == arcade.key.SPACE:
                self._init_game()
            return

        if key == arcade.key.UP:
            self.pac_next_dir = UP
        elif key == arcade.key.DOWN:
            self.pac_next_dir = DOWN
        elif key == arcade.key.LEFT:
            self.pac_next_dir = LEFT
        elif key == arcade.key.RIGHT:
            self.pac_next_dir = RIGHT
        elif key == arcade.key.ESCAPE:
            self.window.show_view(self.menu_view)

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
        elif self.btn_new.contains(x, y):
            self._init_game()
        elif self.btn_help.contains(x, y):
            rules_view = RulesView(
                "Pac-Man", "pacman.txt", None, self.menu_view,
                existing_game_view=self,
            )
            self.window.show_view(rules_view)

    def on_draw(self):
        self.clear()
        pacman_renderer.draw(self)
