"""
Renderer for the Mahjong Solitaire game.
All arcade.draw_* calls live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Top bar
TOP_BAR_HEIGHT = 50

# Tile dimensions
TILE_W = 40
TILE_H = 50
LAYER_OFFSET_X = 4
LAYER_OFFSET_Y = 4

# Board origin (bottom-left of layer 0, col -1, row 0)
# Grid spans col -1..12 (14 cols), row 0..7 (8 rows), plus 5 layers
GRID_COLS = 14  # -1 to 12
GRID_ROWS = 8
BOARD_W = GRID_COLS * TILE_W + 5 * LAYER_OFFSET_X
BOARD_H = GRID_ROWS * TILE_H + 5 * LAYER_OFFSET_Y
BOARD_ORIGIN_X = (WIDTH - BOARD_W) / 2 + TILE_W  # offset for col -1
BOARD_ORIGIN_Y = (HEIGHT - TOP_BAR_HEIGHT - BOARD_H) / 2

# Colors
BG_COLOR = (40, 44, 52)
TILE_FACE_COLOR = (240, 230, 210)
TILE_SIDE_COLOR = (180, 170, 150)
TILE_SHADOW_COLOR = (120, 110, 100)
TILE_SELECTED_COLOR = (180, 220, 255)
TILE_FREE_BORDER = (100, 180, 100)
TILE_LOCKED_BORDER = (140, 130, 120)
WIN_OVERLAY = (0, 0, 0, 160)


def draw(game):
    """Render the entire Mahjong Solitaire game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_tiles(game)
    if game.game_won:
        _draw_win_overlay(game)


def _draw_background():
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR)


def _draw_top_bar(game):
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50))

    # Back button
    bx, by, bw, bh = 55, bar_y, 90, 35
    arcade.draw_rect_filled(arcade.XYWH(bx, by, bw, bh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(bx, by, bw, bh), arcade.color.WHITE)
    game.txt_back.draw()

    # Shuffle button
    sx, sy, sw, sh = WIDTH / 2, bar_y, 80, 35
    arcade.draw_rect_filled(arcade.XYWH(sx, sy, sw, sh), arcade.color.DARK_GOLDENROD)
    arcade.draw_rect_outline(arcade.XYWH(sx, sy, sw, sh), arcade.color.WHITE)
    game.txt_shuffle.draw()

    # Remaining tiles count
    remaining = game._remaining_count()
    game.txt_remaining.text = f"{remaining} left"
    game.txt_remaining.draw()

    # New Game button
    nx, ny, nw, nh = WIDTH - 65, bar_y, 110, 35
    arcade.draw_rect_filled(arcade.XYWH(nx, ny, nw, nh), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(nx, ny, nw, nh), arcade.color.WHITE)
    game.txt_new_game.draw()

    # Help button
    hx, hy, hw, hh = WIDTH - 135, bar_y, 40, 40
    arcade.draw_rect_filled(arcade.XYWH(hx, hy, hw, hh), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(hx, hy, hw, hh), arcade.color.WHITE)
    game.txt_help.draw()


def _draw_tiles(game):
    """Draw all non-removed tiles, sorted by layer (bottom first), then by row (top-down for overlap)."""
    visible = [t for t in game.tiles if not t["removed"]]
    # Sort: lower layers first, then higher rows first (draw from back to front)
    visible.sort(key=lambda t: (t["layer"], -t["row"]))

    for tile in visible:
        tx, ty = game._tile_screen_pos(tile)
        is_selected = (game.selected == tile["id"])
        is_free = game._is_free(tile)
        label = game.tile_label(tile)
        text_color = game.tile_color(tile)

        # 3D effect: draw side/shadow
        shadow_x = tx - LAYER_OFFSET_X
        shadow_y = ty - LAYER_OFFSET_Y
        arcade.draw_rect_filled(
            arcade.XYWH(shadow_x, shadow_y, TILE_W, TILE_H),
            TILE_SHADOW_COLOR,
        )

        # Tile face
        face_color = TILE_SELECTED_COLOR if is_selected else TILE_FACE_COLOR
        arcade.draw_rect_filled(
            arcade.XYWH(tx, ty, TILE_W, TILE_H),
            face_color,
        )

        # Border
        border_color = TILE_FREE_BORDER if is_free else TILE_LOCKED_BORDER
        if is_selected:
            border_color = arcade.color.BLUE
        arcade.draw_rect_outline(
            arcade.XYWH(tx, ty, TILE_W, TILE_H),
            border_color, border_width=2,
        )

        # Label text
        txt_obj = game.txt_tiles[tile["id"]]
        txt_obj.text = label
        txt_obj.x = tx
        txt_obj.y = ty
        txt_obj.color = text_color
        txt_obj.draw()


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        WIN_OVERLAY,
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
