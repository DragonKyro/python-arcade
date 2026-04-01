import arcade
from pages.rules import RulesView
from renderers import kakuro_renderer
from renderers.kakuro_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, CELL_SIZE,
    GRID_ORIGIN_X, GRID_ORIGIN_Y,
)

# Cell types
BLACK = "black"       # solid black (no clue)
CLUE = "clue"         # clue cell with down/across hints
WHITE = "white"       # player-fillable cell

# Puzzles: list of dicts with 'rows', 'cols', 'grid'
# grid[r][c] = BLACK | (CLUE, across_sum_or_0, down_sum_or_0) | WHITE
# across_sum = sum for the run going right; down_sum = sum for run going down
# 0 means no clue in that direction

PUZZLES = [
    # Puzzle 1: 6x6
    {
        "rows": 6, "cols": 6,
        "grid": [
            [BLACK,            BLACK,            (CLUE, 0, 16),  (CLUE, 0, 3),   BLACK,            BLACK],
            [BLACK,            (CLUE, 6, 17),    WHITE,           WHITE,           (CLUE, 0, 12),   BLACK],
            [(CLUE, 23, 0),    WHITE,            WHITE,           WHITE,           WHITE,            BLACK],
            [BLACK,            WHITE,            WHITE,           WHITE,           WHITE,            (CLUE, 0, 0)],
            [BLACK,            (CLUE, 16, 0),    WHITE,           WHITE,           WHITE,            WHITE],
            [BLACK,            BLACK,            (CLUE, 3, 0),    WHITE,           WHITE,            BLACK],
        ],
    },
    # Puzzle 2: 6x6
    {
        "rows": 6, "cols": 6,
        "grid": [
            [BLACK,            (CLUE, 0, 4),    (CLUE, 0, 11),  BLACK,            BLACK,            BLACK],
            [(CLUE, 3, 0),     WHITE,           WHITE,           (CLUE, 0, 10),   BLACK,            BLACK],
            [(CLUE, 15, 3),    WHITE,           WHITE,           WHITE,            (CLUE, 0, 6),    BLACK],
            [BLACK,            (CLUE, 13, 0),   WHITE,           WHITE,            WHITE,            BLACK],
            [BLACK,            BLACK,            (CLUE, 7, 0),   WHITE,            WHITE,            (CLUE, 0, 0)],
            [BLACK,            BLACK,            BLACK,           (CLUE, 3, 0),    WHITE,            WHITE],
        ],
    },
    # Puzzle 3: 5x5
    {
        "rows": 5, "cols": 5,
        "grid": [
            [BLACK,           (CLUE, 0, 17),  (CLUE, 0, 24),  BLACK,           BLACK],
            [(CLUE, 16, 0),   WHITE,           WHITE,           (CLUE, 0, 16),  BLACK],
            [(CLUE, 41, 0),   WHITE,           WHITE,           WHITE,           WHITE],
            [BLACK,           (CLUE, 24, 0),   WHITE,           WHITE,           WHITE],
            [BLACK,           BLACK,            (CLUE, 17, 0),  WHITE,           WHITE],
        ],
    },
]


