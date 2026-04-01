"""
Renderer for Rock Paper Scissors game.
All arcade.draw_* calls for the RPS game live here.
"""

import arcade

# Window constants
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


def create_text_objects(game):
    """Create all arcade.Text objects on the game instance. Call from __init__."""
    # Score bar
    game.txt_score = arcade.Text(
        "", WIDTH // 2, HEIGHT - 30,
        TEXT_COLOR, 20, anchor_x="center",
    )
    # Back button label
    game.txt_back = arcade.Text(
        "Back", 60, HEIGHT - 30, TEXT_COLOR, 14,
        anchor_x="center", anchor_y="center",
    )
    # New Game button label
    game.txt_new_game = arcade.Text(
        "New Game", WIDTH - 70, HEIGHT - 30, TEXT_COLOR, 14,
        anchor_x="center", anchor_y="center",
    )
    # Choice button labels
    labels = ["Rock", "Paper", "Scissors"]
    game.txt_choice_labels = []
    for i, (cx, label) in enumerate(zip(BTN_CENTERS, labels)):
        game.txt_choice_labels.append(arcade.Text(
            label, cx, BTN_Y - 45, TEXT_COLOR, 14,
            anchor_x="center", anchor_y="center",
        ))
    # "Thinking..." text
    game.txt_thinking = arcade.Text(
        "Thinking...", WIDTH // 2, HEIGHT // 2, TEXT_COLOR, 28,
        anchor_x="center",
    )
    # Result area: "You" label
    mid_y = HEIGHT // 2 + 20
    game.txt_you_label = arcade.Text(
        "You", WIDTH // 2 - 120, mid_y + 60, TEXT_COLOR, 18,
        anchor_x="center",
    )
    # Result area: "vs" label
    game.txt_vs = arcade.Text(
        "vs", WIDTH // 2, mid_y + 20, TEXT_COLOR, 22,
        anchor_x="center",
    )
    # Result area: "AI" label
    game.txt_ai_label = arcade.Text(
        "AI", WIDTH // 2 + 120, mid_y + 60, TEXT_COLOR, 18,
        anchor_x="center",
    )
    # Result text (dynamic: "You Win!", "You Lose!", "Draw!")
    game.txt_result = arcade.Text(
        "", WIDTH // 2, mid_y - 60, TEXT_COLOR, 30,
        anchor_x="center", bold=True,
    )
    # History header
    start_y = HEIGHT - 70
    game.txt_history_header = arcade.Text(
        "Last rounds:", 20, start_y, TEXT_COLOR, 13, bold=True,
    )
    # History items (up to 5)
    game.txt_history_items = []
    for i in range(5):
        game.txt_history_items.append(arcade.Text(
            "", 20, start_y - 20 * (i + 1), TEXT_COLOR, 12,
        ))


def draw(game):
    """Render the entire RPS game state."""
    arcade.set_background_color(BG_COLOR)

    # -- Score bar --
    game.txt_score.text = f"Player: {game.player_wins}   AI: {game.ai_wins}   Draws: {game.draws}"
    game.txt_score.draw()

    # -- Back button (top-left) --
    arcade.draw_rect_filled(arcade.XYWH(60, HEIGHT - 30, 100, 36), BTN_COLOR)
    game.txt_back.draw()

    # -- New Game button (top-right) --
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 70, HEIGHT - 30, 120, 36), BTN_COLOR)
    game.txt_new_game.draw()

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
        game.txt_choice_labels[i].draw()

    # -- Show round result area --
    if game.waiting_for_reveal:
        game.txt_thinking.draw()
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
    game.txt_you_label.draw()
    _draw_icon(WIDTH // 2 - 120, mid_y, game.player_choice, scale=1.3)

    game.txt_vs.draw()

    # AI choice
    game.txt_ai_label.draw()
    _draw_icon(WIDTH // 2 + 120, mid_y, game.ai_choice, scale=1.3)

    # Result
    if game.result_text:
        color = {
            "You Win!": WIN_COLOR,
            "You Lose!": LOSE_COLOR,
            "Draw!": DRAW_COLOR,
        }.get(game.result_text, TEXT_COLOR)
        game.txt_result.text = game.result_text
        game.txt_result.color = color
        game.txt_result.draw()


def _draw_history(game):
    """Draw the last 5 rounds in the upper-middle area."""
    game.txt_history_header.draw()
    recent = game.round_log[-5:]
    for i, (p, a, r) in enumerate(reversed(recent)):
        label = f"{p.capitalize()} vs {a.capitalize()} -> {r.upper()}"
        color = {
            "win": WIN_COLOR,
            "lose": LOSE_COLOR,
            "draw": DRAW_COLOR,
        }.get(r, TEXT_COLOR)
        game.txt_history_items[i].text = label
        game.txt_history_items[i].color = color
        game.txt_history_items[i].draw()
