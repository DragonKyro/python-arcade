"""
Rock Paper Scissors game view for Python Arcade 2.6.x.
"""

import arcade
from ai.rps_ai import RPSAI, COUNTERS
from pages.components import Button
from pages.rules import RulesView
from renderers import rps_renderer

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
        self.help_button = Button(WIDTH - 155, HEIGHT - 30, 40, 36, "?", color=arcade.color.DARK_SLATE_BLUE)
        self._reset()

    # ------------------------------------------------------------------ state
    def _reset(self):
        self.player_wins = 0
        self.ai_wins = 0
        self.draws = 0
        self.player_history = []
        self.round_log = []  # (player, ai, result)
        self._clear_round()

    def _clear_round(self):
        self.player_choice = None
        self.ai_choice = None
        self.result_text = None
        self.reveal_timer: float = 0.0
        self.waiting_for_reveal: bool = False

    # --------------------------------------------------------------- drawing
    def on_draw(self):
        self.clear()
        rps_renderer.draw(self)

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

        # Help button
        if self.help_button.hit_test(x, y):
            rules_view = RulesView("Rock Paper Scissors", "rps.txt", None, self.menu_view, existing_game_view=self)
            self.window.show_view(rules_view)
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
