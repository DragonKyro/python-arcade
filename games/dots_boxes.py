"""
Dots and Boxes game view for Python Arcade 2.6.x.
"""

import arcade
import copy

from ai.dots_boxes_ai import DotsBoxesAI

# Window / layout constants
WIDTH = 800
HEIGHT = 600

GRID_ROWS = 5
GRID_COLS = 5
DOT_COUNT_X = GRID_COLS + 1  # 6
DOT_COUNT_Y = GRID_ROWS + 1  # 6

DOT_SPACING = 80
DOT_RADIUS = 6

# Compute top-left of the grid so it is centred
GRID_W = (DOT_COUNT_X - 1) * DOT_SPACING
GRID_H = (DOT_COUNT_Y - 1) * DOT_SPACING
ORIGIN_X = (WIDTH - GRID_W) / 2
ORIGIN_Y = (HEIGHT - GRID_H) / 2 - 10  # nudge down a bit for score room

# Colours
COLOR_BG = arcade.color.WHITE
COLOR_DOT = arcade.color.BLACK
COLOR_PLAYER_LINE = arcade.color.BLUE
COLOR_AI_LINE = arcade.color.RED
COLOR_PLAYER_FILL = (173, 216, 230, 120)  # light blue
COLOR_AI_FILL = (255, 182, 182, 120)      # light red
COLOR_UNDRAWN = (220, 220, 220)
COLOR_TEXT = arcade.color.BLACK

LINE_WIDTH = 4
HIT_TOLERANCE = 20  # pixels from a line segment centre to register a click

# Button geometry
BTN_W = 100
BTN_H = 32
BTN_BACK_X = 60
BTN_BACK_Y = HEIGHT - 25
BTN_NEW_X = WIDTH - 60
BTN_NEW_Y = HEIGHT - 25


def _dot_pos(row, col):
    """Return (x, y) screen position for the dot at grid (row, col). Row 0 is top."""
    x = ORIGIN_X + col * DOT_SPACING
    y = ORIGIN_Y + (GRID_ROWS - row) * DOT_SPACING  # flip so row 0 is top visually
    return x, y


