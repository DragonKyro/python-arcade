"""Renderer for Tic-Tac-Toe — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid layout
CELL_SIZE = 140
GRID_SIZE = CELL_SIZE * 3  # 420
GRID_LEFT = (WIDTH - GRID_SIZE) // 2
GRID_TOP = (HEIGHT - GRID_SIZE) // 2 + 30  # shift up slightly for status text
GRID_BOTTOM = GRID_TOP + GRID_SIZE  # in screen coords, y goes up

# Colors
BG_COLOR = (30, 30, 46)
LINE_COLOR = (205, 214, 244)
X_COLOR = (243, 139, 168)
O_COLOR = (137, 180, 250)
HIGHLIGHT_COLOR = (249, 226, 175)
BUTTON_COLOR = (69, 71, 90)
BUTTON_HOVER_COLOR = (88, 91, 112)
BUTTON_TEXT_COLOR = (205, 214, 244)
OVERLAY_COLOR = (30, 30, 46, 200)
MESSAGE_COLOR = (166, 227, 161)


def _grid_to_screen(row: int, col: int):
    """Convert grid (row, col) to screen center (x, y). Row 0 is top."""
    x = GRID_LEFT + col * CELL_SIZE + CELL_SIZE // 2
    y = HEIGHT - (GRID_TOP + row * CELL_SIZE + CELL_SIZE // 2)
    return x, y


def draw(game):
    """Render the entire Tic-Tac-Toe game state."""
    # Background
    arcade.draw_rect_filled(arcade.XYWH(WIDTH // 2, HEIGHT // 2, WIDTH, HEIGHT), BG_COLOR)

    # Title
    game.txt_title.draw()

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
    game.txt_status.text = status
    game.txt_status.draw()

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

    game.txt_overlay_msg.text = msg
    game.txt_overlay_msg.draw()

    game.btn_play_again.draw(
        hover=game.btn_play_again.contains(game.mouse_x, game.mouse_y)
    )
