"""Renderer for Laser Maze — all drawing code lives here."""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
CELL_SIZE = 60
GAP = 2

# Game states
PLAYING = 0
WON = 1

# Cell types
EMPTY_CELL = 0
WALL = 1
MIRROR_NE = 2   # reflects: right<->up, left<->down  (/ orientation)
MIRROR_NW = 3   # reflects: left<->up, right<->down   (\ orientation)
LASER_SRC = 4   # laser source (fixed)
TARGET = 5       # must be hit by laser
SPLITTER = 6     # splits beam into two (/ and \ simultaneously)

# Direction constants (for reference, not imported by game)
DIR_UP = 0
DIR_RIGHT = 1
DIR_DOWN = 2
DIR_LEFT = 3

BG_COLOR = (25, 30, 40)
GRID_BG_COLOR = (40, 45, 55)
CELL_EMPTY_COLOR = (50, 55, 65)
CELL_BORDER_COLOR = (70, 75, 85)
WALL_COLOR = (80, 80, 90)
MIRROR_COLOR = (180, 200, 220)
LASER_SRC_COLOR = (220, 40, 40)
TARGET_COLOR = (40, 200, 40)
TARGET_HIT_COLOR = (100, 255, 100)
SPLITTER_COLOR = (200, 200, 100)
BEAM_COLOR = (255, 40, 40, 200)
BEAM_WIDTH = 3


def grid_metrics(grid_rows, grid_cols):
    """Compute grid origin and dimensions."""
    gw = grid_cols * CELL_SIZE
    gh = grid_rows * CELL_SIZE
    ox = (WIDTH - gw) / 2
    oy = (HEIGHT - TOP_BAR_HEIGHT - gh) / 2
    return gw, gh, ox, oy


def cell_center(row, col, grid_rows, grid_cols):
    """Pixel center of cell (row, col). Row 0 = top visually."""
    gw, gh, ox, oy = grid_metrics(grid_rows, grid_cols)
    visual_row = (grid_rows - 1) - row
    cx = ox + col * CELL_SIZE + CELL_SIZE / 2
    cy = oy + visual_row * CELL_SIZE + CELL_SIZE / 2
    return cx, cy


def _draw_mirror(cx, cy, mirror_type):
    """Draw a mirror (/ or \\) as a line across the cell."""
    half = CELL_SIZE * 0.35
    if mirror_type == MIRROR_NE:  # /
        arcade.draw_line(cx - half, cy - half, cx + half, cy + half, MIRROR_COLOR, 3)
        # Small triangle indicators
        arcade.draw_circle_filled(cx - half, cy - half, 4, MIRROR_COLOR)
        arcade.draw_circle_filled(cx + half, cy + half, 4, MIRROR_COLOR)
    elif mirror_type == MIRROR_NW:  # backslash
        arcade.draw_line(cx - half, cy + half, cx + half, cy - half, MIRROR_COLOR, 3)
        arcade.draw_circle_filled(cx - half, cy + half, 4, MIRROR_COLOR)
        arcade.draw_circle_filled(cx + half, cy - half, 4, MIRROR_COLOR)


def _draw_splitter(cx, cy):
    """Draw a splitter (both / and \\)."""
    half = CELL_SIZE * 0.35
    arcade.draw_line(cx - half, cy - half, cx + half, cy + half, SPLITTER_COLOR, 2)
    arcade.draw_line(cx - half, cy + half, cx + half, cy - half, SPLITTER_COLOR, 2)
    arcade.draw_circle_filled(cx, cy, 5, SPLITTER_COLOR)


def _draw_laser_source(cx, cy, direction):
    """Draw the laser source with direction indicator."""
    arcade.draw_circle_filled(cx, cy, CELL_SIZE * 0.3, LASER_SRC_COLOR)
    arcade.draw_circle_outline(cx, cy, CELL_SIZE * 0.3, (255, 100, 100), 2)
    # Arrow showing direction
    arrow_len = CELL_SIZE * 0.2
    dx, dy = 0, 0
    if direction == DIR_UP:
        dy = arrow_len
    elif direction == DIR_DOWN:
        dy = -arrow_len
    elif direction == DIR_LEFT:
        dx = -arrow_len
    elif direction == DIR_RIGHT:
        dx = arrow_len
    arcade.draw_line(cx, cy, cx + dx, cy + dy, (255, 200, 200), 3)


def _draw_target(cx, cy, hit):
    """Draw a target, highlighted if hit."""
    color = TARGET_HIT_COLOR if hit else TARGET_COLOR
    size = CELL_SIZE * 0.28
    # Diamond shape
    pts = [
        (cx, cy + size),
        (cx + size, cy),
        (cx, cy - size),
        (cx - size, cy),
    ]
    arcade.draw_polygon_filled(pts, color)
    arcade.draw_polygon_outline(pts, (255, 255, 255, 120), 2)
    if hit:
        arcade.draw_circle_filled(cx, cy, 5, (255, 255, 255))


def draw(game):
    """Render the entire Laser Maze game state."""
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

    # --- Grid ---
    gr = game.grid_rows
    gc = game.grid_cols
    gw, gh, ox, oy = grid_metrics(gr, gc)

    # Grid background
    arcade.draw_rect_filled(
        arcade.XYWH(ox + gw / 2, oy + gh / 2, gw, gh), GRID_BG_COLOR,
    )

    # Draw cells
    for r in range(gr):
        for c in range(gc):
            cx, cy = cell_center(r, c, gr, gc)
            cell_type = game.grid[r][c]
            s = CELL_SIZE - GAP

            if cell_type == WALL:
                arcade.draw_rect_filled(arcade.XYWH(cx, cy, s, s), WALL_COLOR)
            else:
                arcade.draw_rect_filled(arcade.XYWH(cx, cy, s, s), CELL_EMPTY_COLOR)

            arcade.draw_rect_outline(arcade.XYWH(cx, cy, s, s), CELL_BORDER_COLOR)

            # Draw cell contents
            if cell_type == MIRROR_NE or cell_type == MIRROR_NW:
                _draw_mirror(cx, cy, cell_type)
            elif cell_type == SPLITTER:
                _draw_splitter(cx, cy)
            elif cell_type == LASER_SRC:
                _draw_laser_source(cx, cy, game.laser_dir)
            elif cell_type == TARGET:
                hit = (r, c) in game.hit_targets
                _draw_target(cx, cy, hit)

    # --- Draw laser beam ---
    for seg in game.beam_segments:
        (r1, c1), (r2, c2) = seg
        x1, y1 = cell_center(r1, c1, gr, gc)
        x2, y2 = cell_center(r2, c2, gr, gc)
        arcade.draw_line(x1, y1, x2, y2, BEAM_COLOR, BEAM_WIDTH)

    # --- Win overlay ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), (0, 0, 0, 150),
        )
        game.txt_you_win.draw()
        game.txt_win_details.draw()
