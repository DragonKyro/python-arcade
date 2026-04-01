"""Renderer for Lights Out — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
CELL_SIZE = 80

# Game states
PLAYING = 0
WON = 1

# Default 5x5 grid origin (recalculated dynamically)
GRID_ORIGIN_X = (WIDTH - 5 * CELL_SIZE) // 2
GRID_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - 5 * CELL_SIZE) // 2

# Colors
COLOR_ON = (255, 255, 100)
COLOR_OFF = (50, 50, 80)
COLOR_ON_OUTLINE = (200, 200, 60)
COLOR_OFF_OUTLINE = (80, 80, 110)


def draw(game):
    """Render the entire Lights Out game state."""
    # Background
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (30, 30, 50))

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

    # New Game button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.WHITE)
    game.txt_help.draw()

    # --- Grid ---
    n = game.grid_size
    ox, oy = game._get_grid_origin()

    for row in range(n):
        for col in range(n):
            cx = ox + col * CELL_SIZE + CELL_SIZE / 2
            cy = oy + row * CELL_SIZE + CELL_SIZE / 2
            is_on = game.grid[row][col]

            fill_color = COLOR_ON if is_on else COLOR_OFF
            outline_color = COLOR_ON_OUTLINE if is_on else COLOR_OFF_OUTLINE

            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy, CELL_SIZE - 4, CELL_SIZE - 4), fill_color
            )
            arcade.draw_rect_outline(
                arcade.XYWH(cx, cy, CELL_SIZE - 4, CELL_SIZE - 4), outline_color, 2
            )

    # --- Win overlay ---
    if game.game_state == WON:
        # Semi-transparent overlay
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            (0, 0, 0, 150)
        )
        game.txt_you_win.draw()
        game.txt_win_moves.text = f"Solved in {game.moves} moves"
        game.txt_win_moves.draw()
