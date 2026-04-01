"""
Puzzle Bubble (Bust-a-Move) game view for Python Arcade 3.x.
Shoot colored bubbles to match 3+ of the same color and clear the board.
"""

import arcade
import random
import math
from collections import deque
from pages.rules import RulesView
from renderers import puzzle_bubble_renderer

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
PLAY_AREA_LEFT = 100
PLAY_AREA_RIGHT = 700
PLAY_AREA_TOP = HEIGHT - TOP_BAR_HEIGHT - 10
PLAY_AREA_BOTTOM = 60

# Grid
BUBBLE_RADIUS = 18
BUBBLE_DIAMETER = BUBBLE_RADIUS * 2
GRID_COLS = 12
GRID_ROWS = 15
GRID_ORIGIN_X = PLAY_AREA_LEFT + BUBBLE_RADIUS
GRID_ORIGIN_Y = PLAY_AREA_TOP - BUBBLE_RADIUS

# Shooter
SHOOTER_X = WIDTH // 2
SHOOTER_Y = PLAY_AREA_BOTTOM + 20
MIN_ANGLE = math.radians(10)
MAX_ANGLE = math.radians(170)
AIM_SPEED = 2.0  # radians per second
BUBBLE_SPEED = 600.0

# Danger line
DANGER_LINE_Y = PLAY_AREA_BOTTOM + 80

# Colors
BG_COLOR = (20, 20, 35)
GRID_LINE_COLOR = (40, 40, 60, 60)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (20, 20, 35, 200)
STATUS_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (249, 226, 175)
DANGER_COLOR = (243, 139, 168, 100)

# Bubble colors
BUBBLE_COLORS = {
    "red": (243, 80, 80),
    "blue": (80, 140, 250),
    "green": (80, 220, 120),
    "yellow": (250, 220, 80),
    "purple": (180, 100, 240),
    "orange": (250, 160, 60),
}
COLOR_NAMES = list(BUBBLE_COLORS.keys())

# Scoring
POP_SCORE = 10
DROP_BONUS = 20
CHAIN_MULTIPLIER = 1.5

# Initial rows of bubbles
INITIAL_ROWS = 6


class _Button:
    """Simple rectangular button helper."""

    def __init__(self, cx, cy, w, h, label):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.label = label

    def contains(self, x, y):
        return (abs(x - self.cx) <= self.w / 2) and (abs(y - self.cy) <= self.h / 2)

    def draw(self, hover=False):
        color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
        arcade.draw_rect_filled(arcade.XYWH(self.cx, self.cy, self.w, self.h), color)
        arcade.draw_rect_outline(arcade.XYWH(self.cx, self.cy, self.w, self.h), LINE_COLOR, 2)
        if not hasattr(self, '_txt_label'):
            self._txt_label = arcade.Text(
                self.label, self.cx, self.cy, BUTTON_TEXT_COLOR,
                font_size=14, anchor_x="center", anchor_y="center",
            )
        self._txt_label.text = self.label
        self._txt_label.x = self.cx
        self._txt_label.y = self.cy
        self._txt_label.draw()


def grid_to_screen(col, row):
    """Convert grid (col, row) to screen center (x, y).
    Row 0 is the top row. Odd rows are offset by half a bubble diameter (hex packing).
    """
    offset = BUBBLE_RADIUS if row % 2 == 1 else 0
    x = GRID_ORIGIN_X + col * BUBBLE_DIAMETER + offset
    y = GRID_ORIGIN_Y - row * (BUBBLE_DIAMETER * 0.866)  # sqrt(3)/2 vertical spacing
    return x, y


def screen_to_grid(x, y):
    """Convert screen (x, y) to nearest grid (col, row)."""
    best_dist = float('inf')
    best_col, best_row = 0, 0
    for row in range(GRID_ROWS):
        max_cols = GRID_COLS - (1 if row % 2 == 1 else 0)
        for col in range(max_cols):
            gx, gy = grid_to_screen(col, row)
            dist = (x - gx) ** 2 + (y - gy) ** 2
            if dist < best_dist:
                best_dist = dist
                best_col, best_row = col, row
    return best_col, best_row


