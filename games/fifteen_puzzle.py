import arcade
import random
from pages.rules import RulesView
from renderers import fifteen_puzzle_renderer
from renderers.fifteen_puzzle_renderer import (
    WIDTH, HEIGHT, GRID_SIZE, CELL_SIZE, GAP,
    TOP_BAR_HEIGHT, GRID_ORIGIN_X, GRID_ORIGIN_Y,
    GRID_WIDTH, GRID_HEIGHT, PLAYING, WON,
    cell_center,
)


class FifteenPuzzleView(arcade.View):
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
        self.txt_moves = arcade.Text(
            "", 200, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_timer = arcade.Text(
            "", 420, bar_y, arcade.color.YELLOW,
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

        # Tile number texts — one per grid cell
        self.txt_tile_numbers = {}
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cx, cy = cell_center(row, col)
                t = arcade.Text(
                    "", cx, cy, arcade.color.WHITE,
                    font_size=36, anchor_x="center", anchor_y="center",
                    bold=True,
                )
                self.txt_tile_numbers[(row, col)] = t

        self.txt_you_win = arcade.Text(
            "YOU WIN!", WIDTH / 2, HEIGHT / 2 + 20,
            arcade.color.YELLOW, font_size=44,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_details = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 25,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset all game state."""
        # Build solved board: 1..15, 0 in bottom-right
        self.board = [
            [(row * GRID_SIZE + col + 1) % (GRID_SIZE * GRID_SIZE)
             for col in range(GRID_SIZE)]
            for row in range(GRID_SIZE)
        ]
        # board[0] = [1,2,3,4], ..., board[3] = [13,14,15,0]
        self.empty_row = GRID_SIZE - 1
        self.empty_col = GRID_SIZE - 1

        self._shuffle()

        self.move_count = 0
        self.elapsed_time = 0.0
        self.timer_started = False
        self.game_state = PLAYING

    def _shuffle(self, num_moves=200):
        """Shuffle by making random valid moves from the solved state."""
        last_move = None
        opposites = {(1, 0): (-1, 0), (-1, 0): (1, 0),
                     (0, 1): (0, -1), (0, -1): (0, 1)}
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for _ in range(num_moves):
            valid = []
            for dr, dc in directions:
                nr, nc = self.empty_row + dr, self.empty_col + dc
                if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                    # Avoid immediately undoing the last move
                    if last_move and (dr, dc) == opposites[last_move]:
                        continue
                    valid.append((dr, dc))
            dr, dc = random.choice(valid)
            nr, nc = self.empty_row + dr, self.empty_col + dc
            self.board[self.empty_row][self.empty_col] = self.board[nr][nc]
            self.board[nr][nc] = 0
            self.empty_row, self.empty_col = nr, nc
            last_move = (dr, dc)

    def _try_move(self, tile_row, tile_col):
        """Try to slide the tile at (tile_row, tile_col) into the empty space."""
        if (tile_row < 0 or tile_row >= GRID_SIZE or
                tile_col < 0 or tile_col >= GRID_SIZE):
            return False

        # Tile must be adjacent to the empty space
        dr = abs(tile_row - self.empty_row)
        dc = abs(tile_col - self.empty_col)
        if not ((dr == 1 and dc == 0) or (dr == 0 and dc == 1)):
            return False

        # Swap
        self.board[self.empty_row][self.empty_col] = self.board[tile_row][tile_col]
        self.board[tile_row][tile_col] = 0
        self.empty_row, self.empty_col = tile_row, tile_col

        if not self.timer_started:
            self.timer_started = True
        self.move_count += 1
        self._check_win()
        return True

    def _check_win(self):
        """Check if tiles 1-15 are in order with empty in bottom-right."""
        expected = 1
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if row == GRID_SIZE - 1 and col == GRID_SIZE - 1:
                    if self.board[row][col] != 0:
                        return
                else:
                    if self.board[row][col] != expected:
                        return
                    expected += 1
        self.game_state = WON

    def _pixel_to_grid(self, x, y):
        """Convert pixel coordinates to grid (row, col) or None if outside grid."""
        # Invert the cell_center mapping
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cx, cy = cell_center(row, col)
                half = CELL_SIZE / 2
                if cx - half <= x <= cx + half and cy - half <= y <= cy + half:
                    return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        """Check if (x, y) is inside a rectangle centered at (bx, by) with size (bw, bh)."""
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_update(self, delta_time):
        if self.game_state == PLAYING and self.timer_started:
            self.elapsed_time += delta_time

    def on_draw(self):
        self.clear()
        fifteen_puzzle_renderer.draw(self)

    def on_key_press(self, key, modifiers):
        if self.game_state != PLAYING:
            return

        # Arrow keys: move the tile that is in the direction relative to the empty space
        # Up arrow -> slide tile below empty space upward
        if key == arcade.key.UP:
            self._try_move(self.empty_row + 1, self.empty_col)
        elif key == arcade.key.DOWN:
            self._try_move(self.empty_row - 1, self.empty_col)
        elif key == arcade.key.LEFT:
            self._try_move(self.empty_row, self.empty_col + 1)
        elif key == arcade.key.RIGHT:
            self._try_move(self.empty_row, self.empty_col - 1)

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
                "15 Puzzle", "fifteen_puzzle.txt", None,
                self.menu_view, existing_game_view=self,
            )
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
        self._try_move(row, col)
