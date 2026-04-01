"""Renderer for 2048 — all drawing code lives here."""

import arcade
from games.twenty48 import (
    WIDTH, HEIGHT, GRID_SIZE, CELL_SIZE, CELL_GAP, GRID_PIXEL,
    GRID_LEFT, GRID_BOTTOM, GRID_BG_COLOR, DARK_TEXT,
    _get_tile_color, _get_text_color, _font_size_for_value,
)


def draw(game):
    """Render the entire 2048 game state."""
    # Background
    arcade.set_background_color((250, 248, 239))

    # Title
    arcade.draw_text(
        "2048",
        WIDTH / 2, HEIGHT - 30,
        DARK_TEXT,
        font_size=36,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )

    # Score
    arcade.draw_text(
        f"Score: {game.score}",
        WIDTH / 2, HEIGHT - 65,
        DARK_TEXT,
        font_size=20,
        anchor_x="center",
        anchor_y="center",
    )

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
                txt_color = _get_text_color(value)
                fsize = _font_size_for_value(value)
                arcade.draw_text(
                    str(value),
                    x, y,
                    txt_color,
                    font_size=fsize,
                    anchor_x="center",
                    anchor_y="center",
                    bold=True,
                )

    # Win overlay
    if game.won and not game.won_acknowledged:
        _draw_overlay("You Win!", "Click to continue")

    # Game over overlay
    if game.game_over:
        _draw_overlay("Game Over!", "Click New Game to restart")


def _draw_overlay(title, subtitle):
    """Draw a semi-transparent overlay with a message."""
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (255, 255, 255, 150))
    arcade.draw_text(
        title,
        WIDTH / 2, HEIGHT / 2 + 20,
        (119, 110, 101),
        font_size=52,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )
    arcade.draw_text(
        subtitle,
        WIDTH / 2, HEIGHT / 2 - 30,
        (119, 110, 101),
        font_size=20,
        anchor_x="center",
        anchor_y="center",
    )
