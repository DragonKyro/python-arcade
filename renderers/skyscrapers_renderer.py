"""
Renderer for the Skyscrapers game.
All arcade.draw_* calls live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Top bar
TOP_BAR_HEIGHT = 50

# Grid constants
CELL_SIZE = 70
CLUE_SIZE = 35  # space for clue labels around the grid

# Grid origin: bottom-left of the full area (including clue margin)
# Centered for a 5x5 grid by default; game recalculates based on grid_size
GRID_ORIGIN_X = 150
GRID_ORIGIN_Y = 50

# Colors
BG_COLOR = (40, 44, 52)
GRID_BG = (255, 255, 255)
CELL_HIGHLIGHT = (200, 220, 255)
SELECTED_COLOR = (100, 149, 237)
CONFLICT_COLOR = (255, 180, 180)
PLAYER_TEXT_COLOR = (50, 100, 220)
CONFLICT_TEXT_COLOR = (220, 40, 40)
CLUE_COLOR = (200, 200, 200)
CLUE_VIOLATED_COLOR = (255, 100, 100)
THIN_LINE_COLOR = (160, 160, 160)
THICK_LINE_COLOR = (20, 20, 20)
WIN_OVERLAY = (0, 0, 0, 160)


def _grid_origin(game):
    """Compute centered grid origin for current grid size."""
    n = game.grid_size
    total_w = n * CELL_SIZE + 2 * CLUE_SIZE
    total_h = n * CELL_SIZE + 2 * CLUE_SIZE
    ox = (WIDTH - total_w) / 2
    oy = (HEIGHT - TOP_BAR_HEIGHT - total_h) / 2
    return ox, oy


def draw(game):
    """Render the entire Skyscrapers game state."""
    # Update grid origin dynamically
    ox, oy = _grid_origin(game)
    # Patch the game's grid origin for coordinate calculations
    import renderers.skyscrapers_renderer as self_mod
    self_mod.GRID_ORIGIN_X = ox
    self_mod.GRID_ORIGIN_Y = oy

    _draw_background()
    _draw_top_bar(game)
    _draw_size_buttons(game)
    _draw_grid_background(game)
    _draw_cell_highlights(game)
    _draw_numbers(game)
    _draw_grid_lines(game)
    _draw_clues(game)
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

    # Size label
    game.txt_size_label.text = f"Skyscrapers {game.grid_size}x{game.grid_size}"
    game.txt_size_label.draw()

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


def _draw_size_buttons(game):
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    for size, label_txt, txt_x in [
        (4, game.txt_size_4, WIDTH / 2 - 40),
        (5, game.txt_size_5, WIDTH / 2),
        (6, game.txt_size_6, WIDTH / 2 + 40),
    ]:
        color = arcade.color.DARK_GREEN if size == game.grid_size else (80, 80, 80)
        arcade.draw_rect_filled(arcade.XYWH(txt_x, bar_y - 18, 35, 20), color)
        arcade.draw_rect_outline(arcade.XYWH(txt_x, bar_y - 18, 35, 20), arcade.color.WHITE)
        label_txt.draw()


def _draw_grid_background(game):
    n = game.grid_size
    ox = GRID_ORIGIN_X + CLUE_SIZE
    oy = GRID_ORIGIN_Y + CLUE_SIZE
    grid_px = n * CELL_SIZE
    arcade.draw_rect_filled(
        arcade.XYWH(ox + grid_px / 2, oy + grid_px / 2, grid_px, grid_px),
        GRID_BG,
    )


def _draw_cell_highlights(game):
    n = game.grid_size
    if game.selected is not None:
        sr, sc = game.selected
        # Highlight row and column
        for r in range(n):
            for c in range(n):
                if r == sr or c == sc:
                    cx, cy = game.cell_center(r, c)
                    arcade.draw_rect_filled(
                        arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                        CELL_HIGHLIGHT,
                    )

        # Conflict cells
        for r in range(n):
            for c in range(n):
                if game.conflicts[r][c]:
                    cx, cy = game.cell_center(r, c)
                    arcade.draw_rect_filled(
                        arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
                        CONFLICT_COLOR,
                    )

        # Selected cell
        cx, cy = game.cell_center(sr, sc)
        arcade.draw_rect_outline(
            arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE),
            SELECTED_COLOR, border_width=3,
        )


def _draw_numbers(game):
    n = game.grid_size
    for r in range(n):
        for c in range(n):
            val = game.board[r][c]
            txt = game.txt_cells[(r, c)]
            if val == 0:
                txt.text = ""
                continue
            cx, cy = game.cell_center(r, c)
            txt.text = str(val)
            txt.x = cx
            txt.y = cy
            txt.color = CONFLICT_TEXT_COLOR if game.conflicts[r][c] else PLAYER_TEXT_COLOR
            txt.draw()


def _draw_grid_lines(game):
    n = game.grid_size
    ox = GRID_ORIGIN_X + CLUE_SIZE
    oy = GRID_ORIGIN_Y + CLUE_SIZE
    grid_px = n * CELL_SIZE

    for i in range(n + 1):
        lw = 3 if i == 0 or i == n else 1
        col = THICK_LINE_COLOR if i == 0 or i == n else THIN_LINE_COLOR

        x0 = ox + i * CELL_SIZE
        arcade.draw_line(x0, oy, x0, oy + grid_px, col, lw)

        y0 = oy + i * CELL_SIZE
        arcade.draw_line(ox, y0, ox + grid_px, y0, col, lw)


def _draw_clues(game):
    n = game.grid_size
    for side in ["top", "bottom", "left", "right"]:
        for i in range(n):
            clue_val = game.clues[side][i]
            if clue_val == 0:
                continue
            cx, cy = game.clue_center(side, i)
            txt = game.txt_clues[side][i]
            txt.text = str(clue_val)
            txt.x = cx
            txt.y = cy
            violated = game.clue_violations[side][i]
            txt.color = CLUE_VIOLATED_COLOR if violated else CLUE_COLOR
            txt.draw()


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        WIN_OVERLAY,
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
