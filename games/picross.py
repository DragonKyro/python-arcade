import arcade
import random
import time
from pages.rules import RulesView
from renderers import picross_renderer
from renderers.picross_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    CELL_SIZE, GRID_ORIGIN_X, GRID_ORIGIN_Y, CLUE_AREA_W, CLUE_AREA_H,
)

# ---------- Puzzle generation ----------

THEMES = [
    "Random",
    "Heart",
    "Star",
    "Arrow",
    "Smiley",
]


def _generate_random_pattern(rows, cols, density=0.55):
    """Generate a random binary pattern."""
    pattern = []
    for r in range(rows):
        row = []
        for c in range(cols):
            row.append(1 if random.random() < density else 0)
        pattern.append(row)
    return pattern


def _generate_themed_pattern(theme, rows, cols):
    """Generate a themed pattern for the given grid size."""
    if theme == "Heart" and rows >= 8 and cols >= 8:
        # Simple heart pattern centered in grid
        heart = [
            [0, 1, 1, 0, 0, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        return _embed_pattern(heart, rows, cols)
    elif theme == "Star" and rows >= 8 and cols >= 8:
        star = [
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 0, 0, 1, 1, 0],
            [1, 1, 0, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        return _embed_pattern(star, rows, cols)
    elif theme == "Arrow" and rows >= 8 and cols >= 8:
        arrow = [
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 1, 1, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 1],
            [0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 0],
        ]
        return _embed_pattern(arrow, rows, cols)
    elif theme == "Smiley" and rows >= 8 and cols >= 8:
        smiley = [
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 0, 0, 0, 0, 1, 0],
            [1, 0, 1, 0, 0, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 0, 1, 0, 1],
            [1, 0, 0, 1, 1, 0, 0, 1],
            [0, 1, 0, 0, 0, 0, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
        ]
        return _embed_pattern(smiley, rows, cols)
    # Fallback to random
    return _generate_random_pattern(rows, cols)


def _embed_pattern(small, rows, cols):
    """Embed a small pattern centered in a larger grid, filling edges randomly."""
    sr, sc = len(small), len(small[0])
    pattern = [[0] * cols for _ in range(rows)]
    offset_r = (rows - sr) // 2
    offset_c = (cols - sc) // 2
    for r in range(sr):
        for c in range(sc):
            pattern[offset_r + r][offset_c + c] = small[r][c]
    # Optionally add some random noise in the margins
    for r in range(rows):
        for c in range(cols):
            if r < offset_r or r >= offset_r + sr or c < offset_c or c >= offset_c + sc:
                pattern[r][c] = 1 if random.random() < 0.2 else 0
    return pattern


def _derive_clues(pattern, rows, cols):
    """Derive row and column clues from a binary pattern."""
    row_clues = []
    for r in range(rows):
        clue = []
        count = 0
        for c in range(cols):
            if pattern[r][c] == 1:
                count += 1
            else:
                if count > 0:
                    clue.append(count)
                count = 0
        if count > 0:
            clue.append(count)
        if not clue:
            clue = [0]
        row_clues.append(clue)

    col_clues = []
    for c in range(cols):
        clue = []
        count = 0
        for r in range(rows):
            if pattern[r][c] == 1:
                count += 1
            else:
                if count > 0:
                    clue.append(count)
                count = 0
        if count > 0:
            clue.append(count)
        if not clue:
            clue = [0]
        col_clues.append(clue)

    return row_clues, col_clues


def _check_line(player_line, clue):
    """Check if a player's line (list of 0/1) matches the clue."""
    groups = []
    count = 0
    for v in player_line:
        if v == 1:
            count += 1
        else:
            if count > 0:
                groups.append(count)
            count = 0
    if count > 0:
        groups.append(count)
    if not groups:
        groups = [0]
    return groups == clue


# ---------- View ----------

class PicrossView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.grid_rows = 10
        self.grid_cols = 10
        self.theme = "Random"
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 65, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 135, bar_y, arcade.color.WHITE,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_timer = arcade.Text(
            "", WIDTH / 2, bar_y, arcade.color.WHITE,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_theme_label = arcade.Text(
            "", WIDTH / 2, bar_y - 16, arcade.color.LIGHT_GRAY,
            font_size=10, anchor_x="center", anchor_y="center",
        )
        self.txt_mistakes = arcade.Text(
            "", WIDTH / 2 + 120, bar_y, arcade.color.LIGHT_GRAY,
            font_size=12, anchor_x="center", anchor_y="center",
        )
        # Win overlay
        self.txt_win_title = arcade.Text(
            "Puzzle Complete!", WIDTH / 2, HEIGHT / 2 + 30,
            arcade.color.GOLD, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_time = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 20,
            arcade.color.WHITE, font_size=20,
            anchor_x="center", anchor_y="center",
        )
        self.txt_win_hint = arcade.Text(
            "Click New Game to play again",
            WIDTH / 2, HEIGHT / 2 - 60,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )
        # Row clue texts (max 15 rows, up to 6 clue numbers each)
        self.txt_row_clues = {}
        for r in range(15):
            for i in range(6):
                self.txt_row_clues[(r, i)] = arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY,
                    font_size=11, anchor_x="right", anchor_y="center",
                )
        # Col clue texts (max 15 cols, up to 6 clue numbers each)
        self.txt_col_clues = {}
        for c in range(15):
            for i in range(6):
                self.txt_col_clues[(c, i)] = arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY,
                    font_size=11, anchor_x="center", anchor_y="bottom",
                )
        # Size buttons
        self.txt_size_btns = []
        sizes = ["5x5", "10x10", "15x15"]
        for idx, label in enumerate(sizes):
            bx = 200 + idx * 55
            self.txt_size_btns.append(arcade.Text(
                label, bx, bar_y - 16, arcade.color.WHITE,
                font_size=9, anchor_x="center", anchor_y="center",
            ))
        # Theme cycle button
        self.txt_theme_btn = arcade.Text(
            "Theme", 380, bar_y - 16, arcade.color.WHITE,
            font_size=9, anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        rows, cols = self.grid_rows, self.grid_cols
        if self.theme == "Random":
            self.solution = _generate_random_pattern(rows, cols)
        else:
            self.solution = _generate_themed_pattern(self.theme, rows, cols)
        self.row_clues, self.col_clues = _derive_clues(self.solution, rows, cols)
        # Player grid: 0=empty, 1=filled, 2=marked-X
        self.grid = [[0] * cols for _ in range(rows)]
        self.elapsed_time = 0.0
        self.game_won = False
        self.mistakes = 0
        self.row_complete = [False] * rows
        self.col_complete = [False] * cols
        self._dragging = False
        self._drag_value = 0

    def cell_center(self, row, col):
        """Return pixel center of a grid cell. Row 0 is top visually."""
        ox = GRID_ORIGIN_X + CLUE_AREA_W
        oy = GRID_ORIGIN_Y
        x = ox + col * CELL_SIZE + CELL_SIZE / 2
        y = oy + (self.grid_rows - 1 - row) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def _pixel_to_cell(self, px, py):
        ox = GRID_ORIGIN_X + CLUE_AREA_W
        oy = GRID_ORIGIN_Y
        col = int((px - ox) / CELL_SIZE)
        row = self.grid_rows - 1 - int((py - oy) / CELL_SIZE)
        if 0 <= row < self.grid_rows and 0 <= col < self.grid_cols:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _update_completion(self):
        """Check which rows/cols are completed."""
        for r in range(self.grid_rows):
            player_line = [1 if self.grid[r][c] == 1 else 0 for c in range(self.grid_cols)]
            self.row_complete[r] = _check_line(player_line, self.row_clues[r])
        for c in range(self.grid_cols):
            player_line = [1 if self.grid[r][c] == 1 else 0 for r in range(self.grid_rows)]
            self.col_complete[c] = _check_line(player_line, self.col_clues[c])

    def _check_win(self):
        if all(self.row_complete) and all(self.col_complete):
            self.game_won = True

    # --- arcade callbacks ---

    def on_update(self, delta_time):
        if not self.game_won:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()
        picross_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Back button
        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            self._init_game()
            return

        # Help button
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView("Picross", "picross.txt", None,
                                   self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Size buttons
        sizes_data = [(5, 5), (10, 10), (15, 15)]
        for idx, (nr, nc) in enumerate(sizes_data):
            bx = 200 + idx * 55
            if self._hit_test_button(x, y, bx, bar_y - 16, 48, 18):
                if nr != self.grid_rows or nc != self.grid_cols:
                    self.grid_rows = nr
                    self.grid_cols = nc
                    self._init_game()
                return

        # Theme button
        if self._hit_test_button(x, y, 380, bar_y - 16, 50, 18):
            idx = THEMES.index(self.theme)
            self.theme = THEMES[(idx + 1) % len(THEMES)]
            self._init_game()
            return

        if self.game_won:
            return

        # Grid click
        cell = self._pixel_to_cell(x, y)
        if cell is not None:
            r, c = cell
            if button == arcade.MOUSE_BUTTON_LEFT:
                # Toggle fill
                if self.grid[r][c] == 1:
                    self.grid[r][c] = 0
                else:
                    self.grid[r][c] = 1
                self._drag_value = self.grid[r][c]
            elif button == arcade.MOUSE_BUTTON_RIGHT:
                # Toggle X mark
                if self.grid[r][c] == 2:
                    self.grid[r][c] = 0
                else:
                    self.grid[r][c] = 2
                self._drag_value = self.grid[r][c]
            self._dragging = True
            self._drag_button = button
            self._update_completion()
            self._check_win()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self._dragging or self.game_won:
            return
        cell = self._pixel_to_cell(x, y)
        if cell is not None:
            r, c = cell
            if self._drag_button == arcade.MOUSE_BUTTON_LEFT:
                self.grid[r][c] = self._drag_value
            elif self._drag_button == arcade.MOUSE_BUTTON_RIGHT:
                self.grid[r][c] = self._drag_value
            self._update_completion()
            self._check_win()

    def on_mouse_release(self, x, y, button, modifiers):
        self._dragging = False
