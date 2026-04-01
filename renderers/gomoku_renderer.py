"""
Renderer for Gomoku (Five in a Row) game.
All arcade.draw_* calls for Gomoku live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Board constants
BOARD_SIZE = 15
CELL_SIZE = 34
BOARD_PIXEL = (BOARD_SIZE - 1) * CELL_SIZE  # intersections, not cells
BOARD_LEFT = (WIDTH - BOARD_PIXEL) / 2
BOARD_BOTTOM = (HEIGHT - BOARD_PIXEL) / 2 - 15

# Stone drawing
STONE_RADIUS = CELL_SIZE * 0.42

# Game values
EMPTY = 0
BLACK = 1
WHITE = 2

# Colors
BOARD_COLOR = (220, 179, 92)
BOARD_LINE_COLOR = (40, 30, 10)
BLACK_STONE = (20, 20, 20)
WHITE_STONE = (240, 240, 240)
HIGHLIGHT_COLOR = (255, 50, 50, 160)
STAR_COLOR = (40, 30, 10)

# Button constants
BUTTON_W = 90
BUTTON_H = 36

# Difficulty options
DIFFICULTIES = ["easy", "medium", "hard"]

# Star points for 15x15 board
STAR_POINTS = [(3, 3), (3, 7), (3, 11), (7, 3), (7, 7), (7, 11), (11, 3), (11, 7), (11, 11)]


def create_text_objects(game):
    """Create all arcade.Text objects on the game instance."""
    game.txt_back = arcade.Text(
        "Back", 60, HEIGHT - 30, arcade.color.WHITE,
        font_size=14, anchor_x="center", anchor_y="center",
    )
    game.txt_new_game = arcade.Text(
        "New Game", WIDTH - 70, HEIGHT - 30, arcade.color.WHITE,
        font_size=14, anchor_x="center", anchor_y="center",
    )
    game.txt_turn = arcade.Text(
        "", WIDTH / 2, HEIGHT - 30,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )
    game.txt_game_over = arcade.Text(
        "", WIDTH / 2, HEIGHT / 2 + 25,
        arcade.color.WHITE, font_size=24,
        anchor_x="center", anchor_y="center", bold=True,
    )
    game.txt_play_again = arcade.Text(
        "Click 'New Game' to play again.",
        WIDTH / 2, HEIGHT / 2 - 15,
        arcade.color.LIGHT_GRAY, font_size=13,
        anchor_x="center", anchor_y="center",
    )
    game.txt_difficulty = arcade.Text(
        "", WIDTH / 2, HEIGHT / 2 + 40,
        arcade.color.WHITE, font_size=18,
        anchor_x="center", anchor_y="center",
    )
    game.txt_diff_label = arcade.Text(
        "Select Difficulty", WIDTH / 2, HEIGHT / 2 + 100,
        arcade.color.WHITE, font_size=24,
        anchor_x="center", anchor_y="center", bold=True,
    )
    game.txt_diff_hint = arcade.Text(
        "Click a difficulty to begin", WIDTH / 2, HEIGHT / 2 - 80,
        arcade.color.LIGHT_GRAY, font_size=13,
        anchor_x="center", anchor_y="center",
    )
    game.txt_diff_easy = arcade.Text(
        "Easy", WIDTH / 2 - 150, HEIGHT / 2,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )
    game.txt_diff_medium = arcade.Text(
        "Medium", WIDTH / 2, HEIGHT / 2,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )
    game.txt_diff_hard = arcade.Text(
        "Hard", WIDTH / 2 + 150, HEIGHT / 2,
        arcade.color.WHITE, font_size=16,
        anchor_x="center", anchor_y="center",
    )


def intersection_pos(row, col):
    """Return (x, y) pixel position for an intersection. Row 0 = top."""
    x = BOARD_LEFT + col * CELL_SIZE
    y = BOARD_BOTTOM + (BOARD_SIZE - 1 - row) * CELL_SIZE
    return x, y


def draw(game):
    """Render the entire Gomoku game state."""
    if game.phase == "difficulty":
        _draw_difficulty_screen(game)
        return

    _draw_board(game)
    _draw_stones(game)

    if game.last_move is not None:
        _draw_last_move_marker(game)

    _draw_buttons(game)
    _draw_turn_indicator(game)

    if game.game_over:
        _draw_game_over(game)


def _draw_difficulty_screen(game):
    """Draw the difficulty selection screen."""
    _draw_buttons(game)
    game.txt_diff_label.draw()

    # Easy button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2 - 150, HEIGHT / 2, 100, 40), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2 - 150, HEIGHT / 2, 100, 40), arcade.color.WHITE)
    game.txt_diff_easy.draw()

    # Medium button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 100, 40), arcade.color.DARK_GOLDENROD)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 100, 40), arcade.color.WHITE)
    game.txt_diff_medium.draw()

    # Hard button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2 + 150, HEIGHT / 2, 100, 40), arcade.color.DARK_RED)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2 + 150, HEIGHT / 2, 100, 40), arcade.color.WHITE)
    game.txt_diff_hard.draw()

    game.txt_diff_hint.draw()


def _draw_board(game):
    """Draw the wooden board background and grid lines."""
    # Board background (slightly larger than grid)
    margin = CELL_SIZE * 0.7
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, BOARD_BOTTOM + BOARD_PIXEL / 2,
                     BOARD_PIXEL + margin * 2, BOARD_PIXEL + margin * 2),
        BOARD_COLOR,
    )

    # Grid lines
    for i in range(BOARD_SIZE):
        # Horizontal
        y = BOARD_BOTTOM + i * CELL_SIZE
        arcade.draw_line(BOARD_LEFT, y, BOARD_LEFT + BOARD_PIXEL, y, BOARD_LINE_COLOR, 1)
        # Vertical
        x = BOARD_LEFT + i * CELL_SIZE
        arcade.draw_line(x, BOARD_BOTTOM, x, BOARD_BOTTOM + BOARD_PIXEL, BOARD_LINE_COLOR, 1)

    # Star points
    for sr, sc in STAR_POINTS:
        x, y = intersection_pos(sr, sc)
        arcade.draw_circle_filled(x, y, 4, STAR_COLOR)


def _draw_stones(game):
    """Draw all placed stones."""
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if game.board[r][c] == EMPTY:
                continue
            x, y = intersection_pos(r, c)
            if game.board[r][c] == BLACK:
                arcade.draw_circle_filled(x, y, STONE_RADIUS, BLACK_STONE)
                arcade.draw_circle_outline(x, y, STONE_RADIUS, (60, 60, 60), 1)
            else:
                arcade.draw_circle_filled(x, y, STONE_RADIUS, WHITE_STONE)
                arcade.draw_circle_outline(x, y, STONE_RADIUS, (180, 180, 180), 1)


def _draw_last_move_marker(game):
    """Draw a small marker on the last move."""
    r, c = game.last_move
    x, y = intersection_pos(r, c)
    marker_color = (255, 50, 50) if game.board[r][c] == BLACK else (200, 0, 0)
    arcade.draw_circle_filled(x, y, 4, marker_color)


def _draw_buttons(game):
    """Draw Back, New Game, and Help buttons."""
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
    """Draw current turn indicator."""
    if game.game_over:
        return
    if game.current_turn == BLACK:
        label = "Your turn (Black)"
    else:
        label = "AI thinking..."
    game.txt_turn.text = label
    game.txt_turn.draw()


def _draw_game_over(game):
    """Draw the game over overlay."""
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), (0, 0, 0, 200))
    arcade.draw_rect_outline(arcade.XYWH(WIDTH / 2, HEIGHT / 2, 400, 120), arcade.color.WHITE, 2)

    if game.winner == BLACK:
        msg = "You Win!"
        color = arcade.color.LIGHT_GREEN
    elif game.winner == WHITE:
        msg = "AI Wins!"
        color = arcade.color.LIGHT_CORAL
    else:
        msg = "Draw!"
        color = arcade.color.LIGHT_BLUE

    game.txt_game_over.text = msg
    game.txt_game_over.color = color
    game.txt_game_over.draw()

    game.txt_play_again.draw()