class DotsBoxesView(arcade.View):
    """Dots and Boxes: player vs AI."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = DotsBoxesAI()
        self._init_game()

    # ------------------------------------------------------------------ #
    # State helpers
    # ------------------------------------------------------------------ #
    def _init_game(self):
        # Horizontal lines: (GRID_ROWS+1) x GRID_COLS
        self.h_lines = [[False] * GRID_COLS for _ in range(GRID_ROWS + 1)]
        # Vertical lines: GRID_ROWS x (GRID_COLS+1)
        self.v_lines = [[False] * (GRID_COLS + 1) for _ in range(GRID_ROWS)]

        # Who drew each line: same shape, value None / 'player' / 'ai'
        self.h_owners = [[None] * GRID_COLS for _ in range(GRID_ROWS + 1)]
        self.v_owners = [[None] * (GRID_COLS + 1) for _ in range(GRID_ROWS)]

        # Box owners: GRID_ROWS x GRID_COLS, None / 'player' / 'ai'
        self.box_owner = [[None] * GRID_COLS for _ in range(GRID_ROWS)]

        self.player_score = 0
        self.ai_score = 0
        self.current_turn = 'player'  # 'player' or 'ai'
        self.game_over = False

        # AI delay accumulator
        self.ai_timer = 0.0
        self.ai_delay = 0.3

    def _all_lines_drawn(self):
        for row in self.h_lines:
            if False in row:
                return False
        for row in self.v_lines:
            if False in row:
                return False
        return True

    def _place_line(self, orientation, r, c, who):
        """Place a line and check for completed boxes. Return number of boxes completed."""
        if orientation == 'h':
            self.h_lines[r][c] = True
            self.h_owners[r][c] = who
        else:
            self.v_lines[r][c] = True
            self.v_owners[r][c] = who

        completed = 0
        boxes_to_check = []
        if orientation == 'h':
            if r > 0:
                boxes_to_check.append((r - 1, c))
            if r < GRID_ROWS:
                boxes_to_check.append((r, c))
        else:
            if c > 0:
                boxes_to_check.append((r, c - 1))
            if c < GRID_COLS:
                boxes_to_check.append((r, c))

        for br, bc in boxes_to_check:
            if self.box_owner[br][bc] is None:
                if self.ai.count_sides(self.h_lines, self.v_lines, br, bc) == 4:
                    self.box_owner[br][bc] = who
                    if who == 'player':
                        self.player_score += 1
                    else:
                        self.ai_score += 1
                    completed += 1

        if self._all_lines_drawn():
            self.game_over = True

        return completed

    # ------------------------------------------------------------------ #
    # Input
    # ------------------------------------------------------------------ #
    def _closest_line(self, mx, my):
        """Return (orientation, r, c, dist) of the closest undrawn line to (mx, my)."""
        best = None
        best_dist = float('inf')

        # Check horizontal lines
        for r in range(GRID_ROWS + 1):
            for c in range(GRID_COLS):
                if self.h_lines[r][c]:
                    continue
                x1, y1 = _dot_pos(r, c)
                x2, y2 = _dot_pos(r, c + 1)
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                d = ((mx - cx) ** 2 + (my - cy) ** 2) ** 0.5
                if d < best_dist:
                    best_dist = d
                    best = ('h', r, c, d)

        # Check vertical lines
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS + 1):
                if self.v_lines[r][c]:
                    continue
                x1, y1 = _dot_pos(r, c)
                x2, y2 = _dot_pos(r + 1, c)
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                d = ((mx - cx) ** 2 + (my - cy) ** 2) ** 0.5
                if d < best_dist:
                    best_dist = d
                    best = ('v', r, c, d)

        return best

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if (BTN_BACK_X - BTN_W / 2 <= x <= BTN_BACK_X + BTN_W / 2
                and BTN_BACK_Y - BTN_H / 2 <= y <= BTN_BACK_Y + BTN_H / 2):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if (BTN_NEW_X - BTN_W / 2 <= x <= BTN_NEW_X + BTN_W / 2
                and BTN_NEW_Y - BTN_H / 2 <= y <= BTN_NEW_Y + BTN_H / 2):
            self._init_game()
            return

        if self.game_over or self.current_turn != 'player':
            return

        result = self._closest_line(x, y)
        if result is None:
            return
        orientation, r, c, dist = result
        if dist > HIT_TOLERANCE + DOT_SPACING / 2:
            return

        completed = self._place_line(orientation, r, c, 'player')
        if not self.game_over and completed == 0:
            self.current_turn = 'ai'
            self.ai_timer = 0.0

    # ------------------------------------------------------------------ #
    # Update (AI turn)
    # ------------------------------------------------------------------ #
    def on_update(self, delta_time):
        if self.game_over or self.current_turn != 'ai':
            return

        self.ai_timer += delta_time
        if self.ai_timer < self.ai_delay:
            return

        move = self.ai.get_move(self.h_lines, self.v_lines, GRID_ROWS, GRID_COLS)
        if move is None:
            self.game_over = True
            return

        orientation, r, c = move
        completed = self._place_line(orientation, r, c, 'ai')

        if not self.game_over:
            if completed > 0:
                # AI gets another turn; reset timer
                self.ai_timer = 0.0
            else:
                self.current_turn = 'player'

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #
    def on_draw(self):
        arcade.start_render()
        self.draw_background()
        self.draw_filled_boxes()
        self.draw_lines()
        self.draw_dots()
        self.draw_ui()

    def draw_background(self):
        arcade.draw_rectangle_filled(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT, COLOR_BG)

    def draw_filled_boxes(self):
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                owner = self.box_owner[r][c]
                if owner is None:
                    continue
                x1, y1 = _dot_pos(r, c)
                x2, y2 = _dot_pos(r + 1, c + 1)
                cx = (x1 + x2) / 2
                cy = (y1 + y2) / 2
                color = COLOR_PLAYER_FILL if owner == 'player' else COLOR_AI_FILL
                arcade.draw_rectangle_filled(cx, cy, DOT_SPACING, DOT_SPACING, color)

    def draw_lines(self):
        # Horizontal
        for r in range(GRID_ROWS + 1):
            for c in range(GRID_COLS):
                x1, y1 = _dot_pos(r, c)
                x2, y2 = _dot_pos(r, c + 1)
                if self.h_lines[r][c]:
                    owner = self.h_owners[r][c]
                    color = COLOR_PLAYER_LINE if owner == 'player' else COLOR_AI_LINE
                    arcade.draw_line(x1, y1, x2, y2, color, LINE_WIDTH)
                else:
                    arcade.draw_line(x1, y1, x2, y2, COLOR_UNDRAWN, 1)

        # Vertical
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS + 1):
                x1, y1 = _dot_pos(r, c)
                x2, y2 = _dot_pos(r + 1, c)
                if self.v_lines[r][c]:
                    owner = self.v_owners[r][c]
                    color = COLOR_PLAYER_LINE if owner == 'player' else COLOR_AI_LINE
                    arcade.draw_line(x1, y1, x2, y2, color, LINE_WIDTH)
                else:
                    arcade.draw_line(x1, y1, x2, y2, COLOR_UNDRAWN, 1)

    def draw_dots(self):
        for r in range(DOT_COUNT_Y):
            for c in range(DOT_COUNT_X):
                x, y = _dot_pos(r, c)
                arcade.draw_circle_filled(x, y, DOT_RADIUS, COLOR_DOT)

    def draw_ui(self):
        # Score
        arcade.draw_text(
            f"Player (Blue): {self.player_score}    AI (Red): {self.ai_score}",
            WIDTH / 2, HEIGHT - 55, COLOR_TEXT, 16, anchor_x="center"
        )

        # Turn / game-over indicator
        if self.game_over:
            if self.player_score > self.ai_score:
                msg = "You win!"
            elif self.ai_score > self.player_score:
                msg = "AI wins!"
            else:
                msg = "It's a tie!"
            arcade.draw_text(msg, WIDTH / 2, HEIGHT - 80, COLOR_TEXT, 18,
                             anchor_x="center", bold=True)
        else:
            turn_msg = "Your turn" if self.current_turn == 'player' else "AI thinking..."
            arcade.draw_text(turn_msg, WIDTH / 2, HEIGHT - 80, COLOR_TEXT, 14,
                             anchor_x="center")

        # Back button
        arcade.draw_rectangle_filled(BTN_BACK_X, BTN_BACK_Y, BTN_W, BTN_H,
                                     arcade.color.LIGHT_GRAY)
        arcade.draw_rectangle_outline(BTN_BACK_X, BTN_BACK_Y, BTN_W, BTN_H,
                                      arcade.color.DARK_GRAY, 2)
        arcade.draw_text("Back", BTN_BACK_X, BTN_BACK_Y, COLOR_TEXT, 13,
                         anchor_x="center", anchor_y="center")

        # New Game button
        arcade.draw_rectangle_filled(BTN_NEW_X, BTN_NEW_Y, BTN_W, BTN_H,
                                     arcade.color.LIGHT_GRAY)
        arcade.draw_rectangle_outline(BTN_NEW_X, BTN_NEW_Y, BTN_W, BTN_H,
                                      arcade.color.DARK_GRAY, 2)
        arcade.draw_text("New Game", BTN_NEW_X, BTN_NEW_Y, COLOR_TEXT, 13,
                         anchor_x="center", anchor_y="center")
