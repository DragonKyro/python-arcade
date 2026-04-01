"""Renderer for 15 Puzzle — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
GRID_SIZE = 4
CELL_SIZE = 110
GAP = 6

# Grid dimensions
GRID_WIDTH = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * GAP
GRID_HEIGHT = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * GAP
GRID_ORIGIN_X = (WIDTH - GRID_WIDTH) / 2
GRID_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - GRID_HEIGHT) / 2

# Tile colors by number range
TILE_COLORS = {
    range(1, 5): (70, 130, 210),     # blue
    range(5, 9): (60, 170, 90),      # green
    range(9, 13): (220, 150, 50),    # orange
    range(13, 16): (200, 60, 60),    # red
}

EMPTY_COLOR = (40, 40, 50)
TILE_BORDER_RADIUS = 12
TILE_TEXT_COLOR = arcade.color.WHITE

# Game states
PLAYING = 0
WON = 1


def _tile_color(number):
    """Return the color for a tile based on its number."""
    for r, color in TILE_COLORS.items():
        if number in r:
            return color
    return (100, 100, 100)


def cell_center(row, col):
    """Get the pixel center of a cell. Row 0 is the top row visually."""
    # Row 0 = top of grid, so we flip: visual row 0 is at the highest y
    grid_row = (GRID_SIZE - 1) - row
    cx = GRID_ORIGIN_X + GAP * (col + 1) + CELL_SIZE * col + CELL_SIZE / 2
    cy = GRID_ORIGIN_Y + GAP * (grid_row + 1) + CELL_SIZE * grid_row + CELL_SIZE / 2
    return cx, cy


def draw(game):
    """Render the entire 15 Puzzle game state."""
    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        arcade.color.DARK_SLATE_GRAY,
    )

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT),
        (50, 50, 50),
    )

    # Back button
    back_bx, back_by, back_bw, back_bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(
        arcade.XYWH(back_bx, back_by, back_bw, back_bh),
        arcade.color.DARK_SLATE_BLUE,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(back_bx, back_by, back_bw, back_bh),
        arcade.color.WHITE,
    )
    game.txt_back.draw()

    # Move counter
    game.txt_moves.text = f"Moves: {game.move_count}"
    game.txt_moves.draw()

    # Timer
    seconds = int(game.elapsed_time)
    minutes = seconds // 60
    secs = seconds % 60
    game.txt_timer.text = f"Time: {minutes}:{secs:02d}"
    game.txt_timer.draw()

    # New Game button
    new_bx, new_by, new_bw, new_bh = WIDTH - 65, bar_y, 110, 35
    arcade.draw_rect_filled(
        arcade.XYWH(new_bx, new_by, new_bw, new_bh),
        arcade.color.DARK_GREEN,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(new_bx, new_by, new_bw, new_bh),
        arcade.color.WHITE,
    )
    game.txt_new_game.draw()

    # Help button
    help_bx, help_by, help_bw, help_bh = WIDTH - 135, bar_y, 40, 35
    arcade.draw_rect_filled(
        arcade.XYWH(help_bx, help_by, help_bw, help_bh),
        arcade.color.DARK_SLATE_BLUE,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(help_bx, help_by, help_bw, help_bh),
        arcade.color.WHITE,
    )
    game.txt_help.draw()

    # --- Grid background ---
    arcade.draw_rect_filled(
        arcade.XYWH(
            GRID_ORIGIN_X + GRID_WIDTH / 2,
            GRID_ORIGIN_Y + GRID_HEIGHT / 2,
            GRID_WIDTH,
            GRID_HEIGHT,
        ),
        (30, 30, 40),
    )

    # --- Tiles ---
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            cx, cy = cell_center(row, col)
            value = game.board[row][col]

            if value == 0:
                # Empty space
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE - 4, CELL_SIZE - 4),
                    EMPTY_COLOR,
                )
            else:
                # Colored tile
                color = _tile_color(value)
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE - 4, CELL_SIZE - 4),
                    color,
                    tilt_angle=0,
                )
                # Rounded border highlight
                arcade.draw_rect_outline(
                    arcade.XYWH(cx, cy, CELL_SIZE - 4, CELL_SIZE - 4),
                    (255, 255, 255, 60),
                    border_width=2,
                )
                # Tile number
                txt_obj = game.txt_tile_numbers[(row, col)]
                txt_obj.text = str(value)
                txt_obj.draw()

    # --- Win overlay ---
    if game.game_state == WON:
        # Semi-transparent overlay
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            (0, 0, 0, 150),
        )
        game.txt_you_win.draw()
        seconds = int(game.elapsed_time)
        minutes = seconds // 60
        secs = seconds % 60
        game.txt_win_details.text = (
            f"Solved in {game.move_count} moves  |  Time: {minutes}:{secs:02d}"
        )
        game.txt_win_details.draw()
