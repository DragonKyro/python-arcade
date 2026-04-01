import arcade
import random
import copy
from pages.rules import RulesView
from renderers import skyscrapers_renderer
from renderers.skyscrapers_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    CELL_SIZE, GRID_ORIGIN_X, GRID_ORIGIN_Y, CLUE_SIZE,
)

# ---------- Puzzle generation ----------

def _visible_count(line):
    """Count visible buildings from left looking right in a line of heights."""
    count = 0
    max_h = 0
    for h in line:
        if h > max_h:
            count += 1
            max_h = h
    return count


def _generate_solved_board(n):
    """Generate a valid NxN Latin square using backtracking."""
    board = [[0] * n for _ in range(n)]

    def _is_valid(r, c, val):
        for i in range(n):
            if board[r][i] == val or board[i][c] == val:
                return False
        return True

    def _solve():
        for r in range(n):
            for c in range(n):
                if board[r][c] == 0:
                    nums = list(range(1, n + 1))
                    random.shuffle(nums)
                    for num in nums:
                        if _is_valid(r, c, num):
                            board[r][c] = num
                            if _solve():
                                return True
                            board[r][c] = 0
                    return False
        return True

    _solve()
    return board


def _derive_clues(board, n):
    """Derive edge clues from a solved board.
    Returns dict with keys: top, bottom, left, right (each a list of n ints).
    """
    clues = {"top": [], "bottom": [], "left": [], "right": []}
    for c in range(n):
        col = [board[r][c] for r in range(n)]
        clues["top"].append(_visible_count(col))
        clues["bottom"].append(_visible_count(col[::-1]))
    for r in range(n):
        row = board[r]
        clues["left"].append(_visible_count(row))
        clues["right"].append(_visible_count(row[::-1]))
    return clues


def _generate_puzzle(n, difficulty="Medium"):
    """Generate a skyscrapers puzzle. Returns (clues, solution).
    Some clues are removed for difficulty.
    """
    solution = _generate_solved_board(n)
    all_clues = _derive_clues(solution, n)

    # Remove some clues based on difficulty
    remove_pct = {"Easy": 0.15, "Medium": 0.35, "Hard": 0.55}
    pct = remove_pct.get(difficulty, 0.35)

    clues = copy.deepcopy(all_clues)
    all_positions = []
    for side in ["top", "bottom", "left", "right"]:
        for i in range(n):
            all_positions.append((side, i))
    random.shuffle(all_positions)

    remove_count = int(len(all_positions) * pct)
    for side, i in all_positions[:remove_count]:
        clues[side][i] = 0  # 0 means no clue shown

    return clues, solution


# ---------- View ----------

