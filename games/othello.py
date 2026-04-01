import arcade
from ai.othello_ai import OthelloAI, get_valid_moves, apply_move, check_game_over

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

        self._draw_board()
        self._draw_pieces()

        if not self.game_over and self.current_turn == BLACK:
            self._draw_hints()

        self._draw_score()
        self._draw_buttons()
        self._draw_turn_indicator()

        if self.game_over:
            self._draw_game_over()

    def _draw_board(self):
        # Green background
        arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, BOARD_PIXEL, BOARD_PIXEL), BOARD_GREEN)
        # Grid lines
        for i in range(BOARD_SIZE + 1):
            # Horizontal
            y = BOARD_BOTTOM + i * CELL_SIZE
            arcade.draw_line(BOARD_LEFT, y, BOARD_LEFT + BOARD_PIXEL, y, BOARD_LINE, 2)
            # Vertical
            x = BOARD_LEFT + i * CELL_SIZE
            arcade.draw_line(x, BOARD_BOTTOM, x, BOARD_BOTTOM + BOARD_PIXEL, BOARD_LINE, 2)

    def _draw_pieces(self):
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == EMPTY:
                    continue
                x, y = self._cell_center(r, c)
                color = BLACK_PIECE if self.board[r][c] == BLACK else WHITE_PIECE
                arcade.draw_circle_filled(x, y, PIECE_RADIUS, color)
                outline = (60, 60, 60) if self.board[r][c] == BLACK else (180, 180, 180)
                arcade.draw_circle_outline(x, y, PIECE_RADIUS, outline, 2)

    def _draw_hints(self):
        for r, c in self.player_valid_moves:
            x, y = self._cell_center(r, c)
            arcade.draw_circle_filled(x, y, HINT_RADIUS, HINT_COLOR)

    def _draw_score(self):
        b, w = self._count_pieces()
        # Black score (left side)
        arcade.draw_circle_filled(30, HEIGHT / 2 + 10, 12, BLACK_PIECE)
        arcade.draw_text(
            str(b), 30, HEIGHT / 2 - 20,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center", bold=True,
        )
        # White score (right side)
        arcade.draw_circle_filled(WIDTH - 30, HEIGHT / 2 + 10, 12, WHITE_PIECE)
        arcade.draw_text(
            str(w), WIDTH - 30, HEIGHT / 2 - 20,
            arcade.color.WHITE, font_size=18,
            anchor_x="center", anchor_y="center", bold=True,
        )

    def _draw_buttons(self):
        # Back button
        self._draw_button(60, HEIGHT - 30, 90, 36, "Back", arcade.color.DARK_SLATE_BLUE)
        # New Game button
        self._draw_button(WIDTH - 70, HEIGHT - 30, 110, 36, "New Game", arcade.color.DARK_GREEN)

    def _draw_button(self, cx, cy, w, h, text, color):
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
        arcade.draw_text(
            text, cx, cy, arcade.color.WHITE,
            font_size=14, anchor_x="center", anchor_y="center",
        )

    def _draw_turn_indicator(self):
        if self.game_over:
            return
        if self.current_turn == BLACK:
            label = "Your turn (Black)"
        else:
            label = "AI thinking..."
        arcade.draw_text(
            label, WIDTH / 2, HEIGHT - 30,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )

    def _draw_game_over(self):
        # Semi-transparent overlay
        arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 140), (0, 0, 0, 200))
        arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 140), arcade.color.WHITE, 2)

        b, w = self._count_pieces()
        if self.winner == BLACK:
            msg = "Black Wins!"
            color = arcade.color.LIGHT_GREEN
        elif self.winner == WHITE:
            msg = "White Wins!"
            color = arcade.color.LIGHT_CORAL
        else:
            msg = "It's a Tie!"
            color = arcade.color.LIGHT_BLUE

        arcade.draw_text(
            msg, WIDTH / 2, HEIGHT / 2 + 25,
            color, font_size=24,
            anchor_x="center", anchor_y="center", bold=True,
        )
        arcade.draw_text(
            f"Final Score:  Black {b}  -  White {w}",
            WIDTH / 2, HEIGHT / 2 - 5,
            arcade.color.WHITE, font_size=16,
            anchor_x="center", anchor_y="center",
        )
        arcade.draw_text(
            "Click 'New Game' to play again.",
            WIDTH / 2, HEIGHT / 2 - 35,
            arcade.color.LIGHT_GRAY, font_size=13,
            anchor_x="center", anchor_y="center",
        )

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
