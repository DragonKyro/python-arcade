"""
Connect Four game view using Arcade 2.6.x APIs.
"""

import arcade
from ai.connect4_ai import (
    Connect4AI,
    check_winner,
    get_valid_columns,
    get_next_open_row,
    get_winning_positions,
    ROWS,
    COLS,
    EMPTY,
    PLAYER_PIECE,
    AI_PIECE,
)

WIDTH = 800
HEIGHT = 600

# Board drawing constants
CELL_SIZE = 70
BOARD_MARGIN_X = (WIDTH - COLS * CELL_SIZE) // 2
BOARD_MARGIN_Y = 40
CIRCLE_RADIUS = 28

# Colors
BOARD_COLOR = (0, 70, 180)
EMPTY_COLOR = (20, 20, 40)
PLAYER_COLOR = arcade.color.RED
AI_COLOR = arcade.color.YELLOW
HIGHLIGHT_COLOR = (255, 255, 255, 60)
WIN_HIGHLIGHT_COLOR = (255, 255, 255, 180)
OVERLAY_BG = (0, 0, 0, 170)

# Button dimensions
BUTTON_W = 100
BUTTON_H = 36

# Game states
STATE_PLAYER_TURN = "player_turn"
STATE_AI_THINKING = "ai_thinking"
STATE_GAME_OVER = "game_over"


