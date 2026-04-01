"""
Renderer for the KenKen game.
All arcade.draw_* calls for KenKen live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid constants
CELL_SIZE = 70

# Default origin (recalculated dynamically based on grid size)
GRID_ORIGIN_X = (WIDTH - 4 * CELL_SIZE) // 2
GRID_ORIGIN_Y = (HEIGHT - 50 - 4 * CELL_SIZE) // 2

# Top bar
TOP_BAR_HEIGHT = 50

# Colors
BG_COLOR = (40, 44, 52)
GRID_BG = (255, 255, 255)
SELECTED_COLOR = (100, 149, 237)
CONFLICT_COLOR = (255, 180, 180)
CONFLICT_TEXT_COLOR = (220, 40, 40)
PLAYER_TEXT_COLOR = (50, 100, 220)
THIN_LINE_COLOR = (180, 180, 180)
CAGE_LINE_COLOR = (20, 20, 20)
CAGE_LABEL_COLOR = (80, 80, 80)
WIN_OVERLAY = (0, 0, 0, 160)


def draw(game):
    """Render the entire KenKen game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_grid_background(game)
    _draw_cell_highlights(game)
    _draw_numbers(game)
    _draw_thin_grid_lines(game)
    _draw_cage_borders(game)
    _draw_cage_labels(game)
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

    # Title
    game.txt_title.draw()
    game.txt_puzzle_num.text = f"Puzzle {game.puzzle_index + 1} ({game.size}x{game.size})"
    game.txt_puzzle_num.draw()

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


def _draw_grid_background(game):
    ox, oy = game._grid_origin()
    grid_px = game.size * CELL_SIZE
    arcade.draw_rect_filled(
        arcade.XYWH(ox + grid_px / 2, oy + grid_px / 2, grid_px, grid_px),
        GRID_BG
    )


def _draw_cell_highlights(game):
    """Draw selected cell and conflict highlights."""
    for r in range(game.size):
        for c in range(game.size):
            cx, cy = game._cell_center(r, c)
            if game.conflicts[r][c]:
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), CONFLICT_COLOR
                )
    if game.selected:
        sr, sc = game.selected
        cx, cy = game._cell_center(sr, sc)
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
            SELECTED_COLOR, border_width=3
        )


def _draw_numbers(game):
    """Draw player-entered numbers."""
    for r in range(game.size):
        for c in range(game.size):
            val = game.values[r][c]
            if val == 0:
                continue
            txt = game.txt_cells.get((r, c))
            if txt:
                cx, cy = game._cell_center(r, c)
                txt.x = cx
                txt.y = cy
                txt.text = str(val)
                txt.color = CONFLICT_TEXT_COLOR if game.conflicts[r][c] else PLAYER_TEXT_COLOR
                txt.draw()


def _draw_thin_grid_lines(game):
    """Draw thin internal grid lines."""
    ox, oy = game._grid_origin()
    grid_px = game.size * CELL_SIZE
    for i in range(game.size + 1):
        x = ox + i * CELL_SIZE
        arcade.draw_line(x, oy, x, oy + grid_px, THIN_LINE_COLOR, 1)
        y = oy + i * CELL_SIZE
        arcade.draw_line(ox, y, ox + grid_px, y, THIN_LINE_COLOR, 1)


def _draw_cage_borders(game):
    """Draw bold borders around cage groups."""
    cage_map = game.cell_cage
    size = game.size
    ox, oy = game._grid_origin()
    lw = 3

    for r in range(size):
        for c in range(size):
            cage_id = cage_map.get((r, c))
            cx, cy = game._cell_center(r, c)
            half = CELL_SIZE / 2

            # Top edge: if top neighbor is different cage or out of bounds
            if r == 0 or cage_map.get((r - 1, c)) != cage_id:
                arcade.draw_line(cx - half, cy + half, cx + half, cy + half, CAGE_LINE_COLOR, lw)
            # Bottom edge
            if r == size - 1 or cage_map.get((r + 1, c)) != cage_id:
                arcade.draw_line(cx - half, cy - half, cx + half, cy - half, CAGE_LINE_COLOR, lw)
            # Left edge
            if c == 0 or cage_map.get((r, c - 1)) != cage_id:
                arcade.draw_line(cx - half, cy - half, cx - half, cy + half, CAGE_LINE_COLOR, lw)
            # Right edge
            if c == size - 1 or cage_map.get((r, c + 1)) != cage_id:
                arcade.draw_line(cx + half, cy - half, cx + half, cy + half, CAGE_LINE_COLOR, lw)


def _draw_cage_labels(game):
    """Draw target+operation labels in the top-left cell of each cage."""
    for i, (target, op, cells) in enumerate(game.cages):
        if i >= len(game.txt_cage_labels):
            break
        # Find top-left cell (smallest row, then smallest col)
        top_left = min(cells, key=lambda rc: (rc[0], rc[1]))
        cx, cy = game._cell_center(top_left[0], top_left[1])
        half = CELL_SIZE / 2
        label = f"{target}{op}"
        txt = game.txt_cage_labels[i]
        txt.x = cx - half + 4
        txt.y = cy + half - 3
        txt.text = label
        txt.color = CAGE_LABEL_COLOR
        txt.draw()


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), WIN_OVERLAY
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
