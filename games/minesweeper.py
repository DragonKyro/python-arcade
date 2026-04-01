import arcade
import random
from pages.rules import RulesView
from renderers import minesweeper_renderer
from renderers.minesweeper_renderer import (
    WIDTH, HEIGHT, COLS, ROWS, MINE_COUNT,
    TOP_BAR_HEIGHT, CELL_SIZE, GRID_ORIGIN_X, GRID_ORIGIN_Y,
    UNREVEALED, REVEALED, FLAGGED, PLAYING, WON, LOST,
)


class MinesweeperView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        self.txt_back = arcade.Text(
            "Back", 55, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_mines = arcade.Text(
            "", 200, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_timer = arcade.Text(
            "", 500, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 65, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 135, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        # Cell number texts - one per grid cell
        self.txt_cell_numbers = {}
        for row in range(ROWS):
            for col in range(COLS):
                cx = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE / 2
                cy = GRID_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE / 2
                t = arcade.Text(
                    "", cx, cy, arcade.color.BLACK,
                    font_size=int(CELL_SIZE * 0.5),
                    anchor_x="center", anchor_y="center", bold=True,
                )
                self.txt_cell_numbers[(row, col)] = t
        self.txt_game_over = arcade.Text(
            "GAME OVER", WIDTH / 2, HEIGHT / 2 + 10,
            arcade.color.RED, font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to try again", WIDTH / 2, HEIGHT / 2 - 30,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )
        self.txt_you_win = arcade.Text(
            "YOU WIN!", WIDTH / 2, HEIGHT / 2 + 10,
            arcade.color.YELLOW, font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_time = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 30,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset all game state."""
        # Cell data: each cell is [state, is_mine, adjacent_count]
        self.cell_states = [[UNREVEALED for _ in range(COLS)] for _ in range(ROWS)]
        self.mines = [[False for _ in range(COLS)] for _ in range(ROWS)]
        self.adjacent = [[0 for _ in range(COLS)] for _ in range(ROWS)]

        self.first_click = True
        self.game_state = PLAYING
        self.flags_placed = 0
        self.elapsed_time = 0.0
        self.timer_started = False
        self.revealed_count = 0
        self.non_mine_count = ROWS * COLS - MINE_COUNT

    def _generate_mines(self, safe_row, safe_col):
        """Place mines randomly, avoiding the clicked cell and its neighbors."""
        safe_cells = set()
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                r, c = safe_row + dr, safe_col + dc
                if 0 <= r < ROWS and 0 <= c < COLS:
                    safe_cells.add((r, c))

        all_cells = [(r, c) for r in range(ROWS) for c in range(COLS)
                     if (r, c) not in safe_cells]
        mine_cells = random.sample(all_cells, MINE_COUNT)

        for r, c in mine_cells:
            self.mines[r][c] = True

        # Calculate adjacent counts
        for r in range(ROWS):
            for c in range(COLS):
                if self.mines[r][c]:
                    self.adjacent[r][c] = -1
                    continue
                count = 0
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and self.mines[nr][nc]:
                            count += 1
                self.adjacent[r][c] = count

    def _reveal_cell(self, row, col):
        """Reveal a cell. If it has 0 adjacent mines, flood-fill reveal neighbors."""
        if (row < 0 or row >= ROWS or col < 0 or col >= COLS):
            return
        if self.cell_states[row][col] != UNREVEALED:
            return

        self.cell_states[row][col] = REVEALED
        self.revealed_count += 1

        if self.mines[row][col]:
            return

        # If zero adjacent mines, recursively reveal neighbors
        if self.adjacent[row][col] == 0:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if dr == 0 and dc == 0:
                        continue
                    self._reveal_cell(row + dr, col + dc)

    def _reveal_all_mines(self):
        """Reveal all mine cells (on game over)."""
        for r in range(ROWS):
            for c in range(COLS):
                if self.mines[r][c]:
                    self.cell_states[r][c] = REVEALED

    def _check_win(self):
        """Check if the player has won (all non-mine cells revealed)."""
        if self.revealed_count >= self.non_mine_count:
            self.game_state = WON

    def _pixel_to_grid(self, x, y):
        """Convert pixel coordinates to grid (row, col) or None if outside grid."""
        col = (x - GRID_ORIGIN_X) // CELL_SIZE
        row = (y - GRID_ORIGIN_Y) // CELL_SIZE
        if 0 <= row < ROWS and 0 <= col < COLS:
            return int(row), int(col)
        return None

    def _cell_center(self, row, col):
        """Get the pixel center of a cell."""
        cx = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE / 2
        cy = GRID_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE / 2
        return cx, cy

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        """Check if (x, y) is inside a rectangle centered at (bx, by) with size (bw, bh)."""
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_update(self, delta_time):
        if self.game_state == PLAYING and self.timer_started:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()
        minesweeper_renderer.draw(self)

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
            rules_view = RulesView("Minesweeper", "minesweeper.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # If game is over, ignore grid clicks
        if self.game_state != PLAYING:
            return

        # Grid click
        result = self._pixel_to_grid(x, y)
        if result is None:
            return
        row, col = result

        if button == arcade.MOUSE_BUTTON_LEFT:
            if self.cell_states[row][col] == FLAGGED:
                return  # Can't click on flagged cells

            if self.first_click:
                self._generate_mines(row, col)
                self.first_click = False
                self.timer_started = True

            if self.cell_states[row][col] == UNREVEALED:
                if self.mines[row][col]:
                    # Hit a mine
                    self.game_state = LOST
                    self._reveal_all_mines()
                else:
                    self._reveal_cell(row, col)
                    self._check_win()

        elif button == arcade.MOUSE_BUTTON_RIGHT:
            if self.first_click:
                return  # Don't allow flagging before first reveal
            if self.cell_states[row][col] == UNREVEALED:
                self.cell_states[row][col] = FLAGGED
                self.flags_placed += 1
            elif self.cell_states[row][col] == FLAGGED:
                self.cell_states[row][col] = UNREVEALED
                self.flags_placed -= 1
