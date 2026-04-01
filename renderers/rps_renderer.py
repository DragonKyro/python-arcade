"""
Renderer for Rock Paper Scissors game.
All arcade.draw_* calls for the RPS game live here.
"""

import arcade

# Import layout/color constants from the game module
from games.rps import (
    WIDTH, HEIGHT,
    BG_COLOR, BTN_COLOR, BTN_HOVER, TEXT_COLOR,
    WIN_COLOR, LOSE_COLOR, DRAW_COLOR,
    BTN_Y, BTN_W, BTN_H, BTN_SPACING, BTN_CENTERS,
)


def draw(game):
    """Render the entire RPS game state."""
    arcade.set_background_color(BG_COLOR)

    # -- Score bar --
    arcade.draw_text(
        f"Player: {game.player_wins}   AI: {game.ai_wins}   Draws: {game.draws}",
        WIDTH // 2, HEIGHT - 30,
        TEXT_COLOR, 20, anchor_x="center",
    )

    # -- Back button (top-left) --
    arcade.draw_rect_filled(arcade.XYWH(60, HEIGHT - 30, 100, 36), BTN_COLOR)
    arcade.draw_text("Back", 60, HEIGHT - 30, TEXT_COLOR, 14, anchor_x="center", anchor_y="center")

    # -- New Game button (top-right) --
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 70, HEIGHT - 30, 120, 36), BTN_COLOR)
    arcade.draw_text("New Game", WIDTH - 70, HEIGHT - 30, TEXT_COLOR, 14, anchor_x="center", anchor_y="center")

    # -- Help button --
    game.help_button.draw()

    # -- Choice buttons (bottom) --
    labels = ["Rock", "Paper", "Scissors"]
    for i, (cx, label) in enumerate(zip(BTN_CENTERS, labels)):
        color = BTN_COLOR
        arcade.draw_rect_filled(arcade.XYWH(cx, BTN_Y, BTN_W, BTN_H), color)
        arcade.draw_rect_outline(arcade.XYWH(cx, BTN_Y, BTN_W, BTN_H), TEXT_COLOR, 2)
        # Draw simple icon
        _draw_icon(cx, BTN_Y + 10, label.lower())
        arcade.draw_text(label, cx, BTN_Y - 45, TEXT_COLOR, 14, anchor_x="center", anchor_y="center")

    # -- Show round result area --
    if game.waiting_for_reveal:
        arcade.draw_text("Thinking...", WIDTH // 2, HEIGHT // 2, TEXT_COLOR, 28, anchor_x="center")
    elif game.player_choice and game.ai_choice:
        _draw_result_area(game)

    # -- Round history (last 5) --
    _draw_history(game)


def _draw_icon(cx: float, cy: float, move: str, scale: float = 1.0):
    """Draw a simple shape icon for the given move."""
    if move == "rock":
        arcade.draw_circle_filled(cx, cy, 25 * scale, arcade.color.GRAY)
        arcade.draw_circle_outline(cx, cy, 25 * scale, TEXT_COLOR, 2)
    elif move == "paper":
        arcade.draw_rect_filled(arcade.XYWH(cx, cy, 40 * scale, 50 * scale), arcade.color.GHOST_WHITE)
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, 40 * scale, 50 * scale), TEXT_COLOR, 2)
    elif move == "scissors":
        # V-shape
        length = 25 * scale
        arcade.draw_line(cx, cy + length, cx - 12 * scale, cy - length, arcade.color.SILVER, 3)
        arcade.draw_line(cx, cy + length, cx + 12 * scale, cy - length, arcade.color.SILVER, 3)
        # pivot circle
        arcade.draw_circle_filled(cx, cy + length, 4 * scale, arcade.color.SILVER)


def _draw_result_area(game):
    """Draw both choices side by side with result text."""
    mid_y = HEIGHT // 2 + 20

    # Player choice
    arcade.draw_text("You", WIDTH // 2 - 120, mid_y + 60, TEXT_COLOR, 18, anchor_x="center")
    _draw_icon(WIDTH // 2 - 120, mid_y, game.player_choice, scale=1.3)

    arcade.draw_text("vs", WIDTH // 2, mid_y + 20, TEXT_COLOR, 22, anchor_x="center")

    # AI choice
    arcade.draw_text("AI", WIDTH // 2 + 120, mid_y + 60, TEXT_COLOR, 18, anchor_x="center")
    _draw_icon(WIDTH // 2 + 120, mid_y, game.ai_choice, scale=1.3)

    # Result
    if game.result_text:
        color = {
            "You Win!": WIN_COLOR,
            "You Lose!": LOSE_COLOR,
            "Draw!": DRAW_COLOR,
        }.get(game.result_text, TEXT_COLOR)
        arcade.draw_text(game.result_text, WIDTH // 2, mid_y - 60, color, 30,
                         anchor_x="center", bold=True)


def _draw_history(game):
    """Draw the last 5 rounds in the upper-middle area."""
    start_y = HEIGHT - 70
    arcade.draw_text("Last rounds:", 20, start_y, TEXT_COLOR, 13, bold=True)
    recent = game.round_log[-5:]
    for i, (p, a, r) in enumerate(reversed(recent)):
        label = f"{p.capitalize()} vs {a.capitalize()} -> {r.upper()}"
        color = {
            "win": WIN_COLOR,
            "lose": LOSE_COLOR,
            "draw": DRAW_COLOR,
        }.get(r, TEXT_COLOR)
        arcade.draw_text(label, 20, start_y - 20 * (i + 1), color, 12)
