"""
Go (9x9) game view using Arcade 3.x APIs.
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from renderers import go_renderer
from renderers.go_renderer import (
    WIDTH, HEIGHT,
    BOARD_SIZE, CELL_SIZE, BOARD_PIXEL, BOARD_LEFT, BOARD_BOTTOM,
    STONE_RADIUS, BUTTON_W, BUTTON_H,
    EMPTY, BLACK, WHITE,
    intersection_pos,
)
from ai.go_ai import (
    GoAI,
    apply_move,
    get_legal_moves,
    score_game,
    _board_hash,
    _get_group,
)

AI_DELAY = 0.3


class GoView(arcade.View):
    """Arcade View for the Go game."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = GoAI(difficulty="hard")
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
        self.black_captured = 0
        self.white_captured = 0
        self.prev_board_hash = None
        self.consecutive_passes = 0
        self.territory = None
        self.final_score_black = 0
        self.final_score_white = 0
        go_renderer.create_text_objects(self)
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
        self.black_captured = 0
        self.white_captured = 0
        self.prev_board_hash = None
        self.consecutive_passes = 0
        self.territory = None
        self.final_score_black = 0
        self.final_score_white = 0

    def on_show(self):
        arcade.set_background_color((40, 40, 60))

    def _pixel_to_intersection(self, px, py):
        """Convert pixel coords to nearest (row, col) intersection, or None."""
        col = round((px - BOARD_LEFT) / CELL_SIZE)
        row = (BOARD_SIZE - 1) - round((py - BOARD_BOTTOM) / CELL_SIZE)
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            ix, iy = intersection_pos(row, col)
            dist_sq = (px - ix) ** 2 + (py - iy) ** 2
            if dist_sq <= (CELL_SIZE * 0.5) ** 2:
                return row, col
        return None

    def _hit_rect(self, mx, my, cx, cy, w, h):
        return (cx - w / 2 <= mx <= cx + w / 2) and (cy - h / 2 <= my <= cy + h / 2)

    def _compute_territory(self):
        """Compute territory map for display at game end."""
        territory = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.board[r][c] != EMPTY or visited[r][c]:
                    continue
                region = []
                borders = set()
                stack = [(r, c)]
                while stack:
                    cr, cc = stack.pop()
                    if visited[cr][cc]:
                        continue
                    if self.board[cr][cc] != EMPTY:
                        borders.add(self.board[cr][cc])
                        continue
                    visited[cr][cc] = True
                    region.append((cr, cc))
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and not visited[nr][nc]:
                            stack.append((nr, nc))
                if borders == {BLACK}:
                    for rr, rc in region:
                        territory[rr][rc] = BLACK
                elif borders == {WHITE}:
                    for rr, rc in region:
                        territory[rr][rc] = WHITE

        return territory

    def _end_game(self):
        """End the game and compute final scores."""
        self.game_over = True
        self.territory = self._compute_territory()
        bs, ws = score_game(self.board, self.black_captured, self.white_captured)
        self.final_score_black = bs
        self.final_score_white = ws
        if bs > ws:
            self.winner = BLACK
        elif ws > bs:
            self.winner = WHITE
        else:
            self.winner = None

    def _player_pass(self):
        """Handle player passing."""
        self.consecutive_passes += 1
        if self.consecutive_passes >= 2:
            self._end_game()
            return
        self.current_turn = WHITE
        self.ai_thinking = True
        self.ai_timer = 0.0

    # ---- Drawing ----

    def on_draw(self):
        self.clear()
        go_renderer.draw(self)

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
                "Go", "go.txt", None,
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

        if self.game_over:
            return

        # Pass button
        if self.current_turn == BLACK and self._hit_rect(x, y, WIDTH - 70, BOARD_BOTTOM - 30, 90, 36):
            self._player_pass()
            return

        if self.current_turn != BLACK:
            return

        cell = self._pixel_to_intersection(x, y)
        if cell is None:
            return

        row, col = cell
        result = apply_move(self.board, row, col, BLACK, self.prev_board_hash)
        if result is None:
            return  # Illegal move

        new_board, captured, new_hash = result
        self.prev_board_hash = _board_hash(self.board)
        self.board = new_board
        self.white_captured += captured  # Black captured white stones
        self.last_move = (row, col)
        self.consecutive_passes = 0

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
        move = self.ai.get_move(self.board, WHITE, self.prev_board_hash)

        if move == "pass":
            self.consecutive_passes += 1
            if self.consecutive_passes >= 2:
                self._end_game()
                return
            self.current_turn = BLACK
            return

        r, c = move
        result = apply_move(self.board, r, c, WHITE, self.prev_board_hash)
        if result is None:
            # AI made illegal move, pass instead
            self.consecutive_passes += 1
            if self.consecutive_passes >= 2:
                self._end_game()
                return
            self.current_turn = BLACK
            return

        new_board, captured, new_hash = result
        self.prev_board_hash = _board_hash(self.board)
        self.board = new_board
        self.black_captured += captured  # White captured black stones
        self.last_move = (r, c)
        self.consecutive_passes = 0
        self.current_turn = BLACK


# Allow running standalone for testing
if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, "Go (9x9)")
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
    game = GoView(menu)
    window.show_view(game)
    arcade.run()
