"""Renderer for Rush Hour — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
GRID_SIZE = 6
CELL_SIZE = 80

# Grid origin centered in window
GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE
GRID_ORIGIN_X = (WIDTH - GRID_WIDTH) // 2
GRID_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - GRID_HEIGHT) // 2

# Game states
PLAYING = 0
WON = 1

# Exit row for the red car
EXIT_ROW = 2


def draw(game):
    """Render the entire Rush Hour game state."""
    # Background
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (40, 40, 60))

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50))

    # Back button
    arcade.draw_rect_filled(arcade.XYWH(55, bar_y, 90, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(55, bar_y, 90, 35), arcade.color.WHITE)
    game.txt_back.draw()

    # Moves counter
    game.txt_moves.text = f"Moves: {game.moves}"
    game.txt_moves.draw()

    # Level indicator
    game.txt_level.text = f"Level {game.current_level + 1}"
    game.txt_level.draw()

    # New Game button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.WHITE)
    game.txt_help.draw()

    # --- Grid background ---
    grid_cx = GRID_ORIGIN_X + GRID_WIDTH / 2
    grid_cy = GRID_ORIGIN_Y + GRID_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(grid_cx, grid_cy, GRID_WIDTH, GRID_HEIGHT), (70, 70, 90)
    )

    # Grid lines
    for i in range(GRID_SIZE + 1):
        x = GRID_ORIGIN_X + i * CELL_SIZE
        arcade.draw_line(x, GRID_ORIGIN_Y, x, GRID_ORIGIN_Y + GRID_HEIGHT, (100, 100, 120), 1)
    for i in range(GRID_SIZE + 1):
        y = GRID_ORIGIN_Y + i * CELL_SIZE
        arcade.draw_line(GRID_ORIGIN_X, y, GRID_ORIGIN_X + GRID_WIDTH, y, (100, 100, 120), 1)

    # Exit indicator (gap on right side at row 2)
    exit_y = GRID_ORIGIN_Y + EXIT_ROW * CELL_SIZE + CELL_SIZE / 2
    exit_x = GRID_ORIGIN_X + GRID_WIDTH + 10
    arcade.draw_triangle_filled(
        exit_x, exit_y,
        exit_x + 15, exit_y,
        exit_x + 7, exit_y + 10,
        (220, 50, 50)
    )
    arcade.draw_triangle_filled(
        exit_x, exit_y,
        exit_x + 15, exit_y,
        exit_x + 7, exit_y - 10,
        (220, 50, 50)
    )

    # --- Cars ---
    for car in game.cars:
        row, col = car['row'], car['col']
        length = car['length']
        orient = car['orient']
        color = car['color']

        if orient == 'H':
            cx = GRID_ORIGIN_X + col * CELL_SIZE + (length * CELL_SIZE) / 2
            cy = GRID_ORIGIN_Y + row * CELL_SIZE + CELL_SIZE / 2
            w = length * CELL_SIZE - 6
            h = CELL_SIZE - 6
        else:
            cx = GRID_ORIGIN_X + col * CELL_SIZE + CELL_SIZE / 2
            cy = GRID_ORIGIN_Y + row * CELL_SIZE + (length * CELL_SIZE) / 2
            w = CELL_SIZE - 6
            h = length * CELL_SIZE - 6

        arcade.draw_rect_filled(arcade.XYWH(cx, cy, w, h), color)
        # Lighter outline
        outline = tuple(min(255, c + 60) for c in color)
        arcade.draw_rect_outline(arcade.XYWH(cx, cy, w, h), outline, 2)

    # --- Win overlay ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            (0, 0, 0, 150)
        )
        game.txt_you_win.draw()
        game.txt_win_info.text = f"Completed in {game.moves} moves! Click 'New Game' for next level."
        game.txt_win_info.draw()
