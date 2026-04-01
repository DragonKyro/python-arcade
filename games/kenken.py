import arcade
from pages.rules import RulesView
from renderers import kenken_renderer
from renderers.kenken_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, CELL_SIZE,
    GRID_ORIGIN_X, GRID_ORIGIN_Y,
)

# Operations
ADD = "+"
SUB = "-"
MUL = "x"
DIV = "/"
NONE = ""  # single-cell cage (just the number)

# Puzzles: list of dicts with 'size' and 'cages'
# Each cage: (target, operation, [(r, c), ...])
PUZZLES = [
    # Puzzle 1: 4x4
    {
        "size": 4,
        "cages": [
            (2, SUB, [(0, 0), (1, 0)]),
            (3, ADD, [(0, 1), (0, 2)]),
            (1, SUB, [(0, 3), (1, 3)]),
            (12, MUL, [(1, 1), (1, 2), (2, 1)]),
            (2, NONE, [(2, 0)]),
            (3, SUB, [(2, 2), (2, 3)]),
            (2, DIV, [(3, 0), (3, 1)]),
            (7, ADD, [(3, 2), (3, 3)]),
        ],
    },
    # Puzzle 2: 4x4
    {
        "size": 4,
        "cages": [
            (6, ADD, [(0, 0), (0, 1)]),
            (2, SUB, [(0, 2), (0, 3)]),
            (8, MUL, [(1, 0), (2, 0)]),
            (1, SUB, [(1, 1), (1, 2)]),
            (3, NONE, [(1, 3)]),
            (3, SUB, [(2, 1), (3, 1)]),
            (6, ADD, [(2, 2), (2, 3)]),
            (2, DIV, [(3, 0), (3, 1)]),
            (5, ADD, [(3, 2), (3, 3)]),
        ],
    },
    # Puzzle 3: 4x4
    {
        "size": 4,
        "cages": [
            (8, MUL, [(0, 0), (0, 1)]),
            (5, ADD, [(0, 2), (1, 2)]),
            (1, NONE, [(0, 3)]),
            (2, DIV, [(1, 0), (1, 1)]),
            (3, SUB, [(1, 3), (2, 3)]),
            (11, ADD, [(2, 0), (3, 0), (3, 1)]),
            (3, SUB, [(2, 1), (2, 2)]),
            (2, DIV, [(3, 2), (3, 3)]),
        ],
    },
    # Puzzle 4: 6x6
    {
        "size": 6,
        "cages": [
            (11, ADD, [(0, 0), (1, 0)]),
            (2, DIV, [(0, 1), (0, 2)]),
            (20, MUL, [(0, 3), (1, 3)]),
            (6, MUL, [(0, 4), (0, 5), (1, 5)]),
            (3, SUB, [(1, 1), (1, 2)]),
            (3, DIV, [(1, 4), (2, 4)]),
            (240, MUL, [(2, 0), (2, 1), (3, 0), (3, 1)]),
            (6, MUL, [(2, 2), (2, 3)]),
            (6, ADD, [(2, 5), (3, 5)]),
            (7, ADD, [(3, 2), (4, 2)]),
            (30, MUL, [(3, 3), (3, 4)]),
            (6, MUL, [(4, 0), (4, 1)]),
            (9, ADD, [(4, 3), (4, 4), (4, 5)]),
            (8, ADD, [(5, 0), (5, 1)]),
            (2, DIV, [(5, 2), (5, 3)]),
            (5, SUB, [(5, 4), (5, 5)]),
        ],
    },
    # Puzzle 5: 6x6
    {
        "size": 6,
        "cages": [
            (5, SUB, [(0, 0), (1, 0)]),
            (3, DIV, [(0, 1), (0, 2)]),
            (15, ADD, [(0, 3), (0, 4), (0, 5)]),
            (12, MUL, [(1, 1), (1, 2)]),
            (1, SUB, [(1, 3), (1, 4)]),
            (4, NONE, [(1, 5)]),
            (5, ADD, [(2, 0), (2, 1)]),
            (2, SUB, [(2, 2), (3, 2)]),
            (18, MUL, [(2, 3), (2, 4)]),
            (5, ADD, [(2, 5), (3, 5)]),
            (11, ADD, [(3, 0), (3, 1)]),
            (15, MUL, [(3, 3), (3, 4)]),
            (3, SUB, [(4, 0), (5, 0)]),
            (30, MUL, [(4, 1), (4, 2), (5, 1)]),
            (1, SUB, [(4, 3), (4, 4)]),
            (5, ADD, [(4, 5), (5, 5)]),
            (9, ADD, [(5, 2), (5, 3)]),
            (2, DIV, [(5, 4), (5, 5)]),
        ],
    },
]


