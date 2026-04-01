"""
Renderer for the Checkers game.
All arcade.draw_* calls for Checkers live here.
"""

import arcade

from games.checkers import (
    WIDTH, HEIGHT,
    BOARD_SIZE, CELL_SIZE, BOARD_PIXEL, BOARD_LEFT, BOARD_BOTTOM, PIECE_RADIUS,
    LIGHT_SQUARE, DARK_SQUARE, PLAYER_COLOR, AI_PIECE_COLOR,
    SELECT_HIGHLIGHT, VALID_DEST_COLOR, KING_MARKER_COLOR, OVERLAY_BG,
    BUTTON_W, BUTTON_H,
    STATE_PLAYER_TURN, STATE_PLAYER_MULTI_JUMP, STATE_AI_THINKING, STATE_GAME_OVER,
)
from ai.checkers_ai import EMPTY, RED, BLACK, RED_KING, BLACK_KING, count_pieces


def draw(game):
    """Render the entire Checkers game state."""
    _draw_buttons(game)
    _draw_board(game)
    _draw_pieces(game)
    _draw_highlights(game)
    _draw_piece_counts(game)
    if game.state == STATE_GAME_OVER:
        _draw_overlay(game)


def _draw_buttons(game):
    """Draw Back, New Game, Help buttons, title, and turn indicator."""
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
        "Checkers",
        WIDTH // 2, HEIGHT - 30,
        arcade.color.WHITE, 22, anchor_x="center", anchor_y="center",
        bold=True,
    )

    # Turn indicator
    board_top = BOARD_BOTTOM + BOARD_PIXEL
    if game.state == STATE_PLAYER_TURN:
        msg = "Your turn (Red)"
        color = PLAYER_COLOR
    elif game.state == STATE_PLAYER_MULTI_JUMP:
        msg = "Continue jumping!"
        color = PLAYER_COLOR
    elif game.state == STATE_AI_THINKING:
        msg = "AI is thinking..."
        color = arcade.color.WHITE
    else:
        msg = ""
        color = arcade.color.WHITE

    if msg:
        arcade.draw_text(
            msg, WIDTH // 2, board_top + 18,
            color, 16, anchor_x="center", anchor_y="center", bold=True,
        )


def _draw_board(game):
    """Draw the checkerboard squares."""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            cx, cy = game._cell_center(row, col)
            if (row + col) % 2 == 0:
                color = LIGHT_SQUARE
            else:
                color = DARK_SQUARE
            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), color
            )

    # Board border
    bcx = BOARD_LEFT + BOARD_PIXEL // 2
    bcy = BOARD_BOTTOM + BOARD_PIXEL // 2
    arcade.draw_rect_outline(
        arcade.XYWH(bcx, bcy, BOARD_PIXEL, BOARD_PIXEL),
        arcade.color.WHITE, 2,
    )


def _draw_pieces(game):
    """Draw all pieces on the board."""
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = game.board[row][col]
            if piece == EMPTY:
                continue
            cx, cy = game._cell_center(row, col)
            if piece in (RED, RED_KING):
                arcade.draw_circle_filled(cx, cy, PIECE_RADIUS, PLAYER_COLOR)
                arcade.draw_circle_outline(cx, cy, PIECE_RADIUS, (120, 10, 10), 2)
            else:
                arcade.draw_circle_filled(cx, cy, PIECE_RADIUS, AI_PIECE_COLOR)
                arcade.draw_circle_outline(cx, cy, PIECE_RADIUS, (80, 80, 80), 2)

            # King marker
            if piece in (RED_KING, BLACK_KING):
                text_color = KING_MARKER_COLOR
                arcade.draw_text(
                    "K", cx, cy,
                    text_color, 16,
                    anchor_x="center", anchor_y="center",
                    bold=True,
                )


def _draw_highlights(game):
    """Draw selection highlight and valid destination markers."""
    sel = game.selected if game.state == STATE_PLAYER_TURN else game.multi_jump_pos
    if sel is not None:
        cx, cy = game._cell_center(sel[0], sel[1])
        arcade.draw_rect_filled(
            arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), SELECT_HIGHLIGHT
        )

    # Highlight valid destinations
    dest_cells = set()
    for move in game.valid_destinations:
        if len(move) >= 2:
            dest_cells.add(move[1])
    for (dr, dc) in dest_cells:
        cx, cy = game._cell_center(dr, dc)
        arcade.draw_circle_filled(cx, cy, 10, VALID_DEST_COLOR)


def _draw_piece_counts(game):
    """Draw piece count display."""
    red_count, black_count = count_pieces(game.board)
    # Left side - player (red) count
    arcade.draw_circle_filled(25, HEIGHT // 2 + 20, 10, PLAYER_COLOR)
    arcade.draw_text(
        f" {red_count}", 38, HEIGHT // 2 + 20,
        arcade.color.WHITE, 14, anchor_x="left", anchor_y="center",
    )
    # Left side - AI (black) count
    arcade.draw_circle_filled(25, HEIGHT // 2 - 10, 10, AI_PIECE_COLOR)
    arcade.draw_circle_outline(25, HEIGHT // 2 - 10, 10, (80, 80, 80), 1)
    arcade.draw_text(
        f" {black_count}", 38, HEIGHT // 2 - 10,
        arcade.color.WHITE, 14, anchor_x="left", anchor_y="center",
    )


def _draw_overlay(game):
    """Draw a semi-transparent overlay with the result message."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_BG
    )

    if game.winner == RED:
        msg = "You Win!"
        color = PLAYER_COLOR
    elif game.winner == BLACK:
        msg = "AI Wins!"
        color = arcade.color.WHITE
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
