"""Renderer for Nonograms -- all drawing code lives here."""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Layout constants
TOP_BAR_HEIGHT = 50
CELL_SIZE = 30
CLUE_AREA_WIDTH = 120
CLUE_AREA_HEIGHT = 100

# Game states
PLAYING = 0
WON = 1

# Cell states
EMPTY = 0
FILLED = 1
MARKED_X = 2

# Colors
COLOR_CELL_EMPTY = (220, 215, 205)
COLOR_CELL_FILLED = (40, 40, 50)
COLOR_CELL_MARKED = (220, 215, 205)
COLOR_GRID_LINE = (160, 150, 140)
COLOR_GRID_LINE_THICK = (80, 70, 60)
COLOR_CLUE_NORMAL = arcade.color.WHITE
COLOR_CLUE_COMPLETE = (100, 200, 100)
COLOR_X_MARK = (200, 80, 80)


def grid_origin(grid_cols, grid_rows):
    """Return (ox, oy) for bottom-left of the grid."""
    grid_w = grid_cols * CELL_SIZE
    grid_h = grid_rows * CELL_SIZE
    total_w = CLUE_AREA_WIDTH + grid_w
    total_h = CLUE_AREA_HEIGHT + grid_h
    play_area_h = HEIGHT - TOP_BAR_HEIGHT
    ox = (WIDTH - total_w) / 2 + CLUE_AREA_WIDTH
    oy = (play_area_h - total_h) / 2
    return ox, oy


def cell_center(col, row, ox, oy, grid_rows):
    """Return pixel center (cx, cy) for a cell. Row 0 = top row."""
    visual_row = (grid_rows - 1) - row
    cx = ox + col * CELL_SIZE + CELL_SIZE / 2
    cy = oy + visual_row * CELL_SIZE + CELL_SIZE / 2
    return cx, cy


def draw(game):
    """Render the entire Nonograms game state."""
    rows = game.grid_rows
    cols = game.grid_cols
    ox, oy = grid_origin(cols, rows)

    # Background
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
        arcade.color.DARK_SLATE_GRAY,
    )

    # --- Top bar ---
    bar_y = HEIGHT - TOP_BAR_HEIGHT / 2
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, bar_y, WIDTH, TOP_BAR_HEIGHT),
        (50, 50, 50),
    )

    # Back button
    arcade.draw_rect_filled(
        arcade.XYWH(55, bar_y, 90, 35),
        arcade.color.DARK_SLATE_BLUE,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(55, bar_y, 90, 35),
        arcade.color.WHITE,
    )
    game.txt_back.draw()

    # Status
    game.txt_status.draw()

    # New Game button
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH - 65, bar_y, 110, 35),
        arcade.color.DARK_GREEN,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH - 65, bar_y, 110, 35),
        arcade.color.WHITE,
    )
    game.txt_new_game.draw()

    # Help button
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH - 135, bar_y, 40, 35),
        arcade.color.DARK_SLATE_BLUE,
    )
    arcade.draw_rect_outline(
        arcade.XYWH(WIDTH - 135, bar_y, 40, 35),
        arcade.color.WHITE,
    )
    game.txt_help.draw()

    # --- Grid background ---
    grid_w = cols * CELL_SIZE
    grid_h = rows * CELL_SIZE
    arcade.draw_rect_filled(
        arcade.XYWH(ox + grid_w / 2, oy + grid_h / 2, grid_w, grid_h),
        COLOR_CELL_EMPTY,
    )

    # --- Cells ---
    for r in range(rows):
        for c in range(cols):
            cx, cy = cell_center(c, r, ox, oy, rows)
            state = game.player_grid[r][c]
            if state == FILLED:
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE - 1, CELL_SIZE - 1),
                    COLOR_CELL_FILLED,
                )
            elif state == MARKED_X:
                # Draw X
                s = CELL_SIZE * 0.3
                arcade.draw_line(cx - s, cy - s, cx + s, cy + s, COLOR_X_MARK, 2)
                arcade.draw_line(cx - s, cy + s, cx + s, cy - s, COLOR_X_MARK, 2)

    # --- Grid lines ---
    for c in range(cols + 1):
        x = ox + c * CELL_SIZE
        thick = (c % 5 == 0)
        color = COLOR_GRID_LINE_THICK if thick else COLOR_GRID_LINE
        width = 2 if thick else 1
        arcade.draw_line(x, oy, x, oy + grid_h, color, width)

    for r in range(rows + 1):
        y = oy + r * CELL_SIZE
        thick = (r % 5 == 0)
        color = COLOR_GRID_LINE_THICK if thick else COLOR_GRID_LINE
        width = 2 if thick else 1
        arcade.draw_line(ox, y, ox + grid_w, y, color, width)

    # --- Row clues (left side) ---
    for r in range(rows):
        clues = game.row_clues[r]
        completed = game.row_completed[r]
        _, cy = cell_center(0, r, ox, oy, rows)
        clue_str = " ".join(str(c) for c in clues) if clues else "0"
        txt = game.txt_row_clues[r]
        txt.text = clue_str
        txt.y = cy
        txt.color = COLOR_CLUE_COMPLETE if completed else COLOR_CLUE_NORMAL
        txt.draw()

    # --- Column clues (top) ---
    for c in range(cols):
        clues = game.col_clues[c]
        completed = game.col_completed[c]
        cx, _ = cell_center(c, 0, ox, oy, rows)
        # Draw each clue number vertically
        for i, val in enumerate(game.txt_col_clues[c]):
            clue_idx = i
            total = len(clues)
            clue_y = oy + grid_h + CLUE_AREA_HEIGHT - 15 - clue_idx * 16
            val.x = cx
            val.y = clue_y
            val.text = str(clues[i]) if i < len(clues) else ""
            val.color = COLOR_CLUE_COMPLETE if completed else COLOR_CLUE_NORMAL
            if val.text:
                val.draw()

    # --- Win overlay ---
    if game.game_state == WON:
        arcade.draw_rect_filled(
            arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT),
            (0, 0, 0, 150),
        )
        game.txt_you_win.draw()
        game.txt_win_details.draw()