class PuzzleBubbleView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0

        # Mode selection
        self.mode = "select"
        self.btn_solo = _Button(WIDTH / 2, HEIGHT / 2 + 30, 250, 50, "Solo")
        self.btn_vs = _Button(WIDTH / 2, HEIGHT / 2 - 30, 250, 50, "VS AI")
        self.txt_mode_title = arcade.Text(
            "PUZZLE BUBBLE", WIDTH / 2, HEIGHT / 2 + 120, (249, 226, 175),
            font_size=36, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_mode_subtitle = arcade.Text(
            "Choose Mode", WIDTH / 2, HEIGHT / 2 + 75, (205, 214, 244),
            font_size=18, anchor_x="center", anchor_y="center",
        )

        # Buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_new = _Button(WIDTH - 80, HEIGHT - 25, 110, 34, "New Game")
        self.btn_help = _Button(WIDTH - 150, HEIGHT - 25, 40, 40, "?")

        # Key states
        self.key_left = False
        self.key_right = False

        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        self.txt_title = arcade.Text(
            "PUZZLE BUBBLE", 15, HEIGHT - 25, SCORE_COLOR,
            font_size=16, bold=True, anchor_x="left", anchor_y="center",
        )

        self.txt_score_label = arcade.Text(
            "SCORE", PLAY_AREA_RIGHT + 20, PLAY_AREA_TOP - 10, STATUS_TEXT_COLOR,
            font_size=12, anchor_x="left", anchor_y="top",
        )
        self.txt_score_value = arcade.Text(
            "0", PLAY_AREA_RIGHT + 20, PLAY_AREA_TOP - 30, SCORE_COLOR,
            font_size=18, bold=True, anchor_x="left", anchor_y="top",
        )

        self.txt_level_label = arcade.Text(
            "LEVEL", PLAY_AREA_RIGHT + 20, PLAY_AREA_TOP - 70, STATUS_TEXT_COLOR,
            font_size=12, anchor_x="left", anchor_y="top",
        )
        self.txt_level_value = arcade.Text(
            "1", PLAY_AREA_RIGHT + 20, PLAY_AREA_TOP - 90, SCORE_COLOR,
            font_size=18, bold=True, anchor_x="left", anchor_y="top",
        )

        self.txt_next_label = arcade.Text(
            "NEXT", PLAY_AREA_RIGHT + 20, PLAY_AREA_TOP - 140, STATUS_TEXT_COLOR,
            font_size=12, anchor_x="left", anchor_y="top",
        )

        # Controls
        controls = [
            "CONTROLS",
            "<< >>  Aim",
            "Space  Fire",
        ]
        self.txt_controls = []
        base_y = PLAY_AREA_TOP - 250
        for i, line in enumerate(controls):
            fs = 10 if i > 0 else 11
            c = STATUS_TEXT_COLOR if i > 0 else SCORE_COLOR
            t = arcade.Text(
                line, PLAY_AREA_RIGHT + 20, base_y - i * 18, c,
                font_size=fs, anchor_x="left", anchor_y="top",
            )
            self.txt_controls.append(t)

        # Game over texts
        self.txt_game_over = arcade.Text(
            "GAME OVER", WIDTH / 2, HEIGHT / 2 + 30, (243, 139, 168),
            font_size=36, bold=True, anchor_x="center", anchor_y="center",
        )
        self.txt_game_over_score = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 15, SCORE_COLOR,
            font_size=20, anchor_x="center", anchor_y="center",
        )
        self.txt_game_over_hint = arcade.Text(
            "Press ENTER or click New Game to play again",
            WIDTH / 2, HEIGHT / 2 - 50, STATUS_TEXT_COLOR,
            font_size=13, anchor_x="center", anchor_y="center",
        )

        # Level clear text
        self.txt_level_clear = arcade.Text(
            "LEVEL CLEAR!", WIDTH / 2, HEIGHT / 2 + 20, (166, 227, 161),
            font_size=32, bold=True, anchor_x="center", anchor_y="center",
        )
        self.txt_level_clear_hint = arcade.Text(
            "Press ENTER or Space for next level",
            WIDTH / 2, HEIGHT / 2 - 20, STATUS_TEXT_COLOR,
            font_size=13, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------
    # Game state
    # ------------------------------------------------------------------
    def _init_game(self):
        """Initialize / reset all game state."""
        self.score = 0
        self.level = 1
        self.game_over = False
        self.level_clear = False

        # Grid: dict mapping (col, row) -> color_name
        self.grid = {}
        self._populate_grid(INITIAL_ROWS)

        # Shooter
        self.aim_angle = math.radians(90)  # straight up
        self.current_bubble = self._random_color()
        self.next_bubble = self._random_color()

        # Flying bubble state
        self.flying = False
        self.fly_x = 0.0
        self.fly_y = 0.0
        self.fly_dx = 0.0
        self.fly_dy = 0.0
        self.fly_color = None

    def _populate_grid(self, num_rows):
        """Fill the top rows with random bubbles."""
        self.grid = {}
        for row in range(num_rows):
            max_cols = GRID_COLS - (1 if row % 2 == 1 else 0)
            for col in range(max_cols):
                self.grid[(col, row)] = random.choice(COLOR_NAMES)

    def _random_color(self):
        """Pick a random color that exists in the grid (or any if grid is empty)."""
        grid_colors = set(self.grid.values())
        if grid_colors:
            return random.choice(list(grid_colors))
        return random.choice(COLOR_NAMES)

    def _active_colors(self):
        """Return set of colors currently in the grid."""
        return set(self.grid.values())

    # ------------------------------------------------------------------
    # Shooting
    # ------------------------------------------------------------------
    def _fire(self):
        """Fire the current bubble in the aimed direction."""
        if self.flying or self.game_over or self.level_clear:
            return
        self.flying = True
        self.fly_x = float(SHOOTER_X)
        self.fly_y = float(SHOOTER_Y)
        self.fly_dx = math.cos(self.aim_angle) * BUBBLE_SPEED
        self.fly_dy = math.sin(self.aim_angle) * BUBBLE_SPEED
        self.fly_color = self.current_bubble
        self.current_bubble = self.next_bubble
        self.next_bubble = self._random_color()

    # ------------------------------------------------------------------
    # Match and float detection
    # ------------------------------------------------------------------
    def _neighbors(self, col, row):
        """Return list of valid neighbor positions in hex grid."""
        results = []
        # Same row neighbors
        results.append((col - 1, row))
        results.append((col + 1, row))

        # Rows above and below depend on even/odd row
        if row % 2 == 0:
            # Even row: neighbors in adjacent rows are at (col-1) and (col)
            for dr in [-1, 1]:
                nr = row + dr
                results.append((col - 1, nr))
                results.append((col, nr))
        else:
            # Odd row: neighbors in adjacent rows are at (col) and (col+1)
            for dr in [-1, 1]:
                nr = row + dr
                results.append((col, nr))
                results.append((col + 1, nr))

        # Filter to valid positions
        valid = []
        for c, r in results:
            if r < 0 or r >= GRID_ROWS:
                continue
            max_cols = GRID_COLS - (1 if r % 2 == 1 else 0)
            if c < 0 or c >= max_cols:
                continue
            valid.append((c, r))
        return valid

    def _find_connected_same_color(self, col, row, color):
        """BFS to find all connected bubbles of the same color."""
        visited = set()
        queue = deque()
        queue.append((col, row))
        visited.add((col, row))
        while queue:
            c, r = queue.popleft()
            for nc, nr in self._neighbors(c, r):
                if (nc, nr) not in visited and self.grid.get((nc, nr)) == color:
                    visited.add((nc, nr))
                    queue.append((nc, nr))
        return visited

    def _find_floating(self):
        """Find all bubbles not connected to the top row (row 0)."""
        # BFS from all top-row bubbles
        connected = set()
        queue = deque()
        for (c, r), _ in list(self.grid.items()):
            if r == 0:
                connected.add((c, r))
                queue.append((c, r))

        while queue:
            c, r = queue.popleft()
            for nc, nr in self._neighbors(c, r):
                if (nc, nr) not in connected and (nc, nr) in self.grid:
                    connected.add((nc, nr))
                    queue.append((nc, nr))

        # Everything not connected is floating
        floating = set()
        for pos in self.grid:
            if pos not in connected:
                floating.add(pos)
        return floating

    def _snap_and_process(self):
        """Snap flying bubble to grid and check for matches."""
        # Find nearest empty grid cell that is adjacent to an existing bubble OR in row 0
        best_dist = float('inf')
        best_pos = None

        for row in range(GRID_ROWS):
            max_cols = GRID_COLS - (1 if row % 2 == 1 else 0)
            for col in range(max_cols):
                if (col, row) in self.grid:
                    continue
                # Valid if row 0 (top) or adjacent to an existing bubble
                if row == 0 or any((nc, nr) in self.grid for nc, nr in self._neighbors(col, row)):
                    gx, gy = grid_to_screen(col, row)
                    d = (self.fly_x - gx) ** 2 + (self.fly_y - gy) ** 2
                    if d < best_dist:
                        best_dist = d
                        best_pos = (col, row)

        if best_pos is None:
            # Fallback: snap to nearest grid position
            best_pos = screen_to_grid(self.fly_x, self.fly_y)

        col, row = best_pos

        # Place the bubble
        self.grid[(col, row)] = self.fly_color
        self.flying = False

        # Check for matches (3+ connected same color)
        group = self._find_connected_same_color(col, row, self.fly_color)
        popped = 0
        if len(group) >= 3:
            for pos in group:
                del self.grid[pos]
                popped += 1
            self.score += popped * POP_SCORE

            # Remove floating bubbles
            floating = self._find_floating()
            dropped = len(floating)
            for pos in floating:
                del self.grid[pos]
            self.score += int(dropped * DROP_BONUS * CHAIN_MULTIPLIER)

        # Check game over: any bubble at or below the danger line
        self._check_game_state()

    def _check_game_state(self):
        """Check for game over or level clear."""
        if not self.grid:
            # Level clear
            self.level_clear = True
            self.score += 500 * self.level
            return

        for (c, r) in self.grid:
            _, sy = grid_to_screen(c, r)
            if sy - BUBBLE_RADIUS <= DANGER_LINE_Y:
                self.game_over = True
                return

    def _advance_level(self):
        """Move to the next level."""
        self.level += 1
        self.level_clear = False
        rows = min(INITIAL_ROWS + self.level - 1, GRID_ROWS - 4)
        self._populate_grid(rows)
        self.current_bubble = self._random_color()
        self.next_bubble = self._random_color()
        self.flying = False

    # ------------------------------------------------------------------
    # Aim line trajectory (with bounces)
    # ------------------------------------------------------------------
    def get_aim_trajectory(self, max_length=800, max_segments=3):
        """Compute dotted aim line points, bouncing off walls."""
        points = []
        x = float(SHOOTER_X)
        y = float(SHOOTER_Y)
        dx = math.cos(self.aim_angle)
        dy = math.sin(self.aim_angle)
        remaining = max_length
        step = 4.0

        points.append((x, y))
        bounces = 0
        while remaining > 0 and bounces <= max_segments:
            x += dx * step
            y += dy * step
            remaining -= step

            # Bounce off left/right walls
            if x - BUBBLE_RADIUS < PLAY_AREA_LEFT:
                x = PLAY_AREA_LEFT + BUBBLE_RADIUS
                dx = -dx
                bounces += 1
            elif x + BUBBLE_RADIUS > PLAY_AREA_RIGHT:
                x = PLAY_AREA_RIGHT - BUBBLE_RADIUS
                dx = -dx
                bounces += 1

            # Stop at top
            if y + BUBBLE_RADIUS >= PLAY_AREA_TOP:
                points.append((x, PLAY_AREA_TOP - BUBBLE_RADIUS))
                break

            # Stop if hitting a grid bubble
            hit = False
            for (gc, gr), _ in self.grid.items():
                gx, gy = grid_to_screen(gc, gr)
                dist = math.sqrt((x - gx) ** 2 + (y - gy) ** 2)
                if dist < BUBBLE_DIAMETER * 0.9:
                    points.append((x, y))
                    hit = True
                    break
            if hit:
                break

            points.append((x, y))

        return points

    # ------------------------------------------------------------------
    # Arcade View callbacks
    # ------------------------------------------------------------------
    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.mode == "select":
            return
        if self.game_over or self.level_clear:
            return

        # Update aim angle from held keys
        if self.key_left:
            self.aim_angle = min(self.aim_angle + AIM_SPEED * delta_time, MAX_ANGLE)
        if self.key_right:
            self.aim_angle = max(self.aim_angle - AIM_SPEED * delta_time, MIN_ANGLE)

        # Update flying bubble
        if self.flying:
            self.fly_x += self.fly_dx * delta_time
            self.fly_y += self.fly_dy * delta_time

            # Bounce off left/right walls
            if self.fly_x - BUBBLE_RADIUS < PLAY_AREA_LEFT:
                self.fly_x = PLAY_AREA_LEFT + BUBBLE_RADIUS
                self.fly_dx = abs(self.fly_dx)
            elif self.fly_x + BUBBLE_RADIUS > PLAY_AREA_RIGHT:
                self.fly_x = PLAY_AREA_RIGHT - BUBBLE_RADIUS
                self.fly_dx = -abs(self.fly_dx)

            # Hit the top
            if self.fly_y + BUBBLE_RADIUS >= PLAY_AREA_TOP:
                self.fly_y = PLAY_AREA_TOP - BUBBLE_RADIUS
                self._snap_and_process()
                return

            # Check collision with existing bubbles
            for (gc, gr), _ in list(self.grid.items()):
                gx, gy = grid_to_screen(gc, gr)
                dist = math.sqrt((self.fly_x - gx) ** 2 + (self.fly_y - gy) ** 2)
                if dist < BUBBLE_DIAMETER * 0.9:
                    self._snap_and_process()
                    return

    def on_key_press(self, key, modifiers):
        if self.mode == "select":
            return
        if self.game_over:
            if key == arcade.key.RETURN:
                self._init_game()
            return

        if self.level_clear:
            if key in (arcade.key.RETURN, arcade.key.SPACE):
                self._advance_level()
            return

        if key == arcade.key.LEFT:
            self.key_left = True
        elif key == arcade.key.RIGHT:
            self.key_right = True
        elif key == arcade.key.SPACE:
            self._fire()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.key_left = False
        elif key == arcade.key.RIGHT:
            self.key_right = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if self.btn_back.contains(x, y):
            if self.mode == "select":
                self.window.show_view(self.menu_view)
            else:
                self.mode = "select"
            return
        if self.btn_help.contains(x, y):
            rules_view = RulesView("Puzzle Bubble", "puzzle_bubble.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.mode == "select":
            if self.btn_solo.contains(x, y):
                self.mode = "solo"
                self._init_game()
            elif self.btn_vs.contains(x, y):
                from games.puzzle_bubble_vs import PuzzleBubbleVSView
                vs_view = PuzzleBubbleVSView(self.menu_view)
                self.window.show_view(vs_view)
            return

        if self.btn_new.contains(x, y):
            self._init_game()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        if self.mode == "select":
            BG = (20, 20, 40)
            arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG)
            self.txt_mode_title.draw()
            self.txt_mode_subtitle.draw()
            self.btn_solo.draw(self.btn_solo.contains(self.mouse_x, self.mouse_y))
            self.btn_vs.draw(self.btn_vs.contains(self.mouse_x, self.mouse_y))
            self.btn_back.draw(self.btn_back.contains(self.mouse_x, self.mouse_y))
            self.btn_help.draw(self.btn_help.contains(self.mouse_x, self.mouse_y))
        else:
            puzzle_bubble_renderer.draw(self)