class KakuroView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.puzzle_index = 0
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for rendering."""
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
        self.txt_title = arcade.Text(
            "Kakuro", WIDTH / 2, bar_y, arcade.color.WHITE,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_puzzle_num = arcade.Text(
            "", WIDTH / 2, bar_y - 15, arcade.color.LIGHT_GRAY,
            font_size=10, anchor_x="center", anchor_y="center",
        )
        # Pre-create text objects for cells (max grid 10x10)
        self.txt_cells = {}
        for r in range(10):
            for c in range(10):
                cx, cy = self._cell_center_raw(r, c)
                self.txt_cells[(r, c)] = arcade.Text(
                    "", cx, cy, arcade.color.BLACK,
                    font_size=18, anchor_x="center", anchor_y="center",
                )
        # Clue texts (across and down) - small text in corners
        self.txt_clue_across = {}
        self.txt_clue_down = {}
        for r in range(10):
            for c in range(10):
                cx, cy = self._cell_center_raw(r, c)
                # Across clue: bottom-right area of cell
                self.txt_clue_across[(r, c)] = arcade.Text(
                    "", cx + CELL_SIZE * 0.15, cy - CELL_SIZE * 0.15,
                    arcade.color.WHITE, font_size=11,
                    anchor_x="center", anchor_y="center",
                )
                # Down clue: top-left area of cell
                self.txt_clue_down[(r, c)] = arcade.Text(
                    "", cx - CELL_SIZE * 0.15, cy + CELL_SIZE * 0.15,
                    arcade.color.WHITE, font_size=11,
                    anchor_x="center", anchor_y="center",
                )
        # Win overlay
        self.txt_win_title = arcade.Text(
            "Puzzle Solved!", WIDTH / 2, HEIGHT / 2 + 30,
            arcade.color.GOLD, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_hint = arcade.Text(
            "Click New Game for next puzzle",
            WIDTH / 2, HEIGHT / 2 - 20,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )

    def _cell_center_raw(self, row, col):
        """Cell center for pre-creating text objects (before puzzle loaded)."""
        x = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE / 2
        y = GRID_ORIGIN_Y + (9 - row) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def _init_game(self):
        """Initialize or reset game state."""
        puzzle = PUZZLES[self.puzzle_index % len(PUZZLES)]
        self.rows = puzzle["rows"]
        self.cols = puzzle["cols"]
        self.grid_def = puzzle["grid"]  # definition
        # Player values: only for WHITE cells
        self.values = [[0] * self.cols for _ in range(self.rows)]
        self.selected = None  # (row, col) or None
        self.conflicts = [[False] * self.cols for _ in range(self.rows)]
        self.game_won = False

    def _cell_center(self, row, col):
        """Return pixel center of a cell. Row 0 is top row visually."""
        x = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE / 2
        y = GRID_ORIGIN_Y + (self.rows - 1 - row) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def _pixel_to_cell(self, px, py):
        """Convert pixel coords to (row, col) or None."""
        col = int((px - GRID_ORIGIN_X) / CELL_SIZE)
        row = (self.rows - 1) - int((py - GRID_ORIGIN_Y) / CELL_SIZE)
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _is_white(self, r, c):
        """Check if cell (r,c) is a white (fillable) cell."""
        cell = self.grid_def[r][c]
        return cell == WHITE

    def _get_across_run(self, r, c):
        """Get the horizontal run of white cells containing (r, c) and its clue."""
        # Find leftmost white cell in this run
        start_c = c
        while start_c > 0 and self._is_white(r, start_c - 1):
            start_c -= 1
        # The clue cell is to the left of start_c
        clue_sum = 0
        if start_c > 0:
            clue_cell = self.grid_def[r][start_c - 1]
            if isinstance(clue_cell, tuple) and clue_cell[0] == CLUE:
                clue_sum = clue_cell[1]  # across sum
        # Collect run
        run = []
        cc = start_c
        while cc < self.cols and self._is_white(r, cc):
            run.append((r, cc))
            cc += 1
        return run, clue_sum

    def _get_down_run(self, r, c):
        """Get the vertical run of white cells containing (r, c) and its clue."""
        start_r = r
        while start_r > 0 and self._is_white(start_r - 1, c):
            start_r -= 1
        clue_sum = 0
        if start_r > 0:
            clue_cell = self.grid_def[start_r - 1][c]
            if isinstance(clue_cell, tuple) and clue_cell[0] == CLUE:
                clue_sum = clue_cell[2]  # down sum
        run = []
        rr = start_r
        while rr < self.rows and self._is_white(rr, c):
            run.append((rr, c))
            rr += 1
        return run, clue_sum

    def _update_conflicts(self):
        """Check for duplicate digits in runs and mark conflicts."""
        self.conflicts = [[False] * self.cols for _ in range(self.rows)]
        checked_runs = set()

        for r in range(self.rows):
            for c in range(self.cols):
                if not self._is_white(r, c):
                    continue
                # Check across run
                run, clue_sum = self._get_across_run(r, c)
                run_key = ("a", run[0][0], run[0][1])
                if run_key not in checked_runs and len(run) > 1:
                    checked_runs.add(run_key)
                    vals = [self.values[rr][cc] for rr, cc in run if self.values[rr][cc] != 0]
                    # Check duplicates
                    if len(vals) != len(set(vals)):
                        for rr, cc in run:
                            if self.values[rr][cc] != 0:
                                v = self.values[rr][cc]
                                count = sum(1 for rr2, cc2 in run if self.values[rr2][cc2] == v)
                                if count > 1:
                                    self.conflicts[rr][cc] = True
                    # Check sum if all filled
                    if len(vals) == len(run) and clue_sum > 0:
                        if sum(vals) != clue_sum:
                            for rr, cc in run:
                                self.conflicts[rr][cc] = True

                # Check down run
                run, clue_sum = self._get_down_run(r, c)
                run_key = ("d", run[0][0], run[0][1])
                if run_key not in checked_runs and len(run) > 1:
                    checked_runs.add(run_key)
                    vals = [self.values[rr][cc] for rr, cc in run if self.values[rr][cc] != 0]
                    if len(vals) != len(set(vals)):
                        for rr, cc in run:
                            if self.values[rr][cc] != 0:
                                v = self.values[rr][cc]
                                count = sum(1 for rr2, cc2 in run if self.values[rr2][cc2] == v)
                                if count > 1:
                                    self.conflicts[rr][cc] = True
                    if len(vals) == len(run) and clue_sum > 0:
                        if sum(vals) != clue_sum:
                            for rr, cc in run:
                                self.conflicts[rr][cc] = True

    def _check_win(self):
        """Check if puzzle is solved: all white cells filled, no conflicts."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self._is_white(r, c):
                    if self.values[r][c] == 0:
                        return False
                    if self.conflicts[r][c]:
                        return False
        self.game_won = True
        return True

    # --- arcade callbacks ---

    def on_draw(self):
        self.clear()
        kakuro_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            self.puzzle_index = (self.puzzle_index + 1) % len(PUZZLES)
            self._init_game()
            return

        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView("Kakuro", "kakuro.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_won:
            return

        cell = self._pixel_to_cell(x, y)
        if cell is not None:
            r, c = cell
            if self._is_white(r, c):
                self.selected = (r, c)
            else:
                self.selected = None

    def on_key_press(self, key, modifiers):
        if self.game_won or self.selected is None:
            return

        r, c = self.selected

        if arcade.key.KEY_1 <= key <= arcade.key.KEY_9:
            self.values[r][c] = key - arcade.key.KEY_0
        elif arcade.key.NUM_1 <= key <= arcade.key.NUM_9:
            self.values[r][c] = key - arcade.key.NUM_0
        elif key in (arcade.key.KEY_0, arcade.key.DELETE, arcade.key.BACKSPACE):
            self.values[r][c] = 0
        elif key == arcade.key.UP and r > 0:
            self._move_selection(r - 1, c)
            return
        elif key == arcade.key.DOWN and r < self.rows - 1:
            self._move_selection(r + 1, c)
            return
        elif key == arcade.key.LEFT and c > 0:
            self._move_selection(r, c - 1)
            return
        elif key == arcade.key.RIGHT and c < self.cols - 1:
            self._move_selection(r, c + 1)
            return
        elif key == arcade.key.ESCAPE:
            self.selected = None
            return
        else:
            return

        self._update_conflicts()
        self._check_win()

    def _move_selection(self, r, c):
        """Move selection to (r, c) if it's a white cell."""
        if 0 <= r < self.rows and 0 <= c < self.cols and self._is_white(r, c):
            self.selected = (r, c)
