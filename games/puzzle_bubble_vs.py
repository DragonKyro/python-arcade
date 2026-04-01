"""
Puzzle Bubble VS mode -- split-screen competitive Puzzle Bubble against an AI opponent.
"""

import arcade
import random
import math
from collections import deque
from ai.puzzle_bubble_ai import PuzzleBubbleAI
from pages.rules import RulesView
from renderers import puzzle_bubble_vs_renderer

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
BOARD_WIDTH = 350
BOARD_GAP = 20
BOARD_LEFT_X = (WIDTH / 2 - BOARD_GAP / 2 - BOARD_WIDTH)
BOARD_RIGHT_X = (WIDTH / 2 + BOARD_GAP / 2)

# Grid
BUBBLE_RADIUS = 12
BUBBLE_DIAMETER = BUBBLE_RADIUS * 2
GRID_COLS = 8
GRID_ROWS = 18
INITIAL_ROWS = 5

# Board vertical layout
BOARD_TOP = HEIGHT - TOP_BAR_HEIGHT - 10
BOARD_BOTTOM = 50

# Shooter
SHOOTER_Y_OFFSET = 30  # from board bottom
MIN_ANGLE = math.radians(10)
MAX_ANGLE = math.radians(170)
AIM_SPEED = 2.5  # radians per second
BUBBLE_SPEED = 500.0

# Danger line -- relative to board bottom
DANGER_LINE_OFFSET = 70

# Colors
BG_COLOR = (20, 20, 35)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (20, 20, 35, 200)
STATUS_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (249, 226, 175)
JUNK_COLOR_NAME = "gray"

# Bubble colors
BUBBLE_COLORS = {
    "red": (243, 80, 80),
    "blue": (80, 140, 250),
    "green": (80, 220, 120),
    "yellow": (250, 220, 80),
    "purple": (180, 100, 240),
    "orange": (250, 160, 60),
    "gray": (140, 140, 150),
}
COLOR_NAMES = [c for c in BUBBLE_COLORS if c != "gray"]

# Scoring
POP_SCORE = 10
DROP_BONUS = 20

# Difficulty button colors
EASY_COLOR = (30, 120, 50)
EASY_HOVER = (40, 160, 65)
MEDIUM_COLOR = (160, 130, 20)
MEDIUM_HOVER = (200, 165, 30)
HARD_COLOR = (160, 30, 30)
HARD_HOVER = (200, 45, 45)
WHITE = (255, 255, 255)


class _Button:
    """Simple rectangular button helper."""

    def __init__(self, cx, cy, w, h, label, color=BUTTON_COLOR,
                 hover_color=BUTTON_HOVER_COLOR, text_color=BUTTON_TEXT_COLOR,
                 font_size=14):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.label = label
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font_size = font_size

    def contains(self, x, y):
        return (abs(x - self.cx) <= self.w / 2) and (abs(y - self.cy) <= self.h / 2)

    def draw(self, hover=False):
        color = self.hover_color if hover else self.color
        arcade.draw_rect_filled(arcade.XYWH(self.cx, self.cy, self.w, self.h), color)
        arcade.draw_rect_outline(arcade.XYWH(self.cx, self.cy, self.w, self.h), LINE_COLOR, 2)
        if not hasattr(self, '_txt_label'):
            self._txt_label = arcade.Text(
                self.label, self.cx, self.cy, self.text_color,
                font_size=self.font_size, anchor_x="center", anchor_y="center",
            )
        self._txt_label.text = self.label
        self._txt_label.x = self.cx
        self._txt_label.y = self.cy
        self._txt_label.draw()


# ------------------------------------------------------------------
# Board helper: coordinate conversions per board
# ------------------------------------------------------------------

def grid_to_screen(col, row, board_left):
    """Convert grid (col, row) to screen center (x, y) for a board whose left edge is board_left."""
    origin_x = board_left + BUBBLE_RADIUS + 10  # small left margin
    origin_y = BOARD_TOP - BUBBLE_RADIUS
    offset = BUBBLE_RADIUS if row % 2 == 1 else 0
    x = origin_x + col * BUBBLE_DIAMETER + offset
    y = origin_y - row * (BUBBLE_DIAMETER * 0.866)
    return x, y


