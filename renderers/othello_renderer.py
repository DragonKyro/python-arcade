"""
Renderer for Othello game.
All arcade.draw_* calls for Othello live here.
"""

import arcade

from games.othello import (
    WIDTH, HEIGHT,
    BOARD_SIZE, CELL_SIZE, BOARD_PIXEL, BOARD_LEFT, BOARD_BOTTOM,
    PIECE_RADIUS, HINT_RADIUS,
    BOARD_GREEN, BOARD_LINE, BLACK_PIECE, WHITE_PIECE, HINT_COLOR,
    EMPTY, BLACK, WHITE,
)


def draw(game):
    """Render the entire Othello game state."""
    _draw_board(game)
    _draw_pieces(game)

    if not game.game_over and game.current_turn == BLACK:
        _draw_hints(game)

    _draw_score(game)
    _draw_buttons(game)
    _draw_turn_indicator(game)

    if game.game_over:
        _draw_game_over(game)


def _draw_board(game):
    # Green background
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, BOARD_PIXEL, BOARD_PIXEL), BOARD_GREEN)
    # Grid lines
    for i in range(BOARD_SIZE + 1):
        # Horizontal
        y = BOARD_BOTTOM + i * CELL_SIZE
        arcade.draw_line(BOARD_LEFT, y, BOARD_LEFT + BOARD_PIXEL, y, BOARD_LINE, 2)
        # Vertical
        x = BOARD_LEFT + i * CELL_SIZE
        arcade.draw_line(x, BOARD_BOTTOM, x, BOARD_BOTTOM + BOARD_PIXEL, BOARD_LINE, 2)


def _draw_pieces(game):
    for r in range(8):
        for c in range(8):
            if game.board[r][c] == EMPTY:
                continue
            x, y = game._cell_center(r, c)
            color = BLACK_PIECE if game.board[r][c] == BLACK else WHITE_PIECE
            arcade.draw_circle_filled(x, y, PIECE_RADIUS, color)
            outline = (60, 60, 60) if game.board[r][c] == BLACK else (180, 180, 180)
            arcade.draw_circle_outline(x, y, PIECE_RADIUS, outline, 2)


def _draw_hints(game):
    for r, c in game.player_valid_moves:
        x, y = game._cell_center(r, c)
        arcade.draw_circle_filled(x, y, HINT_RADIUS, HINT_COLOR)


def _draw_score(game):
    b, w = game._count_pieces()
    # Black score (left side)
    arcade.draw_circle_filled(30, HEIGHT / 2 + 10, 12, BLACK_PIECE)
    arcade.draw_text(
        str(b), 30, HEIGHT / 2 - 20,
        arcade.color.WHITE, font_size=18,
        anchor_x="center", anchor_y="center", bold=True,
    )
    # White score (right side)
    arcade.draw_circle_filled(WIDTH - 30, HEIGHT / 2 + 10, 12, WHITE_PIECE)
    arcade.draw_text(
        str(w), WIDTH - 30, HEIGHT / 2 - 20,
        arcade.color.WHITE, font_size=18,
        anchor_x="center", anchor_y="center", bold=True,
    )


def _draw_buttons(game):
    # Back button
    _draw_button(60, HEIGHT - 30, 90, 36, "Back", arcade.color.DARK_SLATE_BLUE)
    # New Game button
    _draw_button(WIDTH - 70, HEIGHT - 30, 110, 36, "New Game", arcade.color.DARK_GREEN)
    # Help button
    game.help_button.draw()


def _draw_button(cx, cy, w, h, text, color):
    arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
    arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), arcade.color.WHITE)
    arcade.draw_text(
        text, cx, cy, arcade.color.WHITE,
        font_size=14, anchor_x="center", anchor_y="center",
    )


def _draw_turn_indicator(game):
    if game.game_over:
        return
    if game.current_turn == BLACK:
        label = "Your turn (Black)"
    else:
        label = "AI thinking..."
    arcade.draw_text(
        label, WIDTH / 2, HEIGHT - 30,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )


def _draw_game_over(game):
    # Semi-transparent overlay
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 140), (0, 0, 0, 200))
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 140), arcade.color.WHITE, 2)

    b, w = game._count_pieces()
    if game.winner == BLACK:
        msg = "Black Wins!"
        color = arcade.color.LIGHT_GREEN
    elif game.winner == WHITE:
        msg = "White Wins!"
        color = arcade.color.LIGHT_CORAL
    else:
        msg = "It's a Tie!"
        color = arcade.color.LIGHT_BLUE

    arcade.draw_text(
        msg, WIDTH / 2, HEIGHT / 2 + 25,
        color, font_size=24,
        anchor_x="center", anchor_y="center", bold=True,
    )
    arcade.draw_text(
        f"Final Score:  Black {b}  -  White {w}",
        WIDTH / 2, HEIGHT / 2 - 5,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )
    arcade.draw_text(
        "Click 'New Game' to play again.",
        WIDTH / 2, HEIGHT / 2 - 35,
        arcade.color.LIGHT_GRAY, font_size=13,
        anchor_x="center", anchor_y="center",
    )
