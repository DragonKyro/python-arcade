import arcade
import random
from pages.rules import RulesView
from renderers import lights_out_renderer
from renderers.lights_out_renderer import (
    WIDTH, HEIGHT, TOP_BAR_HEIGHT, CELL_SIZE,
    GRID_ORIGIN_X, GRID_ORIGIN_Y,
    PLAYING, WON,
)


class LightsOutView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.grid_size = 5
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
            "", WIDTH / 2, bar_y, arcade.color.YELLOW,
            font_size=16, anchor_x="center", anchor_y="center",
        )
        self.txt_you_win = arcade.Text(
            "YOU WIN!", WIDTH / 2, HEIGHT / 2 + 10,
            arcade.color.YELLOW, font_size=40,
            anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_win_moves = arcade.Text(
            "", WIDTH / 2, HEIGHT / 2 - 30,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _init_game(self):
        """Initialize or reset game state with a random solvable puzzle."""
        n = self.grid_size
        # Start with all lights off (solved state), apply random toggles
        self.grid = [[False] * n for _ in range(n)]
        self.game_state = PLAYING
        self.moves = 0

        # Apply random clicks to create a solvable puzzle
        num_clicks = random.randint(n, n * n)
        for _ in range(num_clicks):
            r = random.randint(0, n - 1)
            c = random.randint(0, n - 1)
            self._toggle(r, c, count_move=False)

        # Ensure at least some lights are on
        if all(not self.grid[r][c] for r in range(n) for c in range(n)):
            r = random.randint(0, n - 1)
            c = random.randint(0, n - 1)
            self._toggle(r, c, count_move=False)

    def _toggle(self, row, col, count_move=True):
        """Toggle the clicked cell and its 4 orthogonal neighbors."""
        n = self.grid_size
        for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < n and 0 <= nc < n:
                self.grid[nr][nc] = not self.grid[nr][nc]
        if count_move:
            self.moves += 1

    def _check_win(self):
        """Check if all lights are off."""
        n = self.grid_size
        if all(not self.grid[r][c] for r in range(n) for c in range(n)):
            self.game_state = WON

    def _get_grid_origin(self):
        """Calculate grid origin for current grid size."""
        n = self.grid_size
        grid_w = n * CELL_SIZE
        grid_h = n * CELL_SIZE
        ox = (WIDTH - grid_w) // 2
        oy = (HEIGHT - TOP_BAR_HEIGHT - grid_h) // 2
        return ox, oy

    def _pixel_to_grid(self, x, y):
        """Convert pixel coordinates to grid (row, col) or None."""
        ox, oy = self._get_grid_origin()
        n = self.grid_size
        col = int((x - ox) // CELL_SIZE)
        row = int((y - oy) // CELL_SIZE)
        if 0 <= row < n and 0 <= col < n:
            return row, col
        return None

    def _hit_test_button(self, x, y, bx, by, bw, bh):
        return (bx - bw / 2 <= x <= bx + bw / 2 and
                by - bh / 2 <= y <= by + bh / 2)

    def on_draw(self):
        self.clear()
        lights_out_renderer.draw(self)

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
            rules_view = RulesView("Lights Out", "lights_out.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_state != PLAYING:
            return

        result = self._pixel_to_grid(x, y)
        if result is None:
            return
        row, col = result
        self._toggle(row, col)
        self._check_win()
