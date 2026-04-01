import arcade
import random
import copy
from pages.rules import RulesView

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid constants
GRID_SIZE = 9
CELL_SIZE = 50
GRID_PX = GRID_SIZE * CELL_SIZE  # 450

# Center the grid
GRID_ORIGIN_X = (WIDTH - GRID_PX) // 2
GRID_ORIGIN_Y = (HEIGHT - 50 - GRID_PX) // 2  # offset for top bar

# Top bar
TOP_BAR_HEIGHT = 50

# Difficulty: number of cells to remove
DIFFICULTY = {
    "Easy": 35,
    "Medium": 45,
    "Hard": 55,
}

# Colors
BG_COLOR = (40, 44, 52)
GRID_BG = (255, 255, 255)
CELL_HIGHLIGHT = (200, 220, 255)
SELECTED_COLOR = (100, 149, 237)
CONFLICT_COLOR = (255, 180, 180)
GIVEN_TEXT_COLOR = (20, 20, 20)
PLAYER_TEXT_COLOR = (50, 100, 220)
CONFLICT_TEXT_COLOR = (220, 40, 40)
THIN_LINE_COLOR = (160, 160, 160)
THICK_LINE_COLOR = (20, 20, 20)
WIN_OVERLAY = (0, 0, 0, 160)


# ---------- Puzzle generator ----------

