"""
Renderer for the Slitherlink game.
All arcade.draw_* calls for Slitherlink live here.
"""

import arcade
import math

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid constants
GRID_ROWS = 7
GRID_COLS = 7
CELL_SIZE = 55
DOT_RADIUS = 5
EDGE_THICKNESS = 4
EDGE_HOVER_THICKNESS = 6

# Derived layout
GRID_PX_W = GRID_COLS * CELL_SIZE
GRID_PX_H = GRID_ROWS * CELL_SIZE
GRID_ORIGIN_X = (WIDTH - GRID_PX_W) // 2
GRID_ORIGIN_Y = (HEIGHT - 50 - GRID_PX_H) // 2

# Top bar
TOP_BAR_HEIGHT = 50

# Edge click tolerance (pixels from edge center)
EDGE_TOLERANCE = 12

# Colors
BG_COLOR = (40, 44, 52)
DOT_COLOR = (200, 200, 200)
CELL_BG = (55, 60, 70)
CLUE_COLOR = (220, 220, 220)
CLUE_SATISFIED_COLOR = (100, 200, 100)
CLUE_VIOLATED_COLOR = (240, 80, 80)
EDGE_ON_COLOR = (80, 180, 255)
EDGE_OFF_COLOR = (70, 75, 85)
EDGE_X_COLOR = (120, 60, 60)
WIN_OVERLAY = (0, 0, 0, 160)

# Game states
PLAYING = "playing"
WON = "won"


def draw(game):
    """Render the entire Slitherlink game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_cells(game)
    _draw_edges(game)
    _draw_dots()
    _draw_clues(game)
    if game.game_state == WON:
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

    # Timer
    mins = int(game.elapsed_time) // 60
    secs = int(game.elapsed_time) % 60
    game.txt_timer.text = f"{mins:02d}:{secs:02d}"
    game.txt_timer.draw()


def _draw_cells(game):
    """Draw cell backgrounds."""
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            cx = GRID_ORIGIN_X + c * CELL_SIZE + CELL_SIZE / 2
            cy = GRID_ORIGIN_Y + (GRID_ROWS - 1 - r) * CELL_SIZE + CELL_SIZE / 2
            arcade.draw_rect_filled(
                arcade.XYWH(cx, cy, CELL_SIZE - 2, CELL_SIZE - 2),
                CELL_BG
            )


def _draw_edges(game):
    """Draw horizontal and vertical edges."""
    # Horizontal edges: game.h_edges[r][c] for row r (0..ROWS), col c (0..COLS-1)
    for r in range(GRID_ROWS + 1):
        for c in range(GRID_COLS):
            state = game.h_edges[r][c]
            x1 = GRID_ORIGIN_X + c * CELL_SIZE
            x2 = GRID_ORIGIN_X + (c + 1) * CELL_SIZE
            y = GRID_ORIGIN_Y + (GRID_ROWS - r) * CELL_SIZE
            if state == 1:
                arcade.draw_line(x1, y, x2, y, EDGE_ON_COLOR, EDGE_THICKNESS)
            elif state == 2:
                # Draw X mark
                mx = (x1 + x2) / 2
                sz = 6
                arcade.draw_line(mx - sz, y - sz, mx + sz, y + sz, EDGE_X_COLOR, 2)
                arcade.draw_line(mx - sz, y + sz, mx + sz, y - sz, EDGE_X_COLOR, 2)

    # Vertical edges: game.v_edges[r][c] for row r (0..ROWS-1), col c (0..COLS)
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS + 1):
            state = game.v_edges[r][c]
            x = GRID_ORIGIN_X + c * CELL_SIZE
            y1 = GRID_ORIGIN_Y + (GRID_ROWS - r) * CELL_SIZE
            y2 = GRID_ORIGIN_Y + (GRID_ROWS - 1 - r) * CELL_SIZE
            if state == 1:
                arcade.draw_line(x, y1, x, y2, EDGE_ON_COLOR, EDGE_THICKNESS)
            elif state == 2:
                my = (y1 + y2) / 2
                sz = 6
                arcade.draw_line(x - sz, my - sz, x + sz, my + sz, EDGE_X_COLOR, 2)
                arcade.draw_line(x - sz, my + sz, x + sz, my - sz, EDGE_X_COLOR, 2)


def _draw_dots():
    """Draw dots at grid intersections."""
    for r in range(GRID_ROWS + 1):
        for c in range(GRID_COLS + 1):
            x = GRID_ORIGIN_X + c * CELL_SIZE
            y = GRID_ORIGIN_Y + (GRID_ROWS - r) * CELL_SIZE
            arcade.draw_circle_filled(x, y, DOT_RADIUS, DOT_COLOR)


def _draw_clues(game):
    """Draw number clues in cells."""
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            clue = game.clues[r][c]
            if clue is None:
                continue
            txt = game.txt_clues.get((r, c))
            if txt is None:
                continue

            # Count active edges around this cell
            count = _count_cell_edges(game, r, c)
            total_set = count
            # Determine color based on satisfaction
            if total_set == clue:
                color = CLUE_SATISFIED_COLOR
            elif total_set > clue:
                color = CLUE_VIOLATED_COLOR
            else:
                color = CLUE_COLOR

            txt.text = str(clue)
            txt.color = color
            txt.draw()


def _count_cell_edges(game, r, c):
    """Count how many edges are active (state=1) around cell (r, c)."""
    count = 0
    # Top edge
    if game.h_edges[r][c] == 1:
        count += 1
    # Bottom edge
    if game.h_edges[r + 1][c] == 1:
        count += 1
    # Left edge
    if game.v_edges[r][c] == 1:
        count += 1
    # Right edge
    if game.v_edges[r][c + 1] == 1:
        count += 1
    return count


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        WIN_OVERLAY
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
