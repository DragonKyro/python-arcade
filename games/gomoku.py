"""
Gomoku (Five in a Row) game view using Arcade 3.x APIs.
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from renderers import gomoku_renderer
from renderers.gomoku_renderer import (
    WIDTH, HEIGHT,
    BOARD_SIZE, CELL_SIZE, BOARD_PIXEL, BOARD_LEFT, BOARD_BOTTOM,
    STONE_RADIUS, BUTTON_W, BUTTON_H,
    EMPTY, BLACK, WHITE,
    intersection_pos,
)
from ai.gomoku_ai import (
    GomokuAI,
    get_legal_moves,
    check_winner,
    is_board_full,
)

AI_DELAY = 0.3


class GomokuView(arcade.View):
    """Arcade View for the Gomoku game."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = GomokuAI(difficulty="hard")
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?",
            color=arcade.color.DARK_SLATE_BLUE,
        )
        self.board = None
        self.current_turn = BLACK
        self.game_over = False
        self.winner = None
        self.last_move = None
        self.ai_timer = 0.0
        self.ai_thinking = False
        self.phase = "difficulty"  # "difficulty" | "playing"
        gomoku_renderer.create_text_objects(self)
        self.reset_game()

    def reset_game(self):
        """Initialize or reset all game state."""
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_turn = BLACK
        self.game_over = False
        self.winner = None
        self.last_move = None
        self.ai_timer = 0.0
        self.ai_thinking = False
        self.phase = "difficulty"

    def on_show(self):
        arcade.set_background_color((40, 40, 60))

    def _pixel_to_intersection(self, px, py):
        """Convert pixel coords to nearest (row, col) intersection, or None."""
        col = round((px - BOARD_LEFT) / CELL_SIZE)
        row = (BOARD_SIZE - 1) - round((py - BOARD_BOTTOM) / CELL_SIZE)
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            # Check if click is close enough to the intersection
            ix, iy = intersection_pos(row, col)
            dist_sq = (px - ix) ** 2 + (py - iy) ** 2
            if dist_sq <= (CELL_SIZE * 0.5) ** 2:
                return row, col
        return None

    def _hit_rect(self, mx, my, cx, cy, w, h):
        return (cx - w / 2 <= mx <= cx + w / 2) and (cy - h / 2 <= my <= cy + h / 2)

    # ---- Drawing ----

    def on_draw(self):
        self.clear()
        gomoku_renderer.draw(self)

    # ---- Input ----

    def on_mouse_press(self, x, y, button, modifiers):
        # Back button
        if self._hit_rect(x, y, 60, HEIGHT - 30, 90, 36):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._hit_rect(x, y, WIDTH - 70, HEIGHT - 30, 110, 36):
            self.reset_game()
            return

        # Help button
        if self.help_button.hit_test(x, y):
            rules_view = RulesView(
                "Gomoku", "gomoku.txt", None,
                self.menu_view, existing_game_view=self,
            )
            self.window.show_view(rules_view)
            return

        # Difficulty selection
        if self.phase == "difficulty":
            if self._hit_rect(x, y, WIDTH / 2 - 150, HEIGHT / 2, 100, 40):
                self.ai.set_difficulty("easy")
                self.phase = "playing"
                return
            if self._hit_rect(x, y, WIDTH / 2, HEIGHT / 2, 100, 40):
                self.ai.set_difficulty("medium")
                self.phase = "playing"
                return
            if self._hit_rect(x, y, WIDTH / 2 + 150, HEIGHT / 2, 100, 40):
                self.ai.set_difficulty("hard")
                self.phase = "playing"
                return
            return

        if self.game_over or self.current_turn != BLACK:
            return

        cell = self._pixel_to_intersection(x, y)
        if cell is None:
            return

        row, col = cell
        if self.board[row][col] != EMPTY:
            return

        # Player places a stone
        self.board[row][col] = BLACK
        self.last_move = (row, col)

        winner = check_winner(self.board)
        if winner is not None:
            self.game_over = True
            self.winner = winner
            return

        if is_board_full(self.board):
            self.game_over = True
            self.winner = None
            return

        # Switch to AI
        self.current_turn = WHITE
        self.ai_thinking = True
        self.ai_timer = 0.0

    # ---- Update (AI delay) ----

    def on_update(self, delta_time):
        if not self.ai_thinking:
            return

        self.ai_timer += delta_time
        if self.ai_timer < AI_DELAY:
            return

        self.ai_thinking = False
        move = self.ai.get_move(self.board, WHITE)
        if move is not None:
            r, c = move
            self.board[r][c] = WHITE
            self.last_move = (r, c)

        winner = check_winner(self.board)
        if winner is not None:
            self.game_over = True
            self.winner = winner
            return

        if is_board_full(self.board):
            self.game_over = True
            self.winner = None
            return

        self.current_turn = BLACK


# Allow running standalone for testing
if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, "Gomoku")
    arcade.set_background_color((40, 40, 60))

    class DummyMenu(arcade.View):
        def __init__(self):
            super().__init__()
            self.txt = arcade.Text(
                "Menu (placeholder)", WIDTH / 2, HEIGHT / 2,
                arcade.color.WHITE, 20, anchor_x="center",
            )

        def on_draw(self):
            self.clear()
            self.txt.draw()

    menu = DummyMenu()
    game = GomokuView(menu)
    window.show_view(game)
    arcade.run()