def _generate_full_board():
    """Generate a complete valid Sudoku board using backtracking with random choices."""
    board = [[0] * 9 for _ in range(9)]

    def _possible(r, c, num):
        for i in range(9):
            if board[r][i] == num or board[i][c] == num:
                return False
        br, bc = 3 * (r // 3), 3 * (c // 3)
        for i in range(br, br + 3):
            for j in range(bc, bc + 3):
                if board[i][j] == num:
                    return False
        return True

    def _solve():
        for r in range(9):
            for c in range(9):
                if board[r][c] == 0:
                    nums = list(range(1, 10))
                    random.shuffle(nums)
                    for num in nums:
                        if _possible(r, c, num):
                            board[r][c] = num
                            if _solve():
                                return True
                            board[r][c] = 0
                    return False
        return True

    _solve()
    return board


def _generate_puzzle(difficulty="Medium"):
    """Create a puzzle by generating a full board then removing cells."""
    solution = _generate_full_board()
    puzzle = copy.deepcopy(solution)
    remove_count = DIFFICULTY.get(difficulty, 45)

    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    removed = 0
    for r, c in cells:
        if removed >= remove_count:
            break
        puzzle[r][c] = 0
        removed += 1

    return puzzle, solution


# ---------- View ----------

class SudokuView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.difficulty = "Medium"
        self._init_game()

    def _init_game(self):
        """Initialize or reset all game state."""
        puzzle, solution = _generate_puzzle(self.difficulty)
        self.solution = solution
        # board holds current state (0 = empty)
        self.board = copy.deepcopy(puzzle)
        # Track which cells are given clues
        self.given = [[puzzle[r][c] != 0 for c in range(9)] for r in range(9)]
        self.selected = None  # (row, col) or None
        self.elapsed_time = 0.0
        self.game_won = False
        self.conflicts = [[False] * 9 for _ in range(9)]

    # --- helpers ---

    def _cell_center(self, row, col):
        """Return pixel center of a cell. Row 0 is top row visually."""
        x = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE / 2
        # row 0 at top: map row 0 → highest y
        y = GRID_ORIGIN_Y + (8 - row) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def _pixel_to_cell(self, px, py):
        """Convert pixel coords to (row, col) or None."""
        col = int((px - GRID_ORIGIN_X) / CELL_SIZE)
        row = 8 - int((py - GRID_ORIGIN_Y) / CELL_SIZE)
        if 0 <= row < 9 and 0 <= col < 9:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _update_conflicts(self):
        """Mark cells that conflict with another cell in same row/col/box."""
        self.conflicts = [[False] * 9 for _ in range(9)]
        for r in range(9):
            for c in range(9):
                val = self.board[r][c]
                if val == 0:
                    continue
                # Check row
                for c2 in range(9):
                    if c2 != c and self.board[r][c2] == val:
                        self.conflicts[r][c] = True
                        break
                if self.conflicts[r][c]:
                    continue
                # Check col
                for r2 in range(9):
                    if r2 != r and self.board[r2][c] == val:
                        self.conflicts[r][c] = True
                        break
                if self.conflicts[r][c]:
                    continue
                # Check box
                br, bc = 3 * (r // 3), 3 * (c // 3)
                for i in range(br, br + 3):
                    for j in range(bc, bc + 3):
                        if (i, j) != (r, c) and self.board[i][j] == val:
                            self.conflicts[r][c] = True
                            break
                    if self.conflicts[r][c]:
                        break

    def _check_win(self):
        """Check if the board is fully and correctly filled."""
        for r in range(9):
            for c in range(9):
                if self.board[r][c] == 0 or self.conflicts[r][c]:
                    return False
        self.game_won = True

    # --- arcade callbacks ---

    def on_update(self, delta_time):
        if not self.game_won:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()

        # Background
        arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR)

        # --- Top bar ---
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
        arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50))

        # Back button
        bx, by, bw, bh = 55, bar_y, 90, 35
        arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), arcade.color.DARK_SLATE_BLUE)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE)
        arcade.draw_text("Back", bx, by, arcade.color.WHITE,
                         font_size=14, anchor_x="center", anchor_y="center")

        # Timer
        mins = int(self.elapsed_time) // 60
        secs = int(self.elapsed_time) % 60
        arcade.draw_text(f"{mins:02d}:{secs:02d}", WIDTH / 2, bar_y, arcade.color.WHITE,
                         font_size=16, anchor_x="center", anchor_y="center", bold=True)

        # Difficulty label
        arcade.draw_text(self.difficulty, WIDTH / 2, bar_y - 15, arcade.color.LIGHT_GRAY,
                         font_size=10, anchor_x="center", anchor_y="center")

        # New Game button
        nx, ny, nw, nh = WIDTH - 65, bar_y, 110, 35
        arcade.draw_rect_filled(arcade.XYWH(nx, ny, nw, nh), arcade.color.DARK_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(nx, ny, nw, nh), arcade.color.WHITE)
        arcade.draw_text("New Game", nx, ny, arcade.color.WHITE,
                         font_size=14, anchor_x="center", anchor_y="center")

        # Help button
        hx, hy, hw, hh = WIDTH - 135, bar_y, 40, 40
        arcade.draw_rect_filled(arcade.XYWH(hx, hy, hw, hh), arcade.color.DARK_SLATE_BLUE)
        arcade.draw_rect_outline(arcade.XYWH(hx, hy, hw, hh), arcade.color.WHITE)
        arcade.draw_text("?", hx, hy, arcade.color.WHITE,
                         font_size=16, anchor_x="center", anchor_y="center", bold=True)

        # Difficulty buttons (small, left side under bar)
        diff_y = HEIGHT - TOP_BAR_HEIGHT - 20
        for i, diff in enumerate(["Easy", "Medium", "Hard"]):
            dx = GRID_ORIGIN_X + i * 65
            color = arcade.color.DARK_GREEN if diff == self.difficulty else (80, 80, 80)
            arcade.draw_rect_filled(arcade.XYWH(dx + 30, diff_y, 58, 22), color)
            arcade.draw_rect_outline(arcade.XYWH(dx + 30, diff_y, 58, 22), arcade.color.WHITE)
            arcade.draw_text(diff, dx + 30, diff_y, arcade.color.WHITE,
                             font_size=10, anchor_x="center", anchor_y="center")

        # --- Grid background ---
        arcade.draw_rect_filled(
            arcade.XYWH(GRID_ORIGIN_X + GRID_PX / 2, GRID_ORIGIN_Y + GRID_PX / 2, GRID_PX, GRID_PX),
            GRID_BG
        )

        # --- Cell highlights ---
        if self.selected is not None:
            sr, sc = self.selected
            sbr, sbc = 3 * (sr // 3), 3 * (sc // 3)
            for r in range(9):
                for c in range(9):
                    # Highlight row, column, and box of selected cell
                    if r == sr or c == sc or (3 * (r // 3) == sbr and 3 * (c // 3) == sbc):
                        cx, cy = self._cell_center(r, c)
                        arcade.draw_rect_filled(
                            arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                            CELL_HIGHLIGHT
                        )

            # Conflict cells
            for r in range(9):
                for c in range(9):
                    if self.conflicts[r][c]:
                        cx, cy = self._cell_center(r, c)
                        arcade.draw_rect_filled(
                            arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                            CONFLICT_COLOR
                        )

            # Selected cell bold highlight
            cx, cy = self._cell_center(sr, sc)
            arcade.draw_rect_outline(
                arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                SELECTED_COLOR, border_width=3
            )

        # --- Numbers ---
        for r in range(9):
            for c in range(9):
                val = self.board[r][c]
                if val == 0:
                    continue
                cx, cy = self._cell_center(r, c)
                if self.conflicts[r][c]:
                    color = CONFLICT_TEXT_COLOR
                elif self.given[r][c]:
                    color = GIVEN_TEXT_COLOR
                else:
                    color = PLAYER_TEXT_COLOR
                arcade.draw_text(
                    str(val), cx, cy, color,
                    font_size=20 if self.given[r][c] else 18,
                    anchor_x="center", anchor_y="center",
                    bold=self.given[r][c]
                )

        # --- Grid lines ---
        # Thin lines for each cell
        for i in range(10):
            x0 = GRID_ORIGIN_X + i * CELL_SIZE
            y0 = GRID_ORIGIN_Y
            y1 = GRID_ORIGIN_Y + GRID_PX
            lw = 3 if i % 3 == 0 else 1
            col = THICK_LINE_COLOR if i % 3 == 0 else THIN_LINE_COLOR
            arcade.draw_line(x0, y0, x0, y1, col, lw)

            y_h = GRID_ORIGIN_Y + i * CELL_SIZE
            x1 = GRID_ORIGIN_X + GRID_PX
            arcade.draw_line(GRID_ORIGIN_X, y_h, x1, y_h, col, lw)

        # --- Win overlay ---
        if self.game_won:
            arcade.draw_rect_filled(
                arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
                WIN_OVERLAY
            )
            arcade.draw_text(
                "Congratulations!", WIDTH / 2, HEIGHT / 2 + 30,
                arcade.color.GOLD, font_size=36,
                anchor_x="center", anchor_y="center", bold=True
            )
            arcade.draw_text(
                f"Completed in {mins:02d}:{secs:02d}",
                WIDTH / 2, HEIGHT / 2 - 20,
                arcade.color.WHITE, font_size=20,
                anchor_x="center", anchor_y="center"
            )
            arcade.draw_text(
                "Click New Game to play again",
                WIDTH / 2, HEIGHT / 2 - 60,
                arcade.color.LIGHT_GRAY, font_size=14,
                anchor_x="center", anchor_y="center"
            )

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
            rules_view = RulesView("Sudoku", "sudoku.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Difficulty buttons
        diff_y = HEIGHT - TOP_BAR_HEIGHT - 20
        for i, diff in enumerate(["Easy", "Medium", "Hard"]):
            dx = GRID_ORIGIN_X + i * 65 + 30
            if self._hit_test_button(x, y, dx, diff_y, 58, 22):
                if diff != self.difficulty:
                    self.difficulty = diff
                    self._init_game()
                return

        if self.game_won:
            return

        # Grid click
        cell = self._pixel_to_cell(x, y)
        if cell is not None:
            self.selected = cell

    def on_key_press(self, key, modifiers):
        if self.game_won or self.selected is None:
            return

        r, c = self.selected
        if self.given[r][c]:
            return

        # Number keys 1-9
        if arcade.key.KEY_1 <= key <= arcade.key.KEY_9:
            self.board[r][c] = key - arcade.key.KEY_0
        elif key in (arcade.key.KEY_0, arcade.key.DELETE, arcade.key.BACKSPACE):
            self.board[r][c] = 0
        # Numpad 1-9
        elif arcade.key.NUM_1 <= key <= arcade.key.NUM_9:
            self.board[r][c] = key - arcade.key.NUM_0
        elif key == arcade.key.NUM_0:
            self.board[r][c] = 0
        # Arrow keys to move selection
        elif key == arcade.key.UP and r > 0:
            self.selected = (r - 1, c)
        elif key == arcade.key.DOWN and r < 8:
            self.selected = (r + 1, c)
        elif key == arcade.key.LEFT and c > 0:
            self.selected = (r, c - 1)
        elif key == arcade.key.RIGHT and c < 8:
            self.selected = (r, c + 1)
        elif key == arcade.key.ESCAPE:
            self.selected = None
        else:
            return

        self._update_conflicts()
        self._check_win()
