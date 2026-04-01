"""
Renderer for the Nurikabe game.
All arcade.draw_* calls for Nurikabe live here.
"""

import arcade

# Window constants
WIDTH = 800
HEIGHT = 600

# Grid constants
GRID_SIZE = 7
CELL_SIZE = 60
GRID_PX = GRID_SIZE * CELL_SIZE  # 420

# Center the grid
GRID_ORIGIN_X = (WIDTH - GRID_PX) // 2
GRID_ORIGIN_Y = (HEIGHT - 50 - GRID_PX) // 2

# Top bar
TOP_BAR_HEIGHT = 50

# Cell states (must match game module)
UNKNOWN = 0
SEA = 1

# Colors
BG_COLOR = (40, 44, 52)
GRID_BG = (255, 255, 255)
SEA_COLOR = (30, 30, 30)
CLUE_BG = (255, 255, 255)
CONFLICT_COLOR = (220, 60, 60)
CONFLICT_SEA_COLOR = (180, 40, 40)
LINE_COLOR = (100, 100, 100)
THICK_LINE_COLOR = (20, 20, 20)
HOVER_COLOR = (220, 235, 255)
WIN_OVERLAY = (0, 0, 0, 160)


def draw(game):
    """Render the entire Nurikabe game state."""
    _draw_background()
    _draw_top_bar(game)
    _draw_grid_background()
    _draw_cells(game)
    _draw_clue_numbers(game)
    _draw_grid_lines()
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
    game.txt_puzzle_num.text = f"Puzzle {game.puzzle_index + 1}"
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


def _draw_grid_background():
    arcade.draw_rect_filled(
        arcade.XYWH(GRID_ORIGIN_X + GRID_PX / 2, GRID_ORIGIN_Y + GRID_PX / 2, GRID_PX, GRID_PX),
        GRID_BG
    )


def _draw_cells(game):
    """Draw shaded (sea) cells and conflict highlights."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            cx, cy = game._cell_center(r, c)
            if game.grid[r][c] == SEA:
                if game.conflicts[r][c]:
                    color = CONFLICT_SEA_COLOR
                else:
                    color = SEA_COLOR
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), color
                )
            elif game.conflicts[r][c]:
                arcade.draw_rect_filled(
                    arcade.XYWH(cx, cy, CELL_SIZE, CELL_SIZE), (255, 200, 200)
                )


def _draw_clue_numbers(game):
    """Draw island clue numbers."""
    for (r, c), val in game.clues.items():
        txt = game.txt_cells[(r, c)]
        txt.text = str(val)
        if game.conflicts[r][c]:
            txt.color = CONFLICT_COLOR
        else:
            txt.color = arcade.color.BLACK
        txt.draw()


def _draw_grid_lines():
    """Draw grid lines."""
    for i in range(GRID_SIZE + 1):
        x = GRID_ORIGIN_X + i * CELL_SIZE
        y0 = GRID_ORIGIN_Y
        y1 = GRID_ORIGIN_Y + GRID_PX
        lw = 2 if i == 0 or i == GRID_SIZE else 1
        col = THICK_LINE_COLOR if lw == 2 else LINE_COLOR
        arcade.draw_line(x, y0, x, y1, col, lw)

        y = GRID_ORIGIN_Y + i * CELL_SIZE
        x1 = GRID_ORIGIN_X + GRID_PX
        arcade.draw_line(GRID_ORIGIN_X, y, x1, y, col, lw)


def _draw_win_overlay(game):
    arcade.draw_rect_filled(
        arcade.XYWH(WIDTH / 2, HEIGHT / 2, WIDTH, HEIGHT), WIN_OVERLAY
    )
    game.txt_win_title.draw()
    game.txt_win_hint.draw()
