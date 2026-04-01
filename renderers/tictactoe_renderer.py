"""Renderer for Tic-Tac-Toe — all drawing code lives here."""

import arcade
from games.tictactoe import (
    WIDTH, HEIGHT, CELL_SIZE, GRID_SIZE, GRID_LEFT, GRID_TOP,
    BG_COLOR, LINE_COLOR, X_COLOR, O_COLOR, HIGHLIGHT_COLOR,
    MESSAGE_COLOR, OVERLAY_COLOR,
    _grid_to_screen,
)


def draw(game):
    """Render the entire Tic-Tac-Toe game state."""
    # Background
    arcade.draw_rect_filled(arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), BG_COLOR)

    # Title
    arcade.draw_text(
        "Tic-Tac-Toe",
        WIDTH // 2,
        HEIGHT - 30,
        LINE_COLOR,
        font_size=20,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )

    # Buttons (these use the _Button component's draw method)
    game.btn_back.draw(hover=game.btn_back.contains(game.mouse_x, game.mouse_y))
    game.btn_new.draw(hover=game.btn_new.contains(game.mouse_x, game.mouse_y))
    game.btn_help.draw(hover=game.btn_help.contains(game.mouse_x, game.mouse_y))

    # Turn / status text
    if not game.game_over:
        if game.ai_thinking:
            status = "AI is thinking..."
        else:
            status = "Your turn (X)"
    else:
        status = ""
    arcade.draw_text(
        status,
        WIDTH // 2,
        HEIGHT - 65,
        LINE_COLOR,
        font_size=15,
        anchor_x="center",
        anchor_y="center",
    )

    # Draw grid lines
    _draw_grid()

    # Draw markers
    _draw_markers(game)

    # Highlight winning line
    if game.winning_line:
        _draw_winning_highlight(game)

    # Game-over overlay
    if game.game_over:
        _draw_overlay(game)


def _draw_grid():
    """Draw the 3x3 grid lines."""
    left = GRID_LEFT
    right = GRID_LEFT + GRID_SIZE
    top_y = HEIGHT - GRID_TOP
    bottom_y = HEIGHT - GRID_TOP - GRID_SIZE

    # Vertical lines
    for i in range(4):
        x = left + i * CELL_SIZE
        arcade.draw_line(x, top_y, x, bottom_y, LINE_COLOR, 3)

    # Horizontal lines
    for i in range(4):
        y = top_y - i * CELL_SIZE
        arcade.draw_line(left, y, right, y, LINE_COLOR, 3)


def _draw_markers(game):
    """Draw X and O in each occupied cell."""
    pad = 28  # padding inside cell
    for r in range(3):
        for c in range(3):
            val = game.board[r][c]
            if val is None:
                continue
            cx, cy = _grid_to_screen(r, c)
            half = CELL_SIZE // 2 - pad
            if val == "X":
                arcade.draw_line(cx - half, cy - half, cx + half, cy + half, X_COLOR, 4)
                arcade.draw_line(cx - half, cy + half, cx + half, cy - half, X_COLOR, 4)
            else:
                arcade.draw_circle_outline(cx, cy, half, O_COLOR, 4)


def _draw_winning_highlight(game):
    """Draw a thick line through the winning cells."""
    if not game.winning_line or len(game.winning_line) < 2:
        return
    start = game.winning_line[0]
    end = game.winning_line[-1]
    x1, y1 = _grid_to_screen(start[0], start[1])
    x2, y2 = _grid_to_screen(end[0], end[1])
    arcade.draw_line(x1, y1, x2, y2, HIGHLIGHT_COLOR, 6)


def _draw_overlay(game):
    """Draw a translucent overlay with the result message and Play Again button."""
    arcade.draw_rect_filled(arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), OVERLAY_COLOR)

    if game.result == "X":
        msg = "You win!"
    elif game.result == "O":
        msg = "AI wins!"
    else:
        msg = "It's a draw!"

    arcade.draw_text(
        msg,
        WIDTH // 2,
        HEIGHT // 2 + 20,
        MESSAGE_COLOR,
        font_size=36,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )

    game.btn_play_again.draw(
        hover=game.btn_play_again.contains(game.mouse_x, game.mouse_y)
    )
