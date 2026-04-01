import arcade
from pages.rules import RulesView
from renderers import nurikabe_renderer
from renderers.nurikabe_renderer import (
    WIDTH, HEIGHT, GRID_SIZE, CELL_SIZE,
    GRID_ORIGIN_X, GRID_ORIGIN_Y, TOP_BAR_HEIGHT,
)

# Cell states
UNKNOWN = 0   # unshaded
SEA = 1       # shaded (black)

# Hardcoded 7x7 puzzles: dict of (row, col) -> island_size
# 0-indexed, row 0 = top row
PUZZLES = [
    # Puzzle 1
    {
        (0, 0): 2, (0, 4): 1, (2, 2): 3,
        (4, 0): 1, (4, 6): 2, (6, 2): 3, (6, 6): 1,
    },
    # Puzzle 2
    {
        (0, 1): 3, (0, 5): 2, (1, 3): 1,
        (3, 0): 2, (3, 6): 3, (5, 3): 1,
        (6, 1): 2, (6, 5): 3,
    },
    # Puzzle 3
    {
        (0, 0): 1, (0, 3): 5, (0, 6): 1,
        (2, 1): 2, (3, 5): 3,
        (5, 0): 3, (6, 3): 2, (6, 6): 1,
    },
    # Puzzle 4
    {
        (0, 2): 2, (1, 5): 4, (2, 0): 1,
        (4, 6): 1, (5, 1): 4, (6, 4): 2,
    },
    # Puzzle 5
    {
        (0, 0): 3, (0, 6): 2, (2, 3): 1,
        (3, 1): 2, (3, 5): 2,
        (4, 3): 1, (6, 0): 2, (6, 6): 3,
    },
]