class KenKenView(arcade.View):
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
            "KenKen", WIDTH / 2, bar_y, arcade.color.WHITE,
            font_size=16, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_puzzle_num = arcade.Text(
            "", WIDTH / 2, bar_y - 15, arcade.color.LIGHT_GRAY,
            font_size=10, anchor_x="center", anchor_y="center",
        )
        # Cell value texts (max 6x6)
        self.txt_cells = {}
        for r in range(6):
            for c in range(6):
                self.txt_cells[(r, c)] = arcade.Text(
                    "", 0, 0, arcade.color.BLACK,
                    font_size=20, anchor_x="center", anchor_y="center",
                )
        # Cage label texts (one per cage, max ~20 cages)
        self.txt_cage_labels = []
        for i in range(25):
            self.txt_cage_labels.append(arcade.Text(
                "", 0, 0, (80, 80, 80),
                font_size=10, anchor_x="left", anchor_y="top",
            ))
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
        """Initialize or reset game state."""
        puzzle = PUZZLES[self.puzzle_index % len(PUZZLES)]
        self.size = puzzle["size"]
        self.cages = puzzle["cages"]
        self.values = [[0] * self.size for _ in range(self.size)]
        self.selected = None
        self.conflicts = [[False] * self.size for _ in range(self.size)]
        self.game_won = False
        # Build cell-to-cage map
        self.cell_cage = {}
        for i, (target, op, cells) in enumerate(self.cages):
            for rc in cells:
                self.cell_cage[rc] = i

    def _cell_center(self, row, col):
        """Return pixel center of a cell."""
        # Compute dynamic origin based on grid size
        grid_px = self.size * CELL_SIZE
        ox = (WIDTH - grid_px) // 2
        oy = (HEIGHT - TOP_BAR_HEIGHT - grid_px) // 2
        x = ox + col * CELL_SIZE + CELL_SIZE / 2
        y = oy + (self.size - 1 - row) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def _grid_origin(self):
        """Get dynamic grid origin."""
        grid_px = self.size * CELL_SIZE
        ox = (WIDTH - grid_px) // 2
        oy = (HEIGHT - TOP_BAR_HEIGHT - grid_px) // 2
        return ox, oy

    def _pixel_to_cell(self, px, py):
        """Convert pixel coords to (row, col) or None."""
        ox, oy = self._grid_origin()
        col = int((px - ox) / CELL_SIZE)
        row = (self.size - 1) - int((py - oy) / CELL_SIZE)
        if 0 <= row < self.size and 0 <= col < self.size:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def _evaluate_cage(self, target, op, cells):
        """Check if cage cells produce the target with given operation.
        Returns True if valid, False if invalid, None if incomplete."""
        vals = [self.values[r][c] for r, c in cells]
        if 0 in vals:
            return None  # incomplete

        if op == NONE:
            return vals[0] == target
        elif op == ADD:
            return sum(vals) == target
        elif op == MUL:
            product = 1
            for v in vals:
                product *= v
            return product == target
        elif op == SUB:
            # For 2-cell cages, either order
            if len(vals) == 2:
                return abs(vals[0] - vals[1]) == target
            return False
        elif op == DIV:
            if len(vals) == 2:
                a, b = max(vals), min(vals)
                return b != 0 and a / b == target
            return False
        return False

    def _update_conflicts(self):
        """Check row/col uniqueness and cage constraints."""
        self.conflicts = [[False] * self.size for _ in range(self.size)]

        # Row uniqueness
        for r in range(self.size):
            for c in range(self.size):
                v = self.values[r][c]
                if v == 0:
                    continue
                for c2 in range(self.size):
                    if c2 != c and self.values[r][c2] == v:
                        self.conflicts[r][c] = True
                        self.conflicts[r][c2] = True

        # Column uniqueness
        for c in range(self.size):
            for r in range(self.size):
                v = self.values[r][c]
                if v == 0:
                    continue
                for r2 in range(self.size):
                    if r2 != r and self.values[r2][c] == v:
                        self.conflicts[r][c] = True
                        self.conflicts[r2][c] = True

        # Cage constraints
        for target, op, cells in self.cages:
            result = self._evaluate_cage(target, op, cells)
            if result is False:
                for r, c in cells:
                    if self.values[r][c] != 0:
                        self.conflicts[r][c] = True

    def _check_win(self):
        """Check if all cells filled with no conflicts."""
        for r in range(self.size):
            for c in range(self.size):
                if self.values[r][c] == 0 or self.conflicts[r][c]:
                    return False
        self.game_won = True
        return True

    # --- arcade callbacks ---

    def on_draw(self):
        self.clear()
        kenken_renderer.draw(self)

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
            rules_view = RulesView("KenKen", "kenken.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_won:
            return

        cell = self._pixel_to_cell(x, y)
        if cell is not None:
            self.selected = cell

    def on_key_press(self, key, modifiers):
        if self.game_won or self.selected is None:
            return

        r, c = self.selected
        max_digit = self.size

        if arcade.key.KEY_1 <= key <= arcade.key.KEY_0 + max_digit:
            self.values[r][c] = key - arcade.key.KEY_0
        elif arcade.key.NUM_1 <= key <= arcade.key.NUM_0 + max_digit:
            self.values[r][c] = key - arcade.key.NUM_0
        elif key in (arcade.key.KEY_0, arcade.key.DELETE, arcade.key.BACKSPACE):
            self.values[r][c] = 0
        elif key == arcade.key.UP and r > 0:
            self.selected = (r - 1, c)
            return
        elif key == arcade.key.DOWN and r < self.size - 1:
            self.selected = (r + 1, c)
            return
        elif key == arcade.key.LEFT and c > 0:
            self.selected = (r, c - 1)
            return
        elif key == arcade.key.RIGHT and c < self.size - 1:
            self.selected = (r, c + 1)
            return
        elif key == arcade.key.ESCAPE:
            self.selected = None
            return
        else:
            return

        self._update_conflicts()
        self._check_win()
