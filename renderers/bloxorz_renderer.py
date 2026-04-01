"""Renderer for Bloxorz — all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
TILE_W = 50
TILE_H = 30
ISO_X_STEP = TILE_W / 2
ISO_Y_STEP = TILE_H / 2

# Game states
PLAYING = 0
WON = 1
FALLEN = 2

# Tile types
EMPTY = 0
NORMAL = 1
FRAGILE = 2
GOAL = 3

# Block states
STANDING = 0
LYING_X = 1  # lying along col axis (occupies 2 cols)
LYING_Z = 2  # lying along row axis (occupies 2 rows)

# Colors
BG_COLOR = (25, 25, 35)
TILE_NORMAL = (70, 130, 180)
TILE_FRAGILE = (180, 130, 70)
TILE_GOAL = (220, 50, 50)
TILE_TOP_OFFSET = 8
TILE_SIDE_DARKEN = 40
BLOCK_COLOR = (200, 180, 60)
BLOCK_SIDE = (160, 140, 30)


def iso_to_screen(row, col, board_rows, board_cols):
    """Convert grid (row, col) to isometric screen coordinates."""
    cx = WIDTH / 2
    cy = HEIGHT / 2 - TOP_BAR_HEIGHT / 2 + 20
    # Center the board
    offset_x = -(board_cols - board_rows) * ISO_X_STEP / 2
    offset_y = (board_cols + board_rows) * ISO_Y_STEP / 2 - board_rows * ISO_Y_STEP
    sx = cx + (col - row) * ISO_X_STEP + offset_x
    sy = cy - (col + row) * ISO_Y_STEP + offset_y
    return sx, sy


def _draw_tile(sx, sy, color, tile_type):
    """Draw a single isometric tile (top face + side faces)."""
    hw = TILE_W / 2
    hh = TILE_H / 2
    top_y = sy + TILE_TOP_OFFSET

    # Top face (diamond)
    points = [
        (sx, top_y + hh),
        (sx + hw, top_y),
        (sx, top_y - hh),
        (sx - hw, top_y),
    ]
    arcade.draw_polygon_filled(points, color)
    arcade.draw_polygon_outline(points, (255, 255, 255, 50), 1)

    # Right side
    side_r = (max(color[0] - TILE_SIDE_DARKEN, 0),
              max(color[1] - TILE_SIDE_DARKEN, 0),
              max(color[2] - TILE_SIDE_DARKEN, 0))
    right_pts = [
        (sx, top_y - hh),
        (sx + hw, top_y),
        (sx + hw, top_y - TILE_TOP_OFFSET),
        (sx, top_y - hh - TILE_TOP_OFFSET),
    ]
    arcade.draw_polygon_filled(right_pts, side_r)

    # Left side
    side_l = (max(color[0] - TILE_SIDE_DARKEN - 15, 0),
              max(color[1] - TILE_SIDE_DARKEN - 15, 0),
              max(color[2] - TILE_SIDE_DARKEN - 15, 0))
    left_pts = [
        (sx, top_y - hh),
        (sx - hw, top_y),
        (sx - hw, top_y - TILE_TOP_OFFSET),
        (sx, top_y - hh - TILE_TOP_OFFSET),
    ]
    arcade.draw_polygon_filled(left_pts, side_l)

    # Fragile tile marker (X pattern)
    if tile_type == FRAGILE:
        arcade.draw_line(sx - 8, top_y - 4, sx + 8, top_y + 4, (255, 100, 100, 180), 2)
        arcade.draw_line(sx - 8, top_y + 4, sx + 8, top_y - 4, (255, 100, 100, 180), 2)

    # Goal marker (circle)
    if tile_type == GOAL:
        arcade.draw_circle_filled(sx, top_y, 6, (255, 255, 100))


def _draw_block_face(sx, sy, block_height):
    """Draw the block as a tall isometric box."""
    hw = TILE_W / 2 - 4
    hh = TILE_H / 2 - 2
    base_y = sy + TILE_TOP_OFFSET
    top_y = base_y + block_height

    # Top face
    top_pts = [
        (sx, top_y + hh),
        (sx + hw, top_y),
        (sx, top_y - hh),
        (sx - hw, top_y),
    ]
    arcade.draw_polygon_filled(top_pts, BLOCK_COLOR)
    arcade.draw_polygon_outline(top_pts, (255, 255, 200, 100), 1)

    # Right side
    right_pts = [
        (sx, top_y - hh),
        (sx + hw, top_y),
        (sx + hw, base_y),
        (sx, base_y - hh),
    ]
    arcade.draw_polygon_filled(right_pts, BLOCK_SIDE)

    # Left side
    left_pts = [
        (sx, top_y - hh),
        (sx - hw, top_y),
        (sx - hw, base_y),
        (sx, base_y - hh),
    ]
    arcade.draw_polygon_filled(left_pts, (140, 120, 20))


def draw(game):
    """Render the entire Bloxorz game state."""
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), BG_COLOR,
    )

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT), (50, 50, 50),
    )
    arcade.draw_rect_filled(arcade.XYWH(55, bar_y, 90, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(55, bar_y, 90, 35), arcade.color.WHITE)
    game.txt_back.draw()

    game.txt_info.draw()

    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.DARK_GREEN)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 65, bar_y, 110, 35), arcade.color.WHITE)
    game.txt_new_game.draw()

    arcade.draw_rect_filled(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.DARK_SLATE_BLUE)
    arcade.draw_rect_outline(arcade.XYWH(WIDTH - 135, bar_y, 40, 35), arcade.color.WHITE)
    game.txt_help.draw()

    # --- Board tiles ---
    board = game.board
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0

    # Draw tiles back to front (top-left to bottom-right in iso)
    for r in range(rows):
        for c in range(cols):
            tile = board[r][c]
            if tile == EMPTY:
                continue
            sx, sy = iso_to_screen(r, c, rows, cols)
            if tile == FRAGILE:
                _draw_tile(sx, sy, TILE_FRAGILE, FRAGILE)
            elif tile == GOAL:
                _draw_tile(sx, sy, TILE_GOAL, GOAL)
            else:
                _draw_tile(sx, sy, TILE_NORMAL, NORMAL)

    # --- Block ---
    if game.game_state != FALLEN:
        br, bc = game.block_pos
        state = game.block_state
        if state == STANDING:
            sx, sy = iso_to_screen(br, bc, rows, cols)
            _draw_block_face(sx, sy, 30)
        elif state == LYING_X:
            # Occupies (br, bc) and (br, bc+1)
            sx1, sy1 = iso_to_screen(br, bc, rows, cols)
            sx2, sy2 = iso_to_screen(br, bc + 1, rows, cols)
            _draw_block_face(sx1, sy1, 12)
            _draw_block_face(sx2, sy2, 12)
            # Connect them visually
            hw = TILE_W / 2 - 4
            mid_top1 = sy1 + TILE_TOP_OFFSET + 12
            mid_top2 = sy2 + TILE_TOP_OFFSET + 12
            conn_pts = [
                (sx1 + hw, mid_top1),
                (sx2, mid_top2 + (TILE_H / 2 - 2)),
                (sx2 - hw, mid_top2),
                (sx1, mid_top1 - (TILE_H / 2 - 2)),
            ]
            arcade.draw_polygon_filled(conn_pts, BLOCK_COLOR)
        elif state == LYING_Z:
            # Occupies (br, bc) and (br+1, bc)
            sx1, sy1 = iso_to_screen(br, bc, rows, cols)
            sx2, sy2 = iso_to_screen(br + 1, bc, rows, cols)
            _draw_block_face(sx1, sy1, 12)
            _draw_block_face(sx2, sy2, 12)
            hw = TILE_W / 2 - 4
            mid_top1 = sy1 + TILE_TOP_OFFSET + 12
            mid_top2 = sy2 + TILE_TOP_OFFSET + 12
            conn_pts = [
                (sx1, mid_top1 - (TILE_H / 2 - 2)),
                (sx1 - hw, mid_top1),
                (sx2, mid_top2 + (TILE_H / 2 - 2)),
                (sx2 + hw, mid_top2),
            ]
            arcade.draw_polygon_filled(conn_pts, BLOCK_COLOR)

    # --- Overlays ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 150),
        )
        game.txt_you_win.draw()
        game.txt_win_details.draw()
    elif game.game_state == FALLEN:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 150),
        )
        game.txt_fallen.draw()
        game.txt_fallen_hint.draw()
