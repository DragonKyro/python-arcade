"""
Renderer for the Picross game.
All arcade.draw_* calls live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Top bar
TOP_BAR_HEIGHT = 50

# Grid constants (will be adjusted dynamically for different grid sizes)
CELL_SIZE = 32
CLUE_AREA_W = 100  # space for row clues on the left
CLUE_AREA_H = 100  # space for column clues on top

# Grid origin: bottom-left of the grid area (not including clue areas)
GRID_ORIGIN_X = 80
GRID_ORIGIN_Y = 60

# Colors
BG_COLOR = (40, 44, 52)
GRID_BG = (60, 65, 75)
CELL_EMPTY = (80, 85, 95)
CELL_FILLED = (70, 160, 230)
CELL_MARKED = (60, 65, 75)
CELL_BORDER = (100, 105, 115)
THICK_LINE_COLOR = (200, 200, 200)
CLUE_COLOR = (200, 200, 200)
CLUE_COMPLETE_COLOR = (100, 100, 100)
X_COLOR = (200, 80, 80)
WIN_OVERLAY = (0, 0, 0, 160)


def _compute_layout(game):
    """Compute dynamic cell size and origin based on grid dimensions."""
    rows, cols = game.grid_rows, game.grid_cols
    # Available space
    avail_w = WIDTH - CLUE_AREA_W - 40
    avail_h = HEIGHT - TOP_BAR_HEIGHT - CLUE_AREA_H - 40
    cell = min(avail_w // cols, avail_h // rows, 40)
    cell = max(cell, 20)  # minimum cell size

    grid_w = cols * cell
    grid_h = rows * cell
    ox = (WIDTH - CLUE_AREA_W - grid_w) / 2 + CLUE_AREA_W / 2
    oy = (HEIGHT - TOP_BAR_HEIGHT - CLUE_AREA_H - grid_h) / 2

    return cell, ox, oy


def draw(game):
    """Render the entire Picross game state."""
    cell, ox, oy = _compute_layout(game)
    # Patch module-level values for game's coordinate calculations
    import renderers.picross_renderer as self_mod
    self_mod.CELL_SIZE = cell
    self_mod.GRID_ORIGIN_X = ox
    self_mod.GRID_ORIGIN_Y = oy

    _draw_background()
    _draw_top_bar(game)
    _draw_size_buttons(game)
    _draw_grid(game, cell, ox, oy)
    _draw_clues(game, cell, ox, oy)
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

    # Timer
    mins = int(game.elapsed_time) // 60
    secs = int(game.elapsed_time) % 60
    game.txt_timer.text = f"{mins:02d}:{secs:02d}"
    game.txt_timer.draw()

    # Theme label
    game.txt_theme_label.text = f"Theme: {game.theme}"
    game.txt_theme_label.draw()

    # Mistakes
    game.txt_mistakes.text = f"Mistakes: {game.mistakes}"
    game.txt_mistakes.draw()

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
    sizes_data = [(5, 5), (10, 10), (15, 15)]
    for idx, (nr, nc) in enumerate(sizes_data):
        bx = 200 + idx * 55
        is_active = (nr == game.grid_rows and nc == game.grid_cols)
        color = arcade.color.DARK_GREEN if is_active else (80, 80, 80)
        arcade.draw_rect_filled(arcade.XYWH(bx, bar_y - 16, 48, 18), color)
        arcade.draw_rect_outline(arcade.XYWH(bx, bar_y - 16, 48, 18), arcade.color.WHITE)
        game.txt_size_btns[idx].draw()

    # Theme button
    arcade.draw_rect_filled(arcade.XYWH(380, bar_y - 16, 50, 18), (80, 80, 80))
    arcade.draw_rect_outline(arcade.XYWH(380, bar_y - 16, 50, 18), arcade.color.WHITE)
    game.txt_theme_btn.draw()


def _draw_grid(game, cell, ox, oy):
    rows, cols = game.grid_rows, game.grid_cols

    for r in range(rows):
        for c in range(cols):
            cx, cy = game.cell_center(r, c)
            val = game.grid[r][c]

            if val == 1:
                color = CELL_FILLED
            elif val == 2:
                color = CELL_MARKED
            else:
                color = CELL_EMPTY

            arcade.draw_rect_filled(arcade.XYWH(cx, cy, cell - 1, cell - 1), color)

            # Draw X for marked cells
            if val == 2:
                half = cell * 0.3
                arcade.draw_line(cx - half, cy - half, cx + half, cy + half, X_COLOR, 2)
                arcade.draw_line(cx - half, cy + half, cx + half, cy - half, X_COLOR, 2)

    # Grid lines: thick every 5 cells
    grid_w = cols * cell
    grid_h = rows * cell
    grid_left = ox + CLUE_AREA_W
    grid_bottom = oy

    for i in range(cols + 1):
        lw = 2 if i % 5 == 0 else 1
        col = THICK_LINE_COLOR if i % 5 == 0 else CELL_BORDER
        x = grid_left + i * cell
        arcade.draw_line(x, grid_bottom, x, grid_bottom + grid_h, col, lw)

    for i in range(rows + 1):
        lw = 2 if i % 5 == 0 else 1
        col = THICK_LINE_COLOR if i % 5 == 0 else CELL_BORDER
        y = grid_bottom + i * cell
        arcade.draw_line(grid_left, y, grid_left + grid_w, y, col, lw)


def _draw_clues(game, cell, ox, oy):
    rows, cols = game.grid_rows, game.grid_cols
    grid_left = ox + CLUE_AREA_W
    grid_bottom = oy

    # Row clues (on the left)
    for r in range(rows):
        clue = game.row_clues[r]
        is_complete = game.row_complete[r]
        cy = grid_bottom + (rows - 1 - r) * cell + cell / 2
        for i, val in enumerate(reversed(clue)):
            cx = grid_left - 8 - i * 22
            key = (r, len(clue) - 1 - i)
            if key in game.txt_row_clues:
                txt = game.txt_row_clues[key]
                txt.text = str(val)
                txt.x = cx
                txt.y = cy
                txt.color = CLUE_COMPLETE_COLOR if is_complete else CLUE_COLOR
                txt.draw()

    # Column clues (on top)
    for c in range(cols):
        clue = game.col_clues[c]
        is_complete = game.col_complete[c]
        cx = grid_left + c * cell + cell / 2
        for i, val in enumerate(reversed(clue)):
            cy = grid_bottom + rows * cell + 8 + i * 16
            key = (c, len(clue) - 1 - i)
            if key in game.txt_col_clues:
                txt = game.txt_col_clues[key]
                txt.text = str(val)
                txt.x = cx
                txt.y = cy
                txt.color = CLUE_COMPLETE_COLOR if is_complete else CLUE_COLOR
                txt.draw()


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        WIN_OVERLAY,
    )
    game.txt_win_title.draw()
    mins = int(game.elapsed_time) // 60
    secs = int(game.elapsed_time) % 60
    game.txt_win_time.text = f"Completed in {mins:02d}:{secs:02d}"
    game.txt_win_time.draw()
    game.txt_win_hint.draw()
