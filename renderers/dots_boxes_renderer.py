"""
Renderer for Dots and Boxes game.
All arcade.draw_* calls for Dots and Boxes live here.
"""

import arcade

from games.dots_boxes import (
    WIDTH, HEIGHT,
    GRID_ROWS, GRID_COLS,
    DOT_COUNT_X, DOT_COUNT_Y,
    DOT_SPACING, DOT_RADIUS,
    COLOR_BG, COLOR_DOT,
    COLOR_PLAYER_LINE, COLOR_AI_LINE,
    COLOR_PLAYER_FILL, COLOR_AI_FILL,
    COLOR_UNDRAWN, COLOR_TEXT,
    LINE_WIDTH,
    BTN_W, BTN_H, BTN_BACK_X, BTN_BACK_Y, BTN_NEW_X, BTN_NEW_Y,
    _dot_pos,
)


def draw(game):
    """Render the entire Dots and Boxes game state."""
    _draw_background()
    _draw_filled_boxes(game)
    _draw_lines(game)
    _draw_dots()
    _draw_ui(game)


def _draw_background():
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), COLOR_BG)


def _draw_filled_boxes(game):
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            owner = game.box_owner[r][c]
            if owner is None:
                continue
            x1, y1 = _dot_pos(r, c)
            x2, y2 = _dot_pos(r + 1, c + 1)
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            color = COLOR_PLAYER_FILL if owner == 'player' else COLOR_AI_FILL
            arcade.draw_rect_filled(arcade.XYWH(cx, cy, DOT_SPACING, DOT_SPACING), color)


def _draw_lines(game):
    # Horizontal
    for r in range(GRID_ROWS + 1):
        for c in range(GRID_COLS):
            x1, y1 = _dot_pos(r, c)
            x2, y2 = _dot_pos(r, c + 1)
            if game.h_lines[r][c]:
                owner = game.h_owners[r][c]
                color = COLOR_PLAYER_LINE if owner == 'player' else COLOR_AI_LINE
                arcade.draw_line(x1, y1, x2, y2, color, LINE_WIDTH)
            else:
                arcade.draw_line(x1, y1, x2, y2, COLOR_UNDRAWN, 1)

    # Vertical
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS + 1):
            x1, y1 = _dot_pos(r, c)
            x2, y2 = _dot_pos(r + 1, c)
            if game.v_lines[r][c]:
                owner = game.v_owners[r][c]
                color = COLOR_PLAYER_LINE if owner == 'player' else COLOR_AI_LINE
                arcade.draw_line(x1, y1, x2, y2, color, LINE_WIDTH)
            else:
                arcade.draw_line(x1, y1, x2, y2, COLOR_UNDRAWN, 1)


def _draw_dots():
    for r in range(DOT_COUNT_Y):
        for c in range(DOT_COUNT_X):
            x, y = _dot_pos(r, c)
            arcade.draw_circle_filled(x, y, DOT_RADIUS, COLOR_DOT)


def _draw_ui(game):
    # Score
    arcade.draw_text(
        f"Player (Blue): {game.player_score}    AI (Red): {game.ai_score}",
        WIDTH / 2, HEIGHT - 55, COLOR_TEXT, 16, anchor_x="center"
    )

    # Turn / game-over indicator
    if game.game_over:
        if game.player_score > game.ai_score:
            msg = "You win!"
        elif game.ai_score > game.player_score:
            msg = "AI wins!"
        else:
            msg = "It's a tie!"
        arcade.draw_text(msg, WIDTH / 2, HEIGHT - 80, COLOR_TEXT, 18,
                         anchor_x="center", bold=True)
    else:
        turn_msg = "Your turn" if game.current_turn == 'player' else "AI thinking..."
        arcade.draw_text(turn_msg, WIDTH / 2, HEIGHT - 80, COLOR_TEXT, 14,
                         anchor_x="center")

    # Back button
    arcade.draw_rect_filled(arcade.XYWH(BTN_BACK_X, BTN_BACK_Y, BTN_W, BTN_H), arcade.color.LIGHT_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(BTN_BACK_X, BTN_BACK_Y, BTN_W, BTN_H), arcade.color.DARK_GRAY, 2)
    arcade.draw_text("Back", BTN_BACK_X, BTN_BACK_Y, COLOR_TEXT, 13,
                     anchor_x="center", anchor_y="center")

    # New Game button
    arcade.draw_rect_filled(arcade.XYWH(BTN_NEW_X, BTN_NEW_Y, BTN_W, BTN_H), arcade.color.LIGHT_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(BTN_NEW_X, BTN_NEW_Y, BTN_W, BTN_H), arcade.color.DARK_GRAY, 2)
    arcade.draw_text("New Game", BTN_NEW_X, BTN_NEW_Y, COLOR_TEXT, 13,
                     anchor_x="center", anchor_y="center")

    # Help button
    game.help_button.draw()
