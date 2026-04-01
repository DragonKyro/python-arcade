"""
Connect Four game view using Arcade 2.6.x APIs.
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from renderers import connect4_renderer
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
        self.help_button = Button(WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE)
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
        connect4_renderer.draw(self)

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

        # Help button
        if self.help_button.hit_test(x, y):
            rules_view = RulesView("Connect Four", "connect4.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
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
