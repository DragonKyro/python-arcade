"""Renderer for 2048 — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid configuration
GRID_SIZE = 4
CELL_SIZE = 120
CELL_GAP = 10
GRID_PIXEL = GRID_SIZE * CELL_SIZE + (GRID_SIZE + 1) * CELL_GAP

# Position the grid: centered horizontally, shifted down a bit to leave room for header
GRID_LEFT = (WIDTH - GRID_PIXEL) / 2
GRID_BOTTOM = (HEIGHT - GRID_PIXEL) / 2 - 40

# Tile color mapping (value -> (R, G, B))
TILE_COLORS = {
    0:    (205, 193, 180),
    2:    (238, 228, 218),
    4:    (237, 224, 200),
    8:    (242, 177, 121),
    16:   (245, 149, 99),
    32:   (246, 124, 95),
    64:   (246, 94, 59),
    128:  (237, 207, 114),
    256:  (237, 204, 97),
    512:  (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46),
}

# Text color: dark for 2/4, white for everything else
DARK_TEXT = (119, 110, 101)
LIGHT_TEXT = (255, 255, 255)

# Background color for the grid area
GRID_BG_COLOR = (187, 173, 160)

# Default tile color for values > 2048
HIGH_TILE_COLOR = (60, 58, 50)


def _get_tile_color(value):
    """Return the background color for a tile value."""
    if value in TILE_COLORS:
        return TILE_COLORS[value]
    return HIGH_TILE_COLOR


def _get_text_color(value):
    """Return text color: dark for 2/4, white otherwise."""
    if value <= 4:
        return DARK_TEXT
    return LIGHT_TEXT


def _font_size_for_value(value):
    """Return an appropriate font size so large numbers fit in the cell."""
    if value < 100:
        return 40
    if value < 1000:
        return 34
    if value < 10000:
        return 28
    return 22


def draw(game):
    """Render the entire 2048 game state."""
    # Background
    arcade.set_background_color((250, 248, 239))

    # Title
    game.txt_title.draw()

    # Score
    game.txt_score.text = f"Score: {game.score}"
    game.txt_score.draw()

    # Buttons (these use the shared Button component's draw method)
    game.back_button.draw()
    game.new_game_button.draw()
    game.help_button.draw()

    # Grid background
    grid_cx = GRID_LEFT + GRID_PIXEL / 2
    grid_cy = GRID_BOTTOM + GRID_PIXEL / 2
    arcade.draw_rect_filled(arcade.XYWH(grid_cx, grid_cy, GRID_PIXEL + 6, GRID_PIXEL + 6), GRID_BG_COLOR)

    # Draw each cell
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            value = game.grid[r][c]
            # Cell position: row 0 is top row visually
            x = GRID_LEFT + CELL_GAP + c * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2
            y = GRID_BOTTOM + GRID_PIXEL - (CELL_GAP + r * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2)

            color = _get_tile_color(value)
            arcade.draw_rect_filled(arcade.XYWH(x, y, CELL_SIZE, CELL_SIZE), color)

            if value != 0:
                txt_obj = game.txt_cells[(r, c)]
                txt_obj.text = str(value)
                txt_obj.color = _get_text_color(value)
                txt_obj.font_size = _font_size_for_value(value)
                txt_obj.draw()

    # Win overlay
    if game.won and not game.won_acknowledged:
        _draw_overlay(game, "You Win!", "Click to continue")

    # Game over overlay
    if game.game_over:
        _draw_overlay(game, "Game Over!", "Click New Game to restart")


def _draw_overlay(game, title, subtitle):
    """Draw a semi-transparent overlay with a message."""
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (255, 255, 255, 150))
    game.txt_overlay_title.text = title
    game.txt_overlay_title.draw()
    game.txt_overlay_subtitle.text = subtitle
    game.txt_overlay_subtitle.draw()
