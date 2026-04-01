"""
Nim game view using Arcade 3.x APIs (misere variant).
"""

import arcade
from pages.components import Button
from pages.rules import RulesView
from ai.nim_ai import NimAI
from renderers.nim_renderer import (
    WIDTH, HEIGHT,
    STONE_RADIUS, STONE_SPACING, ROW_SPACING, BOARD_TOP,
    BUTTON_W, BUTTON_H, TAKE_BUTTON_W, TAKE_BUTTON_H,
)

# Starting rows (classic Nim)
STARTING_ROWS = [1, 3, 5, 7]

# Game states
STATE_PLAYER_TURN = "player_turn"
STATE_AI_THINKING = "ai_thinking"
STATE_GAME_OVER = "game_over"


class NimView(arcade.View):
    """Arcade View for the Nim game (misere variant)."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = NimAI()
        self.help_button = Button(
            WIDTH - 145, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE
        )
        self.rows = None
        self.max_rows = None
        self.state = None
        self.winner = None
        self.selected_row = -1
        self.selected_from = -1  # index from which stones are selected (to the right)
        self.ai_delay = 0.0
        self.last_ai_move = None  # (row, count) for visual feedback
        self.ai_feedback_timer = 0.0
        self._create_texts()
        self.new_game()

    def _create_texts(self):
        """Create reusable arcade.Text objects for the renderer."""
        # Button labels (static)
        self.txt_btn_back = arcade.Text(
            "Back", 60, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_btn_new_game = arcade.Text(
            "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE, 14,
            anchor_x="center", anchor_y="center",
        )

        # Title (static)
        self.txt_title = arcade.Text(
            "Nim", WIDTH // 2, HEIGHT - 30,
            arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
        )

        # Turn indicator (dynamic)
        self.txt_turn = arcade.Text(
            "", WIDTH // 2, HEIGHT - 70,
            arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        )

        # Row labels (dynamic -- content changes as stones are removed)
        self.txt_row_labels = []
        for r in range(len(STARTING_ROWS)):
            label_y = BOARD_TOP - r * ROW_SPACING
            # x will be set dynamically since it depends on max_rows
            self.txt_row_labels.append(
                arcade.Text("", 0, label_y, arcade.color.LIGHT_GRAY, 14,
                            anchor_x="center", anchor_y="center")
            )

        # Take button (dynamic)
        self.txt_take_btn = arcade.Text(
            "", WIDTH // 2, 40, arcade.color.WHITE, 16,
            anchor_x="center", anchor_y="center", bold=True,
        )

        # Game over texts
        self.txt_game_over_msg = arcade.Text(
            "", WIDTH // 2, HEIGHT // 2 + 30,
            arcade.color.WHITE, 48, anchor_x="center", anchor_y="center", bold=True,
        )
        self.txt_game_over_rule = arcade.Text(
            "The player who takes the last stone loses!",
            WIDTH // 2, HEIGHT // 2 - 20,
            arcade.color.LIGHT_GRAY, 14,
            anchor_x="center", anchor_y="center",
        )
        self.txt_game_over_hint = arcade.Text(
            "Click 'New Game' to play again",
            WIDTH // 2, HEIGHT // 2 - 50,
            arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
        )

    def new_game(self):
        """Reset the board and start a fresh game."""
        self.rows = list(STARTING_ROWS)
        self.max_rows = list(STARTING_ROWS)
        self.state = STATE_PLAYER_TURN
        self.winner = None
        self.selected_row = -1
        self.selected_from = -1
        self.ai_delay = 0.0
        self.last_ai_move = None
        self.ai_feedback_timer = 0.0

    # ------------------------------------------------------------------ helpers

    def _stone_center(self, row_idx, stone_idx):
        """Return (x, y) for the center of a stone."""
        max_stones = self.max_rows[row_idx]
        total_width = (max_stones - 1) * STONE_SPACING
        start_x = (WIDTH - total_width) / 2
        x = start_x + stone_idx * STONE_SPACING
        y = BOARD_TOP - row_idx * ROW_SPACING
        return x, y

    def _hit_stone(self, mx, my):
        """Return (row_idx, stone_idx) if click is on a live stone, else None."""
        for r, count in enumerate(self.rows):
            for s in range(count):
                cx, cy = self._stone_center(r, s)
                if (mx - cx) ** 2 + (my - cy) ** 2 <= STONE_RADIUS ** 2:
                    return (r, s)
        return None

    def _in_rect(self, x, y, cx, cy, w, h):
        """Check if (x, y) is inside a rectangle centered at (cx, cy)."""
        return cx - w / 2 <= x <= cx + w / 2 and cy - h / 2 <= y <= cy + h / 2

    def _selection_count(self):
        """Return the number of currently selected stones."""
        if self.selected_row < 0 or self.selected_from < 0:
            return 0
        return self.rows[self.selected_row] - self.selected_from

    def _check_game_over(self):
        """Check if all stones are gone. The player who just moved loses (misere)."""
        if sum(self.rows) == 0:
            return True
        return False

    # ------------------------------------------------------------------ update

    def on_update(self, delta_time):
        # AI feedback timer
        if self.last_ai_move is not None:
            self.ai_feedback_timer += delta_time
            if self.ai_feedback_timer >= 0.8:
                self.last_ai_move = None
                self.ai_feedback_timer = 0.0

        if self.state == STATE_AI_THINKING:
            self.ai_delay += delta_time
            if self.ai_delay >= 0.5:
                if sum(self.rows) == 0:
                    # No stones left — player took the last one, AI wins
                    self.winner = "ai"
                    self.state = STATE_GAME_OVER
                    return

                row_idx, count = self.ai.get_move(self.rows)
                self.rows[row_idx] -= count
                self.last_ai_move = (row_idx, count)
                self.ai_feedback_timer = 0.0

                if self._check_game_over():
                    # AI took the last stone — AI loses (misere)
                    self.winner = "player"
                    self.state = STATE_GAME_OVER
                else:
                    self.state = STATE_PLAYER_TURN

    # ------------------------------------------------------------------ draw

    def on_draw(self):
        self.clear()
        from renderers import nim_renderer
        nim_renderer.draw(self)

    # ------------------------------------------------------------------ input

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        # Back button
        if self._in_rect(x, y, 60, HEIGHT - 30, BUTTON_W, BUTTON_H):
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if self._in_rect(x, y, WIDTH - 70, HEIGHT - 30, BUTTON_W + 10, BUTTON_H):
            self.new_game()
            return

        # Help button
        if self.help_button.hit_test(x, y):
            rules_view = RulesView(
                "Nim", "nim.txt", None, self.menu_view, existing_game_view=self
            )
            self.window.show_view(rules_view)
            return

        if self.state != STATE_PLAYER_TURN:
            return

        # Take button
        if self._selection_count() > 0:
            tx, ty = WIDTH // 2, 40
            if self._in_rect(x, y, tx, ty, TAKE_BUTTON_W, TAKE_BUTTON_H):
                count = self._selection_count()
                self.rows[self.selected_row] -= count
                self.selected_row = -1
                self.selected_from = -1

                if self._check_game_over():
                    # Player took the last stone — player loses (misere)
                    self.winner = "ai"
                    self.state = STATE_GAME_OVER
                else:
                    self.state = STATE_AI_THINKING
                    self.ai_delay = 0.0
                return

        # Stone click
        hit = self._hit_stone(x, y)
        if hit is not None:
            r, s = hit
            if self.selected_row == r and self.selected_from == s:
                # Clicking the same stone again deselects
                self.selected_row = -1
                self.selected_from = -1
            else:
                # Select this stone and all stones to its right in the row
                self.selected_row = r
                self.selected_from = s
        else:
            # Clicked empty area — deselect
            self.selected_row = -1
            self.selected_from = -1
