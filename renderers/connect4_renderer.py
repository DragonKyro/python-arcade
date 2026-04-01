"""
Renderer for Connect Four game.
All arcade.draw_* calls for Connect Four live here.
"""

import arcade

from ai.connect4_ai import ROWS, COLS, PLAYER_PIECE, AI_PIECE

# Window constants
WIDTH = 800
HEIGHT = 600

# Board drawing constants
CELL_SIZE = 70
BOARD_MARGIN_X = (WIDTH - COLS * CELL_SIZE) // 2
BOARD_MARGIN_Y = 40
CIRCLE_RADIUS = 28

# Colors
BOARD_COLOR = (0, 70, 180)
EMPTY_COLOR = (20, 20, 40)
PLAYER_COLOR = arcade.color.RED
AI_COLOR = arcade.color.YELLOW
HIGHLIGHT_COLOR = (255, 255, 255, 60)
WIN_HIGHLIGHT_COLOR = (255, 255, 255, 180)
OVERLAY_BG = (0, 0, 0, 170)

# Button dimensions
BUTTON_W = 100
BUTTON_H = 36

# Game states
STATE_PLAYER_TURN = "player_turn"
STATE_AI_THINKING = "ai_thinking"
STATE_GAME_OVER = "game_over"


def create_text_objects(game):
    """Create all arcade.Text objects on the game instance. Call from __init__."""
    # Back button label
    bx, by = 60, HEIGHT - 30
    game.txt_back = arcade.Text(
        "Back", bx, by, arcade.color.WHITE, 14,
        anchor_x="center", anchor_y="center",
    )
    # New Game button label
    nx, ny = WIDTH - 70, HEIGHT - 30
    game.txt_new_game = arcade.Text(
        "New Game", nx, ny, arcade.color.WHITE, 14,
        anchor_x="center", anchor_y="center",
    )
    # Title
    game.txt_title = arcade.Text(
        "Connect Four", WIDTH // 2, HEIGHT - 30,
        arcade.color.WHITE, 22, anchor_x="center", anchor_y="center",
        bold=True,
    )
    # Turn indicator (dynamic)
    board_top = BOARD_MARGIN_Y + ROWS * CELL_SIZE
    game.txt_turn = arcade.Text(
        "", WIDTH // 2, board_top + 18,
        arcade.color.WHITE, 16, anchor_x="center", anchor_y="center",
        bold=True,
    )
    # Overlay: result message (dynamic)
    game.txt_game_over = arcade.Text(
        "", WIDTH // 2, HEIGHT // 2 + 30,
        arcade.color.WHITE, 48, anchor_x="center", anchor_y="center",
        bold=True,
    )
    # Overlay: play again hint
    game.txt_play_again = arcade.Text(
        "Click 'New Game' to play again",
        WIDTH // 2, HEIGHT // 2 - 30,
        arcade.color.WHITE, 18, anchor_x="center", anchor_y="center",
    )


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
    game.txt_back.draw()

    # New Game button (top-right)
    nx, ny = WIDTH - 70, HEIGHT - 30
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, BUTTON_W + 10, BUTTON_H), arcade.color.WHITE, 2)
    game.txt_new_game.draw()

    # Help button
    game.help_button.draw()

    # Title
    game.txt_title.draw()

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
        game.txt_turn.text = msg
        game.txt_turn.color = color
        game.txt_turn.draw()


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

    game.txt_game_over.text = msg
    game.txt_game_over.color = color
    game.txt_game_over.draw()

    game.txt_play_again.draw()
