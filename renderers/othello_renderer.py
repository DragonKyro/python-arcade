"""
Renderer for Othello game.
All arcade.draw_* calls for Othello live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Board constants
BOARD_SIZE = 8
CELL_SIZE = 55
BOARD_PIXEL = BOARD_SIZE * CELL_SIZE  # 440
BOARD_LEFT = (WIDTH - BOARD_PIXEL) / 2
BOARD_BOTTOM = (HEIGHT - BOARD_PIXEL) / 2

# Piece drawing
PIECE_RADIUS = CELL_SIZE * 0.4
HINT_RADIUS = 5

# Colors
BOARD_GREEN = (0, 128, 0)
BOARD_LINE = (0, 0, 0)
BLACK_PIECE = (20, 20, 20)
WHITE_PIECE = (240, 240, 240)
HINT_COLOR = (0, 0, 0, 100)

# Game values
EMPTY = 0
BLACK = 1
WHITE = 2


def create_text_objects(game):
    """Create all arcade.Text objects on the game instance. Call from __init__."""
    # Black score (left side)
    game.txt_score_black = arcade.Text(
        "", 30, HEIGHT / 2 - 20,
        arcade.color.WHITE, font_size=18,
        anchor_x="center", anchor_y="center", bold=True,
    )
    # White score (right side)
    game.txt_score_white = arcade.Text(
        "", WIDTH - 30, HEIGHT / 2 - 20,
        arcade.color.WHITE, font_size=18,
        anchor_x="center", anchor_y="center", bold=True,
    )
    # Back button label
    game.txt_back = arcade.Text(
        "Back", 60, HEIGHT - 30, arcade.color.WHITE,
        font_size=14, anchor_x="center", anchor_y="center",
    )
    # New Game button label
    game.txt_new_game = arcade.Text(
        "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE,
        font_size=14, anchor_x="center", anchor_y="center",
    )
    # Turn indicator (dynamic)
    game.txt_turn = arcade.Text(
        "", WIDTH / 2, HEIGHT - 30,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )
    # Game over: result message
    game.txt_game_over = arcade.Text(
        "", WIDTH / 2, HEIGHT / 2 + 25,
        arcade.color.WHITE, font_size=24,
        anchor_x="center", anchor_y="center", bold=True,
    )
    # Game over: final score
    game.txt_final_score = arcade.Text(
        "", WIDTH / 2, HEIGHT / 2 - 5,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )
    # Game over: play again hint
    game.txt_play_again = arcade.Text(
        "Click 'New Game' to play again.",
        WIDTH / 2, HEIGHT / 2 - 35,
        arcade.color.LIGHT_GRAY, font_size=13,
        anchor_x="center", anchor_y="center",
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
    game.txt_score_black.text = str(b)
    game.txt_score_black.draw()
    # White score (right side)
    arcade.draw_circle_filled(WIDTH - 30, HEIGHT / 2 + 10, 12, WHITE_PIECE)
    game.txt_score_white.text = str(w)
    game.txt_score_white.draw()


def _draw_buttons(game):
    # Back button
    arcade.draw_rect_filled(arcade.XYWH(60, HEIGHT - 30, 90, 36), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(60, HEIGHT - 30, 90, 36), arcade.color.WHITE)
    game.txt_back.draw()
    # New Game button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 70, HEIGHT - 30, 110, 36), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 70, HEIGHT - 30, 110, 36), arcade.color.WHITE)
    game.txt_new_game.draw()
    # Help button
    game.help_button.draw()


def _draw_turn_indicator(game):
    if game.game_over:
        return
    if game.current_turn == BLACK:
        label = "Your turn (Black)"
    else:
        label = "AI thinking..."
    game.txt_turn.text = label
    game.txt_turn.draw()


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

    game.txt_game_over.text = msg
    game.txt_game_over.color = color
    game.txt_game_over.draw()

    game.txt_final_score.text = f"Final Score:  Black {b}  -  White {w}"
    game.txt_final_score.draw()

    game.txt_play_again.draw()
