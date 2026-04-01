import arcade
from pages.rules import RulesView
from renderers import peg_solitaire_renderer
from renderers.peg_solitaire_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, CELL_SPACING,
    BOARD_ORIGIN_X, BOARD_ORIGIN_Y, PEG_RADIUS,
    PLAYING, WON, LOST,
    UNDO_BTN_X, UNDO_BTN_Y, UNDO_BTN_W, UNDO_BTN_H,
)

# Valid board positions for English peg solitaire (cross/plus shape)
VALID_POSITIONS = set()
for r in range(7):
    for c in range(7):
        if r in (0, 1, 5, 6) and c not in (2, 3, 4):
            continue
        VALID_POSITIONS.add((r, c))


class PegSolitaireView(arcade.View):
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
        self.txt_new_game = arcade.Text(
            "New Game", WIDTH - 65, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_help = arcade.Text(
            "?", WIDTH - 135, bar_y, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )
        self.txt_moves = arcade.Text(
            "Moves: 0", WIDTH / 2, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_undo = arcade.Text(
            "Undo", UNDO_BTN_X, UNDO_BTN_Y, arcade.color.WHITE,
            font_size=13, anchor_x="center", anchor_y="center",
        )
        self.txt_you_win = arcade.Text(
            "YOU WIN!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.YELLOW, font_size=44,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_hint = arcade.Text(
            "Perfect game! Only 1 peg remaining.", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )
        self.txt_game_over = arcade.Text(
            "NO MORE MOVES", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.RED, font_size=36,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_hint = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset all game state."""
        # Board: True = peg present, False = empty hole
        self.board = {}
        for pos in VALID_POSITIONS:
            self.board[pos] = True
        # Center hole starts empty
        self.board[(3, 3)] = False

        self.selected = None          # (row, col) of selected peg or None
        self.valid_jumps = []         # list of (dest_row, dest_col, jumped_row, jumped_col)
        self.move_count = 0
        self.move_history = []        # list of (from_pos, jumped_pos, to_pos)
        self.game_state = PLAYING

    def _get_jumps_for(self, row, col):
        """Return list of valid jumps from (row, col): [(dest_r, dest_c, jumped_r, jumped_c), ...]"""
        if not self.board.get((row, col), False):
            return []
        jumps = []
        for dr, dc in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            mr, mc = row + dr // 2, col + dc // 2
            dest_r, dest_c = row + dr, col + dc
            if ((dest_r, dest_c) in VALID_POSITIONS and
                    not self.board[(dest_r, dest_c)] and
                    self.board.get((mr, mc), False)):
                jumps.append((dest_r, dest_c, mr, mc))
        return jumps

    def _any_jumps_available(self):
        """Check if any peg on the board has a valid jump."""
        for pos, has_peg in self.board.items():
            if has_peg and self._get_jumps_for(*pos):
                return True
        return False

    def _peg_count(self):
        """Count remaining pegs."""
        return sum(1 for v in self.board.values() if v)

    def _check_game_over(self):
        """Check if game is over (no moves left)."""
        if not self._any_jumps_available():
            if self._peg_count() == 1:
                self.game_state = WON
            else:
                self.game_state = LOST

    def _do_jump(self, from_pos, dest_pos, jumped_pos):
        """Execute a jump move."""
        self.board[from_pos] = False
        self.board[jumped_pos] = False
        self.board[dest_pos] = True
        self.move_count += 1
        self.move_history.append((from_pos, jumped_pos, dest_pos))
        self.selected = None
        self.valid_jumps = []
        self._check_game_over()

    def _undo(self):
        """Undo the last move."""
        if not self.move_history or self.game_state != PLAYING:
            # Also allow undo from game-over states to let player continue exploring
            if self.move_history and self.game_state in (WON, LOST):
                self.game_state = PLAYING
            else:
                return
        from_pos, jumped_pos, dest_pos = self.move_history.pop()
        self.board[dest_pos] = False
        self.board[jumped_pos] = True
        self.board[from_pos] = True
        self.move_count -= 1
        self.selected = None
        self.valid_jumps = []

    def _pixel_to_grid(self, x, y):
        """Convert pixel coordinates to grid (row, col) or None."""
        col = round((x - BOARD_ORIGIN_X) / CELL_SPACING)
        row = round((y - BOARD_ORIGIN_Y) / CELL_SPACING)
        if (row, col) in VALID_POSITIONS:
            # Check distance to center of that cell
            cx = BOARD_ORIGIN_X + col * CELL_SPACING
            cy = BOARD_ORIGIN_Y + row * CELL_SPACING
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist <= PEG_RADIUS + 5:
                return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        """Check if (x, y) is inside a rectangle centered at (bx, by) with size (bw, bh)."""
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_draw(self):
        self.clear()
        peg_solitaire_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Z:
            self._undo()

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
            rules_view = RulesView("Peg Solitaire", "peg_solitaire.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Undo button
        if self._hit_test_button(x, y, UNDO_BTN_X, UNDO_BTN_Y, UNDO_BTN_W, UNDO_BTN_H):
            self._undo()
            return

        # Ignore clicks if game is over
        if self.game_state != PLAYING:
            return

        # Board click
        result = self._pixel_to_grid(x, y)
        if result is None:
            # Clicked outside board — deselect
            self.selected = None
            self.valid_jumps = []
            return

        row, col = result

        # If a peg is selected, check if clicking a valid destination
        if self.selected is not None:
            for dest_r, dest_c, jumped_r, jumped_c in self.valid_jumps:
                if (row, col) == (dest_r, dest_c):
                    self._do_jump(self.selected, (dest_r, dest_c), (jumped_r, jumped_c))
                    return

        # Select a peg (or re-select)
        if self.board.get((row, col), False):
            jumps = self._get_jumps_for(row, col)
            if jumps:
                self.selected = (row, col)
                self.valid_jumps = jumps
            else:
                # Peg has no valid jumps — deselect
                self.selected = None
                self.valid_jumps = []
        else:
            # Clicked an empty hole — deselect
            self.selected = None
            self.valid_jumps = []