class NurikabeView(arcade.View):
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
            "Nurikabe", WIDTH / 2, bar_y, arcade.color.WHITE,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_puzzle_num = arcade.Text(
            "", WIDTH / 2, bar_y - 15, arcade.color.LIGHT_GRAY,
            font_size=10, anchor_x="center", anchor_y="center",
        )
        # Cell number texts for island clues
        self.txt_cells = {}
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cx, cy = self._cell_center(r, c)
                self.txt_cells[(r, c)] = arcade.Text(
                    "", cx, cy, arcade.color.BLACK,
                    font_size=18, anchor_x="center", anchor_y="center", bold=True,
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

    def _init_game(self):
        """Initialize or reset game state from current puzzle."""
        self.clues = PUZZLES[self.puzzle_index % len(PUZZLES)]
        self.grid = [[UNKNOWN] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.conflicts = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.game_won = False

    def _cell_center(self, row, col):
        """Return pixel center of a cell. Row 0 is top row visually."""
        x = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE / 2
        y = GRID_ORIGIN_Y + (GRID_SIZE - 1 - row) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def _pixel_to_cell(self, px, py):
        """Convert pixel coords to (row, col) or None."""
        col = int((px - GRID_ORIGIN_X) / CELL_SIZE)
        row = (GRID_SIZE - 1) - int((py - GRID_ORIGIN_Y) / CELL_SIZE)
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _flood_fill(self, r, c, value, visited):
        """Flood fill to find connected region of cells with given value."""
        if r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE:
            return []
        if (r, c) in visited:
            return []
        if self.grid[r][c] != value and not ((r, c) in self.clues and value == UNKNOWN):
            return []
        # For island flood fill: clue cells and UNKNOWN cells are island
        is_island = (self.grid[r][c] == UNKNOWN) or ((r, c) in self.clues)
        if value == UNKNOWN and not is_island:
            return []
        visited.add((r, c))
        cells = [(r, c)]
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cells.extend(self._flood_fill(r + dr, c + dc, value, visited))
        return cells

    def _get_island_cells(self, r, c, visited):
        """Get all connected non-sea cells from (r,c)."""
        if r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE:
            return []
        if (r, c) in visited:
            return []
        if self.grid[r][c] == SEA:
            return []
        visited.add((r, c))
        cells = [(r, c)]
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cells.extend(self._get_island_cells(r + dr, c + dc, visited))
        return cells

    def _get_sea_cells(self, r, c, visited):
        """Get all connected sea cells from (r,c)."""
        if r < 0 or r >= GRID_SIZE or c < 0 or c >= GRID_SIZE:
            return []
        if (r, c) in visited:
            return []
        if self.grid[r][c] != SEA:
            return []
        visited.add((r, c))
        cells = [(r, c)]
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cells.extend(self._get_sea_cells(r + dr, c + dc, visited))
        return cells

    def _update_conflicts(self):
        """Check all Nurikabe rules and mark conflicts."""
        self.conflicts = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Rule 1: Each numbered cell's island must be exactly that size
        # Rule 2: Each island contains exactly one numbered cell
        visited_island = set()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] != SEA and (r, c) not in visited_island:
                    island = self._get_island_cells(r, c, set())
                    for cell in island:
                        visited_island.add(cell)
                    # Count clues in this island
                    clue_cells = [(ir, ic) for ir, ic in island if (ir, ic) in self.clues]
                    if len(clue_cells) > 1:
                        # Multiple clues in one island - conflict
                        for ir, ic in island:
                            self.conflicts[ir][ic] = True
                    elif len(clue_cells) == 1:
                        cr, cc = clue_cells[0]
                        expected = self.clues[(cr, cc)]
                        if len(island) > expected:
                            for ir, ic in island:
                                self.conflicts[ir][ic] = True

        # Rule 3: No 2x2 sea blocks
        for r in range(GRID_SIZE - 1):
            for c in range(GRID_SIZE - 1):
                if (self.grid[r][c] == SEA and self.grid[r + 1][c] == SEA and
                        self.grid[r][c + 1] == SEA and self.grid[r + 1][c + 1] == SEA):
                    self.conflicts[r][c] = True
                    self.conflicts[r + 1][c] = True
                    self.conflicts[r][c + 1] = True
                    self.conflicts[r + 1][c + 1] = True

    def _check_win(self):
        """Check if puzzle is fully and correctly solved."""
        # Every non-clue, non-sea cell is part of an island
        # All sea cells must be connected
        # Each island has exactly one clue and correct size
        # No 2x2 sea

        # Check no conflicts
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.conflicts[r][c]:
                    return False

        # Check all sea is connected
        sea_cells = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] == SEA:
                    sea_cells.append((r, c))
        if len(sea_cells) > 0:
            connected = self._get_sea_cells(sea_cells[0][0], sea_cells[0][1], set())
            if len(connected) != len(sea_cells):
                return False

        # Check each island has exactly one clue and correct size
        visited = set()
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] != SEA and (r, c) not in visited:
                    island = self._get_island_cells(r, c, set())
                    for cell in island:
                        visited.add(cell)
                    clue_cells = [(ir, ic) for ir, ic in island if (ir, ic) in self.clues]
                    if len(clue_cells) != 1:
                        return False
                    cr, cc = clue_cells[0]
                    if len(island) != self.clues[(cr, cc)]:
                        return False

        # Must have at least one sea cell
        if len(sea_cells) == 0:
            return False

        self.game_won = True
        return True

    # --- arcade callbacks ---

    def on_draw(self):
        self.clear()
        nurikabe_renderer.draw(self)

    def on_mouse_press(self, x, y, button, modifiers):
        bar_y = HEIGHT - TOP_BAR_HEIGHT / 2

        # Back button
        if self._hit_test_button(x, y, 55, bar_y, 90, 35):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._hit_test_button(x, y, WIDTH - 65, bar_y, 110, 35):
            self.puzzle_index = (self.puzzle_index + 1) % len(PUZZLES)
            self._init_game()
            return

        # Help button
        if self._hit_test_button(x, y, WIDTH - 135, bar_y, 40, 40):
            rules_view = RulesView("Nurikabe", "nurikabe.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_won:
            return

        # Grid click - toggle cell
        cell = self._pixel_to_cell(x, y)
        if cell is not None:
            r, c = cell
            # Cannot shade clue cells
            if (r, c) in self.clues:
                return
            # Toggle
            if self.grid[r][c] == UNKNOWN:
                self.grid[r][c] = SEA
            else:
                self.grid[r][c] = UNKNOWN
            self._update_conflicts()
            self._check_win()
