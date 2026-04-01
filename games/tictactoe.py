"""
Tic-Tac-Toe game view for Python Arcade 2.6.x.
Human plays X, AI plays O.
"""

import arcade
from ai.tictactoe_ai import TicTacToeAI, check_winner, get_winning_line
from pages.rules import RulesView
from renderers import tictactoe_renderer
from renderers.tictactoe_renderer import (
    WIDTH, HEIGHT, CELL_SIZE, GRID_SIZE, GRID_LEFT, GRID_TOP,
    BUTTON_COLOR, BUTTON_HOVER_COLOR, BUTTON_TEXT_COLOR, LINE_COLOR,
)

AI_DELAY = 0.5  # seconds before AI moves


def _screen_to_grid(sx: float, sy: float):
    """Convert screen (x, y) to grid (row, col) or None if outside grid."""
    # Convert to grid-relative pixel coords (origin top-left of grid)
    gx = sx - GRID_LEFT
    gy = (HEIGHT - sy) - GRID_TOP
    if gx < 0 or gy < 0 or gx >= GRID_SIZE or gy >= GRID_SIZE:
        return None
    col = int(gx // CELL_SIZE)
    row = int(gy // CELL_SIZE)
    if 0 <= row < 3 and 0 <= col < 3:
        return row, col
    return None


class _Button:
    """Simple rectangular button helper."""

    def __init__(self, cx, cy, w, h, label):
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.label = label
        self._txt = arcade.Text(
            label, cx, cy, BUTTON_TEXT_COLOR,
            font_size=14, anchor_x="center", anchor_y="center",
        )

    def contains(self, x, y):
        return (abs(x - self.cx) <= self.w / 2) and (abs(y - self.cy) <= self.h / 2)

    def draw(self, hover=False):
        color = BUTTON_HOVER_COLOR if hover else BUTTON_COLOR
        arcade.draw_rect_filled(arcade.XYWH(self.cx, self.cy, self.w, self.h), color)
        arcade.draw_rect_outline(arcade.XYWH(self.cx, self.cy, self.w, self.h), LINE_COLOR, 2)
        self._txt.draw()


class TicTacToeView(arcade.View):
    """Tic-Tac-Toe: Human (X) vs AI (O)."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.board = [[None] * 3 for _ in range(3)]
        self.ai = TicTacToeAI()
        self.current_turn = "X"  # X always goes first
        self.game_over = False
        self.result = None  # 'X', 'O', 'draw', or None
        self.winning_line = None  # list of (row, col) or None
        self.ai_timer = 0.0
        self.ai_thinking = False
        self.mouse_x = 0
        self.mouse_y = 0

        # Text objects for the renderer
        self._create_texts()

        # Buttons
        self.btn_back = _Button(70, HEIGHT - 30, 100, 36, "Back")
        self.btn_new = _Button(WIDTH - 80, HEIGHT - 30, 120, 36, "New Game")
        self.btn_help = _Button(WIDTH - 155, HEIGHT - 30, 40, 36, "?")
        self.btn_play_again = _Button(WIDTH // 2, HEIGHT // 2 - 60, 160, 44, "Play Again")

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        from renderers.tictactoe_renderer import LINE_COLOR, MESSAGE_COLOR
        self.txt_title = arcade.Text(
            "Tic-Tac-Toe", WIDTH // 2, HEIGHT - 30, LINE_COLOR,
            font_size=20, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_status = arcade.Text(
            "", WIDTH // 2, HEIGHT - 65, LINE_COLOR,
            font_size=15, anchor_x="center", anchor_y="center",
        )
        self.txt_overlay_msg = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 20, MESSAGE_COLOR,
            font_size=36, anchor_x="center", anchor_y="center", bold=True,
        )

    def _reset(self):
        self.board = [[None] * 3 for _ in range(3)]
        self.current_turn = "X"
        self.game_over = False
        self.result = None
        self.winning_line = None
        self.ai_timer = 0.0
        self.ai_thinking = False

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def on_update(self, delta_time: float):
        if self.game_over:
            return

        if self.ai_thinking:
            self.ai_timer += delta_time
            if self.ai_timer >= AI_DELAY:
                move = self.ai.get_move(self.board)
                if move is not None:
                    r, c = move
                    self.board[r][c] = "O"
                self.ai_thinking = False
                self.ai_timer = 0.0
                self._check_end()
                if not self.game_over:
                    self.current_turn = "X"

    def _check_end(self):
        result = check_winner(self.board)
        if result is not None:
            self.game_over = True
            self.result = result
            self.winning_line = get_winning_line(self.board)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def on_draw(self):
        self.clear()
        tictactoe_renderer.draw(self)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Back button
        if self.btn_back.contains(x, y):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self.btn_new.contains(x, y):
            self._reset()
            return

        # Help button
        if self.btn_help.contains(x, y):
            rules_view = RulesView("Tic-Tac-Toe", "tictactoe.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
            return

        # Play Again button (only visible when game over)
        if self.game_over and self.btn_play_again.contains(x, y):
            self._reset()
            return

        # Player move
        if self.game_over or self.current_turn != "X" or self.ai_thinking:
            return

        cell = _screen_to_grid(x, y)
        if cell is None:
            return
        r, c = cell
        if self.board[r][c] is not None:
            return

        self.board[r][c] = "X"
        self._check_end()
        if not self.game_over:
            self.current_turn = "O"
            self.ai_thinking = True
            self.ai_timer = 0.0