def screen_to_grid(x, y, board_left):
    """Convert screen (x, y) to nearest grid (col, row) for a board."""
    best_dist = float('inf')
    best_col, best_row = 0, 0
    for row in range(GRID_ROWS):
        max_cols = GRID_COLS - (1 if row % 2 == 1 else 0)
        for col in range(max_cols):
            gx, gy = grid_to_screen(col, row, board_left)
            dist = (x - gx) ** 2 + (y - gy) ** 2
            if dist < best_dist:
                best_dist = dist
                best_col, best_row = col, row
    return best_col, best_row


def shooter_pos(board_left):
    """Return (x, y) of the shooter for a board."""
    x = board_left + BOARD_WIDTH / 2
    y = BOARD_BOTTOM + SHOOTER_Y_OFFSET
    return x, y


def danger_line_y():
    """Return the y position of the danger line."""
    return BOARD_BOTTOM + DANGER_LINE_OFFSET


# ------------------------------------------------------------------
# Board state container
# ------------------------------------------------------------------

class _BoardState:
    """State for one side of the VS game."""

    def __init__(self, board_left):
        self.board_left = board_left
        self.grid = {}  # (col, row) -> color_name
        self.score = 0
        self.aim_angle = math.radians(90)

        # Flying bubble
        self.flying = False
        self.fly_x = 0.0
        self.fly_y = 0.0
        self.fly_dx = 0.0
        self.fly_dy = 0.0
        self.fly_color = None

        # Current / next bubble
        self.current_bubble = None
        self.next_bubble = None

        # Junk pending from opponent
        self.pending_junk = 0

        self.lost = False

    def populate(self, num_rows):
        """Fill top rows with random bubbles."""
        self.grid = {}
        for row in range(num_rows):
            max_cols = GRID_COLS - (1 if row % 2 == 1 else 0)
            for col in range(max_cols):
                self.grid[(col, row)] = random.choice(COLOR_NAMES)

    def random_color(self):
        """Pick a random color from what exists on the board."""
        grid_colors = {v for v in self.grid.values() if v != JUNK_COLOR_NAME}
        if grid_colors:
            return random.choice(list(grid_colors))
        return random.choice(COLOR_NAMES)

    def fire(self):
        """Fire the current bubble."""
        if self.flying or self.lost:
            return
        sx, sy = shooter_pos(self.board_left)
        self.flying = True
        self.fly_x = float(sx)
        self.fly_y = float(sy)
        self.fly_dx = math.cos(self.aim_angle) * BUBBLE_SPEED
        self.fly_dy = math.sin(self.aim_angle) * BUBBLE_SPEED
        self.fly_color = self.current_bubble
        self.current_bubble = self.next_bubble
        self.next_bubble = self.random_color()

    def neighbors(self, col, row):
        """Return valid hex-grid neighbors."""
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
            if r < 0 or r >= GRID_ROWS:
                continue
            max_cols = GRID_COLS - (1 if r % 2 == 1 else 0)
            if c < 0 or c >= max_cols:
                continue
            valid.append((c, r))
        return valid

    def find_connected_same_color(self, col, row, color):
        """BFS to find all connected bubbles of the same color."""
        visited = set()
        queue = deque()
        queue.append((col, row))
        visited.add((col, row))
        while queue:
            c, r = queue.popleft()
            for nc, nr in self.neighbors(c, r):
                if (nc, nr) not in visited and self.grid.get((nc, nr)) == color:
                    visited.add((nc, nr))
                    queue.append((nc, nr))
        return visited

    def find_floating(self):
        """Find all bubbles not connected to the top row."""
        connected = set()
        queue = deque()
        for (c, r) in self.grid:
            if r == 0:
                connected.add((c, r))
                queue.append((c, r))
        while queue:
            c, r = queue.popleft()
            for nc, nr in self.neighbors(c, r):
                if (nc, nr) not in connected and (nc, nr) in self.grid:
                    connected.add((nc, nr))
                    queue.append((nc, nr))
        return {pos for pos in self.grid if pos not in connected}

    def snap_and_process(self):
        """Snap flying bubble to grid, check matches. Returns junk count to send to opponent."""
        col, row = screen_to_grid(self.fly_x, self.fly_y, self.board_left)

        # Find nearest free cell if occupied
        if (col, row) in self.grid:
            best_dist = float('inf')
            best_pos = (col, row)
            for nc, nr in self.neighbors(col, row):
                if (nc, nr) not in self.grid:
                    gx, gy = grid_to_screen(nc, nr, self.board_left)
                    d = (self.fly_x - gx) ** 2 + (self.fly_y - gy) ** 2
                    if d < best_dist:
                        best_dist = d
                        best_pos = (nc, nr)
            col, row = best_pos

        self.grid[(col, row)] = self.fly_color
        self.flying = False

        junk_to_send = 0

        group = self.find_connected_same_color(col, row, self.fly_color)
        popped = 0
        if len(group) >= 3:
            for pos in group:
                del self.grid[pos]
                popped += 1
            self.score += popped * POP_SCORE

            # Remove floating bubbles
            floating = self.find_floating()
            dropped = len(floating)
            for pos in floating:
                del self.grid[pos]
            self.score += dropped * DROP_BONUS

            # Calculate junk to send: 3=1, 4=2, 5+=3, plus bonus for floaters
            if popped == 3:
                junk_to_send = 1
            elif popped == 4:
                junk_to_send = 2
            else:
                junk_to_send = 3
            # Bonus for dropped floaters
            junk_to_send += dropped

        # Check if game over
        self._check_danger()

        return junk_to_send

    def receive_junk(self):
        """Add pending junk bubbles as gray on the top rows."""
        if self.pending_junk <= 0:
            return

        count = self.pending_junk
        self.pending_junk = 0

        # Shift existing grid down by the needed rows
        junk_rows = max(1, (count + GRID_COLS - 1) // GRID_COLS)

        # Shift all existing bubbles down
        new_grid = {}
        for (c, r), color in self.grid.items():
            new_r = r + junk_rows
            if new_r < GRID_ROWS:
                new_grid[(c, new_r)] = color
        self.grid = new_grid

        # Fill top rows with gray junk
        placed = 0
        for row in range(junk_rows):
            max_cols = GRID_COLS - (1 if row % 2 == 1 else 0)
            for col in range(max_cols):
                if placed >= count:
                    break
                self.grid[(col, row)] = JUNK_COLOR_NAME
                placed += 1
            if placed >= count:
                break

        self._check_danger()

    def _check_danger(self):
        """Check if any bubble is at or below the danger line."""
        dl = danger_line_y()
        for (c, r) in self.grid:
            _, sy = grid_to_screen(c, r, self.board_left)
            if sy - BUBBLE_RADIUS <= dl:
                self.lost = True
                return

    def get_aim_trajectory(self, max_length=600, max_segments=3):
        """Compute aim line points with wall bounces."""
        sx, sy = shooter_pos(self.board_left)
        points = []
        x, y = float(sx), float(sy)
        dx = math.cos(self.aim_angle)
        dy = math.sin(self.aim_angle)
        remaining = max_length
        step = 4.0

        left_wall = self.board_left
        right_wall = self.board_left + BOARD_WIDTH

        points.append((x, y))
        bounces = 0
        while remaining > 0 and bounces <= max_segments:
            x += dx * step
            y += dy * step
            remaining -= step

            if x - BUBBLE_RADIUS < left_wall:
                x = left_wall + BUBBLE_RADIUS
                dx = -dx
                bounces += 1
            elif x + BUBBLE_RADIUS > right_wall:
                x = right_wall - BUBBLE_RADIUS
                dx = -dx
                bounces += 1

            if y + BUBBLE_RADIUS >= BOARD_TOP:
                points.append((x, BOARD_TOP - BUBBLE_RADIUS))
                break

            # Stop if hitting a grid bubble
            hit = False
            for (gc, gr), _ in self.grid.items():
                gx, gy = grid_to_screen(gc, gr, self.board_left)
                dist = math.sqrt((x - gx) ** 2 + (y - gy) ** 2)
                if dist < BUBBLE_DIAMETER * 0.9:
                    points.append((x, y))
                    hit = True
                    break
            if hit:
                break

            points.append((x, y))

        return points

    def update_flying(self, delta_time):
        """Update a flying bubble, handling wall bounces and collisions.
        Returns junk_to_send (int) when the bubble snaps, else 0."""
        if not self.flying:
            return 0

        self.fly_x += self.fly_dx * delta_time
        self.fly_y += self.fly_dy * delta_time

        left_wall = self.board_left
        right_wall = self.board_left + BOARD_WIDTH

        if self.fly_x - BUBBLE_RADIUS < left_wall:
            self.fly_x = left_wall + BUBBLE_RADIUS
            self.fly_dx = abs(self.fly_dx)
        elif self.fly_x + BUBBLE_RADIUS > right_wall:
            self.fly_x = right_wall - BUBBLE_RADIUS
            self.fly_dx = -abs(self.fly_dx)

        # Hit top
        if self.fly_y + BUBBLE_RADIUS >= BOARD_TOP:
            self.fly_y = BOARD_TOP - BUBBLE_RADIUS
            return self.snap_and_process()

        # Hit existing bubble
        for (gc, gr), _ in list(self.grid.items()):
            gx, gy = grid_to_screen(gc, gr, self.board_left)
            dist = math.sqrt((self.fly_x - gx) ** 2 + (self.fly_y - gy) ** 2)
            if dist < BUBBLE_DIAMETER * 0.9:
                return self.snap_and_process()

        return 0


# ==================================================================
# Main View
# ==================================================================

class PuzzleBubbleVSView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.mouse_x = 0
        self.mouse_y = 0

        # Top bar buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_help = _Button(WIDTH - 40, HEIGHT - 25, 40, 40, "?")

        # Difficulty selection buttons
        btn_y = HEIGHT // 2
        self.btn_easy = _Button(WIDTH // 2 - 150, btn_y, 120, 50, "Easy",
                                EASY_COLOR, EASY_HOVER, WHITE, 18)
        self.btn_medium = _Button(WIDTH // 2, btn_y, 120, 50, "Medium",
                                  MEDIUM_COLOR, MEDIUM_HOVER, WHITE, 18)
        self.btn_hard = _Button(WIDTH // 2 + 150, btn_y, 120, 50, "Hard",
                                HARD_COLOR, HARD_HOVER, WHITE, 18)
        self.difficulty_buttons = [self.btn_easy, self.btn_medium, self.btn_hard]

        # Key states
        self.key_left = False
        self.key_right = False

        # State
        self.state = "select"  # "select", "playing", "gameover"
        self.ai = None
        self.ai_timer = 0.0

        # Boards
        self.player_board = None
        self.ai_board = None

        # Winner text
        self.winner = ""  # "player" or "ai"

        self._create_texts()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        self.txt_title = arcade.Text(
            "PUZZLE BUBBLE VS", WIDTH / 2, HEIGHT / 2 + 120, SCORE_COLOR,
            font_size=28, bold=True, anchor_x="center", anchor_y="center",
        )
        self.txt_select = arcade.Text(
            "Select Difficulty", WIDTH / 2, HEIGHT / 2 + 60, STATUS_TEXT_COLOR,
            font_size=18, anchor_x="center", anchor_y="center",
        )
        self.txt_vs = arcade.Text(
            "VS", WIDTH / 2, HEIGHT / 2, (243, 139, 168),
            font_size=28, bold=True, anchor_x="center", anchor_y="center",
        )
        self.txt_player_label = arcade.Text(
            "PLAYER", BOARD_LEFT_X + BOARD_WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT - 2,
            SCORE_COLOR, font_size=11, bold=True,
            anchor_x="center", anchor_y="top",
        )
        self.txt_ai_label = arcade.Text(
            "AI", BOARD_RIGHT_X + BOARD_WIDTH / 2, HEIGHT - TOP_BAR_HEIGHT - 2,
            SCORE_COLOR, font_size=11, bold=True,
            anchor_x="center", anchor_y="top",
        )
        self.txt_player_score = arcade.Text(
            "0", BOARD_LEFT_X + BOARD_WIDTH / 2, BOARD_BOTTOM + 8, SCORE_COLOR,
            font_size=12, anchor_x="center", anchor_y="center",
        )
        self.txt_ai_score = arcade.Text(
            "0", BOARD_RIGHT_X + BOARD_WIDTH / 2, BOARD_BOTTOM + 8, SCORE_COLOR,
            font_size=12, anchor_x="center", anchor_y="center",
        )
        self.txt_player_junk = arcade.Text(
            "", BOARD_LEFT_X + BOARD_WIDTH - 10, BOARD_TOP - 5, (243, 139, 168),
            font_size=10, anchor_x="right", anchor_y="top",
        )
        self.txt_ai_junk = arcade.Text(
            "", BOARD_RIGHT_X + BOARD_WIDTH - 10, BOARD_TOP - 5, (243, 139, 168),
            font_size=10, anchor_x="right", anchor_y="top",
        )
        self.txt_winner = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 + 30, (166, 227, 161),
            font_size=36, bold=True, anchor_x="center", anchor_y="center",
        )
        self.txt_restart_hint = arcade.Text(
            "Press ENTER to play again", WIDTH / 2, HEIGHT / 2 - 20,
            STATUS_TEXT_COLOR, font_size=14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_difficulty_label = arcade.Text(
            "", WIDTH / 2, BOARD_BOTTOM + 8, STATUS_TEXT_COLOR,
            font_size=10, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------
    # Game state
    # ------------------------------------------------------------------

    def _start_game(self, difficulty):
        """Start a new VS game with the chosen difficulty."""
        self.ai = PuzzleBubbleAI(difficulty)
        self.ai_timer = self.ai.settings['fire_delay']

        self.player_board = _BoardState(BOARD_LEFT_X)
        self.ai_board = _BoardState(BOARD_RIGHT_X)

        self.player_board.populate(INITIAL_ROWS)
        self.ai_board.populate(INITIAL_ROWS)

        self.player_board.current_bubble = self.player_board.random_color()
        self.player_board.next_bubble = self.player_board.random_color()
        self.ai_board.current_bubble = self.ai_board.random_color()
        self.ai_board.next_bubble = self.ai_board.random_color()

        self.winner = ""
        self.state = "playing"

        self.key_left = False
        self.key_right = False

    # ------------------------------------------------------------------
    # Arcade View callbacks
    # ------------------------------------------------------------------

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.state != "playing":
            return

        pb = self.player_board
        ab = self.ai_board

        if pb.lost or ab.lost:
            return

        # --- Player aim ---
        if self.key_left:
            pb.aim_angle = min(pb.aim_angle + AIM_SPEED * delta_time, MAX_ANGLE)
        if self.key_right:
            pb.aim_angle = max(pb.aim_angle - AIM_SPEED * delta_time, MIN_ANGLE)

        # --- Update flying bubbles ---
        player_junk = pb.update_flying(delta_time)
        if player_junk > 0:
            ab.pending_junk += player_junk

        ai_junk = ab.update_flying(delta_time)
        if ai_junk > 0:
            pb.pending_junk += ai_junk

        # --- Deliver junk after a shot lands (not while flying) ---
        if not pb.flying and pb.pending_junk > 0:
            pb.receive_junk()
        if not ab.flying and ab.pending_junk > 0:
            ab.receive_junk()

        # --- AI logic ---
        if not ab.flying and not ab.lost:
            self.ai_timer -= delta_time
            if self.ai_timer <= 0:
                angle = self.ai.get_aim_angle(
                    ab.grid, ab.current_bubble, GRID_COLS, GRID_ROWS, BUBBLE_RADIUS
                )
                ab.aim_angle = angle
                ab.fire()
                self.ai_timer = self.ai.settings['fire_delay']

        # --- Check for game over ---
        if pb.lost:
            self.winner = "ai"
            self.state = "gameover"
        elif ab.lost:
            self.winner = "player"
            self.state = "gameover"

    def on_draw(self):
        self.clear()
        puzzle_bubble_vs_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if self.state == "gameover":
            if key == arcade.key.RETURN:
                difficulty = self.ai.difficulty if self.ai else 'medium'
                self._start_game(difficulty)
            return

        if self.state == "select":
            return

        if key == arcade.key.LEFT:
            self.key_left = True
        elif key == arcade.key.RIGHT:
            self.key_right = True
        elif key == arcade.key.SPACE:
            if self.player_board and not self.player_board.lost:
                self.player_board.fire()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.key_left = False
        elif key == arcade.key.RIGHT:
            self.key_right = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Top bar buttons
        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
            return
        if self.btn_help.contains(x, y):
            rules_view = RulesView("Puzzle Bubble VS", "puzzle_bubble_vs.txt",
                                   None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Difficulty selection
        if self.state == "select":
            if self.btn_easy.contains(x, y):
                self._start_game('easy')
            elif self.btn_medium.contains(x, y):
                self._start_game('medium')
            elif self.btn_hard.contains(x, y):
                self._start_game('hard')
