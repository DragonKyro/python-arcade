import arcade
from ai.othello_ai import OthelloAI, get_valid_moves, apply_move, check_game_over
from pages.components import Button
from pages.rules import RulesView
from renderers import othello_renderer

# Window constants
WIDTH = 800
HEIGHT = 600

# Board constants
BOARD_SIZE = 8
CELL_SIZE = 55
BOARD_PIXEL = BOARD_SIZE * CELL_SIZE  # 440
BOARD_LEFT = (WIDTH - BOARD_PIXEL) / 2
BOARD_BOTTOM = (HEIGHT - BOARD_PIXEL) / 2

# Piece drawing
PIECE_RADIUS = CELL_SIZE * 0.4
HINT_RADIUS = 5

# Colors
BOARD_GREEN = (0, 128, 0)
BOARD_LINE = (0, 0, 0)
BLACK_PIECE = (20, 20, 20)
WHITE_PIECE = (240, 240, 240)
HINT_COLOR = (0, 0, 0, 100)

# Game values
EMPTY = 0
BLACK = 1
WHITE = 2

AI_DELAY = 0.5


class OthelloView(arcade.View):
    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = OthelloAI(depth=4)
        self.help_button = Button(WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE)
        self.reset_game()

    def reset_game(self):
        """Initialize or reset all game state."""
        self.board = [[EMPTY] * 8 for _ in range(8)]
        # Standard Othello starting position
        self.board[3][3] = WHITE
        self.board[3][4] = BLACK
        self.board[4][3] = BLACK
        self.board[4][4] = WHITE

        self.current_turn = BLACK  # Black (player) goes first
        self.game_over = False
        self.winner = None  # None, BLACK, WHITE, or "tie"
        self.ai_timer = 0.0
        self.ai_thinking = False
        self.player_valid_moves = get_valid_moves(self.board, BLACK)

    def on_show(self):
        arcade.set_background_color((40, 40, 60))

    def _cell_center(self, row, col):
        """Return (x, y) pixel center for a board cell. Row 0 is top."""
        x = BOARD_LEFT + col * CELL_SIZE + CELL_SIZE / 2
        y = BOARD_BOTTOM + (BOARD_SIZE - 1 - row) * CELL_SIZE + CELL_SIZE / 2
        return x, y

    def _pixel_to_cell(self, px, py):
        """Convert pixel coords to (row, col) or None if outside board."""
        col = int((px - BOARD_LEFT) / CELL_SIZE)
        row = (BOARD_SIZE - 1) - int((py - BOARD_BOTTOM) / CELL_SIZE)
        if 0 <= row < 8 and 0 <= col < 8:
            return row, col
        return None

    def _count_pieces(self):
        """Return (black_count, white_count)."""
        b = sum(cell == BLACK for row in self.board for cell in row)
        w = sum(cell == WHITE for row in self.board for cell in row)
        return b, w

    # ---- Drawing ----

    def on_draw(self):
        self.clear()
        othello_renderer.draw(self)

    # ---- Input ----

    def _hit_rect(self, mx, my, cx, cy, w, h):
        return (cx - w / 2 <= mx <= cx + w / 2) and (cy - h / 2 <= my <= cy + h / 2)

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
            rules_view = RulesView("Othello", "othello.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        if self.game_over or self.current_turn != BLACK:
            return

        cell = self._pixel_to_cell(x, y)
        if cell is None:
            return

        row, col = cell
        if (row, col) not in self.player_valid_moves:
            return

        # Player makes a move
        self.board = apply_move(self.board, row, col, BLACK)
        self._advance_turn()

    # ---- Turn management ----

    def _advance_turn(self):
        """Switch turn, handling passes and game-over."""
        if check_game_over(self.board):
            self._end_game()
            return

        # Switch to opponent
        self.current_turn = WHITE if self.current_turn == BLACK else BLACK

        moves = get_valid_moves(self.board, self.current_turn)
        if not moves:
            # Current player must pass, switch back
            self.current_turn = WHITE if self.current_turn == BLACK else BLACK
            moves = get_valid_moves(self.board, self.current_turn)
            if not moves:
                self._end_game()
                return

        if self.current_turn == BLACK:
            self.player_valid_moves = moves
        else:
            # AI's turn - start delay timer
            self.ai_thinking = True
            self.ai_timer = 0.0

    def _end_game(self):
        self.game_over = True
        b, w = self._count_pieces()
        if b > w:
            self.winner = BLACK
        elif w > b:
            self.winner = WHITE
        else:
            self.winner = "tie"

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
            self.board = apply_move(self.board, move[0], move[1], WHITE)
        self._advance_turn()


# Allow running standalone for testing
if __name__ == "__main__":
    window = arcade.Window(WIDTH, HEIGHT, "Othello")
    arcade.set_background_color((40, 40, 60))

    class DummyMenu(arcade.View):
        def on_draw(self):
            self.clear()
            arcade.draw_text("Menu (placeholder)", WIDTH / 2, HEIGHT / 2,
                             arcade.color.WHITE, 20, anchor_x="center")

    menu = DummyMenu()
    game = OthelloView(menu)
    window.show_view(game)
    arcade.run()
