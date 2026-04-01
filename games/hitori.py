import arcade
import random
from pages.rules import RulesView
from renderers import hitori_renderer
from renderers.hitori_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT,
    GRID_SIZE, CELL_SIZE, GRID_ORIGIN_X, GRID_ORIGIN_Y,
    NORMAL, SHADED, CONFIRMED,
    PLAYING, WON,
)


# ---------- Puzzle generator ----------

def _generate_latin_square(n):
    """Generate a random Latin square of size n."""
    # Start with a basic Latin square and shuffle
    base = [[(i + j) % n + 1 for j in range(n)] for i in range(n)]

    # Shuffle rows
    random.shuffle(base)

    # Shuffle columns
    cols = list(range(n))
    random.shuffle(cols)
    base = [[row[c] for c in cols] for row in base]

    # Shuffle number assignments
    perm = list(range(1, n + 1))
    random.shuffle(perm)
    base = [[perm[val - 1] for val in row] for row in base]

    return base


def _generate_puzzle(n):
    """Generate a Hitori puzzle.

    Strategy:
    1. Create a valid Latin square (no duplicates in rows/cols)
    2. Decide which cells to shade (ensuring shaded cells aren't adjacent
       and unshaded cells stay connected)
    3. Replace shaded cells with duplicate values to create the puzzle
    """
    latin = _generate_latin_square(n)

    # Pick cells to shade
    shaded = _pick_shaded_cells(n)

    # Create the puzzle board by introducing duplicates at shaded positions
    board = [row[:] for row in latin]
    for r, c in shaded:
        # Pick a value that already exists in this row or column (unshaded)
        row_vals = [board[r][cc] for cc in range(n) if (r, cc) not in shaded and cc != c]
        col_vals = [board[rr][c] for rr in range(n) if (rr, c) not in shaded and rr != r]
        candidates = row_vals + col_vals
        if candidates:
            board[r][c] = random.choice(candidates)
        else:
            # Rare edge case: just pick a random value
            board[r][c] = random.randint(1, n)

    return board, shaded


def _pick_shaded_cells(n):
    """Pick cells to shade ensuring no two are adjacent and remaining cells are connected."""
    max_attempts = 100
    for _ in range(max_attempts):
        shaded = set()
        cells = [(r, c) for r in range(n) for c in range(n)]
        random.shuffle(cells)
        target = random.randint(n, n + n // 2)

        for r, c in cells:
            if len(shaded) >= target:
                break
            # Check no adjacent shaded cell
            adjacent_shaded = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if (r + dr, c + dc) in shaded:
                    adjacent_shaded = True
                    break
            if adjacent_shaded:
                continue
            # Tentatively add and check connectivity
            shaded.add((r, c))
            if not _check_unshaded_connected(shaded, n):
                shaded.remove((r, c))

        if len(shaded) >= n and _check_unshaded_connected(shaded, n):
            return shaded

    # Fallback: minimal shading
    return {(0, 0), (2, 2), (4, 4)} if n >= 5 else {(0, 0), (2, 2)}


def _check_unshaded_connected(shaded, n):
    """Check that all unshaded cells form a connected group."""
    unshaded = [(r, c) for r in range(n) for c in range(n) if (r, c) not in shaded]
    if not unshaded:
        return False

    visited = set()
    queue = [unshaded[0]]
    visited.add(unshaded[0])
    unshaded_set = set(unshaded)

    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in unshaded_set and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))

    return len(visited) == len(unshaded)


# ---------- View ----------