class Connect4View(arcade.View):
    """Arcade View for the Connect Four game."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = Connect4AI()
        self.board = None
        self.state = None
        self.winner = None
        self.winning_positions = []
        self.hover_col = -1
        self.ai_delay = 0.0
        self.new_game()

    def new_game(self):
        """Reset the board and start a fresh game."""
        self.board = [[EMPTY] * COLS for _ in range(ROWS)]
        self.state = STATE_PLAYER_TURN
        self.winner = None
        self.winning_positions = []
        self.ai_delay = 0.0

    # ------------------------------------------------------------------ helpers

    def _col_from_x(self, x):
        """Convert a screen x coordinate to a board column, or -1."""
        rel = x - BOARD_MARGIN_X
        if rel < 0 or rel >= COLS * CELL_SIZE:
            return -1
        return int(rel // CELL_SIZE)

    def _cell_center(self, row, col):
        """Return (screen_x, screen_y) for the center of a board cell.
        Row 0 is the top row in the data model but drawn at the top of the board."""
        cx = BOARD_MARGIN_X + col * CELL_SIZE + CELL_SIZE // 2
        # Row 0 (top of array) is visually at the top of the board.
        cy = BOARD_MARGIN_Y + (ROWS - 1 - row) * CELL_SIZE + CELL_SIZE // 2
        return cx, cy

    def _in_button(self, x, y, bx, by):
        """Check if (x, y) is inside a button centered at (bx, by)."""
        return (
            bx - BUTTON_W // 2 <= x <= bx + BUTTON_W // 2
            and by - BUTTON_H // 2 <= y <= by + BUTTON_H // 2
        )

    # ------------------------------------------------------------------ update

    def on_update(self, delta_time):
        if self.state == STATE_AI_THINKING:
            self.ai_delay += delta_time
            if self.ai_delay >= 0.5:
                col = self.ai.get_move(self.board, AI_PIECE, PLAYER_PIECE)
                if col is not None:
                    row = get_next_open_row(self.board, col)
                    if row != -1:
                        self.board[row][col] = AI_PIECE
                result = check_winner(self.board)
                if result is not None:
                    self.winner = result
                    self.winning_positions = get_winning_positions(self.board)
                    self.state = STATE_GAME_OVER
                else:
                    self.state = STATE_PLAYER_TURN

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        self._draw_buttons()
        self._draw_board()
        self._draw_hover()
        if self.state == STATE_GAME_OVER:
            self._draw_win_highlights()
            self._draw_overlay()

    def _draw_buttons(self):
        # Back button (top-left)
        bx, by = 60, HEIGHT - 30
        arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
        arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
        arcade.draw_text("Back", bx, by, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center")

        # New Game button (top-right)
        nx, ny = WIDTH - 70, HEIGHT - 30
        arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
        arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
        arcade.draw_text("New Game", nx, ny, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center")

        # Title
        arcade.draw_text(
            "Connect Four",
            WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center",
            bold=True,
        )

        # Turn indicator
        if self.state == STATE_PLAYER_TURN:
            msg = "Your turn (Red)"
            color = PLAYER_COLOR
        elif self.state == STATE_AI_THINKING:
            msg = "AI is thinking..."
            color = AI_COLOR
        else:
            msg = ""
            color = arcade.color.WHITE

        if msg:
            board_top = BOARD_MARGIN_Y + ROWS * CELL_SIZE
            arcade.draw_text(
                msg, WIDTH // 2, board_top + 18,
                color, 16, anchor_x="center", anchor_y="center", bold=True,
            )

    def _draw_board(self):
        # Blue board background
        bx = BOARD_MARGIN_X + (COLS * CELL_SIZE) // 2
        by = BOARD_MARGIN_Y + (ROWS * CELL_SIZE) // 2
        arcade.draw_rect_filled(arcade.XYWH(bx, by, COLS * CELL_SIZE, ROWS * CELL_SIZE), BOARD_COLOR)

        # Circles
        for row in range(ROWS):
            for col in range(COLS):
                cx, cy = self._cell_center(row, col)
                piece = self.board[row][col]
                if piece == PLAYER_PIECE:
                    color = PLAYER_COLOR
                elif piece == AI_PIECE:
                    color = AI_COLOR
                else:
                    color = EMPTY_COLOR
                arcade.draw_circle_filled(cx, cy, CIRCLE_RADIUS, color)

    def _draw_hover(self):
        """Draw a translucent highlight over the hovered column."""
        if self.state != STATE_PLAYER_TURN or self.hover_col < 0:
            return
        hx = BOARD_MARGIN_X + self.hover_col * CELL_SIZE + CELL_SIZE // 2
        hy = BOARD_MARGIN_Y + (ROWS * CELL_SIZE) // 2
        arcade.draw_rect_filled(arcade.XYWH(hx, hy, CELL_SIZE, ROWS * CELL_SIZE), HIGHLIGHT_COLOR)

        # Preview piece at top
        preview_y = BOARD_MARGIN_Y + ROWS * CELL_SIZE + 18
        arcade.draw_circle_filled(hx, preview_y + 18, CIRCLE_RADIUS // 2, PLAYER_COLOR)

    def _draw_win_highlights(self):
        """Draw white rings around the winning four pieces."""
        for row, col in self.winning_positions:
            cx, cy = self._cell_center(row, col)
            arcade.draw_circle_outline(cx, cy, CIRCLE_RADIUS + 3, arcade.color.WHITE, 4)

    def _draw_overlay(self):
        """Draw a semi-transparent overlay with the result message."""
        arcade.draw_rect_filled(arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG)

        if self.winner == PLAYER_PIECE:
            msg = "You Win!"
            color = PLAYER_COLOR
        elif self.winner == AI_PIECE:
            msg = "AI Wins!"
            color = AI_COLOR
        else:
            msg = "It's a Draw!"
            color = arcade.color.WHITE

        arcade.draw_text(
            msg, WIDTH // 2, HEIGHT // 2 + 30,
            color, 48, anchor_x="center", anchor_y="center", bold=True,
        )
        arcade.draw_text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 30,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
        )

    # ------------------------------------------------------------------ input

    def on_mouse_motion(self, x, y, dx, dy):
        self.hover_col = self._col_from_x(x)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Back button
        if self._in_button(x, y, 60, HEIGHT - 30):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._in_button(x, y, WIDTH - 70, HEIGHT - 30):
            self.new_game()
            return

        # Player move
        if self.state != STATE_PLAYER_TURN:
            return

        col = self._col_from_x(x)
        if col < 0 or col not in get_valid_columns(self.board):
            return

        row = get_next_open_row(self.board, col)
        if row == -1:
            return

        self.board[row][col] = PLAYER_PIECE

        result = check_winner(self.board)
        if result is not None:
            self.winner = result
            self.winning_positions = get_winning_positions(self.board)
            self.state = STATE_GAME_OVER
        else:
            self.state = STATE_AI_THINKING
            self.ai_delay = 0.0
