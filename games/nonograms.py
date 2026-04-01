import arcade
import random
from pages.rules import RulesView
from renderers import nonograms_renderer
from renderers.nonograms_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, PLAYING, WON,
    EMPTY, FILLED, MARKED_X,
    CELL_SIZE, CLUE_AREA_WIDTH, CLUE_AREA_HEIGHT,
    grid_origin, cell_center,
)


def _generate_puzzle(rows, cols, fill_ratio=0.55):
    """Generate a random nonogram puzzle. Returns solution grid and clues."""
    # Create random solution
    solution = []
    for r in range(rows):
        row = []
        for c in range(cols):
            row.append(1 if random.random() < fill_ratio else 0)
        solution.append(row)

    # Derive row clues
    row_clues = []
    for r in range(rows):
        clues = []
        count = 0
        for c in range(cols):
            if solution[r][c] == 1:
                count += 1
            else:
                if count > 0:
                    clues.append(count)
                count = 0
        if count > 0:
            clues.append(count)
        if not clues:
            clues = [0]
        row_clues.append(clues)

    # Derive column clues
    col_clues = []
    for c in range(cols):
        clues = []
        count = 0
        for r in range(rows):
            if solution[r][c] == 1:
                count += 1
            else:
                if count > 0:
                    clues.append(count)
                count = 0
        if count > 0:
            clues.append(count)
        if not clues:
            clues = [0]
        col_clues.append(clues)

    return solution, row_clues, col_clues


def _compute_line_clues(cells):
    """Compute the run-length clues for a line of cells (FILLED=1, else 0)."""
    clues = []
    count = 0
    for cell in cells:
        if cell == FILLED:
            count += 1
        else:
            if count > 0:
                clues.append(count)
            count = 0
    if count > 0:
        clues.append(count)
    return clues if clues else [0]


class NonogramsView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.grid_rows = 10
        self.grid_cols = 10
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_status = arcade.Text(
            "", 300, bar_y, arcade.color.YELLOW,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 65, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 135, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )

        # Row clue texts (one per row)
        self.txt_row_clues = []
        for r in range(self.grid_rows):
            ox, oy = grid_origin(self.grid_cols, self.grid_rows)
            t = arcade.Text(
                "", ox - 10, 0, arcade.color.WHITE,
                font_size=11, anchor_x="right", anchor_y="center",
            )
            self.txt_row_clues.append(t)

        # Column clue texts (multiple per column for vertical display)
        max_col_clues = 6  # max clue numbers per column
        self.txt_col_clues = []
        for c in range(self.grid_cols):
            col_texts = []
            for i in range(max_col_clues):
                t = arcade.Text(
                    "", 0, 0, arcade.color.WHITE,
                    font_size=10, anchor_x="center", anchor_y="center",
                )
                col_texts.append(t)
            self.txt_col_clues.append(col_texts)

        self.txt_you_win = arcade.Text(
            "PUZZLE COMPLETE!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.YELLOW, font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_details = arcade.Text(
            "Great job!", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset game state with a new puzzle."""
        self.solution, self.row_clues, self.col_clues = _generate_puzzle(
            self.grid_rows, self.grid_cols
        )
        self.player_grid = [
            [EMPTY for _ in range(self.grid_cols)]
            for _ in range(self.grid_rows)
        ]
        self.game_state = PLAYING
        self.row_completed = [False] * self.grid_rows
        self.col_completed = [False] * self.grid_cols
        self._update_completion()

    def _update_completion(self):
        """Check which rows/columns have correct clue patterns."""
        for r in range(self.grid_rows):
            player_clues = _compute_line_clues(self.player_grid[r])
            self.row_completed[r] = (player_clues == self.row_clues[r])

        for c in range(self.grid_cols):
            col_cells = [self.player_grid[r][c] for r in range(self.grid_rows)]
            player_clues = _compute_line_clues(col_cells)
            self.col_completed[c] = (player_clues == self.col_clues[c])

    def _check_win(self):
        """Win when filled cells exactly match the solution."""
        for r in range(self.grid_rows):
            for c in range(self.grid_cols):
                is_filled = (self.player_grid[r][c] == FILLED)
                should_fill = (self.solution[r][c] == 1)
                if is_filled != should_fill:
                    return
        self.game_state = WON

    def _pixel_to_grid(self, x, y):
        """Convert pixel coordinates to grid (row, col) or None."""
        ox, oy = grid_origin(self.grid_cols, self.grid_rows)
        grid_w = self.grid_cols * CELL_SIZE
        grid_h = self.grid_rows * CELL_SIZE
        if x < ox or x > ox + grid_w or y < oy or y > oy + grid_h:
            return None
        col = int((x - ox) / CELL_SIZE)
        visual_row = int((y - oy) / CELL_SIZE)
        row = (self.grid_rows - 1) - visual_row
        if 0 <= row < self.grid_rows and 0 <= col < self.grid_cols:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_draw(self):
        self.clear()
        nonograms_renderer.draw(self)

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
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 35):
            rules_view = RulesView(
                "Nonograms", "nonograms.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        if self.game_state != PLAYING:
            return

        # Grid click
        result = self._pixel_to_grid(x, y)
        if result is None:
            return
        row, col = result

        if button == arcade.MOUSE_BUTTON_LEFT:
            # Toggle fill
            if self.player_grid[row][col] == FILLED:
                self.player_grid[row][col] = EMPTY
            else:
                self.player_grid[row][col] = FILLED
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            # Toggle X mark
            if self.player_grid[row][col] == MARKED_X:
                self.player_grid[row][col] = EMPTY
            else:
                self.player_grid[row][col] = MARKED_X

        self._update_completion()
        self._check_win()
