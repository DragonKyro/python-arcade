"""
Renderer for the Mancala game view.
All arcade.draw_* calls for Mancala are centralized here.
"""

import arcade
import math

from games.mancala import (
    WIDTH, HEIGHT,
    BOARD_CX, BOARD_CY, BOARD_W, BOARD_H,
    STORE_W, STORE_H, PIT_RADIUS, PIT_SPACING, PITS_START_X,
    PLAYER_ROW_Y, AI_ROW_Y, STORE_Y,
    LEFT_STORE_X, RIGHT_STORE_X,
    STONE_RADIUS, STONE_COLOR,
    BOARD_COLOR, BOARD_OUTLINE_COLOR,
    PIT_COLOR, PIT_HIGHLIGHT_COLOR, STORE_COLOR,
    PLAYER_SIDE, AI_SIDE,
)


def draw(game):
    """Render the entire Mancala game state."""
    # Title
    arcade.draw_text(
        "Mancala",
        WIDTH / 2, HEIGHT - 30,
        arcade.color.WHITE, font_size=28,
        anchor_x="center", anchor_y="center", bold=True,
    )

    # Buttons
    _draw_button(60, HEIGHT - 30, 90, 36, "Back", arcade.color.DARK_SLATE_BLUE)
    _draw_button(WIDTH - 70, HEIGHT - 30, 110, 36, "New Game", arcade.color.DARK_GREEN)
    _draw_button(WIDTH - 140, HEIGHT - 30, 40, 36, "?", arcade.color.DARK_SLATE_BLUE)

    _draw_board()
    _draw_pits(game)
    _draw_stores(game)
    _draw_labels(game)

    if game.extra_turn_timer > 0:
        arcade.draw_text(
            game.extra_turn_text,
            WIDTH / 2, HEIGHT / 2,
            arcade.color.YELLOW, font_size=22,
            anchor_x="center", anchor_y="center", bold=True,
        )

    if game.game_over:
        _draw_game_over(game)


def _draw_button(cx, cy, w, h, text, color):
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
    arcade.draw_text(
        text, cx, cy, arcade.color.WHITE,
        font_size=14, anchor_x="center", anchor_y="center",
    )


def _draw_board():
    """Draw the rounded board background."""
    arcade.draw_rect_filled(arcade.XYWH(BOARD_CX, BOARD_CY, BOARD_W, BOARD_H), BOARD_COLOR)
    arcade.draw_rect_outline(arcade.XYWH(BOARD_CX, BOARD_CY, BOARD_W, BOARD_H), BOARD_OUTLINE_COLOR, 3)
    # Rounded ends (circles at left/right)
    arcade.draw_circle_filled(BOARD_CX - BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_COLOR)
    arcade.draw_circle_filled(BOARD_CX + BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_COLOR)
    arcade.draw_circle_outline(BOARD_CX - BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_OUTLINE_COLOR, 3)
    arcade.draw_circle_outline(BOARD_CX + BOARD_W / 2, BOARD_CY, BOARD_H / 2, BOARD_OUTLINE_COLOR, 3)


def _draw_pits(game):
    """Draw all 12 pits with stones."""
    for i in range(6):
        px = game._pit_x(i)

        # --- Player pit (bottom row) ---
        is_valid = (
            game.player_turn
            and not game.game_over
            and game.pits[PLAYER_SIDE][i] > 0
        )
        is_hovered = is_valid and game.hovered_pit == i
        pit_col = PIT_HIGHLIGHT_COLOR if is_hovered else (PIT_COLOR if not is_valid else (90, 65, 35))
        outline_col = arcade.color.LIGHT_GREEN if is_valid else BOARD_OUTLINE_COLOR

        arcade.draw_circle_filled(px, PLAYER_ROW_Y, PIT_RADIUS, pit_col)
        arcade.draw_circle_outline(px, PLAYER_ROW_Y, PIT_RADIUS, outline_col, 2)
        _draw_stones_in_pit(px, PLAYER_ROW_Y, game.pits[PLAYER_SIDE][i])

        # --- AI pit (top row, mirrored: AI pit 0 is above player pit 5) ---
        ai_display_index = 5 - i
        ai_px = game._pit_x(i)
        arcade.draw_circle_filled(ai_px, AI_ROW_Y, PIT_RADIUS, PIT_COLOR)
        arcade.draw_circle_outline(ai_px, AI_ROW_Y, PIT_RADIUS, BOARD_OUTLINE_COLOR, 2)
        _draw_stones_in_pit(ai_px, AI_ROW_Y, game.pits[AI_SIDE][ai_display_index])


