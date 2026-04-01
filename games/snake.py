"""
Snake game view for Python Arcade 3.x.
Classic snake gameplay with arrow key controls.
"""

import arcade
import random
from pages.rules import RulesView
from renderers import snake_renderer

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout
TOP_BAR_HEIGHT = 50
CELL_SIZE = 25

# Grid dimensions (play area below top bar)
GRID_COLS = WIDTH // CELL_SIZE
GRID_ROWS = (HEIGHT - TOP_BAR_HEIGHT) // CELL_SIZE
GRID_ORIGIN_X = (WIDTH - GRID_COLS * CELL_SIZE) // 2
GRID_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - GRID_ROWS * CELL_SIZE) // 2

# Directions
UP = (0, 1)
DOWN = (0, -1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Colors (Catppuccin-ish palette to match other games)
BG_COLOR = (30, 30, 46)
GRID_LINE_COLOR = (45, 45, 65)
SNAKE_HEAD_COLOR = (64, 160, 64)
SNAKE_BODY_COLOR = (116, 199, 116)
FOOD_COLOR = (243, 139, 168)
LINE_COLOR = (205, 214, 244)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (30, 30, 46, 200)
STATUS_TEXT_COLOR = (205, 214, 244)
SCORE_COLOR = (249, 226, 175)

# Timing
BASE_MOVE_INTERVAL = 0.15  # seconds between moves at start
MIN_MOVE_INTERVAL = 0.05   # fastest speed


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
        arcade.draw_text(
            self.label,
            self.cx,
            self.cy,
            BUTTON_TEXT_COLOR,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
        )


def _cell_to_screen(col, row):
    """Convert grid (col, row) to screen center (x, y)."""
    x = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE // 2
    y = GRID_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


class SnakeView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.high_score = 0
        self.mouse_x = 0
        self.mouse_y = 0

        # Buttons
        self.btn_back = _Button(60, HEIGHT - 25, 90, 34, "Back")
        self.btn_new = _Button(170, HEIGHT - 25, 110, 34, "New Game")
        self.btn_help = _Button(WIDTH - 30, HEIGHT - 25, 40, 40, "?")

        self._init_game()

    def _init_game(self):
        """Initialize or reset all game state."""
        # Snake starts at center, length 3, moving right
        cx = GRID_COLS // 2
        cy = GRID_ROWS // 2
        self.snake = [(cx - 2, cy), (cx - 1, cy), (cx, cy)]  # tail ... head
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.score = 0
        self.game_over = False
        self.move_timer = 0.0
        self._place_food()

    def _place_food(self):
        """Place food at a random empty cell."""
        snake_set = set(self.snake)
        empty = []
        for c in range(GRID_COLS):
            for r in range(GRID_ROWS):
                if (c, r) not in snake_set:
                    empty.append((c, r))
        if empty:
            self.food = random.choice(empty)
        else:
            # Snake fills the entire board - you win!
            self.food = None

    def _move_interval(self):
        """Current move interval based on snake length."""
        # Speed up as snake grows
        length = len(self.snake)
        interval = BASE_MOVE_INTERVAL - (length - 3) * 0.002
        return max(interval, MIN_MOVE_INTERVAL)

    def on_show_view(self):
        arcade.set_background_color(BG_COLOR)

    def on_update(self, delta_time):
        if self.game_over:
            return

        self.move_timer += delta_time
        if self.move_timer < self._move_interval():
            return
        self.move_timer = 0.0

        # Apply queued direction
        self.direction = self.next_direction

        # Calculate new head position
        head = self.snake[-1]
        new_head = (head[0] + self.direction[0], head[1] + self.direction[1])

        # Wall collision
        if new_head[0] < 0 or new_head[0] >= GRID_COLS or new_head[1] < 0 or new_head[1] >= GRID_ROWS:
            self._end_game()
            return

        # Self collision
        if new_head in self.snake:
            self._end_game()
            return

        # Move snake
        self.snake.append(new_head)

        # Check food
        if new_head == self.food:
            self.score += 1
            if self.score > self.high_score:
                self.high_score = self.score
            self._place_food()
        else:
            self.snake.pop(0)

    def _end_game(self):
        self.game_over = True
        if self.score > self.high_score:
            self.high_score = self.score

    def on_draw(self):
        self.clear()
        snake_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if self.game_over:
            if key == arcade.key.RETURN or key == arcade.key.ENTER:
                self._init_game()
            return

        # Direction changes -- prevent reversing into self
        if key == arcade.key.UP and self.direction != DOWN:
            self.next_direction = UP
        elif key == arcade.key.DOWN and self.direction != UP:
            self.next_direction = DOWN
        elif key == arcade.key.LEFT and self.direction != RIGHT:
            self.next_direction = LEFT
        elif key == arcade.key.RIGHT and self.direction != LEFT:
            self.next_direction = RIGHT

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
            return

        if self.btn_new.contains(x, y):
            self._init_game()
            return

        if self.btn_help.contains(x, y):
            rules_view = RulesView("Snake", "snake.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return