class HitoriView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self._create_texts()
        self._init_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects."""
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

        # Cell number texts
        self.txt_cells = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
                cy = GRID_ORIGIN_Y + (GRID_SIZE - 1 - r) * CELL_SIZE + CELL_SIZE / 2
                self.txt_cells[(r, c)] = arcade.Text(
                    "", cx, cy, arcade.color.BLACK,
                    font_size=22, anchor_x="center", anchor_y="center", bold=True,
                )

        # Win overlay
        self.txt_win_title = arcade.Text(
            "Puzzle Solved!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.GOLD, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_hint = arcade.Text(
            "Click New Game to play again",
            WIDTH / 2, HEIGHT / 2 - 30,
            arcade.color.LIGHT_GRAY, font_size=14,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset game state."""
        board, self._solution_shaded = _generate_puzzle(GRID_SIZE)
        self.board = board
        self.cell_states = [[NORMAL] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.conflicts = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.selected = None
        self.game_state = PLAYING
        self.elapsed_time = 0.0
        self._update_conflicts()

    def _pixel_to_cell(self, px, py):
        """Convert pixel position to (row, col) or None."""
        col = int((px - GRID_ORIGIN_X) / CELL_SIZE)
        row = GRID_SIZE - 1 - int((py - GRID_ORIGIN_Y) / CELL_SIZE)
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _update_conflicts(self):
        """Mark cells that have duplicate unshaded values in same row/col."""
        self.conflicts = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        for r in range(GRID_SIZE):
            # Check row for duplicate unshaded values
            seen = {}
            for c in range(GRID_SIZE):
                if self.cell_states[r][c] == SHADED:
                    continue
                val = self.board[r][c]
                if val in seen:
                    self.conflicts[r][c] = True
                    self.conflicts[r][seen[val]] = True
                else:
                    seen[val] = c

        for c in range(GRID_SIZE):
            # Check column for duplicate unshaded values
            seen = {}
            for r in range(GRID_SIZE):
                if self.cell_states[r][c] == SHADED:
                    continue
                val = self.board[r][c]
                if val in seen:
                    self.conflicts[r][c] = True
                    self.conflicts[seen[val]][c] = True
                else:
                    seen[val] = r

    def _check_adjacent_shaded(self):
        """Check that no two shaded cells are orthogonally adjacent."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.cell_states[r][c] != SHADED:
                    continue
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                        if self.cell_states[nr][nc] == SHADED:
                            return False
        return True

    def _check_unshaded_connected(self):
        """Check that all unshaded cells are connected."""
        unshaded = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.cell_states[r][c] != SHADED:
                    unshaded.append((r, c))
        if not unshaded:
            return False

        visited = set()
        queue = [unshaded[0]]
        visited.add(unshaded[0])
        unshaded_set = set(unshaded)

        while queue:
            r, c = queue.pop(0)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in unshaded_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))

        return len(visited) == len(unshaded)

    def _check_no_duplicate_unshaded(self):
        """Check no row/col has duplicate unshaded values."""
        for r in range(GRID_SIZE):
            vals = []
            for c in range(GRID_SIZE):
                if self.cell_states[r][c] != SHADED:
                    vals.append(self.board[r][c])
            if len(vals) != len(set(vals)):
                return False

        for c in range(GRID_SIZE):
            vals = []
            for r in range(GRID_SIZE):
                if self.cell_states[r][c] != SHADED:
                    vals.append(self.board[r][c])
            if len(vals) != len(set(vals)):
                return False

        return True

    def _check_win(self):
        """Check all three rules for a win."""
        if (self._check_no_duplicate_unshaded() and
                self._check_adjacent_shaded() and
                self._check_unshaded_connected()):
            self.game_state = WON

    # --- arcade callbacks ---

    def on_update(self, delta_time):
        if self.game_state == PLAYING:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()
        hitori_renderer.draw(self)

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
            rules_view = RulesView("Hitori", "hitori.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_state != PLAYING:
            return

        # Grid click
        cell = self._pixel_to_cell(x, y)
        if cell is None:
            self.selected = None
            return

        r, c = cell
        self.selected = (r, c)

        if button == arcade.MOUSE_BUTTON_LEFT:
            # Toggle: normal -> shaded -> normal
            if self.cell_states[r][c] == NORMAL:
                self.cell_states[r][c] = SHADED
            elif self.cell_states[r][c] == SHADED:
                self.cell_states[r][c] = NORMAL
            elif self.cell_states[r][c] == CONFIRMED:
                self.cell_states[r][c] = SHADED

        elif button == arcade.MOUSE_BUTTON_RIGHT:
            # Toggle: normal -> confirmed -> normal
            if self.cell_states[r][c] == NORMAL:
                self.cell_states[r][c] = CONFIRMED
            elif self.cell_states[r][c] == CONFIRMED:
                self.cell_states[r][c] = NORMAL
            elif self.cell_states[r][c] == SHADED:
                self.cell_states[r][c] = CONFIRMED

        self._update_conflicts()
        self._check_win()
