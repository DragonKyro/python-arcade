"""
Renderer for Dots and Boxes game.
All arcade.draw_* calls for Dots and Boxes live here.
"""

import arcade

# Window / layout constants
WIDTH = 800
HEIGHT = 600

GRID_ROWS = 5
GRID_COLS = 5
DOT_COUNT_X = GRID_COLS + 1  # 6
DOT_COUNT_Y = GRID_ROWS + 1  # 6

DOT_SPACING = 80
DOT_RADIUS = 6

# Compute top-left of the grid so it is centred
GRID_W = (DOT_COUNT_X - 1) * DOT_SPACING
GRID_H = (DOT_COUNT_Y - 1) * DOT_SPACING
ORIGIN_X = (WIDTH - GRID_W) / 2
ORIGIN_Y = (HEIGHT - GRID_H) / 2 - 10  # nudge down a bit for score room

# Colours
COLOR_BG = arcade.color.WHITE
COLOR_DOT = arcade.color.BLACK
COLOR_PLAYER_LINE = arcade.color.BLUE
COLOR_AI_LINE = arcade.color.RED
COLOR_PLAYER_FILL = (173, 216, 230, 120)  # light blue
COLOR_AI_FILL = (255, 182, 182, 120)      # light red
COLOR_UNDRAWN = (220, 220, 220)
COLOR_TEXT = arcade.color.BLACK

LINE_WIDTH = 4
HIT_TOLERANCE = 20  # pixels from a line segment centre to register a click

# Button geometry
BTN_W = 100
BTN_H = 32
BTN_BACK_X = 60
BTN_BACK_Y = HEIGHT - 25
BTN_NEW_X = WIDTH - 60
BTN_NEW_Y = HEIGHT - 25


def _dot_pos(row, col):
    """Return (x, y) screen position for the dot at grid (row, col). Row 0 is top."""
    x = ORIGIN_X + col * DOT_SPACING
    y = ORIGIN_Y + (GRID_ROWS - row) * DOT_SPACING  # flip so row 0 is top visually
    return x, y


def create_text_objects(game):
    """Create all arcade.Text objects on the game instance. Call from __init__."""
    # Score (dynamic)
    game.txt_score = arcade.Text(
        "", WIDTH / 2, HEIGHT - 55, COLOR_TEXT, 16,
        anchor_x="center",
    )
    # Game over / turn indicator (dynamic)
    game.txt_status = arcade.Text(
        "", WIDTH / 2, HEIGHT - 80, COLOR_TEXT, 14,
        anchor_x="center",
    )
    # Back button label
    game.txt_back = arcade.Text(
        "Back", BTN_BACK_X, BTN_BACK_Y, COLOR_TEXT, 13,
        anchor_x="center", anchor_y="center",
    )
    # New Game button label
    game.txt_new_game = arcade.Text(
        "New Game", BTN_NEW_X, BTN_NEW_Y, COLOR_TEXT, 13,
        anchor_x="center", anchor_y="center",
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
    game.txt_score.text = f"Player (Blue): {game.player_score}    AI (Red): {game.ai_score}"
    game.txt_score.draw()

    # Turn / game-over indicator
    if game.game_over:
        if game.player_score > game.ai_score:
            msg = "You win!"
        elif game.ai_score > game.player_score:
            msg = "AI wins!"
        else:
            msg = "It's a tie!"
        game.txt_status.text = msg
        game.txt_status.font_size = 18
        game.txt_status.bold = True
        game.txt_status.draw()
    else:
        turn_msg = "Your turn" if game.current_turn == 'player' else "AI thinking..."
        game.txt_status.text = turn_msg
        game.txt_status.font_size = 14
        game.txt_status.bold = False
        game.txt_status.draw()

    # Back button
    arcade.draw_rect_filled(arcade.XYWH(BTN_BACK_X, BTN_BACK_Y, BTN_W, BTN_H), arcade.color.LIGHT_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(BTN_BACK_X, BTN_BACK_Y, BTN_W, BTN_H), arcade.color.DARK_GRAY, 2)
    game.txt_back.draw()

    # New Game button
    arcade.draw_rect_filled(arcade.XYWH(BTN_NEW_X, BTN_NEW_Y, BTN_W, BTN_H), arcade.color.LIGHT_GRAY)
    arcade.draw_rect_outline(arcade.XYWH(BTN_NEW_X, BTN_NEW_Y, BTN_W, BTN_H), arcade.color.DARK_GRAY, 2)
    game.txt_new_game.draw()

    # Help button
    game.help_button.draw()
