"""
Renderer for Connect Four game.
All arcade.draw_* calls for Connect Four live here.
"""

import arcade

from games.connect4 import (
    WIDTH, HEIGHT,
    CELL_SIZE, BOARD_MARGIN_X, BOARD_MARGIN_Y, CIRCLE_RADIUS,
    BOARD_COLOR, EMPTY_COLOR, PLAYER_COLOR, AI_COLOR,
    HIGHLIGHT_COLOR, WIN_HIGHLIGHT_COLOR, OVERLAY_BG,
    BUTTON_W, BUTTON_H,
    STATE_PLAYER_TURN, STATE_AI_THINKING, STATE_GAME_OVER,
)
from ai.connect4_ai import ROWS, COLS, EMPTY, PLAYER_PIECE, AI_PIECE


def draw(game):
    """Render the entire Connect Four game state."""
    _draw_buttons(game)
    _draw_board(game)
    _draw_hover(game)
    if game.state == STATE_GAME_OVER:
        _draw_win_highlights(game)
        _draw_overlay(game)


def _draw_buttons(game):
    # Back button (top-left)
    bx, by = 60, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.DARK_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, BUTTON_W, BUTTON_H), arcade.color.WHITE, 2)
    arcade.draw_text("Back", bx, by, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center")

    # New Game button (top-right)
    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
    arcade.draw_text("New Game", nx, ny, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center")

    # Help button
    game.help_button.draw()

    # Title
    arcade.draw_text(
        "Connect Four",
        WIDTH // 2, HEIGHT - 30,
        arcade.color.WHITE, 22, anchor_x="center", anchor_y="center",
        bold=True,
    )

    # Turn indicator
    if game.state == STATE_PLAYER_TURN:
        msg = "Your turn (Red)"
        color = PLAYER_COLOR
    elif game.state == STATE_AI_THINKING:
        msg = "AI is thinking..."
        color = AI_COLOR
    else:
        msg = ""
        color = arcade.color.WHITE

    if msg:
        board_top = BOARD_MARGIN_Y + ROWS * CELL_SIZE
        arcade.draw_text(
            msg, WIDTH // 2, board_top + 18,
            color, 16, anchor_x="center", anchor_y="center", bold=True,
        )


def _draw_board(game):
    # Blue board background
    bx = BOARD_MARGIN_X + (COLS * CELL_SIZE) // 2
    by = BOARD_MARGIN_Y + (ROWS * CELL_SIZE) // 2
    arcade.draw_rect_filled(arcade.XYWH(bx, by, COLS * CELL_SIZE, ROWS * CELL_SIZE), BOARD_COLOR)

    # Circles
    for row in range(ROWS):
        for col in range(COLS):
            cx, cy = game._cell_center(row, col)
            piece = game.board[row][col]
            if piece == PLAYER_PIECE:
                color = PLAYER_COLOR
            elif piece == AI_PIECE:
                color = AI_COLOR
            else:
                color = EMPTY_COLOR
            arcade.draw_circle_filled(cx, cy, CIRCLE_RADIUS, color)


def _draw_hover(game):
    """Draw a translucent highlight over the hovered column."""
    if game.state != STATE_PLAYER_TURN or game.hover_col < 0:
        return
    hx = BOARD_MARGIN_X + game.hover_col * CELL_SIZE + CELL_SIZE // 2
    hy = BOARD_MARGIN_Y + (ROWS * CELL_SIZE) // 2
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, CELL_SIZE, ROWS * CELL_SIZE), HIGHLIGHT_COLOR)

    # Preview piece at top
    preview_y = BOARD_MARGIN_Y + ROWS * CELL_SIZE + 18
    arcade.draw_circle_filled(hx, preview_y + 18, CIRCLE_RADIUS // 2, PLAYER_COLOR)


def _draw_win_highlights(game):
    """Draw white rings around the winning four pieces."""
    for row, col in game.winning_positions:
        cx, cy = game._cell_center(row, col)
        arcade.draw_circle_outline(cx, cy, CIRCLE_RADIUS + 3, arcade.color.WHITE, 4)


def _draw_overlay(game):
    """Draw a semi-transparent overlay with the result message."""
    arcade.draw_rect_filled(arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG)

    if game.winner == PLAYER_PIECE:
        msg = "You Win!"
        color = PLAYER_COLOR
    elif game.winner == AI_PIECE:
        msg = "AI Wins!"
        color = AI_COLOR
    else:
        msg = "It's a Draw!"
        color = arcade.color.WHITE

    arcade.draw_text(
        msg, WIDTH // 2, HEIGHT // 2 + 30,
        color, 48, anchor_x="center", anchor_y="center", bold=True,
    )
    arcade.draw_text(
        "Click 'New Game' to play again",
        WIDTH // 2, HEIGHT // 2 - 30,
        arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
    )
