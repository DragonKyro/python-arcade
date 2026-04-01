"""
2048 Game — an arcade.View implementation for arcade 2.6.x
"""

import arcade
import random
import copy

WIDTH = 800
HEIGHT = 600

# Grid configuration
GRID_SIZE = 4
CELL_SIZE = 120
CELL_GAP = 10
GRID_PIXEL = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * CELL_GAP

# Position the grid: centered horizontally, shifted down a bit to leave room for header
GRID_LEFT = (WIDTH - GRID_PIXEL) / 2
GRID_BOTTOM = (HEIGHT - GRID_PIXEL) / 2 - 40

# Tile color mapping (value -> (R, G, B))
TILE_COLORS = {
    0:    (205, 193, 180),
    2:    (238, 228, 218),
    4:    (237, 224, 200),
    8:    (242, 177, 121),
    16:   (245, 149, 99),
    32:   (246, 124, 95),
    64:   (246, 94, 59),
    128:  (237, 207, 114),
    256:  (237, 204, 97),
    512:  (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}

# Text color: dark for 2/4, white for everything else
DARK_TEXT = (119, 110, 101)
LIGHT_TEXT = (255, 255, 255)

# Background color for the grid area
GRID_BG_COLOR = (187, 173, 160)

# Default tile color for values > 2048
HIGH_TILE_COLOR = (60, 58, 50)


class Button:
    """Simple clickable button."""

    def __init__(self, cx, cy, w, h, text, bg_color=(120, 110, 100), text_color=(255, 255, 255)):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.text = text
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self):
        arcade.draw_rectangle_filled(self.cx, self.cy, self.w, self.h, self.bg_color)
        arcade.draw_rectangle_outline(self.cx, self.cy, self.w, self.h, (255, 255, 255), 2)
        arcade.draw_text(
            self.text,
            self.cx, self.cy,
            self.text_color,
            font_size=16,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

    def hit_test(self, x, y):
        return (
            abs(x - self.cx) <= self.w / 2
            and abs(y - self.cy) <= self.h / 2
        )


def _get_tile_color(value):
    """Return the background color for a tile value."""
    if value in TILE_COLORS:
        return TILE_COLORS[value]
    return HIGH_TILE_COLOR


def _get_text_color(value):
    """Return text color: dark for 2/4, white otherwise."""
    if value <= 4:
        return DARK_TEXT
    return LIGHT_TEXT


def _font_size_for_value(value):
    """Return an appropriate font size so large numbers fit in the cell."""
    if value < 100:
        return 40
    if value < 1000:
        return 34
    if value < 10000:
        return 28
    return 22


class Twenty48View(arcade.View):
    """Full 2048 game implemented as an arcade.View."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.won = False
        self.won_acknowledged = False  # player dismissed the win overlay
        self.game_over = False

        # Buttons
        self.back_button = Button(70, HEIGHT - 30, 110, 40, "Back", bg_color=(143, 122, 102))
        self.new_game_button = Button(200, HEIGHT - 30, 130, 40, "New Game", bg_color=(143, 122, 102))

        self._new_game()

    # ------------------------------------------------------------------ #
    # Game logic
    # ------------------------------------------------------------------ #

    def _new_game(self):
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.score = 0
        self.won = False
        self.won_acknowledged = False
        self.game_over = False
        self._spawn_tile()
        self._spawn_tile()

    def _empty_cells(self):
        """Return list of (row, col) for empty cells."""
        cells = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == 0:
                    cells.append((r, c))
        return cells

    def _spawn_tile(self):
        empty = self._empty_cells()
        if not empty:
            return
        r, c = random.choice(empty)
        self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def _compress(self, row):
        """Slide non-zero values to the front of the list (left)."""
        new = [v for v in row if v != 0]
        new += [0] * (GRID_SIZE - len(new))
        return new

    def _merge(self, row):
        """Merge adjacent equal tiles (left-to-right). Each tile merges at most once."""
        score_add = 0
        for i in range(GRID_SIZE - 1):
            if row[i] != 0 and row[i] == row[i + 1]:
                row[i] *= 2
                score_add += row[i]
                row[i + 1] = 0
        return row, score_add

    def _move_left(self, grid):
        new_grid = []
        total_score = 0
        for row in grid:
            compressed = self._compress(row)
            merged, sc = self._merge(compressed)
            total_score += sc
            final = self._compress(merged)
            new_grid.append(final)
        return new_grid, total_score

    def _rotate_90_cw(self, grid):
        """Rotate the grid 90 degrees clockwise."""
        n = GRID_SIZE
        return [[grid[n - 1 - j][i] for j in range(n)] for i in range(n)]

    def _rotate_90_ccw(self, grid):
        """Rotate the grid 90 degrees counter-clockwise."""
        n = GRID_SIZE
        return [[grid[j][n - 1 - i] for j in range(n)] for i in range(n)]

    def _move(self, direction):
        """
        Execute a move. direction is one of 'left', 'right', 'up', 'down'.
        Returns True if the board changed.
        """
        old_grid = copy.deepcopy(self.grid)

        if direction == "left":
            self.grid, sc = self._move_left(self.grid)
        elif direction == "right":
            # Reverse each row, move left, reverse back
            rev = [row[::-1] for row in self.grid]
            moved, sc = self._move_left(rev)
            self.grid = [row[::-1] for row in moved]
        elif direction == "up":
            # Rotate so that up becomes left, move, rotate back
            rotated = self._rotate_90_ccw(self.grid)
            moved, sc = self._move_left(rotated)
            self.grid = self._rotate_90_cw(moved)
        elif direction == "down":
            rotated = self._rotate_90_cw(self.grid)
            moved, sc = self._move_left(rotated)
            self.grid = self._rotate_90_ccw(moved)
        else:
            return False

        changed = self.grid != old_grid
        if changed:
            self.score += sc
            self._spawn_tile()
            # Check win
            if not self.won:
                for row in self.grid:
                    if 2048 in row:
                        self.won = True
            # Check lose
            if not self._has_moves():
                self.game_over = True
        return changed

    def _has_moves(self):
        """Return True if any move is possible."""
        # Any empty cell?
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == 0:
                    return True
        # Any adjacent equal?
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                val = self.grid[r][c]
                if c + 1 < GRID_SIZE and self.grid[r][c + 1] == val:
                    return True
                if r + 1 < GRID_SIZE and self.grid[r + 1][c] == val:
                    return True
        return False

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #

    def on_draw(self):
        arcade.start_render()

        # Background
        arcade.set_background_color((250, 248, 239))

        # Title
        arcade.draw_text(
            "2048",
            WIDTH / 2, HEIGHT - 30,
            DARK_TEXT,
            font_size=36,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )

        # Score
        arcade.draw_text(
            f"Score: {self.score}",
            WIDTH / 2, HEIGHT - 65,
            DARK_TEXT,
            font_size=20,
            anchor_x="center",
            anchor_y="center",
        )

        # Buttons
        self.back_button.draw()
        self.new_game_button.draw()

        # Grid background
        grid_cx = GRID_LEFT + GRID_PIXEL / 2
        grid_cy = GRID_BOTTOM + GRID_PIXEL / 2
        arcade.draw_rectangle_filled(grid_cx, grid_cy, GRID_PIXEL + 6, GRID_PIXEL + 6, GRID_BG_COLOR)

        # Draw each cell
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                value = self.grid[r][c]
                # Cell position: row 0 is top row visually
                x = GRID_LEFT + CELL_GAP + c * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2
                y = GRID_BOTTOM + GRID_PIXEL - (CELL_GAP + r * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2)

                color = _get_tile_color(value)
                arcade.draw_rectangle_filled(x, y, CELL_SIZE, CELL_SIZE, color)

                if value != 0:
                    txt_color = _get_text_color(value)
                    fsize = _font_size_for_value(value)
                    arcade.draw_text(
                        str(value),
                        x, y,
                        txt_color,
                        font_size=fsize,
                        anchor_x="center",
                        anchor_y="center",
                        bold=True,
                    )

        # Win overlay
        if self.won and not self.won_acknowledged:
            self._draw_overlay("You Win!", "Click to continue")

        # Game over overlay
        if self.game_over:
            self._draw_overlay("Game Over!", "Click New Game to restart")

    def _draw_overlay(self, title, subtitle):
        """Draw a semi-transparent overlay with a message."""
        # Semi-transparent backdrop over the grid
        arcade.draw_rectangle_filled(
            WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT, (255, 255, 255, 150)
        )
        arcade.draw_text(
            title,
            WIDTH / 2, HEIGHT / 2 + 20,
            (119, 110, 101),
            font_size=52,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        arcade.draw_text(
            subtitle,
            WIDTH / 2, HEIGHT / 2 - 30,
            (119, 110, 101),
            font_size=20,
            anchor_x="center",
            anchor_y="center",
        )

    # ------------------------------------------------------------------ #
    # Input handling
    # ------------------------------------------------------------------ #

    def on_key_press(self, key, modifiers):
        # Don't allow moves if game over or win overlay is showing
        if self.game_over:
            return
        if self.won and not self.won_acknowledged:
            return

        direction = None
        if key == arcade.key.UP:
            direction = "up"
        elif key == arcade.key.DOWN:
            direction = "down"
        elif key == arcade.key.LEFT:
            direction = "left"
        elif key == arcade.key.RIGHT:
            direction = "right"
        elif key == arcade.key.ESCAPE:
            self.window.show_view(self.menu_view)
            return

        if direction:
            self._move(direction)

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if self.back_button.hit_test(x, y):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self.new_game_button.hit_test(x, y):
            self._new_game()
            return

        # Dismiss win overlay
        if self.won and not self.won_acknowledged and not self.game_over:
            self.won_acknowledged = True
            return


# ---------------------------------------------------------------------- #
# Standalone entry point for testing
# ---------------------------------------------------------------------- #

if __name__ == "__main__":
    class _DummyMenuView(arcade.View):
        """Placeholder so the game can be tested standalone."""
        def on_draw(self):
            arcade.start_render()
            arcade.draw_text("Menu (press Enter for 2048)", WIDTH / 2, HEIGHT / 2,
                             arcade.color.WHITE, 24, anchor_x="center", anchor_y="center")

        def on_key_press(self, key, modifiers):
            if key == arcade.key.RETURN:
                self.window.show_view(Twenty48View(self))

    window = arcade.Window(WIDTH, HEIGHT, "2048")
    menu = _DummyMenuView()
    window.show_view(Twenty48View(menu))
    arcade.run()