class SkyscrapersView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.grid_size = 5
        self.difficulty = "Medium"
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
        self.txt_size_label = arcade.Text(
            "", WIDTH / 2, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        # Win overlay
        self.txt_win_title = arcade.Text(
            "Congratulations!", WIDTH / 2, HEIGHT / 2 + 30,
            arcade.color.GOLD, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_hint = arcade.Text(
            "Click New Game to play again",
            WIDTH / 2, HEIGHT / 2 - 20,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )
        # Grid cell texts (max 7x7)
        self.txt_cells = {}
        for r in range(7):
            for c in range(7):
                self.txt_cells[(r, c)] = arcade.Text(
                    "", 0, 0, arcade.color.WHITE,
                    font_size=20, anchor_x="center", anchor_y="center",
                )
        # Clue texts (max 7 per side)
        self.txt_clues = {"top": [], "bottom": [], "left": [], "right": []}
        for side in self.txt_clues:
            for i in range(7):
                self.txt_clues[side].append(arcade.Text(
                    "", 0, 0, arcade.color.LIGHT_GRAY,
                    font_size=16, anchor_x="center", anchor_y="center", bold=True,
                ))
        # Size toggle buttons
        self.txt_size_4 = arcade.Text(
            "4x4", WIDTH / 2 - 40, bar_y - 18, arcade.color.WHITE,
            font_size=10, anchor_x="center", anchor_y="center",
        )
        self.txt_size_5 = arcade.Text(
            "5x5", WIDTH / 2, bar_y - 18, arcade.color.WHITE,
            font_size=10, anchor_x="center", anchor_y="center",
        )
        self.txt_size_6 = arcade.Text(
            "6x6", WIDTH / 2 + 40, bar_y - 18, arcade.color.WHITE,
            font_size=10, anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        n = self.grid_size
        self.clues, self.solution = _generate_puzzle(n, self.difficulty)
        self.board = [[0] * n for _ in range(n)]
        self.selected = None  # (row, col) or None
        self.game_won = False
        self.elapsed_time = 0.0
        self.conflicts = [[False] * n for _ in range(n)]
        self.clue_violations = {"top": [False] * n, "bottom": [False] * n,
                                "left": [False] * n, "right": [False] * n}

    def cell_center(self, row, col):
        """Return pixel center of a grid cell. Row 0 is top row visually."""
        n = self.grid_size
        ox = GRID_ORIGIN_X + CLUE_SIZE
        oy = GRID_ORIGIN_Y + CLUE_SIZE
        x = ox + col * CELL_SIZE + CELL_SIZE / 2
        y = oy + (n - 1 - row) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def clue_center(self, side, index):
        """Return pixel center of a clue label."""
        n = self.grid_size
        ox = GRID_ORIGIN_X + CLUE_SIZE
        oy = GRID_ORIGIN_Y + CLUE_SIZE
        if side == "top":
            x = ox + index * CELL_SIZE + CELL_SIZE / 2
            y = oy + n * CELL_SIZE + CLUE_SIZE / 2
        elif side == "bottom":
            x = ox + index * CELL_SIZE + CELL_SIZE / 2
            y = GRID_ORIGIN_Y + CLUE_SIZE / 2
        elif side == "left":
            x = GRID_ORIGIN_X + CLUE_SIZE / 2
            y = oy + (n - 1 - index) * CELL_SIZE + CELL_SIZE / 2
        else:  # right
            x = ox + n * CELL_SIZE + CLUE_SIZE / 2
            y = oy + (n - 1 - index) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def _pixel_to_cell(self, px, py):
        n = self.grid_size
        ox = GRID_ORIGIN_X + CLUE_SIZE
        oy = GRID_ORIGIN_Y + CLUE_SIZE
        col = int((px - ox) / CELL_SIZE)
        row = n - 1 - int((py - oy) / CELL_SIZE)
        if 0 <= row < n and 0 <= col < n:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _update_conflicts(self):
        n = self.grid_size
        self.conflicts = [[False] * n for _ in range(n)]
        # Row/col duplicate check
        for r in range(n):
            for c in range(n):
                val = self.board[r][c]
                if val == 0:
                    continue
                for c2 in range(n):
                    if c2 != c and self.board[r][c2] == val:
                        self.conflicts[r][c] = True
                        break
                if not self.conflicts[r][c]:
                    for r2 in range(n):
                        if r2 != r and self.board[r2][c] == val:
                            self.conflicts[r][c] = True
                            break

        # Clue violation check
        self.clue_violations = {"top": [False] * n, "bottom": [False] * n,
                                "left": [False] * n, "right": [False] * n}
        # Only check complete rows/columns
        for c in range(n):
            col = [self.board[r][c] for r in range(n)]
            if 0 not in col:
                if self.clues["top"][c] > 0 and _visible_count(col) != self.clues["top"][c]:
                    self.clue_violations["top"][c] = True
                if self.clues["bottom"][c] > 0 and _visible_count(col[::-1]) != self.clues["bottom"][c]:
                    self.clue_violations["bottom"][c] = True
        for r in range(n):
            row = self.board[r]
            if 0 not in row:
                if self.clues["left"][r] > 0 and _visible_count(row) != self.clues["left"][r]:
                    self.clue_violations["left"][r] = True
                if self.clues["right"][r] > 0 and _visible_count(row[::-1]) != self.clues["right"][r]:
                    self.clue_violations["right"][r] = True

    def _check_win(self):
        n = self.grid_size
        for r in range(n):
            for c in range(n):
                if self.board[r][c] == 0 or self.conflicts[r][c]:
                    return False
        # Check all clue violations
        for side in self.clue_violations:
            if any(self.clue_violations[side]):
                return False
        self.game_won = True

    # --- arcade callbacks ---

    def on_update(self, delta_time):
        if not self.game_won:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()
        skyscrapers_renderer.draw(self)

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
            rules_view = RulesView("Skyscrapers", "skyscrapers.txt", None,
                                   self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Size toggle buttons
        for size, txt_x in [(4, WIDTH / 2 - 40), (5, WIDTH / 2), (6, WIDTH / 2 + 40)]:
            if self._hit_test_button(x, y, txt_x, bar_y - 18, 35, 20):
                if size != self.grid_size:
                    self.grid_size = size
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
        n = self.grid_size

        # Number keys 1-N
        for i in range(1, n + 1):
            if key == getattr(arcade.key, f"KEY_{i}"):
                self.board[r][c] = i
                self._update_conflicts()
                self._check_win()
                return
            if key == getattr(arcade.key, f"NUM_{i}"):
                self.board[r][c] = i
                self._update_conflicts()
                self._check_win()
                return

        if key in (arcade.key.KEY_0, arcade.key.DELETE, arcade.key.BACKSPACE, arcade.key.NUM_0):
            self.board[r][c] = 0
            self._update_conflicts()
        elif key == arcade.key.UP and r > 0:
            self.selected = (r - 1, c)
        elif key == arcade.key.DOWN and r < n - 1:
            self.selected = (r + 1, c)
        elif key == arcade.key.LEFT and c > 0:
            self.selected = (r, c - 1)
        elif key == arcade.key.RIGHT and c < n - 1:
            self.selected = (r, c + 1)
        elif key == arcade.key.ESCAPE:
            self.selected = None
