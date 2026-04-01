"""
Rock Paper Scissors game view for Python Arcade 2.6.x.
"""

import arcade
from ai.rps_ai import RPSAI, COUNTERS

WIDTH = 800
HEIGHT = 600

# Colours
BG_COLOR = arcade.color.DARK_SLATE_GRAY
BTN_COLOR = arcade.color.DARK_CYAN
BTN_HOVER = arcade.color.CYAN
TEXT_COLOR = arcade.color.WHITE
WIN_COLOR = arcade.color.GREEN
LOSE_COLOR = arcade.color.RED
DRAW_COLOR = arcade.color.YELLOW

# Layout constants
BTN_Y = 100
BTN_W = 160
BTN_H = 120
BTN_SPACING = 200
BTN_CENTERS = [WIDTH // 2 - BTN_SPACING, WIDTH // 2, WIDTH // 2 + BTN_SPACING]

REVEAL_DELAY = 0.3  # seconds


def _determine_result(player_move: str, ai_move: str) -> str:
    """Return 'win', 'lose', or 'draw' from the player's perspective."""
    if player_move == ai_move:
        return "draw"
    if COUNTERS[ai_move] == player_move:
        # player's move beats ai's move
        return "win"
    return "lose"


class RPSView(arcade.View):
    """Rock Paper Scissors game view."""

    def __init__(self, menu_view):
        super().__init__()
        self.menu_view = menu_view
        self.ai = RPSAI()
        self._reset()

    # ------------------------------------------------------------------ state
    def _reset(self):
        self.player_wins = 0
        self.ai_wins = 0
        self.draws = 0
        self.player_history: list[str] = []
        self.round_log: list[tuple[str, str, str]] = []  # (player, ai, result)
        self._clear_round()

    def _clear_round(self):
        self.player_choice: str | None = None
        self.ai_choice: str | None = None
        self.result_text: str | None = None
        self.reveal_timer: float = 0.0
        self.waiting_for_reveal: bool = False

    # --------------------------------------------------------------- drawing
    def on_draw(self):
        arcade.start_render()
        arcade.set_background_color(BG_COLOR)

        # -- Score bar --
        arcade.draw_text(
            f"Player: {self.player_wins}   AI: {self.ai_wins}   Draws: {self.draws}",
            WIDTH // 2, HEIGHT - 30,
            TEXT_COLOR, 20, anchor_x="center",
        )

        # -- Back button (top-left) --
        arcade.draw_rectangle_filled(60, HEIGHT - 30, 100, 36, BTN_COLOR)
        arcade.draw_text("Back", 60, HEIGHT - 30, TEXT_COLOR, 14, anchor_x="center", anchor_y="center")

        # -- New Game button (top-right) --
        arcade.draw_rectangle_filled(WIDTH - 70, HEIGHT - 30, 120, 36, BTN_COLOR)
        arcade.draw_text("New Game", WIDTH - 70, HEIGHT - 30, TEXT_COLOR, 14, anchor_x="center", anchor_y="center")

        # -- Choice buttons (bottom) --
        labels = ["Rock", "Paper", "Scissors"]
        for i, (cx, label) in enumerate(zip(BTN_CENTERS, labels)):
            color = BTN_COLOR
            arcade.draw_rectangle_filled(cx, BTN_Y, BTN_W, BTN_H, color)
            arcade.draw_rectangle_outline(cx, BTN_Y, BTN_W, BTN_H, TEXT_COLOR, 2)
            # Draw simple icon
            self._draw_icon(cx, BTN_Y + 10, label.lower())
            arcade.draw_text(label, cx, BTN_Y - 45, TEXT_COLOR, 14, anchor_x="center", anchor_y="center")

        # -- Show round result area --
        if self.waiting_for_reveal:
            arcade.draw_text("Thinking...", WIDTH // 2, HEIGHT // 2, TEXT_COLOR, 28, anchor_x="center")
        elif self.player_choice and self.ai_choice:
            self._draw_result_area()

        # -- Round history (last 5) --
        self._draw_history()

    def _draw_icon(self, cx: float, cy: float, move: str, scale: float = 1.0):
        """Draw a simple shape icon for the given move."""
        if move == "rock":
            arcade.draw_circle_filled(cx, cy, 25 * scale, arcade.color.GRAY)
            arcade.draw_circle_outline(cx, cy, 25 * scale, TEXT_COLOR, 2)
        elif move == "paper":
            arcade.draw_rectangle_filled(cx, cy, 40 * scale, 50 * scale, arcade.color.GHOST_WHITE)
            arcade.draw_rectangle_outline(cx, cy, 40 * scale, 50 * scale, TEXT_COLOR, 2)
        elif move == "scissors":
            # V-shape
            length = 25 * scale
            arcade.draw_line(cx, cy + length, cx - 12 * scale, cy - length, arcade.color.SILVER, 3)
            arcade.draw_line(cx, cy + length, cx + 12 * scale, cy - length, arcade.color.SILVER, 3)
            # pivot circle
            arcade.draw_circle_filled(cx, cy + length, 4 * scale, arcade.color.SILVER)

    def _draw_result_area(self):
        """Draw both choices side by side with result text."""
        mid_y = HEIGHT // 2 + 20

        # Player choice
        arcade.draw_text("You", WIDTH // 2 - 120, mid_y + 60, TEXT_COLOR, 18, anchor_x="center")
        self._draw_icon(WIDTH // 2 - 120, mid_y, self.player_choice, scale=1.3)

        arcade.draw_text("vs", WIDTH // 2, mid_y + 20, TEXT_COLOR, 22, anchor_x="center")

        # AI choice
        arcade.draw_text("AI", WIDTH // 2 + 120, mid_y + 60, TEXT_COLOR, 18, anchor_x="center")
        self._draw_icon(WIDTH // 2 + 120, mid_y, self.ai_choice, scale=1.3)

        # Result
        if self.result_text:
            color = {
                "You Win!": WIN_COLOR,
                "You Lose!": LOSE_COLOR,
                "Draw!": DRAW_COLOR,
            }.get(self.result_text, TEXT_COLOR)
            arcade.draw_text(self.result_text, WIDTH // 2, mid_y - 60, color, 30,
                             anchor_x="center", bold=True)

    def _draw_history(self):
        """Draw the last 5 rounds in the upper-middle area."""
        start_y = HEIGHT - 70
        arcade.draw_text("Last rounds:", 20, start_y, TEXT_COLOR, 13, bold=True)
        recent = self.round_log[-5:]
        for i, (p, a, r) in enumerate(reversed(recent)):
            label = f"{p.capitalize()} vs {a.capitalize()} -> {r.upper()}"
            color = {
                "win": WIN_COLOR,
                "lose": LOSE_COLOR,
                "draw": DRAW_COLOR,
            }.get(r, TEXT_COLOR)
            arcade.draw_text(label, 20, start_y - 20 * (i + 1), color, 12)

    # --------------------------------------------------------------- update
    def on_update(self, delta_time: float):
        if self.waiting_for_reveal:
            self.reveal_timer += delta_time
            if self.reveal_timer >= REVEAL_DELAY:
                self._reveal_ai_choice()

    # --------------------------------------------------------------- input
    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        # Back button
        if 10 <= x <= 110 and HEIGHT - 48 <= y <= HEIGHT - 12:
            self.window.show_view(self.menu_view)
            return

        # New Game button
        if WIDTH - 130 <= x <= WIDTH - 10 and HEIGHT - 48 <= y <= HEIGHT - 12:
            self._reset()
            return

        # Ignore clicks while waiting for reveal
        if self.waiting_for_reveal:
            return

        # Choice buttons
        moves = ["rock", "paper", "scissors"]
        for i, cx in enumerate(BTN_CENTERS):
            if (cx - BTN_W // 2 <= x <= cx + BTN_W // 2
                    and BTN_Y - BTN_H // 2 <= y <= BTN_Y + BTN_H // 2):
                self._start_round(moves[i])
                return

    # --------------------------------------------------------------- logic
    def _start_round(self, player_move: str):
        """Player has chosen; start the reveal delay."""
        self.player_choice = player_move
        self.ai_choice = None
        self.result_text = None
        self.reveal_timer = 0.0
        self.waiting_for_reveal = True

    def _reveal_ai_choice(self):
        """Called after the delay to show the AI's move and score the round."""
        self.waiting_for_reveal = False
        self.ai_choice = self.ai.get_move(self.player_history)
        self.player_history.append(self.player_choice)

        result = _determine_result(self.player_choice, self.ai_choice)
        if result == "win":
            self.player_wins += 1
            self.result_text = "You Win!"
        elif result == "lose":
            self.ai_wins += 1
            self.result_text = "You Lose!"
        else:
            self.draws += 1
            self.result_text = "Draw!"

        self.round_log.append((self.player_choice, self.ai_choice, result))