def _draw_stones_in_pit(cx, cy, count):
    """Draw stone count and small circles if count <= 10."""
    if count <= 0:
        return

    # Draw small stone circles for counts up to 10
    if count <= 10:
        positions = _stone_positions(cx, cy, count)
        for sx, sy in positions:
            arcade.draw_circle_filled(sx, sy, STONE_RADIUS, STONE_COLOR)
            arcade.draw_circle_outline(sx, sy, STONE_RADIUS, (120, 90, 60), 1)

    # Always draw count text
    arcade.draw_text(
        str(count), cx, cy - PIT_RADIUS - 12,
        arcade.color.WHITE, font_size=12,
        anchor_x="center", anchor_y="center", bold=True,
    )


def _stone_positions(cx, cy, count):
    """Return a list of (x, y) positions to draw stones in a pit."""
    positions = []
    if count == 1:
        positions.append((cx, cy))
    elif count <= 4:
        offsets = [(-8, -8), (8, -8), (-8, 8), (8, 8)]
        for k in range(count):
            positions.append((cx + offsets[k][0], cy + offsets[k][1]))
    elif count <= 10:
        # Arrange in a circle
        radius = min(18, PIT_RADIUS - STONE_RADIUS - 4)
        for k in range(count):
            angle = 2 * math.pi * k / count - math.pi / 2
            sx = cx + radius * math.cos(angle)
            sy = cy + radius * math.sin(angle)
            positions.append((sx, sy))
    return positions


def _draw_stores(game):
    """Draw the two stores on left and right ends."""
    # AI store (left)
    arcade.draw_rect_filled(arcade.XYWH(LEFT_STORE_X, STORE_Y, STORE_W, STORE_H), STORE_COLOR)
    arcade.draw_rect_outline(arcade.XYWH(LEFT_STORE_X, STORE_Y, STORE_W, STORE_H), BOARD_OUTLINE_COLOR, 2)
    arcade.draw_text(
        str(game.stores[AI_SIDE]),
        LEFT_STORE_X, STORE_Y,
        arcade.color.WHITE, font_size=24,
        anchor_x="center", anchor_y="center", bold=True,
    )
    arcade.draw_text(
        "AI", LEFT_STORE_X, STORE_Y + STORE_H / 2 + 12,
        arcade.color.LIGHT_GRAY, font_size=11,
        anchor_x="center", anchor_y="center",
    )

    # Player store (right)
    arcade.draw_rect_filled(arcade.XYWH(RIGHT_STORE_X, STORE_Y, STORE_W, STORE_H), STORE_COLOR)
    arcade.draw_rect_outline(arcade.XYWH(RIGHT_STORE_X, STORE_Y, STORE_W, STORE_H), BOARD_OUTLINE_COLOR, 2)
    arcade.draw_text(
        str(game.stores[PLAYER_SIDE]),
        RIGHT_STORE_X, STORE_Y,
        arcade.color.WHITE, font_size=24,
        anchor_x="center", anchor_y="center", bold=True,
    )
    arcade.draw_text(
        "You", RIGHT_STORE_X, STORE_Y - STORE_H / 2 - 12,
        arcade.color.LIGHT_GRAY, font_size=11,
        anchor_x="center", anchor_y="center",
    )


def _draw_labels(game):
    """Draw row labels and turn indicator."""
    # Turn indicator
    if not game.game_over:
        if game.player_turn:
            turn_text = "Your turn -- click a highlighted pit"
        else:
            turn_text = "AI is thinking..."
        arcade.draw_text(
            turn_text, WIDTH / 2, 40,
            arcade.color.WHITE, font_size=14,
            anchor_x="center", anchor_y="center",
        )

    # Pit index labels for player
    for i in range(6):
        px = game._pit_x(i)
        arcade.draw_text(
            str(i + 1), px, PLAYER_ROW_Y - PIT_RADIUS - 26,
            arcade.color.LIGHT_GRAY, font_size=10,
            anchor_x="center", anchor_y="center",
        )


def _draw_game_over(game):
    """Draw game over overlay."""
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 420, 140), (0, 0, 0, 200))
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 420, 140), arcade.color.WHITE, 2)

    if game.winner == "Tie":
        msg = "It's a tie!"
        color = arcade.color.LIGHT_STEEL_BLUE
    elif game.winner == "Player":
        msg = "You win!"
        color = arcade.color.LIGHT_GREEN
    else:
        msg = "AI wins!"
        color = arcade.color.LIGHT_CORAL

    score_msg = f"You: {game.stores[PLAYER_SIDE]}  --  AI: {game.stores[AI_SIDE]}"

    arcade.draw_text(
        msg, WIDTH / 2, HEIGHT / 2 + 25,
        color, font_size=26,
        anchor_x="center", anchor_y="center", bold=True,
    )
    arcade.draw_text(
        score_msg, WIDTH / 2, HEIGHT / 2 - 10,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )
    arcade.draw_text(
        "Click 'New Game' to play again.",
        WIDTH / 2, HEIGHT / 2 - 40,
        arcade.color.LIGHT_GRAY, font_size=13,
        anchor_x="center", anchor_y="center",
    )
