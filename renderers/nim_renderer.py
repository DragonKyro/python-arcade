"""
Renderer for the Nim game view.
All arcade.draw_* calls for Nim are centralized here.
"""

import arcade

from games.nim import (
    WIDTH, HEIGHT,
    STONE_RADIUS, STONE_SPACING, ROW_SPACING, BOARD_TOP,
    STONE_COLOR, STONE_OUTLINE, SELECTED_COLOR, SELECTED_OUTLINE,
    REMOVED_COLOR, OVERLAY_BG,
    BUTTON_W, BUTTON_H, TAKE_BUTTON_W, TAKE_BUTTON_H,
    STATE_PLAYER_TURN, STATE_AI_THINKING, STATE_GAME_OVER,
)


def draw(game):
    """Render the entire Nim game state."""
    _draw_buttons(game)
    _draw_turn_indicator(game)
    _draw_board(game)
    _draw_take_button(game)
    if game.state == STATE_GAME_OVER:
        _draw_overlay(game)


def _draw_buttons(game):
    # Back button (top-left)
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(
        arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY
    )
    arcade.draw_rect_outline(
        arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2
    )
    arcade.draw_text(
        "Back", bx, by, arcade.color.WHITE, 14,
        anchor_x="center", anchor_y="center",
    )

    # New Game button (top-right)
    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(
        arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN
    )
    arcade.draw_rect_outline(
        arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2
    )
    arcade.draw_text(
        "New Game", nx, ny, arcade.color.WHITE, 14,
        anchor_x="center", anchor_y="center",
    )

    # Help button
    game.help_button.draw()

    # Title
    arcade.draw_text(
        "Nim", WIDTH // 2, HEIGHT - 30,
        arcade.color.WHITE, 22, anchor_x="center", anchor_y="center", bold=True,
    )


def _draw_turn_indicator(game):
    if game.state == STATE_PLAYER_TURN:
        msg = "Your turn - click stones to select, then Take"
        color = arcade.color.WHITE
    elif game.state == STATE_AI_THINKING:
        msg = "AI is thinking..."
        color = arcade.color.YELLOW
    else:
        msg = ""
        color = arcade.color.WHITE

    if msg:
        arcade.draw_text(
            msg, WIDTH // 2, HEIGHT - 70,
            color, 16, anchor_x="center", anchor_y="center",
        )


def _draw_board(game):
    for r in range(len(game.max_rows)):
        for s in range(game.max_rows[r]):
            cx, cy = game._stone_center(r, s)
            if s >= game.rows[r]:
                # Removed stone -- dim placeholder
                arcade.draw_circle_filled(cx, cy, STONE_RADIUS, REMOVED_COLOR)
            elif (
                game.selected_row == r
                and game.selected_from >= 0
                and s >= game.selected_from
            ):
                # Selected stone
                arcade.draw_circle_filled(cx, cy, STONE_RADIUS, SELECTED_COLOR)
                arcade.draw_circle_outline(cx, cy, STONE_RADIUS, SELECTED_OUTLINE, 3)
            else:
                # Normal stone
                arcade.draw_circle_filled(cx, cy, STONE_RADIUS, STONE_COLOR)
                arcade.draw_circle_outline(cx, cy, STONE_RADIUS, STONE_OUTLINE, 2)

        # Row label
        label_x = (WIDTH - (game.max_rows[r] - 1) * STONE_SPACING) / 2 - 40
        label_y = BOARD_TOP - r * ROW_SPACING
        arcade.draw_text(
            f"{game.rows[r]}", label_x, label_y,
            arcade.color.LIGHT_GRAY, 14,
            anchor_x="center", anchor_y="center",
        )


def _draw_take_button(game):
    count = game._selection_count()
    if count <= 0 or game.state != STATE_PLAYER_TURN:
        return
    tx, ty = WIDTH // 2, 40
    arcade.draw_rect_filled(
        arcade.XYWH(tx, ty, TAKE_BUTTON_W, TAKE_BUTTON_H), arcade.color.DARK_RED
    )
    arcade.draw_rect_outline(
        arcade.XYWH(tx, ty, TAKE_BUTTON_W, TAKE_BUTTON_H), arcade.color.WHITE, 2
    )
    arcade.draw_text(
        f"Take {count}", tx, ty, arcade.color.WHITE, 16,
        anchor_x="center", anchor_y="center", bold=True,
    )


def _draw_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
    )
    if game.winner == "player":
        msg = "You Win!"
        color = arcade.color.GREEN
    else:
        msg = "AI Wins!"
        color = arcade.color.RED

    arcade.draw_text(
        msg, WIDTH // 2, HEIGHT // 2 + 30,
        color, 48, anchor_x="center", anchor_y="center", bold=True,
    )
    arcade.draw_text(
        "The player who takes the last stone loses!",
        WIDTH // 2, HEIGHT // 2 - 20,
        arcade.color.LIGHT_GRAY, 14,
        anchor_x="center", anchor_y="center",
    )
    arcade.draw_text(
        "Click 'New Game' to play again",
        WIDTH // 2, HEIGHT // 2 - 50,
        arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
    )
